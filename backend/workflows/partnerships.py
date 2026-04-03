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
    StudentEvidence, StudentSummaryEvidence,
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
    text: str                                  # Full text context
    occupation_evidence: list[dict] = field(default_factory=list)
    student_evidence: dict = field(default_factory=dict)
    regions: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 1: Context Gathering
# ═══════════════════════════════════════════════════════════════════════════


def _gather_targeted_context(employer: str, college: str, engagement_type: str = "") -> GatheredContext:
    """Gather employer-specific context from the graph. Returns structured data + text."""
    driver = get_driver()
    lines = []
    occupation_evidence = []
    student_evidence = {"total_students": 0, "students_with_3plus_courses": 0, "top_skills": []}

    with driver.session() as session:
        # A. Employer overview
        emp_result = session.run("""
            MATCH (emp:Employer {name: $employer})
            OPTIONAL MATCH (emp)-[:IN_MARKET]->(r:Region)
            RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                   collect(COALESCE(r.display_name, r.name)) AS regions
        """, employer=employer).single()

        if not emp_result:
            raise ValueError(f"Employer '{employer}' not found in the graph.")

        lines.append(f"EMPLOYER: {emp_result['name']}")
        if emp_result["sector"]:
            lines.append(f"Sector: {emp_result['sector']}")
        if emp_result["description"]:
            lines.append(f"Description: {emp_result['description']}")
        if emp_result["regions"]:
            lines.append(f"Regions: {', '.join(emp_result['regions'])}")
        lines.append(f"College: {college}")

        # B. Skill alignment detail (course-level, for signal filter)
        skill_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:IN_MARKET]->(r:Region),
                  (emp)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r),
                  (occ)-[:REQUIRES_SKILL]->(sk:Skill)
            OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
            OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
            RETURN occ.title AS occupation, d.annual_wage AS annual_wage,
                   sk.name AS skill,
                   CASE WHEN course IS NOT NULL THEN true ELSE false END AS developed,
                   course.code AS course_code, course.name AS course_name,
                   dept.name AS department
        """, employer=employer, college=college).data()

        occ_skills: dict[str, dict] = defaultdict(lambda: {"wage": None, "aligned": [], "gaps": []})
        for r in skill_result:
            occ = r["occupation"]
            occ_skills[occ]["wage"] = r["annual_wage"]
            if r["developed"] and r["course_code"]:
                occ_skills[occ]["aligned"].append({
                    "skill": r["skill"],
                    "course_code": r["course_code"],
                    "course_name": r["course_name"],
                    "department": r["department"] or "Unknown",
                })
            else:
                occ_skills[occ]["gaps"].append(r["skill"])

        lines.append("")
        lines.append("SKILL ALIGNMENT BY OCCUPATION:")
        total_aligned = 0
        total_gaps = 0
        for occ, data in occ_skills.items():
            wage_str = f" (${data['wage']:,}/yr)" if data["wage"] else ""
            lines.append(f"\n  {occ}{wage_str}:")
            if data["aligned"]:
                lines.append("    Aligned Skills (college develops these):")
                seen = set()
                for entry in data["aligned"]:
                    if entry["skill"] not in seen:
                        seen.add(entry["skill"])
                        lines.append(f"      - {entry['skill']} → {entry['course_code']} {entry['course_name']} ({entry['department']})")
                        total_aligned += 1
            if data["gaps"]:
                unique_gaps = list(dict.fromkeys(data["gaps"]))
                lines.append("    Unmapped Skills (required by employer, not currently mapped to college courses):")
                for gap in unique_gaps:
                    lines.append(f"      - {gap}")
                    total_gaps += 1

        lines.append(f"\nSUMMARY: {total_aligned} aligned skills, {total_gaps} skill gaps across {len(occ_skills)} occupations.")

        # Skill → occupation count for ranking pipeline skills
        skill_occ_count: dict[str, int] = Counter()
        for occ, data in occ_skills.items():
            for entry in data["aligned"]:
                skill_occ_count[entry["skill"]] += 1
            for gap in data["gaps"]:
                skill_occ_count[gap] += 1

        # C. Student pipeline
        pipeline_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
                  -[:REQUIRES_SKILL]->(sk:Skill)<-[:HAS_SKILL]-(st:Student)
            WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            WITH DISTINCT st, collect(DISTINCT sk.name) AS student_skills
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
            WHERE e.grade IN ['A','B','C','P']
            WITH st, student_skills, count(DISTINCT c) AS completed
            RETURN count(st) AS total_students,
                   sum(CASE WHEN completed >= 3 THEN 1 ELSE 0 END) AS deep_pipeline,
                   reduce(all_skills = [], s IN collect(student_skills) | all_skills + s) AS flat_skills
        """, employer=employer, college=college).single()

        if pipeline_result and pipeline_result["total_students"] > 0:
            pipeline_skill_set = set(pipeline_result["flat_skills"])
            relevant_skills = [
                s for s, _ in sorted(skill_occ_count.items(), key=lambda x: x[1], reverse=True)
                if s in pipeline_skill_set
            ][:5]

            student_evidence = {
                "total_students": pipeline_result["total_students"],
                "students_with_3plus_courses": pipeline_result["deep_pipeline"],
                "top_skills": relevant_skills,
            }

            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append(f"  Total students with relevant skills: {pipeline_result['total_students']}")
            lines.append(f"  Students with 3+ completed courses: {pipeline_result['deep_pipeline']}")
            if relevant_skills:
                lines.append(f"  Top employer-relevant skills in pipeline: {', '.join(relevant_skills)}")
        else:
            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append("  Total students with relevant skills: 0")
            lines.append("  Students with 3+ completed courses: 0")

        # D. Regional employment (also builds occupation_evidence)
        econ_result = session.run("""
            MATCH (:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                  <-[:HIRES_FOR]-(emp:Employer {name: $employer})
            RETURN occ.title AS title, occ.soc_code AS soc_code,
                   d.annual_wage AS annual_wage,
                   d.employment AS employment, d.growth_rate AS growth_rate,
                   d.annual_openings AS annual_openings,
                   COALESCE(r.display_name, r.name) AS region
        """, employer=employer, college=college).data()

        if econ_result:
            lines.append("")
            lines.append("ECONOMIC DATA (regional employment, wages, and demand projections):")
            for r in econ_result:
                wage = f"${r['annual_wage']:,}/yr" if r["annual_wage"] else "wage unavailable"
                emp_count = f"{r['employment']:,} employed" if r["employment"] else "employment data unavailable"
                parts = [f"{r['title']} in {r['region']}: {wage}, {emp_count}"]
                if r.get("growth_rate") is not None:
                    parts.append(f"{r['growth_rate']:+.1%} growth (2024-2029)")
                if r.get("annual_openings") is not None:
                    parts.append(f"{r['annual_openings']:,} annual openings")
                lines.append(f"  {', '.join(parts)}")

                occupation_evidence.append({
                    "title": r["title"],
                    "soc_code": r.get("soc_code"),
                    "annual_wage": r["annual_wage"],
                    "employment": r["employment"],
                    "annual_openings": r.get("annual_openings"),
                    "growth_rate": r.get("growth_rate"),
                })

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return GatheredContext(
        text="\n".join(lines),
        occupation_evidence=occupation_evidence,
        student_evidence=student_evidence,
        regions=emp_result["regions"] if emp_result else [],
    )


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Signal Filter
# ═══════════════════════════════════════════════════════════════════════════

