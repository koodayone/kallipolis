"""Strong Workforce Program project generation — partnership-grounded, NOVA-compatible."""
from __future__ import annotations

import os
import re
import json
import logging
from typing import Optional
import anthropic
from models import (
    SwpProjectRequest, SwpProject, SwpSection,
    LmiContext, LmiOccupation, SupplyEstimate,
)
from pipeline.industry.coe_supply import get_coe_supply, get_coe_demand
from pipeline.industry.mcf_lookup import lookup_top6

logger = logging.getLogger(__name__)


# ── LMI Context (COE-grounded demand/supply) ──────────────────────────


def get_lmi_context(req: SwpProjectRequest) -> LmiContext:
    """Gather LMI demand/supply data from COE-published datasets.

    Demand: SOC codes from the proposal's occupation evidence → COE demand CSV.
    Supply: Course prefixes from the proposal's curriculum evidence → COE supply CSV.
    Both sides are annual flow metrics (openings vs. completions).
    """
    # Demand: use the proposal's selected occupation SOC code for focused LMI
    # The proposal selects one occupation as the partnership's target;
    # opportunity_evidence may contain all employer occupations which is too broad.
    if req.selected_soc_code:
        soc_codes = [req.selected_soc_code]
    else:
        soc_codes = [
            e.soc_code for e in req.opportunity_evidence
            if e.soc_code
        ]
    occupations_data, total_demand = get_coe_demand(soc_codes, req.college)

    occupations = [
        LmiOccupation(
            soc_code=o["soc_code"],
            title=o["title"],
            annual_wage=o.get("annual_wage"),
            employment=o.get("employment"),
            growth_rate=o.get("growth_rate"),
            annual_openings=o.get("annual_openings"),
            education_level=o.get("education_level"),
            region=o.get("region", ""),
        )
        for o in occupations_data
    ]

    # Supply: look up exact TOP6 codes for the proposal's courses via MCF
    course_codes = [
        course.code
        for dept_ev in req.curriculum_evidence
        for course in dept_ev.courses
    ]
    top6_codes = lookup_top6(course_codes, req.college)
    supply_data, total_supply = get_coe_supply(top6_codes, req.college)

    supply_estimates = [
        SupplyEstimate(
            top_code=s["top_code"],
            top_title=s["top_title"],
            award_level=s["award_level"],
            annual_projected_supply=s["annual_projected_supply"],
        )
        for s in supply_data
    ]

    gap = total_demand - total_supply

    return LmiContext(
        occupations=occupations,
        supply_estimates=supply_estimates,
        total_demand=total_demand,
        total_supply=total_supply,
        gap=gap,
        gap_eligible=gap > 0,
    )


# ── Claude prompt ─────────────────────────────────────────���─────────────

SWP_PROJECT_PROMPT = """You are a compliance writer for California's Strong Workforce Program (SWP). You are generating a NOVA-compatible SWP project application document that translates a community college's industry partnership into the compliance format required for state workforce funding.

Every claim must reference specific data from the context provided. Do not invent data.

PARTNERSHIP CONTEXT:
Employer: {employer}
College: {college}
Partnership Type: {partnership_type}
Selected Occupation: {selected_occupation}
Core Skills: {core_skills}

OPPORTUNITY:
{opportunity}

CURRICULUM:
{curriculum_composition}

{curriculum_detail}

SKILL GAP:
{gap_skill_text}

STUDENT PIPELINE:
{student_composition}

Pipeline size: {pipeline_total} students in program, {pipeline_qualified} with all core skills
Top students: {top_student_count} profiled

LABOR MARKET INTELLIGENCE (Centers of Excellence):
{lmi_text}

COORDINATOR DIRECTION:
Goal: {goal}
SWP Metrics: {metrics}
Apprenticeship Component: {apprenticeship}
Work-Based Learning Component: {wbl}

Generate a JSON array of objects, each with keys "key", "title", and "content". Generate exactly these 8 sections:

1. key: "project_name"
   title: "Project Name & Description"
   content: A project name (max 100 characters) followed by " | " followed by a project description (max 500 characters). The name should summarize the partnership and program area at a glance. The description should state the goal, the employer, and the expected impact.

2. key: "rationale"
   title: "Project Rationale & Needs Assessment"
   content: Up to 10000 characters. Explain what needs motivate this project. Reference specific LMI data (occupation titles, annual openings, wages), and how the partnership addresses a documented regional workforce need. Ground every claim in the data above.

3. key: "sector"
   title: "Industry Sector Classification"
   content: Name the primary sector and any secondary sectors. Use standard SWP sector names (e.g., Advanced Manufacturing, Health, Information & Communication Technologies, etc.).

4. key: "employer_narrative"
   title: "Employer Partner & Community Value"
   content: Up to 2500 characters. Describe why this partnership would be valuable to the employer and the community. Reference the employer's hiring needs, the skill alignment with the college's curriculum, and the economic context (wages, annual openings).

5. key: "metrics_narrative"
   title: "Metrics & Investment Narrative"
   content: Up to 10000 characters. Describe how the planned investments will result in improved performance on the selected SWP metrics ({metrics}). Reference specific student pipeline data, curriculum alignment, and projected outcomes. Connect each metric to concrete evidence.

6. key: "workplan_activities"
   title: "Workplan: Major Activities"
   content: Up to 10000 characters. List 4-8 major activities that execute the partnership. Each activity should be concrete, time-bound where possible. Include: curriculum alignment activities, employer engagement milestones, student placement steps, and any skill gap closure actions.

7. key: "workplan_outcomes"
   title: "Workplan: Major Outcomes"
   content: Up to 10000 characters. List 4-8 measurable outcomes tied to the selected SWP metrics. Each outcome should specify what will be measured, the target, and how it connects to the LMI data. Reference student counts, completion projections, and employment outcomes.

8. key: "risks"
   title: "Risks & Mitigation"
   content: Up to 10000 characters. Identify 3-5 risks that may prevent successful completion. For each risk, provide a specific mitigation strategy. Consider: employer commitment risks, student pipeline risks, curriculum timeline risks, and labor market shift risks.

Return ONLY valid JSON: [{{"key": "...", "title": "...", "content": "..."}}, ...]
Do NOT include any text before or after the JSON array."""


