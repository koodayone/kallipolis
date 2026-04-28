"""Neo4j data retrieval for partnership proposals — no LLM calls."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ontology.schema import get_driver


@dataclass
class GatheredContext:
    """Structured output from Neo4j context gathering."""
    employer_name: str = ""
    sector: str = ""
    description: str = ""
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
            RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
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
        description=emp_result["description"] or "",
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

    Gating swapped from skills-overlap to TOP-SOC alignment via the
    institutional crosswalk: a course is "aligned" iff its top_code
    crosswalks to the selected SOC, materialized as the
    Course-[:PREPARES_FOR]->Occupation edge written by
    ontology.prepares_for at load time. Skills are no longer the gate —
    they are a within-set ranker, used here to decorate each course
    with which of the occupation's core skills it develops, so the
    narrative prompt can speak to specific course-skill matches.

    The skills-overlap gate produced cross-domain false positives
    (nursing courses surfacing under manufacturing partnerships because
    both develop generic skills like documentation). PREPARES_FOR
    grounds the gate in the Chancellor's-Office TOP↔CIP↔SOC chain:
    institutional ground truth, not LLM-derived skill similarity.

    When no departments at this college prepare students for the SOC,
    returns ("", []) — caller surfaces this honestly rather than
    falling back to the prior skills-soup matching.

    Returns (dept_text_for_prompt, curriculum_evidence_list).
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (col:College {name: $college})-[:OFFERS]->(dept:Department)
                  -[:CONTAINS]->(c:Course {college: $college})
                  -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            OPTIONAL MATCH (c)-[:DEVELOPS]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH dept, c, collect(DISTINCT sk.name) AS aligned_skills
            RETURN dept.name AS department, c.code AS code, c.name AS name,
                   c.description AS description,
                   c.learning_outcomes AS learning_outcomes,
                   c.course_objectives AS course_objectives,
                   c.skill_mappings AS skill_mappings,
                   aligned_skills
            ORDER BY dept.name, c.code
        """, college=college, soc_code=soc_code, core_skills=core_skills).data()

    # Group by department
    dept_agg: dict[str, dict] = defaultdict(lambda: {"courses": [], "skills": set()})
    for r in result:
        dept = r["department"]
        dept_agg[dept]["courses"].append({
            "code": r["code"],
            "name": r["name"],
            "description": r["description"] or "",
            "learning_outcomes": r["learning_outcomes"] or [],
            "skills": r["aligned_skills"],
        })
        dept_agg[dept]["skills"].update(r["aligned_skills"])

    # Build text block for narrative prompt. Skills coverage is now
    # decoration on top of the TOP-aligned set, not the gating signal,
    # so the "Missing" line communicates which core skills none of
    # this department's PREPARES_FOR courses develop — useful context
    # for the narrative's curriculum-alignment section.
    core_set = set(core_skills)
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT (gated by TOP-SOC crosswalk):"]
    for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["courses"]), reverse=True):
        skills_str = ", ".join(sorted(data["skills"])) if data["skills"] else "(none of the core skills)"
        missing = core_set - data["skills"]
        missing_str = f". Missing: {', '.join(sorted(missing))}" if missing else ""
        lines.append(f"  {dept}: develops {skills_str} (across {len(data['courses'])} courses){missing_str}")
    dept_text = "\n".join(lines) if dept_agg else ""

    # Sort by course count (largest department first) — with skills as
    # ranker, "more aligned skills" is no longer a meaningful sort key
    # since the gate already passed. Course count is a faithful proxy
    # for the depth of curricular coverage on the SOC's pathway.
    curriculum_evidence = [
        {
            "department": dept,
            "courses": data["courses"],
            "aligned_skills": sorted(data["skills"]),
        }
        for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["courses"]), reverse=True)
    ]

    return dept_text, curriculum_evidence


def _gather_student_pipeline(
    college: str, departments: list[str], soc_code: str, core_skills: list[str]
) -> tuple[dict, list[dict]]:
    """Find students whose academic pathway aligns with the partnership.

    The gating principle: the unit of partnership engagement is the
    department, not the course. A signed partnership with an employer
    benefits every student whose primary focus is in an aligned
    department's pathway, regardless of whether they have yet taken
    the specific course that crosswalks to the selected SOC. Counting
    only course-takers undersells the partnership's scope; the
    headline number should reflect the broader department-rooted
    population.

    Concretely:
      - Eligibility gate: student.primary_focus IN aligned_departments
        (those returned by _gather_aligned_curriculum, derived from
        Department-[:CONTAINS]->Course-[:PREPARES_FOR]->Occupation).
      - Headline count: |eligible students at this college|.
      - "All core skills" subcount: how many of the eligible students
        already demonstrate all the SOC's core skills via HAS_SKILL —
        a finer-grained signal of pipeline readiness.
      - Top-N exemplars: ranked within the eligible set by skill-match
        count, then GPA. Their displayed enrollments are the courses
        they have taken that PREPARES_FOR the selected SOC, so the
        artifact surfaces concrete curricular evidence per student.

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
        return {"total_in_program": 0, "with_all_core_skills": 0}, []

    with driver.session() as session:
        # Headline count: every student whose primary_focus is one of
        # the aligned departments. Restricted to students with at
        # least one enrollment at this college so cross-college
        # Student nodes (synthetic data is per-college today, but the
        # constraint future-proofs the query) don't bleed in.
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
        }

        # Top-10 exemplars: same eligibility gate, ranked by skill-match
        # count then GPA. Per-student enrollments shown are the
        # PREPARES_FOR-aligned courses (the concrete curricular evidence
        # for this SOC). A student may rank into the top-10 with zero
        # PREPARES_FOR enrollments if they're early in their pathway —
        # that's faithful to the "potential beneficiary" framing.
        result = session.run("""
            MATCH (st:Student)
            WHERE st.primary_focus IN $departments
              AND EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            OPTIONAL MATCH (st)-[:HAS_SKILL]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH st, count(DISTINCT sk) AS core_count, collect(DISTINCT sk.name) AS relevant_skills
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
                  -[:PREPARES_FOR]->(:Occupation {soc_code: $soc_code})
            WITH st, core_count, relevant_skills,
                 collect(DISTINCT {code: c.code, name: c.name, grade: e.grade, term: e.term}) AS enrollments
            ORDER BY core_count DESC, st.gpa DESC
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
            "relevant_skills": r["relevant_skills"],
        }
        for i, r in enumerate(result)
    ]

    return student_stats, top_students