_OCCUPATION_SELECTION_PROMPT = """You are selecting the primary hiring occupation for a community college partnership proposal.

Given this employer data:

{context}

Select the ONE occupation that most credibly represents this employer's primary hiring need — the role they would hire in volume. A plumbing company hires plumbers. A hospital hires nurses. A food manufacturer hires food science technicians. Do not select generic management or administrative roles unless the employer is specifically a management consulting or staffing firm.

Then identify the 3 skills most central to the day-to-day work of that occupation. These should be the skills that define the role — not generic skills like Record Keeping or Professional Ethics that any job requires. For an HVAC mechanic: HVAC Systems, Refrigeration, Plumbing. For a registered nurse: Patient Care, Clinical Documentation, Nursing Process. Choose only from the skills listed in the data.

Return ONLY this JSON with no other text:
{{"selected_occupation": {{"title": "...", "soc_code": "...", "core_skills": ["...", "...", "..."]}}}}"""


def _select_occupation(raw_context: str) -> dict:
    """Select the primary occupation for this employer. Returns {title, soc_code}."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": _OCCUPATION_SELECTION_PROMPT.format(context=raw_context)}],
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

    # Build text block for narrative prompt
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:"]
    for dept, data in sorted(dept_agg.items(), key=lambda x: len(x[1]["skills"]), reverse=True):
        skills_str = ", ".join(sorted(data["skills"]))
        lines.append(f"  {dept}: develops {skills_str} (across {len(data['courses'])} courses)")
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


def _build_narrative_context(gathered: GatheredContext, dept_text: str, selected_occ: dict) -> str:
    """Build the context string for the narrative generation prompt.

    Uses selected occupation + department-level alignment + student pipeline + economic data.
    """
    lines = []

    # Extract employer header, student pipeline, and economic data from gathered text
    sections = gathered.text.split("\n\n")
    for section in sections:
        stripped = section.strip()
        if stripped.startswith("EMPLOYER:") or stripped.startswith("College:"):
            lines.append(section)
        elif stripped.startswith("STUDENT PIPELINE:"):
            lines.append(section)
        elif stripped.startswith("ECONOMIC DATA"):
            lines.append(section)
        elif stripped.startswith("PARTNERSHIP ENGAGEMENT TYPE:"):
            lines.append(section)

    # Insert selected occupation and department-level alignment
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    lines.insert(1, f"\nSELECTED OCCUPATION: {occ_title} ({occ_soc})\nThis is the occupation the partnership proposal focuses on. All narrative sections should be about placing students into this specific role at this employer.")
    lines.insert(2, "")
    lines.insert(3, dept_text)

    return "\n\n".join(lines)


def _gather_top_students(college: str, departments: list[str], core_skills: list[str]) -> tuple[dict, list[dict]]:
    """Fetch student pipeline stats and top 10 candidates by primary_focus match.

    Returns (student_stats, top_students_list).
    student_stats: {total_in_program, with_all_core_skills}
    """
    driver = get_driver()
    num_core = len(core_skills)

    with driver.session() as session:
        # Aggregate stats: students whose primary_focus matches aligned departments
        stats = session.run("""
            MATCH (st:Student)
            WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
              AND ANY(dept IN $departments WHERE st.primary_focus CONTAINS dept
                 OR dept CONTAINS st.primary_focus)
            WITH st
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

        # Top 10 candidates by primary_focus match, sorted by GPA
        result = session.run("""
            MATCH (st:Student)
            WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
              AND ANY(dept IN $departments WHERE st.primary_focus CONTAINS dept
                 OR dept CONTAINS st.primary_focus)
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
            WHERE e.grade IN ['A','B','C','P']
            WITH st, count(DISTINCT c) AS completed
            ORDER BY st.gpa DESC, completed DESC
            LIMIT 10
            RETURN st.uuid AS uuid, st.primary_focus AS primary_focus,
                   completed AS courses_completed,
                   COALESCE(st.gpa, 0.0) AS gpa
        """, college=college, departments=departments).data()

    top_students = [
        {
            "uuid": r["uuid"],
            "display_number": i + 1,
            "primary_focus": r["primary_focus"] or "",
            "courses_completed": r["courses_completed"],
            "gpa": round(r["gpa"], 2),
            "matching_skills": 0,
        }
        for i, r in enumerate(result)
    ]

    return student_stats, top_students


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3: Proposal Generation Prompts
# ═══════════════════════════════════════════════════════════════════════════

