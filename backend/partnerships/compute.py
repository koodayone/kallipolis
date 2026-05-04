"""Precompute PARTNERSHIP_ALIGNMENT edges.

The partnership landscape view in the atlas needs to return every employer
in a college's region ranked by alignment score, gap count, and student
pipeline size. Computing that at request time is O(employers × occupations
× skills × students) per college and took 30+ seconds for a populated
region. The fix is to materialize the answer onto a `PARTNERSHIP_ALIGNMENT`
edge at ingestion time and have the read endpoint return precomputed
properties directly.

This module owns that materialization. It runs after industry and student
data have both been loaded (so the pipeline metrics exist) and before any
partnership landscape queries are served. The edge schema is documented
in docs/architecture/graph-model.md under "The precomputed analytical edge".
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def precompute_partnership_alignment(driver, college_names: list[str] | None = None) -> dict[str, int]:
    """Materialize `PARTNERSHIP_ALIGNMENT` edges for the given colleges.

    For each (College, Employer) pair where the two share a region, this
    writes a single edge carrying five properties:
      - alignment_score: count of this college's courses that PREPARES_FOR
        any of the employer's hires SOCs (institutional crosswalk depth)
      - gap_count: count of the employer's hires SOCs the college has zero
        institutionally-aligned curriculum for
      - top_occupation / top_wage: the employer's highest-wage occupation
        in any shared region
      - pipeline_size: count of students at the college whose primary_focus
        is in an aligned department

    Stale edges are cleared per-college before recomputation so that
    employers removed from a region do not leave dangling alignments.

    Args:
        driver: Neo4j driver instance.
        college_names: College names to recompute for, or None to run over
            every College node currently in the graph.

    Returns:
        Dict with counts: {"colleges": N, "edges": M}.
    """
    counts = {"colleges": 0, "edges": 0}

    with driver.session() as session:
        if college_names is None:
            result = session.run("MATCH (c:College) RETURN c.name AS name ORDER BY name").data()
            college_names = [r["name"] for r in result]

        for college in college_names:
            rows = _build_alignment_rows(session, college)

            # Clear stale edges so employers removed from a region don't linger.
            session.run("""
                MATCH (col:College {name: $college})-[pa:PARTNERSHIP_ALIGNMENT]->(:Employer)
                DELETE pa
            """, college=college)

            if not rows:
                logger.info(f"  {college}: no employers in shared regions, no alignment edges written")
                continue

            session.run("""
                UNWIND $rows AS row
                MATCH (col:College {name: $college})
                MATCH (emp:Employer {name: row.employer})
                MERGE (col)-[pa:PARTNERSHIP_ALIGNMENT]->(emp)
                SET pa.alignment_score = row.alignment_score,
                    pa.gap_count = row.gap_count,
                    pa.top_occupation = row.top_occupation,
                    pa.top_wage = row.top_wage,
                    pa.pipeline_size = row.pipeline_size
            """, college=college, rows=rows)

            counts["colleges"] += 1
            counts["edges"] += len(rows)
            logger.info(f"  {college}: wrote {len(rows)} PARTNERSHIP_ALIGNMENT edges")

    return counts


def _build_alignment_rows(session, college: str) -> list[dict]:
    """Gather the per-employer alignment data for one college, ranked
    on institutional curriculum-depth at the (college × employer's
    hires SOCs) intersection.

    Per the institutional-deference architectural commitment:
      - alignment_score is the count of this college's courses with a
        PREPARES_FOR edge to ANY of this employer's hires SOCs. The
        PREPARES_FOR edge is materialized from the Chancellor's Office
        TOP-CIP crosswalk and the BLS/NCES CIP-SOC crosswalk.
      - gap_count is the count of this employer's hires SOCs that the
        college has zero institutionally-aligned curriculum for. A
        higher gap_count signals an institutional curriculum gap.

    Three focused queries; row assembly in Python.
    """
    alignment_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
        MATCH (emp)-[:HIRES_FOR]->(occ:Occupation)
        OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
        WITH emp, occ, count(DISTINCT course) AS course_count
        WITH emp,
             sum(course_count) AS alignment_score,
             sum(CASE WHEN course_count = 0 THEN 1 ELSE 0 END) AS gap_count
        RETURN emp.name AS employer,
               alignment_score,
               gap_count
    """, college=college).data()

    if not alignment_data:
        return []

    top_occ_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer),
              (emp)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r)
        WITH emp, occ.title AS title, d.annual_wage AS wage
        ORDER BY wage DESC
        RETURN emp.name AS employer,
               head(collect(title)) AS top_occupation,
               head(collect(wage)) AS top_wage
    """, college=college).data()
    top_map = {
        r["employer"]: (r["top_occupation"], r["top_wage"])
        for r in top_occ_data
    }

    # Pipeline size per employer: students whose primary_focus is in a
    # department that has institutionally-aligned curriculum for any of
    # this employer's hires SOCs.
    pipeline_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
              -[:HIRES_FOR]->(occ:Occupation)
        MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
        MATCH (course)<-[:CONTAINS]-(dept:Department)
        WITH emp, collect(DISTINCT dept.name) AS aligned_depts
        OPTIONAL MATCH (st:Student)
        WHERE st.primary_focus IN aligned_depts
          AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
        RETURN emp.name AS employer, count(DISTINCT st) AS pipeline_size
    """, college=college).data()
    pipeline_map = {r["employer"]: r["pipeline_size"] for r in pipeline_data}

    rows: list[dict] = []
    for row in alignment_data:
        emp = row["employer"]
        top_title, top_wage = top_map.get(emp, (None, None))
        rows.append({
            "employer": emp,
            "alignment_score": row["alignment_score"] or 0,
            "gap_count": row["gap_count"] or 0,
            "top_occupation": top_title,
            "top_wage": top_wage,
            "pipeline_size": pipeline_map.get(emp, 0),
        })

    return rows


# ── CLI entry point ──────────────────────────────────────────────────────

def main() -> None:
    """Recompute PARTNERSHIP_ALIGNMENT for every College node in the graph.

    Standalone invocation:
        python -m partnerships.compute

    The pipeline reload entrypoint (`pipeline.reload`) calls
    `precompute_partnership_alignment` directly with a list of college
    display names; this CLI is the manual companion when you want to
    re-materialize PA edges without re-running the full reload (e.g.,
    after a layer 1 migration that rewrote HIRES_FOR edges).
    """
    import logging
    from ontology.schema import close_driver, get_driver

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    driver = get_driver()
    try:
        stats = precompute_partnership_alignment(driver)
        logger.info(f"PARTNERSHIP_ALIGNMENT: {stats['edges']} edges across "
                    f"{stats['colleges']} colleges")
    finally:
        close_driver()


if __name__ == "__main__":
    main()
