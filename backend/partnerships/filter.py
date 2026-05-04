"""Deterministic selection helpers for the partnership pipeline.

Per the institutional-deference architectural commitment, all selection
in the partnership flow is deterministic and rooted in the institutional
crosswalk. The LLM-driven occupation picker was retired in C2; the LLM
department-relevance cap-to-3 was retired in C3 because the inbound
department set is already PREPARES_FOR-gated; the LLM narrative writer
was retired with the move to deterministic templates (see
``narrative_templates.py``). Once that retirement removed the only
caller of ``_extract_json``, the JSON parser was removed too.

Surviving helper:
  - _select_occupation: deterministic crosswalk-depth ranker
"""

from __future__ import annotations

import logging

from ontology.schema import get_driver

from partnerships.gather import GatheredContext

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Occupation Selection — deterministic, crosswalk-rooted
# ═══════════════════════════════════════════════════════════════════════════


def _select_occupation(gathered: GatheredContext) -> dict:
    """Pick the most institutionally-aligned SOC the employer hires for.

    Deterministic ranking by:
      1. aligned_course_count DESC — number of this college's courses
         whose PREPARES_FOR edge points at this SOC
      2. annual_openings DESC — regional labor-market demand
      3. soc_code ASC — final tiebreaker

    When no occupation in the employer's hires set has any aligned
    curriculum at this college, the highest-openings SOC wins by
    tiebreaker — the artifact will then honestly surface an empty
    curriculum_evidence and the prose will name the partial nature.
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
    }


