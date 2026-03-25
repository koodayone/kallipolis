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

from pipeline.scraper import RawCourse
from pipeline.skills import derive_skills
from pipeline.loader import load_college, CollegeConfig, LoadStats
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

    region = data.get("region", "Unknown")
    entries = {}

    for college_id, info in data.get("colleges", {}).items():
        if not info.get("catalog_pdf_url"):
            continue  # Skip colleges with no PDF
        entries[college_id] = {
            "catalog_pdf_url": info["catalog_pdf_url"],
            "scraper_type": "pdf",
            "config": CollegeConfig(
                name=info["name"],
                region=region,
                city=info.get("city", ""),
                state="California",
            ),
        }

    return entries


COLLEGES = _load_colleges()

CACHE_DIR = Path(__file__).resolve().parent.parent / "pipeline" / "cache"


def _cache_path(college_key: str, stage: str) -> Path:
    return CACHE_DIR / f"{college_key}_{stage}.json"


async def run_pipeline(
    college_key: str,
    skip_skills: bool = False,
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
        from pipeline.scraper_pdf import scrape_pdf_catalog
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

        from pipeline.students import generate_and_load_students
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
        from pipeline.students import generate_and_load_students

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
        "--load-employers", action="store_true", help="Load regional employer data"
    )
    args = parser.parse_args()

    # Load env — .env is at repo root (two levels up from backend/)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Handle --load-employers as a standalone action
    if args.load_employers:
        from pipeline.employers import load_employers
        os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
        os.environ.setdefault("NEO4J_USERNAME", "neo4j")
        os.environ.setdefault("NEO4J_PASSWORD", "kallipolis_dev")
        college = COLLEGES.get(args.college)
        if college:
            driver = get_driver()
            try:
                region = college["config"].region
                load_employers(driver, region)
            finally:
                close_driver()
        return

    asyncio.run(run_pipeline(
        college_key=args.college,
        skip_skills=args.skip_skills,
        from_cache=args.from_cache,
        scrape_only=args.scrape_only,
        generate_students=args.generate_students,
        num_students=args.num_students,
        seed=args.seed,
    ))


if __name__ == "__main__":
    main()
