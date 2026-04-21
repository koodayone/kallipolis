"""
Pipeline runner — orchestrates scrape → enrich → load for a college.

Usage:
    python -m pipeline.run --college foothill
    python -m pipeline.run --college foothill --skip-skills  # scrape only, no LLM
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
from ontology.skills import derive_skills
from courses.load import load_college, CollegeConfig, LoadStats
from courses.department_mapping import (
    OVERLAY_DIR as DEPT_OVERLAY_DIR,
    UnknownPrefixError,
    canonicalize_courses,
    resolve_unknown_prefixes,
)
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
            continue  # Skip colleges with no PDF
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


def _canonicalize_departments(
    college_key: str,
    enriched_courses: list[dict],
    *,
    allow_unmapped: bool,
) -> list[dict]:
    """Stage 2.5: rewrite every course's `department` field to the canonical
    human-readable name derived from the course code's prefix.

    Skipped (with a warning) for colleges that don't yet have a committed
    overlay file at `backend/courses/department_mapping/overlays/{key}.json`.
    Existing enriched data flows through unchanged in that case, preserving
    prior behavior during rollout.

    When an overlay exists and Stage 2.5 runs, any course prefix not in the
    merged mapping is a hard failure by default — the operator must add an
    overlay entry before the load can proceed. The `--allow-unmapped`
    escape hatch swaps the failure for a deliberately ugly `Unmapped: XXX`
    placeholder, which surfaces visibly in the atlas UI and prevents a
    one-day outage from blocking a 79-college reload.

    Writes the canonicalized list back to `{college}_enriched.json` so
    every downstream consumer (Neo4j loader, student generator, partnership
    gatherer, audits) reads the canonical department value without needing
    to know this step happened.
    """
    overlay_path = DEPT_OVERLAY_DIR / f"{college_key}.json"
    if not overlay_path.exists():
        logger.warning(
            "Stage 2.5 skipped — no department overlay at %s. Run "
            "`python tools/courses-audit/seed_department_mapping.py "
            "--college %s` to generate one.",
            overlay_path.relative_to(Path(__file__).resolve().parent.parent.parent),
            college_key,
        )
        return enriched_courses

    if not allow_unmapped:
        # Surface the full set of missing prefixes at once rather than
        # raising on the first one — gives the operator a complete punch
        # list instead of a whack-a-mole sequence.
        missing = resolve_unknown_prefixes(enriched_courses, college_key)
        if missing:
            lines = [
                f"Stage 2.5: {len(missing)} prefix(es) in {college_key}_enriched.json",
                f"  have no mapping entry in overlays/{college_key}.json:",
            ]
            for prefix, count in missing.items():
                lines.append(f"    {prefix!r}: {count} course(s)")
            lines.append(
                "Add entries to the overlay under 'prefixes', or rerun with "
                "--allow-unmapped to use placeholder labels."
            )
            raise UnknownPrefixError(next(iter(missing)), college_key).__class__(
                "\n".join(lines)
            )

    canonicalized, rewrote = canonicalize_courses(
        enriched_courses, college_key, strict=not allow_unmapped
    )
    enriched_cache = _cache_path(college_key, "enriched")
    with enriched_cache.open("w") as f:
        json.dump(canonicalized, f, indent=2, ensure_ascii=False)
    logger.info(
        "Stage 2.5 complete: rewrote department on %d/%d course(s); "
        "%d unique department names after canonicalization",
        rewrote,
        len(canonicalized),
        len({c.get("department", "") for c in canonicalized}),
    )
    return canonicalized


async def run_pipeline(
    college_key: str,
    skip_skills: bool = False,
    from_cache: bool = False,
    scrape_only: bool = False,
    generate_students: bool = False,
    num_students: Optional[int] = None,
    seed: int = 42,
    allow_unmapped_departments: bool = False,
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

    # ── Stage 2: Skill derivation ────────────────────────────────────────
    # The PDF scraper now extracts courses + skills in a single pass,
    # caching the result as {college_key}_enriched.json. If that cache
    # exists, Stage 2 is already done. Otherwise, fall back to the
    # separate skill derivation pipeline.
    enriched_cache = _cache_path(college_key, "enriched")

    # If only generating students (with --from-cache), skip stages 2-3
    # and jump directly to student generation
    if generate_students and from_cache and enriched_cache.exists():
        logger.info(f"Loading cached enriched data from {enriched_cache}")
        with open(enriched_cache) as f:
            enriched_courses = json.load(f)
        logger.info(f"Loaded {len(enriched_courses)} courses from cache")

        # Stage 2.5 runs even on the student-gen-only path so that synthetic
        # enrollments are sampled from canonical department buckets, not the
        # fragmented ones Gemini originally emitted.
        enriched_courses = _canonicalize_departments(
            college_key, enriched_courses, allow_unmapped=allow_unmapped_departments
        )

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
        # Combined extraction already produced enriched data
        logger.info(f"Loading enriched data from {enriched_cache}")
        with open(enriched_cache) as f:
            enriched_courses = json.load(f)
        logger.info(f"Stage 2 skipped — skills already derived during extraction")
    elif skip_skills:
        logger.info("Skipping skill derivation — using raw data with empty skill_mappings")
        enriched_courses = [c.to_dict() for c in raw_courses]
        for c in enriched_courses:
            c["skill_mappings"] = []
    else:
        # Fallback: separate skill derivation (for non-PDF scrapers)
        logger.info(f"Deriving skills for {len(raw_courses)} courses...")
        enriched_courses = await derive_skills(raw_courses)

        with open(enriched_cache, "w") as f:
            json.dump(enriched_courses, f, indent=2)
        logger.info(f"Cached enriched courses to {enriched_cache}")

    logger.info(f"Stage 2 complete: {len(enriched_courses)} courses enriched")

    # ── Stage 2.5: Canonicalize department field ─────────────────────────
    # Rewrite each course's `department` to the human-readable name derived
    # from its code prefix via the committed mapping. This eliminates the
    # "Dance" vs "Dance (DANC)" fragmentation that Gemini introduces when
    # extracting subject headers from chunked PDF pages. See
    # backend/courses/department_mapping/ for the mapping + invariants.
    enriched_courses = _canonicalize_departments(
        college_key, enriched_courses, allow_unmapped=allow_unmapped_departments
    )

    # ── Stage 3: Load into Neo4j ─────────────────────────────────────────
    logger.info(f"Loading {len(enriched_courses)} courses into Neo4j for {config.name}...")

    driver = get_driver()
    try:
        stats = load_college(driver, config, enriched_courses)
    finally:
        close_driver()

    logger.info(f"Stage 3 complete: {stats}")

    # ── Summary ──────────────────────────────────────────────────────────
    all_skills: set[str] = set()
    for c in enriched_courses:
        all_skills.update(c.get("skill_mappings", []))
    logger.info(f"Unique skills in taxonomy: {len(all_skills)}")

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
        "--skip-skills", action="store_true", help="Skip Claude skill derivation"
    )
    parser.add_argument(
        "--from-cache", action="store_true", help="Load from cached scrape results"
    )
    parser.add_argument(
        "--scrape-only", action="store_true", help="Only scrape, don't derive skills or load"
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
    parser.add_argument(
        "--allow-unmapped-departments",
        action="store_true",
        help="Instead of failing on a course prefix with no department mapping "
             "entry, substitute 'Unmapped: PREFIX' as a placeholder label. "
             "Use only as an operational escape hatch; the placeholder is "
             "deliberately ugly and must be fixed in the overlay within 7 days.",
    )
    args = parser.parse_args()

    # Load env — .env is at repo root (two levels up from backend/)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    asyncio.run(run_pipeline(
        college_key=args.college,
        skip_skills=args.skip_skills,
        from_cache=args.from_cache,
        scrape_only=args.scrape_only,
        generate_students=args.generate_students,
        num_students=args.num_students,
        seed=args.seed,
        allow_unmapped_departments=args.allow_unmapped_departments,
    ))


if __name__ == "__main__":
    main()
