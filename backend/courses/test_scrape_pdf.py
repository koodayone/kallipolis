"""Unit tests for courses.scrape_pdf — PDF catalog extraction helpers.

The scrape_pdf module owns the active stage-1+2 course extraction path: it
downloads a college catalog PDF, filters course-description pages by a
regex heuristic, chunks them for Gemini, and post-processes the returned
course records. These tests exercise the pure helpers that do not touch
Gemini, the filesystem, or pypdf — the parts of the pipeline whose
correctness is silent-failure prone because broken logic just loses
courses rather than raising.

The course code regex is the highest-leverage piece. A prior version
(`[A-Z]{2,6}\\s+\\d{1,4}[A-Z]?`) silently dropped multi-word department
codes like "C S 1A" at Foothill, which meant entire pages of courses
slipped below the page-filter threshold. These tests pin the shape of the
replacement regex so that failure mode cannot return.

Coverage:
  - COURSE_CODE_PATTERN matches single-word, multi-word, and two-letter-
    suffix course codes, and rejects near-misses that were false positives
    under the old pattern.
  - normalize_course_code collapses whitespace, hyphens, dots, and case
    differences to a single canonical form.
  - _deduplicate_courses collapses duplicate codes by normalized key and
    keeps the more populated record.
  - _ensure_str_list coerces mixed list/string/empty inputs into a list of
    trimmed strings.
  - _to_raw_course strips the trailing catalog-year stamp from descriptions
    and coerces all fields to strings with default empties.
  - _taxonomy_hash is stable, short, and changes with the taxonomy.
"""

from __future__ import annotations

from unittest.mock import patch

from courses.scrape_pdf import (
    COURSE_CODE_PATTERN,
    _deduplicate_courses,
    _ensure_str_list,
    _taxonomy_hash,
    _to_raw_course,
    normalize_course_code,
)


class TestCourseCodePattern:
    def test_matches_single_word_prefix(self):
        assert COURSE_CODE_PATTERN.findall("ENGL 1A") == ["ENGL 1A"]

    def test_matches_leading_zero_course_number(self):
        assert COURSE_CODE_PATTERN.findall("BUS 010") == ["BUS 010"]

    def test_matches_multi_word_prefix_like_computer_science(self):
        # The old regex (`[A-Z]{2,6}\\s+\\d`) dropped this form entirely,
        # losing every Foothill CS course. Pin the fix.
        assert "C S 1A" in COURSE_CODE_PATTERN.findall("C S 1A: Object Oriented Programming")

    def test_matches_three_token_prefix(self):
        assert "MED A 10" in COURSE_CODE_PATTERN.findall("MED A 10 — Medical Terminology")

    def test_matches_two_letter_numeric_suffix(self):
        assert "CIS 101L" in COURSE_CODE_PATTERN.findall("CIS 101L Lab")

    def test_finds_multiple_codes_in_one_page(self):
        page = "ENGL 1A - Composition. Prerequisite: ENGL 100. See also BIOL 10A."
        codes = COURSE_CODE_PATTERN.findall(page)
        assert "ENGL 1A" in codes
        assert "ENGL 100" in codes
        assert "BIOL 10A" in codes

    def test_ignores_lowercase_words(self):
        assert COURSE_CODE_PATTERN.findall("this is not a course") == []

    def test_ignores_bare_acronyms_without_numbers(self):
        assert COURSE_CODE_PATTERN.findall("CSU UC IGETC") == []


class TestNormalizeCourseCode:
    def test_collapses_internal_whitespace(self):
        assert normalize_course_code("C S 1A") == "CS1A"

    def test_uppercases_input(self):
        assert normalize_course_code("cs 1a") == "CS1A"

    def test_strips_hyphens_dots_and_underscores(self):
        assert normalize_course_code("CS-1A") == "CS1A"
        assert normalize_course_code("CS.1A") == "CS1A"
        assert normalize_course_code("CS_1A") == "CS1A"

    def test_every_common_spelling_of_cs_1a_collapses_to_the_same_key(self):
        canonical = normalize_course_code("CS 1A")
        assert normalize_course_code("C S 1A") == canonical
        assert normalize_course_code("cs-1a") == canonical
        assert normalize_course_code("CS.1A") == canonical
        assert normalize_course_code("CS1A") == canonical

    def test_preserves_alphanumeric_order_for_numeric_suffix(self):
        assert normalize_course_code("CIS 101L") == "CIS101L"

    def test_empty_input_normalizes_to_empty(self):
        assert normalize_course_code("") == ""


