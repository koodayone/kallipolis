"""Deterministic quality evals for the four-section partnership artifact.

Every check is fast, repeatable, and runs against the structured proposal —
no LLM judge, no network calls. Each check returns a list of violation
strings. Empty list = pass.

Checks are non-blocking: a proposal still ships even if it has violations.
The violations are logged + returned so callers can surface them inline
(e.g., the atlas can render "this artifact has 2 quality concerns").

The check categories:

  Section discipline — economic figures only in Occupational Demand;
  no economic figures in Executive Summary, Curriculum Alignment, or
  Student Impact.

  Incorporation — each section must reference specific data from the
  context: department names, skill names, occupation/SOC, student counts,
  COE region.

  Voice — banned phrases (deficit language, evaluative superlatives,
  type prescription, em dashes), department naming convention.

  Math integrity — SwpEvidence totals match the underlying lists.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from partnerships.models import NarrativeProposal

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Result types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class EvalViolation:
    rule: str
    section: str  # "executive_summary", "occupational_demand", ..., or "swp_evidence"
    message: str


@dataclass
class EvalResult:
    violations: list[EvalViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violation_count": self.violation_count,
            "violations": [
                {"rule": v.rule, "section": v.section, "message": v.message}
                for v in self.violations
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# Banned-phrase patterns
# ═══════════════════════════════════════════════════════════════════════════

# Deficit-language patterns that contradict the strengthening-language rule.
# Surface form: word-boundary matches, case-insensitive. "Gap" alone is allowed
# in the SWP evidence block (it's a quantitative term there); flagged in
# narrative sections.
_DEFICIT_PATTERNS = [
    r"\bmissing\b",
    r"\bdoes not address\b",
    r"\bfalls short\b",
    r"\bnot fully prepared\b",
    r"\blacks?\b",
    r"\bdeficien(?:t|cy|cies)\b",
    r"\binadequate(?:ly)?\b",
    r"\bgap(?:s)?\s+in\b",
]

# Evaluative superlatives banned by the epistemic standard.
_SUPERLATIVE_PATTERNS = [
    r"\bcompelling\b",
    r"\bstrong fit\b",
    r"\bexceptional(?:ly)?\b",
    r"\buniquely\b",
    r"\bthe only\b",
    r"\birreplaceable\b",
    r"\bbest-in-class\b",
    r"\btransformative\b",
    r"\btremendous\b",
    r"\bremarkable\b",
    r"\bextraordinary\b",
]

# Partnership-type prescription patterns. These should not appear in any
# narrative section — the artifact is type-agnostic.
_TYPE_PRESCRIPTION_PATTERNS = [
    r"\badvisory board\b",
    r"\binternship pipeline\b",
    r"\bcurriculum co-design\b",
    r"\bcurriculum codesign\b",
    r"\bco-design partnership\b",
]

# Prescription verbs naming what the coordinator should do.
_PRESCRIPTION_VERB_PATTERNS = [
    r"\bshould (?:establish|form|pursue|implement|launch|create)\b",
    r"\bmust (?:establish|form|pursue|implement|launch|create)\b",
    r"\brecommend(?:ed|s)?\s+(?:establishing|forming|pursuing|implementing|launching|creating)\b",
]

# Readiness evaluation phrases banned in Student Impact (the prompt says
# "state composition; do not evaluate readiness").
_READINESS_PATTERNS = [
    r"\bare ready\b",
    r"\bare prepared\b",
    r"\bare qualified\b",
    r"\bare a (?:strong|good|great) fit\b",
    r"\bwell[- ]prepared\b",
    r"\bwell[- ]qualified\b",
]

# Economic-figure patterns. Match dollar amounts, percentages of growth,
# and explicit openings/employment counts. Used to flag economic content
# in sections where it doesn't belong.
_DOLLAR_AMOUNT = re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?\s*(?:K|k|M|m|/yr|/year|annually|per year)?")
_PERCENT_GROWTH = re.compile(r"[+-]?\s*\d+(?:\.\d+)?\s*%\s*(?:projected\s+)?growth", re.IGNORECASE)
_OPENINGS_COUNT = re.compile(
    r"\b\d{1,3}(?:,\d{3})*\s+(?:annual\s+)?(?:regional\s+)?openings?\b",
    re.IGNORECASE,
)
_EMPLOYMENT_COUNT = re.compile(
    r"\b\d{1,3}(?:,\d{3})*\s+(?:regional\s+)?(?:employment|employed)\b",
    re.IGNORECASE,
)

# National-scope claims that contradict regional COE data.
_NATIONAL_CLAIM_PATTERNS = [
    r"\bnationally\b",
    r"\bacross the country\b",
    r"\bacross the (?:united states|U\.?S\.?)\b",
    r"\bnationwide\b",
]


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _find_pattern(text: str, pattern: str) -> str | None:
    """Return the first match of `pattern` (case-insensitive), or None."""
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(0) if m else None


def _find_any_pattern(text: str, patterns: list[str]) -> list[str]:
    """Return all distinct surface-form matches across the patterns."""
    found: list[str] = []
    seen: set[str] = set()
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            surface = m.group(0).lower()
            if surface not in seen:
                seen.add(surface)
                found.append(m.group(0))
    return found


def _has_economic_figure(text: str) -> list[str]:
    """Return a list of economic-figure surface forms found in `text`."""
    matches: list[str] = []
    for pat in (_DOLLAR_AMOUNT, _PERCENT_GROWTH, _OPENINGS_COUNT, _EMPLOYMENT_COUNT):
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


def _digit_sequences(text: str) -> list[str]:
    """Return all digit sequences (with optional commas) in text — used to
    detect specific numerical references like student counts."""
    return re.findall(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{2,}\b", text)


# ═══════════════════════════════════════════════════════════════════════════
# Section-discipline checks
# ═══════════════════════════════════════════════════════════════════════════


def _check_no_economic_figures_in(
    section_name: str, text: str
) -> list[EvalViolation]:
    """Flag economic figures (wages/openings/growth/employment) appearing in
    sections where they don't belong."""
    findings = _has_economic_figure(text)
    if findings:
        return [
            EvalViolation(
                rule="no_econ_in_wrong_sections",
                section=section_name,
                message=(
                    f"Economic figure(s) appear in {section_name}: "
                    f"{', '.join(findings[:3])}. These belong in occupational_demand."
                ),
            )
        ]
    return []