def _gather_swp_context(req: SwpProjectRequest, lmi: LmiContext) -> str:
    """Build the text context for the Claude prompt from request + LMI data."""
    # Curriculum detail from proposal evidence
    curriculum_lines = []
    for dept_ev in req.curriculum_evidence:
        curriculum_lines.append(f"  {dept_ev.department}:")
        for course in dept_ev.courses:
            skills_str = ", ".join(course.skills) if course.skills else ""
            curriculum_lines.append(f"    {course.code} {course.name}" + (f" — {skills_str}" if skills_str else ""))
    curriculum_detail = "\n".join(curriculum_lines) if curriculum_lines else "  (none)"

    # Gap skill text
    gap_skill_text = f"  {req.gap_skill}" if req.gap_skill else "  (none identified)"

    # LMI text — COE-grounded demand and supply
    lmi_lines = ["  Occupations (demand from Centers of Excellence projections):"]
    for occ in lmi.occupations:
        wage = f"${occ.annual_wage:,}/yr" if occ.annual_wage else "wage unavailable"
        parts = [f"{occ.soc_code} {occ.title} in {occ.region}: {wage}"]
        if occ.annual_openings is not None:
            parts.append(f"{occ.annual_openings:,} avg annual openings")
        if occ.growth_rate is not None:
            parts.append(f"{occ.growth_rate:+.1%} projected growth (2024-2029)")
        if occ.education_level:
            parts.append(f"entry: {occ.education_level}")
        lmi_lines.append(f"    {', '.join(parts)}")

    lmi_lines.append(f"  Total regional demand (annual openings): {lmi.total_demand:,}")
    lmi_lines.append("")
    lmi_lines.append("  Program supply (COE projected annual completions, by TOP code):")
    for s in lmi.supply_estimates:
        lmi_lines.append(f"    {s.top_code} {s.top_title} ({s.award_level}): {s.annual_projected_supply:.1f}")
    lmi_lines.append(f"  Total annual projected supply: {lmi.total_supply:.0f}")
    lmi_lines.append("")
    lmi_lines.append(f"  Annual gap (openings - supply): {lmi.gap:,.0f}")
    lmi_lines.append(f"  Funding eligibility: {'ELIGIBLE (demand exceeds supply)' if lmi.gap_eligible else 'NOT ELIGIBLE (supply exceeds demand)'}")
    lmi_text = "\n".join(lmi_lines)

    # Student pipeline
    student_ev = req.student_evidence
    pipeline_total = student_ev.total_in_program
    pipeline_qualified = student_ev.with_all_core_skills
    top_student_count = len(student_ev.top_students)

    return SWP_PROJECT_PROMPT.format(
        employer=req.employer,
        college=req.college,
        partnership_type=req.partnership_type,
        selected_occupation=req.selected_occupation,
        core_skills=", ".join(req.core_skills),
        opportunity=req.opportunity,
        curriculum_composition=req.curriculum_composition,
        curriculum_detail=curriculum_detail,
        gap_skill_text=gap_skill_text,
        student_composition=req.student_composition,
        pipeline_total=pipeline_total,
        pipeline_qualified=pipeline_qualified,
        top_student_count=top_student_count,
        lmi_text=lmi_text,
        goal=req.goal,
        metrics=", ".join(req.metrics),
        apprenticeship="Yes" if req.apprenticeship else "No",
        wbl="Yes" if req.work_based_learning else "No",
    )


