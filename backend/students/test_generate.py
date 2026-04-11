"""Unit tests for students.generate — synthetic student population generator.

The generator is the largest pure-logic surface in the students feature.
It takes an enriched course catalog plus DataMart TOP4 calibration and
produces a deterministic, seeded population of synthetic students whose
enrollments and grade distributions are calibrated against real
institutional data. These tests exercise the generator without touching
Neo4j, the MCF directory, or any calibration file on disk — calibration
loaders and prefix-map loaders are monkeypatched to hermetic fixtures,
and the Neo4j loader is exercised only through _derive_student_fields,
the pure helper that computes gpa / primary_focus / courses_completed
directly from in-memory state.

Coverage:
  - _parse_units string shapes: decimals, ranges, unit suffixes, blanks
  - _course_prefix letter-prefix extraction with and without spaces
  - _resolve_prefix alias map and "ENGL C" concurrent-variant rule
  - _build_term_sequence ordering and absence of Summer terms
  - generate_students determinism under a fixed seed with injected calibration
  - generate_students assigns the declared primary_top4 to every student
  - generate_students only emits grades from the TOP4 distribution it was given
  - Start cohort spread: students begin in multiple academic years
  - _derive_student_fields computes gpa, primary_focus, courses_completed
    from the in-memory GeneratedStudent without any Neo4j round-trip
"""

from __future__ import annotations

from typing import Dict, List

import pytest

from students import generate as gen
from students.generate import (
    Enrollment,
    GeneratedStudent,
    _build_term_sequence,
    _course_prefix,
    _derive_student_fields,
    _parse_units,
    _resolve_prefix,
    generate_students,
)


# ── Pure-helper tests ──────────────────────────────────────────────────────────


class TestParseUnits:
    def test_returns_zero_for_empty_string(self):
        assert _parse_units("") == 0.0

    def test_returns_zero_for_non_numeric_string(self):
        assert _parse_units("TBA") == 0.0

    def test_parses_integer_unit_count(self):
        assert _parse_units("3") == 3.0

    def test_parses_decimal_unit_count(self):
        assert _parse_units("4.5") == 4.5

    def test_averages_range_expressed_with_hyphen(self):
        # "1-2" → (1 + 2) / 2 = 1.5
        assert _parse_units("1-2") == 1.5

    def test_parses_leading_number_when_suffixed_with_unit_label(self):
        assert _parse_units("3unit(s)") == 3.0


class TestCoursePrefix:
    def test_extracts_letter_prefix_from_code_with_space(self):
        assert _course_prefix("CS 1A") == "CS"

    def test_extracts_multi_word_prefix_with_internal_space(self):
        assert _course_prefix("C S 1A") == "C S"

    def test_returns_empty_string_when_no_letter_prefix(self):
        assert _course_prefix("123") == ""


class TestResolvePrefix:
    def test_returns_alias_when_prefix_is_in_alias_table(self):
        # "CS" is aliased to "C S" in PREFIX_ALIASES
        assert _resolve_prefix("CS", {"C S": "0701"}) == "C S"

    def test_strips_concurrent_enrollment_suffix_when_base_is_mapped(self):
        # "ENGL C" is a concurrent-enrollment variant of "ENGL"; when the
        # base "ENGL" is in the prefix map (and the suffixed form is not),
        # the suffix is stripped.
        prefix_map = {"ENGL": "1501"}
        assert _resolve_prefix("ENGL C", prefix_map) == "ENGL"

    def test_does_not_strip_trailing_c_without_a_space_boundary(self):
        # "AGTC" must not be mistaken for "AGT C" — the suffix rule requires
        # an explicit trailing space before the C.
        prefix_map = {"AGT": "0102"}
        assert _resolve_prefix("AGTC", prefix_map) == "AGTC"

    def test_returns_prefix_unchanged_when_no_rule_applies(self):
        assert _resolve_prefix("BIOL", {"BIOL": "0401"}) == "BIOL"


class TestBuildTermSequence:
    def test_emits_three_terms_per_academic_year(self):
        terms = _build_term_sequence()
        # ACADEMIC_YEARS has 3 years × 3 terms per year = 9 terms
        assert len(terms) == 9

    def test_contains_no_summer_terms(self):
        # Summer terms were dead code in the old sequence — the season
        # weight existed but the term was never emitted. The fix removes
        # Summer from START_TERM_WEIGHTS and from the sequence entirely.
        terms = _build_term_sequence()
        assert all("Summer" not in t for t in terms)

    def test_starts_with_fall_of_first_academic_year(self):
        terms = _build_term_sequence()
        assert terms[0].endswith("Fall")


# ── Generator tests (fixture-based) ───────────────────────────────────────────


def _fake_top4_calibration() -> dict:
    """Two TOP4 codes with distinct grade distributions.

    0701 (Information Technology) is an A-heavy distribution.
    0401 (Biological Sciences) is a B-heavy distribution.
    The two distributions do not share any weight, so the test can assert
    that generated grades only come from the calibrated letters.
    """
    return {
        "college_name": "TestCollege",
        "total_enrollments": 1000,
        "top4_codes": {
            "0701": {
                "name": "Information Technology",
                "enrollment": 600,
                "grades": {"A": 0.6, "B": 0.3, "W": 0.1},
            },
            "0401": {
                "name": "Biological Sciences",
                "enrollment": 400,
                "grades": {"B": 0.6, "C": 0.3, "W": 0.1},
            },
        },
    }


