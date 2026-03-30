"""Strong Workforce Program project generation — partnership-grounded, NOVA-compatible."""
from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional
import anthropic
from ontology.schema import get_driver
from models import (
    SwpProjectRequest, SwpProject, SwpSection,
    LmiContext, LmiOccupation, SupplyEstimate,
)

logger = logging.getLogger(__name__)

# ── Data files loaded at module init ────────────────────────────────────

_CALIBRATIONS_DIR = Path(__file__).parent.parent / "pipeline" / "calibrations"

_PREFIX_TO_TOP4: dict[str, str] = json.loads(
    (_CALIBRATIONS_DIR / "prefix_to_top4.json").read_text()
)

# 2-digit TOP code prefix → TOP group name (matches calibration JSON keys)
_TOP2_TO_GROUP: dict[str, str] = {
    "01": "Agriculture and Natural Resources",
    "03": "Environmental Sciences and Technologies",
    "04": "Biological Sciences",
    "05": "Business and Management",
    "06": "Media and Communications",
    "07": "Information Technology",
    "08": "Education",
    "09": "Engineering and Industrial Technologies",
    "10": "Fine and Applied Arts",
    "11": "Foreign Language",
    "12": "Health",
    "13": "Family and Consumer Sciences",
    "14": "Law",
    "15": "Humanities (Letters)",
    "16": "Library Science",
    "17": "Mathematics",
    "19": "Physical Sciences",
    "20": "Psychology",
    "21": "Public and Protective Services",
    "22": "Social Sciences",
    "49": "Interdisciplinary Studies",
}


def _load_calibration(college: str) -> dict | None:
    """Load per-college calibration JSON. Returns None if not found."""
    # Derive slug: "Foothill College" -> "foothill", "De Anza College" -> "deanza"
    slug = college.lower().replace(" college", "").replace(" ", "").strip()
    cal_path = _CALIBRATIONS_DIR / f"{slug}.json"
    if cal_path.exists():
        return json.loads(cal_path.read_text())
    # Try first word only: "Foothill College" -> "foothill"
    slug_alt = college.lower().split()[0]
    cal_path_alt = _CALIBRATIONS_DIR / f"{slug_alt}.json"
    if cal_path_alt.exists():
        return json.loads(cal_path_alt.read_text())
    logger.warning(f"No calibration file found for college: {college}")
    return None


def _top4_to_group(top4: str) -> str | None:
    """Map a 4-digit TOP code to its 2-digit group name."""
    prefix = top4[:2]
    return _TOP2_TO_GROUP.get(prefix)


# ── LMI Context (Phase 2 right panel) ──────────────────────────────────


