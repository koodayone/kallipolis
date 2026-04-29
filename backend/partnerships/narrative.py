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


def _build_institutional_chain_block(
    gathered: GatheredContext,
    curriculum_evidence: list[dict],
    selected_occ: dict,
    swp_evidence: SwpEvidence,
) -> list[str]:
    """Render the empirical chain that grounds every claim in the
    artifact: Employer → SOC → CIP → TOP6 → College Department →
    Pipeline → Region. Each link names its institutional source so the
    narrative LLM has structure to walk rather than interpret beyond.

    The chain is the artifact's epistemic foundation — every categorical
    claim made by the prose can be traced back to one of these links,
    each authored by an external institution: the BLS/NCES CIP-SOC
    crosswalk, the California Chancellor's Office TOP-CIP crosswalk,
    the Centers of Excellence regional demand and supply publications.
    Returns an empty list when the chain has insufficient data
    (no SOC, no aligned departments) — caller decides whether to
    skip it or render an honest empty-set block.
    """
    occ_title = selected_occ.get("title", "")
    occ_soc = selected_occ.get("soc_code", "")
    if not occ_soc or not occ_title:
        return []

    # Selected occupation's CIP set (BLS/NCES CIP-SOC crosswalk side).
    selected_swp_occ = next(
        (o for o in swp_evidence.occupations if o.soc_code == occ_soc),
        None,
    )
    cip_codes = (selected_swp_occ.cip_codes if selected_swp_occ else []) or []

    # Department-level via_top / via_cip aggregation.
    aligned_depts = []
    all_via_top: set[str] = set()
    for d in curriculum_evidence:
        dept_name = d.get("department", "")
        d_via_top = d.get("via_top") or []
        course_count = len(d.get("courses") or [])
        aligned_depts.append((dept_name, d_via_top, course_count))
        all_via_top.update(d_via_top)

    coe_region = swp_evidence.coe_region or ""
    coe_region_display = (
        swp_evidence.sources.coe_region_display
        if swp_evidence.sources else coe_region
    )

    lines = ["INSTITUTIONAL CHAIN (the empirical foundation of this artifact — every categorical claim below traces to one of these external sources):"]
    lines.append(f"  Employer hires for SOC {occ_soc} ({occ_title})")
    if cip_codes:
        lines.append(
            f"  → BLS/NCES CIP-SOC crosswalk: SOC {occ_soc} ↔ "
            f"CIP {', '.join(cip_codes[:3])}{' …' if len(cip_codes) > 3 else ''}"
        )
    if aligned_depts:
        lines.append(
            "  → Chancellor's Office TOP-CIP crosswalk routes those CIPs to "
            f"TOP {', '.join(sorted(all_via_top)) if all_via_top else '(unknown)'}"
        )
        lines.append("  → College departments operating courses in those TOP codes:")
        for dept_name, d_via_top, course_count in aligned_depts:
            via_str = f" [TOP {', '.join(d_via_top)}]" if d_via_top else ""
            lines.append(f"      {dept_name}{via_str}: {course_count} aligned courses")
    else:
        lines.append("  → No college departments at this college operate courses in any TOP that crosswalks to this SOC.")
    if coe_region:
        lines.append(
            f"  → COE Bay region demand: {swp_evidence.total_demand:,} annual openings"
            if coe_region == "Bay"
            else f"  → COE {coe_region_display or coe_region} region demand: {swp_evidence.total_demand:,} annual openings"
        )
        lines.append(
            f"  → COE supply: {swp_evidence.total_supply:.0f} annual completions; "
            f"workforce gap: {swp_evidence.gap:,.0f}"
        )
    lines.append(
        "  Source attributions: Chancellor's Office TOP-CIP Crosswalk; "
        "BLS/NCES CIP-SOC Crosswalk; California Centers of Excellence "
        "regional demand and supply data."
    )
    lines.append("The narrative below WALKS this chain. It does not invent connections beyond it.")
    return lines


