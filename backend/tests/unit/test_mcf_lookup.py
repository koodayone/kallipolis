"""Unit tests for ontology.mcf_lookup string normalizers.

These two functions are the lookup-key bridge between Neo4j course codes
("CT 100") and the Chancellor's Office Master Course File format
("CT100AB"). Drift here silently breaks TOP6 resolution for SWP projects.
"""

from ontology.mcf_lookup import _normalize_course_code, _normalize_mcf_course_id


class TestNormalizeCourseCode:
    def test_strips_space_between_prefix_and_number(self):
        assert _normalize_course_code("CT 221") == "CT221"

    def test_handles_multiletter_prefix(self):
        assert _normalize_course_code("ARCH 100") == "ARCH100"

    def test_preserves_alphanumeric_suffix(self):
        assert _normalize_course_code("ACCT 101A") == "ACCT101A"

    def test_handles_split_prefix(self):
        assert _normalize_course_code("D H 063A") == "DH063A"

    def test_uppercases_input(self):
        assert _normalize_course_code("ct 221") == "CT221"

    def test_collapses_leading_and_trailing_whitespace(self):
        assert _normalize_course_code("  CT 221  ") == "CT221"


class TestNormalizeMcfCourseId:
    def test_strips_trailing_dot(self):
        # MCF exports sometimes emit "CT221." with a trailing dot.
        assert _normalize_mcf_course_id("CT221.") == "CT221"

    def test_strips_internal_whitespace(self):
        assert _normalize_mcf_course_id("CT 221") == "CT221"

    def test_uppercases_input(self):
        assert _normalize_mcf_course_id("ct221") == "CT221"

    def test_round_trips_with_course_code_normalizer(self):
        # Both functions should produce the same key for the same logical course,
        # which is what makes the (normalized, college) index lookup work.
        assert _normalize_course_code("CT 221") == _normalize_mcf_course_id("CT 221.")
