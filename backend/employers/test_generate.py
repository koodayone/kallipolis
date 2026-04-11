"""Unit tests for employers/generate.py pure helpers.

Targets the name-cleaning regex chain, the unified canonical dedup key,
the ordering key used to sort EDD records by employer size, the branch
deduplication that collapses multiple records for the same employer
down to the entry with the largest size class, the NAICS-to-SOC
fallback assigner, the employers.json formatter, and the cross-college
merge that unions regions and occupations. Drift in any of these
routines silently corrupts the employer index feeding partnership
proposals — partners with the wrong names, wrong sector tags, two
entries where there should be one, or employers tagged to the wrong
region after a merge.

Coverage:
  - _clean_employer_name: abbreviation expansion (Ctr, Hosp, Med, Assn, Sys, etc.)
  - _clean_employer_name: corporate suffix stripping (Inc, LLC, Ltd)
  - _clean_employer_name: case-insensitive matching and whitespace
  - _normalize_name / _canonical_key: lowercasing, suffix stripping,
    trailing-location collapsing, whitespace normalization
  - _should_drop_name: deterministic pre-filter for "Dept Of X" and
    similar non-institutional entries
  - _size_sort_key: ordering by size class, unknown/missing fall last
  - _size_sort_key: substring matching against real EDD size strings
  - _deduplicate_branches: single-entry pass-through, collapse to
    largest size, branch preservation (e.g. UCLA vs UCSD), name
    cleanup on the surviving entry
  - _assign_soc_codes: NAICS 4-to-2 digit prefix fallback, 10-code cap,
    empty regional group handling, missing NAICS
  - _format_for_json: COE region resolution, LLM description
    pass-through, fallback description construction
  - _merge_employers: new insert, region union on collision, SOC union
    on collision, added/updated counts
"""

