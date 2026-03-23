"""
Pipeline runner — orchestrates scrape → enrich → load for a college.

Usage:
    python -m pipeline.run --college foothill
    python -m pipeline.run --college foothill --skip-skills  # scrape only, no LLM
    python -m pipeline.run --college foothill --from-cache    # load from cached JSON
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

from pipeline.scraper import scrape_catalog, RawCourse
from pipeline.skills import derive_skills
from pipeline.loader import load_college, CollegeConfig, LoadStats
from ontology.schema import get_driver, close_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")

# ── College registry ───────────────────────────────────────────────────────────
# Add colleges here as we scale. Each entry has the catalog URL and Neo4j config.

COLLEGES = {
    "foothill": {
        "catalog_url": "https://catalog.foothill.edu",
        "config": CollegeConfig(
            name="Foothill College",
            region="San Francisco Bay Area",
            city="Los Altos Hills",
            state="California",
        ),
    },
}

CACHE_DIR = Path(__file__).resolve().parent.parent / "pipeline" / "cache"


def _cache_path(college_key: str, stage: str) -> Path:
    return CACHE_DIR / f"{college_key}_{stage}.json"


async def run_pipeline(
    college_key: str,
    skip_skills: bool = False,
    from_cache: bool = False,
    scrape_only: bool = False,
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
        logger.info(f"Scraping catalog: {college['catalog_url']}")
        raw_courses = await scrape_catalog(college["catalog_url"])

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
    enriched_cache = _cache_path(college_key, "enriched")

    if skip_skills and enriched_cache.exists():
        logger.info(f"Loading cached enriched data from {enriched_cache}")
        with open(enriched_cache) as f:
            enriched_courses = json.load(f)
    elif skip_skills:
        logger.info("Skipping skill derivation — using raw data with empty skill_mappings")
        enriched_courses = [c.to_dict() for c in raw_courses]
        for c in enriched_courses:
            c["skill_mappings"] = []
    else:
        logger.info(f"Deriving skills for {len(raw_courses)} courses...")
        enriched_courses = await derive_skills(raw_courses)

        # Cache enriched results
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
    # Count unique skills across all courses
    all_skills: set[str] = set()
    for c in enriched_courses:
        all_skills.update(c.get("skill_mappings", []))
    logger.info(f"Unique skills in taxonomy: {len(all_skills)}")

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
    args = parser.parse_args()

    # Load env — .env is at repo root (two levels up from backend/)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    asyncio.run(run_pipeline(
        college_key=args.college,
        skip_skills=args.skip_skills,
        from_cache=args.from_cache,
        scrape_only=args.scrape_only,
    ))


if __name__ == "__main__":
    main()