def _fake_courses() -> List[dict]:
    """Enough catalog breadth to keep the DEPT_CAP/unit-cap loops happy."""
    courses: List[dict] = []
    # IT (TOP4 0701, prefix CS, department "Computer Science")
    for i in range(1, 11):
        courses.append({
            "code": f"CS {i}",
            "name": f"CS course {i}",
            "department": "Computer Science",
            "units": "3",
            "grading": "Letter",
        })
    # Biology (TOP4 0401, prefix BIOL, department "Biology")
    for i in range(1, 11):
        courses.append({
            "code": f"BIOL {i}",
            "name": f"Biology course {i}",
            "department": "Biology",
            "units": "3",
            "grading": "Letter",
        })
    return courses


@pytest.fixture
def injected_calibration(monkeypatch):
    """Inject a hermetic calibration + prefix map so generate_students
    never touches the filesystem."""
    monkeypatch.setattr(
        gen, "_load_top4_calibration", lambda college_key: _fake_top4_calibration()
    )
    monkeypatch.setattr(
        gen,
        "_load_calibration",
        lambda college_key: {"ft_ratio": 0.5, "retention_rate": 0.8, "enrollment": 50},
    )
    monkeypatch.setattr(
        gen,
        "_load_college_prefix_map",
        lambda college_key: {"CS": "0701", "BIOL": "0401"},
    )


class TestGenerateStudents:
    def test_produces_a_nonempty_population_under_a_fixed_seed(self, injected_calibration):
        students, stats = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=30,
            seed=42,
        )
        assert stats.students_generated > 0
        assert stats.enrollments_created > 0
        assert len(students) == stats.students_generated

    def test_is_deterministic_under_the_same_seed(self, injected_calibration):
        s1, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=20,
            seed=7,
        )
        s2, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=20,
            seed=7,
        )
        assert [st.uuid for st in s1] == [st.uuid for st in s2]
        assert [len(st.enrollments) for st in s1] == [len(st.enrollments) for st in s2]

    def test_assigns_every_student_a_valid_primary_top4(self, injected_calibration):
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=40,
            seed=1,
        )
        assert all(st.primary_top4 in {"0701", "0401"} for st in students)

    def test_grades_come_only_from_calibrated_distributions(self, injected_calibration):
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=40,
            seed=3,
        )
        # Union of grade keys across both fake TOP4 distributions
        allowed = {"A", "B", "C", "W"}
        observed = {
            e.grade
            for st in students
            for e in st.enrollments
        }
        assert observed.issubset(allowed)

    def test_spreads_start_cohorts_across_multiple_academic_years(self, injected_calibration):
        # The old "first matching term" lookup pinned every student to
        # the 2022 cohort. The fix builds weighted start candidates across
        # the full term sequence, so a population should include starters
        # from multiple years.
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=80,
            seed=5,
        )
        first_terms = {st.enrollments[0].term for st in students if st.enrollments}
        start_years = {term.split("-", 1)[0] for term in first_terms}
        assert len(start_years) >= 2, (
            f"expected start cohorts in multiple years, got {start_years}"
        )


# ── Derived-field helper tests ────────────────────────────────────────────────


class TestDeriveStudentFields:
    def test_computes_gpa_from_completed_enrollments_only(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top4="0701",
            enrollments=[
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "A", "Completed"),
                Enrollment("CS 2", "CS 2", "Computer Science", "2022-Fall", "C", "Completed"),
                Enrollment("CS 3", "CS 3", "Computer Science", "2022-Winter", "W", "Withdrawn"),
            ],
        )
        rows = _derive_student_fields([student], top4_to_dept={"0701": "Computer Science"})
        assert len(rows) == 1
        # (4 + 2) / 2 = 3.0; the withdrawn row is excluded
        assert rows[0]["gpa"] == 3.0
        assert rows[0]["courses_completed"] == 2

    def test_uses_top4_to_dept_mapping_for_primary_focus_when_available(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top4="0701",
            enrollments=[
                Enrollment("BIOL 1", "Bio 1", "Biology", "2022-Fall", "A", "Completed"),
            ],
        )
        # Even though the single completed enrollment is in Biology, the
        # authoritative TOP4 → department mapping should win.
        rows = _derive_student_fields([student], top4_to_dept={"0701": "Computer Science"})
        assert rows[0]["primary_focus"] == "Computer Science"

    def test_falls_back_to_enrollment_derived_focus_when_top4_unmapped(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top4="9999",
            enrollments=[
                Enrollment("BIOL 1", "Bio 1", "Biology", "2022-Fall", "A", "Completed"),
                Enrollment("BIOL 2", "Bio 2", "Biology", "2022-Fall", "B", "Completed"),
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "A", "Completed"),
            ],
        )
        rows = _derive_student_fields([student], top4_to_dept={})
        assert rows[0]["primary_focus"] == "Biology"

    def test_returns_zero_gpa_when_no_completed_enrollments(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top4="0701",
            enrollments=[
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "W", "Withdrawn"),
            ],
        )
        rows = _derive_student_fields([student], top4_to_dept={"0701": "Computer Science"})
        assert rows[0]["gpa"] == 0.0
        assert rows[0]["courses_completed"] == 0
