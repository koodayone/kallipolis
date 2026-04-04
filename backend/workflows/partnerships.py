"""Partnership proposal pipeline: context → signal filter → department aggregation → narrative generation."""

from __future__ import annotations

import os
import re
import json
import logging
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import anthropic
from ontology.schema import get_driver
from models import (
    NarrativeProposal, ProposalJustification,
    OccupationEvidence, DepartmentEvidence, CourseEvidence,
    StudentEvidence, StudentSummaryEvidence, StudentEnrollmentEvidence,
)

logger = logging.getLogger(__name__)

TYPE_LABELS = {
    "internship": "Internship Pipeline",
    "curriculum_codesign": "Curriculum Co-Design",
    "advisory_board": "Advisory Board",
}


# ═══════════════════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GatheredContext:
    """Structured output from Neo4j context gathering."""
    employer_name: str = ""
    sector: str = ""
    description: str = ""
    regions: list[str] = field(default_factory=list)
    college: str = ""
    occupation_evidence: list[dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 1: Context Gathering
# ═══════════════════════════════════════════════════════════════════════════


def _gather_targeted_context(employer: str, college: str, engagement_type: str = "") -> GatheredContext:
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


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Signal Filter
# ═══════════════════════════════════════════════════════════════════════════

_OCCUPATION_SELECTION_PROMPT = """Select the primary hiring occupation for this employer. Return ONLY the JSON below — no reasoning, no explanation, no other text.

{context}

Rules:
- Pick the ONE occupation this employer would hire in volume. A plumbing company hires plumbers. A hospital hires nurses. Not generic management or admin roles.
- Pick 3 skills most central to the daily work of that role. Choose ONLY from the skills listed under that occupation. Not generic skills like Record Keeping or Professional Ethics.
- Prefer skills the college develops (course count > 0). You may include one skill with 0 courses if it is genuinely central to the occupation — this represents a curriculum gap worth noting.

{{"selected_occupation": {{"title": "...", "soc_code": "...", "core_skills": ["...", "...", "..."]}}}}"""

_OCCUPATION_SELECTION_CODESIGN_PROMPT = """Select the primary hiring occupation for this employer. Return ONLY the JSON below — no reasoning, no explanation, no other text.

{context}

Rules:
- Pick the ONE occupation this employer would hire in volume. Not generic management or admin roles.
- Pick 3 core skills from the "Skills the college develops" list. These represent existing alignment.

{{"selected_occupation": {{"title": "...", "soc_code": "...", "core_skills": ["...", "...", "..."]}}}}"""


def _build_occupation_selection_context(gathered: GatheredContext) -> str:
    """Build context string for the occupation selection LLM call, including skills per occupation."""
    driver = get_driver()

    # Fetch skills for each occupation with college course coverage
    occ_skills: dict[str, list[dict]] = {}
    with driver.session() as session:
        for occ in gathered.occupation_evidence:
            title = occ["title"]
            result = session.run("""
                MATCH (occ:Occupation {title: $title})-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk)
                RETURN sk.name AS skill, count(DISTINCT c) AS course_count
                ORDER BY skill
            """, title=title, college=gathered.college).data()
            occ_skills[title] = result

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        "",
        "OCCUPATIONS THIS EMPLOYER HIRES FOR:",
    ]
    for occ in gathered.occupation_evidence:
        parts = [f"  {occ['title']}"]
        if occ.get("annual_wage"):
            parts.append(f"${occ['annual_wage']:,}/yr")
        if occ.get("annual_openings"):
            parts.append(f"{occ['annual_openings']:,} openings/yr")
        lines.append(", ".join(parts))
        skills = occ_skills.get(occ["title"], [])
        if skills:
            skill_parts = []
            for s in skills:
                cnt = s["course_count"]
                gap = " — gap" if cnt == 0 else ""
                skill_parts.append(f"{s['skill']} ({cnt} courses{gap})")
            lines.append(f"    Skills: {', '.join(skill_parts)}")
    return "\n".join(line for line in lines if line is not None)


