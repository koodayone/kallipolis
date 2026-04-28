"""Canonical end-to-end fixture: Abbott Vascular at Foothill, SOC 51-9061.

This fixture is the canonical "what good looks like" gate for the
institutional-deference architectural commitment. It's deliberately
shaped around the reference case the architectural shift was named
against: a medical-device employer (Abbott Vascular, SWP "Advanced
Manufacturing") matched against a community college (Foothill) whose
only institutionally-aligned QC pathway is the aerospace NDT
apprenticeship sequence (Apprenticeship: Aerospace under TOP 095680).

The fixture builds a fully-specified `NarrativeProposal` using
hand-crafted prose that satisfies every existing eval rule plus the
four institutional-deference rules added in C8:

  - no_direct_mapping_overclaim
  - no_skills_as_pathway
  - missing_institutional_attribution
  - cross_industry_honesty

If a future change breaks any of these contracts, this fixture fails
loudly and surfaces the regression before it ships. The expected pass
state is: `evaluate_proposal(p).passed == True`.

The prose mirrors the live deployed output verified during C7/C8
(post-prompt-rewrite, post-eval-rule). It is not an LLM transcript;
it is a pinned reference whose every sentence has been checked against
the eval rules.
"""

from __future__ import annotations

import pytest

from partnerships.evals import evaluate_proposal
from partnerships.models import (
    CourseEvidence,
    DepartmentEnrollment,
    DepartmentEvidence,
    InstitutionalSources,
    NarrativeProposal,
    OccupationEvidence,
    StudentEvidence,
    SupplyEstimate,
    SwpEvidence,
)


def _make_abbott_vascular_proposal() -> NarrativeProposal:
    """The canonical institutional-deference reference proposal.

    Every link of the empirical chain is named: SOC 51-9061, CIP 15.0702,
    TOP 095680, Apprenticeship: Aerospace department, COE Bay region,
    workforce gap of 1,680. The prose uses transferability vocabulary
    ('transferable foundation,' 'methods transfer across manufacturing
    industries,' 'applied here in a medical device context') because
    the employer's SWP sector ('Advanced Manufacturing') and the
    department's PCAH sector context (the same — both manufacturing-
    family, but different sub-flavor: aerospace QC vs medical device
    QC) generate the partial-alignment case principle 4 names.

    Note on cross_industry_honesty rule activation: The eval rule
    activates only when the in-repo PCAH TOP6 sector for via_top
    differs from proposal.sector. TOP 095680's PCAH sector is
    'Advanced Manufacturing' — same as Abbott Vascular's. The rule
    is therefore dormant for this fixture, which is correct: the
    institutional taxonomy treats both as Advanced Manufacturing.
    The fixture's prose still uses transferability vocabulary
    because the lived-experience industry contexts (aerospace
    apprenticeship vs medical device manufacturing) differ; the eval
    rule is conservative — it only fires when the institutional
    taxonomy itself flags a sector mismatch.
    """
    return NarrativeProposal(
        employer="Abbott Vascular",
        sector="Advanced Manufacturing",
        selected_occupation="Inspectors, Testers, Sorters, Samplers, and Weighers",
        selected_soc_code="51-9061",
        core_skills=["Quality Control", "Safety Protocols", "Manufacturing"],
        regions=["Inland Empire and Desert"],
        executive_summary=(
            "Abbott Vascular develops cardiovascular medical device technologies, "
            "serving healthcare professionals managing heart health across the "
            "Inland Empire and Desert region. In the Bay COE region, demand for "
            "Inspectors, Testers, Sorters, Samplers, and Weighers is substantial, "
            "and labor market analysis indicates an unmet workforce gap of 1,680 "
            "on an annual basis. Foothill College's Apprenticeship: Aerospace "
            "department, organized under TOP 095680, develops quality control and "
            "safety protocols relevant to this occupation. The BLS/NCES crosswalk "
            "routes this occupation to CIP 15.0702, and the methods developed in "
            "this aerospace-rooted program transfer across manufacturing "
            "industries, making this a transferable foundation rather than a "
            "turnkey match for Abbott's medical device context."
        ),
        occupational_demand=(
            "Abbott Vascular's Bay-region hiring centers on Inspectors, Testers, "
            "Sorters, Samplers, and Weighers (51-9061), with median annual wages "
            "near $56,770 and roughly 1,680 regional annual openings projected by "
            "Centers of Excellence regional data each year. The company's medical "
            "device scope generates a diverse set of inspection competencies new "
            "hires are expected to bring on day one."
        ),
        curriculum_alignment=(
            "The institutional crosswalk identifies Foothill College's "
            "Apprenticeship: Aerospace department as aligned to SOC 51-9061 "
            "through TOP 095680, tracing the connection via the Chancellor's "
            "Office TOP-CIP crosswalk and the BLS/NCES CIP-SOC crosswalk. Across "
            "12 aligned courses, the program develops quality control and safety "
            "protocols, two of the three core skills this occupation requires. "
            "Coverage of manufacturing could be strengthened, representing an "
            "opportunity to deepen preparation within an applied medical device "
            "manufacturing context."
        ),
        student_impact=(
            "The Apprenticeship: Aerospace department reports a department-level "
            "enrollment of 25 students whose academic pathway aligns with this "
            "occupation. This pipeline reflects the institutional curriculum "
            "currently feeding the SOC 51-9061 occupation's pathway at Foothill."
        ),
        opportunity_evidence=[
            OccupationEvidence(
                title="Inspectors, Testers, Sorters, Samplers, and Weighers",
                soc_code="51-9061",
                annual_wage=56770,
                annual_openings=1680,
                cip_codes=["15.0702"],
            ),
        ],
        curriculum_evidence=[
            DepartmentEvidence(
                department="Apprenticeship: Aerospace",
                courses=[
                    CourseEvidence(
                        code=f"AATA10{i}{suffix}",
                        name=f"Sample NDT Course {i}{suffix}",
                        description="",
                        learning_outcomes=[],
                        skills=[],
                        top_code="095680",
                    )
                    for i, suffix in [
                        (1, "A"), (1, "B"), (2, "A"), (2, "B"),
                        (3, "A"), (3, "B"), (4, "A"), (4, "B"),
                        (5, "A"), (5, "B"), (5, "C"), (5, "R"),
                    ]
                ],
                aligned_skills=["Quality Control", "Safety Protocols"],
                via_top=["095680"],
                via_cip=["15.0702"],
            ),
        ],
        student_evidence=StudentEvidence(
            total_in_program=25,
            with_all_core_skills=0,
            top_students=[],
        ),
        swp_evidence=SwpEvidence(
            occupations=[
                OccupationEvidence(
                    title="Inspectors, Testers, Sorters, Samplers, and Weighers",
                    soc_code="51-9061",
                    annual_wage=56770,
                    annual_openings=1680,
                    cip_codes=["15.0702"],
                ),
            ],
            supply_estimates=[],
            department_enrollments=[
                DepartmentEnrollment(
                    department="Apprenticeship: Aerospace",
                    student_count=25,
                ),
            ],
            total_demand=1680,
            total_supply=0.0,
            gap=1680.0,
            coe_region="Bay",
            sources=InstitutionalSources(
                coe_region="Bay",
                coe_region_display="Bay Area",
            ),
        ),
    )


