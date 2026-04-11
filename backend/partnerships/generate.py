"""Partnership proposal orchestrator: entry points and pipeline wiring.

Delegates to three siblings:
- gather.py     — Neo4j data retrieval (GatheredContext, curriculum, students)
- filter.py     — LLM-based occupation / advisory / department selection
- narrative.py  — LLM-based proposal authoring, parsing, assembly, evaluation
"""

from __future__ import annotations

import logging

from partnerships.gather import (
    GatheredContext,
    _gather_aligned_curriculum,
    _gather_student_pipeline,
    _gather_targeted_context,
    _get_developed_skills,
)
from partnerships.filter import (
    _identify_agenda_topics,
    _identify_gap_skill,
    _select_advisory_occupations,
    _select_occupation,
    _select_primary_department_llm,
    _select_relevant_departments,
    _synthesize_advisory_thesis,
)
from partnerships.narrative import (
    _assemble_proposal,
    _build_advisory_context,
    _build_codesign_context,
    _build_dept_text,
    _build_narrative_context,
    _call_claude,
    _evaluate_proposal,
    _get_prompt,
    _parse_narrative_fields,
)
from partnerships.models import NarrativeProposal

logger = logging.getLogger(__name__)

TYPE_LABELS = {
    "internship": "Internship Pipeline",
    "curriculum_codesign": "Curriculum Co-Design",
    "advisory_board": "Advisory Board",
}


def _build_proposal_context(employer: str, college: str, engagement_type: str,
                            gathered: GatheredContext,
                            selected_occ: dict = None,
                            selected_occupations: list[dict] = None) -> dict:
    """Shared pipeline logic: build curriculum evidence, students, and narrative context.

    Returns dict with keys: curriculum_evidence, student_stats, top_students,
    narrative_context, core_skills, gap_skill, and advisory-specific fields
    (advisory_thesis, agenda_topics, selected_occupations).
    """
    gap_skill = ""
    gap_rationale = ""
    advisory_thesis = ""
    agenda_topics = []

    # ── Advisory board: multi-occupation, thesis-driven ──
    if engagement_type == "advisory_board" and selected_occupations:
        # Union core skills across all selected occupations
        core_skills = []
        seen = set()
        for occ in selected_occupations:
            for sk in occ.get("core_skills", []):
                if sk not in seen:
                    core_skills.append(sk)
                    seen.add(sk)

        # Synthesize thesis
        advisory_thesis = _synthesize_advisory_thesis(
            gathered.employer_name, gathered.sector, gathered.description, selected_occupations
        )

        # Curriculum query scoped to union of core skills
        _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

        # Select top 3 most relevant departments
        all_dept_names = [d["department"] for d in curriculum_evidence]
        occ_titles = ", ".join(o.get("title", "") for o in selected_occupations)
        selected_depts = _select_relevant_departments(gathered.employer_name, occ_titles, all_dept_names)
        curriculum_evidence = [d for d in curriculum_evidence if d["department"] in selected_depts]

        dept_text = _build_dept_text(curriculum_evidence, core_skills)
        aligned_depts = [d["department"] for d in curriculum_evidence]
        student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)

        # Agenda topics
        agenda_topics = _identify_agenda_topics(
            gathered.employer_name, gathered.sector, advisory_thesis,
            selected_occupations, aligned_depts, core_skills
        )

        narrative_context = _build_advisory_context(
            gathered, dept_text, selected_occupations, advisory_thesis,
            agenda_topics, core_skills, engagement_type
        )

        return {
            "curriculum_evidence": curriculum_evidence,
            "student_stats": student_stats,
            "top_students": top_students,
            "narrative_context": narrative_context,
            "core_skills": core_skills,
            "gap_skill": "",
            "advisory_thesis": advisory_thesis,
            "agenda_topics": agenda_topics,
            "selected_occupations": selected_occupations,
        }

    # ── Internship / Curriculum Co-Design: single-occupation ──
    core_skills = selected_occ.get("core_skills", [])

    # Curriculum co-design: dedicated gap identification
    if engagement_type == "curriculum_codesign":
        occ_title = selected_occ.get("title", "")
        college_skills = _get_developed_skills(college, occ_title)
        gap_result = _identify_gap_skill(gathered.employer_name, gathered.sector, occ_title, college_skills)
        gap_skill = gap_result.get("gap_skill", "")
        gap_rationale = gap_result.get("rationale", "")

    _, curriculum_evidence = _gather_aligned_curriculum(college, core_skills)

    # Select top 3 most relevant departments
    all_dept_names = [d["department"] for d in curriculum_evidence]
    selected_depts = _select_relevant_departments(gathered.employer_name, selected_occ.get("title", ""), all_dept_names)
    curriculum_evidence = [d for d in curriculum_evidence if d["department"] in selected_depts]

    # Curriculum co-design: narrow to one primary department via LLM
    if engagement_type == "curriculum_codesign" and curriculum_evidence:
        dept_names = [d["department"] for d in curriculum_evidence]
        primary_dept = _select_primary_department_llm(
            gathered.employer_name, selected_occ.get("title", ""), dept_names
        )
        curriculum_evidence = [d for d in curriculum_evidence if d["department"] == primary_dept]

    dept_text = _build_dept_text(curriculum_evidence, core_skills)
    aligned_depts = [d["department"] for d in curriculum_evidence]
    student_stats, top_students = _gather_student_pipeline(college, aligned_depts, core_skills)

    # Build narrative context — co-design gets gap skill + rationale
    if engagement_type == "curriculum_codesign":
        narrative_context = _build_codesign_context(gathered, dept_text, selected_occ, gap_skill, engagement_type, gap_rationale)
    else:
        narrative_context = _build_narrative_context(gathered, dept_text, selected_occ, engagement_type)

    return {
        "curriculum_evidence": curriculum_evidence,
        "student_stats": student_stats,
        "top_students": top_students,
        "narrative_context": narrative_context,
        "core_skills": core_skills,
        "gap_skill": gap_skill,
        "advisory_thesis": "",
        "agenda_topics": [],
        "selected_occupations": [],
    }


