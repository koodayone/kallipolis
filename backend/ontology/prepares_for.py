"""
Materialize Course -[:PREPARES_FOR {via_top}]-> Occupation edges.

The institutional crosswalk TOP6 → CIP → SOC (composed in
ontology/crosswalks.py) connects each Chancellor's-Office TOP6 program
classification to the federal SOC occupations that program prepares
students for. Until this module, that crosswalk lived in memory only —
computed at ingestion time, used to filter which occupations to load,
then discarded. The graph carried no edge that answered the partnership
gating question "which courses at this college prepare students for this
occupation?"; partnership queries fell back to skills-overlap matching,
which produces cross-domain false positives (nursing students surfaced
under a manufacturing partnership being the canonical failure).

This module materializes the crosswalk as graph edges. Each Course's
top_code property maps via the in-memory crosswalk to a set of SOC
codes; for each (Course, Occupation) pair, a PREPARES_FOR edge is
written with the mediating TOP6 stored as a `via_top` property for
audit. Department→Occupation reachability falls out of the topology
(Department-[:CONTAINS]->Course-[:PREPARES_FOR]->Occupation) without
needing Department→TOP edges.

Idempotent: re-running drops this college's existing PREPARES_FOR edges
and re-derives them from the current top_code state, so changes in MCF
assignments propagate cleanly.
"""

from __future__ import annotations

import logging

from neo4j import Driver

from ontology.crosswalks import top6_to_soc

logger = logging.getLogger(__name__)


def materialize_prepares_for(driver: Driver, college: str) -> dict:
    """Write Course-[:PREPARES_FOR {via_top}]->Occupation edges for one college.

    Reads the distinct top_code values from this college's Course nodes,
    composes the TOP6→SOC crosswalk via ontology.crosswalks.top6_to_soc,
    and writes one edge per (course, occupation) pair where both nodes
    exist in the graph. Existing PREPARES_FOR edges for this college's
    courses are dropped first to keep the materialization idempotent.

    The Occupation node must already exist (created by occupations/load.py
    from the COE-curated occupations.json). When an Occupation is missing
    for a SOC the crosswalk yields, the pair is silently skipped — the
    institutional CTE filter applied at occupation load time legitimately
    excludes some SOCs, and the graph should reflect what's loaded.

    Returns: {edges_dropped, edges_created, courses_with_top, top_codes,
              soc_codes_in_crosswalk, edges_skipped_missing_occupation}
    """
    stats = {
        "edges_dropped": 0,
        "edges_created": 0,
        "courses_with_top": 0,
        "top_codes": 0,
        "soc_codes_in_crosswalk": 0,
        "edges_skipped_missing_occupation": 0,
    }

    with driver.session() as session:
        # 1. Drop existing PREPARES_FOR edges for this college's courses.
        # Idempotency: if a course's top_code changes (or is removed)
        # between runs, the edge set rebuilds cleanly.
        result = session.run(
            """
            MATCH (c:Course {college: $college})-[r:PREPARES_FOR]->(:Occupation)
            DELETE r
            RETURN count(r) AS n
            """,
            college=college,
        ).single()
        stats["edges_dropped"] = result["n"] if result else 0

        # 2. Collect distinct top_code values from this college's courses.
        rows = session.run(
            """
            MATCH (c:Course {college: $college})
            WHERE c.top_code IS NOT NULL AND c.top_code <> ''
            RETURN DISTINCT c.top_code AS top_code,
                   count(c) AS course_count
            """,
            college=college,
        ).data()
        stats["courses_with_top"] = sum(r["course_count"] for r in rows)
        stats["top_codes"] = len(rows)
        top_codes = [r["top_code"] for r in rows]

        if not top_codes:
            logger.warning(
                f"materialize_prepares_for({college}): no Course nodes with "
                f"top_code property; pipeline order may be wrong (run "
                f"load_college before this step)"
            )
            return stats

        # 3. Compose the TOP6 → SOC crosswalk for this college's TOP set.
        # Pairs are flattened to (top_code, soc_code) tuples for batch
        # ingestion. Many-to-many is preserved natively — one TOP can
        # crosswalk to multiple SOCs and vice versa.
        top_soc_map = top6_to_soc(top_codes)
        pairs = [
            {"top_code": t, "soc_code": s}
            for t, socs in top_soc_map.items()
            for s in socs
        ]
        stats["soc_codes_in_crosswalk"] = len({p["soc_code"] for p in pairs})

        if not pairs:
            logger.info(
                f"materialize_prepares_for({college}): no TOP6 codes have "
                f"crosswalk entries; zero edges written"
            )
            return stats

        # 4. Pre-flight: count SOC codes that have no Occupation node, so
        # the stats faithfully report the gap between crosswalk reach and
        # graph presence. Useful for diagnosing CTE-filter sparseness.
        soc_in_pairs = list({p["soc_code"] for p in pairs})
        present = session.run(
            """
            MATCH (occ:Occupation)
            WHERE occ.soc_code IN $socs
            RETURN occ.soc_code AS soc_code
            """,
            socs=soc_in_pairs,
        ).data()
        present_set = {r["soc_code"] for r in present}
        missing_socs = set(soc_in_pairs) - present_set
        if missing_socs:
            stats["edges_skipped_missing_occupation"] = sum(
                1 for p in pairs if p["soc_code"] in missing_socs
            )

        # 5. Write edges. The MATCH on Occupation ensures only pairs whose
        # Occupation exists in the graph create edges — no CREATE for
        # missing nodes; the institutional CTE filter is honored.
        result = session.run(
            """
            UNWIND $pairs AS p
            MATCH (c:Course {college: $college, top_code: p.top_code})
            MATCH (occ:Occupation {soc_code: p.soc_code})
            MERGE (c)-[r:PREPARES_FOR]->(occ)
            SET r.via_top = p.top_code
            RETURN count(r) AS n
            """,
            college=college,
            pairs=pairs,
        ).single()
        stats["edges_created"] = result["n"] if result else 0

    logger.info(
        f"materialize_prepares_for({college}): "
        f"{stats['edges_created']} PREPARES_FOR edges written across "
        f"{stats['top_codes']} TOP codes "
        f"({stats['edges_skipped_missing_occupation']} pairs skipped: "
        f"Occupation not in graph; "
        f"{stats['edges_dropped']} stale edges cleared)"
    )
    return stats
