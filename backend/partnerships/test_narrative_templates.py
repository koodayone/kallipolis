"""Foundation tests for the deterministic narrative templates.

These tests are the contract on every formatting decision the
institutional voice depends on. Each test pins down a specific
behavior. A failing test means a stylistic decision changed. The PR
diff is the explicit consent to that change — these are not flaky
like the LLM versions; deterministic output means a regression is a
real regression.

Coverage:
  - fmt_count: zero/one/many pluralization, thousands separator, custom
    irregular plurals
  - fmt_have / fmt_are: verb-agreement helpers for singular vs plural
    count subjects
  - fmt_wage: dollar-sign formatting and the unreported-fallback string
  - fmt_openings: singular/plural openings with the unreported fallback
  - fmt_demand_clause: composes the wage + openings noun phrase, with
    each missing-figure case
  - _normalize_skill: lowercases skills with the all-caps acronym
    carve-out (HVAC, OSHA, HACCP, EHR, BLS)
  - fmt_skills_list: empty / one / two / three+ items with Oxford comma
    and acronym preservation
  - build_executive_summary: full happy-path snapshot, singular-student
    pipeline verb agreement, sector and workforce fallbacks for
    un-characterized employers
  - build_occupational_demand: full happy-path snapshot, missing-wage
    case, no-core-skills honest fallback
  - build_curriculum_alignment: plural and singular department forms
  - build_student_impact: plural and singular student forms
  - build_narrative: composes all four sections, deterministic across
    repeated calls
"""

import pytest

from partnerships.narrative_templates import (
    _normalize_skill,
    build_curriculum_alignment,
    build_executive_summary,
    build_narrative,
    build_occupational_demand,
    build_student_impact,
    fmt_count,
    fmt_demand_clause,
    fmt_have,
    fmt_openings,
    fmt_skills_list,
    fmt_wage,
)


# ═══════════════════════════════════════════════════════════════════════════
# Formatting primitives
# ═══════════════════════════════════════════════════════════════════════════


class TestFmtCount:
    def test_zero_uses_plural(self):
        assert fmt_count(0, "student") == "0 students"

    def test_one_uses_singular(self):
        assert fmt_count(1, "student") == "1 student"

    def test_many_uses_thousands_separator_and_plural(self):
        assert fmt_count(13038, "student") == "13,038 students"

    def test_irregular_plural_via_explicit_arg(self):
        assert fmt_count(2, "child", plural="children") == "2 children"
        assert fmt_count(1, "child", plural="children") == "1 child"

    def test_course_pluralizes_correctly(self):
        assert fmt_count(354, "course") == "354 courses"
        assert fmt_count(1, "course") == "1 course"


class TestFmtVerb:
    def test_have_for_plural_subject(self):
        assert fmt_have(0) == "have"
        assert fmt_have(2) == "have"
        assert fmt_have(13038) == "have"

    def test_has_for_singular_subject(self):
        assert fmt_have(1) == "has"


class TestFmtWage:
    def test_real_figure_renders_with_dollar_and_separator(self):
        assert fmt_wage(99490) == "a median annual wage of $99,490"
        assert fmt_wage(58610) == "a median annual wage of $58,610"

    def test_missing_falls_back_to_unreported(self):
        assert fmt_wage(None) == "unreported median annual wage"

    def test_float_input_truncates_to_int(self):
        assert fmt_wage(99490.5) == "a median annual wage of $99,490"


class TestFmtOpenings:
    def test_plural_typical(self):
        assert fmt_openings(1470) == "1,470 annual openings"

    def test_singular_carries_grammar(self):
        assert fmt_openings(1) == "1 annual opening"

    def test_zero_uses_plural(self):
        assert fmt_openings(0) == "0 annual openings"

    def test_missing_falls_back_to_unreported(self):
        assert fmt_openings(None) == "unreported annual openings"


class TestFmtDemandClause:
    def test_both_present(self):
        assert fmt_demand_clause(99490, 1470) == (
            "an occupation with a median annual wage of $99,490 "
            "and 1,470 annual openings"
        )

    def test_wage_missing_openings_present(self):
        assert fmt_demand_clause(None, 1470) == (
            "an occupation with 1,470 annual openings"
        )

    def test_wage_present_openings_missing(self):
        assert fmt_demand_clause(99490, None) == (
            "an occupation with a median annual wage of $99,490"
        )

    def test_both_missing_collapses_cleanly(self):
        assert fmt_demand_clause(None, None) == "an occupation"


