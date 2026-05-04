"""Partnership proposal orchestrator: entry points and pipeline wiring.

Delegates to four siblings:
- gather.py     — Neo4j data retrieval (GatheredContext, curriculum, students)
- filter.py     — LLM-based occupation and department selection
- narrative.py  — LLM-based proposal authoring, parsing, assembly

Single linear pipeline: gather context → select occupation → gather aligned
curriculum and student pipeline → assemble regional supply-demand evidence →
generate four-section narrative → assemble final proposal."""

from __future__ import annotations

import logging

from ontology.schema import get_driver
from partnerships.evals import evaluate_proposal
from partnerships.filter import _select_occupation
from partnerships.gather import (
    GatheredContext,
    _gather_aligned_curriculum,
    _gather_student_pipeline,
    _gather_targeted_context,
)
from partnerships.models import (
    DepartmentEnrollment,
    InstitutionalSources,
    NarrativeProposal,
    OccupationEvidence,
    SupplyEstimate,
    SwpEvidence,
)
from partnerships.narrative import _assemble_proposal
from partnerships.narrative_templates import build_narrative

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Regional supply-demand evidence (the tabular SWP block)
# ═══════════════════════════════════════════════════════════════════════════


def _assemble_swp_evidence(
    college: str,
    gathered: GatheredContext,
    curriculum_evidence: list[dict],
    selected_occ: dict,
) -> SwpEvidence:
    """Assemble the tabular regional supply-demand evidence block, scoped
    to the selected occupation.

    The artifact is built around one specific occupation choice (the SOC
    the coordinator picked or the LLM auto-selected). Every other section
    — narrative, curriculum, students — is scoped to that SOC; the SWP
    evidence block is too. Demand is the annual regional openings for
    the selected occupation only; supply is the projected annual
    completions of programs whose TOP6 the institutional crosswalk maps
    to that SOC; the gap is the meaningful one-occupation reading,
    matching the docs-page Partnership Narrative example
    ("workforce gap of 232" for one Solar Photovoltaic Installers row).

    Earlier the demand totaled across every occupation the employer
    hired for, while supply was already curriculum-aligned and therefore
    selected-SOC-scoped. The gap was that asymmetric subtraction: a
    cross-occupation demand minus a single-pathway supply. The
    integrative figure cited at the bottom of the executive summary
    inherited that asymmetry. Scoping demand to the selected SOC
    restores the meaning.

    Args:
        selected_occ: dict with at least "soc_code"; used to locate the
            corresponding row in gathered.occupation_evidence.
    """
    from ontology.crosswalks import _load_cip_to_soc, _load_top_to_cip
    from ontology.mcf_lookup import lookup_top6
    from ontology.regions import COE_REGION_DISPLAY, COLLEGE_COE_REGION
    from ontology.supply import get_coe_supply

    coe_region = COLLEGE_COE_REGION.get(college, "")

    # Reverse-walk the CIP-SOC crosswalk so the artifact can attribute
    # the chain SOC ↔ CIP for the selected occupation. This surfaces
    # the second link in the empirical chain on every artifact.
    selected_soc = selected_occ.get("soc_code")
    cip_soc = _load_cip_to_soc()
    cips_for_soc = sorted([cip for cip, socs in cip_soc.items() if selected_soc in socs])

    # Demand: scoped to the selected occupation. The full list of
    # employer-hires occupations remains in gathered.occupation_evidence
    # for any caller that wants the broader view (e.g., the picker), but
    # the artifact's evidence table is single-row by design.
    selected_row = next(
        (o for o in gathered.occupation_evidence if o.get("soc_code") == selected_soc),
        None,
    )
    if selected_row:
        occupations = [
            OccupationEvidence(
                title=selected_row["title"],
                soc_code=selected_row.get("soc_code"),
                annual_wage=selected_row.get("annual_wage"),
                employment=selected_row.get("employment"),
                annual_openings=selected_row.get("annual_openings"),
                growth_rate=selected_row.get("growth_rate"),
                cip_codes=cips_for_soc,
            )
        ]
    else:
        # Defensive fallback: if the selected SOC isn't in the employer's
        # hires set (shouldn't happen — picker validates upstream), emit
        # an empty list and a zero gap rather than crash.
        occupations = []
    total_demand = sum(o.annual_openings or 0 for o in occupations)

    # Supply: lookup TOP6 codes for the aligned courses, then COE supply CSV.
    course_codes = [
        course["code"]
        for dept_ev in curriculum_evidence
        for course in dept_ev.get("courses", [])
    ]
    top6_codes = lookup_top6(course_codes, college)
    supply_data, total_supply = get_coe_supply(top6_codes, college)

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

    # Department-level student enrollment counts.
    departments = [d["department"] for d in curriculum_evidence]
    dept_enrollments: list[DepartmentEnrollment] = []
    if departments:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (dept:Department)-[:CONTAINS]->(c:Course {college: $college})
                      <-[:ENROLLED_IN]-(s:Student)
                WHERE dept.name IN $departments
                RETURN dept.name AS department, count(DISTINCT s) AS student_count
                ORDER BY student_count DESC
            """, college=college, departments=departments).data()
            dept_enrollments = [
                DepartmentEnrollment(department=r["department"], student_count=r["student_count"])
                for r in result
            ]

    # Institutional sources block — externally-authored attribution for
    # every categorical claim in the artifact. The publication-name
    # defaults live on the InstitutionalSources model; we override the
    # COE region fields here from the regions metadata so the atlas can
    # display "Bay Area" rather than "Bay" when rendering the source
    # caption.
    sources = InstitutionalSources(
        coe_region=coe_region,
        coe_region_display=COE_REGION_DISPLAY.get(coe_region, coe_region),
    )

    return SwpEvidence(
        occupations=occupations,
        supply_estimates=supply_estimates,
        department_enrollments=dept_enrollments,
        total_demand=total_demand,
        total_supply=total_supply,
        gap=gap,
        coe_region=coe_region,
        sources=sources,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════════════════════


def _select_occupation_from_soc(gathered: GatheredContext, soc_code: str) -> dict:
    """Build the selected-occupation dict for a coordinator-picked SOC."""
    for occ in gathered.occupation_evidence:
        if occ.get("soc_code") == soc_code:
            return {
                "title": occ.get("title", ""),
                "soc_code": soc_code,
            }
    raise ValueError(
        f"Selected SOC '{soc_code}' is not in {gathered.employer_name}'s "
        f"hires_for set in the {gathered.college} graph"
    )


def _run_pipeline(
    employer: str,
    college: str,
    gathered: GatheredContext,
    selected_occupation_soc: str | None = None,
) -> NarrativeProposal:
    """Single linear pipeline shared by sync and streaming entry points.

    Stages (all deterministic; no LLM call at runtime):
      2. Occupation selection — when selected_occupation_soc is provided,
         deterministic lookup by SOC; otherwise the crosswalk-rooted
         _select_occupation runs.
      3. Curriculum and student pipeline gathering (Neo4j, PREPARES_FOR-gated)
      4. Regional supply-demand evidence assembly (Neo4j + COE CSVs)
      5. Narrative composition from deterministic templates over the
         gathered data + the employer's pre-computed operations_summary.
      6. Final assembly
    """
    if selected_occupation_soc:
        selected_occ = _select_occupation_from_soc(gathered, selected_occupation_soc)
        logger.info(
            f"Stage 2 complete: coordinator-picked '{selected_occ['title']}' "
            f"({selected_occupation_soc}) for {employer}"
        )
    else:
        selected_occ = _select_occupation(gathered)
        logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    selected_soc = selected_occ.get("soc_code") or ""
    curriculum_evidence = _gather_aligned_curriculum(college, selected_soc)

    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(
        college, aligned_depts, selected_soc
    )
    logger.info(f"Stage 3 complete: gathered curriculum and student pipeline for {employer}")

    swp_evidence = _assemble_swp_evidence(college, gathered, curriculum_evidence, selected_occ)
    logger.info(f"Stage 4 complete: assembled regional supply-demand evidence (gap={swp_evidence.gap:,.0f})")

    # Coordinator-facing sector uses the institutional Doing-What-Matters /
    # Strong Workforce taxonomy ("Advanced Manufacturing"), not the
    # employer's BLS classification.
    proposal_sector = gathered.swp_sectors[0] if gathered.swp_sectors else gathered.sector

    selected_demand_row = swp_evidence.occupations[0] if swp_evidence.occupations else None
    annual_wage = selected_demand_row.annual_wage if selected_demand_row else None
    annual_openings = selected_demand_row.annual_openings if selected_demand_row else None
    coe_region_display = (
        swp_evidence.sources.coe_region_display
        if swp_evidence.sources else swp_evidence.coe_region
    )
    total_aligned_courses = sum(len(d.get("courses", [])) for d in curriculum_evidence)
    narrative = build_narrative(
        employer_name=employer,
        operations_summary=gathered.operations_summary,
        sector_display=proposal_sector or "",
        college=college,
        soc_code=selected_occ.get("soc_code") or "",
        soc_title=selected_occ.get("title") or "",
        annual_wage=annual_wage,
        annual_openings=annual_openings,
        coe_region_display=coe_region_display or "",
        total_aligned_courses=total_aligned_courses,
        total_in_aligned_departments=student_stats.get("total_in_aligned_departments", 0),
        n_departments=len(curriculum_evidence),
    )
    logger.info(f"Stage 5 complete: deterministic narrative composed for {employer}")
    proposal = _assemble_proposal(
        narrative=narrative,
        employer=employer,
        sector=proposal_sector,
        gathered=gathered,
        curriculum_evidence=curriculum_evidence,
        selected_occ=selected_occ,
        student_stats=student_stats,
        top_students=top_students,
        swp_evidence=swp_evidence,
    )

    # Non-blocking quality eval. The proposal ships regardless; violations
    # are logged so we can see drift across runs and surface them inline
    # in the atlas if the caller wants them.
    evaluate_proposal(proposal)

    logger.info(f"Proposal complete for {employer}.")
    return proposal


async def run_targeted_proposal(
    employer: str,
    college: str,
    selected_occupation_soc: str | None = None,
) -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    gathered = _gather_targeted_context(employer, college)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    return _run_pipeline(employer, college, gathered, selected_occupation_soc)


def stream_targeted_proposal(
    employer: str,
    college: str,
    selected_occupation_soc: str | None = None,
):
    """Generator that yields a NarrativeProposal when the pipeline completes."""
    gathered = _gather_targeted_context(employer, college)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    yield _run_pipeline(employer, college, gathered, selected_occupation_soc)
