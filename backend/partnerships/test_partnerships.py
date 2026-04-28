"""Unit tests for partnerships pure helpers.

Targets the JSON parser that every LLM-based selection call depends on,
the narrative field parser that wraps it, and the deterministic
department-text builder used to construct LLM prompts. Each of these is
a brittle point — the LLM responses vary in surface form (code fences,
leading prose, trailing commentary) and the parser has to tolerate the
variance without corrupting the selection path.

Coverage:
  - _extract_json: plain objects, markdown code fences (with and without
    json hint), leading and trailing text, nested objects, braces in
    string literals, malformed input, empty strings
  - _parse_narrative_fields: well-formed four-section responses, missing
    sections (default to empty string), fence-wrapped responses
  - _build_dept_text: empty evidence, single and multiple departments,
    missing-skill reporting, alphabetical sorting of missing skills
"""

import pytest

from partnerships.evals import evaluate_proposal
from partnerships.filter import _extract_json
from partnerships.models import (
    DepartmentEnrollment,
    DepartmentEvidence,
    NarrativeProposal,
    OccupationEvidence,
    StudentEvidence,
    SupplyEstimate,
    SwpEvidence,
)
from partnerships.narrative import _build_dept_text, _parse_narrative_fields


def _make_minimal_good_proposal() -> NarrativeProposal:
    """A proposal that should pass every deterministic eval rule."""
    return NarrativeProposal(
        employer="Test Corp",
        sector="Tech",
        selected_occupation="Software Developers",
        selected_soc_code="15-1252",
        core_skills=["Programming", "Software Development", "Algorithms"],
        regions=["Bay"],
        executive_summary=(
            "Test Corp operates across the Bay COE region, with a hiring profile centered "
            "on software developer and engineering roles. The Computer Science department "
            "develops the programming and algorithms skills those roles require, and the "
            "Mathematics department reinforces the quantitative foundation. Students across "
            "these programs are completing coursework aligned with what Test Corp hires for."
        ),
        occupational_demand=(
            "Test Corp's Bay-region hiring centers on Software Developers (15-1252), with "
            "median annual wages near $190,000 and roughly 11,000 regional openings projected "
            "each year. The company's software scope generates a diverse set of competencies "
            "new hires are expected to bring on day one."
        ),
        curriculum_alignment=(
            "The Computer Science department develops programming, software development, and "
            "algorithms across 33 courses. The Mathematics department reinforces algorithmic "
            "thinking across 20 courses, deepening preparation in applied development."
        ),
        student_impact=(
            "The Computer Science department has 5,137 students enrolled in courses developing "
            "the relevant competencies, with 386 carrying all three core skills. The Mathematics "
            "department adds another concentration of students preparing for these roles."
        ),
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
            DepartmentEvidence(department="Mathematics", courses=[], aligned_skills=["Algorithms"]),
        ],
        student_evidence=StudentEvidence(total_in_program=5137, with_all_core_skills=386, top_students=[]),
        swp_evidence=SwpEvidence(
            occupations=[OccupationEvidence(title="Software Developers", soc_code="15-1252", annual_openings=11000)],
            supply_estimates=[SupplyEstimate(top_code="070700", top_title="CS", award_level="Cert", annual_projected_supply=28.0)],
            department_enrollments=[DepartmentEnrollment(department="Computer Science", student_count=5137)],
            total_demand=11000, total_supply=28.0, gap=10972.0, coe_region="Bay",
        ),
    )


