"""
Load Employer nodes into Neo4j from employers.json.

Usage:
    python -m pipeline.industry.employers
"""

import json
import logging
from pathlib import Path

from neo4j import Driver
from ontology.schema import get_driver, close_driver

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def cleanup_stale_employers(driver: Driver, valid_names: list[str]) -> int:
    """DETACH DELETE Employer nodes not in the valid set. Returns count deleted."""
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Employer) WHERE NOT e.name IN $names DETACH DELETE e RETURN count(e) AS cnt",
            names=valid_names,
        )
        deleted = result.single()["cnt"]
    if deleted:
        logger.info(f"Cleaned up {deleted} stale Employer nodes")
    return deleted


def load_employers(driver: Driver, employers: list[dict]) -> dict:
    """Load Employer nodes and relationships into Neo4j."""
    stats = {"employers": 0, "in_market": 0, "hires_for": 0}

    with driver.session() as session:
        # Create Employer nodes
        for emp in employers:
            session.run(
                "MERGE (e:Employer {name: $name}) SET e.sector = $sector, e.description = $description, e.website = $website",
                name=emp["name"],
                sector=emp["sector"],
                description=emp.get("description"),
                website=emp.get("website"),
            )
            stats["employers"] += 1

        logger.info(f"Created {stats['employers']} Employer nodes")

        # Create Employer -[:IN_MARKET]-> Region
        for emp in employers:
            for region in emp["regions"]:
                session.run(
                    """
                    MATCH (e:Employer {name: $name})
                    MATCH (r:Region {name: $region})
                    MERGE (e)-[:IN_MARKET]->(r)
                    """,
                    name=emp["name"],
                    region=region,
                )
                stats["in_market"] += 1

        logger.info(f"Created {stats['in_market']} IN_MARKET edges")

        # Create Employer -[:HIRES_FOR]-> Occupation
        for emp in employers:
            for soc in emp["occupations"]:
                result = session.run(
                    """
                    MATCH (e:Employer {name: $name})
                    MATCH (o:Occupation {soc_code: $soc})
                    MERGE (e)-[:HIRES_FOR]->(o)
                    RETURN count(*) AS cnt
                    """,
                    name=emp["name"],
                    soc=soc,
                )
                stats["hires_for"] += result.single()["cnt"]

        logger.info(f"Created {stats['hires_for']} HIRES_FOR edges")

    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data_path = Path(__file__).parent / "employers.json"
    with open(data_path) as f:
        employers = json.load(f)

    logger.info(f"Loading {len(employers)} employers into Neo4j")

    driver = get_driver()
    try:
        cleanup_stale_employers(driver, [e["name"] for e in employers])
        stats = load_employers(driver, employers)
        logger.info(f"\nComplete: {stats}")
    finally:
        close_driver()
