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
from partnerships.filter import (
    _select_core_skills_for,
    _select_occupation,
    _select_relevant_departments,
)
from partnerships.gather import (
    GatheredContext,
    _gather_aligned_curriculum,
    _gather_student_pipeline,
    _gather_targeted_context,
)
from partnerships.models import (
    DepartmentEnrollment,
    NarrativeProposal,
    OccupationEvidence,
    SupplyEstimate,
    SwpEvidence,
)
from partnerships.narrative import (
    NARRATIVE_PROMPT,
    _assemble_proposal,
    _build_dept_text,
    _build_narrative_context,
    _call_claude,
    _parse_narrative_fields,
)

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
    from ontology.mcf_lookup import lookup_top6
    from ontology.regions import COLLEGE_COE_REGION
    from ontology.supply import get_coe_supply

    coe_region = COLLEGE_COE_REGION.get(college, "")

    # Demand: scoped to the selected occupation. The full list of
    # employer-hires occupations remains in gathered.occupation_evidence
    # for any caller that wants the broader view (e.g., the picker), but
    # the artifact's evidence table is single-row by design.
    selected_soc = selected_occ.get("soc_code")
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

    return SwpEvidence(
        occupations=occupations,
        supply_estimates=supply_estimates,
        department_enrollments=dept_enrollments,
        total_demand=total_demand,
        total_supply=total_supply,
        gap=gap,
        coe_region=coe_region,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════════════════════


def _select_occupation_from_soc(gathered: GatheredContext, soc_code: str, college: str) -> dict:
    """Build the selected-occupation dict for a coordinator-picked SOC.

    Looks up the occupation in gathered.occupation_evidence by SOC code and
    pairs it with deterministic core-skills selection. No LLM call.
    """
    for occ in gathered.occupation_evidence:
        if occ.get("soc_code") == soc_code:
            title = occ.get("title", "")
            return {
                "title": title,
                "soc_code": soc_code,
                "core_skills": _select_core_skills_for(college, title),
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

    Stages:
      2. Occupation selection — when selected_occupation_soc is provided,
         deterministic lookup by SOC plus deterministic core-skills selection;
         otherwise the legacy LLM-based _select_occupation runs.
      3. Curriculum and student pipeline gathering (Neo4j)
      4. Department relevance filter (LLM, cap 3)
      5. Regional supply-demand evidence assembly (Neo4j + COE CSVs)
      6. Narrative generation (LLM, four sections)
      7. Final assembly
    """
    if selected_occupation_soc:
        selected_occ = _select_occupation_from_soc(gathered, selected_occupation_soc, college)
        logger.info(
            f"Stage 2 complete: coordinator-picked '{selected_occ['title']}' "
            f"({selected_occupation_soc}) for {employer}"
        )
    else:
        selected_occ = _select_occupation(gathered)
        logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    selected_soc = selected_occ.get("soc_code") or ""
    _, curriculum_evidence = _gather_aligned_curriculum(college, selected_soc, core_skills)

    # Cap to top 3 most relevant departments. With PREPARES_FOR-gating
    # the inbound set is already TOP-aligned, so the LLM filter operates
    # on a much smaller and more honest candidate pool. When the
    # inbound set is empty (no aligned curriculum at this college), we
    # skip the filter call — there is nothing for it to choose from.
    if curriculum_evidence:
        all_dept_names = [d["department"] for d in curriculum_evidence]
        selected_depts = _select_relevant_departments(
            gathered.employer_name, selected_occ.get("title", ""), all_dept_names
        )
        curriculum_evidence = [d for d in curriculum_evidence if d["department"] in selected_depts]

    dept_text = _build_dept_text(curriculum_evidence, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(
        college, aligned_depts, selected_soc, core_skills
    )
    logger.info(f"Stage 3 complete: gathered curriculum and student pipeline for {employer}")

    swp_evidence = _assemble_swp_evidence(college, gathered, curriculum_evidence, selected_occ)
    logger.info(f"Stage 4 complete: assembled regional supply-demand evidence (gap={swp_evidence.gap:,.0f})")

    narrative_context = _build_narrative_context(
        gathered, dept_text, selected_occ, student_stats, swp_evidence
    )
    prompt_text = NARRATIVE_PROMPT.format(context=narrative_context)
    raw = _call_claude(prompt_text)
    logger.info(f"Stage 5 complete: Claude narrative response received for {employer}")

    narrative = _parse_narrative_fields(raw)
    # Coordinator-facing sector uses the institutional Doing-What-Matters /
    # Strong Workforce taxonomy ("Advanced Manufacturing"), not the
    # employer's BLS classification ("Manufacturing"). The artifact is
    # built on CTE programs, regional priority sectors, and SWP funding
    # categories — its surface vocabulary should match. Falls back to
    # BLS when the employer has no SWP classification.
    proposal_sector = gathered.swp_sectors[0] if gathered.swp_sectors else gathered.sector
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
        core_skills=core_skills,
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
