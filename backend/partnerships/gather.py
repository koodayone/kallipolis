"""Neo4j data retrieval for partnership opportunity reports — no LLM calls.

Three helpers used by ``opportunity.py``:

    _gather_aligned_curriculum(college, soc_code) -> list[dict]
        Departments and courses at the college that PREPARES_FOR the SOC.

    _gather_student_pipeline(college, departments, soc_code)
        -> tuple[dict, list[dict]]
        Student pipeline counts and the top exemplar students.

    _gather_curriculum_crosswalk(college, soc_code) -> dict
        TOP4 × CIP × SOC pathway structure for the report's hero
        visualization. Marks each TOP4 as taught-at-college or missing,
        and each CIP as active (reachable through a taught TOP4) or
        inactive.

All are scoped to a (college, SOC) pair and gated by the institutional
PREPARES_FOR edge — same pattern the employer-centric proposal flow used
historically. Per the institutional-deference principle: every claim is
derived from edges materialized via the Chancellor's Office TOP-CIP and
BLS/NCES CIP-SOC crosswalks; nothing here is LLM-mediated.
"""

from __future__ import annotations

from collections import defaultdict

from ontology.schema import get_driver


# SAM codes considered "occupational" for partnership-evidence framing.
# A: Apprenticeship, B: Advanced Occupational, C: Clearly Occupational,
# D: Possibly Occupational. Excludes E (Non-Occupational) — gen-ed
# feeders that bloat broad SOC prep sets without representing
# workforce-development action surface. The boundary is CCCCO's own
# (MIS Data Element Dictionary), so the filter is institutional, not a
# vendor heuristic.
SAM_OCCUPATIONAL = ["A", "B", "C", "D"]


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
        #
        # No SAM filter. The institutional prep universe (the hero's
        # denominator) is SAM-filtered at the system level — that
        # defines which TOPs are "occupationally relevant" for this
        # SOC. But for the per-college accordion, what matters is
        # whether this college teaches in those relevant TOPs at all,
        # not how this particular college chose to classify their own
        # courses (some colleges tag the same TOP-aligned course as
        # SAM C, others as SAM E). The accordion shows every course
        # at this college that institutionally prepares for this SOC.
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

    The eligibility gate is TOP4 program-family alignment: a student is
    eligible if they have at least one ENROLLED_IN edge to a course at
    this college whose top_code shares its 4-digit prefix (TOP4) with
    any PREPARES_FOR course for this SOC. Top-N ranking within the
    eligible set is by count of TOP4-aligned courses then GPA — direct
    institutional-pathway measures.

    Why TOP4, not the strict TOP6 / HAS_COMPETENCY edge: an upstream
    discrepancy between the MCF top_code on courses and the DataMart-
    derived top6 calibration causes systematic gaps where a course's
    PREPARES_FOR edge exists but no synthetic student is enrolled in
    that specific course (the calibration bucketed the parent code
    XX00 differently than the course's actual XX00 vs sibling XX50).
    Empirically this hits 105 of 115 colleges to varying degrees;
    Redwoods is 100% gap. Widening to TOP4 surfaces students who took
    courses in the same 4-digit program family — the candidate
    pipeline a partnership would route into specific prep courses
    rather than a strict "already prepared" claim. See
    `docs/product/the-atlas.md` (or this commit's PR description) for
    the framing trade-off.

    Concretely:
      - Headline count (`total_in_aligned_departments`): students at
        this college enrolled in any course in any department that
        contains a PREPARES_FOR-aligned course for the SOC. Read off
        the precomputed OCCUPATION_PIPELINE.student_count edge.
      - In-program count (`total_in_program`): students at this college
        with at least one TOP4-aligned enrollment.
      - Top-N exemplars: students with TOP4-aligned enrollments,
        ranked by count of TOP4-aligned courses then GPA. Their
        displayed enrollments are the TOP4-aligned courses they have
        taken (not just the strict PREPARES_FOR set).

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

        # In-program count: distinct students with at least one TOP4-
        # aligned enrollment at this college. Strict subset of the
        # OCCUPATION_PIPELINE.student_count headline (which is dept-
        # aligned, broader). Available for narrative composition.
        #
        # College-scoping pivot via the `student_college` index keeps
        # the per-(college, SOC) cost bounded — ~13K students/college
        # with a constant-time top_code prefix check per ENROLLED_IN
        # edge.
        stats = session.run("""
            MATCH (c:Course {college: $college})-[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WITH collect(DISTINCT substring(c.top_code, 0, 4)) AS prep_top4s
            WHERE size(prep_top4s) > 0
            MATCH (s:Student {college: $college})-[:ENROLLED_IN]->(c2:Course {college: $college})
            WHERE c2.top_code IS NOT NULL
              AND substring(c2.top_code, 0, 4) IN prep_top4s
            RETURN count(DISTINCT s) AS total_in_program
        """, college=college, soc_code=soc_code).single()

        student_stats = {
            "total_in_program": (stats["total_in_program"] if stats else 0) or 0,
            "total_in_aligned_departments": (broad["total_in_aligned_departments"] if broad else 0) or 0,
        }

        # Top-10 exemplars from the TOP4-aligned student pool. Single-
        # pass query:
        #
        #   1. Compute the prep TOP4 set: distinct 4-digit prefixes of
        #      top_codes on this college's PREPARES_FOR-tagged courses
        #      for the SOC.
        #   2. Pivot from Student.college (uses student_college
        #      index, ~13K nodes/college). For each student, count
        #      distinct ENROLLED_IN courses whose top_code shares a
        #      prep TOP4 prefix. Sort by that count then GPA, LIMIT 10.
        #   3. Re-walk the same student-course set to surface
        #      enrollment detail (course code, name, grade, term) for
        #      the panel expansion. Only TOP4-aligned courses appear
        #      in the displayed enrollment list — the table represents
        #      program-family affinity, not all coursework.
        #
        # The query has no HAS_COMPETENCY dependency. It works even
        # when the synthetic student generator has not enrolled any
        # student in the specific PREPARES_FOR course (the structural
        # gap that motivates this widening). Multi-college future:
        # convert `s.college` to a list and switch to
        # `$college IN s.colleges`.
        top4_query = """
            MATCH (c:Course {college: $college})-[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WITH collect(DISTINCT substring(c.top_code, 0, 4)) AS prep_top4s
            WHERE size(prep_top4s) > 0
            MATCH (s:Student {college: $college})-[:ENROLLED_IN]->(c2:Course {college: $college})
            WHERE c2.top_code IS NOT NULL
              AND substring(c2.top_code, 0, 4) IN prep_top4s
            WITH prep_top4s, s, count(DISTINCT c2) AS top4_courses_completed
            ORDER BY top4_courses_completed DESC, COALESCE(s.gpa, 0.0) DESC
            LIMIT 10
            OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(c3:Course {college: $college})
            WHERE c3.top_code IS NOT NULL
              AND substring(c3.top_code, 0, 4) IN prep_top4s
            WITH s, top4_courses_completed,
                 collect(DISTINCT CASE WHEN c3 IS NOT NULL THEN {
                     code: c3.code, name: c3.name,
                     grade: e.grade, term: e.term
                 } END) AS raw_enrollments
            WITH s, top4_courses_completed,
                 [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
            RETURN s.uuid AS uuid, s.primary_focus AS primary_focus,
                   top4_courses_completed AS courses_completed,
                   COALESCE(s.gpa, 0.0) AS gpa,
                   enrollments
        """
        result = session.run(
            top4_query,
            college=college, soc_code=soc_code,
        ).data()

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


def _gather_curriculum_crosswalk(college: str, soc_code: str) -> dict:
    """Build the TOP4 × CIP × SOC pathway data for the report's hero
    visualization. Renders the institutional crosswalk chain in three
    columns:

      • TOP4 column: every 4-digit TOP family whose courses
        institutionally prepare for the SOC, marked taught-at-college
        or missing.
      • CIP column: every NCES CIP that bridges any of those TOPs to
        the target SOC, marked active (reachable through a taught
        TOP4) or inactive.
      • SOC column: the report's anchor occupation.

    SAM filter: courses are scoped to A/B/C/D (Apprenticeship through
    Possibly Occupational, per CCCCO MIS Data Element Dictionary).
    Non-occupational gen-ed feeders (SAM E) are excluded — they bloat
    broad SOC prep sets without representing workforce-development
    action surface. The filter is institutional, not a vendor
    heuristic; the report attributes it to its CCCCO source.

    Returns a dict shaped for the OpportunityReport `curriculum_crosswalk`
    field — see partnerships.models.CurriculumCrosswalk.
    """
    driver = get_driver()
    from ontology.crosswalks import (
        _load_top4_names,
        load_cip_titles,
        top4_to_cips_for_soc,
    )

    top4_names = _load_top4_names()["top4"]
    cip_titles = load_cip_titles()

    # Asymmetric SAM filtering: SAM A/B/C/D on global only.
    #
    #   global_rows: the institutional prep set across ALL CCCs,
    #     SAM-filtered to occupational. Defines which TOPs are
    #     "occupationally relevant" for this SOC at the system level.
    #     Bounded so noisy SOCs (e.g., Secondary Teachers' gen-ed
    #     feeders) don't dominate the universe.
    #
    #   taught_rows: every TOP this specific college teaches for this
    #     SOC, NO SAM filter. SAM classification varies by college —
    #     the same TOP-aligned course can be SAM C at one college and
    #     SAM E at another. For the per-(college, SOC) report, what
    #     matters is whether the college has any course at all in
    #     this TOP that institutionally prepares for the SOC; the
    #     college's own SAM tagging shouldn't gate that answer. This
    #     also matches _gather_aligned_curriculum (the accordion
    #     above), which is unfiltered for the same reason.
    with driver.session() as session:
        global_rows = session.run(
            """
            MATCH (c:Course)-[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WHERE c.sam_code IN $sam_codes
            RETURN DISTINCT r.via_top AS top6
            """,
            soc_code=soc_code, sam_codes=SAM_OCCUPATIONAL,
        ).data()
        taught_rows = session.run(
            """
            MATCH (c:Course {college: $college})-[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            RETURN DISTINCT r.via_top AS top6
            """,
            college=college, soc_code=soc_code,
        ).data()

    global_top4 = {row["top6"][:4] for row in global_rows if row.get("top6")}
    taught_top4 = {row["top6"][:4] for row in taught_rows if row.get("top6")}

    # Bridge each TOP4 to its relevant CIPs for this SOC.
    cips_by_top4 = top4_to_cips_for_soc(soc_code)

    # Project: every TOP4 in the global prep set, plus its bridging CIPs.
    tops = []
    all_cips: set[str] = set()
    for top4 in sorted(global_top4):
        relevant_cips = sorted(cips_by_top4.get(top4, set()))
        if not relevant_cips:
            # TOP4 has no CIP that bridges to this SOC — shouldn't happen
            # given the global query came from PREPARES_FOR edges, but
            # guard against orphan TOPs nonetheless.
            continue
        tops.append({
            "code": top4,
            "name": top4_names.get(top4, ""),
            "taught_at_college": top4 in taught_top4,
            "cips": relevant_cips,
        })
        all_cips.update(relevant_cips)

    # Active CIPs: those reachable through at least one taught TOP4.
    active_cips: set[str] = set()
    for t in tops:
        if t["taught_at_college"]:
            active_cips.update(t["cips"])

    cips = [
        {
            "code": cip,
            "title": cip_titles.get(cip, ""),
            "active": cip in active_cips,
        }
        for cip in sorted(all_cips)
    ]

    n_total = len(tops)
    n_taught = sum(1 for t in tops if t["taught_at_college"])
    coverage_pct = round(100.0 * n_taught / n_total, 1) if n_total else 0.0

    return {
        "tops": tops,
        "cips": cips,
        "n_taught": n_taught,
        "n_total": n_total,
        "coverage_pct": coverage_pct,
    }