class TestExtractJson:
    def test_plain_object(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_object_in_json_code_fence(self):
        raw = '```json\n{"a": 1, "b": 2}\n```'
        assert _extract_json(raw) == {"a": 1, "b": 2}

    def test_object_in_plain_code_fence(self):
        raw = '```\n{"a": 1}\n```'
        assert _extract_json(raw) == {"a": 1}

    def test_object_with_leading_text(self):
        # The LLM sometimes prefixes reasoning before the JSON.
        raw = 'Here is my answer:\n{"selected": "nurse"}'
        assert _extract_json(raw) == {"selected": "nurse"}

    def test_object_with_trailing_text(self):
        raw = '{"selected": "nurse"}\nThat is my choice.'
        assert _extract_json(raw) == {"selected": "nurse"}

    def test_nested_object(self):
        raw = '{"outer": {"inner": [1, 2, 3]}}'
        assert _extract_json(raw) == {"outer": {"inner": [1, 2, 3]}}

    def test_object_with_braces_in_strings(self):
        # Depth tracking must ignore braces inside string literals.
        raw = '{"template": "{{curly}}"}'
        assert _extract_json(raw) == {"template": "{{curly}}"}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            _extract_json("")

    def test_text_without_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            _extract_json("I cannot answer that question.")

    def test_malformed_json_raises(self):
        with pytest.raises(ValueError):
            _extract_json("{bad json without quotes}")


class TestParseNarrativeFields:
    def test_well_formed_four_section_response(self):
        raw = """{
            "executive_summary": "An integrative paragraph.",
            "occupational_demand": "A demand claim.",
            "curriculum_alignment": "An alignment claim.",
            "student_impact": "A pipeline claim."
        }"""
        result = _parse_narrative_fields(raw)
        assert result["executive_summary"] == "An integrative paragraph."
        assert result["occupational_demand"] == "A demand claim."
        assert result["curriculum_alignment"] == "An alignment claim."
        assert result["student_impact"] == "A pipeline claim."

    def test_missing_executive_summary_defaults_to_empty(self):
        raw = '{"occupational_demand": "d", "curriculum_alignment": "c", "student_impact": "s"}'
        result = _parse_narrative_fields(raw)
        assert result["executive_summary"] == ""
        assert result["occupational_demand"] == "d"

    def test_missing_all_sections_default_to_empty_strings(self):
        raw = '{}'
        result = _parse_narrative_fields(raw)
        assert result["executive_summary"] == ""
        assert result["occupational_demand"] == ""
        assert result["curriculum_alignment"] == ""
        assert result["student_impact"] == ""

    def test_wrapped_in_markdown_fence(self):
        raw = (
            '```json\n'
            '{"executive_summary": "e", "occupational_demand": "o", '
            '"curriculum_alignment": "c", "student_impact": "s"}\n'
            '```'
        )
        result = _parse_narrative_fields(raw)
        assert result["executive_summary"] == "e"
        assert result["student_impact"] == "s"


class TestBuildDeptText:
    def test_empty_evidence(self):
        result = _build_dept_text([], ["python"])
        # Header is always present so callers can diff against it.
        assert "DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:" in result

    def test_single_dept_no_missing_skills(self):
        evidence = [{
            "department": "Computer Science",
            "courses": [{"code": "CS 101"}, {"code": "CS 102"}],
            "aligned_skills": ["python", "algorithms"],
        }]
        result = _build_dept_text(evidence, ["python", "algorithms"])
        assert "Computer Science" in result
        assert "python" in result
        assert "algorithms" in result
        assert "2 courses" in result
        assert "Missing" not in result

    def test_missing_skills_reported(self):
        evidence = [{
            "department": "Computer Science",
            "courses": [{"code": "CS 101"}],
            "aligned_skills": ["python"],
        }]
        result = _build_dept_text(evidence, ["python", "kubernetes"])
        assert "Missing: kubernetes" in result

    def test_multiple_missing_skills_sorted(self):
        evidence = [{
            "department": "CS",
            "courses": [{"code": "CS 101"}],
            "aligned_skills": [],
        }]
        # Sorted alphabetically: docker, kubernetes, python
        result = _build_dept_text(evidence, ["python", "docker", "kubernetes"])
        assert "Missing: docker, kubernetes, python" in result

    def test_multiple_departments_each_listed(self):
        evidence = [
            {
                "department": "CS",
                "courses": [{"code": "CS 101"}],
                "aligned_skills": ["python"],
            },
            {
                "department": "Math",
                "courses": [{"code": "MATH 200"}],
                "aligned_skills": ["linear algebra"],
            },
        ]
        result = _build_dept_text(evidence, ["python", "linear algebra"])
        assert "CS" in result
        assert "Math" in result


class TestEvaluateProposal:
    """Coverage of the deterministic quality evals.

    Each test holds the rest of the proposal valid and mutates one section
    or field to trigger a single rule, so a failure points to the rule.
    """

    def test_clean_proposal_passes(self):
        result = evaluate_proposal(_make_minimal_good_proposal())
        assert result.passed, f"clean proposal raised: {[v.message for v in result.violations]}"

    def test_em_dash_in_any_section_flagged(self):
        p = _make_minimal_good_proposal()
        p.curriculum_alignment = (
            "The Computer Science department develops programming — algorithms, software development — "
            "across 33 courses. The Mathematics department reinforces algorithmic thinking."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_em_dashes" in rules

    def test_deficit_language_flagged(self):
        p = _make_minimal_good_proposal()
        p.curriculum_alignment = (
            "The Computer Science department develops programming and algorithms but the curriculum "
            "is missing software development. The Mathematics department reinforces algorithmic thinking."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_deficit_language" in rules

    def test_evaluative_superlative_flagged(self):
        p = _make_minimal_good_proposal()
        p.executive_summary = p.executive_summary.replace(
            "with a hiring profile centered",
            "compelling and uniquely positioned, with a hiring profile centered",
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_evaluative_superlatives" in rules

    def test_partnership_type_prescription_flagged(self):
        p = _make_minimal_good_proposal()
        p.executive_summary = p.executive_summary.replace(
            "Students across these programs are completing coursework aligned with what Test Corp hires for.",
            "An advisory board with Test Corp would formalize this alignment.",
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_type_prescription" in rules

    def test_economic_figure_in_executive_summary_flagged(self):
        p = _make_minimal_good_proposal()
        p.executive_summary = p.executive_summary.replace(
            "The Computer Science department",
            "Software Developers earn $190,000 annually. The Computer Science department",
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        # Both "no_econ_in_wrong_sections" (the $190,000) and
        # "no_specific_counts_in_exec" (the digits) should fire.
        assert "no_econ_in_wrong_sections" in rules

    def test_economic_figure_in_curriculum_alignment_flagged(self):
        p = _make_minimal_good_proposal()
        p.curriculum_alignment = (
            "The Computer Science department develops programming and algorithms across 33 courses, "
            "with graduates earning $190,000. The Mathematics department reinforces algorithmic thinking."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_econ_in_wrong_sections" in rules

    def test_missing_economic_figure_in_occupational_demand_flagged(self):
        p = _make_minimal_good_proposal()
        p.occupational_demand = (
            "Test Corp's Bay-region hiring centers on Software Developers (15-1252). "
            "The company's software scope generates a diverse set of competencies."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "missing_economic_figure" in rules

    def test_missing_coe_region_in_occupational_demand_flagged(self):
        p = _make_minimal_good_proposal()
        p.occupational_demand = (
            "Test Corp's hiring centers on Software Developers (15-1252), with median annual wages "
            "near $190,000 and roughly 11,000 regional openings projected each year. "
            "The company's software scope generates a diverse set of competencies."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "missing_coe_region" in rules

    def test_national_claim_in_occupational_demand_flagged(self):
        p = _make_minimal_good_proposal()
        p.occupational_demand = (
            "Test Corp's hiring in the Bay COE region centers on Software Developers (15-1252), "
            "with median annual wages near $190,000 and 11,000 openings projected each year nationally. "
            "The company's software scope generates a diverse set of competencies."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_national_claims" in rules

    def test_missing_student_count_in_student_impact_flagged(self):
        p = _make_minimal_good_proposal()
        p.student_impact = (
            "Students in the Computer Science department are building programming, software "
            "development, and algorithmic skills aligned with Test Corp's hiring profile."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "missing_student_count" in rules

    def test_readiness_evaluation_in_student_impact_flagged(self):
        p = _make_minimal_good_proposal()
        p.student_impact = (
            "5,137 students in the Computer Science department are well-prepared for Test Corp's "
            "software developer roles, ready to contribute on day one."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "no_readiness_evaluation" in rules

    def test_swp_demand_math_mismatch_flagged(self):
        p = _make_minimal_good_proposal()
        p.swp_evidence.total_demand = 99999  # doesn't match sum of occupations
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_demand_math" in rules

    def test_swp_gap_math_mismatch_flagged(self):
        p = _make_minimal_good_proposal()
        p.swp_evidence.gap = 0  # should be 11000 - 28 = 10972
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "swp_gap_math" in rules

    def test_executive_summary_too_short_flagged(self):
        p = _make_minimal_good_proposal()
        p.executive_summary = "Test Corp is in the Bay COE region with the Computer Science department aligned with what Test Corp hires for."
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "executive_summary_length" in rules

    def test_missing_department_in_curriculum_alignment_flagged(self):
        p = _make_minimal_good_proposal()
        p.curriculum_alignment = (
            "Several departments at the college develop the relevant skills, supporting the "
            "competencies Test Corp's roles require across multiple courses."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "missing_department_reference" in rules

    def test_aggregate_openings_in_occupational_demand_flagged(self):
        """The model citing the aggregate-demand total instead of the selected
        occupation's specific openings is a real failure mode the eval must catch."""
        p = _make_minimal_good_proposal()
        # opportunity_evidence has annual_openings=11000 for the selected occupation;
        # the swp_evidence aggregate sums to 11000 as well in the fixture, so we
        # need a different mismatch number — simulate the model citing a fabricated
        # or aggregate figure that doesn't match.
        p.occupational_demand = (
            "Test Corp's Bay-region hiring centers on Software Developers (15-1252), with "
            "median annual wages near $190,000 and 31,420 annual openings across the region. "
            "The company's scope generates a diverse set of competencies new hires bring."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "occupational_demand_openings_mismatch" in rules

    def test_wrong_wage_in_occupational_demand_flagged(self):
        p = _make_minimal_good_proposal()
        # Cite a wage well outside the 5%/$1k tolerance from the expected $190,000.
        p.occupational_demand = (
            "Test Corp's Bay-region hiring centers on Software Developers (15-1252), with "
            "median annual wages near $50,000 and 11,000 regional openings projected each year. "
            "The company's scope generates a diverse set of competencies new hires bring."
        )
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "occupational_demand_wage_mismatch" in rules

    def test_wage_within_rounding_tolerance_passes(self):
        """Rounded wage figures (e.g., 'near $190,000' for actual $190,500) should pass."""
        p = _make_minimal_good_proposal()
        # Tweak the actual wage slightly so the prose's $190,000 round is within 5%.
        p.opportunity_evidence[0].annual_wage = 190500
        # Prose still cites $190,000 — within tolerance.
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "occupational_demand_wage_mismatch" not in rules

    def test_correct_specific_openings_passes(self):
        """When the model cites the selected occupation's actual openings figure, no flag."""
        p = _make_minimal_good_proposal()
        # Default fixture cites 11,000 openings, expected_openings is 11000. Pass.
        result = evaluate_proposal(p)
        rules = {v.rule for v in result.violations}
        assert "occupational_demand_openings_mismatch" not in rules
