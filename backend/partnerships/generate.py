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
) -> SwpEvidence:
    """Assemble the tabular regional supply-demand evidence block.

    Demand: occupations the employer hires for, with regional annual openings
    (read from the partnership-flow GatheredContext, which already populated
    annual_openings from the Neo4j graph's COE-grounded DEMANDS edges).

    Supply: TOP6 codes mapped from the aligned curriculum's course codes,
    looked up against the COE-published projected annual completions CSV.

    Department enrollments: total enrolled students per aligned department,
    for the student-impact dimension of the table.

    Both demand and supply are annual flow metrics (openings vs. completions).
    The gap is total demand minus total supply.
    """
    from ontology.mcf_lookup import lookup_top6
    from ontology.regions import COLLEGE_COE_REGION
    from ontology.supply import get_coe_supply

    coe_region = COLLEGE_COE_REGION.get(college, "")

    # Demand: all occupations the employer hires for in this region.
    occupations = [
        OccupationEvidence(
            title=o["title"],
            soc_code=o.get("soc_code"),
            annual_wage=o.get("annual_wage"),
            employment=o.get("employment"),
            annual_openings=o.get("annual_openings"),
            growth_rate=o.get("growth_rate"),
        )
        for o in gathered.occupation_evidence
    ]
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


def _run_pipeline(employer: str, college: str, gathered: GatheredContext) -> NarrativeProposal:
    """Single linear pipeline shared by sync and streaming entry points.

    Stages:
      2. Occupation selection (LLM)
      3. Curriculum and student pipeline gathering (Neo4j)
      4. Department relevance filter (LLM, cap 3)
      5. Regional supply-demand evidence assembly (Neo4j + COE CSVs)
      6. Narrative generation (LLM, four sections)
      7. Final assembly
    """
    selected_occ = _select_occupation(gathered)
    logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")

    core_skills = selected_occ.get("core_skills", [])
    _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

    # Cap to top 3 most relevant departments
    all_dept_names = [d["department"] for d in curriculum_evidence]
    selected_depts = _select_relevant_departments(
        gathered.employer_name, selected_occ.get("title", ""), all_dept_names
    )
    curriculum_evidence = [d for d in curriculum_evidence if d["department"] in selected_depts]

    dept_text = _build_dept_text(curriculum_evidence, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)
    logger.info(f"Stage 3 complete: gathered curriculum and student pipeline for {employer}")

    swp_evidence = _assemble_swp_evidence(college, gathered, curriculum_evidence)
    logger.info(f"Stage 4 complete: assembled regional supply-demand evidence (gap={swp_evidence.gap:,.0f})")

    narrative_context = _build_narrative_context(
        gathered, dept_text, selected_occ, student_stats, swp_evidence
    )
    prompt_text = NARRATIVE_PROMPT.format(context=narrative_context)
    raw = _call_claude(prompt_text)
    logger.info(f"Stage 5 complete: Claude narrative response received for {employer}")

    narrative = _parse_narrative_fields(raw)
    proposal = _assemble_proposal(
        narrative=narrative,
        employer=employer,
        sector=gathered.sector,
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


async def run_targeted_proposal(employer: str, college: str) -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    gathered = _gather_targeted_context(employer, college)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    return _run_pipeline(employer, college, gathered)


def stream_targeted_proposal(employer: str, college: str):
    """Generator that yields a NarrativeProposal when the pipeline completes."""
    gathered = _gather_targeted_context(employer, college)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    yield _run_pipeline(employer, college, gathered)
