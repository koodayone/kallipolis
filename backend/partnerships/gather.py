"""Neo4j data retrieval for partnership opportunity reports — no LLM calls.

Two helpers used by ``opportunity.py``:

    _gather_aligned_curriculum(college, soc_code) -> list[dict]
        Departments and courses at the college that PREPARES_FOR the SOC.

    _gather_student_pipeline(college, departments, soc_code)
        -> tuple[dict, list[dict]]
        Student pipeline counts and the top exemplar students.

Both are scoped to a (college, SOC) pair and gated by the institutional
PREPARES_FOR edge — same pattern the employer-centric proposal flow used
historically. Per the institutional-deference principle: every claim is
derived from edges materialized via the Chancellor's Office TOP-CIP and
BLS/NCES CIP-SOC crosswalks; nothing here is LLM-mediated.
"""

from __future__ import annotations

from collections import defaultdict

from ontology.schema import get_driver


def _gather_aligned_curriculum(
    college: str, soc_code: str
) -> list[dict]:
    """Fetch departments and courses that PREPARES_FOR the selected occupation.

    Per the institutional-deference architectural commitment: the
    pathway claim is established by the institutional crosswalk
    (Course-[:PREPARES_FOR]->Occupation, written from the Chancellor's
    Office TOP-CIP and BLS/NCES CIP-SOC crosswalks). When no
    departments at this college prepare students for the SOC, returns
    [] — caller surfaces this honestly rather than falling back.

    Returns curriculum_evidence_list, with `via_top` and `via_cip` per
    department for downstream institutional-source attribution.
    """
    driver = get_driver()
    with driver.session() as session:
        # The PREPARES_FOR edge carries `via_top` as an audit-trail
        # property — the TOP6 the institutional crosswalk used to
        # mediate this Course→Occupation alignment.
        result = session.run("""
            MATCH (col:College {name: $college})-[:OFFERS]->(dept:Department)
                  -[:CONTAINS]->(c:Course {college: $college})
                  -[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            RETURN dept.name AS department, c.code AS code, c.name AS name,
                   c.description AS description,
                   c.learning_outcomes AS learning_outcomes,
                   c.course_objectives AS course_objectives,
                   c.top_code AS top_code,
                   r.via_top AS via_top
            ORDER BY dept.name, c.code
        """, college=college, soc_code=soc_code).data()

    from ontology.crosswalks import _load_top_to_cip
    top_cip_map = _load_top_to_cip()

    dept_agg: dict[str, dict] = defaultdict(
        lambda: {"courses": [], "via_top": set(), "via_cip": set()}
    )
    for r in result:
        dept = r["department"]
        course_via_top = r.get("via_top")
        course_cips = list(top_cip_map.get(course_via_top, set())) if course_via_top else []
        dept_agg[dept]["courses"].append({
            "code": r["code"],
            "name": r["name"],
            "description": r["description"] or "",
            "learning_outcomes": r["learning_outcomes"] or [],
            "top_code": r.get("top_code"),
        })
        if course_via_top:
            dept_agg[dept]["via_top"].add(course_via_top)
        dept_agg[dept]["via_cip"].update(course_cips)

    return [
        {
            "department": dept,
            "courses": data["courses"],
            "via_top": sorted(data["via_top"]),
            "via_cip": sorted(data["via_cip"]),
        }
        for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["courses"]), reverse=True)
    ]


