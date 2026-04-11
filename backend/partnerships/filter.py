"""LLM-based selection and filtering: occupation picks, gap identification,
advisory thesis, agenda topics, department relevance filter. Also houses the
shared `_extract_json` utility used by both this module and narrative.py."""

from __future__ import annotations

import json
import logging
import os
import re

import anthropic
from ontology.schema import get_driver

from partnerships.gather import GatheredContext

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# JSON parsing utility (shared)
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


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Signal Filter (occupation selection + gap identification)
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
# Advisory Board: Identity-Driven Selection
# ═══════════════════════════════════════════════════════════════════════════

_ADVISORY_OCCUPATION_SELECTION_PROMPT = """Select 2-3 occupations that best define this employer's institutional identity. Return ONLY the JSON below — no reasoning, no explanation, no other text.

{context}

Rules:
- Choose occupations that reveal what this employer DOES — the roles that define its operational focus. A food manufacturer is defined by food science and production roles. A hospital is defined by clinical care roles.
- Prefer identity-defining occupations over generic ones. Sales Representatives, Office Clerks, and General Managers tell you less about what makes this employer distinctive. But do not exclude generic roles if they are genuinely important to the employer's labor composition.
- For each occupation, pick 2 skills the college develops (course count > 0) that connect this role to the college's programs.
- The selected occupations together should paint a clear picture of this employer's operational focus.

{{"selected_occupations": [{{"title": "...", "soc_code": "...", "core_skills": ["...", "..."]}}, ...]}}"""


_ADVISORY_THESIS_PROMPT = """You are characterizing why this employer's perspective would be valuable to a community college's programs. Return ONLY the JSON below.

Employer: {employer_name}
Sector: {sector}
Description: {description}

Identity-defining occupations this employer hires for:
{occupations_text}

Write a 1-2 sentence thesis that captures what is distinctive about this employer's operational reality and why it is relevant to the college's programs. Be specific — the thesis should describe THIS employer, not any employer in the same sector. Do not claim the employer is unique or irreplaceable. Characterize what they do and let the relevance speak for itself.

{{"thesis": "..."}}"""


_ADVISORY_AGENDA_PROMPT = """Identify 2-3 inaugural agenda topics for an advisory board between this employer and the college. Return ONLY the JSON below.

Employer: {employer_name} ({sector})
Thesis: {thesis}

Selected occupations:
{occupations_text}

Relevant departments at the college:
{departments_text}

Skills the college develops for these occupations:
{skills_text}

Each topic should be:
1. A specific question this employer can answer from operational experience. Not a generic workforce question like "what skills do you need."
2. Actionable for the college's program development within one catalog cycle.
3. Grounded in the intersection of the employer's operations and the college's existing programs.
4. Focused on workforce-oriented programs. Be cautious about suggesting changes to foundational or general education courses. If a foundational department is relevant, present it tentatively.

Topic format: Each topic is a short, direct question. One question per topic. Do not combine two questions with "and." Keep questions under 25 words.

Rationale format: One concise sentence. Do not use deficit language — no "gaps," "falls short," "deficiencies," "shortcomings," or "inadequately." Frame in terms of what the employer's input could strengthen or inform.

Tone: Department names are proper nouns and should be capitalized. Skill names are lowercase. Legitimate acronyms (HVAC, HACCP, EPA, OSHA, EHR) retain standard capitalization. Reference actual department names in rationales, not skill labels as curricula.

{{"agenda_topics": [{{"topic": "...", "rationale": "..."}}, ...]}}"""


def _select_advisory_occupations(gathered: GatheredContext) -> list[dict]:
    """Select 2-4 identity-defining occupations for advisory board proposal."""
    context = _build_occupation_selection_context(gathered)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": _ADVISORY_OCCUPATION_SELECTION_PROMPT.format(context=context)}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        selected = result.get("selected_occupations", [])
        titles = [o.get("title", "?") for o in selected]
        logger.info(f"Advisory occupations selected: {titles}")
        return selected
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Advisory occupation selection returned invalid JSON ({e})")
        return []


def _synthesize_advisory_thesis(employer_name: str, sector: str, description: str, selected_occupations: list[dict]) -> str:
    """Synthesize a thesis for why this employer's perspective matters."""
    occ_lines = []
    for occ in selected_occupations:
        skills = ", ".join(occ.get("core_skills", []))
        occ_lines.append(f"  {occ.get('title', '?')}: {skills}")
    occupations_text = "\n".join(occ_lines)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": _ADVISORY_THESIS_PROMPT.format(
            employer_name=employer_name,
            sector=sector or "Unknown",
            description=description or "",
            occupations_text=occupations_text,
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        thesis = result.get("thesis", "")
        logger.info(f"Advisory thesis: {thesis}")
        return thesis
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Thesis synthesis returned invalid JSON ({e})")
        return ""


def _identify_agenda_topics(employer_name: str, sector: str, thesis: str,
                            occupations: list[dict], departments: list[str],
                            skills: list[str]) -> list[dict]:
    """Identify 2-3 inaugural agenda topics for the advisory board."""
    occ_lines = []
    for occ in occupations:
        occ_skills = ", ".join(occ.get("core_skills", []))
        occ_lines.append(f"  {occ.get('title', '?')}: {occ_skills}")
    occupations_text = "\n".join(occ_lines)
    departments_text = "\n".join(f"  {d}" for d in departments)
    skills_text = "\n".join(f"  {s}" for s in skills)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": _ADVISORY_AGENDA_PROMPT.format(
            employer_name=employer_name,
            sector=sector or "Unknown",
            thesis=thesis,
            occupations_text=occupations_text,
            departments_text=departments_text,
            skills_text=skills_text,
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        topics = result.get("agenda_topics", [])
        logger.info(f"Agenda topics identified: {[t.get('topic', '?') for t in topics]}")
        return topics
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Agenda topic identification returned invalid JSON ({e})")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Department Relevance Filter
# ═══════════════════════════════════════════════════════════════════════════

_DEPT_SELECTION_PROMPT = """Select up to {max_departments} departments most relevant to this partnership. Return ONLY the JSON — no reasoning.

Employer: {employer}
Occupation(s): {occupation}
Departments: {department_list}

Select the departments whose programs most directly prepare students for the work this employer does. Prefer workforce-oriented departments over foundational or general education departments. If fewer than {max_departments} departments are genuinely relevant, return fewer.

{{"selected_departments": ["...", "..."]}}"""


def _select_relevant_departments(employer: str, occupation: str, departments: list[str], max_departments: int = 3) -> list[str]:
    """Select the most relevant departments for this partnership, capped at max_departments."""
    if not departments:
        return departments
    if len(departments) <= max_departments:
        return departments

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": _DEPT_SELECTION_PROMPT.format(
            employer=employer,
            occupation=occupation,
            department_list=", ".join(departments),
            max_departments=max_departments,
        )}],
    )
    raw = message.content[0].text

    try:
        result = _extract_json(raw)
        selected = result.get("selected_departments", [])
        # Ensure only valid department names are returned
        selected = [d for d in selected if d in departments][:max_departments]
        logger.info(f"Department selection: {len(selected)}/{len(departments)} departments selected")
        return selected
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Department selection returned invalid JSON ({e}), falling back to top {max_departments} by skill count")
        # Deterministic fallback: can't sort here since we don't have skill counts, return first N
        return departments[:max_departments]


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