def _build_narrative_context(
    gathered: GatheredContext,
    dept_text: str,
    selected_occ: dict,
    student_stats: dict,
    swp_evidence: SwpEvidence,
    curriculum_evidence: list[dict] | None = None,
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

    lines = []

    # INSTITUTIONAL CHAIN block — surfaces the empirical chain to the
    # LLM in code-named form so the prose has a structure to walk
    # rather than interpret beyond. Each link names its institutional
    # source: the Chancellor's Office TOP-CIP crosswalk, the BLS/NCES
    # CIP-SOC crosswalk, the COE regional demand and supply data.
    # The narrative prompt asks the LLM to walk this chain; the eval
    # rules verify that the prose attributes correctly. When the
    # curriculum_evidence list is not passed (legacy callers, mocks),
    # the chain block silently falls through to the rest of the
    # context — the chain is additive, not load-bearing on existing
    # call paths.
    if curriculum_evidence is not None:
        chain_block = _build_institutional_chain_block(
            gathered, curriculum_evidence, selected_occ, swp_evidence
        )
        if chain_block:
            lines.extend(chain_block)
            lines.append("")

    lines.extend([
        f"EMPLOYER: {gathered.employer_name}",
        f"Sector: {primary_sector}" if primary_sector else None,
        f"Description: {gathered.description}" if gathered.description else None,
        f"Regions employer operates in: {', '.join(gathered.regions)}" if gathered.regions else None,
        f"College: {gathered.college}",
        f"COE region for regional labor market data: {swp_evidence.coe_region}" if swp_evidence.coe_region else None,
        "",
    ])

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

    # Student pipeline counts.
    total_in_aligned = student_stats.get("total_in_aligned_departments", 0)
    total_in_program = student_stats.get("total_in_program", 0)
    with_all_core = student_stats.get("with_all_core_skills", 0)
    lines.append("STUDENT PIPELINE:")
    lines.append(
        f"  HEADLINE — Students enrolled in courses across the aligned departments (deduplicated): {total_in_aligned:,}"
    )
    lines.append(
        f"  Students whose declared primary focus is one of the aligned departments: {total_in_program:,}"
    )
    lines.append(
        f"  Students enrolled in courses developing all {len(core_skills)} core skills: {with_all_core:,}"
    )
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

ARCHITECTURAL PREMISE: institutional deference. Every categorical claim in your prose must trace to one of the externally-authored institutional sources named in the INSTITUTIONAL CHAIN block at the top of the context: the California Chancellor's Office TOP-CIP crosswalk, the BLS/NCES CIP-SOC crosswalk, or the California Centers of Excellence regional demand and supply data. The chain is the case. Your job is to walk it, not interpret beyond it. Do not invent connections the chain does not build.

Below is curated institutional context for a specific employer.

{context}

Each narrative section is followed by a structured evidence block that shows the complete record — every department, course, skill, and figure. The evidence block handles completeness. Your narrative handles meaning. Be selective: highlight the most significant elements and explain why they matter for this partnership. Do not summarize or enumerate what the evidence block already shows. Do not speculate about career progressions, advancement pathways, or specific collaboration shapes.

Argument structure: You are writing one continuous argument across four sections — executive summary, occupational demand, curriculum alignment, and student impact. Each section after the executive summary begins with its central claim in a single direct sentence. The first sentence states what the section argues. The sentences that follow substantiate that claim with evidence from the context. Do not build toward the point. State it, then support it. Each topic sentence must be specific to this employer and college — not a generic template phrase.

Section claims:

- EXECUTIVE SUMMARY (1 paragraph, ~70-90 words, four sentences): The partnership thesis. State the case for why this college and this employer should partner, anchored in three concrete facts: the employer in regional context, the count of college courses whose TOP code maps to the selected occupation's SOC, and the count of students enrolled in those departments' courses. Plain agent-subject grammar throughout — the employer, the college, and the students act; codes are anchors named on nouns, never subjects.
  STRUCTURE — four sentences, in order, each carrying one idea:
    1. EMPLOYER IN REGIONAL CONTEXT: Characterize the employer through what they do — operations, scale, or scope — and place them in the COE region by name. The employer is the subject. One sentence, declarative.
    2. PARTNERSHIP THESIS: State that the college can partner with the employer to fulfill their hiring needs by leveraging the college's institutional assets. The college is the subject. This sentence frames the rest of the paragraph; it is the only place the partnership is explicitly proposed.
    3. CURRICULUM PROOF: State the count of courses at this college whose TOP code maps to the selected occupation's SOC. Sum the per-department aligned course counts from the INSTITUTIONAL CHAIN block. Name the SOC code as a property of the occupation, not as a subject. Example shape: "The college offers 15 courses with TOP codes that map to SOC 49-1011, the target occupation for this partnership." The college is the subject.
    4. STUDENT PIPELINE PROOF: State the count of students enrolled in courses across the aligned departments — use the HEADLINE figure from the STUDENT PIPELINE block (the deduplicated count of students enrolled in any course in any aligned department at this college). Frame it as a sourceable talent pool. Example shape: "5,000 students have taken courses in the departments offering these courses, indicating a talent pool that can be sourced to fulfill labor market demand." Students are the subject.
  TONE: Each sentence advances one idea. Light evaluative framing is acceptable in sentences 2 and 4 ("by leveraging its institutional assets," "indicating a talent pool that can be sourced") since this section makes the case. Keep evaluative language measured — never superlative.
  FORBIDDEN:
    - Specific wage figures or annual openings counts (those belong in OCCUPATIONAL DEMAND).
    - The workforce gap figure (the proposal's gap visualization shows it; prose does not need to repeat).
    - Naming a partnership type or prescribing a collaboration shape (advisory board, internship pipeline, curriculum codesign, etc.).
    - Superlatives: "exceptional," "remarkable," "transformative," "industry-leading."
    - Direct-mapping interpretive bridges: "directly maps," "maps directly," "perfect fit," "turnkey," "seamless," "1:1 alignment." Always use "map to," "aligns with," or "prepares students for" — never the directness adverbs.
    - Generic openers: "This partnership opportunity..." "There is significant demand..." Lead with the employer's name or operations, not a meta-observation.
    - Crosswalk mechanism vocabulary: "BLS/NCES crosswalk," "CIP code," "Chancellor's Office crosswalk," "the institutional crosswalk routes...". The crosswalk is the *source* of the alignment claim and belongs in CURRICULUM ALIGNMENT where the institutional pathway is named explicitly. The executive summary uses the result, not the mechanism.
    - Industry-fit hedging: "industry-portable," "transferable foundation," "turnkey match," "transfer across manufacturing industries," "partnership-conversation topic." The detail sections show the departments involved; the coordinator can read the fit themselves. The exec summary does not pre-apologize.

- OCCUPATIONAL DEMAND (2-3 sentences): The employer's hiring profile represents institutionally significant regional labor market demand, scoped to the SELECTED OCCUPATION only.
  REQUIRED REFERENCES:
    - The selected occupation's title and SOC code from the SELECTED OCCUPATION block.
    - The Median annual wage AND Annual openings figures listed in the SELECTED OCCUPATION block. These are the only wage/openings figures permitted in this section.
    - The COE region by name AND a phrase that attributes the demand-data source — "Centers of Excellence projections," "COE [region] regional data," or similar. The figures' authority comes from the COE; surface that.
  FORBIDDEN:
    - Citing wage/openings figures from any other occupation in the BROADER HIRING PROFILE list. Those figures belong to other roles the employer hires for; they describe the employer's overall hiring scale, not the demand for the selected role.
    - Citing the aggregate demand total from the REGIONAL SUPPLY-DEMAND block. That total sums multiple occupations and belongs only in the SWP evidence table, not in this section's prose.
    - Framing the figures as "national" or "across the country" — these are COE-region figures.
    - Speculation about career ladders or advancement.

- CURRICULUM ALIGNMENT (exactly 2 sentences): The table caption for the department evidence rendered immediately below. The prose frames what the table shows; it does not enumerate or rank the departments.
  STRUCTURE — two sentences, in order:
    1. SOURCE + PATHWAY FRAMING: Attribute the pathway claim to the institutional source by plain name, and state that the departments below prepare students for the selected occupation by SOC code. Use this exact source phrasing: "the SOC-to-TOP institutional crosswalk maintained by the California Chancellor's Office." Example shape: "According to the SOC-to-TOP institutional crosswalk maintained by the California Chancellor's Office, the departments below prepare students for SOC 49-1011."
    2. COMPETENCY FRAMING: State that these departments develop the core competencies required to perform the selected occupation, named by its official SOC title, at this employer. Example shape: "These departments develop the core competencies required to perform the role of First-Line Supervisors of Mechanics, Installers, and Repairers at Amtrak."
  PRINCIPLE: The pathway claim rests on the institutional crosswalk; the prose names the source, points at the table, and frames what the table represents. Specificity (which departments, which TOP codes, which courses, which skills) is in the table — the prose is the caption above it.
  WHEN PARTIAL SKILL COVERAGE: If the prose ever needs to flag that a core skill is not covered by the institutionally-aligned courses, use strengthening-language only: "could be strengthened," "an opportunity to deepen," "could be more rigorously developed." Default behavior is silence — let the table speak.
  FORBIDDEN:
    - Naming any specific department, TOP6 code, CIP code, course count, or competency name in the prose. Those belong in the table.
    - Ranking departments ("the most aligned department is…," "the strongest preparation comes from…"). The system's department ranking is noisy; the prose must not over-claim it.
    - Economic figures (wages, openings, growth percentages, employment counts).
    - Deficit language: "missing," "does not address," "falls short," "not fully prepared."
    - Direct-mapping interpretive bridges (same list as EXECUTIVE SUMMARY).
    - Skills-as-pathway claims: do not write that a skill "prepares students for" or "qualifies graduates for" or "is the gateway to" the occupation. Skills characterize courses; the institutional crosswalk is what prepares.
    - Departing from the prescribed source phrasing in sentence 1. The exact phrase "the SOC-to-TOP institutional crosswalk maintained by the California Chancellor's Office" is the authoritative attribution; do not paraphrase it into "the BLS/NCES crosswalk," "the Centers of Excellence crosswalk," or any other variant.

- STUDENT IMPACT (exactly 2 sentences): The table caption for the candidate table rendered immediately below. The prose frames the headline pipeline count and points at the table; it does not name individual students or departments.
  STRUCTURE — two sentences, in order:
    1. PIPELINE COUNT + INSTITUTIONAL ANCHOR: State the headline count from the STUDENT PIPELINE block (the deduplicated total enrolled in courses across the aligned departments). Anchor to the institutional pathway by referring to "the TOP-SOC crosswalk" and naming the SOC by code. Example shape: "3,000 students are enrolled in the departments containing TOP codes that align with SOC 49-1011."
    2. TABLE POINTER + PREPARATION FRAMING: Point at the candidate table that follows ("Shown below are…") and frame the candidates as students whose coursework on the TOP-SOC crosswalk gives them the strongest pathway preparation. Example shape: "Shown below are students that are most strongly prepared with the coursework included in the TOP-SOC crosswalk."
  PRINCIPLE: This section is a caption for the candidate table. The headline count is the institutional pipeline figure; the table itself shows the ranked candidates. The word "prepared" is OK in this section ONLY when its grammatical object is coursework or the institutional pathway ("prepared with the coursework," "prepared by the TOP-SOC pathway"). Never claim students are prepared FOR the role, the work, the job, or the employer — that's a readiness over-claim the data cannot support.
  FORBIDDEN:
    - Naming individual students or specific departments in the prose. Those belong in the table.
    - Specific student-count figures other than the HEADLINE pipeline count (the with-all-core-skills figure and the primary-focus figure may exist in the data block but do not appear in this section's prose).
    - Economic figures.
    - Readiness over-claims: "students are ready," "students are qualified," "students are a fit," "well-qualified." These claim graduate readiness the data cannot support.
    - Skills-as-readiness claims: do not write that a skill makes students "qualified" or "ready" for the role.
    - Departing from the prescribed source phrasing for the institutional pathway: use the short form "the TOP-SOC crosswalk" in this section (the full attribution lives in CURRICULUM ALIGNMENT).

Write a single JSON object:

{{
  "executive_summary": "<single paragraph, ~80 words>",
  "occupational_demand": "<2-3 sentences>",
  "curriculum_alignment": "<exactly 2 sentences>",
  "student_impact": "<exactly 2 sentences>"
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

Executive Summary: Kaiser Permanente operates inpatient and outpatient clinical facilities across the Far North COE region. Shasta College can partner with Kaiser to fulfill its clinical hiring needs by leveraging the college's institutional assets. The college offers 28 courses with TOP codes that map to SOC 29-1141, the target occupation for this partnership. 1,140 students have taken courses in the departments offering these courses, indicating a talent pool that can be sourced to fulfill labor market demand.

Occupational Demand: Kaiser Permanente's Far North hiring centers on Registered Nurses (29-1141), with roughly 1,200 regional annual openings and median annual wages near $130,000. The company's clinical scope spans inpatient and outpatient settings, generating a diverse set of nursing competencies new hires are expected to bring on day one.

Curriculum Alignment: According to the SOC-to-TOP institutional crosswalk maintained by the California Chancellor's Office, the departments below prepare students for SOC 29-1141. These departments develop the core competencies required to perform the role of Registered Nurses at Kaiser Permanente.

Student Impact: 1,140 students are enrolled in the departments containing TOP codes that align with SOC 29-1141. Shown below are students that are most strongly prepared with the coursework included in the TOP-SOC crosswalk.

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
    # Enrich each occupation row from gathered context with the CIP
    # codes the BLS/NCES CIP-SOC crosswalk maps to its SOC. The SwpEvidence
    # already carries this on its single selected-SOC row; opportunity_evidence
    # mirrors the same enrichment so any caller reading directly from
    # the proposal's opportunity_evidence sees the institutional chain
    # without needing to cross-reference swp_evidence.
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
            total_in_aligned_departments=student_stats.get("total_in_aligned_departments", 0),
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