_GAP_IDENTIFICATION_PROMPT = """You are identifying a curriculum gap for a community college partnership proposal.

Employer: {employer_name} ({sector})
Occupation: {occupation}

The college currently develops these skills for this occupation:
{skills_list}

Your task: Identify ONE skill that is critical to the daily practice of this occupation at this employer but is genuinely NOT covered by the college's existing curriculum.

Before selecting, verify your choice against these criteria:
1. SEMANTIC CHECK: Is your proposed skill a synonym, subset, or variant of ANY skill in the list above? "Medication Administration" is a synonym of "Drug Administration." "Patient Triage" is a subset of "Patient Assessment." If there is any semantic overlap, reject it and choose something else.
2. SPECIFICITY: The skill must be specific enough that a curriculum developer could build a course module around it. "Communication" is too broad. "Electronic Health Records (EHR) Navigation" is specific.
3. SCOPE: The skill must be teachable at a community college level. "Surgical Technique" is beyond scope. "Sterile Field Preparation" is within scope.
4. RELEVANCE: The skill must be something this specific employer would value. Consider the employer's sector and operational context.
5. ACTIONABILITY: A faculty-industry working group could reasonably address this gap within one catalog cycle.

Return ONLY this JSON:
{{"gap_skill": "...", "rationale": "one sentence explaining why this skill is absent and why it matters for this occupation at this employer"}}"""


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


def _identify_gap_skill(employer_name: str, sector: str, occupation: str, college_skills: list[str]) -> dict:
    """Dedicated LLM call to identify a genuine curriculum gap skill.

    Returns {gap_skill, rationale}.
    """
    skills_list = "\n".join(f"  - {s}" for s in college_skills)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": _GAP_IDENTIFICATION_PROMPT.format(
            employer_name=employer_name,
            sector=sector or "Unknown",
            occupation=occupation,
            skills_list=skills_list,
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        gap = result.get("gap_skill", "")
        rationale = result.get("rationale", "")
        logger.info(f"Gap skill identified: {gap} — {rationale}")
        return {"gap_skill": gap, "rationale": rationale}
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Gap identification returned invalid JSON ({e})")
        return {"gap_skill": "", "rationale": ""}


def _build_codesign_selection_context(gathered: GatheredContext) -> str:
    """Build context for co-design occupation selection — skills with coverage only, no gap labels."""
    driver = get_driver()

    occ_skills: dict[str, list[dict]] = {}
    with driver.session() as session:
        for occ in gathered.occupation_evidence:
            title = occ["title"]
            result = session.run("""
                MATCH (occ:Occupation {title: $title})-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk)
                WITH sk.name AS skill, count(DISTINCT c) AS course_count
                WHERE course_count > 0
                RETURN skill, course_count
                ORDER BY skill
            """, title=title, college=gathered.college).data()
            occ_skills[title] = result

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        "",
        "OCCUPATIONS THIS EMPLOYER HIRES FOR:",
    ]
    for occ in gathered.occupation_evidence:
        parts = [f"  {occ['title']}"]
        if occ.get("annual_wage"):
            parts.append(f"${occ['annual_wage']:,}/yr")
        if occ.get("annual_openings"):
            parts.append(f"{occ['annual_openings']:,} openings/yr")
        lines.append(", ".join(parts))
        skills = occ_skills.get(occ["title"], [])
        if skills:
            skill_parts = [f"{s['skill']} ({s['course_count']} courses)" for s in skills]
            lines.append(f"    Skills the college develops: {', '.join(skill_parts)}")
    return "\n".join(line for line in lines if line is not None)


def _select_occupation(gathered: GatheredContext, engagement_type: str = "") -> dict:
    """Select the primary occupation for this employer. Returns {title, soc_code, core_skills, gap_skill?}."""
    if engagement_type == "curriculum_codesign":
        context = _build_codesign_selection_context(gathered)
        prompt = _OCCUPATION_SELECTION_CODESIGN_PROMPT
    else:
        context = _build_occupation_selection_context(gathered)
        prompt = _OCCUPATION_SELECTION_PROMPT
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt.format(context=context)}],
    )
    raw_response = message.content[0].text

    try:
        result = _extract_json(raw_response)
        selected = result.get("selected_occupation", {})
        logger.info(f"Occupation selected: {selected.get('title', '?')} ({selected.get('soc_code', '?')})")
        return selected
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Occupation selection returned invalid JSON ({e})")
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# Deterministic Curriculum Query
# ═══════════════════════════════════════════════════════════════════════════


