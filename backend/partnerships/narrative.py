"""LLM-based proposal authoring: narrative context builder, the unified
four-section prompt, the LLM call, response parsing, and proposal assembly.

The artifact has four narrative sections (executive summary, occupational
demand, curriculum alignment, student impact) plus a tabular regional
supply-demand evidence block. The narrative carries meaning; the evidence
blocks carry completeness."""

from __future__ import annotations

import logging
import os

import anthropic

from partnerships.filter import _extract_json
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


# ═══════════════════════════════════════════════════════════════════════════
# Narrative context builder
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


def _build_narrative_context(
    gathered: GatheredContext,
    dept_text: str,
    selected_occ: dict,
    student_stats: dict,
    swp_evidence: SwpEvidence,
) -> str:
    """Build the curated context for the unified narrative prompt.

    Includes everything the four sections need to reference:
    - Employer profile + the occupations it hires for (top 6 by openings, with
      the selected occupation highlighted) so the executive summary can
      characterize the hiring profile and the occupational demand section can
      cite specific figures
    - Curriculum alignment block (departments + courses + missing skills) for
      the curriculum alignment section
    - Student pipeline counts so the student impact section can cite specific
      numbers instead of generalizing
    - Regional supply-demand summary so the executive summary can anchor the
      COE region scope (avoiding national-vs-regional confusion)
    """
    occ_title = selected_occ.get("title", "Unknown")
    occ_soc = selected_occ.get("soc_code", "")
    core_skills = selected_occ.get("core_skills", [])

    # Surface the SWP-canonical sector to the LLM context, falling back
    # to BLS only when the employer has no Doing-What-Matters
    # classification. This keeps the narrative voice institutionally
    # aligned with the rest of the artifact (CTE program references,
    # regional priority sectors, SWP funding language).
    primary_sector = gathered.swp_sectors[0] if gathered.swp_sectors else gathered.sector

    lines = [
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {primary_sector}" if primary_sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions employer operates in: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        f"COE region for regional labor market data: {swp_evidence.coe_region}" if swp_evidence.coe_region else None,
        "",
    ]

    # SELECTED OCCUPATION block — the figures cited in the OCCUPATIONAL DEMAND
    # section MUST come from here, not from the broader hiring profile below.
    selected_occ_data = next(
        (o for o in gathered.occupation_evidence if o.get("title") == occ_title),
        None,
    )
    lines.append("SELECTED OCCUPATION (the role this artifact is scoped to — cite THESE figures in OCCUPATIONAL DEMAND):")
    lines.append(f"  Title: {occ_title}")
    lines.append(f"  SOC code: {occ_soc}")
    if selected_occ_data:
        if selected_occ_data.get("annual_wage"):
            lines.append(f"  Median annual wage: ${selected_occ_data['annual_wage']:,}")
        if selected_occ_data.get("annual_openings"):
            lines.append(f"  Annual openings (regional): {selected_occ_data['annual_openings']:,}")
        if selected_occ_data.get("growth_rate") is not None:
            lines.append(f"  Projected employment growth: {selected_occ_data['growth_rate']:+.1%}")
        if selected_occ_data.get("employment"):
            lines.append(f"  Regional employment: {selected_occ_data['employment']:,}")
    lines.append(f"  Core skills: {', '.join(core_skills)}")
    lines.append("")

    # Broader hiring profile — top 6 by annual openings. Used by the EXECUTIVE
    # SUMMARY to characterize what the employer does (one or two roles that
    # capture operational identity). The OCCUPATIONAL DEMAND section must
    # NOT cite figures from this list — those figures belong only to roles
    # that are not the selected one.
    occupations_sorted = sorted(
        gathered.occupation_evidence,
        key=lambda o: (o.get("annual_openings") or 0),
        reverse=True,
    )[:6]

    lines.append("BROADER HIRING PROFILE (other occupations this employer hires for, top 6 by openings — use ONLY for executive summary context, do NOT cite these figures in OCCUPATIONAL DEMAND):")
    for occ_ev in occupations_sorted:
        is_selected = occ_ev.get("title") == occ_title
        marker = " ← this is the SELECTED OCCUPATION (figures listed in the block above)" if is_selected else ""
        parts = [f"  {occ_ev.get('soc_code', '?'):<10} {occ_ev.get('title', '?')}{marker}"]
        details = []
        if not is_selected:
            if occ_ev.get("annual_wage"):
                details.append(f"${occ_ev['annual_wage']:,}/yr median")
            if occ_ev.get("annual_openings"):
                details.append(f"{occ_ev['annual_openings']:,} annual openings")
            if occ_ev.get("growth_rate") is not None:
                details.append(f"{occ_ev['growth_rate']:+.1%} employment growth")
        if details:
            parts.append(f"     {', '.join(details)}")
        lines.extend(parts)
    lines.append("")

    # Curriculum alignment: departments + courses + missing skills.
    lines.append(dept_text)
    lines.append("")

    # Student pipeline counts for the student impact section.
    total_in_program = student_stats.get("total_in_program", 0)
    with_all_core = student_stats.get("with_all_core_skills", 0)
    lines.append("STUDENT PIPELINE (scoped to the selected occupation's core skills):")
    lines.append(f"  Students enrolled in courses that develop one or more core skills: {total_in_program:,}")
    lines.append(f"  Students enrolled in courses developing all {len(core_skills)} core skills: {with_all_core:,}")
    if swp_evidence.department_enrollments:
        dept_enrollment_str = ", ".join(
            f"{d.department} ({d.student_count:,})"
            for d in swp_evidence.department_enrollments
        )
        lines.append(f"  Department-level total enrollment: {dept_enrollment_str}")
    lines.append("")

    # Regional supply-demand summary, scoped to the selected occupation
    # (the same SOC the rest of the artifact is built around). The gap is
    # the integrative figure cited at the close of the executive summary;
    # it must be a meaningful one-occupation reading, not an
    # asymmetric cross-occupation aggregate.
    if swp_evidence.coe_region:
        lines.append(f"REGIONAL SUPPLY-DEMAND ({swp_evidence.coe_region} COE region, scoped to the SELECTED occupation):")
        lines.append(f"  Annual regional demand for {occ_title}: {swp_evidence.total_demand:,} openings")
        lines.append(f"  Annual projected supply across {len(swp_evidence.supply_estimates)} aligned TOP codes: {swp_evidence.total_supply:.0f} completions")
        lines.append(f"  Workforce gap (demand minus supply, both scoped to this occupation): {swp_evidence.gap:,.0f}")
        lines.append("  Note: the gap is the integrative figure for the executive summary's closing line.")
        lines.append("  It compares this region's demand for this occupation against the supply produced by the curriculum that prepares for it.")

    return "\n".join(line for line in lines if line is not None)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3: The unified four-section narrative prompt