from employers.generate import (
    _assign_soc_codes,
    _canonical_key,
    _clean_employer_name,
    _deduplicate_branches,
    _format_for_json,
    _merge_employers,
    _normalize_name,
    _should_drop_name,
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


class TestCanonicalKey:
    def test_strips_corporate_suffix(self):
        assert _canonical_key("Acme Corp") == "acme"

    def test_strips_trailing_city_after_dash(self):
        assert _canonical_key("Kaiser Permanente - Los Angeles") == "kaiser permanente"

    def test_strips_trailing_city_after_comma(self):
        assert _canonical_key("Kaiser Permanente, Fresno") == "kaiser permanente"

    def test_collapses_whitespace(self):
        assert _canonical_key("Foo    Bar") == "foo bar"

    def test_preserves_distinct_names_without_delimiters(self):
        # "University of California Los Angeles" has no dash or comma,
        # so the trailing-location stripper must leave it alone — UCLA
        # and UCSD must not collapse to the same key.
        k1 = _canonical_key("University of California Los Angeles")
        k2 = _canonical_key("University of California San Diego")
        assert k1 != k2


class TestShouldDropName:
    def test_drops_dept_of(self):
        assert _should_drop_name("Dept Of Motor Vehicles") is True

    def test_drops_county_of(self):
        assert _should_drop_name("County Of Los Angeles") is True

    def test_preserves_regular_employer(self):
        assert _should_drop_name("Kaiser Permanente") is False

    def test_case_insensitive(self):
        assert _should_drop_name("dept of health") is True


class TestAssignSocCodes:
    def test_naics4_to_naics2_fallback(self):
        # NAICS4 "3341" has no 3-digit entry in NAICS_TO_SOC_GROUPS, so
        # the function falls back to the 2-digit prefix "33" which maps
        # to SOC major groups ["51", "17", "15"].
        occ_by_group = {
            "51": ["51-1011", "51-2011"],
            "17": ["17-2112"],
            "15": ["15-1252"],
        }
        emp = {"naics4": "3341"}
        result = _assign_soc_codes(emp, occ_by_group)
        assert "51-1011" in result
        assert "17-2112" in result
        assert "15-1252" in result

    def test_caps_at_ten(self):
        occ_by_group = {
            "51": [f"51-{i:04d}" for i in range(20)],
            "17": [f"17-{i:04d}" for i in range(20)],
        }
        emp = {"naics4": "3341"}
        result = _assign_soc_codes(emp, occ_by_group)
        assert len(result) == 10

    def test_missing_naics_returns_empty(self):
        assert _assign_soc_codes({}, {"51": ["51-1011"]}) == []

    def test_unknown_naics_returns_empty(self):
        # NAICS prefix "99" is not in NAICS_TO_SOC_GROUPS.
        assert _assign_soc_codes({"naics4": "9900"}, {"51": ["51-1011"]}) == []

    def test_empty_regional_group(self):
        # NAICS4 "6221" → prefix "62" → SOC groups ["29", "31", "21", "11"].
        # No codes in any of those groups means empty result.
        assert _assign_soc_codes({"naics4": "6221"}, {}) == []


class TestFormatForJson:
    def test_llm_description_passed_through(self):
        # An LLM-provided description that differs from the name should
        # survive into the formatted output unchanged.
        result = _format_for_json(
            [{"name": "Acme", "sector": "Manufacturing",
              "description": "Acme makes cogs.", "soc_codes": ["51-1011"]}],
            metro="Los Angeles-Long Beach-Glendale",
        )
        assert len(result) == 1
        assert result[0]["description"] == "Acme makes cogs."
        assert result[0]["occupations"] == ["51-1011"]
        assert result[0]["sector"] == "Manufacturing"

    def test_fallback_description_built_from_edd_fields(self):
        # With no LLM description (or description identical to name),
        # the formatter assembles one from city/county/industry/size.
        result = _format_for_json(
            [{
                "name": "Acme",
                "sector": "Manufacturing",
                "city": "Fresno",
                "county": "Fresno",
                "industry": "Machine Shops",
                "size_class": "500-999 employees",
                "soc_codes": [],
            }],
            metro="Fresno",
        )
        desc = result[0]["description"]
        assert "Acme" in desc
        assert "Fresno" in desc
        assert "Machine Shops" in desc
        assert "500-999" in desc

    def test_regions_derived_from_metro(self):
        # The formatted record's regions array comes from
        # OEWS_METRO_TO_COE; if a metro doesn't map, the metro name is
        # used as-is (legacy fallback).
        result = _format_for_json(
            [{"name": "A", "sector": "X", "description": "d", "soc_codes": []}],
            metro="Los Angeles-Long Beach-Glendale",
        )
        assert len(result[0]["regions"]) == 1
        # LA metro maps to the "LA" COE code, not back to the full metro name.
        assert result[0]["regions"][0] != "Los Angeles-Long Beach-Glendale"


class TestMergeEmployers:
    def test_new_employer_inserted(self):
        existing: list[dict] = []
        new = [{"name": "Acme", "sector": "Manufacturing", "regions": ["LA"],
                "occupations": ["51-1011"]}]
        merged, added, updated = _merge_employers(new, existing)
        assert added == 1
        assert updated == 0
        assert len(merged) == 1

    def test_region_union_on_name_collision(self):
        # Two runs insert the same employer from different metros; the
        # merged record should carry both regions.
        existing = [{"name": "Kaiser", "sector": "Healthcare",
                     "regions": ["Bay"], "occupations": ["29-1141"]}]
        new = [{"name": "Kaiser", "sector": "Healthcare",
                "regions": ["LA"], "occupations": ["29-1141"]}]
        merged, added, updated = _merge_employers(new, existing)
        assert added == 0
        assert updated == 1
        assert set(merged[0]["regions"]) == {"Bay", "LA"}

    def test_occupation_union_on_name_collision(self):
        # Two runs insert the same employer with different occupation
        # assignments; both should survive in the merged record.
        existing = [{"name": "Kaiser", "sector": "Healthcare",
                     "regions": ["Bay"], "occupations": ["29-1141"]}]
        new = [{"name": "Kaiser", "sector": "Healthcare",
                "regions": ["Bay"], "occupations": ["29-2061"]}]
        merged, _, _ = _merge_employers(new, existing)
        assert set(merged[0]["occupations"]) == {"29-1141", "29-2061"}

    def test_no_duplicate_region_or_soc(self):
        # If the new record repeats an existing region or SOC, the
        # merged lists do not grow (set-like union semantics).
        existing = [{"name": "Acme", "sector": "Manufacturing",
                     "regions": ["Bay"], "occupations": ["51-1011"]}]
        new = [{"name": "Acme", "sector": "Manufacturing",
                "regions": ["Bay"], "occupations": ["51-1011"]}]
        merged, added, updated = _merge_employers(new, existing)
        assert added == 0
        assert updated == 1
        assert merged[0]["regions"] == ["Bay"]
        assert merged[0]["occupations"] == ["51-1011"]

    def test_collision_uses_canonical_key(self):
        # Suffixes and trailing locations shouldn't cause a miss.
        existing = [{"name": "Kaiser Permanente", "sector": "Healthcare",
                     "regions": ["Bay"], "occupations": []}]
        new = [{"name": "Kaiser Permanente, LA", "sector": "Healthcare",
                "regions": ["LA"], "occupations": []}]
        merged, added, updated = _merge_employers(new, existing)
        assert added == 0
        assert updated == 1
        assert set(merged[0]["regions"]) == {"Bay", "LA"}