def _gather_aligned_curriculum(college: str, core_skills: list[str]) -> tuple[str, list[dict]]:
    """Fetch departments and courses that develop the core skills for the selected occupation.

    Returns (dept_text_for_prompt, curriculum_evidence_list).
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (sk:Skill)<-[:DEVELOPS]-(c:Course {college: $college})
                  <-[:CONTAINS]-(dept:Department)
            WHERE sk.name IN $core_skills
            RETURN dept.name AS department, c.code AS code, c.name AS name,
                   c.description AS description,
                   c.learning_outcomes AS learning_outcomes,
                   c.course_objectives AS course_objectives,
                   c.skill_mappings AS skill_mappings,
                   collect(DISTINCT sk.name) AS aligned_skills
            ORDER BY dept.name, c.code
        """, core_skills=core_skills, college=college).data()

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

    # Build text block for narrative prompt (includes explicit missing skills)
    core_set = set(core_skills)
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:"]
    for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["skills"]), reverse=True):
        skills_str = ", ".join(sorted(data["skills"]))
        missing = core_set - data["skills"]
        missing_str = f". Missing: {', '.join(sorted(missing))}" if missing else ""
        lines.append(f"  {dept}: develops {skills_str} (across {len(data['courses'])} courses){missing_str}")
    dept_text = "\n".join(lines)

    # Build curriculum_evidence
    curriculum_evidence = [
        {
            "department": dept,
            "courses": data["courses"],
            "aligned_skills": sorted(data["skills"]),
        }
        for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["skills"]), reverse=True)
    ]

    return dept_text, curriculum_evidence


# ═══════════════════════════════════════════════════════════════════════════
# Department Relevance Filter
# ═══════════════════════════════════════════════════════════════════════════

_DEPT_FILTER_PROMPT = """Filter this list of departments to only those that directly train students for this specific occupation. Return ONLY the JSON — no reasoning.

Employer: {employer}
Occupation: {occupation}
Departments: {department_list}

The question is: would coursework in this department contribute to a student's ability to perform this occupation? Remove departments with no plausible connection to the role. An Ornamental Horticulture department does not train Sales Representatives. A Fashion department does not train Food Science Technicians. A Mathematics department does not train Plumbers. But an Agriculture department IS relevant to Food Science Technicians because food science draws on agricultural knowledge.

{{"relevant_departments": ["...", "..."]}}"""


def _filter_relevant_departments(employer: str, occupation: str, departments: list[str]) -> list[str]:
    """Filter departments to those semantically relevant to this employer and occupation."""
    if not departments:
        return departments

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": _DEPT_FILTER_PROMPT.format(
            employer=employer,
            occupation=occupation,
            department_list=", ".join(departments),
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        relevant = result.get("relevant_departments", [])
        logger.info(f"Department filter: {len(relevant)}/{len(departments)} departments kept")
        removed = set(departments) - set(relevant)
        if removed:
            logger.info(f"  Removed: {', '.join(sorted(removed))}")
        return relevant
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Department filter returned invalid JSON ({e}), keeping all")
        return departments


def _select_primary_department_by_count(curriculum_evidence: list[dict]) -> str:
    """Fallback: select the department with the most aligned courses."""
    if not curriculum_evidence:
        return ""
    return max(curriculum_evidence, key=lambda d: len(d["courses"]))["department"]


_PRIMARY_DEPT_PROMPT = """Select the ONE department that is the most natural home for a curriculum co-design partnership focused on this occupation. Return ONLY the JSON — no reasoning.

Employer: {employer}
Occupation: {occupation}
Departments: {department_list}

The question is: which department would a program coordinator naturally approach to build a workforce partnership for this role? Not which department has the most courses — which department's identity and mission most directly align with this occupation.

Prefer departments that train students specifically for this occupation over departments that teach foundational prerequisites. Chemistry and Biology teach foundational science that supports many careers. Agriculture, Culinary, and Nursing train students specifically for their respective industries. For a Food Science Technician at a food manufacturer, prefer Agriculture or Culinary over Chemistry or Biology. If only foundational departments are available, pick the most directly relevant one.

{{"primary_department": "..."}}"""