def get_lmi_context(employer: str, college: str) -> LmiContext:
    """Gather LMI demand/supply data for an employer-college pair."""
    driver = get_driver()

    with driver.session() as session:
        # Demand: occupations the employer hires for in the college's region
        demand_result = session.run("""
            MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)
                  -[d:DEMANDS]->(occ:Occupation)<-[:HIRES_FOR]-(emp:Employer {name: $employer})
            RETURN occ.soc_code AS soc_code, occ.title AS title,
                   occ.annual_wage AS annual_wage, d.employment AS employment,
                   d.growth_rate AS growth_rate, d.annual_openings AS annual_openings,
                   d.education_level AS education_level,
                   r.name AS region
        """, employer=employer, college=college).data()

        # Supply: course prefixes aligned to employer's required skills
        supply_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
                  -[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
            OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
            WITH DISTINCT dept.name AS department, split(course.code, ' ')[0] AS prefix
            RETURN department, prefix
        """, employer=employer, college=college).data()

    # Build demand occupations
    occupations = [
        LmiOccupation(
            soc_code=r["soc_code"],
            title=r["title"],
            annual_wage=r.get("annual_wage"),
            employment=r.get("employment"),
            growth_rate=r.get("growth_rate"),
            annual_openings=r.get("annual_openings"),
            education_level=r.get("education_level"),
            region=r["region"],
        )
        for r in demand_result
    ]

    total_demand = sum(o.employment or 0 for o in occupations)

    # Estimate supply from calibration data
    cal = _load_calibration(college)
    supply_estimates: list[SupplyEstimate] = []

    if cal and supply_result:
        enrollment = cal.get("enrollment", 0)
        top_shares = cal.get("top_group_enrollment_share", {})
        top_success = cal.get("top_group_success_rate", {})

        # Group prefixes by TOP group
        group_depts: dict[str, set[str]] = {}  # group_name -> set of departments
        for r in supply_result:
            prefix = r["prefix"]
            dept = r["department"] or "Unknown"
            top4 = _PREFIX_TO_TOP4.get(prefix)
            if not top4:
                continue
            group = _top4_to_group(top4)
            if not group:
                continue
            if group not in group_depts:
                group_depts[group] = set()
            group_depts[group].add(dept)

        for group, depts in group_depts.items():
            share = top_shares.get(group, 0)
            success = top_success.get(group, cal.get("success_rate", 0.7))
            if share > 0 and enrollment > 0:
                annual_completions = int(enrollment * share * success / 3)
                top4_code = ""
                for prefix in _PREFIX_TO_TOP4:
                    if _top4_to_group(_PREFIX_TO_TOP4[prefix]) == group:
                        top4_code = _PREFIX_TO_TOP4[prefix]
                        break

                supply_estimates.append(SupplyEstimate(
                    top_code=top4_code,
                    top_title=group,
                    department=", ".join(sorted(depts)),
                    estimated_annual_completions=annual_completions,
                ))

    total_supply = sum(s.estimated_annual_completions for s in supply_estimates)
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
Executive Summary: {executive_summary}

CURRICULUM ALIGNMENT:
{curriculum_alignment_text}

SKILL GAPS:
{skill_gaps_text}

STUDENT PIPELINE:
Total students with relevant skills: {pipeline_total}
Students with 3+ completed courses: {pipeline_deep}
Top skills: {pipeline_skills}

LABOR MARKET INTELLIGENCE:
{lmi_text}

ECONOMIC DATA:
{economic_text}

COORDINATOR DIRECTION:
Project Framing: {project_framing}
Vision for Success Goal: {goal}
SWP Metrics: {metrics}
Apprenticeship Component: {apprenticeship}
Work-Based Learning Component: {wbl}
{workforce_training_line}

Generate a JSON array of objects, each with keys "key", "title", and "content". Generate exactly these 8 sections:

1. key: "project_name"
   title: "Project Name & Description"
   content: A project name (max 100 characters) followed by " | " followed by a project description (max 500 characters). The name should summarize the partnership and program area at a glance. The description should state the goal, the employer, and the expected impact.

2. key: "rationale"
   title: "Project Rationale & Needs Assessment"
   content: Up to 10000 characters. Explain what needs motivate this project. Reference specific LMI data (occupation titles, annual demand figures, wages), skill gaps, and how the partnership addresses a documented regional workforce need. Ground every claim in the data above.

3. key: "sector"
   title: "Industry Sector Classification"
   content: Name the primary sector and any secondary sectors. Use standard SWP sector names (e.g., Advanced Manufacturing, Health, Information & Communication Technologies, etc.).

4. key: "employer_narrative"
   title: "Employer Partner & Community Value"
   content: Up to 2500 characters. Describe why this partnership would be valuable to the employer and the community. Reference the employer's hiring needs, the skill alignment with the college's curriculum, and the economic context (wages, employment).

5. key: "metrics_narrative"
   title: "Metrics & Investment Narrative"
   content: Up to 10000 characters. Describe how the planned investments will result in improved performance on the selected SWP metrics ({metrics}). Reference specific student pipeline data, curriculum alignment, and projected outcomes. Connect each metric to concrete evidence.

6. key: "workplan_activities"
   title: "Workplan: Major Activities"
   content: Up to 10000 characters. List 4-8 major activities that execute the partnership. Each activity should be concrete, time-bound where possible, and tied to the coordinator's framing. Include: curriculum alignment activities, employer engagement milestones, student placement steps, and any skill gap closure actions.

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
    # Curriculum alignment text
    alignment_lines = []
    for a in req.curriculum_alignment:
        alignment_lines.append(f"  - {a.department}: {a.course_code} {a.course_name} → {a.skill}")
    curriculum_alignment_text = "\n".join(alignment_lines) if alignment_lines else "  (none)"

    # Skill gaps text
    gap_lines = []
    for g in req.skill_gaps:
        gap_lines.append(f"  - {g.skill} (required by: {', '.join(g.required_by)})")
        gap_lines.append(f"    Recommended action: {g.recommended_action}")
    skill_gaps_text = "\n".join(gap_lines) if gap_lines else "  (none)"

    # LMI text
    lmi_lines = ["  Occupations (demand from EDD OEWS + COE projections):"]
    for occ in lmi.occupations:
        wage = f"${occ.annual_wage:,}/yr" if occ.annual_wage else "wage unavailable"
        emp = f"{occ.employment:,} jobs" if occ.employment else "employment unavailable"
        parts = [f"{occ.soc_code} {occ.title} in {occ.region}: {wage}, {emp}"]
        if occ.growth_rate is not None:
            parts.append(f"{occ.growth_rate:+.1%} projected growth (2024-2029)")
        if occ.annual_openings is not None:
            parts.append(f"{occ.annual_openings:,} avg annual openings")
        if occ.education_level:
            parts.append(f"entry: {occ.education_level}")
        lmi_lines.append(f"    {', '.join(parts)}")
    lmi_lines.append(f"  Total regional demand: {lmi.total_demand:,} jobs")
    lmi_lines.append(f"  Estimated annual supply (3-yr avg completions): {lmi.total_supply:,}")
    lmi_lines.append(f"  Demand-supply gap: {lmi.gap:,}")
    lmi_lines.append(f"  Funding eligibility: {'ELIGIBLE (demand exceeds supply)' if lmi.gap_eligible else 'NOT ELIGIBLE (supply exceeds demand)'}")
    lmi_text = "\n".join(lmi_lines)

    # Economic text
    econ_lines = []
    for occ in req.economic_impact.occupations:
        wage = f"${occ['annual_wage']:,}/yr" if occ.get("annual_wage") else "wage unavailable"
        emp = f"{occ['employment']:,} employed" if occ.get("employment") else ""
        econ_lines.append(f"  {occ['title']}: {wage}" + (f", {emp}" if emp else ""))
    if req.economic_impact.aggregate_employment:
        econ_lines.append(f"  Aggregate regional employment: {req.economic_impact.aggregate_employment:,}")
    economic_text = "\n".join(econ_lines) if econ_lines else "  (no economic data)"

    # Workforce training line
    wt_line = ""
    if req.workforce_training_type:
        wt_line = f"Workforce Training Type: {req.workforce_training_type}"

    return SWP_PROJECT_PROMPT.format(
        employer=req.employer,
        college=req.college,
        partnership_type=req.partnership_type,
        executive_summary=req.executive_summary,
        curriculum_alignment_text=curriculum_alignment_text,
        skill_gaps_text=skill_gaps_text,
        pipeline_total=req.student_pipeline.total_students,
        pipeline_deep=req.student_pipeline.students_with_3plus_courses,
        pipeline_skills=", ".join(req.student_pipeline.top_skills),
        lmi_text=lmi_text,
        economic_text=economic_text,
        project_framing=req.project_framing,
        goal=req.goal,
        metrics=", ".join(req.metrics),
        apprenticeship="Yes" if req.apprenticeship else "No",
        wbl="Yes" if req.work_based_learning else "No",
        workforce_training_line=wt_line,
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
    lmi = get_lmi_context(req.employer, req.college)
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
    lmi = get_lmi_context(req.employer, req.college)
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