# ═══════════════════════════════════════════════════════════════════════════

NARRATIVE_PROMPT = """You are a workforce partnership analyst writing for Kallipolis, an institutional intelligence platform for California community colleges.

Kallipolis voice: short sentences. Direct. No filler. No em dashes. State the fact, move on. Every sentence carries a concrete claim or a specific insight. If a sentence could be cut without losing information, cut it. The reader is a busy program coordinator who will skim past anything that feels like LLM output.

Below is curated institutional context for a specific employer.

{context}

Each narrative section is followed by a structured evidence block that shows the complete record — every department, course, skill, and figure. The evidence block handles completeness. Your narrative handles meaning. Be selective: highlight the most significant elements and explain why they matter for this partnership. Do not summarize or enumerate what the evidence block already shows. Do not speculate about career progressions, advancement pathways, or specific collaboration shapes.

Argument structure: You are writing one continuous argument across four sections — executive summary, occupational demand, curriculum alignment, and student impact. Each section after the executive summary begins with its central claim in a single direct sentence. The first sentence states what the section argues. The sentences that follow substantiate that claim with evidence from the context. Do not build toward the point. State it, then support it. Each topic sentence must be specific to this employer and college — not a generic template phrase.

Section claims:

- EXECUTIVE SUMMARY (1 paragraph, ~70-80 words): The institutional case for this partnership, integrating four threads into a single synthetic paragraph.
  STRUCTURE — four threads woven through the paragraph in this order:
    1. EMPLOYER IDENTITY: Characterize the employer through what they do — their operations, scale, or scope — not through their hiring count. One sentence, declarative.
    2. REGIONAL DEMAND CONTEXT: Set up the labor-market context for the selected occupation. Use directional language ("accelerating demand," "rising need," "growing requirement") anchored in the COE region by name. No specific wage or openings figures here — those belong in OCCUPATIONAL DEMAND.
    3. CURRICULUM CAPABILITY: Name the most aligned department and two-to-four core competencies it develops for this occupation. The competencies should come from the core skills list. Treat them as comma-separated competencies in the flow of the sentence.
    4. WORKFORCE GAP: Close with the gap figure from the REGIONAL SUPPLY-DEMAND block as the integrative claim. Phrase it neutrally ("Labor market analysis indicates an unmet workforce gap of N on an annual basis"). The gap is the only figure permitted in this section — it earns its place because it synthesizes demand and supply into one number.
  TONE: Light evaluative framing is acceptable here ("represents a strong partnership candidate," "positions the college to address"), since this section's job is to make the case. The other three sections do the granular substantiation. Keep evaluative language measured — never superlative.
  FORBIDDEN:
    - Specific wage figures or annual openings counts (those belong in OCCUPATIONAL DEMAND).
    - Specific student counts (those belong in STUDENT IMPACT).
    - Course counts (those belong in CURRICULUM ALIGNMENT).
    - Naming a partnership type or prescribing a collaboration shape (advisory board, internship pipeline, curriculum codesign, etc.).
    - Superlatives: "exceptional," "remarkable," "transformative," "industry-leading."
    - Generic openers: "This partnership opportunity..." "There is significant demand..." Lead with the employer's name or operations, not a meta-observation.

- OCCUPATIONAL DEMAND (2-3 sentences): The employer's hiring profile represents institutionally significant regional labor market demand, scoped to the SELECTED OCCUPATION only.
  REQUIRED REFERENCES:
    - The selected occupation's title and SOC code from the SELECTED OCCUPATION block.
    - The Median annual wage AND Annual openings figures listed in the SELECTED OCCUPATION block. These are the only wage/openings figures permitted in this section.
    - The COE region by name (so the geographic scope is explicit, not implied).
  FORBIDDEN:
    - Citing wage/openings figures from any other occupation in the BROADER HIRING PROFILE list. Those figures belong to other roles the employer hires for; they describe the employer's overall hiring scale, not the demand for the selected role.
    - Citing the aggregate demand total from the REGIONAL SUPPLY-DEMAND block. That total sums multiple occupations and belongs only in the SWP evidence table, not in this section's prose.
    - Framing the figures as "national" or "across the country" — these are COE-region figures.
    - Speculation about career ladders or advancement.

- CURRICULUM ALIGNMENT (2-3 sentences): Specific departments at the college develop the skills these occupations require.
  REQUIRED REFERENCES: At least one specific department name from the curriculum evidence. At least one specific skill name from the core skills list. Course counts (e.g., "across 33 courses") are appropriate when they characterize the depth of preparation.
  PARTIAL ALIGNMENT: When a department covers some but not all core skills, name the partial alignment honestly using strengthening-language: "could be strengthened," "an opportunity to deepen," "could be more rigorously developed."
  FORBIDDEN: Economic figures (wages, openings, growth percentages, employment counts). Enumerating every department the evidence block lists. Deficit language: "missing," "does not address," "falls short," "not fully prepared."

- STUDENT IMPACT (2-3 sentences): The composition and alignment of the student pipeline with this opportunity.
  REQUIRED REFERENCES: At least one specific student count from the student pipeline data — the total enrolled in core-skill courses, OR the count carrying all core skills, OR a department-level enrollment figure. At least one department name.
  FORBIDDEN: Economic figures. Evaluative readiness language ("ready," "prepared," "qualified," "fit"). State the composition; do not evaluate it.

Write a single JSON object:

{{
  "executive_summary": "<single paragraph, ~80 words>",
  "occupational_demand": "<2-3 sentences>",
  "curriculum_alignment": "<2-3 sentences>",
  "student_impact": "<2-3 sentences>"
}}

Tone:
- Short, direct sentences. Each sentence makes one point. If a sentence has more than one comma, it is probably making more than one point. Split it. No subordinate clauses that explain why something matters. State it and move on.
- Figures are fine where they flow naturally. Do not avoid them artificially.
- No em dashes (the long horizontal punctuation mark, like this — see how it interrupts the rhythm). Use commas, semicolons, or parentheses instead. This rule is strict: zero em dashes anywhere in any section. No rhetorical flourishes. No "remarkably," "notably," "importantly."
- Reference departments and skills naturally within the flow of sentences. Department names are proper nouns and should be capitalized. When referencing a department, use "the [Name] department" or "the [Name] program" so the reader knows it is an organizational unit, not a general concept — "the Environmental Control Technology department" not "Environmental Control Technology." Skill names are not proper nouns and should be lowercase (food safety, operations management, clinical documentation). Legitimate acronyms (HVAC, HACCP, EPA, OSHA, EHR, BLS) retain their standard capitalization. Weave names into the argument rather than listing them as labels.
- Present evidence, not instructions. The reader is the decision-maker. The narrative presents the case. It does not prescribe the action.
- When discussing the college's programs, affirm what the department does well. The coordinator built these programs. Respect that work. When alignment is partial, name it honestly — but frame partial alignment as an area for potential strengthening.
- Do not say "missing," "does not address," "falls short," or "not fully prepared." Use "can be strengthened," "an opportunity to deepen," or "could be more rigorously developed" when partial alignment needs to be named.
- Do not use bullet points or numbered lists.
- Focus on workforce-oriented programs. Be cautious about characterizing foundational or general education courses (e.g., biology, chemistry, mathematics) as primary targets for this partnership — these courses serve many pathways.
- Do not introduce skill names that are not in the context. Do not assert how many core skills a department covers or claim complete coverage.
- Do not restate what has already been established within a section. Once a skill or department has been named and its role in the argument established, subsequent sentences should build on that rather than re-list it. Each sentence should introduce new information or advance the argument.

Epistemic standard: Be persuasive and epistemically rigorous. Persuade through specificity and grounded evidence, not through superlatives or exclusivity claims. Do not claim the employer is unique, the only option, the best fit, or irreplaceable. Characterize what they do and let the evidence make the case. If a claim cannot be verified from the data provided, do not make it.

REFERENCE EXAMPLE (match this prose quality — do not copy its content):

Executive Summary: Kaiser Permanente operates inpatient and outpatient clinical facilities across the Far North COE region, with a hiring profile centered on registered nurses and allied health roles. The college's Nursing department develops the clinical reasoning and documentation workflows central to Kaiser's roles, and the Health Sciences program extends that preparation into supervised practice. Students across these programs are completing coursework aligned with the competencies Kaiser hires for.

Occupational Demand: Kaiser Permanente's Far North hiring centers on Registered Nurses (29-1141), with roughly 1,200 regional annual openings and median annual wages near $130,000. The company's clinical scope spans inpatient and outpatient settings, generating a diverse set of nursing competencies new hires are expected to bring on day one.

Curriculum Alignment: The Nursing department provides the most direct preparation for Kaiser's clinical roles, developing patient care, clinical documentation, and assessment across 28 courses. The Health Sciences program extends this into supervised practice settings, deepening preparation in clinical assessment.

Student Impact: The Nursing department has 1,140 students enrolled in courses developing the relevant clinical competencies, with 240 carrying all three core skills. The Health Sciences program adds another concentration of students preparing for clinical roles.

Return ONLY valid JSON with no text before or after."""


