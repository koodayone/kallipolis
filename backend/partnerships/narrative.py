"""LLM-based proposal authoring: narrative context builders, prompt templates,
LLM calls, response parsing, proposal assembly, and quality evaluation."""

from __future__ import annotations

import json
import logging
import os

import anthropic

from partnerships.filter import _extract_json
from partnerships.gather import GatheredContext
from partnerships.models import (
    CourseEvidence,
    DepartmentEvidence,
    NarrativeProposal,
    OccupationEvidence,
    ProposalJustification,
    StudentEnrollmentEvidence,
    StudentEvidence,
    StudentSummaryEvidence,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Narrative context builders
# ═══════════════════════════════════════════════════════════════════════════


def _build_dept_text(curriculum_evidence: list[dict], core_skills: list[str]) -> str:
    """Build department-level text for the narrative prompt from filtered evidence."""
    core_set = set(core_skills)
    lines = ["DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:"]
    for dept_ev in curriculum_evidence:
        dept = dept_ev["department"]
        skills = set(dept_ev["aligned_skills"])
        skills_str = ", ".join(sorted(skills))
        missing = core_set - skills
        missing_str = f". Missing: {', '.join(sorted(missing))}" if missing else ""
        lines.append(f"  {dept}: develops {skills_str} (across {len(dept_ev['courses'])} courses){missing_str}")
    return "\n".join(lines)


def _build_narrative_context(gathered: GatheredContext, dept_text: str, selected_occ: dict, engagement_type: str = "") -> str:
    """Build the context string for the narrative generation prompt.

    Only includes data scoped to the selected occupation and core skills.
    """
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    core_skills = selected_occ.get("core_skills", [])

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        "",
        f"SELECTED OCCUPATION: {occ_title} ({occ_soc})",
        f"CORE SKILLS: {', '.join(core_skills)}",
        "",
        dept_text,
    ]

    # Economic data for selected occupation only
    for occ_ev in gathered.occupation_evidence:
        if occ_ev.get("title") == occ_title:
            parts = [f"ECONOMIC DATA: {occ_ev['title']}"]
            if occ_ev.get("annual_wage"):
                parts.append(f"${occ_ev['annual_wage']:,}/yr")
            if occ_ev.get("employment"):
                parts.append(f"{occ_ev['employment']:,} employed")
            if occ_ev.get("growth_rate") is not None:
                parts.append(f"{occ_ev['growth_rate']:+.1%} growth")
            if occ_ev.get("annual_openings"):
                parts.append(f"{occ_ev['annual_openings']:,} annual openings")
            lines.append("")
            lines.append(", ".join(parts))
            break

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(line for line in lines if line is not None)


def _build_codesign_context(gathered: GatheredContext, dept_text: str, selected_occ: dict, gap_skill: str, engagement_type: str = "", gap_rationale: str = "") -> str:
    """Build context for curriculum co-design narrative — includes gap skill."""
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    core_skills = selected_occ.get("core_skills", [])

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        "",
        f"SELECTED OCCUPATION: {occ_title} ({occ_soc})",
        f"CORE SKILLS (college develops these): {', '.join(core_skills)}",
        f"GAP SKILL: {gap_skill}",
        f"RATIONALE: {gap_rationale}" if gap_rationale else None,
        "This area can be more rigorously developed through co-design with the employer. A collaborative review would determine the scope and curricular approach.",
        "",
        dept_text,
    ]

    for occ_ev in gathered.occupation_evidence:
        if occ_ev.get("title") == occ_title:
            parts = [f"ECONOMIC DATA: {occ_ev['title']}"]
            if occ_ev.get("annual_wage"):
                parts.append(f"${occ_ev['annual_wage']:,}/yr")
            if occ_ev.get("employment"):
                parts.append(f"{occ_ev['employment']:,} employed")
            if occ_ev.get("growth_rate") is not None:
                parts.append(f"{occ_ev['growth_rate']:+.1%} growth")
            if occ_ev.get("annual_openings"):
                parts.append(f"{occ_ev['annual_openings']:,} annual openings")
            lines.append("")
            lines.append(", ".join(parts))
            break

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(line for line in lines if line is not None)