# ═══════════════════════════════════════════════════════════════════════════
# Voice checks (apply to all narrative sections)
# ═══════════════════════════════════════════════════════════════════════════


def _check_voice(section_name: str, text: str) -> list[EvalViolation]:
    violations: list[EvalViolation] = []

    # Em dashes
    if "—" in text:
        violations.append(
            EvalViolation(
                rule="no_em_dashes",
                section=section_name,
                message="Section contains an em dash; the Kallipolis voice rule forbids them.",
            )
        )

    # Deficit language
    deficit_hits = _find_any_pattern(text, _DEFICIT_PATTERNS)
    if deficit_hits:
        violations.append(
            EvalViolation(
                rule="no_deficit_language",
                section=section_name,
                message=(
                    f"Deficit-language phrase(s) found: {', '.join(deficit_hits)}. "
                    f"Use strengthening-language instead "
                    f"('can be strengthened', 'an opportunity to deepen', 'could be more rigorously developed')."
                ),
            )
        )

    # Evaluative superlatives
    superlative_hits = _find_any_pattern(text, _SUPERLATIVE_PATTERNS)
    if superlative_hits:
        violations.append(
            EvalViolation(
                rule="no_evaluative_superlatives",
                section=section_name,
                message=(
                    f"Evaluative/superlative phrase(s) found: {', '.join(superlative_hits)}. "
                    f"Persuade through specificity and grounded evidence, not adjectives."
                ),
            )
        )

    # Partnership-type prescription
    type_hits = _find_any_pattern(text, _TYPE_PRESCRIPTION_PATTERNS)
    if type_hits:
        violations.append(
            EvalViolation(
                rule="no_type_prescription",
                section=section_name,
                message=(
                    f"Partnership-type phrase(s) found: {', '.join(type_hits)}. "
                    f"The artifact is type-agnostic; the coordinator decides the collaboration shape."
                ),
            )
        )

    # Prescription verbs
    verb_hits = _find_any_pattern(text, _PRESCRIPTION_VERB_PATTERNS)
    if verb_hits:
        violations.append(
            EvalViolation(
                rule="no_prescription",
                section=section_name,
                message=(
                    f"Prescriptive phrase(s) found: {', '.join(verb_hits)}. "
                    f"Present evidence and options, not instructions."
                ),
            )
        )

    return violations


