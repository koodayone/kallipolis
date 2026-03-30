"""
Load Region and Occupation nodes into Neo4j from generated occupations.json.

Usage:
    python -m pipeline.industry.loader
"""

import json
import logging
from pathlib import Path
from typing import Optional

from neo4j import Driver
from ontology.schema import get_driver, close_driver
from pipeline.industry.region_maps import COLLEGE_REGION_MAP, OEWS_METRO_TO_COE

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def load_industry(driver: Driver, occupations: list[dict], coe_data: Optional[dict] = None) -> dict:
    """Load Region, Occupation, and relationship data into Neo4j.

    Args:
        driver: Neo4j driver instance.
        occupations: List of occupation dicts from occupations.json.
        coe_data: Optional COE parsed data dict from coe_parsed.json.
                  If provided, enriches DEMANDS edges with growth_rate,
                  annual_openings, and education_level.
    """
    stats = {"regions": 0, "occupations": 0, "demands": 0, "requires_skill": 0, "college_links": 0, "coe_enriched": 0}

    with driver.session() as session:
        # 1. Create Region nodes
        regions = set()
        for occ in occupations:
            regions.update(occ["regions"].keys())

        for region_name in regions:
            session.run("MERGE (r:Region {name: $name})", name=region_name)
            stats["regions"] += 1
        logger.info(f"Created {stats['regions']} Region nodes")

        # 2. Link Colleges to Regions
        for college_name, region_name in COLLEGE_REGION_MAP.items():
            result = session.run(
                """
                MATCH (c:College {name: $college})
                MERGE (r:Region {name: $region})
                MERGE (c)-[:IN_MARKET]->(r)
                RETURN count(*) AS cnt
                """,
                college=college_name,
                region=region_name,
            )
            stats["college_links"] += result.single()["cnt"]
        logger.info(f"Created {stats['college_links']} College-Region links")

        # 3. Create Occupation nodes
        occ_batch = []
        for occ in occupations:
            occ_batch.append({
                "soc_code": occ["soc_code"],
                "title": occ["title"],
                "description": occ["description"],
                "annual_wage": occ["annual_wage"],
            })
            if len(occ_batch) >= BATCH_SIZE:
                _create_occupations(session, occ_batch)
                stats["occupations"] += len(occ_batch)
                occ_batch = []
        if occ_batch:
            _create_occupations(session, occ_batch)
            stats["occupations"] += len(occ_batch)
        logger.info(f"Created {stats['occupations']} Occupation nodes")

        # 4. Create Region -[:DEMANDS]-> Occupation
        demand_batch = []
        for occ in occupations:
            for region_name, employment in occ["regions"].items():
                demand_batch.append({
                    "soc_code": occ["soc_code"],
                    "region": region_name,
                    "employment": employment,
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
            for skill_name in occ["skills"]:
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

        # 6. Enrich DEMANDS edges with COE demand projections
        if coe_data:
            coe_occs = coe_data.get("occupations", {})
            enrich_batch = []

            for occ in occupations:
                soc = occ["soc_code"]
                coe_occ = coe_occs.get(soc)
                if not coe_occ:
                    continue

                for region_name in occ["regions"]:
                    coe_region = OEWS_METRO_TO_COE.get(region_name)
                    if not coe_region:
                        continue
                    coe_region_data = coe_occ["regions"].get(coe_region)
                    if not coe_region_data:
                        # Fall back to statewide
                        coe_region_data = coe_occ["regions"].get("CA")
                    if not coe_region_data:
                        continue

                    enrich_batch.append({
                        "soc_code": soc,
                        "region": region_name,
                        "growth_rate": coe_region_data.get("growth_rate"),
                        "annual_openings": coe_region_data.get("annual_openings"),
                        "education_level": coe_occ.get("education_level"),
                    })

                    if len(enrich_batch) >= BATCH_SIZE:
                        _enrich_demands(session, enrich_batch)
                        stats["coe_enriched"] += len(enrich_batch)
                        enrich_batch = []

            if enrich_batch:
                _enrich_demands(session, enrich_batch)
                stats["coe_enriched"] += len(enrich_batch)
            logger.info(f"Enriched {stats['coe_enriched']} DEMANDS edges with COE data")

    return stats


def _create_occupations(session, batch: list[dict]):
    session.run(
        """
        UNWIND $batch AS row
        MERGE (o:Occupation {soc_code: row.soc_code})
        SET o.title = row.title,
            o.description = row.description,
            o.annual_wage = row.annual_wage
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
        SET d.employment = row.employment
        """,
        batch=batch,
    )


def _enrich_demands(session, batch: list[dict]):
    """Add COE demand projections to existing DEMANDS edges."""
    session.run(
        """
        UNWIND $batch AS row
        MATCH (r:Region {name: row.region})-[d:DEMANDS]->(o:Occupation {soc_code: row.soc_code})
        SET d.growth_rate = row.growth_rate,
            d.annual_openings = row.annual_openings,
            d.education_level = row.education_level
        """,
        batch=batch,
    )


def _create_requires_skill(session, batch: list[dict]) -> int:
    result = session.run(
        """
        UNWIND $batch AS row
        MATCH (o:Occupation {soc_code: row.soc_code})
        MATCH (s:Skill {name: row.skill})
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

    # Load COE data if available
    coe_path = Path(__file__).parent / "coe_parsed.json"
    coe_data = None
    if coe_path.exists():
        with open(coe_path) as f:
            coe_data = json.load(f)
        logger.info(f"Loaded COE data: {len(coe_data.get('occupations', {}))} occupations")

    logger.info(f"Loading {len(occupations)} occupations into Neo4j")

    driver = get_driver()
    try:
        stats = load_industry(driver, occupations, coe_data=coe_data)
        logger.info(f"\nComplete: {stats}")
    finally:
        close_driver()
