"""Unit tests for employers/generate.py pure helpers.

Targets the name-cleaning regex chain, the ordering key used to sort
EDD records by employer size, and the branch deduplication that
collapses multiple records for the same employer down to the entry
with the largest size class. Drift in any of these routines silently
corrupts the employer index feeding partnership proposals — partners
with the wrong names, wrong sector tags, or two entries where there
should be one.

Coverage:
  - _clean_employer_name: abbreviation expansion (Ctr, Hosp, Med, etc.)
  - _clean_employer_name: corporate suffix stripping (Inc, LLC, Ltd)
  - _clean_employer_name: case-insensitive matching and whitespace
  - _normalize_name: lowercasing and suffix stripping for dedup keys
  - _size_sort_key: ordering by size class, unknown/missing fall last
  - _size_sort_key: substring matching against real EDD size strings
  - _deduplicate_branches: single-entry pass-through, collapse to
    largest size, branch preservation (e.g. UCLA vs UCSD), name
    cleanup on the surviving entry
"""

from employers.generate import (
    _clean_employer_name,
    _deduplicate_branches,
    _normalize_name,
    _size_sort_key,
)


class TestCleanEmployerName:
    def test_expands_ctr_to_center(self):
        assert _clean_employer_name("Valley Medical Ctr") == "Valley Medical Center"

    def test_expands_hosp_to_hospital(self):
        assert _clean_employer_name("St Mary Hosp") == "St Mary Hospital"

    def test_multiple_abbreviations_expanded(self):
        assert _clean_employer_name("Regional Med Ctr") == "Regional Medical Center"

    def test_strips_inc_suffix(self):
        assert _clean_employer_name("Acme Corp Inc") == "Acme Corporation"

    def test_strips_llc_suffix(self):
        assert _clean_employer_name("Foothill Services LLC") == "Foothill Services"

    def test_strips_ltd_suffix(self):
        assert _clean_employer_name("Central Valley Ltd") == "Central Valley"

    def test_case_insensitive_abbreviation_match(self):
        # The regex chain uses re.IGNORECASE; lowercase input should still expand.
        assert _clean_employer_name("valley medical ctr") == "valley medical Center"

    def test_already_clean_name_unchanged(self):
        assert _clean_employer_name("Foothill Community College") == "Foothill Community College"

    def test_strips_whitespace(self):
        assert _clean_employer_name("  Acme Corp  ") == "Acme Corporation"


class TestNormalizeName:
    def test_lowercases_for_matching(self):
        assert _normalize_name("Acme Corp") == "acme"

    def test_strips_suffix_before_lowercasing(self):
        assert _normalize_name("Foothill LLC") == "foothill"

    def test_plain_name_passed_through(self):
        assert _normalize_name("Plain Name") == "plain name"


class TestSizeSortKey:
    def test_larger_size_sorts_first(self):
        big = {"size_class": "1,000-4,999 employees"}
        small = {"size_class": "50-99 employees"}
        assert _size_sort_key(big) < _size_sort_key(small)

    def test_unknown_size_sorts_last(self):
        known = {"size_class": "500-999 employees"}
        unknown = {"size_class": "mystery"}
        assert _size_sort_key(known) < _size_sort_key(unknown)

    def test_missing_size_class_sorts_last(self):
        assert _size_sort_key({}) == 99

    def test_substring_match(self):
        # The lookup uses `in`, so a size_class containing extra prose still hits.
        assert _size_sort_key({"size_class": "Approximately 500-999 employees"}) == 1


class TestDeduplicateBranches:
    def test_single_employer_passed_through(self):
        result = _deduplicate_branches([
            {"name": "Acme Corp", "size_class": "500-999 employees"},
        ])
        assert len(result) == 1
        assert result[0]["name"] == "Acme Corporation"  # cleaned on output

    def test_duplicate_names_collapse_to_largest(self):
        employers = [
            {"name": "Acme", "size_class": "100-249 employees"},
            {"name": "Acme", "size_class": "1,000-4,999 employees"},
            {"name": "Acme", "size_class": "50-99 employees"},
        ]
        result = _deduplicate_branches(employers)
        assert len(result) == 1
        assert "1,000-4,999" in result[0]["size_class"]

    def test_different_branches_preserved(self):
        # Different trailing qualifiers must not collide — normalize_name only
        # strips corporate suffixes, not city/division names.
        employers = [
            {"name": "University of California Los Angeles", "size_class": "1,000-4,999 employees"},
            {"name": "University of California San Diego", "size_class": "1,000-4,999 employees"},
        ]
        result = _deduplicate_branches(employers)
        assert len(result) == 2

    def test_cleans_surviving_name(self):
        employers = [
            {"name": "Regional Med Ctr", "size_class": "500-999 employees"},
            {"name": "Regional Med Ctr", "size_class": "1,000-4,999 employees"},
        ]
        result = _deduplicate_branches(employers)
        assert len(result) == 1
        assert result[0]["name"] == "Regional Medical Center"

    def test_empty_input(self):
        assert _deduplicate_branches([]) == []
