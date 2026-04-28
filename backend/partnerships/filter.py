"""Deterministic selection helpers for the partnership pipeline.

Per the institutional-deference architectural commitment, all selection
in the partnership flow is deterministic and rooted in the institutional
crosswalk. The legacy LLM-driven occupation picker was retired in C2;
the LLM department-relevance cap-to-3 was retired in C3 because the
inbound department set is already PREPARES_FOR-gated (institutionally
aligned), so applying LLM judgment on top would dilute the institutional
purity that the gating layer establishes.

Surviving helpers:
  - _select_occupation: deterministic crosswalk-depth ranker
  - _select_core_skills_for: deterministic core-skills characterization
  - _extract_json: shared JSON-parsing utility used by narrative.py
"""

from __future__ import annotations

import json
import logging
import re

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
# Occupation Selection — deterministic, crosswalk-rooted
# ═══════════════════════════════════════════════════════════════════════════
#
# When the coordinator has not chosen a SOC explicitly (e.g., the legacy
# auto-pick path), the system selects one. Per the institutional-deference
# commitment, this selection is itself an institutional question: of the
# occupations the employer hires for, which one is most institutionally
# aligned with the college's curriculum?
#
# Prior implementation: an LLM-driven "pick the volume role" prompt that
# reasoned over skill-set summaries. That introduced LLM judgment into
# what should be a deterministic ranking and could pick occupations that
# the college's catalog has zero institutionally-aligned coverage for.
#
# Current implementation: rank the employer's hires SOCs by
# (aligned_course_count DESC, annual_openings DESC, soc_code ASC).
# - aligned_course_count reflects institutional pathway alignment AT
#   THIS COLLEGE — counted via the same PREPARES_FOR edges that gate
#   curriculum_evidence downstream.
# - annual_openings reflects regional demand scale (tiebreaker).
# - soc_code is a deterministic final tiebreaker.


def _select_core_skills_for(college: str, occupation_title: str, k: int = 3) -> list[str]:
    """Deterministic core-skills selection for an occupation already chosen.

    Used when a SOC arrives from the picker (skipping the auto-pick) and
    when the auto-pick path completes. Returns up to k skills the
    occupation requires, ranked by (course_count DESC, skill_name) —
    preferring skills the college develops most thoroughly. Skills here
    are characterization for the narrative prompt, not the gating
    signal: per the institutional-deference commitment, pathway claims
    come only from the TOP-SOC crosswalk.
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
    """Pick the most institutionally-aligned SOC the employer hires for.

    Deterministic ranking by:
      1. aligned_course_count DESC — number of this college's courses
         whose PREPARES_FOR edge points at this SOC
      2. annual_openings DESC — regional labor-market demand
      3. soc_code ASC — final tiebreaker

    Returns the top-ranked occupation paired with its core-skills
    characterization. When no occupation in the employer's hires set
    has any aligned curriculum at this college, the highest-openings
    SOC wins by tiebreaker — the artifact will then honestly surface
    an empty curriculum_evidence and the prose will name the partial
    nature.

    No LLM call. The selection is itself an institutional question
    (which pathway is most aligned at this college?), and answering it
    deterministically against the crosswalk is what principle 3
    requires.
    """
    if not gathered.occupation_evidence:
        return {}

    socs = [o.get("soc_code") for o in gathered.occupation_evidence if o.get("soc_code")]
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            UNWIND $socs AS soc
            OPTIONAL MATCH (c:Course {college: $college})-[:PREPARES_FOR]->(:Occupation {soc_code: soc})
            RETURN soc, count(DISTINCT c) AS aligned_course_count
        """, socs=socs, college=gathered.college).data()
    aligned_by_soc = {r["soc"]: r["aligned_course_count"] for r in rows}

    def sort_key(occ: dict) -> tuple:
        soc = occ.get("soc_code") or ""
        return (
            -aligned_by_soc.get(soc, 0),
            -(occ.get("annual_openings") or 0),
            soc,
        )

    ranked = sorted(gathered.occupation_evidence, key=sort_key)
    selected = ranked[0]
    title = selected.get("title", "")
    soc = selected.get("soc_code")
    aligned_count = aligned_by_soc.get(soc, 0) if soc else 0
    logger.info(
        f"Occupation auto-selected: '{title}' ({soc}) — "
        f"{aligned_count} aligned course(s) at {gathered.college}, "
        f"{selected.get('annual_openings') or 0} regional openings"
    )

    return {
        "title": title,
        "soc_code": soc,
        "core_skills": _select_core_skills_for(gathered.college, title) if title else [],
    }