class TestNormalizeSkill:
    def test_titlecase_lowercased(self):
        # "Public Speaking" → "public speaking" per institutional style
        assert _normalize_skill("Public Speaking") == "public speaking"
        assert _normalize_skill("Instructional Design") == "instructional design"

    def test_acronym_preserved(self):
        # All-caps multi-letter words are recognized as acronyms
        assert _normalize_skill("HVAC") == "HVAC"
        assert _normalize_skill("OSHA Compliance") == "OSHA compliance"
        assert _normalize_skill("HACCP") == "HACCP"

    def test_single_letter_lowercased(self):
        # Single-letter words are not acronyms; lowercase them
        assert _normalize_skill("A B Testing") == "a b testing"

    def test_already_lowercase_unchanged(self):
        assert _normalize_skill("food safety") == "food safety"


class TestFmtSkillsList:
    def test_empty_list(self):
        assert fmt_skills_list([]) == ""

    def test_single_skill_normalized(self):
        assert fmt_skills_list(["Public Speaking"]) == "public speaking"

    def test_two_skills_no_oxford_comma(self):
        assert fmt_skills_list(["Public Speaking", "Assessment"]) == (
            "public speaking and assessment"
        )

    def test_three_skills_with_oxford_comma(self):
        assert fmt_skills_list(
            ["Public Speaking", "Instructional Design", "Assessment"]
        ) == "public speaking, instructional design, and assessment"

    def test_acronym_preserved_in_list(self):
        assert fmt_skills_list(["HVAC", "Equipment Maintenance"]) == (
            "HVAC and equipment maintenance"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Section builders
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildExecutiveSummary:
    def test_full_happy_path_locks_exact_prose(self):
        # The Bellarmine × Foothill scenario as it appears in production.
        # This snapshot is the contract on the executive-summary shape.
        result = build_executive_summary(
            employer_name="Bellarmine College Preparatory",
            operations_summary=(
                "operates an all-boys Jesuit college-preparatory high "
                "school in San Jose serving approximately 1,600 students"
            ),
            sector_display="Education and Human Development",
            college="Foothill College",
            soc_code="25-2031",
            total_aligned_courses=354,
            total_in_aligned_departments=13038,
        )
        assert result == (
            "Bellarmine College Preparatory operates an all-boys Jesuit "
            "college-preparatory high school in San Jose serving "
            "approximately 1,600 students. "
            "Foothill College can partner with Bellarmine College Preparatory "
            "to fulfill the employer's hiring needs for this role by leveraging "
            "the college's institutional assets. "
            "The college offers 354 courses with TOP codes that map to "
            "SOC 25-2031, the target occupation for this partnership. "
            "13,038 students have taken courses in the departments offering "
            "these courses, indicating a talent pool that can be sourced to "
            "fulfill labor market demand."
        )

    def test_singular_student_pipeline_uses_has(self):
        # The "1 student has taken courses" verb-agreement edge.
        result = build_executive_summary(
            employer_name="Smallville Co",
            operations_summary="manufactures widgets in Smallville",
            sector_display="Advanced Manufacturing",
            college="Smallville Community College",
            soc_code="51-9061",
            total_aligned_courses=1,
            total_in_aligned_departments=1,
        )
        # Pluralization: "1 course", "1 student", "1 student has taken"
        assert "1 course with TOP codes" in result
        assert "1 student has taken courses" in result
        assert "students have" not in result

    def test_uncharacterized_employer_falls_back_to_sector(self):
        # When operations_summary is empty (employer hasn't been through
        # employers.characterize yet), ES.1 falls back to a sector-only
        # structural sentence rather than producing an awkward
        # "{name}." with nothing else.
        result = build_executive_summary(
            employer_name="Mystery Inc",
            operations_summary="",
            sector_display="Health",
            college="Foothill College",
            soc_code="29-1141",
            total_aligned_courses=10,
            total_in_aligned_departments=200,
        )
        assert result.startswith("Mystery Inc operates in the Health sector.")

    def test_uncharacterized_no_sector_falls_back_to_workforce(self):
        # No operations_summary AND no sector — final fallback so the
        # sentence still composes.
        result = build_executive_summary(
            employer_name="Mystery Inc",
            operations_summary="",
            sector_display="",
            college="Foothill College",
            soc_code="29-1141",
            total_aligned_courses=10,
            total_in_aligned_departments=200,
        )
        assert result.startswith("Mystery Inc operates in the workforce.")


class TestBuildOccupationalDemand:
    def test_full_happy_path(self):
        result = build_occupational_demand(
            employer_name="Bellarmine College Preparatory",
            soc_code="25-2031",
            soc_title="Secondary School Teachers, Except Special and Career/Technical Education",
            annual_wage=99490,
            annual_openings=1470,
            coe_region_display="Bay Area",
            core_skills=["Public Speaking", "Instructional Design", "Assessment"],
        )
        assert result == (
            "Bellarmine College Preparatory's core hiring centers on "
            "Secondary School Teachers, Except Special and Career/Technical "
            "Education (SOC 25-2031), an occupation with a median annual "
            "wage of $99,490 and 1,470 annual openings in the Bay Area "
            "region according to Centers of Excellence projections. "
            "Core skills for this role include public speaking, "
            "instructional design, and assessment."
        )

    def test_missing_wage_omits_wage_clause(self):
        result = build_occupational_demand(
            employer_name="Some Co",
            soc_code="29-1141",
            soc_title="Registered Nurses",
            annual_wage=None,
            annual_openings=2400,
            coe_region_display="Far North",
            core_skills=["Patient Assessment"],
        )
        # No wage clause but openings still cited
        assert "$" not in result
        assert "2,400 annual openings" in result
        assert "in the Far North region" in result

    def test_no_core_skills_uses_honest_fallback(self):
        result = build_occupational_demand(
            employer_name="Some Co",
            soc_code="11-9121",
            soc_title="Natural Sciences Managers",
            annual_wage=111440,
            annual_openings=10,
            coe_region_display="Far North",
            core_skills=[],
        )
        assert "Core skills for this role are not surfaced" in result


class TestBuildCurriculumAlignment:
    def test_multiple_departments_uses_plural_form(self):
        result = build_curriculum_alignment(
            employer_name="Bellarmine College Preparatory",
            soc_code="25-2031",
            soc_title="Secondary School Teachers, Except Special and Career/Technical Education",
            n_departments=31,
        )
        assert result == (
            "According to the SOC-to-TOP institutional crosswalk maintained "
            "by the California Chancellor's Office, the departments below "
            "prepare students for SOC 25-2031. "
            "These departments develop the core competencies required to "
            "perform the role of Secondary School Teachers, Except Special "
            "and Career/Technical Education at Bellarmine College Preparatory."
        )

    def test_single_department_uses_singular_form(self):
        result = build_curriculum_alignment(
            employer_name="Acme Co",
            soc_code="51-9061",
            soc_title="Inspectors",
            n_departments=1,
        )
        assert "the department below prepares students" in result
        assert "This department develops the core competencies" in result
        assert "departments below" not in result
        assert "These departments develop" not in result


class TestBuildStudentImpact:
    def test_plural_students_uses_are(self):
        result = build_student_impact(
            soc_code="25-2031",
            total_in_aligned_departments=13038,
        )
        assert result == (
            "13,038 students are enrolled in the departments containing "
            "TOP codes that align with SOC 25-2031. "
            "Shown below are students that are most strongly prepared with "
            "the coursework included in the TOP-SOC crosswalk."
        )

    def test_singular_student_uses_is(self):
        result = build_student_impact(
            soc_code="29-1141",
            total_in_aligned_departments=1,
        )
        assert result.startswith("1 student is enrolled")
        assert "students are" not in result.split(".")[0]


# ═══════════════════════════════════════════════════════════════════════════
# Composed narrative
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildNarrative:
    def test_returns_all_four_sections(self):
        result = build_narrative(
            employer_name="Test Co",
            operations_summary="operates a test facility in Testville",
            sector_display="Testing",
            college="Test College",
            soc_code="00-0000",
            soc_title="Testers",
            annual_wage=50000,
            annual_openings=100,
            coe_region_display="Testland",
            core_skills=["Quality Control"],
            total_aligned_courses=5,
            total_in_aligned_departments=50,
            n_departments=2,
        )
        assert set(result.keys()) == {
            "executive_summary",
            "occupational_demand",
            "curriculum_alignment",
            "student_impact",
        }
        # Each section is a non-empty composed string
        for section, text in result.items():
            assert isinstance(text, str)
            assert len(text) > 0

    def test_deterministic_across_runs(self):
        # Same inputs always yield byte-identical output. This is the
        # property the architecture is built on.
        kwargs = dict(
            employer_name="Test Co",
            operations_summary="operates a test facility in Testville",
            sector_display="Testing",
            college="Test College",
            soc_code="00-0000",
            soc_title="Testers",
            annual_wage=50000,
            annual_openings=100,
            coe_region_display="Testland",
            core_skills=["Quality Control"],
            total_aligned_courses=5,
            total_in_aligned_departments=50,
            n_departments=2,
        )
        first = build_narrative(**kwargs)
        for _ in range(5):
            assert build_narrative(**kwargs) == first
