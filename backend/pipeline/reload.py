"""
Full graph reload for a region.

Clears existing data, loads courses + occupations + employers from
cached enriched files and calibration data.

Usage:
    python -m pipeline.reload --region bay_area
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path

from courses.load import load_college, CollegeConfig
from occupations.load import load_industry
from employers.load import load_employers, cleanup_stale_employers
from ontology.schema import get_driver, close_driver, init_schema
from ontology.programs import load_programs, load_program_wage_outcomes
from partnerships.compute import (
    materialize_partnership_alignment,
    materialize_occupation_pipeline,
)
from partnerships.precompute import build_all as precompute_partnership_cache

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
OCCUPATIONS_DIR = Path(__file__).parent.parent / "occupations"
EMPLOYERS_DIR = Path(__file__).parent.parent / "employers"

BAY_AREA = [
    "foothill", "deanza", "ccsf", "laney", "merritt", "berkeleycc",
    "alameda", "skyline", "canada", "csm", "losmedanos", "diablo",
    "contracosta", "evergreen", "sanjosecity", "marin", "santarosa",
    "napavalley", "solano", "westvalley", "mission", "ohlone",
    "chabot", "laspositas", "cabrillo", "gavilan",
]

REGIONS = {
    "bay_area": BAY_AREA,
}


def _load_college_configs() -> dict[str, dict]:
    """Load college configs from catalog_sources.json."""
    sources_path = Path(__file__).parent / "catalog_sources.json"
    with open(sources_path) as f:
        data = json.load(f)
    default_region = data.get("region", "San Francisco Bay Area")
    configs = {}
    for key, info in data.get("colleges", {}).items():
        configs[key] = {
            "name": info.get("name", key),
            "city": info.get("city", ""),
            # Per-college region wins over the top-level default so the
            # registry can hold colleges from multiple regions.
            "region": info.get("region", default_region),
        }
    return configs


def clear_graph(driver) -> None:
    """Clear all nodes and edges from the graph."""
    logger.info("Clearing graph...")
    with driver.session() as s:
        # Legacy Student nodes — no longer generated under the non-PII
        # configuration, but cleared here so a reload drops any that
        # remain from a pre-migration graph.
        result = s.run("MATCH (s:Student) RETURN count(s) AS cnt")
        cnt = result.single()["cnt"]
        if cnt > 0:
            logger.info(f"  Deleting {cnt} legacy students...")
            s.run("CALL { MATCH (s:Student) DETACH DELETE s } IN TRANSACTIONS OF 1000 ROWS")

        # Courses
        result = s.run("MATCH (c:Course) RETURN count(c) AS cnt")
        cnt = result.single()["cnt"]
        if cnt > 0:
            logger.info(f"  Deleting {cnt} courses...")
            s.run("CALL { MATCH (c:Course) DETACH DELETE c } IN TRANSACTIONS OF 1000 ROWS")

        # Programs (TOP6) + their shared time-dimension nodes
        s.run("MATCH (p:Program) DETACH DELETE p")
        s.run("MATCH (n:AcademicYear) DETACH DELETE n")
        s.run("MATCH (n:Term) DETACH DELETE n")
        # Departments
        s.run("MATCH (d:Department) DETACH DELETE d")
        # Skills (legacy — drop any leftover nodes from pre-crosswalk graphs)
        s.run("MATCH (s:Skill) DETACH DELETE s")
        # Occupations
        s.run("MATCH (o:Occupation) DETACH DELETE o")
        # Employers
        s.run("MATCH (e:Employer) DETACH DELETE e")
        # Regions
        s.run("MATCH (r:Region) DETACH DELETE r")
        # Colleges
        s.run("MATCH (c:College) DETACH DELETE c")

    logger.info("  Graph cleared")


def load_courses(driver, college_keys: list[str], configs: dict[str, dict]) -> int:
    """Load courses for all colleges."""
    logger.info(f"Loading courses for {len(college_keys)} colleges...")
    total_courses = 0

    for key in college_keys:
        enriched_path = CACHE_DIR / f"{key}_enriched.json"
        if not enriched_path.exists():
            logger.warning(f"  {key}: no enriched file, skipping")
            continue

        with open(enriched_path) as f:
            courses = json.load(f)

        info = configs.get(key, {"name": key, "city": "", "region": "San Francisco Bay Area"})
        config = CollegeConfig(
            name=info["name"],
            region=info["region"],
            city=info["city"],
            state="California",
        )

        stats = load_college(driver, config, courses)
        total_courses += stats.courses_created + stats.courses_updated
        logger.info(f"  {key}: {stats.courses_created} courses, {stats.departments_created} depts")

    return total_courses


def load_industry_data(driver) -> None:
    """Load occupations, regions, and employers."""
    logger.info("Loading industry data...")

    # Occupations
    occ_path = OCCUPATIONS_DIR / "occupations.json"
    with open(occ_path) as f:
        occupations = json.load(f)

    # Check for COE data
    coe_path = OCCUPATIONS_DIR / "coe_data.json"
    coe_data = None
    if coe_path.exists():
        with open(coe_path) as f:
            coe_data = json.load(f)

    stats = load_industry(driver, occupations, coe_data)
    logger.info(f"  Occupations: {stats.get('occupations', 0)}, "
                f"Regions: {stats.get('regions', 0)}, "
                f"DEMANDS: {stats.get('demands', 0)}")

    # Employers
    emp_path = EMPLOYERS_DIR / "employers.json"
    with open(emp_path) as f:
        employers = json.load(f)

    cleanup_stale_employers(driver, [e["name"] for e in employers])
    emp_stats = load_employers(driver, employers)
    logger.info(f"  Employers: {emp_stats.get('employers', 0)}, "
                f"HIRES_FOR: {emp_stats.get('hires_for', 0)}")


def verify(driver) -> None:
    """Run verification queries."""
    logger.info("Verifying graph...")
    with driver.session() as s:
        queries = [
            ("Courses", "MATCH (c:Course) RETURN count(c) AS cnt"),
            ("Departments", "MATCH (d:Department) RETURN count(d) AS cnt"),
            ("Colleges", "MATCH (c:College) RETURN count(c) AS cnt"),
            ("Occupations", "MATCH (o:Occupation) RETURN count(o) AS cnt"),
            ("Employers", "MATCH (e:Employer) RETURN count(e) AS cnt"),
            ("Regions", "MATCH (r:Region) RETURN count(r) AS cnt"),
            ("PREPARES_FOR", "MATCH ()-[p:PREPARES_FOR]->() RETURN count(p) AS cnt"),
            ("HIRES_FOR", "MATCH ()-[h:HIRES_FOR]->() RETURN count(h) AS cnt"),
            ("PARTNERSHIP_ALIGNMENT", "MATCH ()-[p:PARTNERSHIP_ALIGNMENT]->() RETURN count(p) AS cnt"),
            ("OCCUPATION_PIPELINE", "MATCH ()-[p:OCCUPATION_PIPELINE]->() RETURN count(p) AS cnt"),
        ]
        for label, query in queries:
            result = s.run(query)
            cnt = result.single()["cnt"]
            logger.info(f"  {label}: {cnt:,}")


def reload_region(region_key: str) -> None:
    """Full reload for a region."""
    if region_key not in REGIONS:
        logger.error(f"Unknown region: {region_key}. Available: {list(REGIONS.keys())}")
        return

    college_keys = REGIONS[region_key]
    configs = _load_college_configs()

    start = time.time()
    driver = get_driver()

    try:
        # Step 1: Initialize schema (fresh DB after docker compose down -v)
        init_schema()

        # Step 2: Load courses + skills
        total_courses = load_courses(driver, college_keys, configs)

        # Step 3: Load industry
        load_industry_data(driver)

        # Step 4: Load Program (TOP6) nodes + award/enrollment measures.
        # Must run after load_courses (Course/Department/TOP6 universe exist)
        # and before the partnership precompute. Additive and self-scoping:
        # only creates Programs for colleges present in the graph, so it is a
        # no-op for regions the DataMart exports don't cover. Failure is
        # non-fatal — the rest of the graph is unaffected.
        try:
            load_programs(driver)
        except Exception as e:
            logger.error(f"load_programs failed: {e}; Program layer absent until rerun")

        # Step 4b: Materialize statewide ProgramWageOutcome nodes (pooled TOP6
        # graduate-wage cohorts) + HAS_WAGE_OUTCOME edges. After load_programs
        # (Program nodes must exist). Additive and self-scoping; failure is
        # non-fatal — the wage-backed comparison criteria gate cleanly if absent.
        try:
            load_program_wage_outcomes(driver)
        except Exception as e:
            logger.error(f"load_program_wage_outcomes failed: {e}; wage outcomes absent until rerun")

        # Step 5: Materialize PARTNERSHIP_ALIGNMENT and OCCUPATION_PIPELINE
        # edges. Must run after both load_courses (PREPARES_FOR exists) and
        # load_industry_data (Employer / HIRES_FOR exist).
        for key in college_keys:
            college_name = configs.get(key, {"name": key})["name"]
            try:
                materialize_partnership_alignment(driver, college_name)
            except Exception as e:
                logger.error(
                    f"materialize_partnership_alignment failed for {college_name}: {e}; "
                    f"/employers/ will return empty until rerun"
                )
            try:
                materialize_occupation_pipeline(driver, college_name)
            except Exception as e:
                logger.error(
                    f"materialize_occupation_pipeline failed for {college_name}: {e}; "
                    f"/partnerships/sectors will fall back to live computation "
                    f"(slow) until rerun"
                )

        # Step 6: Verify
        verify(driver)

        # Step 7: Precompute partnership reports. Materializes every
        # /partnerships/sectors and /partnerships/opportunity/{soc}
        # response to gzipped JSON on disk so the serving layer can
        # return them with a single file read instead of running the
        # 6–8 Cypher queries per request that produced the slow tail
        # (p99=60s, max=469s on prod). Wrapped in try/except because
        # a precompute failure should not fail the reload — the
        # serving layer's fallback path remains operational.
        try:
            cache_dir = Path(os.environ.get(
                "KALLIPOLIS_CACHE_DIR", "/var/lib/kallipolis/cache"
            ))
            precompute_partnership_cache(driver=driver, out_dir=cache_dir)
        except Exception as e:
            logger.error(
                f"precompute_partnership_cache failed: {e}; "
                f"/partnerships endpoints will fall back to live "
                f"computation (slow) until rerun"
            )

    finally:
        close_driver()

    elapsed = time.time() - start
    logger.info(f"\n{'=' * 60}")
    logger.info(f"RELOAD COMPLETE in {elapsed / 60:.1f} min")
    logger.info(f"  Courses: {total_courses:,}")


def main():
    parser = argparse.ArgumentParser(description="Full graph reload")
    parser.add_argument("--region", required=True, choices=list(REGIONS.keys()),
                        help="Region to reload")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    reload_region(args.region)


if __name__ == "__main__":
    main()