_NARRATIVE_PREAMBLE = """You are a workforce partnership analyst writing for Kallipolis, an institutional intelligence platform for California community colleges.

Write in the Kallipolis voice: clear, elegant, restrained. Every sentence earns its place through insight, not data. Favor clarity and economy of words. Write prose that a thoughtful analyst would write — not a template filled in. The reader is a busy program coordinator who will skim past anything that feels robotic or formulaic.

Below is curated institutional context for a specific employer.

{context}

Each section of the proposal is followed by a structured evidence block that presents all specific figures — wages, openings, growth rates, department details, student counts, skill lists. Your narrative must never duplicate those figures. Your job is to interpret what the evidence means, not to read it aloud. You may reference that supporting evidence follows (e.g., "the occupations below", "as the evidence shows").

You are writing one continuous argument. Each section picks up where the previous one left off:
- OPPORTUNITY establishes the economic case
- CURRICULUM COMPOSITION answers "can we meet that demand?"
- STUDENT COMPOSITION confirms "is the pipeline real?"
- ROADMAP proposes "what do we do next?"

Write a partnership proposal as a single JSON object:

{{
  "opportunity": "<2-4 sentences>",
  "justification": {{
    "curriculum_composition": "<2-4 sentences>",
    "student_composition": "<2-4 sentences>"
  }},
  "roadmap": "<2-4 sentences>"
}}

Section requirements:
- OPPORTUNITY: 2-4 sentences. Describe the employment opportunity — why this employer matters in the region, what the career pathway looks like, why the demand structure warrants a partnership. Do not cite specific wages, openings, or growth rates — the evidence block presents those.
- CURRICULUM COMPOSITION: 2-4 sentences. Articulate which departments are the strongest alignment points and why. Do not enumerate course counts or skill lists. When mentioning skill gaps, use hedged language — these may reflect data limitations.
- STUDENT COMPOSITION: 2-4 sentences. Interpret the pipeline — connect the curriculum to student readiness. Is it deep or shallow, concentrated or broad? Do not restate totals or skill names.
- ROADMAP: 2-4 sentences. Directional next steps. This section may reference specific departments and timelines since it has no evidence block.

Tone:
- Measured advocacy grounded in evidence is appropriate. Confidence is earned when the evidence block supports the claim.
- Do not use bullet points or numbered lists. Write in flowing prose.
- Return ONLY valid JSON with no text before or after."""


