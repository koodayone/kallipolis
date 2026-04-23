"""Unit tests for students.helpers — GPA, primary-focus derivation, and
course code ordering.

compute_gpa and compute_primary_focus produce derived fields materialized
onto every Student node after enrollment generation. course_order_key
supplies the ordering used by the sampler to enforce same-prefix numeric
sequence within a student's enrollment history. All three are pure and
have to stay that way — drift silently corrupts the student pipeline the
partnership landscape view reads from.

Coverage:
  - compute_gpa grade point mapping, averaging, and rounding
  - Invalid grade handling (withdrawals, incompletes, unknown letters)
  - compute_primary_focus department tallying across completed courses
  - Status filtering (only "Completed" enrollments count)
  - Empty-input defaults for both derivation functions
  - course_order_key parsing across simple, multi-letter prefix, CSU
    concurrent-enrollment, repeatable, honors, and multi-digit forms
  - Ordering correctness via tuple comparison within a numeric class
"""

from students.helpers import compute_gpa, compute_primary_focus, course_order_key


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


class TestCourseOrderKey:
    def test_simple_prefix_and_number(self):
        assert course_order_key("HIST 17") == (17, "")

    def test_letter_suffix_captured(self):
        assert course_order_key("HIST 17B") == (17, "B")

    def test_multi_letter_prefix(self):
        assert course_order_key("C S 77B") == (77, "B")

    def test_csu_concurrent_enrollment_code(self):
        assert course_order_key("ENGL C1001") == (1001, "")

    def test_csu_concurrent_with_honors_suffix(self):
        assert course_order_key("PSYC C1000H") == (1000, "H")

    def test_multi_digit_with_multi_letter_suffix(self):
        assert course_order_key("CHEM 12AL") == (12, "AL")

    def test_honors_suffix_preserved(self):
        assert course_order_key("ENGL 1CH") == (1, "CH")

    def test_repeatable_suffix_preserved(self):
        assert course_order_key("PSYC 72R") == (72, "R")

    def test_no_number_returns_zero(self):
        assert course_order_key("UNKNOWN") == (0, "")

    def test_ordering_number_dominates(self):
        assert course_order_key("HIST 17B") < course_order_key("HIST 18A")

    def test_ordering_suffix_breaks_tie_on_equal_number(self):
        assert course_order_key("HIST 17A") < course_order_key("HIST 17B")
        assert course_order_key("HIST 17B") < course_order_key("HIST 17C")

    def test_ordering_plain_number_before_suffixed(self):
        # 17 with no suffix sorts before 17A
        assert course_order_key("HIST 17") < course_order_key("HIST 17A")
