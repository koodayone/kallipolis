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
        # Primary headline count: distinct students with at least one
        # ENROLLED_IN edge to any course in any aligned department.
        broad = session.run("""
            MATCH (dept:Department)-[:CONTAINS]->(c:Course {college: $college})
                  <-[:ENROLLED_IN]-(s:Student)
            WHERE dept.name IN $departments
            RETURN count(DISTINCT s) AS total_in_aligned_departments
        """, college=college, departments=departments).single()

        # Secondary count: students whose primary_focus is one of the
        # aligned departments AND who have at least one enrollment at
        # this college.
        stats = session.run("""
            MATCH (st:Student)
            WHERE st.primary_focus IN $departments
              AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            RETURN count(st) AS total_in_program
        """, college=college, departments=departments).single()

        student_stats = {
            "total_in_program": stats["total_in_program"] if stats else 0,
            "total_in_aligned_departments": broad["total_in_aligned_departments"] if broad else 0,
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
        result = session.run("""
            MATCH (dept:Department)-[:CONTAINS]->(:Course {college: $college})
                  <-[:ENROLLED_IN]-(st:Student)
            WHERE dept.name IN $departments
            WITH DISTINCT st

            // Count SOC-aligned course enrollments for ranking.
            OPTIONAL MATCH (st)-[:ENROLLED_IN]->(prep:Course {college: $college})
                  -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WITH st, count(DISTINCT prep) AS soc_aligned_count

            // Collect the student's full aligned-department enrollment list
            // for the expansion body.
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
                  <-[:CONTAINS]-(d:Department)
            WHERE d.name IN $departments
            WITH st, soc_aligned_count,
                 collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
                     code: c.code, name: c.name,
                     grade: e.grade, term: e.term
                 } END) AS raw_enrollments
            WITH st, soc_aligned_count,
                 [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments,
                 CASE WHEN st.primary_focus IN $departments
                      THEN 1 ELSE 0 END AS focus_match
            ORDER BY focus_match DESC, soc_aligned_count DESC,
                     size(enrollments) DESC, COALESCE(st.gpa, 0.0) DESC
            LIMIT 10
            RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                   size(enrollments) AS courses_completed,
                   COALESCE(st.gpa, 0.0) AS gpa,
                   enrollments
        """, college=college, departments=departments, soc_code=soc_code).data()

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