def _select_primary_department_llm(employer: str, occupation: str, departments: list[str]) -> str:
    """LLM-guided primary department selection for curriculum co-design."""
    if not departments:
        return ""
    if len(departments) == 1:
        return departments[0]

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[{"role": "user", "content": _PRIMARY_DEPT_PROMPT.format(
            employer=employer,
            occupation=occupation,
            department_list=", ".join(departments),
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        primary = result.get("primary_department", "")
        if primary in departments:
            logger.info(f"Primary department selected: {primary}")
            return primary
        logger.warning(f"LLM selected '{primary}' not in department list, falling back")
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Primary department selection returned invalid JSON ({e}), falling back")

    # Fallback to deterministic
    return departments[0]


def _build_dept_text(curriculum_evidence: list[dict], core_skills: list[str]) -> str:
    """Build department-level text for the narrative prompt from filtered evidence."""
    core_set = set(core_skills)
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:"]
    for dept_ev in curriculum_evidence:
        dept = dept_ev["department"]
        skills = set(dept_ev["aligned_skills"])
        skills_str = ", ".join(sorted(skills))
        missing = core_set - skills
        missing_str = f". Missing: {', '.join(sorted(missing))}" if missing else ""
        lines.append(f"  {dept}: develops {skills_str} (across {len(dept_ev['courses'])} courses){missing_str}")
    return "\n".join(lines)


def _build_narrative_context(gathered: GatheredContext, dept_text: str, selected_occ: dict, engagement_type: str = "") -> str:
    """Build the context string for the narrative generation prompt.

    Only includes data scoped to the selected occupation and core skills.
    """
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    core_skills = selected_occ.get("core_skills", [])

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        "",
        f"SELECTED OCCUPATION: {occ_title} ({occ_soc})",
        f"CORE SKILLS: {', '.join(core_skills)}",
        "",
        dept_text,
    ]

    # Economic data for selected occupation only
    for occ_ev in gathered.occupation_evidence:
        if occ_ev.get("title") == occ_title:
            parts = [f"ECONOMIC DATA: {occ_ev['title']}"]
            if occ_ev.get("annual_wage"):
                parts.append(f"${occ_ev['annual_wage']:,}/yr")
            if occ_ev.get("employment"):
                parts.append(f"{occ_ev['employment']:,} employed")
            if occ_ev.get("growth_rate") is not None:
                parts.append(f"{occ_ev['growth_rate']:+.1%} growth")
            if occ_ev.get("annual_openings"):
                parts.append(f"{occ_ev['annual_openings']:,} annual openings")
            lines.append("")
            lines.append(", ".join(parts))
            break

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(line for line in lines if line is not None)


def _build_codesign_context(gathered: GatheredContext, dept_text: str, selected_occ: dict, gap_skill: str, engagement_type: str = "", gap_rationale: str = "") -> str:
    """Build context for curriculum co-design narrative — includes gap skill."""
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    core_skills = selected_occ.get("core_skills", [])

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        "",
        f"SELECTED OCCUPATION: {occ_title} ({occ_soc})",
        f"CORE SKILLS (college develops these): {', '.join(core_skills)}",
        f"GAP SKILL: {gap_skill}",
        f"RATIONALE: {gap_rationale}" if gap_rationale else None,
        "This area can be more rigorously developed through co-design with the employer. A collaborative review would determine the scope and curricular approach.",
        "",
        dept_text,
    ]

    for occ_ev in gathered.occupation_evidence:
        if occ_ev.get("title") == occ_title:
            parts = [f"ECONOMIC DATA: {occ_ev['title']}"]
            if occ_ev.get("annual_wage"):
                parts.append(f"${occ_ev['annual_wage']:,}/yr")
            if occ_ev.get("employment"):
                parts.append(f"{occ_ev['employment']:,} employed")
            if occ_ev.get("growth_rate") is not None:
                parts.append(f"{occ_ev['growth_rate']:+.1%} growth")
            if occ_ev.get("annual_openings"):
                parts.append(f"{occ_ev['annual_openings']:,} annual openings")
            lines.append("")
            lines.append(", ".join(parts))
            break

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(line for line in lines if line is not None)


def _gather_student_pipeline(college: str, departments: list[str], core_skills: list[str]) -> tuple[dict, list[dict]]:
    """Find students enrolled in courses within aligned departments that develop core skills.

    Students are guaranteed to have at least one relevant enrollment.
    Returns (student_stats, top_students_with_detail).
    """
    driver = get_driver()
    num_core = len(core_skills)

    with driver.session() as session:
        # Stats: students enrolled in relevant courses with matching primary_focus
        stats = session.run("""
            MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk:Skill),
                  (c)<-[:CONTAINS]-(dept:Department)
            WHERE sk.name IN $core_skills AND dept.name IN $departments
            WITH collect(DISTINCT c) AS relevant_courses
            UNWIND relevant_courses AS rc
            MATCH (st:Student)-[:ENROLLED_IN]->(rc)
            WHERE ANY(dept IN $departments WHERE st.primary_focus CONTAINS dept
               OR dept CONTAINS st.primary_focus)
            WITH DISTINCT st
            OPTIONAL MATCH (st)-[:HAS_SKILL]->(sk2:Skill)
            WHERE sk2.name IN $core_skills
            WITH st, count(DISTINCT sk2) AS core_count
            RETURN count(st) AS total_in_program,
                   sum(CASE WHEN core_count = $num_core THEN 1 ELSE 0 END) AS with_all_core_skills
        """, college=college, departments=departments, core_skills=core_skills, num_core=num_core).single()

        student_stats = {
            "total_in_program": stats["total_in_program"] if stats else 0,
            "with_all_core_skills": stats["with_all_core_skills"] if stats else 0,
        }

        # Top 10 with all courses developing core skills (filtered by primary_focus)
        result = session.run("""
            MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk:Skill)
            WHERE sk.name IN $core_skills
            WITH collect(DISTINCT c) AS relevant_courses
            UNWIND relevant_courses AS rc
            MATCH (st:Student)-[e:ENROLLED_IN]->(rc)
            WHERE ANY(dept IN $departments WHERE st.primary_focus CONTAINS dept
               OR dept CONTAINS st.primary_focus)
            WITH st, collect(DISTINCT {code: rc.code, name: rc.name, grade: e.grade, term: e.term}) AS enrollments
            OPTIONAL MATCH (st)-[:HAS_SKILL]->(sk2:Skill)
            WHERE sk2.name IN $core_skills
            WITH st, enrollments, collect(DISTINCT sk2.name) AS relevant_skills, count(DISTINCT sk2) AS core_count
            ORDER BY core_count DESC, st.gpa DESC
            LIMIT 10
            RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                   size(enrollments) AS courses_completed,
                   COALESCE(st.gpa, 0.0) AS gpa,
                   core_count AS matching_skills,
                   enrollments, relevant_skills
        """, college=college, departments=departments, core_skills=core_skills).data()

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
                for e in r["enrollments"]
            ],
            "relevant_skills": r["relevant_skills"],
        }
        for i, r in enumerate(result)
    ]

    return student_stats, top_students


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3: Proposal Generation Prompts
# ═══════════════════════════════════════════════════════════════════════════

