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
    # Demand: use the proposal's opportunity_evidence directly.
    # The partnership pipeline already computed the occupation data with
    # wages, openings, and growth from the Neo4j graph. No need to re-derive
    # from the COE CSV (which can fail on SOC code granularity mismatches).
    from pipeline.industry.region_maps import COLLEGE_COE_REGION
    coe_region = COLLEGE_COE_REGION.get(req.college, "")

    occupations = [
        LmiOccupation(
            soc_code=e.soc_code or "",
            title=e.title,
            annual_wage=e.annual_wage,
            employment=e.employment,
            growth_rate=e.growth_rate,
            annual_openings=e.annual_openings,
            education_level=None,
            region=coe_region,
        )
        for e in req.opportunity_evidence
    ]
    total_demand = sum(o.annual_openings or 0 for o in occupations)

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

SWP_PROJECT_PROMPT = """You are a NOVA compliance writer for California's Strong Workforce Program (SWP). You produce concise, form-style responses that answer specific NOVA questions. Each section is a direct response — not a narrative essay.

Voice rules:
- The LMI data table (provided separately to the reviewer) owns all numbers. Do NOT restate specific figures (dollar amounts, percentages, counts, openings) that appear in the LMI data. Reference the occupational cluster and gap direction instead.
- Open each section with its central claim in one direct sentence.
- Short, direct sentences. No filler, no em dashes, no rhetorical flourishes.
- Every claim must be grounded in the context provided. Do not invent assertions.
- This is a compliance response, not a persuasive narrative. Answer the NOVA question, nothing more.
- Use commitment language: "will" not "could explore." Compliance requires commitment.
- "Gap" is legitimate as a quantitative measurement. Do not use "missing," "falls short," or "deficient" as judgments on the college. Frame the college as capable of executing.
- Department names are proper nouns (capitalize). Skill names are lowercase. Acronyms (HVAC, HACCP, EHR) retain standard capitalization.
- Do not repeat information across sections. Each sentence introduces new information.

CONTEXT:
Employer: {employer}
College: {college}
Partnership Type: {partnership_type}
Selected Occupation: {selected_occupation} ({selected_soc_code})
Core Skills: {core_skills}
Objective Type: {objective_type}
Vision for Success Goal: {vision_goal}
SWP Metrics: {swp_metrics}

PARTNERSHIP OPPORTUNITY:
{opportunity}

CURRICULUM ALIGNMENT:
{curriculum_composition}

{curriculum_detail}

STUDENT PIPELINE:
{student_composition}

Pipeline: {pipeline_total} students in program, {pipeline_qualified} with all core skills

LABOR MARKET INTELLIGENCE (Centers of Excellence):
{lmi_text}

PROPOSED NEXT STEPS (from partnership proposal):
{roadmap}

Generate exactly 7 sections as a JSON array. Each section answers a specific NOVA question concisely.

1. key: "project_name", title: "Project Name"
   content: Short label summarizing the partnership, program area, and college. Max 100 characters.

2. key: "project_description", title: "Project Description"
   content: 1-2 sentences stating the goal, employer, program area, and expected impact. Max 500 characters.

3. key: "rationale", title: "Project Rationale"
   content: Answers "What needs motivate this project?" 3-4 sentences. Reference the occupational cluster and the demand/supply gap direction without restating specific numbers. Name the SOC code and relevant TOP codes so the reviewer can cross-check the LMI table. State why this employer and this program are the right match.

4. key: "student_impact", title: "Student Impact"
   content: Answers "How many students will be positively impacted and how was this determined?" 2-3 sentences. State the pipeline size and qualification count from the data. Describe what positive impact looks like for these students.

5. key: "vision_goal", title: "Vision for Success Goal"
   content: State the SWP Vision for Success goal. 1-2 sentences connecting this project to that goal. This establishes what the project aims to achieve.

6. key: "objective", title: "Objective"
   content: Three sub-components in one block. First line: "Objective Type: {objective_type}". Then 1-2 sentences describing a quantifiable, measurable objective. Then 1 sentence stating how this objective addresses regional workforce priorities.

7. key: "activity", title: "Activity"
   content: Answers "Who, what, when?" 2-3 sentences describing concrete actions that will be taken, by whom, in what timeframe. Tied to the objective above. Derived from the proposed next steps.

Return ONLY valid JSON: [{{"key": "...", "title": "...", "content": "..."}}, ...]
Do NOT include any text before or after the JSON array."""


_OBJECTIVE_TYPE_MAP: dict[str, str] = {
    "Internship Pipeline": "Improve career readiness and job placement",
    "Curriculum Co-Design": "Increase quality of existing program(s)",
    "Advisory Board": "Increase quality of existing program(s)",
}


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

    # Deterministic objective type from partnership type
    objective_type = _OBJECTIVE_TYPE_MAP.get(req.partnership_type, "Improve career readiness and job placement")

    # Student pipeline
    student_ev = req.student_evidence
    pipeline_total = student_ev.total_in_program
    pipeline_qualified = student_ev.with_all_core_skills

    return SWP_PROJECT_PROMPT.format(
        employer=req.employer,
        college=req.college,
        partnership_type=req.partnership_type,
        selected_occupation=req.selected_occupation,
        selected_soc_code=req.selected_soc_code or "",
        core_skills=", ".join(req.core_skills),
        objective_type=objective_type,
        vision_goal=req.goal,
        swp_metrics=", ".join(req.metrics),
        opportunity=req.opportunity,
        curriculum_composition=req.curriculum_composition,
        curriculum_detail=curriculum_detail,
        student_composition=req.student_composition,
        pipeline_total=pipeline_total,
        pipeline_qualified=pipeline_qualified,
        lmi_text=lmi_text,
        roadmap=req.roadmap,
    )


# ── Claude invocation & parsing ─────────────────────────────────────────

_SECTION_CHAR_LIMITS: dict[str, int] = {
    "project_name": 100,
    "project_description": 500,
    "rationale": 1000,
    "student_impact": 600,
    "vision_goal": 400,
    "objective": 800,
    "activity": 600,
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
        max_tokens=2048,
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
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt_text}],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

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