def _build_advisory_context(gathered: GatheredContext, dept_text: str,
                            selected_occupations: list[dict], thesis: str,
                            agenda_topics: list[dict], core_skills: list[str],
                            engagement_type: str = "") -> str:
    """Build context for advisory board narrative — multiple occupations, thesis, agenda topics."""
    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {gathered.sector}" if gathered.sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        "",
        f"THESIS: {thesis}",
        "",
        "IDENTITY-DEFINING OCCUPATIONS:",
    ]

    occ_titles = {o.get("title") for o in selected_occupations}
    for occ in selected_occupations:
        occ_title = occ.get("title", "Unknown")
        occ_skills = ", ".join(occ.get("core_skills", []))
        lines.append(f"  {occ_title}: {occ_skills}")

    lines.append("")
    lines.append(f"CROSS-CUTTING SKILLS: {', '.join(core_skills)}")
    lines.append("")
    lines.append(dept_text)

    # Economic data for all selected occupations
    for occ_ev in gathered.occupation_evidence:
        if occ_ev.get("title") in occ_titles:
            parts = [f"ECONOMIC DATA: {occ_ev['title']}"]
            if occ_ev.get("annual_wage"):
                parts.append(f"${occ_ev['annual_wage']:,}/yr")
            if occ_ev.get("employment"):
                parts.append(f"{occ_ev['employment']:,} employed")
            if occ_ev.get("growth_rate") is not None:
                parts.append(f"{occ_ev['growth_rate']:+.1%} growth")
            if occ_ev.get("annual_openings"):
                parts.append(f"{occ_ev['annual_openings']:,} annual openings")
            lines.append("")
            lines.append(", ".join(parts))

    if agenda_topics:
        lines.append("")
        lines.append("INAUGURAL AGENDA TOPICS:")
        for t in agenda_topics:
            lines.append(f"  {t.get('topic', '')}")
            if t.get("rationale"):
                lines.append(f"    Rationale: {t['rationale']}")

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(line for line in lines if line is not None)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3: Proposal Generation Prompts
# ═══════════════════════════════════════════════════════════════════════════

_NARRATIVE_PREAMBLE = """You are a workforce partnership analyst writing for Kallipolis, an institutional intelligence platform for California community colleges.

Kallipolis voice: short sentences. Direct. No filler. No em dashes. State the fact, move on. Every sentence carries a concrete claim or a specific insight. If a sentence could be cut without losing information, cut it. The reader is a busy program coordinator who will skim past anything that feels like LLM output.

Below is curated institutional context for a specific employer.

{context}

Each section is followed by a structured evidence block that shows the complete record — every department, course, skill, and figure. The evidence block handles completeness. Your narrative handles meaning. Be selective: highlight the most significant elements and explain why they matter for this partnership. Do not summarize or enumerate what the evidence block already shows. Do not speculate about career progressions or advancement pathways.

Argument structure: You are writing one continuous argument across four sections: opportunity, curriculum composition, student composition, and roadmap. Begin each section with its central claim in a single direct sentence. The first sentence states what the section argues. The sentences that follow substantiate that claim with evidence from the context. Do not build toward the point. State it, then support it. Each topic sentence must be specific to this employer and college — not a generic template phrase. The opportunity topic sentence should naturally connect the employer, the partnership type, and the college's programs so the reader knows in the first sentence what is being proposed and why.

Write a single JSON object:

{{
  "opportunity": "<2-3 sentences>",
  "justification": {{
    "curriculum_composition": "<2-3 sentences>",
    "student_composition": "<2-3 sentences>"
  }},
  "roadmap": "<2-3 sentences>"
}}

Tone:
- Short, direct sentences. Each sentence makes one point. If a sentence has more than one comma, it is probably making more than one point. Split it. No subordinate clauses that explain why something matters. State it and move on.
- Figures are fine where they flow naturally. Do not avoid them artificially.
- No em dashes. No rhetorical flourishes. No "remarkably," "notably," "importantly."
- Reference departments and skills naturally within the flow of sentences. Department names are proper nouns and should be capitalized. When referencing a department, use "the [Name] department" or "the [Name] program" so the reader knows it is an organizational unit, not a general concept — "the Environmental Control Technology department" not "Environmental Control Technology." Skill names are not proper nouns and should be lowercase (food safety, operations management, clinical documentation). Legitimate acronyms (HVAC, HACCP, EPA, OSHA, EHR, BLS) retain their standard capitalization. Weave names into the argument rather than listing them as labels.
- Present evidence and options, not instructions. Use "could explore," "a potential starting point," "one area worth examining" rather than "should address," "must implement," "the meeting should open with." The reader is the decision-maker. The narrative presents the case. It does not prescribe the action.
- When discussing the college's programs, affirm what the department does well. The coordinator built these programs. Respect that work. Do not introduce development areas or weaknesses unless the partnership type specifically calls for it.
- Do not say "gaps," "missing," "does not address," "falls short," or "not fully prepared."
- Do not use bullet points or numbered lists.
- Focus recommendations on workforce-oriented programs. Be cautious about recommending changes to foundational or general education courses (e.g., biology, chemistry, mathematics) based on a single employer's needs — these courses serve many pathways.
- Do not introduce skill names that are not in the context. Do not assert how many core skills a department covers or claim complete coverage.
- Do not restate what has already been established within a section. Once a skill or department has been named and its role in the argument established, subsequent sentences should build on that rather than re-list it. Each sentence should introduce new information or advance the argument.

Epistemic standard: Be persuasive and epistemically rigorous. Persuade through specificity and grounded evidence, not through superlatives or exclusivity claims. Do not claim the employer is unique, the only option, the best fit, or irreplaceable. Characterize what they do and let the evidence make the case. If a claim cannot be verified from the data provided, do not make it.

- Return ONLY valid JSON with no text before or after."""


