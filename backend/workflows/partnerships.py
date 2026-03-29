"""Targeted partnership proposal generation — employer-specific, evidence-grounded."""

import os
import re
import json
import logging
from collections import Counter, defaultdict
import anthropic
from ontology.schema import get_driver
from models import (
    TargetedProposal, AlignmentDetail, SkillGapDetail,
    PipelineStats, EconomicImpact,
)

logger = logging.getLogger(__name__)

_PREAMBLE = """You are an institutional intelligence analyst for California community college workforce partnerships.

Below is the institutional context for a specific employer:

{context}

Generate a partnership proposal as a single JSON object. Every claim must reference specific data from the context — course codes, skill names, student counts, and wage figures. Do not invent data."""

_BASE_SCHEMA = """
  "executive_summary": "2-3 sentences maximum. State the employer, the partnership type, and the expected outcome. Do not enumerate skills, course codes, or statistics — just the core thesis.",
  "partnership_type": "{partnership_type_name}",
  "partnership_type_rationale": "2-3 sentences explaining why this partnership type fits the specific alignment/gap pattern",
  "curriculum_alignment": [
    {{"department": "department name", "course_code": "course code", "course_name": "course name", "skill": "the skill this course develops that the employer needs"}}
  ],
  "skill_gaps": [
    {{"skill": "employer-needed skill the college does NOT develop", "required_by": ["occupation title(s)"], "recommended_action": "specific recommendation"}}
  ],
  "student_pipeline": {{
    "total_students": "<integer from context>",
    "students_with_3plus_courses": "<integer from context>",
    "top_skills": ["top 3-5 skills held by the student pipeline"]
  }},
  "economic_impact": {{
    "occupations": [{{"title": "occupation title", "annual_wage": "<integer or null>", "employment": "<integer or null>"}}],
    "aggregate_employment": "<total employment or null>"
  }},
  "next_steps": ["Exactly 3 steps in chronological order. Each is one sentence. First step: immediate action. Last step: partnership launch milestone."],
  "measurable_objective": "One sentence: specific number of students + role/occupation + timeframe.","""

_BASE_GUIDELINES = """
- Include 4-8 curriculum alignment entries covering the strongest course-to-skill connections
- Include ALL skill gaps from the context
- Economic impact should include all occupations the employer hires for that have wage/employment data
- Next steps should be actionable by a program coordinator — not generic advice
- Return ONLY valid JSON with no text before or after."""

INTERNSHIP_PROMPT = _PREAMBLE + """

The coordinator has selected an **Internship Pipeline** partnership. Generate a proposal focused on structured student work rotations at the employer site.

The JSON must match this schema:
{{
""" + _BASE_SCHEMA.replace("{partnership_type_name}", "Internship Pipeline") + """
  "type_details": {{
    "rotation_duration": "e.g. 16 weeks / one semester — must be between 8-16 weeks",
    "hours_per_week": <integer, typically 15-20>,
    "academic_credit": "identify a specific course code and unit count for internship credit from the college's catalog",
    "supervisor_model": "describe on-site employer supervisor + faculty liaison structure, name the relevant department"
  }}
}}

Type-specific guidelines:
- Rotation must be time-bounded (8-16 weeks typical for a semester)
- Academic credit path must reference an existing course or cooperative education code
- Supervisor model must name a specific department for the faculty liaison
- Next steps should include: identifying site supervisors, establishing liability agreements, and launching the first cohort
- Measurable objective should reference a specific number of students placed in rotations
""" + _BASE_GUIDELINES

APPRENTICESHIP_PROMPT = _PREAMBLE + """

The coordinator has selected an **Apprenticeship Program** partnership. Generate a proposal for a registered, paid, multi-year career pathway.

The JSON must match this schema:
{{
""" + _BASE_SCHEMA.replace("{partnership_type_name}", "Apprenticeship Program") + """
  "type_details": {{
    "program_duration": "2-4 years typical",
    "wage_progression": "starting hourly wage → journey-level wage, based on occupation wage data from context",
    "das_registration": "note on filing with the California Division of Apprenticeship Standards",
    "journeyperson_ratio": "e.g. 1 journeyperson per 4 apprentices"
  }}
}}

Type-specific guidelines:
- Must reference the California Division of Apprenticeship Standards (DAS) registration requirement
- Must define a wage progression from entry to journey-level, grounded in the wage data from context
- Program duration should be 2-4 years
- Next steps should include: convening a program design committee, filing DAS paperwork, and recruiting the first apprentice cohort
- Measurable objective should reference apprentices reaching journey status
""" + _BASE_GUIDELINES

