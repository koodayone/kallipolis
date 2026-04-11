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
    writes a single edge carrying seven properties:
      - aligned_skills: skill names the employer requires AND the college
        develops via its course catalog
      - gap_skills: skill names the employer requires but the college does
        not develop
      - alignment_score / gap_count: sizes of the above two lists
      - top_occupation / top_wage: the employer's highest-wage occupation
        in any shared region
      - pipeline_size: count of students at the college with ≥3 matching
        skills for this employer's occupations

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

            # Single round trip: UNWIND the per-employer rows and MERGE each edge.
            session.run("""
                UNWIND $rows AS row
                MATCH (col:College {name: $college})
                MATCH (emp:Employer {name: row.employer})
                MERGE (col)-[pa:PARTNERSHIP_ALIGNMENT]->(emp)
                SET pa.aligned_skills = row.aligned_skills,
                    pa.gap_skills = row.gap_skills,
                    pa.alignment_score = row.alignment_score,
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
    """Gather the per-employer alignment data for one college.

    Uses three focused queries rather than one monolithic traversal so
    each piece is independently readable and the row assembly happens in
    Python. Returns a list of dicts ready to UNWIND into a batched MERGE.
    """
    # Aligned and gap skill sets per employer.
    alignment_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
        MATCH (emp)-[:HIRES_FOR]->(:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
        OPTIONAL MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk)
        WITH emp, sk, count(DISTINCT c) AS dev_count
        WITH emp,
             collect(DISTINCT CASE WHEN dev_count > 0 THEN sk.name END) AS aligned_raw,
             collect(DISTINCT CASE WHEN dev_count = 0 THEN sk.name END) AS gap_raw
        RETURN emp.name AS employer,
               [s IN aligned_raw WHERE s IS NOT NULL] AS aligned_skills,
               [s IN gap_raw WHERE s IS NOT NULL] AS gap_skills
    """, college=college).data()

    if not alignment_data:
        return []

    # Top-wage occupation per employer in shared regions.
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

    # Pipeline size per employer (students with ≥3 matching core skills).
    pipeline_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
              -[:HIRES_FOR]->(:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
              <-[:HAS_SKILL]-(st:Student)
        WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
        WITH emp, st, count(DISTINCT sk) AS matching_skills
        WHERE matching_skills >= 3
        RETURN emp.name AS employer, count(DISTINCT st) AS pipeline_size
    """, college=college).data()
    pipeline_map = {r["employer"]: r["pipeline_size"] for r in pipeline_data}

    rows: list[dict] = []
    for row in alignment_data:
        emp = row["employer"]
        aligned = row["aligned_skills"] or []
        gap = row["gap_skills"] or []
        top_title, top_wage = top_map.get(emp, (None, None))
        rows.append({
            "employer": emp,
            "aligned_skills": aligned,
            "gap_skills": gap,
            "alignment_score": len(aligned),
            "gap_count": len(gap),
            "top_occupation": top_title,
            "top_wage": top_wage,
            "pipeline_size": pipeline_map.get(emp, 0),
        })

    return rows