_NARRATIVE_PREAMBLE = """You are a workforce partnership analyst writing for Kallipolis, an institutional intelligence platform for California community colleges.

Kallipolis voice: short sentences. Direct. No filler. No em dashes. State the fact, move on. Every sentence carries a concrete claim or a specific insight. If a sentence could be cut without losing information, cut it. The reader is a busy program coordinator who will skim past anything that feels like LLM output.

Below is curated institutional context for a specific employer.

{context}

Each section is followed by a structured evidence block with specific figures. Your narrative interprets the evidence. You may cite figures where they make the prose flow naturally, but do not list or enumerate data that the evidence block already presents. Do not speculate about career progressions or advancement pathways unless the data explicitly supports them.

You are writing one continuous argument:
- OPPORTUNITY: why this employer and occupation matter
- CURRICULUM COMPOSITION: which departments align and why
- STUDENT COMPOSITION: whether the pipeline is ready
- ROADMAP: what to do next

Write a single JSON object:

{{
  "opportunity": "<2-3 sentences>",
  "justification": {{
    "curriculum_composition": "<2-3 sentences>",
    "student_composition": "<2-3 sentences>"
  }},
  "roadmap": "<2-3 sentences>"
}}

Section requirements:
- OPPORTUNITY: 2-3 sentences. Why this employer matters in the region for this occupation. What makes this a partnership worth pursuing. Stick to what the data shows. Do not speculate about career ladders or advancement pathways.
- CURRICULUM COMPOSITION: 2-3 sentences. Which departments align with this role and what they contribute. Do not assert how many core skills a department covers or claim complete coverage. The evidence block shows the specific skill-department mappings. Do not introduce skill names that are not in the context.
- STUDENT COMPOSITION: 2-3 sentences. Whether students in these programs are prepared for this role. Reference the departments and core skills from the sections above. Candidates are ranked by how many core skills they've developed, then by GPA. Do not introduce new skill names or characterize the pipeline with subjective language.
- ROADMAP: 2-3 sentences. Concrete next steps. Name departments and timelines.

Tone:
- Short, direct sentences. No subordinate clauses that explain why something matters. State it and move on.
- Figures are fine where they flow naturally. Do not avoid them artificially.
- No em dashes. No rhetorical flourishes. No "remarkably," "notably," "importantly."
- When discussing the college's programs, lead with what the department does well. Frame development areas as opportunities to strengthen existing preparation, not deficiencies to correct. The coordinator built these programs. Respect that work.
- Do not say "gaps," "missing," "does not address," "falls short," or "not fully prepared." Instead say "can be strengthened," "an opportunity to deepen," or "an area for continued development."
- Do not use bullet points or numbered lists.
- Return ONLY valid JSON with no text before or after."""


INTERNSHIP_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Internship Pipeline — structured student work rotations at the employer site.