INTERNSHIP_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Internship Pipeline — structured student work rotations at the employer site.

Type-specific guidance:
- OPPORTUNITY: Frame the career pathway — entry-level roles leading to management — and why structured rotations at this employer connect students to it.
- CURRICULUM COMPOSITION: Identify which departments produce students ready for on-site rotations.
- ROADMAP: Reference identifying operational areas for rotations, rotation duration (8-16 weeks), mapping to existing course sequences for academic credit, and a first-cohort target.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Kaiser Permanente anchors the Central Valley's healthcare hiring pipeline, with nursing and clinical support roles generating the highest-volume openings in the region and compensation that reflects the progression from bedside care through clinical management. An internship pipeline would place students in structured rotations across nursing, clinical, and administrative functions, building supervised experience at one of the region's largest healthcare employers and connecting a credentialed local workforce to a career pathway with demonstrated upward mobility.

Curriculum Composition: The college's Nursing department is the strongest alignment point, with clinical documentation, patient care, and nursing process competencies mapping directly to Kaiser's highest-volume hiring needs. The Health Sciences and Work Experience departments extend this alignment into workplace safety and supervised professional hours that translate to hospital rotation readiness, while the Business department offers a moderate administrative pathway.

Student Composition: The pipeline runs deep — the vast majority of students with relevant skills have completed three or more courses in aligned programs, indicating genuine program commitment rather than incidental enrollment. The strongest skill concentrations map directly to the clinical and compliance functions that define entry-level hospital rotations.

Roadmap: The first step is to convene a meeting between the Nursing and Health Sciences department chairs and Kaiser's workforce development leadership to identify two to three rotation sites. The college and Kaiser should define an 8–12 week structure mapped to existing Work Experience course sequences, targeting a first cohort of 8–15 students within two semesters."""


CURRICULUM_CODESIGN_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Curriculum Co-Design — the employer shapes program content and quality through ongoing collaboration with faculty.

Type-specific guidance:
- OPPORTUNITY: Frame the case for curriculum evolution — what the employer needs that the college doesn't yet fully develop, and why that gap matters given the demand landscape.
- CURRICULUM COMPOSITION: This is the most important section. Lead with skill gaps and which departments would be involved in closing them.
- ROADMAP: Reference convening a faculty-industry working group, conducting a curriculum gap audit, piloting revised content, and establishing a quarterly review cadence.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill's hiring portfolio in the Central Valley includes several high-demand roles where the college's graduates are nearly — but not fully — competitive. The gap is specific and addressable: a small number of employer-required skills are absent from the college's current curriculum, affecting occupations with substantial regional openings and attractive compensation. A co-design partnership would embed Cargill's operational standards directly into program development to close that distance.

