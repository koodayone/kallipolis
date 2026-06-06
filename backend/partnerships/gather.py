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
    college: str, soc_code: str, hero_top4s: set[str] | None = None,
) -> list[dict]:
    """Fetch departments and courses that PREPARES_FOR the selected occupation.

    Per the institutional-deference architectural commitment: the
    pathway claim is established by the institutional crosswalk
    (Course-[:PREPARES_FOR]->Occupation, written from the Chancellor's
    Office TOP-CIP and BLS/NCES CIP-SOC crosswalks). When no
    departments at this college prepare students for the SOC, returns
    [] — caller surfaces this honestly rather than falling back.

    `hero_top4s`: optional restriction to TOP4 families in the hero's
    SAM-occupational universe for this SOC. When provided, courses
    whose `via_top[:4]` falls outside this set are dropped — keeps the
    accordion and hero pathway visualization coherent (a TOP shown in
    one is shown in the other). Pass `None` to surface every TOP this
    college teaches for the SOC regardless of system-wide SAM
    relevance — used by the LLM-narrative generator where the broader
    pool is desirable.

    Returns curriculum_evidence_list, with `via_top` and `via_cip` per
    department for downstream institutional-source attribution.
    """
    driver = get_driver()
    with driver.session() as session:
        # The PREPARES_FOR edge carries `via_top` as an audit-trail
        # property — the TOP6 the institutional crosswalk used to
        # mediate this Course→Occupation alignment.
        #
        # No SAM filter on the per-college side. The institutional prep
        # universe (the hero's denominator) is SAM-filtered at the
        # system level — that defines which TOPs are "occupationally
        # relevant" for this SOC. But for the per-college accordion,
        # what matters is whether this college teaches in those
        # relevant TOPs at all, not how this particular college chose
        # to classify their own courses (some colleges tag the same
        # TOP-aligned course as SAM C, others as SAM E).
        #
        # When `hero_top4s` is provided, additionally restrict to TOPs
        # in that universe — drops the inverse case (a college teaches
        # a TOP for this SOC but the TOP is not in the system-wide
        # SAM-occupational set, e.g. Butte's Geography → Environmental
        # Science Tech). Without this restriction the accordion
        # surfaces TOPs that the hero visualization can't represent,
        # which reads as inconsistency.
        if hero_top4s is not None:
            where_clause = (
                "WHERE r.via_top IS NOT NULL "
                "AND substring(r.via_top, 0, 4) IN $hero_top4s"
            )
            params = {
                "college": college,
                "soc_code": soc_code,
                "hero_top4s": list(hero_top4s),
            }
        else:
            where_clause = ""
            params = {"college": college, "soc_code": soc_code}

        result = session.run(f"""
            MATCH (col:College {{name: $college}})-[:OFFERS]->(dept:Department)
                  -[:CONTAINS]->(c:Course {{college: $college}})
                  -[r:PREPARES_FOR]->(:Occupation {{soc_code: $soc_code}})
            {where_clause}
            RETURN dept.name AS department, c.code AS code, c.name AS name,
                   c.description AS description,
                   c.learning_outcomes AS learning_outcomes,
                   c.course_objectives AS course_objectives,
                   c.top_code AS top_code,
                   r.via_top AS via_top
            ORDER BY dept.name, c.code
        """, **params).data()

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
    college: str, departments: list[str], soc_code: str,
    hero_top4s: set[str] | None = None,
) -> tuple[dict, list[dict]]:
    """Find students whose academic pathway aligns with the partnership.

    The eligibility gate is TOP4 program alignment: a student is
    eligible if they have at least one ENROLLED_IN edge to a course at
    this college whose top_code shares its 4-digit prefix (TOP4) with
    any PREPARES_FOR course for this SOC. Top-N ranking within the
    eligible set is by count of TOP4-aligned courses then GPA — direct
    institutional-pathway measures.

    `hero_top4s`: optional restriction to TOP4s in the hero pathway's
    SAM-occupational universe. When provided, the prep TOP4 set is
    intersected with this universe before student matching — keeps the
    student section coherent with the accordion + hero (Butte's
    Geography → Environmental Science Tech case). The broad headline
    `total_in_aligned_departments` is also recomputed at request time
    under the same filter, replacing the precomputed
    OCCUPATION_PIPELINE.student_count which has no hero awareness.
    Pass None for the unfiltered behavior used by the LLM-narrative
    generator.

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
        # When the hero filter is in effect, the prep TOP4 set is
        # intersected with the hero universe — keeps the student
        # pipeline coherent with the accordion + hero. When None, the
        # set is the unfiltered PREPARES_FOR cover (current behavior
        # used by the LLM-narrative generator).
        if hero_top4s is not None:
            prep_filter = (
                "WHERE substring(c.top_code, 0, 4) IN $hero_top4s"
            )
            hero_params = {"hero_top4s": list(hero_top4s)}
        else:
            prep_filter = ""
            hero_params = {}

        # Broad headline `total_in_aligned_departments`: distinct
        # students at this college enrolled in any course in any
        # department that contains a PREPARES_FOR-aligned course for
        # the SOC. With the hero filter, the department set is
        # restricted to those containing hero-universe PREPARES_FOR
        # courses; recomputed at request time. Without the filter, the
        # precomputed OCCUPATION_PIPELINE.student_count is the fast
        # path.
        if hero_top4s is not None:
            broad = session.run(f"""
                MATCH (c:Course {{college: $college}})-[:PREPARES_FOR]
                      ->(:Occupation {{soc_code: $soc_code}})
                {prep_filter}
                MATCH (c)<-[:CONTAINS]-(dept:Department)
                WITH collect(DISTINCT dept) AS aligned_depts
                MATCH (s:Student {{college: $college}})-[:ENROLLED_IN]
                      ->(:Course {{college: $college}})
                      <-[:CONTAINS]-(d:Department)
                WHERE d IN aligned_depts
                RETURN count(DISTINCT s) AS total_in_aligned_departments
            """, college=college, soc_code=soc_code, **hero_params).single()
        else:
            broad = session.run("""
                MATCH (col:College {name: $college})-[op:OCCUPATION_PIPELINE]
                      ->(:Occupation {soc_code: $soc_code})
                RETURN op.student_count AS total_in_aligned_departments
            """, college=college, soc_code=soc_code).single()

        # In-program count: distinct students with at least one TOP4-
        # aligned enrollment at this college. Strict subset of the
        # broad headline above.
        #
        # College-scoping pivot via the `student_college` index keeps
        # the per-(college, SOC) cost bounded — ~13K students/college
        # with a constant-time top_code prefix check per ENROLLED_IN
        # edge.
        stats = session.run(f"""
            MATCH (c:Course {{college: $college}})-[:PREPARES_FOR]
                  ->(:Occupation {{soc_code: $soc_code}})
            {prep_filter}
            WITH collect(DISTINCT substring(c.top_code, 0, 4)) AS prep_top4s
            WHERE size(prep_top4s) > 0
            MATCH (s:Student {{college: $college}})-[:ENROLLED_IN]
                  ->(c2:Course {{college: $college}})
            WHERE c2.top_code IS NOT NULL
              AND substring(c2.top_code, 0, 4) IN prep_top4s
            RETURN count(DISTINCT s) AS total_in_program
        """, college=college, soc_code=soc_code, **hero_params).single()

        student_stats = {
            "total_in_program": (stats["total_in_program"] if stats else 0) or 0,
            "total_in_aligned_departments": (broad["total_in_aligned_departments"] if broad else 0) or 0,
        }

        # Top-10 exemplars from the (hero-filtered, if applicable)
        # TOP4-aligned student pool. Single-pass query:
        #
        #   1. Compute the prep TOP4 set: distinct 4-digit prefixes of
        #      top_codes on this college's PREPARES_FOR-tagged courses
        #      for the SOC, optionally restricted to the hero universe.
        #   2. Pivot from Student.college (uses student_college
        #      index, ~13K nodes/college). For each student, count
        #      distinct ENROLLED_IN courses whose top_code shares a
        #      prep TOP4 prefix. Sort by that count then GPA, LIMIT 10.
        #   3. Re-walk the same student-course set to surface
        #      enrollment detail (course code, name, grade, term) for
        #      the panel expansion. Only TOP4-aligned courses appear
        #      in the displayed enrollment list — the table represents
        #      TOP4-program affinity, not all coursework.
        #
        # The query has no HAS_COMPETENCY dependency. It works even
        # when the synthetic student generator has not enrolled any
        # student in the specific PREPARES_FOR course (the structural
        # gap that motivates this widening). Multi-college future:
        # convert `s.college` to a list and switch to
        # `$college IN s.colleges`.
        top4_query = f"""
            MATCH (c:Course {{college: $college}})-[:PREPARES_FOR]
                  ->(:Occupation {{soc_code: $soc_code}})
            {prep_filter}
            WITH collect(DISTINCT substring(c.top_code, 0, 4)) AS prep_top4s
            WHERE size(prep_top4s) > 0
            MATCH (s:Student {{college: $college}})-[:ENROLLED_IN]
                  ->(c2:Course {{college: $college}})
            WHERE c2.top_code IS NOT NULL
              AND substring(c2.top_code, 0, 4) IN prep_top4s
            WITH prep_top4s, s, count(DISTINCT c2) AS top4_courses_completed
            ORDER BY top4_courses_completed DESC, COALESCE(s.gpa, 0.0) DESC
            LIMIT 10
            OPTIONAL MATCH (s)-[e:ENROLLED_IN]->(c3:Course {{college: $college}})
            WHERE c3.top_code IS NOT NULL
              AND substring(c3.top_code, 0, 4) IN prep_top4s
            WITH s, top4_courses_completed,
                 collect(DISTINCT CASE WHEN c3 IS NOT NULL THEN {{
                     code: c3.code, name: c3.name,
                     grade: e.grade, term: e.term
                 }} END) AS raw_enrollments
            WITH s, top4_courses_completed,
                 [x IN raw_enrollments WHERE x IS NOT NULL] AS enrollments
            RETURN s.uuid AS uuid, s.primary_focus AS primary_focus,
                   top4_courses_completed AS courses_completed,
                   COALESCE(s.gpa, 0.0) AS gpa,
                   enrollments
        """
        result = session.run(
            top4_query,
            college=college, soc_code=soc_code, **hero_params,
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


def _gather_curriculum_crosswalk(
    college: str,
    soc_code: str,
    top_prefix: str | None = None,
    union_colleges: list[str] | None = None,
    cte_only: bool = False,
    exclude_tops: frozenset[str] | set[str] | None = None,
) -> dict:
    """Build the TOP6 × CIP × SOC pathway data for the report's hero
    visualization. Renders the institutional crosswalk chain in three
    columns:

      • TOP6 column: every 6-digit TOP code whose courses
        institutionally prepare for the SOC, marked taught-at-college
        or missing.
      • CIP column: every NCES CIP that bridges any of those TOPs to
        the target SOC, marked active (reachable through a taught
        TOP6) or inactive.
      • SOC column: the report's anchor occupation.

    Keyed at TOP6 (not TOP4) because that's the granularity the CCCCO
    PCAH TOP→CIP crosswalk actually operates at — rolling up to TOP4
    hid cases where a college teaches some 6-digit children of a 4-
    digit family but not others, with each TOP6 having its own CIP
    bridges. The frontend can still cluster visually by TOP4 prefix
    (substring(code, 0, 4)) without losing the TOP6 fidelity here.

    SAM filter: courses are scoped to A/B/C/D (Apprenticeship through
    Possibly Occupational, per CCCCO MIS Data Element Dictionary).
    Non-occupational gen-ed feeders (SAM E) are excluded — they bloat
    broad SOC prep sets without representing workforce-development
    action surface. The filter is institutional, not a vendor
    heuristic; the report attributes it to its CCCCO source.

    `top_prefix` optionally scopes the prep universe to a TOP division (the
    SVAMP 09-only lens). Default None ⇒ unscoped, so per-college reports are
    byte-identical.

    `union_colleges` optionally marks a TOP "taught" when ANY college in the
    list teaches it (the SVAMP consortium aggregated-occupation view). Default
    None ⇒ the single-`college` taught query, so per-college reports are
    byte-identical.

    `cte_only` optionally restricts the prep universe to CTE (career-technical)
    TOPs per the CCCCO PCAH, dropping transfer/academic ones (the SVAMP
    workforce scope). Default False ⇒ per-college reports are byte-identical.

    `exclude_tops` optionally drops named TOP6 codes from the prep universe —
    the SVAMP director's-mandate exclusions (svamp.SVAMP_MANDATE_EXCLUDED_TOPS),
    programs whose crosswalk link is category-true but whose employment flows
    run to other industry verticals. Default None ⇒ per-college reports are
    byte-identical.

    Returns a dict shaped for the OpportunityReport `curriculum_crosswalk`
    field — see partnerships.models.CurriculumCrosswalk.
    """
    driver = get_driver()
    from ontology.crosswalks import (
        load_top_titles,
        load_cip_titles,
        top6_to_cips_for_soc,
        is_cte_top4_family,
    )

    top_titles = load_top_titles()
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
        if union_colleges is not None:
            # Consortium-union mode (the SVAMP aggregated-occupation view):
            # "taught" means taught by ANY of these member colleges, so the
            # pathway reflects consortium-wide coverage rather than one college.
            taught_rows = session.run(
                """
                MATCH (c:Course)-[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
                WHERE c.college IN $colleges
                RETURN DISTINCT r.via_top AS top6
                """,
                colleges=union_colleges, soc_code=soc_code,
            ).data()
        else:
            taught_rows = session.run(
                """
                MATCH (c:Course {college: $college})-[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
                RETURN DISTINCT r.via_top AS top6
                """,
                college=college, soc_code=soc_code,
            ).data()

        # SVAMP enroll/confer coverage: a TOP also "prepares" the SOC when a
        # member college ENROLLS or CONFERS it — even with no course tagged to
        # its own code (the 095630 parent-code seam). Intersected with the
        # crosswalk universe (global_top6) below so only TOPs that actually map
        # to this SOC count. cte_only marks the SVAMP scope (set for both the
        # aggregated union view and the targeted per-college view); default
        # reports never run this, so they stay course-only and byte-identical.
        active_rows: list[dict] = []
        if cte_only:
            active_rows = session.run(
                """
                MATCH (pr:Program)-[:AWARDED|ENROLLED]->()
                WHERE pr.college IN $colleges
                RETURN DISTINCT pr.top6 AS top6
                """,
                colleges=(union_colleges if union_colleges is not None else [college]),
            ).data()

    global_top6 = {row["top6"] for row in global_rows if row.get("top6")}
    taught_top6 = {row["top6"] for row in taught_rows if row.get("top6")}
    # Fold the activity-based "taught" in (SVAMP only): a crosswalking TOP a
    # member college confers/enrolls reads taught even with no tagged course, so
    # 095630 → Machinists renders solid and the count reads "1 of 1".
    if active_rows:
        active_top6 = {row["top6"] for row in active_rows if row.get("top6")}
        taught_top6 |= active_top6 & global_top6

    # Optional TOP-division scope (the SVAMP 09-only lens). Restricting the prep
    # universe here is the single injection point that scopes the whole report:
    # `tops` (the hero pathway), the `hero_top4s` set derived from it in
    # build_opportunity_report — which gates the curriculum accordion and the
    # student pipeline — all narrow to this division. Default None ⇒ the full
    # faithful crosswalk, so the per-(college, SOC) report is unchanged.
    if top_prefix:
        global_top6 = {t for t in global_top6 if t.startswith(top_prefix)}
        taught_top6 = {t for t in taught_top6 if t.startswith(top_prefix)}
    if exclude_tops:
        # Director's-mandate exclusions (see docstring) — same injection point
        # as top_prefix, so the whole report scopes consistently.
        global_top6 -= set(exclude_tops)
        taught_top6 -= set(exclude_tops)
    if cte_only:
        # Restrict to CTE (career-technical) TOP families per the CCCCO PCAH,
        # dropping transfer/academic ones (the SVAMP workforce scope). Uses the
        # family-level test so newer TOP6 codes missing from the PCAH file but
        # in a CTE family (e.g. 095690 Digital Fabrication) are kept. Default
        # False ⇒ per-college reports unchanged.
        global_top6 = {t for t in global_top6 if is_cte_top4_family(t)}
        taught_top6 = {t for t in taught_top6 if is_cte_top4_family(t)}

    # Project: every TOP6 in the global prep set, plus its bridging CIPs
    # for this SOC. CIPs that map to the SOC but are unreachable from
    # this specific TOP6 are excluded — only "relevant" CIPs for the
    # (TOP6, SOC) pair appear.
    tops = []
    all_cips: set[str] = set()
    for top6 in sorted(global_top6):
        relevant_cips = top6_to_cips_for_soc(top6, soc_code)
        if not relevant_cips:
            # TOP6 has no CIP that bridges to this SOC — shouldn't happen
            # given the global query came from PREPARES_FOR edges, but
            # guard against orphan TOPs nonetheless.
            continue
        tops.append({
            "code": top6,
            "name": top_titles.get(top6, ""),
            "taught_at_college": top6 in taught_top6,
            "cips": relevant_cips,
        })
        all_cips.update(relevant_cips)

    # Active CIPs: those reachable through at least one taught TOP6.
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
