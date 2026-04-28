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
    """Gather the per-employer alignment data for one college, ranked
    on institutional curriculum-depth at the (college × employer's
    hires SOCs) intersection.

    Per the institutional-deference architectural commitment:
      - alignment_score is the count of this college's courses with a
        PREPARES_FOR edge to ANY of this employer's hires SOCs. The
        PREPARES_FOR edge is materialized from the Chancellor's Office
        TOP-CIP crosswalk and the BLS/NCES CIP-SOC crosswalk; the
        ranking is institutional, not skills-derived.
      - gap_count is the count of this employer's hires SOCs that the
        college has zero institutionally-aligned curriculum for. A
        higher gap_count signals an institutional curriculum gap, not
        a skill gap.
      - aligned_skills and gap_skills remain on the edge as
        characterization (which competencies the institutionally-
        aligned course set develops, and which competencies the
        employer's required-skill universe still asks for that the
        aligned set does not develop). They no longer drive the rank.

    Three focused queries; row assembly in Python. Returns a list of
    dicts ready to UNWIND into a batched MERGE.
    """
    # Institutional alignment per employer: count courses at this
    # college whose PREPARES_FOR edge points at any of this employer's
    # hires SOCs in shared regions, and the SOCs the college has no
    # aligned curriculum for.
    alignment_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
        MATCH (emp)-[:HIRES_FOR]->(occ:Occupation)
        OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
        WITH emp, occ, count(DISTINCT course) AS course_count, collect(DISTINCT course) AS courses
        WITH emp,
             sum(course_count) AS alignment_score,
             sum(CASE WHEN course_count = 0 THEN 1 ELSE 0 END) AS gap_count,
             apoc.coll.toSet(apoc.coll.flatten(collect(courses))) AS aligned_courses_raw
        RETURN emp.name AS employer,
               alignment_score,
               gap_count,
               aligned_courses_raw
    """, college=college).data() if _has_apoc(session) else _build_alignment_rows_no_apoc(session, college)

    if not alignment_data:
        return []

    # Characterization: aligned_skills (skills the
    # institutionally-aligned courses develop) and gap_skills (skills
    # the employer's hires require that the aligned course set does
    # not develop). These are no longer the basis of ranking; they
    # describe what the institutionally-aligned curriculum teaches
    # and where the competency profile leaves a residual gap.
    skills_data = session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
        OPTIONAL MATCH (emp)-[:HIRES_FOR]->(occ:Occupation)
        OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
        OPTIONAL MATCH (course)-[:DEVELOPS]->(asg:Skill)
        OPTIONAL MATCH (occ)-[:REQUIRES_SKILL]->(req:Skill)
        WITH emp,
             collect(DISTINCT asg.name) AS aligned_raw,
             collect(DISTINCT req.name) AS required_raw
        RETURN emp.name AS employer,
               [s IN aligned_raw WHERE s IS NOT NULL] AS aligned_skills,
               [s IN required_raw WHERE s IS NOT NULL AND NOT s IN aligned_raw] AS gap_skills
    """, college=college).data()
    skills_map = {
        r["employer"]: (r["aligned_skills"] or [], r["gap_skills"] or [])
        for r in skills_data
    }

    # Top-wage occupation per employer in shared regions (unchanged —
    # institutional COE wage data, already deterministic).
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
    # this employer's hires SOCs. Mirrors the per-proposal student-
    # pipeline gate (gather.py::_gather_student_pipeline) which is
    # department-membership-based, not skill-overlap-based.
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
        aligned, gap = skills_map.get(emp, ([], []))
        top_title, top_wage = top_map.get(emp, (None, None))
        rows.append({
            "employer": emp,
            "aligned_skills": aligned,
            "gap_skills": gap,
            "alignment_score": row["alignment_score"] or 0,
            "gap_count": row["gap_count"] or 0,
            "top_occupation": top_title,
            "top_wage": top_wage,
            "pipeline_size": pipeline_map.get(emp, 0),
        })

    return rows


def _has_apoc(session) -> bool:
    """Detect whether APOC is available; fall back to a no-APOC path
    if not. APOC is bundled with neo4j 5.x community edition by default
    but is occasionally absent in custom builds; guarding the fallback
    means this surface degrades gracefully without a hard dependency."""
    try:
        session.run("RETURN apoc.version() AS v").single()
        return True
    except Exception:
        return False


def _build_alignment_rows_no_apoc(session, college: str) -> list[dict]:
    """APOC-free fallback for the alignment query. Same semantics as the
    APOC-enabled path, just without the flatten/toSet helpers — the
    aligned_courses_raw column is dropped (downstream code doesn't use
    it; it was a debug aid in early development). The institutional
    ranking signals (alignment_score, gap_count) are unaffected."""
    return session.run("""
        MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
        MATCH (emp)-[:HIRES_FOR]->(occ:Occupation)
        OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
        WITH emp, occ, count(DISTINCT course) AS course_count
        WITH emp,
             sum(course_count) AS alignment_score,
             sum(CASE WHEN course_count = 0 THEN 1 ELSE 0 END) AS gap_count
        RETURN emp.name AS employer,
               alignment_score,
               gap_count,
               [] AS aligned_courses_raw
    """, college=college).data()
