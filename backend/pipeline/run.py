"""
Pipeline runner — orchestrates scrape → load for a college.

Usage:
    python -m pipeline.run --college foothill
    python -m pipeline.run --college foothill --from-cache    # load from cached JSON
    python -m pipeline.run --college foothill --generate-students --from-cache
    python -m pipeline.run --college foothill --generate-students --num-students 5000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from courses.scrape import RawCourse
from courses.load import load_college, CollegeConfig, LoadStats
from courses.extraction_filter import filter_extracted
from ontology.schema import get_driver, close_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")

# ── College registry ───────────────────────────────────────────────────────────
# All colleges loaded from catalog_sources.json (PDF pipeline).
# To add a college, add an entry to catalog_sources.json — no code changes needed.

COLLEGES: dict = {}


def _load_colleges() -> dict:
    """Load colleges from catalog_sources.json into the registry."""
    sources_path = Path(__file__).resolve().parent / "catalog_sources.json"
    if not sources_path.exists():
        logger.warning(f"catalog_sources.json not found at {sources_path}")
        return {}

    with open(sources_path) as f:
        data = json.load(f)

    default_region = data.get("region", "Unknown")
    entries = {}

    for college_id, info in data.get("colleges", {}).items():
        if not info.get("catalog_pdf_url"):
            # Some catalogs are online-only (no public PDF URL). If we
            # already have a cached PDF on disk for this college, allow
            # the entry through with the cache path as the URL — the
            # downloader checks the cache first and never fetches when
            # the cache is present.
            cached_pdf = (
                Path(__file__).resolve().parent / "cache" / f"{college_id}_catalog.pdf"
            )
            if not cached_pdf.exists():
                continue  # No URL and no cached PDF — skip
            info = dict(info, catalog_pdf_url=str(cached_pdf))
        # Prefer per-college region override so the registry can hold
        # colleges from multiple regions without the top-level region
        # field silently mislabeling them.
        entries[college_id] = {
            "catalog_pdf_url": info["catalog_pdf_url"],
            "scraper_type": "pdf",
            "config": CollegeConfig(
                name=info["name"],
                region=info.get("region", default_region),
                city=info.get("city", ""),
                state="California",
            ),
        }

    return entries


COLLEGES = _load_colleges()

CACHE_DIR = Path(__file__).resolve().parent.parent / "pipeline" / "cache"


def _cache_path(college_key: str, stage: str) -> Path:
    return CACHE_DIR / f"{college_key}_{stage}.json"


# Stage 2.5 (per-college department-mapping overlay) was removed in favor
# of TOP4-derived department names sourced from the Chancellor's Office
# Taxonomy of Programs Manual. See `ontology.crosswalks.top_to_department_name`
# and `backend/ontology/data/top4_names.json`. The loader (`load_college`)
# computes `Course.department` from `Course.top_code` directly, so no
# pre-load canonicalization step is needed.


async def run_pipeline(
    college_key: str,
    from_cache: bool = False,
    scrape_only: bool = False,
    generate_students: bool = False,
    num_students: Optional[int] = None,
    seed: int = 42,
) -> LoadStats | None:
    """Run the full pipeline for a college."""

    if college_key not in COLLEGES:
        logger.error(f"Unknown college: {college_key}. Available: {list(COLLEGES.keys())}")
        return None

    college = COLLEGES[college_key]
    config = college["config"]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Scrape ──────────────────────────────────────────────────
    raw_cache = _cache_path(college_key, "raw")

    if from_cache and raw_cache.exists():
        logger.info(f"Loading cached raw data from {raw_cache}")
        with open(raw_cache) as f:
            raw_dicts = json.load(f)
        raw_courses = [RawCourse(**d) for d in raw_dicts]
    else:
        logger.info(f"Extracting courses from catalog PDF: {college['catalog_pdf_url']}")
        from courses.scrape_pdf import scrape_pdf_catalog
        raw_courses = await scrape_pdf_catalog(
            pdf_url=college["catalog_pdf_url"],
            college_key=college_key,
        )

        # Cache raw results
        raw_dicts = [c.to_dict() for c in raw_courses]
        with open(raw_cache, "w") as f:
            json.dump(raw_dicts, f, indent=2)
        logger.info(f"Cached {len(raw_courses)} raw courses to {raw_cache}")

    if not raw_courses:
        logger.error("No courses scraped. Aborting pipeline.")
        return None

    logger.info(f"Stage 1 complete: {len(raw_courses)} courses scraped")

    if scrape_only:
        logger.info("Scrape-only mode. Stopping here.")
        return None

    # ── Stage 2: Load enriched data ──────────────────────────────────────
    # The PDF scraper caches its output as {college_key}_enriched.json.
    # When that cache exists, load from it; otherwise serialize the
    # freshly-scraped raw courses to the same cache for the loader.
    enriched_cache = _cache_path(college_key, "enriched")

    # If only generating students (with --from-cache), skip the load
    # stage and jump directly to student generation.
    if generate_students and from_cache and enriched_cache.exists():
        logger.info(f"Loading cached enriched data from {enriched_cache}")
        with open(enriched_cache) as f:
            enriched_courses = json.load(f)
        logger.info(f"Loaded {len(enriched_courses)} courses from cache")

        from students.generate import generate_and_load_students
        logger.info(f"Generating synthetic students (seed={seed})...")
        driver = get_driver()
        try:
            gen_stats = generate_and_load_students(
                college_key=college_key,
                courses=enriched_courses,
                institution_name=config.name,
                driver=driver,
                num_students=num_students,
                seed=seed,
                config=college.get("student_config"),
            )
            logger.info(f"Complete: {gen_stats.students_generated} students, "
                        f"{gen_stats.enrollments_created} enrollments, "
                        f"success rate: {gen_stats.success_rate:.1%}")
        finally:
            close_driver()
        return None

    if enriched_cache.exists():
        logger.info(f"Loading enriched data from {enriched_cache}")
        with open(enriched_cache) as f:
            enriched_courses = json.load(f)
    else:
        # Non-PDF scraper path: serialize the raw scrape directly.
        enriched_courses = [c.to_dict() for c in raw_courses]
        with open(enriched_cache, "w") as f:
            json.dump(enriched_courses, f, indent=2)
        logger.info(f"Cached enriched courses to {enriched_cache}")

    # ── Extraction filter on the load path ───────────────────────────────
    # `scrape_pdf.py` runs the same filter at extraction time, so a fresh
    # scrape's enriched.json is already clean. But the --from-cache path
    # (and the non-PDF path above) reads enriched.json that may pre-date
    # the filter, so artifact rows would otherwise come back as Course
    # nodes. Run the filter unconditionally here — idempotent on already-
    # clean caches, load-bearing on legacy ones.
    pre_filter = len(enriched_courses)
    enriched_courses, dropped = filter_extracted(enriched_courses)
    if dropped:
        from collections import Counter
        reason_counts = Counter(reason for _, reason in dropped)
        logger.info(
            f"Extraction filter dropped {len(dropped)}/{pre_filter} cached "
            f"course row(s): {dict(reason_counts)}"
        )
        # Persist the filtered list so the cache stays clean for future
        # runs and the post-load gate sees the same totals as the loader.
        with open(enriched_cache, "w") as f:
            json.dump(enriched_courses, f, indent=2)

    # ── Stage 3: Load into Neo4j ─────────────────────────────────────────
    logger.info(f"Loading {len(enriched_courses)} courses into Neo4j for {config.name}...")

    driver = get_driver()
    try:
        stats = load_college(driver, config, enriched_courses)
    finally:
        close_driver()

    logger.info(f"Stage 3 complete: {stats}")

    # ── Post-load gate ────────────────────────────────────────────────
    # If TOP6 coverage falls below the hard floor, the run is broken in
    # a way the operator needs to investigate before downstream stages
    # can produce correct output. Common causes:
    #   - mcf_lookup regression (slash/normalization broke matching)
    #   - extraction filter not catching a new artifact pattern
    #   - wrong MCF column mapping in supply._NEO4J_TO_SUPPLY
    #   - MCF dataset for this college is missing or empty
    # The thresholds are intentionally generous (80% hard, 95% soft) so
    # legit MCF lag (e.g., Sacramento City ~88%) doesn't block loads,
    # but a catastrophic regression (Foothill once dropped to 32%) does.
    coverage = stats.courses_with_top_code / max(stats.courses_created, 1)
    if coverage < 0.80:
        logger.error(
            f"TOP6 coverage gate FAILED for {config.name}: "
            f"{stats.courses_with_top_code}/{stats.courses_created} "
            f"= {coverage:.1%} (hard floor 80%). "
            f"Investigate before continuing."
        )
        raise RuntimeError(
            f"TOP6 coverage {coverage:.1%} below 80% floor for {config.name}"
        )
    elif coverage < 0.95:
        logger.warning(
            f"TOP6 coverage below soft target for {config.name}: "
            f"{stats.courses_with_top_code}/{stats.courses_created} "
            f"= {coverage:.1%} (soft target 95%). "
            f"Likely MCF lag — check classify_unmapped.py for the gap shape."
        )
    else:
        logger.info(
            f"TOP6 coverage healthy for {config.name}: {coverage:.1%}"
        )

    # ── Stage 4: Generate synthetic students (optional) ─────────────────
    if generate_students:
        from students.generate import generate_and_load_students

        logger.info(f"Generating synthetic students (seed={seed})...")
        driver = get_driver()
        try:
            gen_stats = generate_and_load_students(
                college_key=college_key,
                courses=enriched_courses,
                institution_name=config.name,
                driver=driver,
                num_students=num_students,
                seed=seed,
                config=college.get("student_config"),
            )
            logger.info(f"Stage 4 complete: {gen_stats.students_generated} students, "
                        f"{gen_stats.enrollments_created} enrollments")
        finally:
            close_driver()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Kallipolis curriculum ingestion pipeline")
    parser.add_argument(
        "--college", required=True, help=f"College key. Available: {list(COLLEGES.keys())}"
    )
    parser.add_argument(
        "--from-cache", action="store_true", help="Load from cached scrape results"
    )
    parser.add_argument(
        "--scrape-only", action="store_true", help="Only scrape, don't load into Neo4j"
    )
    parser.add_argument(
        "--generate-students", action="store_true", help="Generate synthetic student data"
    )
    parser.add_argument(
        "--num-students", type=int, default=None, help="Number of students to generate (default: from calibration or 3000)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for student generation (default: 42)"
    )
    args = parser.parse_args()

    # Load env — .env is at repo root (two levels up from backend/)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    asyncio.run(run_pipeline(
        college_key=args.college,
        from_cache=args.from_cache,
        scrape_only=args.scrape_only,
        generate_students=args.generate_students,
        num_students=args.num_students,
        seed=args.seed,
    ))


if __name__ == "__main__":
    main()
