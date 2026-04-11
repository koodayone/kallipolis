"""Unit tests for students.helpers — GPA and primary-focus derivation."""

from students.helpers import compute_gpa, compute_primary_focus


class TestComputeGpa:
    def test_empty_returns_zero(self):
        assert compute_gpa([]) == 0.0

    def test_all_a_returns_four(self):
        assert compute_gpa(["A", "A", "A"]) == 4.0

    def test_mixed_grades_averages(self):
        # (4 + 3 + 2) / 3 = 3.0
        assert compute_gpa(["A", "B", "C"]) == 3.0

    def test_f_counts_as_zero(self):
        # (4 + 0) / 2 = 2.0
        assert compute_gpa(["A", "F"]) == 2.0

    def test_invalid_grades_are_ignored(self):
        # "W" withdrawal and "I" incomplete aren't in GRADE_POINTS — excluded
        assert compute_gpa(["A", "W", "I", "B"]) == 3.5

    def test_all_invalid_returns_zero(self):
        assert compute_gpa(["W", "I", "P"]) == 0.0

    def test_result_is_rounded_to_two_decimals(self):
        # (4 + 3 + 3) / 3 = 3.333... → 3.33
        assert compute_gpa(["A", "B", "B"]) == 3.33


class TestComputePrimaryFocus:
    def test_empty_returns_undeclared(self):
        assert compute_primary_focus([]) == "Undeclared"

    def test_only_incomplete_returns_undeclared(self):
        enrollments = [
            {"department": "Biology", "status": "In Progress"},
            {"department": "Math", "status": "In Progress"},
        ]
        assert compute_primary_focus(enrollments) == "Undeclared"

    def test_picks_most_common_completed_department(self):
        enrollments = [
            {"department": "Biology", "status": "Completed"},
            {"department": "Biology", "status": "Completed"},
            {"department": "Math", "status": "Completed"},
        ]
        assert compute_primary_focus(enrollments) == "Biology"

    def test_ignores_in_progress_courses(self):
        enrollments = [
            {"department": "Biology", "status": "Completed"},
            {"department": "Math", "status": "In Progress"},
            {"department": "Math", "status": "In Progress"},
            {"department": "Math", "status": "In Progress"},
        ]
        assert compute_primary_focus(enrollments) == "Biology"

    def test_missing_department_field_is_skipped(self):
        enrollments = [
            {"department": "", "status": "Completed"},
            {"department": "Biology", "status": "Completed"},
        ]
        assert compute_primary_focus(enrollments) == "Biology"
