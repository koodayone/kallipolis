"""Unit tests for the partnership proposal data-integrity check.

The narrative is now produced by deterministic templates (see
``narrative_templates.py``); the LLM-drift checks that used to live
here have been retired along with the LLM. The only remaining
runtime eval is a structural check on the SwpEvidence row's totals.

Per-template behavior is tested in ``test_narrative_templates.py``.

Coverage:
  - evaluate_proposal: a clean proposal passes with zero violations
  - swp_demand_math: total_demand drift from sum of occupation
    annual_openings is flagged
  - swp_supply_math: total_supply drift from sum of supply_estimates
    annual_projected_supply is flagged
  - swp_gap_math: gap drift from (total_demand - total_supply) is
    flagged
  - tolerance: floating-point drift below 0.01 in supply totals does
    not fire the supply-math rule
"""

from partnerships.evals import evaluate_proposal
from partnerships.models import (
    DepartmentEnrollment,
    DepartmentEvidence,
    NarrativeProposal,
    OccupationEvidence,
    StudentEvidence,
    SupplyEstimate,
    SwpEvidence,
)


def _make_minimal_good_proposal() -> NarrativeProposal:
    """A proposal whose SwpEvidence row is internally consistent — totals
    match the underlying lists. Tests mutate one field to trigger a check."""
    return NarrativeProposal(
        employer="Test Corp",
        sector="Tech",
        selected_occupation="Software Developers",
        selected_soc_code="15-1252",
        core_skills=["Programming", "Software Development", "Algorithms"],
        regions=["Bay"],
        executive_summary="Test Corp operates a software company.",
        occupational_demand="Test Corp's core hiring centers on Software Developers.",
        curriculum_alignment="The departments below prepare students.",
        student_impact="Students are enrolled.",
        opportunity_evidence=[
            OccupationEvidence(
                title="Software Developers",
                soc_code="15-1252",
                annual_openings=11000,
                annual_wage=190000,
            ),
        ],
        curriculum_evidence=[
            DepartmentEvidence(department="Computer Science", courses=[], aligned_skills=["Programming"]),
        ],
        student_evidence=StudentEvidence(total_in_program=5137, with_all_core_skills=386, top_students=[]),
        swp_evidence=SwpEvidence(
            occupations=[
                OccupationEvidence(title="Software Developers", soc_code="15-1252", annual_openings=11000),
            ],
            supply_estimates=[
                SupplyEstimate(top_code="070700", top_title="CS", award_level="Cert", annual_projected_supply=28.0),
            ],
            department_enrollments=[DepartmentEnrollment(department="Computer Science", student_count=5137)],
            total_demand=11000, total_supply=28.0, gap=10972.0, coe_region="Bay",
        ),
    )


class TestEvaluateProposal:
    """The remaining runtime check: SwpEvidence math must be internally
    consistent. Drift between the totals and the underlying lists would
    indicate the supply-demand block was assembled inconsistently."""

    def test_clean_proposal_passes(self):
        result = evaluate_proposal(_make_minimal_good_proposal())
        assert result.passed, f"clean proposal raised: {[v.message for v in result.violations]}"

    def test_swp_demand_math_mismatch_flagged(self):
        p = _make_minimal_good_proposal()
        p.swp_evidence.total_demand = 99999  # doesn't match sum of occupations
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_demand_math" in rules

    def test_swp_supply_math_mismatch_flagged(self):
        p = _make_minimal_good_proposal()
        p.swp_evidence.total_supply = 99.0  # doesn't match sum of supply_estimates
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_supply_math" in rules

    def test_swp_gap_math_mismatch_flagged(self):
        p = _make_minimal_good_proposal()
        p.swp_evidence.gap = 0  # should be 11000 - 28 = 10972
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_gap_math" in rules

    def test_supply_within_floating_point_tolerance_passes(self):
        # 0.001 drift on a 28.0 sum is below the 0.01 tolerance threshold.
        p = _make_minimal_good_proposal()
        p.swp_evidence.total_supply = 28.001
        # Adjust gap to keep that check consistent.
        p.swp_evidence.gap = 11000 - 28.001
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_supply_math" not in rules