INTERNSHIP_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Internship Pipeline — structured on-site work experience at the employer.

Each section argues:
- OPPORTUNITY (2-3 sentences): This section claims that the employer is a compelling internship partner for the relevant program. Substantiate with regional demand and what the internship could look like. Do not speculate about career ladders.
- CURRICULUM COMPOSITION (2-3 sentences): This section claims that the relevant program provides direct preparation for an internship at this employer. Explain why the program's preparation matters for this specific role — do not inventory what each department teaches. The evidence block shows the detail. Do not suggest the program is insufficient.
- STUDENT COMPOSITION (2-3 sentences): This section asserts the composition and alignment of the student pipeline with this internship opportunity. Describe who the students are and what they are studying. Do not evaluate readiness — state it. Do not include economic data — that belongs in the opportunity section.
- ROADMAP (2-3 sentences): Concise recommended path forward. State the next step, then add specifics: internship duration (8-16 weeks), course credit mapping, first-cohort target. Present as options.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Kaiser Permanente represents one of the strongest internship partners for the college's Nursing program in the Central Valley. The region has sustained demand for registered nurses. Structured clinical rotations could give students supervised experience in the patient care workflows they are already learning in the classroom.

Curriculum Composition: The Nursing department provides the most direct preparation for an internship at Kaiser. Its coursework mirrors the clinical reasoning and documentation workflows students would encounter on the floor. The Health Sciences program extends this into supervised practice settings.

Student Composition: Students in the Nursing and Health Sciences programs are completing coursework aligned with the competencies Kaiser requires. The pipeline is concentrated in the programs most relevant to this role.

Roadmap: A meeting between the Nursing department chair and Kaiser's workforce development team could establish internship sites and capacity for a first cohort. An 8-12 week structure mapped to existing work experience course sequences could place 8-15 students within two semesters."""


CURRICULUM_CODESIGN_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Curriculum Co-Design — the employer shapes program content through collaboration with faculty to strengthen a specific area.

The context identifies a GAP SKILL — a specific area where collaboration with the employer could strengthen the program. This gap skill is the reason the co-design partnership exists. It should be introduced in the opportunity, contextualized in the curriculum composition, and named in the roadmap. Frame the gap as an opportunity to strengthen existing preparation, not a deficiency to correct. Use "can be strengthened," "an opportunity to deepen," or "can be more rigorously developed."

Each section argues:
- OPPORTUNITY (2-3 sentences): This section claims that the primary department is well-positioned for this occupation and that a co-design partnership could strengthen it further in the gap skill area. Tone is collaborative — the college is well-aligned, not falling short.
- CURRICULUM COMPOSITION (2-3 sentences): This section claims that the primary department is the right home for this partnership. Characterize the department's curricular strength for this role, then contextualize the gap skill as an area that could be more rigorously developed through collaboration. Do not enumerate individual skills — the evidence block shows them. Do not say "not addressed" or "missing" — say "can be strengthened" or "can be more rigorously developed."
- STUDENT COMPOSITION (2-3 sentences): This section asserts the composition and alignment of students in the primary department with this co-design opportunity. Describe who the students are and what they are studying. Do not evaluate readiness — state it. Do not include economic data — that belongs in the opportunity section.
- ROADMAP (2-3 sentences): Concise recommended path forward. Name the gap skill specifically as the focus area the working group would evaluate. Pilot within the next catalog cycle. Present as options.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: The college's Nursing program is well-positioned to deepen its alignment with Adventist Health through a co-design partnership focused on electronic health record proficiency. The program develops the core clinical competencies registered nurses need. Collaboration with Adventist Health's clinical education team could strengthen preparation in EHR workflows that are increasingly central to hospital practice.

Curriculum Composition: The Nursing department provides the strongest curricular foundation for this partnership. Its coursework prepares students for the documentation and assessment workflows that define daily nursing practice. EHR navigation is a practical requirement in modern clinical settings that could be more rigorously developed through collaboration with Adventist Health.