CURRICULUM_CODESIGN_PROMPT = _PREAMBLE + """

The coordinator has selected a **Curriculum Co-Design** partnership. Generate a proposal where the employer shapes program content and quality.

The JSON must match this schema:
{{
""" + _BASE_SCHEMA.replace("{partnership_type_name}", "Curriculum Co-Design") + """
  "type_details": {{
    "collaboration_scope": "which specific programs or courses will be redesigned — reference departments from context",
    "review_cycle": "e.g. quarterly curriculum review meetings",
    "deliverables": "concrete artifacts: revised course outlines, new lab exercises, updated learning outcomes, etc.",
    "skill_gaps_addressed": ["list the specific skill gaps from the context that this collaboration targets"]
  }}
}}

Type-specific guidelines:
- Must reference specific skill gaps from the context that the curriculum redesign addresses
- Collaboration scope must name specific departments and courses from the context
- Deliverables must be concrete artifacts, not vague outcomes
- Review cycle should define a cadence for faculty-industry meetings
- Next steps should include: convening a faculty-industry working group, conducting a curriculum gap audit, and piloting revised content
- Measurable objective should reference credential completion or skill gap closure
""" + _BASE_GUIDELINES

HIRING_MOU_PROMPT = _PREAMBLE + """

The coordinator has selected a **Hiring MOU** partnership. Generate a proposal for a formal employer commitment to hire graduates.

The JSON must match this schema:
{{
""" + _BASE_SCHEMA.replace("{partnership_type_name}", "Hiring MOU") + """
  "type_details": {{
    "headcount_commitment": <integer — a specific number of hires per year, grounded in pipeline data>,
    "roles_covered": ["specific occupation titles from the context"],
    "minimum_qualifications": "what graduates need to qualify — reference relevant courses or credentials",
    "hiring_timeline": "e.g. rolling basis, annual cohort, upon program completion"
  }}
}}

Type-specific guidelines:
- Must specify a concrete headcount commitment grounded in the student pipeline size (not aspirational)
- Roles covered must reference specific occupation titles from the context
- Minimum qualifications should reference courses or credentials the college offers
- Hiring timeline must be specific, not open-ended
- Next steps should include: drafting the MOU document, establishing qualification criteria with the employer, and identifying the first eligible cohort
- Measurable objective should reference hires placed in specific roles
""" + _BASE_GUIDELINES

ADVISORY_BOARD_PROMPT = _PREAMBLE + """

The coordinator has selected an **Advisory Board** partnership. Generate a proposal for ongoing strategic guidance from the employer. Note: Advisory boards typically do not require SWP or other grant funding — this is a relationship-based partnership.

The JSON must match this schema:
{{
""" + _BASE_SCHEMA.replace("{partnership_type_name}", "Advisory Board") + """
  "type_details": {{
    "meeting_cadence": "e.g. quarterly, twice per year",
    "program_scope": ["specific departments or programs the board advises — from context"],
    "initial_agenda": ["2-3 specific topics for the first meeting, grounded in skill gaps or curriculum alignment from context"],
    "membership_expectations": "what the employer representative commits to: attendance, feedback, industry trend briefings, etc."
  }}
}}

Type-specific guidelines:
- Must scope the board to specific departments where skill alignment exists in the context
- Initial agenda topics must be grounded in skill gaps or curriculum needs from the data
- This partnership does NOT require SWP funding — do not reference grant applications or funding mechanisms
- Meeting cadence should be realistic (quarterly is standard)
- Next steps should include: sending a formal invitation, scheduling the inaugural meeting, and preparing the first agenda
- Measurable objective should reference curriculum improvements or industry alignment milestones, not student placements
""" + _BASE_GUIDELINES

PROMPTS: dict[str, str] = {
    "internship": INTERNSHIP_PROMPT,
    "apprenticeship": APPRENTICESHIP_PROMPT,
    "curriculum_codesign": CURRICULUM_CODESIGN_PROMPT,
    "hiring_mou": HIRING_MOU_PROMPT,
    "advisory_board": ADVISORY_BOARD_PROMPT,
}