def _gather_student_pipeline(
    college: str, departments: list[str], soc_code: str
) -> tuple[dict, list[dict]]:
    """Find students whose academic pathway aligns with the partnership.

    The eligibility gate is department membership: a student is
    eligible if their `primary_focus` matches one of the aligned
    departments returned by _gather_aligned_curriculum (themselves
    PREPARES_FOR-gated by the institutional crosswalk). Top-N ranking
    within that eligible set is by SOC-aligned course count then GPA
    — both direct institutional-pathway measures.

    Concretely:
      - Eligibility gate (institutional): student.primary_focus IN
        aligned_departments.
      - Headline count: students with at least one enrollment in any
        aligned department.
      - Top-N exemplars: ranked WITHIN the eligible set by SOC-aligned
        course count, then GPA. Their displayed enrollments are the
        courses they have taken that PREPARES_FOR the selected SOC.

    Returns (student_stats, top_students_with_detail).
    """
    driver = get_driver()

    if not departments:
        return {
            "total_in_program": 0,
            "total_in_aligned_departments": 0,
        }, []

    with driver.session() as session:
        # Broad headline (`total_in_aligned_departments`) reads off the
        # OCCUPATION_PIPELINE edge — it's precomputed by
        # partnerships.compute as `student_count` with the same
        # semantics. Saves ~42ms p50; mostly a consistency win (one
        # source of truth for the aggregate).
        broad = session.run("""
            MATCH (col:College {name: $college})-[op:OCCUPATION_PIPELINE]
                  ->(:Occupation {soc_code: $soc_code})
            RETURN op.student_count AS total_in_aligned_departments
        """, college=college, soc_code=soc_code).single()

        # Secondary count (`total_in_program`) stays a live query.
        # Attempted to precompute it as `student_count_in_program` on
        # the edge, but the natural compute query (
        #   OPTIONAL MATCH (Student) WHERE primary_focus IN aligned_dept_names
        # ) per-row OOM'd Neo4j on the e2-medium because the planner
        # couldn't use the student_primary_focus index when the IN-list
        # varies per occ. The live query at request time CAN use the
        # index (the IN-list is bound to a single $departments param)
        # and runs at 2.2s p50 / 7.4s p95 — slow but stable. Revisit
        # by either looping per-soc in the compute (small targeted
        # queries that each hit the index) or batching by unique
        # dept-set hash. Out of scope for this pass.
        stats = session.run("""
            MATCH (st:Student)
            WHERE st.primary_focus IN $departments
              AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            RETURN count(st) AS total_in_program
        """, college=college, departments=departments).single()

        student_stats = {
            "total_in_program": stats["total_in_program"] if stats else 0,
            "total_in_aligned_departments": (broad["total_in_aligned_departments"] if broad else 0) or 0,
        }

        # Top-10 exemplars from the aligned-department student pool, ranked
        # by SOC-aligned course count (primary) then GPA (secondary). The
        # eligibility gate matches the headline `total_in_aligned_departments`
        # figure: any student enrolled in any course in an aligned
        # department. When SOC-prep enrollments exist, the strongest
        # pipeline candidates surface first; when they don't (some TOP6s
        # have no published MIS enrollment data at some colleges), the
        # ordering falls back to GPA so the table still shows real
        # candidates instead of being empty alongside a non-zero headline.
        #
        # The expansion shows the student's full aligned-department course
        # history — not just SOC-prep courses — so the body is always
        # informative even when the SOC-prep count is zero.
        # Two-pass top-10 to keep the dominant Cypher off the
        # 2,664-student × ~12-enrollments expansion that scales with the
        # college's eligibility-set size. Pass 1 anchors on the
        # Student.primary_focus index — the same set the original
        # query's outer ORDER BY focus_match=1 always ranks first — so
        # whenever ≥10 focus-match students exist (the common case at
        # Oxnard / Foothill / similar), one query produces the
        # canonical top-10. Pass 2 only fires when the focus-match pool
        # is too small to fill 10 slots (rare niche-department case),
        # falling back to the broader eligibility set with the
        # already-returned uuids excluded so the result preserves the
        # original semantics exactly.
        focus_query = """
            MATCH (st:Student) WHERE st.primary_focus IN $departments
            WITH st
            WHERE EXISTS {
                MATCH (st)-[:ENROLLED_IN]->(:Course {college: $college})
                      <-[:CONTAINS]-(d:Department)
                WHERE d.name IN $departments
            }
            OPTIONAL MATCH (st)-[:ENROLLED_IN]->(prep:Course {college: $college})
                  -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WITH st, count(DISTINCT prep) AS soc_aligned_count
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
                  <-[:CONTAINS]-(d:Department)
            WHERE d.name IN $departments
            WITH st, soc_aligned_count,
                 collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
                     code: c.code, name: c.name,
                     grade: e.grade, term: e.term
                 } END) AS raw_enrollments
            WITH st, soc_aligned_count,
                 [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
            ORDER BY soc_aligned_count DESC,
                     size(enrollments) DESC, COALESCE(st.gpa, 0.0) DESC
            LIMIT 10
            RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                   size(enrollments) AS courses_completed,
                   COALESCE(st.gpa, 0.0) AS gpa,
                   enrollments
        """
        result = session.run(
            focus_query,
            college=college, departments=departments, soc_code=soc_code,
        ).data()

        if len(result) < 10:
            fallback_query = """
                MATCH (dept:Department)-[:CONTAINS]->(:Course {college: $college})
                      <-[:ENROLLED_IN]-(st:Student)
                WHERE dept.name IN $departments
                  AND NOT (st.primary_focus IN $departments)
                  AND NOT (st.uuid IN $exclude_uuids)
                WITH DISTINCT st
                OPTIONAL MATCH (st)-[:ENROLLED_IN]->(prep:Course {college: $college})
                      -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
                WITH st, count(DISTINCT prep) AS soc_aligned_count
                OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
                      <-[:CONTAINS]-(d:Department)
                WHERE d.name IN $departments
                WITH st, soc_aligned_count,
                     collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
                         code: c.code, name: c.name,
                         grade: e.grade, term: e.term
                     } END) AS raw_enrollments
                WITH st, soc_aligned_count,
                     [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
                ORDER BY soc_aligned_count DESC,
                         size(enrollments) DESC, COALESCE(st.gpa, 0.0) DESC
                LIMIT $limit
                RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                       size(enrollments) AS courses_completed,
                       COALESCE(st.gpa, 0.0) AS gpa,
                       enrollments
            """
            fallback = session.run(
                fallback_query,
                college=college, departments=departments, soc_code=soc_code,
                exclude_uuids=[r["uuid"] for r in result],
                limit=10 - len(result),
            ).data()
            result = result + fallback

    top_students = [
        {
            "uuid": r["uuid"],
            "display_number": i + 1,
            "primary_focus": r["primary_focus"] or "",
            "courses_completed": r["courses_completed"],
            "gpa": round(r["gpa"], 2),
            "enrollments": [
                {"code": e["code"], "name": e["name"], "grade": e["grade"], "term": e["term"]}
                for e in r["enrollments"]
                if e.get("code")
            ],
        }
        for i, r in enumerate(result)
    ]

    return student_stats, top_students