# ═══════════════════════════════════════════════════════════════════════════
# Per-section incorporation checks
# ═══════════════════════════════════════════════════════════════════════════


def _check_executive_summary(p: NarrativeProposal) -> list[EvalViolation]:
    violations: list[EvalViolation] = []
    text = p.executive_summary
    section = "executive_summary"

    if not text or not text.strip():
        violations.append(
            EvalViolation(rule="empty_section", section=section, message="Executive summary is empty.")
        )
        return violations

    # Word count check (target ~80 words; allow 50-120)
    word_count = len(text.split())
    if word_count < 50 or word_count > 120:
        violations.append(
            EvalViolation(
                rule="executive_summary_length",
                section=section,
                message=f"Executive summary is {word_count} words; target is ~80 (range 50-120).",
            )
        )

    # Must mention the COE region (if available)
    coe_region = (p.swp_evidence.coe_region or "").strip()
    if coe_region and coe_region.lower() not in text.lower():
        violations.append(
            EvalViolation(
                rule="missing_coe_region",
                section=section,
                message=f"Executive summary does not name the COE region ('{coe_region}').",
            )
        )

    # Must mention at least one department from the curriculum evidence
    dept_names = [d.department for d in p.curriculum_evidence]
    if dept_names and not any(dept.lower() in text.lower() for dept in dept_names):
        violations.append(
            EvalViolation(
                rule="missing_department_reference",
                section=section,
                message=(
                    f"Executive summary does not name any of the curriculum-evidence departments "
                    f"({', '.join(dept_names[:3])})."
                ),
            )
        )

    # Forbidden: wage / openings / growth / employment figures. The gap
    # figure (workforce gap of N) is structurally different — it's a
    # supply-vs-demand synthesis, not a raw economic figure — so it
    # passes this check naturally and is mandated by the gap-citation
    # rule below.
    violations.extend(_check_no_economic_figures_in(section, text))

    # Required: the workforce gap is the executive summary's signature
    # figure under the new prompt — the only number the LLM is supposed
    # to cite, since it integrates demand and supply into one synthetic
    # claim. Verify the gap value (with ±5% rounding tolerance and
    # comma-formatted fallback) appears in the prose.
    gap = p.swp_evidence.gap if p.swp_evidence else 0
    if gap and abs(gap) >= 1:
        if not _text_contains_gap_value(text, gap):
            violations.append(
                EvalViolation(
                    rule="missing_gap_figure",
                    section=section,
                    message=(
                        f"Executive summary does not cite the workforce gap value ({gap:,.0f}). "
                        f"The gap is the section's required integrative figure under the "
                        f"docs-page Partnership Narrative voice."
                    ),
                )
            )

    # Voice
    violations.extend(_check_voice(section, text))

    return violations


def _text_contains_gap_value(text: str, gap: float) -> bool:
    """Return True iff `text` cites a number matching the gap within a
    5% rounding tolerance. Accepts plain integers, comma-formatted
    integers, and "N annual" / "N on an annual basis" framings.
    """
    target = round(abs(gap))
    if target == 0:
        return False
    # 5% tolerance window matching the demand-figure-faithfulness rule's
    # tolerance posture elsewhere in this module — coordinators round
    # naturally; the eval should not fail on rounding.
    lo = round(target * 0.95)
    hi = round(target * 1.05)
    for m in re.finditer(r"\b\d[\d,]*\b", text):
        try:
            n = int(m.group(0).replace(",", ""))
        except ValueError:
            continue
        if lo <= n <= hi:
            return True
    return False