# ── Claude invocation & parsing ─────────────────────────────────────────

_SECTION_CHAR_LIMITS: dict[str, int] = {
    "project_name": 600,  # 100 name + " | " + 500 description
    "rationale": 10000,
    "employer_narrative": 2500,
    "metrics_narrative": 10000,
    "workplan_activities": 10000,
    "workplan_outcomes": 10000,
    "risks": 10000,
}


def _parse_swp_sections(raw: str) -> list[dict]:
    """Parse Claude's response into a list of section dicts."""
    logger.info(f"Claude SWP raw response (first 300 chars): {raw[:300]!r}")

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
            # Strategy 3: find JSON array directly
            match = re.search(r"\[[\s\S]*\]", raw)
            if match:
                json_str = match.group(0).strip()
            else:
                json_str = raw.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude SWP response: {e}\nRaw: {raw[:800]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")

    if not isinstance(data, list):
        raise ValueError("Expected JSON array of sections")

    return data


def _build_swp_project(
    sections_data: list[dict],
    req: SwpProjectRequest,
    lmi: LmiContext,
) -> SwpProject:
    """Build a SwpProject from parsed sections + request + LMI data."""
    sections = []
    for s in sections_data:
        key = s.get("key", "")
        sections.append(SwpSection(
            key=key,
            title=s.get("title", key),
            content=s.get("content", ""),
            char_limit=_SECTION_CHAR_LIMITS.get(key),
        ))

    return SwpProject(
        employer=req.employer,
        college=req.college,
        partnership_type=req.partnership_type,
        sections=sections,
        lmi_context=lmi,
        goal=req.goal,
        metrics=req.metrics,
    )


def _call_claude(prompt_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt_text}],
    )
    return message.content[0].text


async def run_swp_project(req: SwpProjectRequest) -> SwpProject:
    """Generate a complete SWP project document."""
    lmi = get_lmi_context(req)
    prompt_text = _gather_swp_context(req, lmi)
    logger.info(f"Gathered SWP context for {req.employer}, calling Claude...")
    raw = _call_claude(prompt_text)
    logger.info("Claude SWP response received, parsing sections...")
    sections_data = _parse_swp_sections(raw)
    project = _build_swp_project(sections_data, req, lmi)
    logger.info(f"Parsed SWP project for {req.employer}.")
    return project


def _extract_complete_sections(accumulated: str) -> tuple[list[dict], str]:
    """Extract complete JSON section objects from accumulated Claude output.

    Claude outputs a JSON array: [{...}, {...}, ...]
    We detect complete objects by tracking brace depth.
    Returns (parsed_sections, remaining_unparsed_text).
    """
    sections = []
    i = 0
    # Skip to first '['
    while i < len(accumulated) and accumulated[i] != '[':
        i += 1
    if i >= len(accumulated):
        return [], accumulated

    i += 1  # skip '['

    while i < len(accumulated):
        # Skip whitespace and commas between objects
        while i < len(accumulated) and accumulated[i] in ' \t\n\r,':
            i += 1
        if i >= len(accumulated) or accumulated[i] == ']':
            break
        if accumulated[i] != '{':
            i += 1
            continue

        # Found start of object — track brace depth
        start = i
        depth = 0
        in_string = False
        escape_next = False

        while i < len(accumulated):
            ch = accumulated[i]
            if escape_next:
                escape_next = False
                i += 1
                continue
            if ch == '\\' and in_string:
                escape_next = True
                i += 1
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        # Complete object found
                        obj_str = accumulated[start:i + 1]
                        try:
                            obj = json.loads(obj_str)
                            sections.append(obj)
                        except json.JSONDecodeError:
                            pass
                        i += 1
                        break
            i += 1
        else:
            # Incomplete object — stop here, return what we have
            break

    return sections, accumulated


def stream_swp_project(req: SwpProjectRequest):
    """Generator that yields LMI context, then individual sections as Claude completes them."""
    lmi = get_lmi_context(req)
    prompt_text = _gather_swp_context(req, lmi)
    logger.info(f"Gathered SWP context for {req.employer}, starting Claude stream...")

    # Yield LMI context first so frontend can render immediately
    yield ("lmi", lmi)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""
    sections_yielded = 0

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt_text}],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

            # Check if any new complete sections are available
            sections, _ = _extract_complete_sections(accumulated)
            while sections_yielded < len(sections):
                section_data = sections[sections_yielded]
                key = section_data.get("key", "")
                section = SwpSection(
                    key=key,
                    title=section_data.get("title", key),
                    content=section_data.get("content", ""),
                    char_limit=_SECTION_CHAR_LIMITS.get(key),
                )
                logger.info(f"Streaming section {sections_yielded + 1}: {key}")
                yield ("section", section)
                sections_yielded += 1

    logger.info(f"Stream complete: {sections_yielded} sections for {req.employer}")
