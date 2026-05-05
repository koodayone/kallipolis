"""Unit tests for students.generate — synthetic student population generator.

The generator is the largest pure-logic surface in the students feature.
It takes an enriched course catalog plus DataMart TOP6 calibration and
produces a deterministic, seeded population of synthetic students whose
enrollments and grade distributions are calibrated against real
institutional data. These tests exercise the generator without touching
Neo4j, the MCF directory, or any calibration file on disk — calibration
loaders and the MCF index are monkeypatched to hermetic fixtures, and
the Neo4j loader is exercised only through _derive_student_fields, the
pure helper that computes gpa / primary_focus / courses_completed
directly from in-memory state.

Coverage:
  - _parse_units string shapes: decimals, ranges, unit suffixes, blanks
  - _course_prefix letter-prefix extraction with and without spaces
  - _build_term_sequence ordering and absence of Summer terms
  - generate_students determinism under a fixed seed with injected calibration
  - generate_students assigns the declared primary_top6 to every student
  - generate_students only emits grades from the TOP6 distribution it was given
  - Start cohort spread: students begin in multiple academic years
  - _ordering_ok and _record_prefix per-student prefix-state helpers
  - Same-subject numeric ordering is enforced across every student's trajectory
  - Grade-sampling tier ladder falls back TOP6 → TOP4 rollup → default
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
    _ordering_ok,
    _parse_units,
    _record_prefix,
    _sample_grade,
    generate_students,
)
from students.helpers import course_order_key


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


class TestBuildTermSequence:
    def test_emits_three_terms_per_academic_year(self):
        terms = _build_term_sequence()
        assert len(terms) == 9

    def test_contains_no_summer_terms(self):
        terms = _build_term_sequence()
        assert all("Summer" not in t for t in terms)

    def test_starts_with_fall_of_first_academic_year(self):
        terms = _build_term_sequence()
        assert terms[0].endswith("Fall")


# ── Generator tests (fixture-based) ───────────────────────────────────────────


def _fake_top6_calibration() -> dict:
    """Two TOP6 codes with distinct grade distributions, plus a TOP4 rollup.

    070100 (Computer and Information Sciences, General) is A-heavy.
    040100 (Biology, General) is B-heavy.
    The distributions share no weight, so the test can assert that
    generated grades only come from the calibrated letters.
    """
    return {
        "college_name": "TestCollege",
        "college_key": "testcollege",
        "total_enrollments": 1000,
        "top6_codes": {
            "070100": {
                "name": "Computer and Information Sciences",
                "enrollment": 600,
                "grades": {"A": 0.6, "B": 0.3, "W": 0.1},
            },
            "040100": {
                "name": "Biology, General",
                "enrollment": 400,
                "grades": {"B": 0.6, "C": 0.3, "W": 0.1},
            },
        },
        "top4_rollup": {
            "0701": {"enrollment": 600, "grades": {"A": 0.6, "B": 0.3, "W": 0.1}},
            "0401": {"enrollment": 400, "grades": {"B": 0.6, "C": 0.3, "W": 0.1}},
        },
    }


def _fake_courses() -> List[dict]:
    """Enough catalog breadth to keep the DEPT_CAP/unit-cap loops happy."""
    courses: List[dict] = []
    for i in range(1, 11):
        courses.append({
            "code": f"CS {i}",
            "name": f"CS course {i}",
            "department": "Computer Science",
            "units": "3",
            "grading": "Letter",
        })
    for i in range(1, 11):
        courses.append({
            "code": f"BIOL {i}",
            "name": f"Biology course {i}",
            "department": "Biology",
            "units": "3",
            "grading": "Letter",
        })
    return courses


def _fake_course_to_top6() -> Dict[str, str]:
    """Maps each fake course to its corresponding TOP6 code."""
    mapping = {}
    for i in range(1, 11):
        mapping[f"CS {i}"] = "070100"
        mapping[f"BIOL {i}"] = "040100"
    return mapping


@pytest.fixture
def injected_calibration(monkeypatch):
    """Inject hermetic calibration + per-course TOP6 map so generate_students
    never touches the filesystem or the MCF index."""
    monkeypatch.setattr(
        gen, "_load_top6_calibration", lambda college_key: _fake_top6_calibration()
    )
    monkeypatch.setattr(
        gen,
        "_load_college_metrics",
        lambda college_key: {"ft_ratio": 0.5, "retention_rate": 0.8, "enrollment": 50},
    )
    monkeypatch.setattr(
        gen,
        "_build_course_to_top6",
        lambda courses, college_key: _fake_course_to_top6(),
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

    def test_assigns_every_student_a_valid_primary_top6(self, injected_calibration):
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=40,
            seed=1,
        )
        assert all(st.primary_top6 in {"070100", "040100"} for st in students)

    def test_grades_come_only_from_calibrated_distributions(self, injected_calibration):
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=40,
            seed=3,
        )
        allowed = {"A", "B", "C", "W"}
        observed = {
            e.grade
            for st in students
            for e in st.enrollments
        }
        assert observed.issubset(allowed)

    def test_spreads_start_cohorts_across_multiple_academic_years(self, injected_calibration):
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


# ── Prefix-ordering helper tests ──────────────────────────────────────────────


class TestOrderingHelpers:
    def test_first_enrollment_in_new_prefix_is_always_ok(self):
        assert _ordering_ok("HIST 17B", {}) is True

    def test_same_or_higher_order_key_passes(self):
        prefix_max = {"HIST": (17, "A")}
        assert _ordering_ok("HIST 17A", prefix_max) is True
        assert _ordering_ok("HIST 17B", prefix_max) is True
        assert _ordering_ok("HIST 18", prefix_max) is True

    def test_lower_order_key_in_same_prefix_is_blocked(self):
        prefix_max = {"HIST": (17, "B")}
        assert _ordering_ok("HIST 17A", prefix_max) is False
        assert _ordering_ok("HIST 3A", prefix_max) is False

    def test_ordering_is_scoped_per_prefix(self):
        prefix_max = {"HIST": (17, "B")}
        assert _ordering_ok("PSYC 1", prefix_max) is True

    def test_record_prefix_initializes_a_new_prefix_entry(self):
        prefix_max: Dict[str, tuple] = {}
        _record_prefix("HIST 17A", prefix_max)
        assert prefix_max == {"HIST": (17, "A")}

    def test_record_prefix_advances_only_on_higher_order_key(self):
        prefix_max = {"HIST": (17, "B")}
        _record_prefix("HIST 17A", prefix_max)
        assert prefix_max["HIST"] == (17, "B")
        _record_prefix("HIST 18", prefix_max)
        assert prefix_max["HIST"] == (18, "")

    def test_record_prefix_ignores_codes_without_letter_prefix(self):
        prefix_max: Dict[str, tuple] = {}
        _record_prefix("123", prefix_max)
        assert prefix_max == {}


class TestEnrollmentOrdering:
    """Every generated student's enrollments must be non-decreasing by
    course order key within any prefix they touch. The sampler updates
    prefix_max after each successful draw, so insertion order IS the
    sampler's decision order — walking st.enrollments directly validates
    the same rule. Re-sorting by course code would fire false positives
    because "BIOL 10" sorts before "BIOL 9" alphabetically.
    """

    def test_no_same_prefix_regressions_across_a_generated_population(self, injected_calibration):
        students, _ = generate_students(
            college_key="testcollege",
            courses=_fake_courses(),
            num_students=80,
            seed=11,
        )

        violations: List[str] = []
        for st in students:
            max_key: Dict[str, tuple] = {}
            for e in st.enrollments:
                prefix = _course_prefix(e.course_code)
                if not prefix:
                    continue
                key = course_order_key(e.course_code)
                prior = max_key.get(prefix)
                if prior is not None and key < prior:
                    violations.append(
                        f"{st.uuid}: {e.course_code} ({e.term}) after prior "
                        f"{prefix} order key {prior}"
                    )
                    continue
                if prior is None or key > prior:
                    max_key[prefix] = key

        assert violations == [], (
            f"Found {len(violations)} same-prefix ordering violations in generated "
            f"population (first 5 shown): {violations[:5]}"
        )


# ── Grade-sampling tier ladder ────────────────────────────────────────────────


class TestSampleGrade:
    """The grade sampler uses a tier ladder when TOP6 data is missing:
    exact TOP6 -> parent TOP4 rollup -> DEFAULT_GRADES. The fallback
    level is reported back so the generator can count how often each
    tier was used."""

    def _rng(self, seed: int = 42):
        from random import Random
        return Random(seed)

    def test_uses_exact_top6_when_present(self):
        top6_data = {"070100": {"grades": {"A": 1.0}}}
        top4_rollup: dict = {}
        default = {"A": 0.0, "F": 1.0}
        grade, status, fallback = _sample_grade(
            "070100", top6_data, top4_rollup, default, self._rng(),
        )
        assert grade == "A"
        assert status == "Completed"
        assert fallback == 0

    def test_falls_back_to_parent_top4_when_top6_missing(self):
        top6_data: dict = {}
        top4_rollup = {"0701": {"grades": {"B": 1.0}}}
        default = {"A": 1.0}
        grade, _, fallback = _sample_grade(
            "070100", top6_data, top4_rollup, default, self._rng(),
        )
        assert grade == "B"
        assert fallback == 1

    def test_falls_back_to_default_when_both_missing(self):
        top6_data: dict = {}
        top4_rollup: dict = {}
        default = {"F": 1.0}
        grade, status, fallback = _sample_grade(
            "070100", top6_data, top4_rollup, default, self._rng(),
        )
        assert grade == "F"
        assert status == "Completed"
        assert fallback == 2

    def test_withdrawn_status_maps_from_w_grade(self):
        top6_data = {"070100": {"grades": {"W": 1.0}}}
        grade, status, _ = _sample_grade(
            "070100", top6_data, {}, {}, self._rng(),
        )
        assert grade == "W"
        assert status == "Withdrawn"


# ── Derived-field helper tests ────────────────────────────────────────────────


class TestDeriveStudentFields:
    def test_computes_gpa_from_completed_enrollments_only(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top6="070100",
            enrollments=[
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "A", "Completed"),
                Enrollment("CS 2", "CS 2", "Computer Science", "2022-Fall", "C", "Completed"),
                Enrollment("CS 3", "CS 3", "Computer Science", "2022-Winter", "W", "Withdrawn"),
            ],
        )
        rows = _derive_student_fields([student], top6_to_dept={"070100": "Computer Science"})
        assert len(rows) == 1
        assert rows[0]["gpa"] == 3.0
        assert rows[0]["courses_completed"] == 2

    def test_uses_top6_to_dept_mapping_for_primary_focus_when_available(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top6="070100",
            enrollments=[
                Enrollment("BIOL 1", "Bio 1", "Biology", "2022-Fall", "A", "Completed"),
            ],
        )
        # Even though the single completed enrollment is in Biology, the
        # authoritative TOP6 → department mapping should win.
        rows = _derive_student_fields([student], top6_to_dept={"070100": "Computer Science"})
        assert rows[0]["primary_focus"] == "Computer Science"

    def test_falls_back_to_enrollment_derived_focus_when_top6_unmapped(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top6="999999",
            enrollments=[
                Enrollment("BIOL 1", "Bio 1", "Biology", "2022-Fall", "A", "Completed"),
                Enrollment("BIOL 2", "Bio 2", "Biology", "2022-Fall", "B", "Completed"),
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "A", "Completed"),
            ],
        )
        rows = _derive_student_fields([student], top6_to_dept={})
        assert rows[0]["primary_focus"] == "Biology"

    def test_primary_top6_is_surfaced_on_the_derived_row(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top6="126000",
            enrollments=[
                Enrollment("HLTH 20", "Public Health", "Health", "2022-Fall", "A", "Completed"),
            ],
        )
        rows = _derive_student_fields([student], top6_to_dept={"126000": "Health"})
        assert rows[0]["primary_top6"] == "126000"
        assert rows[0]["primary_focus"] == "Health"

    def test_returns_zero_gpa_when_no_completed_enrollments(self):
        student = GeneratedStudent(
            uuid="uuid-1",
            primary_top6="070100",
            enrollments=[
                Enrollment("CS 1", "CS 1", "Computer Science", "2022-Fall", "W", "Withdrawn"),
            ],
        )
        rows = _derive_student_fields([student], top6_to_dept={"070100": "Computer Science"})
        assert rows[0]["gpa"] == 0.0
        assert rows[0]["courses_completed"] == 0