class TestAbbottVascularCanonicalFixture:
    """Canonical CI gate for institutional-deference. When this fixture
    fails, the architectural commitment has regressed somewhere."""

    def test_passes_every_eval_rule(self):
        """The fixture must pass every existing and new eval rule. A
        violation here is a regression in the prose layer or a
        regression in the eval rules — either way, fix the regression
        before shipping."""
        proposal = _make_abbott_vascular_proposal()
        result = evaluate_proposal(proposal)
        if not result.passed:
            violations_summary = "\n".join(
                f"  [{v.section}] {v.rule}: {v.message}"
                for v in result.violations
            )
            pytest.fail(
                f"Canonical Abbott Vascular fixture failed {len(result.violations)} "
                f"eval rule(s):\n{violations_summary}"
            )

    def test_carries_institutional_chain_through_data_shape(self):
        """The fixture must carry every institutional source forward in
        its structured fields — the atlas rendering and the eval rules
        depend on these being populated."""
        proposal = _make_abbott_vascular_proposal()

        # SwpEvidence.sources block populated.
        sources = proposal.swp_evidence.sources
        assert sources.coe_region == "Bay"
        assert "Centers of Excellence" in sources.coe_demand_publication
        assert "Chancellor's Office" in sources.top_cip_crosswalk_source
        assert "BLS" in sources.cip_soc_crosswalk_source or "NCES" in sources.cip_soc_crosswalk_source

        # Selected occupation's CIP codes populated.
        assert proposal.swp_evidence.occupations[0].cip_codes == ["15.0702"]
        assert proposal.opportunity_evidence[0].cip_codes == ["15.0702"]

        # Department-level via_top + via_cip populated.
        dept = proposal.curriculum_evidence[0]
        assert dept.via_top == ["095680"]
        assert dept.via_cip == ["15.0702"]

        # Per-course top_code populated.
        assert all(c.top_code == "095680" for c in dept.courses)

    def test_executive_summary_walks_chain(self):
        """The executive summary must visibly walk the empirical chain:
        TOP code, CIP code, named source, gap figure, transferability
        vocabulary."""
        proposal = _make_abbott_vascular_proposal()
        text = proposal.executive_summary

        assert "TOP 095680" in text
        assert "CIP 15.0702" in text
        assert "BLS/NCES" in text
        assert "1,680" in text  # gap figure
        assert "transferable foundation" in text or "transfer across" in text

    def test_curriculum_alignment_opens_with_institutional_voice(self):
        """The curriculum_alignment section's first sentence must
        attribute the pathway to the institutional crosswalk —
        not to skills, not to LLM judgment."""
        proposal = _make_abbott_vascular_proposal()
        first_sentence = proposal.curriculum_alignment.split(".")[0]

        # The opening must name the institutional source.
        assert "institutional crosswalk" in first_sentence.lower()
        # And name the pathway by code.
        assert "095680" in first_sentence or "TOP 095680" in proposal.curriculum_alignment
        assert "51-9061" in first_sentence or "51-9061" in proposal.curriculum_alignment