def _check_occupational_demand(p: NarrativeProposal) -> list[EvalViolation]:
    violations: list[EvalViolation] = []
    text = p.occupational_demand
    section = "occupational_demand"

    if not text or not text.strip():
        violations.append(
            EvalViolation(rule="empty_section", section=section, message="Occupational demand is empty.")
        )
        return violations

    # Required: occupation title OR SOC code
    occ_title = (p.selected_occupation or "").strip()
    occ_soc = (p.selected_soc_code or "").strip()
    has_title = bool(occ_title) and occ_title.lower() in text.lower()
    has_soc = bool(occ_soc) and occ_soc in text
    if not (has_title or has_soc):
        violations.append(
            EvalViolation(
                rule="missing_occupation_reference",
                section=section,
                message=(
                    f"Occupational demand does not reference the selected occupation "
                    f"('{occ_title}', SOC {occ_soc})."
                ),
            )
        )

    # Required: at least one specific economic figure
    if not _has_economic_figure(text):
        violations.append(
            EvalViolation(
                rule="missing_economic_figure",
                section=section,
                message=(
                    f"Occupational demand contains no economic figures (wage, openings, growth). "
                    f"This section is the only place those figures should appear."
                ),
            )
        )

    # Required: COE region by name (if available)
    coe_region = (p.swp_evidence.coe_region or "").strip()
    if coe_region and coe_region.lower() not in text.lower():
        violations.append(
            EvalViolation(
                rule="missing_coe_region",
                section=section,
                message=(
                    f"Occupational demand does not name the COE region ('{coe_region}'). "
                    f"The geographic scope must be explicit."
                ),
            )
        )

    # Forbidden: national-scope claims
    nat_hits = _find_any_pattern(text, _NATIONAL_CLAIM_PATTERNS)
    if nat_hits:
        violations.append(
            EvalViolation(
                rule="no_national_claims",
                section=section,
                message=(
                    f"National-scope phrase(s) found: {', '.join(nat_hits)}. "
                    f"The figures are COE-region data, not national."
                ),
            )
        )

    # Faithfulness: any wage/openings figures cited must match the selected
    # occupation's specific values, not the aggregate demand or another
    # occupation's data.
    violations.extend(_check_demand_figure_faithfulness(p))

    # Voice
    violations.extend(_check_voice(section, text))

    return violations


def _check_demand_figure_faithfulness(p: NarrativeProposal) -> list[EvalViolation]:
    """Verify wage and openings figures in OCCUPATIONAL DEMAND match the
    selected occupation's actual data — not the aggregate, not another
    occupation, not a fabricated round number.

    The selected occupation's data lives in p.opportunity_evidence (filtered
    in _assemble_proposal to just the selected role). Numbers cited in prose
    are matched with formatting tolerance: "$194,960" / "194960" / "near
    $195,000" all parse to 195000-ish, and a wage match is allowed within
    a small rounding band (the model often writes "near $130,000" instead of
    the exact figure).
    """
    text = p.occupational_demand
    section = "occupational_demand"
    violations: list[EvalViolation] = []

    if not text or not p.opportunity_evidence:
        return violations

    # Find the selected occupation's actual values. opportunity_evidence is
    # filtered to the selected occupation in _assemble_proposal, so the first
    # entry is normally the right one; double-check by SOC if present.
    selected = None
    for occ in p.opportunity_evidence:
        if p.selected_soc_code and occ.soc_code == p.selected_soc_code:
            selected = occ
            break
    if selected is None and p.opportunity_evidence:
        selected = p.opportunity_evidence[0]
    if selected is None:
        return violations

    # ── Openings check ──────────────────────────────────────────────────
    if selected.annual_openings is not None:
        expected_openings = selected.annual_openings
        # Match "<number> annual openings" or "<number> openings" patterns.
        openings_pattern = re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d{3,})\s+(?:annual\s+|regional\s+|projected\s+)*openings\b",
            re.IGNORECASE,
        )
        for m in openings_pattern.finditer(text):
            cited = int(m.group(1).replace(",", ""))
            if cited != expected_openings:
                violations.append(
                    EvalViolation(
                        rule="occupational_demand_openings_mismatch",
                        section=section,
                        message=(
                            f"Cited {cited:,} openings, but the selected occupation "
                            f"({selected.title}, SOC {selected.soc_code}) has "
                            f"{expected_openings:,} annual openings in this region. "
                            f"Use the selected occupation's specific figure, not the "
                            f"aggregate or another occupation's data."
                        ),
                    )
                )

    # ── Wage check ──────────────────────────────────────────────────────
    if selected.annual_wage is not None:
        expected_wage = selected.annual_wage
        # Match dollar amounts. Tolerance: 5% rounding band, since narratives
        # often write "near $130,000" or "around $190,000" rather than exact.
        # Anything outside that band is flagged as a mismatch.
        dollar_pattern = re.compile(r"\$\s*(\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?")
        tolerance = max(expected_wage * 0.05, 1000)
        for m in dollar_pattern.finditer(text):
            cited = int(m.group(1).replace(",", ""))
            if abs(cited - expected_wage) > tolerance:
                violations.append(
                    EvalViolation(
                        rule="occupational_demand_wage_mismatch",
                        section=section,
                        message=(
                            f"Cited ${cited:,} as a wage figure, but the selected "
                            f"occupation ({selected.title}) has an annual wage of "
                            f"${expected_wage:,}. Use the selected occupation's "
                            f"specific figure, not the aggregate or another role's wage."
                        ),
                    )
                )

    return violations