def _gather_targeted_context(employer: str, college: str, engagement_type: str = "") -> str:
    """Gather employer-specific context from the graph for targeted proposal generation."""
    driver = get_driver()
    lines = []

    with driver.session() as session:
        # A. Employer overview
        emp_result = session.run("""
            MATCH (emp:Employer {name: $employer})
            OPTIONAL MATCH (emp)-[:IN_MARKET]->(r:Region)
            RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                   collect(r.name) AS regions
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

        # B. Skill alignment detail
        skill_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
            OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
            OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
            RETURN occ.title AS occupation, occ.annual_wage AS annual_wage,
                   sk.name AS skill,
                   CASE WHEN course IS NOT NULL THEN true ELSE false END AS developed,
                   course.code AS course_code, course.name AS course_name,
                   dept.name AS department
        """, employer=employer, college=college).data()

        # Group by occupation
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
                # Deduplicate by skill name
                seen = set()
                for entry in data["aligned"]:
                    if entry["skill"] not in seen:
                        seen.add(entry["skill"])
                        lines.append(f"      - {entry['skill']} → {entry['course_code']} {entry['course_name']} ({entry['department']})")
                        total_aligned += 1
            if data["gaps"]:
                unique_gaps = list(dict.fromkeys(data["gaps"]))
                lines.append("    Skill Gaps (employer needs, college does NOT develop):")
                for gap in unique_gaps:
                    lines.append(f"      - {gap}")
                    total_gaps += 1

        lines.append(f"\nSUMMARY: {total_aligned} aligned skills, {total_gaps} skill gaps across {len(occ_skills)} occupations.")

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
            # Count top skills
            skill_counter = Counter()
            for s in pipeline_result["flat_skills"]:
                skill_counter[s] += 1
            top_pipeline_skills = [s for s, _ in skill_counter.most_common(5)]

            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append(f"  Total students with relevant skills: {pipeline_result['total_students']}")
            lines.append(f"  Students with 3+ completed courses: {pipeline_result['deep_pipeline']}")
            if top_pipeline_skills:
                lines.append(f"  Top skills in pipeline: {', '.join(top_pipeline_skills)}")
        else:
            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append("  Total students with relevant skills: 0")
            lines.append("  Students with 3+ completed courses: 0")

        # D. Regional employment
        econ_result = session.run("""
            MATCH (:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                  <-[:HIRES_FOR]-(emp:Employer {name: $employer})
            RETURN occ.title AS title, occ.annual_wage AS annual_wage,
                   d.employment AS employment, r.name AS region
        """, employer=employer, college=college).data()

        if econ_result:
            lines.append("")
            lines.append("ECONOMIC DATA (regional employment and wages):")
            for r in econ_result:
                wage = f"${r['annual_wage']:,}/yr" if r["annual_wage"] else "wage unavailable"
                emp_count = f"{r['employment']:,} employed" if r["employment"] else "employment data unavailable"
                lines.append(f"  {r['title']} in {r['region']}: {wage}, {emp_count}")

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(lines)


def _parse_targeted_proposal(raw: str, employer: str) -> TargetedProposal:
    """Parse Claude's response into a TargetedProposal."""
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    # Strategy 1: extract from ```json ... ``` code block
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        json_str = match.group(1).strip()
    else:
        # Strategy 2: extract from generic ``` ... ``` code block
        match = re.search(r"```\s*([\s\S]*?)\s*```", raw)
        if match:
            json_str = match.group(1).strip()
        else:
            # Strategy 3: find JSON object directly
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                json_str = match.group(0).strip()
            else:
                json_str = raw.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}\nRaw: {raw[:800]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")

    return TargetedProposal(
        employer=employer,
        sector=data.get("sector"),
        executive_summary=data["executive_summary"],
        partnership_type=data["partnership_type"],
        partnership_type_rationale=data["partnership_type_rationale"],
        curriculum_alignment=[
            AlignmentDetail(**a) for a in data.get("curriculum_alignment", [])
        ],
        skill_gaps=[
            SkillGapDetail(**g) for g in data.get("skill_gaps", [])
        ],
        student_pipeline=PipelineStats(**data["student_pipeline"]),
        economic_impact=EconomicImpact(**data["economic_impact"]),
        next_steps=data.get("next_steps", []),
        measurable_objective=data.get("measurable_objective", ""),
        type_details=data.get("type_details", {}),
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


async def run_targeted_proposal(employer: str, college: str, engagement_type: str = "") -> TargetedProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    context = _gather_targeted_context(employer, college, engagement_type)
    prompt_text = _get_prompt(engagement_type, context)
    logger.info(f"Gathered targeted context for {employer} ({engagement_type}), calling Claude...")
    raw = _call_claude(prompt_text)
    logger.info("Claude response received, parsing proposal...")
    proposal = _parse_targeted_proposal(raw, employer)
    logger.info(f"Parsed targeted proposal for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a TargetedProposal when Claude's streaming response completes."""
    context = _gather_targeted_context(employer, college, engagement_type)
    prompt_text = _get_prompt(engagement_type, context)
    logger.info(f"Gathered targeted context for {employer} ({engagement_type}), starting Claude stream...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

    proposal = _parse_targeted_proposal(accumulated, employer)
    logger.info(f"Stream complete: proposal for {employer}")
    yield proposal
