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
        # Broad headline (`total_in_aligned_departments`) reads from the
        # OCCUPATION_PIPELINE edge precomputed by partnerships.compute
        # as `student_count` — distinct students at this college
        # enrolled in any course in any department containing a
        # PREPARES_FOR-aligned course for the SOC.
        broad = session.run("""
            MATCH (col:College {name: $college})-[op:OCCUPATION_PIPELINE]
                  ->(:Occupation {soc_code: $soc_code})
            RETURN op.student_count AS total_in_aligned_departments
        """, college=college, soc_code=soc_code).single()

        # `total_in_program` reads from the HAS_COMPETENCY edge
        # precomputed by partnerships.compute. Definition: students at
        # this college who have at least one prep-tagged course
        # enrollment for this SOC AND have declared their major in one
        # of the aligned departments. Not currently rendered in the UI
        # (only total_in_aligned_departments is shown), but available
        # for narrative composition.
        #
        # College-scoping pivot via the `student_college` index: the
        # query starts from `(s:Student {college: $college})` (~13K
        # nodes/college), filters by primary_focus, then EXISTS-checks
        # HAS_COMPETENCY. Without this pivot, broad CTE-aligned SOCs
        # (e.g., 25-2031 Secondary Teachers with 372K HAS_COMPETENCY
        # edges in prod) caused 30s+ timeouts because the planner
        # scanned the full HAS_COMPETENCY pool and loaded primary_focus
        # for every candidate. Multi-college future: convert
        # `s.college` to a list and switch to `$college IN s.colleges`
        # — the partnership-positioning question stays per-college (a
        # college's pipeline is its own students).
        stats = session.run("""
            MATCH (s:Student {college: $college})
            WHERE s.primary_focus IN $departments
              AND EXISTS {
                  (s)-[:HAS_COMPETENCY]->(:Occupation {soc_code: $soc_code})
              }
            RETURN count(DISTINCT s) AS total_in_program
        """, college=college, departments=departments, soc_code=soc_code).single()

        student_stats = {
            "total_in_program": stats["total_in_program"] if stats else 0,
            "total_in_aligned_departments": (broad["total_in_aligned_departments"] if broad else 0) or 0,
        }

        # Top-10 exemplars from the HAS_COMPETENCY edge set. Two-phase
        # query:
        #
        #   1. Pivot from Student.college (~13K nodes/college via the
        #      student_college index), filter by primary_focus, then
        #      pull the HAS_COMPETENCY edge to the SOC for ranking.
        #      Sort by competency_depth then GPA, LIMIT 10. The
        #      college-pivot bound is what keeps broad CTE-aligned SOCs
        #      tractable (e.g., 25-2031 has 372K HAS_COMPETENCY edges
        #      in prod; without the pivot, the planner scanned that
        #      whole pool and timed out at 30s+).
        #
        #   2. For the 10 returned students, fetch their aligned-dept
        #      enrollment history at this college for the expansion
        #      panel rendering.
        #
        # Multi-college future: convert `s.college` to a list and
        # switch to `$college IN s.colleges`. The partnership question
        # stays per-college — a college's pipeline is its own students,
        # ranked by their HAS_COMPETENCY edge to the chosen SOC
        # (regardless of which college's coursework contributed the
        # competency).
        focus_query = """
            MATCH (s:Student {college: $college})
            WHERE s.primary_focus IN $departments
            MATCH (s)-[hc:HAS_COMPETENCY]->(:Occupation {soc_code: $soc_code})
            WITH s, hc.competency_depth AS competency_depth
            ORDER BY competency_depth DESC, COALESCE(s.gpa, 0.0) DESC
            LIMIT 10
            OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(c:Course {college: $college})
                          <-[:CONTAINS]-(d:Department)
            WHERE d.name IN $departments
            WITH s, competency_depth,
                 collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
                     code: c.code, name: c.name,
                     grade: e.grade, term: e.term
                 } END) AS raw_enrollments
            WITH s, competency_depth,
                 [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
            RETURN s.uuid AS uuid, s.primary_focus AS primary_focus,
                   size(enrollments) AS courses_completed,
                   COALESCE(s.gpa, 0.0) AS gpa,
                   enrollments
        """
        result = session.run(
            focus_query,
            college=college, departments=departments, soc_code=soc_code,
        ).data()

        if len(result) < 10:
            # Fallback: students at this college with HAS_COMPETENCY to
            # this SOC whose primary_focus is outside the aligned
            # departments (e.g., cross-disciplinary candidates whose
            # major is elsewhere but who took prep coursework). Same
            # college-scoping pivot as focus_query, complementary
            # filter, excluding already-returned UUIDs.
            fallback_query = """
                MATCH (s:Student {college: $college})
                WHERE NOT (s.primary_focus IN $departments)
                  AND NOT (s.uuid IN $exclude_uuids)
                MATCH (s)-[hc:HAS_COMPETENCY]->(:Occupation {soc_code: $soc_code})
                WITH s, hc.competency_depth AS competency_depth
                ORDER BY competency_depth DESC, COALESCE(s.gpa, 0.0) DESC
                LIMIT $limit
                OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(c:Course {college: $college})
                              <-[:CONTAINS]-(d:Department)
                WHERE d.name IN $departments
                WITH s, competency_depth,
                     collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
                         code: c.code, name: c.name,
                         grade: e.grade, term: e.term
                     } END) AS raw_enrollments
                WITH s, competency_depth,
                     [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
                RETURN s.uuid AS uuid, s.primary_focus AS primary_focus,
                       size(enrollments) AS courses_completed,
                       COALESCE(s.gpa, 0.0) AS gpa,
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