def _check_curriculum_alignment(p: NarrativeProposal) -> list[EvalViolation]:
    violations: list[EvalViolation] = []
    text = p.curriculum_alignment
    section = "curriculum_alignment"

    if not text or not text.strip():
        violations.append(
            EvalViolation(rule="empty_section", section=section, message="Curriculum alignment is empty.")
        )
        return violations

    # Required: at least one specific department name
    dept_names = [d.department for d in p.curriculum_evidence]
    if dept_names and not any(dept.lower() in text.lower() for dept in dept_names):
        violations.append(
            EvalViolation(
                rule="missing_department_reference",
                section=section,
                message=(
                    f"Curriculum alignment does not name any of the curriculum-evidence departments "
                    f"({', '.join(dept_names[:3])})."
                ),
            )
        )

    # Required: at least one core skill name (if any are specified)
    if p.core_skills and not any(s.lower() in text.lower() for s in p.core_skills):
        violations.append(
            EvalViolation(
                rule="missing_skill_reference",
                section=section,
                message=(
                    f"Curriculum alignment does not name any of the core skills "
                    f"({', '.join(p.core_skills[:3])})."
                ),
            )
        )

    # Forbidden: economic figures
    violations.extend(_check_no_economic_figures_in(section, text))

    # Voice
    violations.extend(_check_voice(section, text))

    return violations