Student Composition: Students in the Nursing program are completing coursework in the clinical competencies this role requires. They represent the strongest candidates for a co-design effort that deepens their preparation for Adventist Health's clinical environment.

Roadmap: A working group between the Nursing department chair and Adventist Health's clinical education leadership could evaluate how EHR proficiency is addressed in clinical coursework. Revised content could be piloted within the next catalog cycle."""


ADVISORY_BOARD_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Advisory Board — ongoing strategic guidance from the employer to inform program direction.

Each section argues:
- OPPORTUNITY (2-3 sentences): This section claims that this employer is a compelling advisory board partner for the college's programs. The topic sentence connects the employer, the advisory board proposition, and the college's programs in a single claim. Substantiate with a characterization of the employer grounded in the thesis from the context. No grant funding is required.
- CURRICULUM COMPOSITION (2-3 sentences): This section claims that specific workforce-oriented programs provide the closest match to this employer's operations. Characterize the nature of the alignment — what kind of preparation these programs provide and why it connects to this employer's operations. Do not argue what the advisory relationship could do for the departments — that belongs in the roadmap. The evidence block shows the full inventory. Be cautious about framing foundational departments as targets for employer-specific advisory input.
- STUDENT COMPOSITION (2-3 sentences): This section asserts the scope and composition of the aggregate student pipeline across programs aligned with this employer's workforce. Describe who the students are and what they are studying. Do not include economic data (wages, employment counts, openings) — that belongs in the opportunity section and evidence blocks.
- ROADMAP (2-3 sentences): Concise recommended path forward. State the quarterly advisory board format, then reference the agenda topics from the context as potential starting points for the inaugural meeting. Not prescribed actions.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Opportunity: Cargill's operational scope across agricultural production and food processing makes it a compelling advisory board partner for several of the college's workforce programs. The company employs food science technicians, production managers, and agricultural inspectors across its Central Valley facilities. Formalizing that perspective as an advisory board would create an ongoing channel for industry guidance with no grant funding required.

Curriculum Composition: The Agriculture, Culinary and Nutrition, and Industrial Technology departments provide the closest curricular match to Cargill's workforce operations. These programs span the applied technical and production management competencies that Cargill's roles require. Sustained industry input could directly inform how coursework in these departments stays current with operational practice.

Student Composition: Students across these departments are developing competencies aligned with the roles Cargill fills in the region. The pipeline spans multiple pathways in food science, manufacturing, and agricultural production.

Roadmap: A quarterly advisory board with Cargill's Central Valley leadership could give these programs sustained access to industry perspective. Potential starting points for the inaugural meeting include how food safety audit processes map onto the competencies new hires need and what production floor workflows reveal about preparation in operations and quality assurance."""


PROMPTS: dict[str, str] = {
    "internship": INTERNSHIP_PROMPT,
    "curriculum_codesign": CURRICULUM_CODESIGN_PROMPT,
    "advisory_board": ADVISORY_BOARD_PROMPT,
}


# ═══════════════════════════════════════════════════════════════════════════
# Parsing & Assembly
# ═══════════════════════════════════════════════════════════════════════════


def _parse_narrative_fields(raw: str) -> dict:
    """Extract LLM-generated narrative fields from Claude's JSON response."""
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    data = _extract_json(raw)

    return {
        "opportunity": data.get("opportunity", ""),
        "justification": {
            "curriculum_composition": data.get("justification", {}).get("curriculum_composition", ""),
            "student_composition": data.get("justification", {}).get("student_composition", ""),
        },
        "roadmap": data.get("roadmap", ""),
    }


