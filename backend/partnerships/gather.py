"""Neo4j data retrieval for partnership proposals — no LLM calls."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ontology.schema import get_driver


@dataclass
class GatheredContext:
    """Structured output from Neo4j context gathering.

    Two sector fields coexist deliberately. `sector` is the employer's
    BLS/general industry classification ("Manufacturing"); `swp_sectors`
    is the institutional Doing-What-Matters / Strong Workforce taxonomy
    ("Advanced Manufacturing"). Coordinator-facing surfaces should
    speak SWP vocabulary — it's the language the partnership artifact
    is grounded in (CTE programs, regional priority sectors, SWP
    funding categories). The BLS sector is kept as backend metadata
    for downstream tooling that needs it.
    """
    employer_name: str = ""
    sector: str = ""
    swp_sectors: list[str] = field(default_factory=list)
    description: str = ""
    # Pre-computed verb phrase characterizing the employer's operations,
    # populated at ingestion by ``employers.characterize``. Drives the
    # opening sentence of the partnership proposal's executive summary
    # via ``f"{employer_name} {operations_summary}."``. The single
    # LLM-derived field in the partnership proposal narrative; every
    # other sentence is templated deterministically over graph data.
    operations_summary: str = ""
    regions: list[str] = field(default_factory=list)
    college: str = ""
    occupation_evidence: list[dict] = field(default_factory=list)


def _gather_targeted_context(employer: str, college: str) -> GatheredContext:
    """Gather employer metadata and occupation evidence from the graph."""
    driver = get_driver()

    with driver.session() as session:
        # Employer overview
        emp_result = session.run("""
            MATCH (emp:Employer {name: $employer})
            OPTIONAL MATCH (emp)-[:IN_MARKET]->(r:Region)
            RETURN emp.name AS name, emp.sector AS sector,
                   COALESCE(emp.swp_sectors, []) AS swp_sectors,
                   emp.description AS description,
                   emp.operations_summary AS operations_summary,
                   collect(COALESCE(r.display_name, r.name)) AS regions
        """, employer=employer).single()

        if not emp_result:
            raise ValueError(f"Employer '{employer}' not found in the graph.")

        # Regional employment data
        econ_result = session.run("""
            MATCH (:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                  <-[:HIRES_FOR]-(emp:Employer {name: $employer})
            RETURN occ.title AS title, occ.soc_code AS soc_code,
                   d.annual_wage AS annual_wage,
                   d.employment AS employment, d.growth_rate AS growth_rate,
                   d.annual_openings AS annual_openings,
                   COALESCE(r.display_name, r.name) AS region
        """, employer=employer, college=college).data()

    return GatheredContext(
        employer_name=emp_result["name"],
        sector=emp_result["sector"] or "",
        swp_sectors=list(emp_result["swp_sectors"]) if emp_result["swp_sectors"] else [],
        description=emp_result["description"] or "",
        operations_summary=emp_result["operations_summary"] or "",
        regions=emp_result["regions"],
        college=college,
        occupation_evidence=[
            {
                "title": r["title"],
                "soc_code": r.get("soc_code"),
                "annual_wage": r["annual_wage"],
                "employment": r["employment"],
                "annual_openings": r.get("annual_openings"),
                "growth_rate": r.get("growth_rate"),
            }
            for r in econ_result
        ],
    )


def _get_developed_skills(college: str, occupation_title: str) -> list[str]:
    """Get all skill names the college develops for a given occupation."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (occ:Occupation {title: $title})-[:REQUIRES_SKILL]->(sk:Skill)
                  <-[:DEVELOPS]-(c:Course {college: $college})
            RETURN DISTINCT sk.name AS skill
            ORDER BY skill
        """, title=occupation_title, college=college).data()
    return [r["skill"] for r in result]


def _gather_aligned_curriculum(
    college: str, soc_code: str, core_skills: list[str]
) -> tuple[str, list[dict]]:
    """Fetch departments and courses that prepare students for the selected occupation.

    The role of `core_skills` here is CHARACTERIZATION, not gating.
    Per the institutional-deference architectural commitment: the
    pathway claim is established by the institutional crosswalk
    (Course-[:PREPARES_FOR]->Occupation, written from the Chancellor's
    Office TOP-CIP and BLS/NCES CIP-SOC crosswalks). Skills are then
    surfaced via OPTIONAL MATCH to decorate each course with which of
    the occupation's required skills it develops, so the narrative
    prompt can speak to specific course-skill matches as
    characterization of what the institutionally-aligned program
    teaches. Skills do not gate which departments surface; the
    crosswalk does.

    The skills-overlap gate (retired in A.1) produced cross-domain
    false positives — nursing courses surfacing under manufacturing
    partnerships because both develop generic skills like documentation.
    PREPARES_FOR grounds the gate in the institutional record:
    institutional ground truth, not LLM-derived skill similarity.

    When no departments at this college prepare students for the SOC,
    returns ("", []) — caller surfaces this honestly rather than
    falling back to the prior skills-soup matching.

    Returns (dept_text_for_prompt, curriculum_evidence_list). The
    curriculum_evidence list carries `via_top` and `via_cip` per
    department for downstream institutional-source attribution
    (atlas rendering, eval rules, narrative chain block).
    """
    driver = get_driver()
    with driver.session() as session:
        # The PREPARES_FOR edge carries `via_top` as an audit-trail
        # property — the TOP6 the institutional crosswalk used to
        # mediate this Course→Occupation alignment. Returning it on
        # each row lets the curriculum_evidence carry the source
        # attribution forward to the narrative prompt and atlas
        # rendering, where the institutional pathway can be made
        # visible (TOP6 → CIP → SOC) per principle 2.
        result = session.run("""
            MATCH (col:College {name: $college})-[:OFFERS]->(dept:Department)
                  -[:CONTAINS]->(c:Course {college: $college})
                  -[r:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            OPTIONAL MATCH (c)-[:DEVELOPS]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH dept, c, r.via_top AS via_top, collect(DISTINCT sk.name) AS aligned_skills
            RETURN dept.name AS department, c.code AS code, c.name AS name,
                   c.description AS description,
                   c.learning_outcomes AS learning_outcomes,
                   c.course_objectives AS course_objectives,
                   c.skill_mappings AS skill_mappings,
                   c.top_code AS top_code,
                   via_top,
                   aligned_skills
            ORDER BY dept.name, c.code
        """, college=college, soc_code=soc_code, core_skills=core_skills).data()

    # Compose CIP codes for each TOP6 surfaced in the result set.
    # Imports here to avoid hoisting external-data load to module
    # import time; crosswalks are cached after first call.
    from ontology.crosswalks import _load_top_to_cip
    top_cip_map = _load_top_to_cip()

    # Group by department, accumulating via_top + via_cip + courses.
    dept_agg: dict[str, dict] = defaultdict(
        lambda: {"courses": [], "skills": set(), "via_top": set(), "via_cip": set()}
    )
    for r in result:
        dept = r["department"]
        course_top = r.get("top_code")
        course_via_top = r.get("via_top")
        course_cips = list(top_cip_map.get(course_via_top, set())) if course_via_top else []
        dept_agg[dept]["courses"].append({
            "code": r["code"],
            "name": r["name"],
            "description": r["description"] or "",
            "learning_outcomes": r["learning_outcomes"] or [],
            "skills": r["aligned_skills"],
            "top_code": course_top,
        })
        dept_agg[dept]["skills"].update(r["aligned_skills"])
        if course_via_top:
            dept_agg[dept]["via_top"].add(course_via_top)
        dept_agg[dept]["via_cip"].update(course_cips)

    # Build text block for narrative prompt. Skills coverage is
    # characterization on top of the TOP-aligned set — not the gating
    # signal — so the "Missing" line communicates which core skills
    # none of this department's PREPARES_FOR courses develop. The
    # institutional pathway is named explicitly per principle 2:
    # each department's TOP6 set is rendered alongside the dept name
    # so the LLM has the structure to attribute correctly.
    core_set = set(core_skills)
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT (gated by TOP-SOC institutional crosswalk):"]
    for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["courses"]), reverse=True):
        skills_str = ", ".join(sorted(data["skills"])) if data["skills"] else "(none of the core skills)"
        missing = core_set - data["skills"]
        missing_str = f". Missing: {', '.join(sorted(missing))}" if missing else ""
        via_tops = sorted(data["via_top"])
        via_top_str = f" [TOP {', '.join(via_tops)}]" if via_tops else ""
        lines.append(
            f"  {dept}{via_top_str}: develops {skills_str} (across {len(data['courses'])} courses){missing_str}"
        )
    dept_text = "\n".join(lines) if dept_agg else ""

    # Sort by course count (largest department first). Skills no longer
    # rank — the gate already passed institutionally. Course count is a
    # faithful proxy for depth of curricular coverage on the SOC's
    # pathway.
    curriculum_evidence = [
        {
            "department": dept,
            "courses": data["courses"],
            "aligned_skills": sorted(data["skills"]),
            "via_top": sorted(data["via_top"]),
            "via_cip": sorted(data["via_cip"]),
        }
        for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["courses"]), reverse=True)
    ]

    return dept_text, curriculum_evidence


def _gather_student_pipeline(
    college: str, departments: list[str], soc_code: str, core_skills: list[str]
) -> tuple[dict, list[dict]]:
    """Find students whose academic pathway aligns with the partnership.

    The role of `core_skills` here is CHARACTERIZATION + within-set
    ranking, not gating. The eligibility gate is department membership
    (per principle 3 of the institutional-deference commitment): a
    student is eligible if their `primary_focus` matches one of the
    aligned departments returned by _gather_aligned_curriculum (which
    are themselves PREPARES_FOR-gated by the institutional crosswalk).
    Skills then rank top-N exemplars within that eligible set, never
    outside it.

    The gating principle: the unit of partnership engagement is the
    department, not the course. A signed partnership with an employer
    benefits every student whose primary focus is in an aligned
    department's pathway, regardless of whether they have yet taken
    the specific course that crosswalks to the selected SOC. Counting
    only course-takers undersells the partnership's scope; the
    headline number should reflect the broader department-rooted
    population.

    Concretely:
      - Eligibility gate (institutional): student.primary_focus IN
        aligned_departments (those returned by
        _gather_aligned_curriculum, derived from
        Department-[:CONTAINS]->Course-[:PREPARES_FOR]->Occupation).
      - Headline count: |eligible students at this college|.
      - "All core skills" subcount: how many of the eligible students
        already demonstrate all the SOC's core skills via HAS_SKILL —
        a finer-grained CHARACTERIZATION signal of pipeline readiness,
        not a gate. Skills here describe what students hold; the
        institutional credential is what qualifies them.
      - Top-N exemplars: ranked WITHIN the eligible set by skill-match
        count, then GPA. Skills are the within-set ranker; the gating
        decision was already made by the department-membership filter.
        Their displayed enrollments are the courses they have taken
        that PREPARES_FOR the selected SOC, so the artifact surfaces
        concrete curricular evidence per student.

    The prior gate (enrollment in skills-developing courses + STARTS
    WITH bidirectional primary_focus matching) was both narrower
    (excluded same-pathway students who had not yet taken a
    skills-developing course) and noisier (skills overlap allowed
    cross-domain bleed-through; STARTS WITH allowed prefix-match
    accidents). Equality on department names is correct now that
    primary_focus is set from the same department-name vocabulary
    that load_college writes into the graph.

    Returns (student_stats, top_students_with_detail).
    """
    driver = get_driver()
    num_core = len(core_skills)

    if not departments:
        # No aligned curriculum at this college → no eligible students.
        # Honest empty set; callers surface this as the "no aligned
        # programs" case in the artifact rather than falling back.
        return {
            "total_in_program": 0,
            "with_all_core_skills": 0,
            "total_in_aligned_departments": 0,
        }, []

    with driver.session() as session:
        # Primary headline count: distinct students with at least one
        # ENROLLED_IN edge to any course in any aligned department.
        # This is the broadest honest count — anyone who has taken a
        # course in one of the institutionally-aligned departments at
        # this college, deduplicated across departments. The narrower
        # primary_focus-gated count below is kept as a secondary
        # measure for prompts that want it.
        broad = session.run("""
            MATCH (dept:Department)-[:CONTAINS]->(c:Course {college: $college})
                  <-[:ENROLLED_IN]-(s:Student)
            WHERE dept.name IN $departments
            RETURN count(DISTINCT s) AS total_in_aligned_departments
        """, college=college, departments=departments).single()

        # Secondary count: students whose primary_focus is one of the
        # aligned departments AND who have at least one enrollment at
        # this college. Narrower (declared focus, not just course
        # enrollment) but useful as a "majors/declared-track" figure.
        stats = session.run("""
            MATCH (st:Student)
            WHERE st.primary_focus IN $departments
              AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            OPTIONAL MATCH (st)-[:HAS_SKILL]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH st, count(DISTINCT sk) AS core_count
            RETURN count(st) AS total_in_program,
                   sum(CASE WHEN core_count = $num_core THEN 1 ELSE 0 END) AS with_all_core_skills
        """, college=college, departments=departments, core_skills=core_skills, num_core=num_core).single()

        student_stats = {
            "total_in_program": stats["total_in_program"] if stats else 0,
            "with_all_core_skills": stats["with_all_core_skills"] if stats else 0,
            "total_in_aligned_departments": broad["total_in_aligned_departments"] if broad else 0,
        }

        # Top-10 exemplars: same eligibility gate as the secondary
        # count, ranked by SOC-aligned course count, then GPA, then
        # core-skill count. The primary sort is the direct
        # institutional-pathway measure: how many courses this student
        # has taken whose TOP routes to the selected SOC. GPA is the
        # secondary signal (institutional academic performance);
        # core-skill count is a final deterministic tiebreaker.
        #
        # `relevant_skills` is the set of skill names DEVELOPS-mapped
        # by this student's SOC-aligned courses — auditable to the
        # course curriculum, not derived from a HAS_SKILL profile that
        # the coordinator can't see. If a student has zero
        # SOC-aligned enrollments, the skill set is empty.
        result = session.run("""
            MATCH (st:Student)
            WHERE st.primary_focus IN $departments
              AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            OPTIONAL MATCH (st)-[:HAS_SKILL]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH st, count(DISTINCT sk) AS core_count
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
                  -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            OPTIONAL MATCH (c)-[:DEVELOPS]->(course_sk:Skill)
            WITH st, core_count,
                 collect(DISTINCT {
                     code: c.code, name: c.name,
                     grade: e.grade, term: e.term
                 }) AS enrollments,
                 collect(DISTINCT course_sk.name) AS relevant_skills
            ORDER BY size(enrollments) DESC, COALESCE(st.gpa, 0.0) DESC, core_count DESC
            LIMIT 10
            RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                   size(enrollments) AS courses_completed,
                   COALESCE(st.gpa, 0.0) AS gpa,
                   core_count AS matching_skills,
                   enrollments, relevant_skills
        """, college=college, departments=departments, soc_code=soc_code, core_skills=core_skills).data()

    top_students = [
        {
            "uuid": r["uuid"],
            "display_number": i + 1,
            "primary_focus": r["primary_focus"] or "",
            "courses_completed": r["courses_completed"],
            "gpa": round(r["gpa"], 2),
            "matching_skills": r["matching_skills"],
            "enrollments": [
                {"code": e["code"], "name": e["name"], "grade": e["grade"], "term": e["term"]}
                # OPTIONAL MATCH may surface a row with all-null fields when
                # the student has zero PREPARES_FOR enrollments; filter those.
                for e in r["enrollments"]
                if e.get("code")
            ],
            # Same null-shell concern as enrollments: if a student has
            # zero SOC-aligned courses, the OPTIONAL MATCH on DEVELOPS
            # collects [null] rather than []. Strip nulls.
            "relevant_skills": [s for s in (r["relevant_skills"] or []) if s],
        }
        for i, r in enumerate(result)
    ]

    return student_stats, top_students