def _check_student_impact(p: NarrativeProposal) -> list[EvalViolation]:
    violations: list[EvalViolation] = []
    text = p.student_impact
    section = "student_impact"

    if not text or not text.strip():
        violations.append(
            EvalViolation(rule="empty_section", section=section, message="Student impact is empty.")
        )
        return violations

    # Required: at least one specific student count.
    # Acceptable counts: total_in_program, with_all_core_skills, dept_enrollment values.
    expected_counts: list[int] = []
    if p.student_evidence.total_in_program > 0:
        expected_counts.append(p.student_evidence.total_in_program)
    if p.student_evidence.with_all_core_skills > 0:
        expected_counts.append(p.student_evidence.with_all_core_skills)
    for d in p.swp_evidence.department_enrollments:
        if d.student_count > 0:
            expected_counts.append(d.student_count)

    if expected_counts:
        text_digits = _digit_sequences(text)
        # Match either exact digit sequence or comma-formatted version
        formatted_expected = {f"{n:,}" for n in expected_counts}
        unformatted_expected = {str(n) for n in expected_counts}
        all_acceptable = formatted_expected | unformatted_expected
        if not any(d in all_acceptable for d in text_digits):
            violations.append(
                EvalViolation(
                    rule="missing_student_count",
                    section=section,
                    message=(
                        f"Student impact contains no specific student count. Expected one of "
                        f"{sorted(expected_counts)[:3]}; found digits: {text_digits[:3] or 'none'}."
                    ),
                )
            )

    # Required: at least one department name
    dept_names = [d.department for d in p.curriculum_evidence]
    if dept_names and not any(dept.lower() in text.lower() for dept in dept_names):
        violations.append(
            EvalViolation(
                rule="missing_department_reference",
                section=section,
                message=(
                    f"Student impact does not name any of the curriculum-evidence departments "
                    f"({', '.join(dept_names[:3])})."
                ),
            )
        )

    # Forbidden: economic figures
    violations.extend(_check_no_economic_figures_in(section, text))

    # Forbidden: readiness evaluation language
    readiness_hits = _find_any_pattern(text, _READINESS_PATTERNS)
    if readiness_hits:
        violations.append(
            EvalViolation(
                rule="no_readiness_evaluation",
                section=section,
                message=(
                    f"Readiness-evaluation phrase(s) found: {', '.join(readiness_hits)}. "
                    f"State the composition of the pipeline; do not evaluate it."
                ),
            )
        )

    # Voice
    violations.extend(_check_voice(section, text))

    return violations


# ═══════════════════════════════════════════════════════════════════════════
# SWP evidence math integrity
# ═══════════════════════════════════════════════════════════════════════════


def _check_swp_evidence_math(p: NarrativeProposal) -> list[EvalViolation]:
    violations: list[EvalViolation] = []
    swp = p.swp_evidence

    # total_demand should equal sum of occupations.annual_openings (treating None as 0)
    expected_demand = sum(o.annual_openings or 0 for o in swp.occupations)
    if swp.total_demand != expected_demand:
        violations.append(
            EvalViolation(
                rule="swp_demand_math",
                section="swp_evidence",
                message=(
                    f"total_demand ({swp.total_demand}) does not equal "
                    f"sum of occupation annual_openings ({expected_demand})."
                ),
            )
        )

    # total_supply should equal sum of supply_estimates.annual_projected_supply
    expected_supply = sum(s.annual_projected_supply for s in swp.supply_estimates)
    # Allow small floating-point drift
    if abs(swp.total_supply - expected_supply) > 0.01:
        violations.append(
            EvalViolation(
                rule="swp_supply_math",
                section="swp_evidence",
                message=(
                    f"total_supply ({swp.total_supply:.2f}) does not equal "
                    f"sum of supply_estimates ({expected_supply:.2f})."
                ),
            )
        )

    # gap should equal total_demand - total_supply
    expected_gap = swp.total_demand - swp.total_supply
    if abs(swp.gap - expected_gap) > 0.01:
        violations.append(
            EvalViolation(
                rule="swp_gap_math",
                section="swp_evidence",
                message=(
                    f"gap ({swp.gap:.2f}) does not equal total_demand - total_supply "
                    f"({expected_gap:.2f})."
                ),
            )
        )

    return violations


# ═══════════════════════════════════════════════════════════════════════════
# Public entry point
# ═══════════════════════════════════════════════════════════════════════════


def evaluate_proposal(proposal: NarrativeProposal) -> EvalResult:
    """Run all deterministic eval checks against a proposal.

    Returns an EvalResult; never raises. Logs the summary; callers can
    inspect the returned object for full violation detail.
    """
    violations: list[EvalViolation] = []
    violations.extend(_check_executive_summary(proposal))
    violations.extend(_check_occupational_demand(proposal))
    violations.extend(_check_curriculum_alignment(proposal))
    violations.extend(_check_student_impact(proposal))
    violations.extend(_check_swp_evidence_math(proposal))

    result = EvalResult(violations=violations)

    if result.passed:
        logger.info(f"Proposal eval for {proposal.employer}: PASS")
    else:
        logger.warning(
            f"Proposal eval for {proposal.employer}: {result.violation_count} violation(s)"
        )
        for v in result.violations:
            logger.warning(f"  [{v.rule}] {v.section}: {v.message}")

    return result