def _assemble_proposal(
    narrative: dict,
    employer: str,
    sector: str | None,
    partnership_type: str,
    gathered: GatheredContext,
    curriculum_evidence: list[dict],
    selected_occ: dict,
    student_stats: dict,
    top_students: list[dict],
    core_skills: list[str] | None = None,
    gap_skill: str = "",
    selected_occupations: list[dict] | None = None,
    advisory_thesis: str = "",
    agenda_topics: list[dict] | None = None,
) -> NarrativeProposal:
    """Merge LLM-generated narrative with deterministic evidence blocks."""
    from partnerships.models import AgendaTopic

    # Advisory board: multiple occupations in evidence, broader scope
    if selected_occupations:
        occ_titles = {o.get("title") for o in selected_occupations}
        occ_evidence = [
            OccupationEvidence(**o) for o in gathered.occupation_evidence
            if o.get("title") in occ_titles
        ] or [OccupationEvidence(**o) for o in gathered.occupation_evidence[:1]]
        primary_title = selected_occupations[0].get("title", "") if selected_occupations else ""
        primary_soc = selected_occupations[0].get("soc_code") if selected_occupations else None
    else:
        occ_evidence = [
            OccupationEvidence(**o) for o in gathered.occupation_evidence
            if o.get("title") == selected_occ.get("title")
        ] or [OccupationEvidence(**o) for o in gathered.occupation_evidence[:1]]
        primary_title = selected_occ.get("title", "")
        primary_soc = selected_occ.get("soc_code")

    return NarrativeProposal(
        employer=employer,
        sector=sector,
        partnership_type=partnership_type,
        selected_occupation=primary_title,
        selected_soc_code=primary_soc,
        core_skills=core_skills or selected_occ.get("core_skills", []),
        gap_skill=gap_skill,
        regions=gathered.regions,
        opportunity=narrative["opportunity"],
        opportunity_evidence=occ_evidence,
        justification=ProposalJustification(
            curriculum_composition=narrative["justification"]["curriculum_composition"],
            curriculum_evidence=[DepartmentEvidence(**d) for d in curriculum_evidence],
            student_composition=narrative["justification"]["student_composition"],
            student_evidence=StudentEvidence(
                total_in_program=student_stats.get("total_in_program", 0),
                with_all_core_skills=student_stats.get("with_all_core_skills", 0),
                top_students=[StudentSummaryEvidence(**s) for s in top_students],
            ),
        ),
        roadmap=narrative["roadmap"],
        selected_occupations=[o.get("title", "") for o in (selected_occupations or [])],
        advisory_thesis=advisory_thesis,
        agenda_topics=[AgendaTopic(**t) for t in (agenda_topics or [])],
    )


def _get_prompt(engagement_type: str, context: str) -> str:
    """Select and format the type-specific prompt template."""
    template = PROMPTS.get(engagement_type, INTERNSHIP_PROMPT)
    return template.format(context=context)


def _call_claude(prompt_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    )
    return message.content[0].text


# ═══════════════════════════════════════════════════════════════════════════
# Evaluation
# ═══════════════════════════════════════════════════════════════════════════

_EVAL_PROMPT = """Evaluate this partnership proposal against two quality rules.

CURATED CONTEXT:
{context}

GENERATED PROPOSAL:
{proposal}

RULES:

1. FAITHFULNESS: Any directional claims (e.g., "highest-volume", "fastest-growing", "strongest alignment") must be supported by the relative ordering in the curated context data. Any department names, skill names, or region names must appear in the context. Flag fabricated or unsupported claims.

2. NO_DATA_IN_NARRATIVE: The narrative sections (opportunity, curriculum_composition, student_composition) should NOT contain specific dollar amounts (e.g., "$80,560"), specific percentages (e.g., "4.7%"), specific counts (e.g., "940 annual openings", "15,000 students"), or specific employment numbers. These belong in the evidence blocks, not the prose. The roadmap section is exempt. Flag any specific figures found in the narrative sections.

Respond with ONLY this JSON object. No reasoning. No commentary. No markdown fences.

{{"faithfulness": {{"pass": true, "violations": []}}, "no_data_in_narrative": {{"pass": true, "violations": []}}}}

Change "pass" to false and add violation strings only where a rule is violated."""

_EVAL_RULES = ["faithfulness", "no_data_in_narrative"]


def _evaluate_proposal(proposal: NarrativeProposal, curated_context: str) -> dict:
    """Evaluate a generated proposal against quality rules. Non-blocking."""
    proposal_text = (
        f"OPPORTUNITY:\n{proposal.opportunity}\n\n"
        f"CURRICULUM COMPOSITION:\n{proposal.justification.curriculum_composition}\n\n"
        f"STUDENT COMPOSITION:\n{proposal.justification.student_composition}\n\n"
        f"ROADMAP:\n{proposal.roadmap}"
    )

    prompt = _EVAL_PROMPT.format(context=curated_context, proposal=proposal_text)

    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1536,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        result = _extract_json(raw)

        passed = sum(1 for r in _EVAL_RULES if result.get(r, {}).get("pass", False))
        logger.info(f"Proposal eval for {proposal.employer}: {passed}/{len(_EVAL_RULES)} rules passed")
        for rule in _EVAL_RULES:
            rule_result = result.get(rule, {})
            if not rule_result.get("pass", True):
                for v in rule_result.get("violations", []):
                    logger.warning(f"  FAIL [{rule}]: {v}")

        return result

    except Exception as e:
        logger.error(f"Proposal evaluation failed: {e}")
        return {"error": str(e)}
