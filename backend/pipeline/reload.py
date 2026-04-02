"""
Full graph reload for a region.

Clears existing data, loads courses + skills + occupations + employers + students
from cached enriched files and calibration data.

Usage:
    python -m pipeline.reload --region bay_area
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from pipeline.loader import load_college, CollegeConfig
from pipeline.students import generate_and_load_students
from pipeline.industry.loader import load_industry
from pipeline.industry.employers import load_employers
from ontology.schema import get_driver, close_driver, init_schema

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
CALIBRATIONS_DIR = Path(__file__).parent / "calibrations"
INDUSTRY_DIR = Path(__file__).parent / "industry"

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
    region = data.get("region", "San Francisco Bay Area")
    configs = {}
    for key, info in data.get("colleges", {}).items():
        configs[key] = {
            "name": info.get("name", key),
            "city": info.get("city", ""),
            "region": region,
        }
    return configs


def clear_graph(driver) -> None:
    """Clear all nodes and edges from the graph."""
    logger.info("Clearing graph...")
    with driver.session() as s:
        # Students first (most nodes)
        result = s.run("MATCH (s:Student) RETURN count(s) AS cnt")
        cnt = result.single()["cnt"]
        if cnt > 0:
            logger.info(f"  Deleting {cnt} students...")
            s.run("CALL { MATCH (s:Student) DETACH DELETE s } IN TRANSACTIONS OF 1000 ROWS")

        # Courses
        result = s.run("MATCH (c:Course) RETURN count(c) AS cnt")
        cnt = result.single()["cnt"]
        if cnt > 0:
            logger.info(f"  Deleting {cnt} courses...")
            s.run("CALL { MATCH (c:Course) DETACH DELETE c } IN TRANSACTIONS OF 1000 ROWS")

        # Departments
        s.run("MATCH (d:Department) DETACH DELETE d")
        # Skills
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
    """Load courses + skills for all colleges."""
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
    occ_path = INDUSTRY_DIR / "occupations.json"
    with open(occ_path) as f:
        occupations = json.load(f)

    # Check for COE data
    coe_path = INDUSTRY_DIR / "coe_data.json"
    coe_data = None
    if coe_path.exists():
        with open(coe_path) as f:
            coe_data = json.load(f)

    stats = load_industry(driver, occupations, coe_data)
    logger.info(f"  Occupations: {stats.get('occupations', 0)}, "
                f"Regions: {stats.get('regions', 0)}, "
                f"REQUIRES_SKILL: {stats.get('requires_skill', 0)}")

    # Employers
    emp_path = INDUSTRY_DIR / "employers.json"
    with open(emp_path) as f:
        employers = json.load(f)

    emp_stats = load_employers(driver, employers)
    logger.info(f"  Employers: {emp_stats.get('employers', 0)}, "
                f"HIRES_FOR: {emp_stats.get('hires_for', 0)}")


def generate_students(driver, college_keys: list[str], configs: dict[str, dict]) -> int:
    """Generate synthetic students for all colleges."""
    logger.info(f"Generating students for {len(college_keys)} colleges...")
    total_students = 0

    for key in college_keys:
        enriched_path = CACHE_DIR / f"{key}_enriched.json"
        if not enriched_path.exists():
            logger.warning(f"  {key}: no enriched file, skipping students")
            continue

        with open(enriched_path) as f:
            courses = json.load(f)

        # Skip if no courses with skills (MCF-only colleges)
        if not any(c.get("skill_mappings") for c in courses):
            logger.info(f"  {key}: no skills, skipping students")
            continue

        info = configs.get(key, {"name": key})
        institution_name = info["name"]

        try:
            stats = generate_and_load_students(
                college_key=key,
                courses=courses,
                institution_name=institution_name,
                driver=driver,
            )
            total_students += stats.students
            logger.info(f"  {key}: {stats.students} students, {stats.enrollments} enrollments")
        except Exception as e:
            logger.error(f"  {key}: student generation failed: {e}")

    return total_students


def verify(driver) -> None:
    """Run verification queries."""
    logger.info("Verifying graph...")
    with driver.session() as s:
        queries = [
            ("Skills", "MATCH (s:Skill) RETURN count(s) AS cnt"),
            ("Courses", "MATCH (c:Course) RETURN count(c) AS cnt"),
            ("Departments", "MATCH (d:Department) RETURN count(d) AS cnt"),
            ("Students", "MATCH (s:Student) RETURN count(s) AS cnt"),
            ("Colleges", "MATCH (c:College) RETURN count(c) AS cnt"),
            ("Occupations", "MATCH (o:Occupation) RETURN count(o) AS cnt"),
            ("Employers", "MATCH (e:Employer) RETURN count(e) AS cnt"),
            ("Regions", "MATCH (r:Region) RETURN count(r) AS cnt"),
            ("DEVELOPS", "MATCH ()-[d:DEVELOPS]->() RETURN count(d) AS cnt"),
            ("REQUIRES_SKILL", "MATCH ()-[r:REQUIRES_SKILL]->() RETURN count(r) AS cnt"),
            ("ENROLLED_IN", "MATCH ()-[e:ENROLLED_IN]->() RETURN count(e) AS cnt"),
            ("HAS_SKILL", "MATCH ()-[h:HAS_SKILL]->() RETURN count(h) AS cnt"),
            ("HIRES_FOR", "MATCH ()-[h:HIRES_FOR]->() RETURN count(h) AS cnt"),
        ]
        for label, query in queries:
            result = s.run(query)
            cnt = result.single()["cnt"]
            logger.info(f"  {label}: {cnt:,}")

        # Bridge skills
        result = s.run("""
            MATCH (s:Skill)
            WHERE EXISTS { MATCH (:Course)-[:DEVELOPS]->(s) }
              AND EXISTS { MATCH (:Occupation)-[:REQUIRES_SKILL]->(s) }
            RETURN count(s) AS cnt
        """)
        bridge = result.single()["cnt"]
        logger.info(f"  Bridge skills (in both DEVELOPS and REQUIRES_SKILL): {bridge}")


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

        # Step 3: Load courses + skills
        total_courses = load_courses(driver, college_keys, configs)

        # Step 4: Load industry
        load_industry_data(driver)

        # Step 5: Generate students
        total_students = generate_students(driver, college_keys, configs)

        # Step 6: Verify
        verify(driver)

    finally:
        close_driver()

    elapsed = time.time() - start
    logger.info(f"\n{'=' * 60}")
    logger.info(f"RELOAD COMPLETE in {elapsed / 60:.1f} min")
    logger.info(f"  Courses: {total_courses:,}")
    logger.info(f"  Students: {total_students:,}")


def main():
    parser = argparse.ArgumentParser(description="Full graph reload")
    parser.add_argument("--region", required=True, choices=list(REGIONS.keys()),
                        help="Region to reload")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    reload_region(args.region)


if __name__ == "__main__":
    main()
