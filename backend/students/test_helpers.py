"""Unit tests for students.helpers — GPA and primary-focus derivation.

These two functions produce the derived fields materialized onto every
Student node after enrollment generation. compute_gpa maps letter grades
to grade points and averages; compute_primary_focus tallies completed
enrollments by department and picks the most common. Both are pure and
have to stay that way — drift silently corrupts the student pipeline
the partnership landscape view reads from.

Coverage:
  - compute_gpa grade point mapping, averaging, and rounding
  - Invalid grade handling (withdrawals, incompletes, unknown letters)
  - compute_primary_focus department tallying across completed courses
  - Status filtering (only "Completed" enrollments count)
  - Empty-input defaults for both functions
"""

from students.helpers import compute_gpa, compute_primary_focus


class TestComputeGpa:
    def test_returns_zero_for_empty_grade_list(self):
        assert compute_gpa([]) == 0.0

    def test_returns_four_when_all_grades_are_a(self):
        assert compute_gpa(["A", "A", "A"]) == 4.0

    def test_averages_mixed_grades(self):
        # (4 + 3 + 2) / 3 = 3.0
        assert compute_gpa(["A", "B", "C"]) == 3.0

    def test_counts_f_as_zero_in_average(self):
        # (4 + 0) / 2 = 2.0
        assert compute_gpa(["A", "F"]) == 2.0

    def test_ignores_grades_outside_the_grade_points_map(self):
        # "W" withdrawal and "I" incomplete aren't in GRADE_POINTS — excluded
        assert compute_gpa(["A", "W", "I", "B"]) == 3.5

    def test_returns_zero_when_all_grades_are_invalid(self):
        assert compute_gpa(["W", "I", "P"]) == 0.0

    def test_rounds_result_to_two_decimals(self):
        # (4 + 3 + 3) / 3 = 3.333... → 3.33
        assert compute_gpa(["A", "B", "B"]) == 3.33


class TestComputePrimaryFocus:
    def test_returns_undeclared_for_empty_enrollments(self):
        assert compute_primary_focus([]) == "Undeclared"

    def test_returns_undeclared_when_only_incomplete_enrollments(self):
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

    def test_ignores_in_progress_enrollments_when_tallying(self):
        enrollments = [
            {"department": "Biology", "status": "Completed"},
            {"department": "Math", "status": "In Progress"},
            {"department": "Math", "status": "In Progress"},
            {"department": "Math", "status": "In Progress"},
        ]
        assert compute_primary_focus(enrollments) == "Biology"

    def test_skips_enrollments_with_missing_department_field(self):
        enrollments = [
            {"department": "", "status": "Completed"},
            {"department": "Biology", "status": "Completed"},
        ]
        assert compute_primary_focus(enrollments) == "Biology"