def _run_pipeline(employer: str, college: str, engagement_type: str, gathered: GatheredContext) -> NarrativeProposal:
    """Shared pipeline logic for both sync and streaming entry points."""
    # Stage 2: Occupation selection — advisory board selects multiple
    if engagement_type == "advisory_board":
        selected_occs = _select_advisory_occupations(gathered)
        titles = [o.get("title", "?") for o in selected_occs]
        logger.info(f"Stage 2 complete: selected advisory occupations {titles} for {employer}")
        selected_occ = selected_occs[0] if selected_occs else {}
        ctx = _build_proposal_context(employer, college, engagement_type, gathered,
                                      selected_occ=selected_occ, selected_occupations=selected_occs)
    else:
        selected_occ = _select_occupation(gathered, engagement_type)
        logger.info(f"Stage 2 complete: selected '{selected_occ.get('title', '?')}' for {employer}")
        ctx = _build_proposal_context(employer, college, engagement_type, gathered,
                                      selected_occ=selected_occ)

    prompt_text = _get_prompt(engagement_type, ctx["narrative_context"])
    raw = _call_claude(prompt_text)
    logger.info("Stage 3 complete: Claude response received")

    narrative = _parse_narrative_fields(raw)
    partnership_type = TYPE_LABELS.get(engagement_type, engagement_type)
    proposal = _assemble_proposal(
        narrative, employer, gathered.sector, partnership_type, gathered,
        ctx["curriculum_evidence"], selected_occ, ctx["student_stats"], ctx["top_students"],
        ctx["core_skills"], ctx["gap_skill"],
        selected_occupations=ctx.get("selected_occupations"),
        advisory_thesis=ctx.get("advisory_thesis", ""),
        agenda_topics=ctx.get("agenda_topics"),
    )

    _evaluate_proposal(proposal, ctx["narrative_context"])
    logger.info(f"Proposal complete for {employer}.")
    return proposal


async def run_targeted_proposal(employer: str, college: str, engagement_type: str = "") -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    return _run_pipeline(employer, college, engagement_type, gathered)


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a NarrativeProposal when Claude's streaming response completes."""
    gathered = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")
    yield _run_pipeline(employer, college, engagement_type, gathered)
