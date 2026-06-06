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
from ontology.oes import oes_socs_for_naics4
from employers.edd_scrape import CTE_NAICS_CODES

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def _load_geocode_cache() -> dict:
    """emp_id -> geocoded {lat, lng} from the decoupled cache
    (employers/geocode_cache.json, produced by geocode.py). Kept separate from
    employers.json so it survives pipeline regeneration; joined back here by the
    stable EDD emp_id. Absent ⇒ employers load without coords and simply don't
    appear on the employer map."""
    path = Path(__file__).resolve().parent / "geocode_cache.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _sector_tags_for_naics(naics4: str | None) -> list[str]:
    """Deterministic NAICS-4 → SWP sector lookup. Returns [] if NAICS-4
    is missing or not in CTE_NAICS_CODES (employer falls outside the
    project's curated CTE search space)."""
    if not naics4: return []
    entry = CTE_NAICS_CODES.get(naics4)
    if not entry: return []
    return list(entry[2])


def _oes_socs_with_pct(naics4: str | None) -> list[tuple[str, float]]:
    """OEWS-derived (SOC, pct_total) pairs for an employer's NAICS-4.
    Pre-filtered to pct_total > 0 since zero-pct entries don't carry
    workforce-composition signal."""
    if not naics4: return []
    return [
        (r["soc"], r.get("pct_total") or 0.0)
        for r in oes_socs_for_naics4(naics4)
        if (r.get("pct_total") or 0.0) > 0
    ]


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
    geo_cache = _load_geocode_cache()
    stats = {
        "employers": 0, "in_market": 0,
        "hires_for": 0, "identity_hires_for": 0,
        "skipped_deferred": 0,
    }

    with driver.session() as session:
        # Create Employer nodes
        # swp_sectors is now derived deterministically from NAICS-4 via
        # the project-curated CTE_NAICS_CODES lookup (replacing the
        # prior LLM identity classification). Multi-sector membership is
        # natural and preserved when a NAICS legitimately spans sectors.
        for emp in employers:
            naics4 = emp.get("naics4")
            sector_tags = _sector_tags_for_naics(naics4)
            geo = geo_cache.get((emp.get("address") or {}).get("emp_id") or "") or {}
            session.run(
                "MERGE (e:Employer {name: $name}) "
                "SET e.sector = $sector, e.description = $description, "
                "    e.website = $website, e.swp_sectors = $swp_sectors, "
                "    e.naics4 = $naics4, "
                "    e.operations_summary = $operations_summary, "
                "    e.lat = $lat, e.lng = $lng",
                name=emp["name"],
                sector=emp["sector"],
                description=emp.get("description"),
                website=emp.get("website"),
                swp_sectors=sector_tags,
                naics4=naics4,
                operations_summary=emp.get("operations_summary"),
                lat=geo.get("lat"),
                lng=geo.get("lng"),
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

        # Create Employer -[:HIRES_FOR]-> Occupation (NAICS-OEWS-derived)
        #
        # The HIRES_FOR linkage is now derived deterministically from the
        # BLS OEWS Industry-Occupation Matrix. For each employer, every
        # SOC that BLS publishes at >0% pct_total in the employer's
        # NAICS-4 becomes a HIRES_FOR edge. The pct_total is persisted
        # as an edge property so per-SOC partnership-candidate lists can
        # be sorted by industry-occupation workforce share.
        #
        # The prior LLM-curated 5-SOC-per-employer picks are preserved
        # as IDENTITY_HIRES_FOR edges (overlay), keeping the identity
        # signal available without making it the primary inclusion rule.
        #
        # Symmetric semantics: prune stale edges of both types before
        # MERGEing new ones, so the graph matches the current state
        # exactly without legacy residue.
        # UNWIND-batched edge writes — one Cypher per employer per edge type
        # rather than per-edge MERGE in a Python loop. The naive per-edge
        # pattern issued ~283K Cypher round trips for a full reload (~136 OEWS
        # SOCs × ~2,085 employers), which OOM-killed the load on the prod
        # e2-medium VM (4GB RAM, ~1.5GB to neo4j, the rest exhausted by
        # accumulated transaction state). UNWIND collapses each employer's
        # edges into a single transaction (~2,085 Cyphers per edge type),
        # cutting both round-trip overhead and per-edge transaction memory.
        pruned_hires_for = 0
        pruned_identity = 0
        for emp in employers:
            naics4 = emp.get("naics4")
            oes_pairs = _oes_socs_with_pct(naics4)
            oes_socs = [s for s, _ in oes_pairs]

            # Prune stale HIRES_FOR not in current OEWS-derived set
            result = session.run(
                """
                MATCH (e:Employer {name: $name})-[r:HIRES_FOR]->(o:Occupation)
                WHERE NOT o.soc_code IN $valid_socs
                DELETE r RETURN count(r) AS cnt
                """,
                name=emp["name"], valid_socs=oes_socs,
            )
            pruned_hires_for += result.single()["cnt"]

            # Write HIRES_FOR with pct_total property — UNWIND-batched
            if oes_pairs:
                result = session.run(
                    """
                    MATCH (e:Employer {name: $name})
                    UNWIND $pairs AS pair
                    MATCH (o:Occupation {soc_code: pair.soc})
                    MERGE (e)-[r:HIRES_FOR]->(o)
                    SET r.pct_total = pair.pct
                    RETURN count(r) AS cnt
                    """,
                    name=emp["name"],
                    pairs=[{"soc": s, "pct": p} for s, p in oes_pairs],
                )
                stats["hires_for"] += result.single()["cnt"]

            # IDENTITY_HIRES_FOR overlay (LLM-curated picks, ~5 per employer)
            identity_socs = list(emp.get("occupations") or [])
            result = session.run(
                """
                MATCH (e:Employer {name: $name})-[r:IDENTITY_HIRES_FOR]->(o:Occupation)
                WHERE NOT o.soc_code IN $valid_socs
                DELETE r RETURN count(r) AS cnt
                """,
                name=emp["name"], valid_socs=identity_socs,
            )
            pruned_identity += result.single()["cnt"]
            if identity_socs:
                result = session.run(
                    """
                    MATCH (e:Employer {name: $name})
                    UNWIND $socs AS soc
                    MATCH (o:Occupation {soc_code: soc})
                    MERGE (e)-[:IDENTITY_HIRES_FOR]->(o)
                    RETURN count(*) AS cnt
                    """,
                    name=emp["name"], socs=identity_socs,
                )
                stats["identity_hires_for"] += result.single()["cnt"]

        if pruned_hires_for:
            logger.info(f"Pruned {pruned_hires_for} stale HIRES_FOR edges")
        if pruned_identity:
            logger.info(f"Pruned {pruned_identity} stale IDENTITY_HIRES_FOR edges")
        stats["hires_for_pruned"] = pruned_hires_for
        stats["identity_hires_for_pruned"] = pruned_identity
        logger.info(
            f"Created/refreshed {stats['hires_for']} HIRES_FOR edges "
            f"(NAICS-OEWS-derived) and {stats['identity_hires_for']} "
            f"IDENTITY_HIRES_FOR edges (LLM-curated overlay)"
        )

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
