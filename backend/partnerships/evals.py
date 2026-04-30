"""Data-integrity checks on the assembled partnership proposal.

Up through commit ``8ce84c1`` this module was a long catalog of
LLM-drift mitigations: deficit-language patterns, superlative bans,
type-prescription detectors, em-dash hunters, readiness over-claim
patterns, direct-mapping over-claim patterns, and so on. All of those
existed to catch ways the LLM-authored narrative could violate the
institutional voice. They were retired when the narrative became
fully deterministic — see ``partnerships.narrative_templates``. A
template that doesn't write em dashes can't fail a "no em dash"
check, and keeping the check around is dead weight.

What remains: a single fast structural-integrity check against the
``SwpEvidence`` block, which is built from independent Cypher queries
+ CSV reads. If the totals on the SwpEvidence row drift from the
underlying lists, that's a real bug worth catching — it'd indicate
the supply-demand block was assembled inconsistently. The check is
non-blocking and runs after assembly; a failing check logs but does
not throw, so a coordinator never sees a partial proposal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from partnerships.models import NarrativeProposal

logger = logging.getLogger(__name__)


@dataclass
class EvalViolation:
    rule: str
    section: str
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


def _check_swp_evidence_math(p: NarrativeProposal) -> list[EvalViolation]:
    """Verify that the SwpEvidence row's totals match the underlying lists.

    The block is assembled in ``_assemble_swp_evidence`` from independent
    Cypher queries and the regional COE supply CSV, so the totals are
    derived data — drift between the totals and the lists would mean
    one of the queries returned a different result than the rolled-up
    figure expected.
    """
    violations: list[EvalViolation] = []
    swp = p.swp_evidence

    expected_demand = sum(o.annual_openings or 0 for o in swp.occupations)
    if swp.total_demand != expected_demand:
        violations.append(
            EvalViolation(
                rule="swp_demand_math",
                section="swp_evidence",
                message=(
                    f"total_demand ({swp.total_demand}) does not equal sum of "
                    f"occupation annual_openings ({expected_demand})."
                ),
            )
        )

    expected_supply = sum(s.annual_projected_supply for s in swp.supply_estimates)
    if abs(swp.total_supply - expected_supply) > 0.01:
        violations.append(
            EvalViolation(
                rule="swp_supply_math",
                section="swp_evidence",
                message=(
                    f"total_supply ({swp.total_supply:.2f}) does not equal sum of "
                    f"supply_estimates ({expected_supply:.2f})."
                ),
            )
        )

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


def evaluate_proposal(proposal: NarrativeProposal) -> EvalResult:
    """Run data-integrity checks on a proposal. Non-blocking.

    Logs PASS or the violation count + each rule. Returns the result
    object; callers can surface violations inline if desired.
    """
    violations = _check_swp_evidence_math(proposal)
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