Type-specific guidance:
- OPPORTUNITY: Why this employer hires for this occupation in this region. What structured rotations would look like. No career ladder speculation.
- CURRICULUM COMPOSITION: Affirm the department's alignment. Which departments prepare students for on-site rotations in this role. Do not suggest the program is insufficient.
- STUDENT COMPOSITION: Students are prepared. Frame their readiness positively.
- ROADMAP: Operational areas for rotations, duration (8-16 weeks), course credit mapping, first-cohort target.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Kaiser Permanente is the largest healthcare employer in the Central Valley, hiring registered nurses at scale with 2,160 annual openings and 7.2% projected growth. An internship pipeline would place students in structured clinical rotations, giving them supervised patient care experience that accelerates licensure readiness.

Curriculum Composition: The Nursing department is the strongest alignment point, developing patient care, clinical documentation, and nursing process skills across its core program. Health Sciences extends this into workplace safety and supervised clinical hours.

Student Composition: Students in the Nursing and Health Sciences programs have completed multiple courses developing the core clinical skills Kaiser requires. The pipeline is concentrated in the right departments with the right preparation.

Roadmap: Convene a meeting between the Nursing department chair and Kaiser's workforce development leadership to identify two to three rotation sites. Define an 8-12 week structure mapped to existing Work Experience course sequences, targeting 8-15 students within two semesters."""


CURRICULUM_CODESIGN_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Curriculum Co-Design — the employer shapes program content through collaboration with faculty to close a specific skill gap.

Type-specific guidance:
- OPPORTUNITY: The college's primary department is well-positioned for this occupation with strong existing alignment. There is one area that a co-design partnership could strengthen further. Tone is collaborative — the college is well-aligned, not falling short.
- CURRICULUM COMPOSITION: Focus on the primary department's strengths across the core skills, then introduce the gap skill as an area that can be more rigorously addressed through collaboration with the employer. Do not say "not addressed" or "missing" — say "can be strengthened" or "can be more rigorously developed." The co-design audit would determine the scope and approach.
- STUDENT COMPOSITION: Students in the primary department who are developing the core skills.
- ROADMAP: Collaborative curriculum review with the primary department and employer, focused on strengthening the identified area. Pilot development within the next catalog cycle.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: The college's Nursing department is well-aligned with Adventist Health's registered nurse hiring needs. A co-design partnership would strengthen the program further by developing areas like EHR proficiency that are increasingly central to clinical workflows.

Curriculum Composition: Nursing develops Clinical Documentation, Nursing Process, and Patient Assessment across its core program. EHR navigation is a practical requirement in modern hospital settings that can be more rigorously developed through collaboration with Adventist Health's clinical education team.

Student Composition: Nursing students are completing coursework in the core clinical skills this role requires. They represent the strongest candidates for a co-design effort that strengthens their readiness for the specific clinical environment at Adventist Health.

Roadmap: Convene a working group between the Nursing department chair and Adventist Health's clinical education leadership. Evaluate EHR coverage and other practice-specific requirements, then pilot revised content within the next catalog cycle."""


ADVISORY_BOARD_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Advisory Board — ongoing strategic guidance from the employer to inform program direction.

Type-specific guidance:
- OPPORTUNITY: Why this employer's perspective matters for the college's programs. No grant funding required.
- CURRICULUM COMPOSITION: Which departments the board would advise. Areas for continued development as inaugural agenda items.
- ROADMAP: Formal invitation, inaugural meeting with 2-3 topics, quarterly cadence.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill hires across eight occupations in the Central Valley with over 4,500 combined annual openings. That hiring breadth makes their perspective on workforce readiness relevant to several college programs. An advisory board would formalize this as an ongoing channel for industry guidance, requiring no grant funding.

Curriculum Composition: The Agriculture, Work Experience, and Business departments cover the core skill areas Cargill hires for. Auditing and labor relations are areas where Cargill's perspective could strengthen program content.

Student Composition: Students in these programs are developing skills relevant to Cargill's operations. The advisory board would give Cargill a way to share current industry standards and help the college stay calibrated.

Roadmap: Send a formal invitation to Cargill's Central Valley regional leadership proposing a quarterly advisory board scoped to Agriculture, Business, and Food Services. The inaugural meeting should address curriculum alignment and identified skill gaps."""


PROMPTS: dict[str, str] = {
    "internship": INTERNSHIP_PROMPT,
    "curriculum_codesign": CURRICULUM_CODESIGN_PROMPT,
    "advisory_board": ADVISORY_BOARD_PROMPT,
}


# ═══════════════════════════════════════════════════════════════════════════
# Parsing & Assembly
# ═══════════════════════════════════════════════════════════════════════════


