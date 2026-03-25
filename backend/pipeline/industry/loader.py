"""
Load Region and Occupation nodes into Neo4j from generated occupations.json.

Usage:
    python -m pipeline.industry.loader
"""

import json
import logging
from pathlib import Path

from neo4j import Driver
from ontology.schema import get_driver, close_driver

logger = logging.getLogger(__name__)

BATCH_SIZE = 500

# College key → Region name
COLLEGE_REGION_MAP = {
    "Foothill College": "San Jose-Sunnyvale-Santa Clara",
    "De Anza College": "San Jose-Sunnyvale-Santa Clara",
    "Mission College": "San Jose-Sunnyvale-Santa Clara",
    "Evergreen Valley College": "San Jose-Sunnyvale-Santa Clara",
    "San Jose City College": "San Jose-Sunnyvale-Santa Clara",
    "West Valley College": "San Jose-Sunnyvale-Santa Clara",
    "Gavilan College": "San Jose-Sunnyvale-Santa Clara",
    "Laney College": "Oakland-Fremont-Berkeley",
    "Merritt College": "Oakland-Fremont-Berkeley",
    "College of Alameda": "Oakland-Fremont-Berkeley",
    "Berkeley City College": "Oakland-Fremont-Berkeley",
    "Chabot College": "Oakland-Fremont-Berkeley",
    "Ohlone College": "Oakland-Fremont-Berkeley",
    "Las Positas College": "Oakland-Fremont-Berkeley",
    "Diablo Valley College": "Oakland-Fremont-Berkeley",
    "Los Medanos College": "Oakland-Fremont-Berkeley",
    "Contra Costa College": "Oakland-Fremont-Berkeley",
    "City College of San Francisco": "San Francisco-San Mateo-Redwood City",
    "Cañada College": "San Francisco-San Mateo-Redwood City",
    "College of San Mateo": "San Francisco-San Mateo-Redwood City",
    "Skyline College": "San Francisco-San Mateo-Redwood City",
    "Santa Rosa Junior College": "Santa Rosa-Petaluma",
    "Napa Valley College": "Napa",
    "Solano Community College": "Vallejo",
    "Cabrillo College": "Santa Cruz-Watsonville",
    "College of Marin": "San Rafael",
}


def load_industry(driver: Driver, occupations: list[dict]) -> dict:
    """Load Region, Occupation, and relationship data into Neo4j."""
    stats = {"regions": 0, "occupations": 0, "demands": 0, "requires_skill": 0, "college_links": 0}

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

    logger.info(f"Loading {len(occupations)} occupations into Neo4j")

    driver = get_driver()
    try:
        stats = load_industry(driver, occupations)
        logger.info(f"\nComplete: {stats}")
    finally:
        close_driver()