# ═══════════════════════════════════════════════════════════════════════════
# Parsing & Assembly
# ═══════════════════════════════════════════════════════════════════════════


def _parse_narrative_fields(raw: str) -> dict:
    """Extract the four narrative sections from Claude's JSON response."""
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    data = _extract_json(raw)

    return {
        "executive_summary": data.get("executive_summary", ""),
        "occupational_demand": data.get("occupational_demand", ""),
        "curriculum_alignment": data.get("curriculum_alignment", ""),
        "student_impact": data.get("student_impact", ""),
    }


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
    core_skills: list[str] | None = None,
) -> NarrativeProposal:
    """Merge LLM-generated narrative with deterministic evidence blocks."""
    occ_evidence = [
        OccupationEvidence(**o) for o in gathered.occupation_evidence
        if o.get("title") == selected_occ.get("title")
    ] or [OccupationEvidence(**o) for o in gathered.occupation_evidence[:1]]

    return NarrativeProposal(
        employer=employer,
        sector=sector,
        selected_occupation=selected_occ.get("title", ""),
        selected_soc_code=selected_occ.get("soc_code"),
        core_skills=core_skills or selected_occ.get("core_skills", []),
        regions=gathered.regions,
        executive_summary=narrative["executive_summary"],
        occupational_demand=narrative["occupational_demand"],
        curriculum_alignment=narrative["curriculum_alignment"],
        student_impact=narrative["student_impact"],
        opportunity_evidence=occ_evidence,
        curriculum_evidence=[DepartmentEvidence(**d) for d in curriculum_evidence],
        student_evidence=StudentEvidence(
            total_in_program=student_stats.get("total_in_program", 0),
            with_all_core_skills=student_stats.get("with_all_core_skills", 0),
            top_students=[StudentSummaryEvidence(**s) for s in top_students],
        ),
        swp_evidence=swp_evidence,
    )


def _call_claude(prompt_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    )
    return message.content[0].text
