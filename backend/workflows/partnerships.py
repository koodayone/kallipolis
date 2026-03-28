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

TARGETED_PROPOSAL_PROMPT = """You are an institutional intelligence analyst for California community college workforce partnerships. Your job is to generate a specific, actionable, and evidence-grounded partnership proposal between a community college and a single employer.

Below is the institutional context for a specific employer:

{context}

Based on this data, generate a partnership proposal as a single JSON object. Every claim must reference specific data from the context — course codes, skill names, student counts, and wage figures. Do not invent data.

The JSON must match this exact schema:

{{
  "executive_summary": "2-3 sentence pitch referencing the specific employer, the number of aligned skills, student pipeline size, and the core value proposition",
  "partnership_type": "one of: Internship Pipeline, Apprenticeship Program, Advisory Board Seat, Guest Lecture Series, Equipment Donation & Lab Access, Co-op Employment, Tuition Reimbursement Compact, Hiring Commitment MOU",
  "partnership_type_rationale": "2-3 sentences explaining why this partnership type fits the specific alignment/gap pattern",
  "curriculum_alignment": [
    {{
      "department": "department name from context",
      "course_code": "course code from context",
      "course_name": "course name from context",
      "skill": "the skill this course develops that the employer needs"
    }}
  ],
  "skill_gaps": [
    {{
      "skill": "a skill the employer needs that the college does NOT develop",
      "required_by": ["occupation title(s) that require this skill"],
      "recommended_action": "a specific, actionable recommendation for how the partnership could close this gap"
    }}
  ],
  "student_pipeline": {{
    "total_students": <integer from context>,
    "students_with_3plus_courses": <integer from context>,
    "top_skills": ["top 3-5 skills held by the student pipeline"]
  }},
  "economic_impact": {{
    "occupations": [
      {{"title": "occupation title", "annual_wage": <integer or null>, "employment": <integer or null>}}
    ],
    "aggregate_employment": <total employment across all listed occupations or null>
  }},
  "next_steps": [
    "3-5 concrete, actionable steps to initiate the partnership — be specific (name departments, suggest meeting formats, reference timelines)"
  ]
}}

Guidelines:
- Include 4-8 curriculum alignment entries covering the strongest course-to-skill connections
- Include ALL skill gaps from the context
- For partnership type selection, consider: high alignment + large pipeline → Internship Pipeline or Co-op; high gaps → Advisory Board or Equipment Donation; specialized knowledge gaps → Guest Lecture Series
- Economic impact should include all occupations the employer hires for that have wage/employment data
- Next steps should be actionable by a program coordinator — not generic advice
- If a coordinator's strategic objective is provided, use it as the organizing principle for the entire proposal. The partnership type, executive summary, curriculum alignment emphasis, and next steps should all be oriented around achieving that objective. The objective represents the coordinator's institutional knowledge and intent — it should steer every section.

Return ONLY valid JSON with no text before or after."""


def _gather_targeted_context(employer: str, college: str, objective: str | None = None) -> str:
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

    if objective:
        lines.append("")
        lines.append(f"COORDINATOR'S STRATEGIC OBJECTIVE: {objective}")

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
    )


def _call_claude(context: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": TARGETED_PROPOSAL_PROMPT.format(context=context),
        }],
    )
    return message.content[0].text


async def run_targeted_proposal(employer: str, college: str, objective: str | None = None) -> TargetedProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    context = _gather_targeted_context(employer, college, objective)
    logger.info(f"Gathered targeted context for {employer}, calling Claude...")
    raw = _call_claude(context)
    logger.info("Claude response received, parsing proposal...")
    proposal = _parse_targeted_proposal(raw, employer)
    logger.info(f"Parsed targeted proposal for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, objective: str | None = None):
    """Generator that yields a TargetedProposal when Claude's streaming response completes."""
    context = _gather_targeted_context(employer, college, objective)
    logger.info(f"Gathered targeted context for {employer}, starting Claude stream...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": TARGETED_PROPOSAL_PROMPT.format(context=context),
        }],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

    # Parse the complete response
    proposal = _parse_targeted_proposal(accumulated, employer)
    logger.info(f"Stream complete: proposal for {employer}")
    yield proposal