def _extract_json(raw: str) -> dict:
    """Extract the first valid JSON object from a string."""
    stripped = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
    if fence_match:
        stripped = fence_match.group(1).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    if start == -1:
        raise ValueError("No JSON object found")

    depth = 0
    for i in range(start, len(stripped)):
        if stripped[i] == "{":
            depth += 1
        elif stripped[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(stripped[start:i + 1])
                except json.JSONDecodeError:
                    break

    match = re.search(r"\{[\s\S]*\}", stripped)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Could not extract valid JSON from response")


def _parse_narrative_fields(raw: str) -> dict:
    """Extract LLM-generated narrative fields from Claude's JSON response."""
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    data = _extract_json(raw)

    return {
        "opportunity": data.get("opportunity", ""),
        "justification": {
            "curriculum_composition": data.get("justification", {}).get("curriculum_composition", ""),
            "student_composition": data.get("justification", {}).get("student_composition", ""),
        },
        "roadmap": data.get("roadmap", ""),
    }


def _assemble_proposal(
    narrative: dict,
    employer: str,
    sector: str | None,
    partnership_type: str,
    gathered: GatheredContext,
    curriculum_evidence: list[dict],
    selected_occ: dict,
    student_stats: dict,
    top_students: list[dict],
    core_skills: list[str] | None = None,
    gap_skill: str = "",
) -> NarrativeProposal:
    """Merge LLM-generated narrative with deterministic evidence blocks."""
    return NarrativeProposal(
        employer=employer,
        sector=sector,
        partnership_type=partnership_type,
        selected_occupation=selected_occ.get("title", ""),
        selected_soc_code=selected_occ.get("soc_code"),
        core_skills=core_skills or selected_occ.get("core_skills", []),
        gap_skill=gap_skill,
        regions=gathered.regions,
        opportunity=narrative["opportunity"],
        opportunity_evidence=[
            OccupationEvidence(**o) for o in gathered.occupation_evidence
            if o.get("title") == selected_occ.get("title")
        ] or [OccupationEvidence(**o) for o in gathered.occupation_evidence[:1]],
        justification=ProposalJustification(
            curriculum_composition=narrative["justification"]["curriculum_composition"],
            curriculum_evidence=[DepartmentEvidence(**d) for d in curriculum_evidence],
            student_composition=narrative["justification"]["student_composition"],
            student_evidence=StudentEvidence(
                total_in_program=student_stats.get("total_in_program", 0),
                with_all_core_skills=student_stats.get("with_all_core_skills", 0),
                top_students=[StudentSummaryEvidence(**s) for s in top_students],
            ),
        ),
        roadmap=narrative["roadmap"],
    )


def _get_prompt(engagement_type: str, context: str) -> str:
    """Select and format the type-specific prompt template."""
    template = PROMPTS.get(engagement_type, INTERNSHIP_PROMPT)
    return template.format(context=context)


def _call_claude(prompt_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    )
    return message.content[0].text


# ═══════════════════════════════════════════════════════════════════════════
# Evaluation
# ═══════════════════════════════════════════════════════════════════════════

_EVAL_PROMPT = """Evaluate this partnership proposal against two quality rules.

CURATED CONTEXT:
{context}

GENERATED PROPOSAL:
{proposal}

RULES:

1. FAITHFULNESS: Any directional claims (e.g., "highest-volume", "fastest-growing", "strongest alignment") must be supported by the relative ordering in the curated context data. Any department names, skill names, or region names must appear in the context. Flag fabricated or unsupported claims.

2. NO_DATA_IN_NARRATIVE: The narrative sections (opportunity, curriculum_composition, student_composition) should NOT contain specific dollar amounts (e.g., "$80,560"), specific percentages (e.g., "4.7%"), specific counts (e.g., "940 annual openings", "15,000 students"), or specific employment numbers. These belong in the evidence blocks, not the prose. The roadmap section is exempt. Flag any specific figures found in the narrative sections.

Respond with ONLY this JSON object. No reasoning. No commentary. No markdown fences.

{{"faithfulness": {{"pass": true, "violations": []}}, "no_data_in_narrative": {{"pass": true, "violations": []}}}}

Change "pass" to false and add violation strings only where a rule is violated."""

_EVAL_RULES = ["faithfulness", "no_data_in_narrative"]


def _evaluate_proposal(proposal: NarrativeProposal, curated_context: str) -> dict:
    """Evaluate a generated proposal against quality rules. Non-blocking."""
    proposal_text = (
        f"OPPORTUNITY:\n{proposal.opportunity}\n\n"
        f"CURRICULUM COMPOSITION:\n{proposal.justification.curriculum_composition}\n\n"
        f"STUDENT COMPOSITION:\n{proposal.justification.student_composition}\n\n"
        f"ROADMAP:\n{proposal.roadmap}"
    )

    prompt = _EVAL_PROMPT.format(context=curated_context, proposal=proposal_text)

    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1536,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        result = _extract_json(raw)

        passed = sum(1 for r in _EVAL_RULES if result.get(r, {}).get("pass", False))
        logger.info(f"Proposal eval for {proposal.employer}: {passed}/{len(_EVAL_RULES)} rules passed")
        for rule in _EVAL_RULES:
            rule_result = result.get(rule, {})
            if not rule_result.get("pass", True):
                for v in rule_result.get("violations", []):
                    logger.warning(f"  FAIL [{rule}]: {v}")

        return result

    except Exception as e:
        logger.error(f"Proposal evaluation failed: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline entry points
# ═══════════════════════════════════════════════════════════════════════════


def _build_proposal_context(employer: str, college: str, engagement_type: str, gathered: GatheredContext, selected_occ: dict):
    """Shared pipeline logic: build curriculum evidence, students, and narrative context.

    Returns (curriculum_evidence, student_stats, top_students, narrative_context, core_skills, gap_skill).
    """
    core_skills = selected_occ.get("core_skills", [])
    gap_skill = ""
    gap_rationale = ""

    # Curriculum co-design: dedicated gap identification
    if engagement_type == "curriculum_codesign":
        occ_title = selected_occ.get("title", "")
        college_skills = _get_developed_skills(college, occ_title)
        gap_result = _identify_gap_skill(gathered.employer_name, gathered.sector, occ_title, college_skills)
        gap_skill = gap_result.get("gap_skill", "")
        gap_rationale = gap_result.get("rationale", "")

    _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

    # Filter departments by semantic relevance
    all_dept_names = [d["department"] for d in curriculum_evidence]
    relevant_depts = _filter_relevant_departments(gathered.employer_name, selected_occ.get("title", ""), all_dept_names)
    curriculum_evidence = [d for d in curriculum_evidence if d["department"] in relevant_depts]

    # Curriculum co-design: narrow to one primary department via LLM
    if engagement_type == "curriculum_codesign" and curriculum_evidence:
        dept_names = [d["department"] for d in curriculum_evidence]
        primary_dept = _select_primary_department_llm(
            gathered.employer_name, selected_occ.get("title", ""), dept_names
        )
        curriculum_evidence = [d for d in curriculum_evidence if d["department"] == primary_dept]

    dept_text = _build_dept_text(curriculum_evidence, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)

    # Build narrative context — co-design gets gap skill + rationale
    if engagement_type == "curriculum_codesign":
        narrative_context = _build_codesign_context(gathered, dept_text, selected_occ, gap_skill, engagement_type, gap_rationale)
    else:
        narrative_context = _build_narrative_context(gathered, dept_text, selected_occ, engagement_type)

    return curriculum_evidence, student_stats, top_students, narrative_context, core_skills, gap_skill


async def run_targeted_proposal(employer: str, college: str, engagement_type: str = "") -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered, engagement_type)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    curriculum_evidence, student_stats, top_students, narrative_context, core_skills, gap_skill = \
        _build_proposal_context(employer, college, engagement_type, gathered, selected_occ)

    prompt_text = _get_prompt(engagement_type, narrative_context)
    raw = _call_claude(prompt_text)
    logger.info("Stage 3 complete: Claude response received")

    narrative = _parse_narrative_fields(raw)
    partnership_type = TYPE_LABELS.get(engagement_type, engagement_type)
    proposal = _assemble_proposal(narrative, employer, gathered.sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students, core_skills, gap_skill)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Proposal complete for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a NarrativeProposal when Claude's streaming response completes."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered, engagement_type)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    curriculum_evidence, student_stats, top_students, narrative_context, core_skills, gap_skill = \
        _build_proposal_context(employer, college, engagement_type, gathered, selected_occ)

    prompt_text = _get_prompt(engagement_type, narrative_context)
    logger.info(f"Stage 3: starting Claude stream for {employer} ({engagement_type})...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

    narrative = _parse_narrative_fields(accumulated)
    partnership_type = TYPE_LABELS.get(engagement_type, engagement_type)
    proposal = _assemble_proposal(narrative, employer, gathered.sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students, core_skills, gap_skill)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Stream complete: proposal for {employer}")
    yield proposal
