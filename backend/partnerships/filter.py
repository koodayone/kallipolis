"""LLM-based selection: occupation pick + department relevance filter.

Also houses the shared `_extract_json` utility used by this module and
narrative.py."""

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
# Occupation Selection
# ═══════════════════════════════════════════════════════════════════════════

_OCCUPATION_SELECTION_PROMPT = """Select the primary hiring occupation for this employer. Return ONLY the JSON below — no reasoning, no explanation, no other text.

{context}

Rules:
- Pick the ONE occupation this employer would hire in volume. A plumbing company hires plumbers. A hospital hires nurses. Not generic management or admin roles.
- Pick 3 skills most central to the daily work of that role. Choose ONLY from the skills listed under that occupation. Not generic skills like Record Keeping or Professional Ethics.
- Prefer skills the college develops (course count > 0). You may include one skill with 0 courses if it is genuinely central to the occupation — this represents a curriculum gap worth noting.

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


def _select_core_skills_for(college: str, occupation_title: str, k: int = 3) -> list[str]:
    """Deterministic core-skills selection for an occupation already chosen by the coordinator.

    Used when a SOC code arrives from the picker, so the LLM occupation-selection
    step is skipped. Returns up to k skills the occupation requires, ranked by
    (course_count DESC, skill_name) — preferring skills the college develops
    most thoroughly. Falls back to the highest-required skills if the college
    develops fewer than k of them, so the resulting list always has up to k entries.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (occ:Occupation {title: $title})-[:REQUIRES_SKILL]->(sk:Skill)
            OPTIONAL MATCH (c:Course {college: $college})-[:DEVELOPS]->(sk)
            RETURN sk.name AS skill, count(DISTINCT c) AS course_count
            ORDER BY course_count DESC, skill ASC
        """, title=occupation_title, college=college).data()
    if not result:
        return []
    return [r["skill"] for r in result[:k]]


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
        logger.warning(f"Department selection returned invalid JSON ({e}), falling back to first {max_departments}")
        # Deterministic fallback: can't sort here since we don't have skill counts, return first N
        return departments[:max_departments]
