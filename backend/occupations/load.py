"""
Load Region and Occupation nodes into Neo4j from generated occupations.json.

Occupations are sourced from Centers of Excellence data. Regions are COE
region codes (Bay, CVML, FN, etc.), not OEWS metros.

Usage:
    python -m pipeline.industry.loader
"""

import json
import logging
from pathlib import Path
from typing import Optional

from neo4j import Driver
from ontology.schema import get_driver, close_driver
from ontology.regions import (
    COLLEGE_COE_REGION,
    COE_REGION_DISPLAY,
    ensure_college_region_link,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def load_industry(
    driver: Driver,
    occupations: list[dict],
    filtered_soc_codes: Optional[set[str]] = None,
) -> dict:
    """Load Region, Occupation, and relationship data into Neo4j.

    Args:
        driver: Neo4j driver instance.
        occupations: List of occupation dicts from occupations.json. The
            workforce-development band filter is applied upstream in
            occupations/generate.py, so this list is already scoped to
            loadable rows.
        filtered_soc_codes: Optional set of SOC codes to load. If provided,
                  only these occupations are loaded into the graph.
    """
    if filtered_soc_codes is not None:
        before = len(occupations)
        occupations = [o for o in occupations if o["soc_code"] in filtered_soc_codes]
        logger.info(f"Filtered to {len(occupations)} occupations (from {before})")
    stats = {"regions": 0, "occupations": 0, "demands": 0, "requires_skill": 0, "college_links": 0}

    with driver.session() as session:
        # 1. Create Region nodes from COE region codes
        regions = set()
        for occ in occupations:
            regions.update(occ["regions"].keys())

        for region_name in regions:
            display_name = COE_REGION_DISPLAY.get(region_name, region_name)
            session.run(
                "MERGE (r:Region {name: $name}) SET r.display_name = $display",
                name=region_name, display=display_name,
            )
            stats["regions"] += 1
        logger.info(f"Created {stats['regions']} Region nodes")

    # 2. Link Colleges to COE Regions — delegates to the helper in
    # ontology/regions.py so the MERGE lives in exactly one place.
    # The helper manages its own session.
    for college_name in COLLEGE_COE_REGION:
        if ensure_college_region_link(driver, college_name):
            stats["college_links"] += 1
    logger.info(f"Created {stats['college_links']} College-Region links")

    with driver.session() as session:
        # 3. Create Occupation nodes (wage is regional, lives on DEMANDS edge)
        occ_batch = []
        for occ in occupations:
            occ_batch.append({
                "soc_code": occ["soc_code"],
                "title": occ["title"],
                "description": occ.get("description", ""),
                "education_level": occ.get("education_level"),
            })
            if len(occ_batch) >= BATCH_SIZE:
                _create_occupations(session, occ_batch)
                stats["occupations"] += len(occ_batch)
                occ_batch = []
        if occ_batch:
            _create_occupations(session, occ_batch)
            stats["occupations"] += len(occ_batch)
        logger.info(f"Created {stats['occupations']} Occupation nodes")

        # 4. Create Region -[:DEMANDS]-> Occupation with full COE data
        demand_batch = []
        for occ in occupations:
            for region_name, region_data in occ["regions"].items():
                demand_batch.append({
                    "soc_code": occ["soc_code"],
                    "region": region_name,
                    "employment": region_data.get("employment"),
                    "annual_wage": region_data.get("annual_wage"),
                    "growth_rate": region_data.get("growth_rate"),
                    "annual_openings": region_data.get("annual_openings"),
                })
                if len(demand_batch) >= BATCH_SIZE:
                    _create_demands(session, demand_batch)
                    stats["demands"] += len(demand_batch)
                    demand_batch = []
        if demand_batch:
            _create_demands(session, demand_batch)
            stats["demands"] += len(demand_batch)
        logger.info(f"Created {stats['demands']} DEMANDS edges")

        # 5. Create Occupation -[:REQUIRES_SKILL]-> Skill
        skill_batch = []
        for occ in occupations:
            for skill_name in occ.get("skills", []):
                skill_batch.append({
                    "soc_code": occ["soc_code"],
                    "skill": skill_name,
                })
                if len(skill_batch) >= BATCH_SIZE:
                    cnt = _create_requires_skill(session, skill_batch)
                    stats["requires_skill"] += cnt
                    skill_batch = []
        if skill_batch:
            cnt = _create_requires_skill(session, skill_batch)
            stats["requires_skill"] += cnt
        logger.info(f"Created {stats['requires_skill']} REQUIRES_SKILL edges")

    return stats


def _create_occupations(session, batch: list[dict]):
    session.run(
        """
        UNWIND $batch AS row
        MERGE (o:Occupation {soc_code: row.soc_code})
        SET o.title = row.title,
            o.description = row.description,
            o.education_level = row.education_level
        """,
        batch=batch,
    )


def _create_demands(session, batch: list[dict]):
    session.run(
        """
        UNWIND $batch AS row
        MATCH (r:Region {name: row.region})
        MATCH (o:Occupation {soc_code: row.soc_code})
        MERGE (r)-[d:DEMANDS]->(o)
        SET d.employment = row.employment,
            d.annual_wage = row.annual_wage,
            d.growth_rate = row.growth_rate,
            d.annual_openings = row.annual_openings
        """,
        batch=batch,
    )


def _create_requires_skill(session, batch: list[dict]) -> int:
    result = session.run(
        """
        UNWIND $batch AS row
        MATCH (o:Occupation {soc_code: row.soc_code})
        MERGE (s:Skill {name: row.skill})
        WITH o, s
        MERGE (o)-[:REQUIRES_SKILL]->(s)
        RETURN count(*) AS cnt
        """,
        batch=batch,
    )
    return result.single()["cnt"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data_path = Path(__file__).parent / "occupations.json"
    with open(data_path) as f:
        occupations = json.load(f)

    logger.info(f"Loading {len(occupations)} occupations into Neo4j")

    driver = get_driver()
    try:
        stats = load_industry(driver, occupations)
        logger.info(f"\nComplete: {stats}")
    finally:
        close_driver()
