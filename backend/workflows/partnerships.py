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

{{"selected_occupation": {{"title": "...", "soc_code": "...", "core_skills": ["...", "...", "..."]}}}}"""


def _build_occupation_selection_context(gathered: GatheredContext) -> str:
    """Build context string for the occupation selection LLM call, including skills per occupation."""
    driver = get_driver()

    # Fetch skills for each occupation
    occ_skills: dict[str, list[str]] = {}
    with driver.session() as session:
        for occ in gathered.occupation_evidence:
            title = occ["title"]
            result = session.run("""
                MATCH (occ:Occupation {title: $title})-[:REQUIRES_SKILL]->(sk:Skill)
                RETURN sk.name AS skill
                ORDER BY skill
            """, title=title).data()
            occ_skills[title] = [r["skill"] for r in result]

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
            lines.append(f"    Skills: {', '.join(skills)}")
    return "\n".join(line for line in lines if line is not None)


def _select_occupation(gathered: GatheredContext) -> dict:
    """Select the primary occupation for this employer. Returns {title, soc_code, core_skills}."""
    context = _build_occupation_selection_context(gathered)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": _OCCUPATION_SELECTION_PROMPT.format(context=context)}],
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
- Do not use bullet points or numbered lists.
- Return ONLY valid JSON with no text before or after."""


INTERNSHIP_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Internship Pipeline — structured student work rotations at the employer site.

Type-specific guidance:
- OPPORTUNITY: Why this employer hires for this occupation in this region. What structured rotations would look like. No career ladder speculation.
- CURRICULUM COMPOSITION: Which departments prepare students for on-site rotations in this role.
- ROADMAP: Operational areas for rotations, duration (8-16 weeks), course credit mapping, first-cohort target.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Kaiser Permanente is the largest healthcare employer in the Central Valley, hiring registered nurses at scale with 2,160 annual openings and 7.2% projected growth. An internship pipeline would place students in structured clinical rotations, giving them supervised patient care experience that accelerates licensure readiness.

Curriculum Composition: The Nursing department is the strongest alignment point, developing patient care, clinical documentation, and nursing process skills across its core program. Health Sciences extends this into workplace safety and supervised clinical hours.

Student Composition: Students in the Nursing and Health Sciences programs have completed multiple courses developing the core clinical skills Kaiser requires. The pipeline is concentrated in the right departments with the right preparation.

Roadmap: Convene a meeting between the Nursing department chair and Kaiser's workforce development leadership to identify two to three rotation sites. Define an 8-12 week structure mapped to existing Work Experience course sequences, targeting 8-15 students within two semesters."""


CURRICULUM_CODESIGN_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Curriculum Co-Design — the employer shapes program content and quality through ongoing collaboration with faculty.

Type-specific guidance:
- OPPORTUNITY: What the employer needs that the college doesn't yet develop. Why that gap matters given regional demand.
- CURRICULUM COMPOSITION: Most important section. Lead with skill gaps and which departments would close them.
- ROADMAP: Faculty-industry working group, curriculum gap audit, pilot revision, quarterly review.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill hires food science technicians at $47,950/yr with 190 annual openings in the Central Valley, but the college's curriculum doesn't fully develop the skills that role requires. A co-design partnership would close that gap by embedding Cargill's standards into program content.

Curriculum Composition: The Business department has the strongest existing alignment but lacks auditing coverage, a skill Cargill requires for its accounting roles. The Agriculture department's supply chain content may need deepening to match the employer's logistics environment.

Student Composition: Students in the Business and Agriculture programs are already developing skills relevant to Cargill's operations. The co-design effort would sharpen existing preparation rather than build it from scratch.

Roadmap: Convene a faculty-industry working group with Business and Agriculture department chairs alongside Cargill's HR and operations leadership. Identify two to three courses for pilot revision in the next catalog cycle with quarterly review."""


ADVISORY_BOARD_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Advisory Board — ongoing strategic guidance from the employer to inform program direction.

Type-specific guidance:
- OPPORTUNITY: Why this employer's perspective matters for the college's programs. No grant funding required.
- CURRICULUM COMPOSITION: Which departments the board would advise. Skill gaps as inaugural agenda items.
- ROADMAP: Formal invitation, inaugural meeting with 2-3 topics, quarterly cadence.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill hires across eight occupations in the Central Valley with over 4,500 combined annual openings. That hiring breadth makes their perspective on workforce readiness relevant to several college programs. An advisory board would formalize this as an ongoing channel for industry guidance, requiring no grant funding.

Curriculum Composition: The Agriculture, Work Experience, and Business departments cover the core skill areas Cargill hires for. Gaps in auditing and labor relations are natural inaugural agenda items.

Student Composition: Students in these programs are developing skills relevant to Cargill's operations. The advisory board would give Cargill a way to assess whether that preparation meets current standards.

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
) -> NarrativeProposal:
    """Merge LLM-generated narrative with deterministic evidence blocks."""
    return NarrativeProposal(
        employer=employer,
        sector=sector,
        partnership_type=partnership_type,
        selected_occupation=selected_occ.get("title", ""),
        selected_soc_code=selected_occ.get("soc_code"),
        core_skills=core_skills or selected_occ.get("core_skills", []),
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


async def run_targeted_proposal(employer: str, college: str, engagement_type: str = "") -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

    # Filter departments by semantic relevance
    all_dept_names = [d["department"] for d in curriculum_evidence]
    relevant_depts = _filter_relevant_departments(gathered.employer_name, selected_occ.get("title", ""), all_dept_names)
    curriculum_evidence = [d for d in curriculum_evidence if d["department"] in relevant_depts]
    dept_text = _build_dept_text(curriculum_evidence, core_skills)

    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)
    narrative_context = _build_narrative_context(gathered, dept_text, selected_occ, engagement_type)

    prompt_text = _get_prompt(engagement_type, narrative_context)
    raw = _call_claude(prompt_text)
    logger.info("Stage 3 complete: Claude response received")

    narrative = _parse_narrative_fields(raw)
    partnership_type = TYPE_LABELS.get(engagement_type, engagement_type)
    proposal = _assemble_proposal(narrative, employer, gathered.sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students, core_skills)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Proposal complete for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a NarrativeProposal when Claude's streaming response completes."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

    # Filter departments by semantic relevance
    all_dept_names = [d["department"] for d in curriculum_evidence]
    relevant_depts = _filter_relevant_departments(gathered.employer_name, selected_occ.get("title", ""), all_dept_names)
    curriculum_evidence = [d for d in curriculum_evidence if d["department"] in relevant_depts]
    dept_text = _build_dept_text(curriculum_evidence, core_skills)

    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)
    narrative_context = _build_narrative_context(gathered, dept_text, selected_occ, engagement_type)

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
    proposal = _assemble_proposal(narrative, employer, gathered.sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students, core_skills)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Stream complete: proposal for {employer}")
    yield proposal