Curriculum Composition: The Business department carries the strongest existing alignment but has a notable gap — auditing competencies required by Cargill's accounting roles are not currently developed by any mapped course, creating a clear co-design target. The Agriculture department's supply chain coverage is relevant but may need deepening to reflect the employer's specific logistics environment, and skill gaps in labor relations represent a second addressable target.

Student Composition: The college already has a large, deeply engaged pipeline of students developing skills relevant to Cargill's operations. The co-design effort would be sharpening an existing workforce, not building one from scratch — closing specific skill gaps to extend the pipeline's competitiveness into roles it currently doesn't reach.

Roadmap: The first step is to convene a faculty-industry working group with the Business and Agriculture departments alongside Cargill's HR and operations leadership, structuring the initial session as a curriculum gap audit. The working group should identify two to three courses for pilot revision in the next catalog cycle, with a quarterly review cadence to assess whether changes are producing measurable improvement."""


ADVISORY_BOARD_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Advisory Board — ongoing strategic guidance from the employer to inform program direction.

Type-specific guidance:
- OPPORTUNITY: Frame the advisory board as a structured channel for industry insight. This partnership requires no grant funding — its value is in the relationship.
- CURRICULUM COMPOSITION: Identify which departments the board would advise. Name skill gaps as natural inaugural agenda items.
- ROADMAP: Reference sending a formal invitation, scheduling an inaugural meeting with 2-3 agenda topics, and setting a quarterly cadence.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill's hiring breadth in the Central Valley — spanning entry-level technical roles through operations management, with sustained growth across all categories — makes the company's perspective on workforce readiness relevant to several of the college's programs simultaneously. An advisory board would formalize this relationship as an ongoing channel for industry guidance on curriculum direction, skill standards, and emerging workforce needs, requiring no grant funding.

Curriculum Composition: The strongest alignment is concentrated in the Agriculture, Work Experience, and Business departments, which together cover the core skill areas Cargill hires for across its food production, logistics, and corporate functions. Gaps in auditing and labor relations represent natural inaugural agenda items where Cargill can advise on the best remediation approach.

Student Composition: The college has a substantial and deeply engaged pipeline of students developing skills relevant to Cargill's operations. The advisory board would provide a structured mechanism for Cargill to assess whether this pipeline's preparation meets current operational standards and where emerging industry trends should shift the college's emphasis.

Roadmap: The first step is to send a formal invitation to Cargill's Central Valley regional leadership, proposing a quarterly advisory board scoped to the Agriculture, Business, and Food Services programs. The inaugural meeting should address curriculum alignment, identified skill gaps, and emerging workforce trends."""


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
) -> NarrativeProposal:
    """Merge LLM-generated narrative with deterministic evidence blocks."""
    return NarrativeProposal(
        employer=employer,
        sector=sector,
        partnership_type=partnership_type,
        selected_occupation=selected_occ.get("title", ""),
        selected_soc_code=selected_occ.get("soc_code"),
        core_skills=selected_occ.get("core_skills", []),
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


def _get_employer_sector(employer: str) -> str | None:
    """Look up the employer's sector from the graph."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Employer {name: $name}) RETURN e.sector AS sector",
            name=employer,
        ).single()
    return result["sector"] if result else None


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
    sector = _get_employer_sector(employer)
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered.text)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    dept_text, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_top_students(college, aligned_depts, core_skills)
    narrative_context = _build_narrative_context(gathered, dept_text, selected_occ)

    prompt_text = _get_prompt(engagement_type, narrative_context)
    raw = _call_claude(prompt_text)
    logger.info("Stage 3 complete: Claude response received")

    narrative = _parse_narrative_fields(raw)
    partnership_type = TYPE_LABELS.get(engagement_type, engagement_type)
    proposal = _assemble_proposal(narrative, employer, sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Proposal complete for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a NarrativeProposal when Claude's streaming response completes."""
    sector = _get_employer_sector(employer)
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    selected_occ = _select_occupation(gathered.text)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    dept_text, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_top_students(college, aligned_depts, core_skills)
    narrative_context = _build_narrative_context(gathered, dept_text, selected_occ)

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
    proposal = _assemble_proposal(narrative, employer, sector, partnership_type, gathered, curriculum_evidence, selected_occ, student_stats, top_students)

    _evaluate_proposal(proposal, narrative_context)
    logger.info(f"Stream complete: proposal for {employer}")
    yield proposal
