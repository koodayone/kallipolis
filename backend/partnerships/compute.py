"""
Materialize College -[:PARTNERSHIP_ALIGNMENT]-> Employer edges.

The /employers/ endpoint ranks employers in a college's region by
curriculum alignment via the institutional TOP-SOC crosswalk: for each
employer, count the courses (and departments) at this college whose
PREPARES_FOR set intersects the employer's HIRES_FOR set.

Computed at request time, that traversal does ~40M DbHits per college
(College → Region → Employer × HIRES_FOR × PREPARES_FOR × CONTAINS),
materializing a multi-million-row cartesian before aggregating. On the
prod e2-medium VM that's 26s for Foothill (Bay region, 311 employers)
and timeouts (>300s) for LA/OC/SD-region colleges (350+ employers).

This module materializes the same alignment as a precomputed edge,
shifting the work to ingestion time. At request time the endpoint is
O(employers in region) — sub-100ms regardless of region size.

Edge properties:
  occupations             list of distinct occupation titles the
                          employer hires for in this college's region.
                          Mirrors the request-time `collect(DISTINCT
                          occ.title)` exactly.
  aligned_course_count    number of distinct courses at this college
                          that PREPARES_FOR any of the employer's
                          hire occupations. The institutional alignment
                          depth — 0 means no curricular pathway exists
                          at this college; higher means deeper coverage.

`aligned_department_count` is intentionally not stored: it appeared in
the legacy edge shape but was never rendered anywhere in the atlas
(checked across EmployersView and the rest of the surface). Materializing
unrendered fields buys no user value and adds work to the compute and
storage cost to the edge. Add it back if a surface starts using it.

Idempotent: re-running drops this college's existing
PARTNERSHIP_ALIGNMENT edges and rebuilds from current state, so changes
in PREPARES_FOR or employer set propagate cleanly. The legacy skill-
based properties (aligned_skills, gap_skills, alignment_score, etc.)
on edges from the old skill-overlap model are dropped along with the
edges and not re-created — Skill nodes were retired with the TOP-SOC
refactor and those properties are no longer meaningful.
"""

from __future__ import annotations

import argparse
import logging

from neo4j import Driver

logger = logging.getLogger(__name__)


def materialize_partnership_alignment(driver: Driver, college: str) -> dict:
    """Drop and rebuild PARTNERSHIP_ALIGNMENT edges out of one college.

    Reads College → Region → Employer → Occupation HIRES_FOR plus
    Course PREPARES_FOR Occupation and Department CONTAINS Course,
    aggregates per (college, employer), writes one edge per employer
    in the college's region. Returns counts for verification.

    Pre-conditions:
      - College, Region, Employer nodes exist (load_industry_data)
      - HIRES_FOR edges exist (load_employers)
      - Course nodes exist with college property (load_courses)
      - PREPARES_FOR edges exist (materialize_prepares_for, called
        from courses/load.py)

    Without those upstream steps the compute writes zero edges (or
    edges with aligned_course_count=0 for employers in region but
    with no curricular alignment). Both are valid outcomes.

    Returns: {edges_dropped, edges_created, employers_with_alignment}

    `employers_with_alignment` counts edges with aligned_course_count>0
    — i.e. employers where the institutional crosswalk establishes at
    least one curricular pathway. Edges are written for every employer
    in the region regardless, so the list view shows them all; the
    count is for diagnostic visibility (a region with very low ratio
    suggests the crosswalk is sparse for that college's TOP set).
    """
    stats = {
        "edges_dropped": 0,
        "edges_created": 0,
        "employers_with_alignment": 0,
    }

    with driver.session() as session:
        # Step 1: drop existing PARTNERSHIP_ALIGNMENT edges out of this
        # college. Idempotency: a re-run gets a clean rebuild from
        # current graph state. Also clears any legacy skill-based
        # properties from the pre-refactor edges.
        result = session.run(
            """
            MATCH (c:College {name: $college})-[pa:PARTNERSHIP_ALIGNMENT]->()
            DELETE pa
            RETURN count(pa) AS n
            """,
            college=college,
        ).single()
        stats["edges_dropped"] = result["n"] if result else 0

        # Step 2: rebuild. Single query per college — Neo4j can keep
        # the (employers in region) working set hot through the
        # aggregation. Using CREATE rather than MERGE because we just
        # deleted; CREATE skips the existence check and avoids the
        # composite-index scan MERGE would do.
        result = session.run(
            """
            MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)
                  <-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)
            OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
            WITH c, emp,
                 collect(DISTINCT occ.title) AS occupations,
                 count(DISTINCT course) AS aligned_course_count
            CREATE (c)-[pa:PARTNERSHIP_ALIGNMENT {
                occupations: occupations,
                aligned_course_count: aligned_course_count
            }]->(emp)
            RETURN count(pa) AS n,
                   sum(CASE WHEN aligned_course_count > 0 THEN 1 ELSE 0 END) AS with_alignment
            """,
            college=college,
        ).single()
        if result:
            stats["edges_created"] = result["n"]
            stats["employers_with_alignment"] = result["with_alignment"]

    logger.info(
        f"materialize_partnership_alignment({college}): "
        f"{stats['edges_created']} edges written "
        f"({stats['employers_with_alignment']} with curricular alignment, "
        f"{stats['edges_dropped']} stale edges cleared)"
    )
    return stats


def _all_colleges(driver: Driver) -> list[str]:
    with driver.session() as s:
        rows = s.run("MATCH (c:College) RETURN c.name AS name ORDER BY c.name").data()
    return [r["name"] for r in rows]


def main():
    """CLI entrypoint for ad-hoc materialization (e.g., on prod after a
    code change that requires fresh edges without a full reload)."""
    parser = argparse.ArgumentParser(
        description="Materialize PARTNERSHIP_ALIGNMENT edges out of a college "
        "(or all colleges).",
    )
    parser.add_argument("--college", help="College name. Omit to process all.")
    parser.add_argument("--all", action="store_true", help="Process every College in graph.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    from ontology.schema import get_driver, close_driver

    driver = get_driver()
    try:
        if args.all or not args.college:
            colleges = _all_colleges(driver)
            logger.info(f"Processing {len(colleges)} colleges")
            for c in colleges:
                materialize_partnership_alignment(driver, c)
        else:
            materialize_partnership_alignment(driver, args.college)
    finally:
        close_driver()


if __name__ == "__main__":
    main()