class TestDeduplicateCourses:
    def test_collapses_variants_of_the_same_code(self):
        courses = [
            {"code": "C S 1A", "name": "Intro"},
            {"code": "CS 1A", "name": "Intro to Programming", "description": "long description", "units": "4"},
        ]
        result = _deduplicate_courses(courses)
        assert len(result) == 1
        # Keeps the more populated entry — the second record has strictly
        # more truthy fields.
        assert result[0]["name"] == "Intro to Programming"

    def test_keeps_distinct_codes(self):
        courses = [
            {"code": "ENGL 1A", "name": "Composition"},
            {"code": "ENGL 1B", "name": "Composition II"},
        ]
        result = _deduplicate_courses(courses)
        assert len(result) == 2

    def test_drops_courses_with_empty_code(self):
        courses = [
            {"code": "", "name": "nameless"},
            {"code": "   ", "name": "whitespace"},
            {"code": "ENGL 1A", "name": "Composition"},
        ]
        result = _deduplicate_courses(courses)
        assert len(result) == 1
        assert result[0]["code"] == "ENGL 1A"

    def test_prefers_entry_with_more_populated_fields(self):
        sparse = {"code": "BIO 10", "name": "Bio", "description": "", "units": ""}
        dense = {"code": "BIO 10", "name": "Bio", "description": "Cell biology", "units": "4"}
        result = _deduplicate_courses([sparse, dense])
        assert result[0]["description"] == "Cell biology"
        assert result[0]["units"] == "4"


class TestEnsureStrList:
    def test_returns_empty_list_for_empty_string(self):
        assert _ensure_str_list("") == []

    def test_wraps_nonempty_string_in_list(self):
        assert _ensure_str_list("single outcome") == ["single outcome"]

    def test_passes_through_list_of_strings(self):
        assert _ensure_str_list(["a", "b"]) == ["a", "b"]

    def test_coerces_non_string_list_items(self):
        assert _ensure_str_list([1, 2]) == ["1", "2"]

    def test_drops_empty_entries_from_list(self):
        assert _ensure_str_list(["keep", "", "   ", "also"]) == ["keep", "also"]

    def test_returns_empty_for_none(self):
        assert _ensure_str_list(None) == []


class TestToRawCourse:
    def test_strips_trailing_catalog_year_stamp_from_description(self):
        raw = _to_raw_course({"code": "CS 1A", "description": "Intro to Python. 2024.25"})
        assert raw.description == "Intro to Python."

    def test_coerces_missing_fields_to_empty_strings(self):
        raw = _to_raw_course({"code": "CS 1A"})
        assert raw.name == ""
        assert raw.department == ""
        assert raw.description == ""
        assert raw.prerequisites == ""
        assert raw.learning_outcomes == []
        assert raw.course_objectives == []

    def test_preserves_learning_outcomes_list(self):
        raw = _to_raw_course({
            "code": "CS 1A",
            "learning_outcomes": ["outcome one", "outcome two"],
        })
        assert raw.learning_outcomes == ["outcome one", "outcome two"]

    def test_sets_url_to_empty(self):
        # PDF extraction has no per-course URL; the pipeline fills this
        # in only for HTML scrapers.
        raw = _to_raw_course({"code": "CS 1A"})
        assert raw.url == ""


class TestTaxonomyHash:
    def test_returns_twelve_character_hex_digest(self):
        h = _taxonomy_hash()
        assert len(h) == 12
        int(h, 16)  # must be valid hex

    def test_is_stable_across_calls(self):
        assert _taxonomy_hash() == _taxonomy_hash()

    def test_changes_when_taxonomy_changes(self):
        baseline = _taxonomy_hash()
        with patch("courses.scrape_pdf.UNIFIED_TAXONOMY", frozenset({"Skill A", "Skill B"})):
            changed = _taxonomy_hash()
        assert baseline != changed
