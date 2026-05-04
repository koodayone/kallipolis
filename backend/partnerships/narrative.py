"""Proposal assembly: merge the deterministic narrative dict with the
graph-derived evidence blocks into a final ``NarrativeProposal``.

What this module is *no longer*: an LLM-driven prose authoring layer.
Up through commit ``8ce84c1`` this file held a ~400-word prompt, the
Claude call, the response parser, and the helpers that built the
prompt's institutional-context block. All of that was retired when
the partnership-proposal narrative was made fully deterministic — see
``partnerships.narrative_templates``. The only LLM-derived input now
is each employer's pre-computed ``operations_summary``, populated at
ingestion by ``employers.characterize`` and stored on the Employer
node.

What this module *is*: the assembly step. Given the four narrative
strings (composed by ``narrative_templates.build_narrative``) and the
deterministic evidence blocks, produce the ``NarrativeProposal``
Pydantic model the API serializes to the atlas.
"""

from __future__ import annotations

import logging

from partnerships.gather import GatheredContext
from partnerships.models import (
    DepartmentEvidence,
    NarrativeProposal,
    OccupationEvidence,
    StudentEvidence,
    StudentSummaryEvidence,
    SwpEvidence,
)

logger = logging.getLogger(__name__)


def _assemble_proposal(
    narrative: dict,
    employer: str,
    sector: str | None,
    gathered: GatheredContext,
    curriculum_evidence: list[dict],
    selected_occ: dict,
    student_stats: dict,
    top_students: list[dict],
    swp_evidence: SwpEvidence,
) -> NarrativeProposal:
    """Merge the deterministic narrative dict with evidence blocks."""
    from ontology.crosswalks import _load_cip_to_soc
    cip_soc = _load_cip_to_soc()

    def _build_occ_evidence(occ_dict: dict) -> OccupationEvidence:
        soc = occ_dict.get("soc_code")
        cips = sorted([cip for cip, socs in cip_soc.items() if soc in socs]) if soc else []
        return OccupationEvidence(
            title=occ_dict.get("title", ""),
            soc_code=soc,
            annual_wage=occ_dict.get("annual_wage"),
            employment=occ_dict.get("employment"),
            annual_openings=occ_dict.get("annual_openings"),
            growth_rate=occ_dict.get("growth_rate"),
            cip_codes=cips,
        )

    occ_evidence = [
        _build_occ_evidence(o) for o in gathered.occupation_evidence
        if o.get("title") == selected_occ.get("title")
    ] or [_build_occ_evidence(o) for o in gathered.occupation_evidence[:1]]

    return NarrativeProposal(
        employer=employer,
        sector=sector,
        selected_occupation=selected_occ.get("title", ""),
        selected_soc_code=selected_occ.get("soc_code"),
        regions=gathered.regions,
        executive_summary=narrative["executive_summary"],
        occupational_demand=narrative["occupational_demand"],
        curriculum_alignment=narrative["curriculum_alignment"],
        student_impact=narrative["student_impact"],
        opportunity_evidence=occ_evidence,
        curriculum_evidence=[DepartmentEvidence(**d) for d in curriculum_evidence],
        student_evidence=StudentEvidence(
            total_in_program=student_stats.get("total_in_program", 0),
            total_in_aligned_departments=student_stats.get("total_in_aligned_departments", 0),
            top_students=[StudentSummaryEvidence(**s) for s in top_students],
        ),
        swp_evidence=swp_evidence,
    )
