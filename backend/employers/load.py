"""
Load Employer nodes into Neo4j from employers.json.

Strict-quality contract (per the "no imperfect data shipped" principle):
    - An employer is loaded if and only if either:
        (a) `enrichment_attempted=True AND identity_verified=True` — the
            employer has been through the enrichment pipeline and produced
            verified, descriptive, accurately-classified data; OR
        (b) `enrichment_attempted` is absent — the employer has never been
            through the new pipeline (legacy baseline). Preserved as-is so
            regions not yet enriched keep their existing atlas presence.

    - An employer is excluded (and actively pruned from Neo4j if previously
      loaded) if `enrichment_attempted=True AND identity_verified is not True`.
      These are deferred employers — re-running enrich.py later may convert
      them to verified, at which point they re-enter the loadable set.

This breaks the "ship imperfect data and rely on probabilistic convergence"
pattern: nothing reaches the atlas until it's been deterministically verified
and enriched.

Usage:
    python -m employers.load
"""

import json
import logging
from pathlib import Path

from neo4j import Driver
from ontology.schema import get_driver, close_driver

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def _is_loadable(emp: dict) -> bool:
    """Strict filter for the no-imperfect-data principle.

    An employer is loadable if and only if:
      - Never attempted (legacy baseline, before this region was enriched), OR
      - Attempted AND identity_verified AND fully promoted by cutover
        (enrichment_promoted=True). The cutover step sets that flag only
        when ALL three shadow fields (_description, _occupations, _swp_sector)
        were present and successfully copied to the canonical fields.

    A verified employer with a partial enrichment outcome (e.g., description
    set but occupations missing) lacks `enrichment_promoted` — its canonical
    fields would still hold pre-enrichment legacy data, which would
    contradict the no-imperfect-data principle. Such employers are excluded
    and pruned from Neo4j until the next enrichment run produces the
    missing field.
    """
    if not emp.get("enrichment_attempted"):
        return True  # legacy baseline preserved
    if not emp.get("identity_verified"):
        return False
    return emp.get("enrichment_promoted") is True


def cleanup_stale_employers(driver: Driver, all_employers: list[dict]) -> int:
    """DETACH DELETE Neo4j Employer nodes that should not be present.

    Removes:
      - Orphans (in Neo4j but not in employers.json at all)
      - Deferred employers (enrichment_attempted=True without identity_verified)
        — these were possibly loaded under old data; remove until reverified.

    Preserves:
      - Verified employers (loaded with new data this run)
      - Legacy employers (enrichment_attempted absent — regions not yet enriched)
    """
    loadable_names = [e["name"] for e in all_employers if _is_loadable(e)]
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Employer) WHERE NOT e.name IN $names DETACH DELETE e RETURN count(e) AS cnt",
            names=loadable_names,
        )
        deleted = result.single()["cnt"]
    if deleted:
        logger.info(f"Cleaned up {deleted} stale or unverified Employer nodes")
    return deleted


def prune_region_in_market(
    driver: Driver,
    region_code: str,
    valid_employer_names: list[str],
) -> int:
    """Delete stale IN_MARKET edges for a region without touching other regions.

    When a regional re-scrape produces a new employer pool, some employers
    that were previously tagged with this region may no longer be in the
    pool. cleanup_stale_employers only removes stale nodes; this function
    removes stale edges so that employers which lost a region tag don't
    retain orphaned IN_MARKET edges in the graph.
    """
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Employer)-[r:IN_MARKET]->(reg:Region {name: $region}) "
            "WHERE NOT e.name IN $names DELETE r RETURN count(r) AS cnt",
            region=region_code,
            names=valid_employer_names,
        )
        pruned = result.single()["cnt"]
    if pruned:
        logger.info(f"Pruned {pruned} stale IN_MARKET edges for region {region_code}")
    return pruned


def load_employers(driver: Driver, employers: list[dict]) -> dict:
    """Load Employer nodes and relationships into Neo4j.

    Iterates only the loadable subset (per `_is_loadable`). Deferred
    employers in employers.json are silently skipped — their removal
    from Neo4j happens via `cleanup_stale_employers`.
    """
    employers = [e for e in employers if _is_loadable(e)]
    stats = {"employers": 0, "in_market": 0, "hires_for": 0, "skipped_deferred": 0}

    with driver.session() as session:
        # Create Employer nodes
        for emp in employers:
            session.run(
                "MERGE (e:Employer {name: $name}) "
                "SET e.sector = $sector, e.description = $description, "
                "    e.website = $website, e.swp_sectors = $swp_sectors",
                name=emp["name"],
                sector=emp["sector"],
                description=emp.get("description"),
                website=emp.get("website"),
                swp_sectors=emp.get("swp_sectors", []),
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

    loadable = [e for e in employers if _is_loadable(e)]
    deferred = [
        e for e in employers
        if e.get("enrichment_attempted") and not e.get("identity_verified")
    ]
    logger.info(
        f"Loading {len(loadable)} of {len(employers)} employers into Neo4j "
        f"(skipping {len(deferred)} deferred unverified)"
    )

    driver = get_driver()
    try:
        cleanup_stale_employers(driver, employers)
        stats = load_employers(driver, employers)
        logger.info(f"\nComplete: {stats}")
    finally:
        close_driver()
