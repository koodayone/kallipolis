"""Unit tests for occupations/generate.py — COE CSV parsing and workforce-band filtering.

generate.py is the upstream step of the occupations pipeline: it parses the
Centers of Excellence occupational demand CSV and emits occupations.json in
the exact shape the loader expects. The tests below guard the pure helpers
that do numeric coercion, row extraction, and workforce-band selection, so
that CSV schema changes and education-level drift are caught at unit-test
time rather than at Neo4j load time.

Coverage:
  - Numeric coercion handles int cells, float cells, empty cells, and junk
  - Row extraction returns the expected (soc, region, shell, education, metrics) tuple
  - Row extraction strips whitespace from SOC, region, title, and education fields
  - Workforce-band filter keeps postsecondary nondegree, associate's, and bachelor's
  - Workforce-band filter drops high-school, no-credential, master's, doctoral, and N/A
"""

from occupations.generate import (
    EXCLUDED_EDUCATION,
    _is_in_workforce_band,
    _parse_float,
    _parse_int,
    _parse_row,
)


class TestParseInt:
    def test_returns_int_for_integer_string(self):
        assert _parse_int("42") == 42

    def test_returns_int_for_integer_value(self):
        assert _parse_int(42) == 42

    def test_returns_none_for_empty_string(self):
        assert _parse_int("") is None

    def test_returns_none_for_none(self):
        assert _parse_int(None) is None

    def test_returns_none_for_non_numeric_string(self):
        assert _parse_int("not a number") is None


class TestParseFloat:
    def test_returns_float_for_decimal_string(self):
        assert _parse_float("0.05") == 0.05

    def test_returns_float_for_integer_string(self):
        assert _parse_float("5") == 5.0

    def test_returns_none_for_empty_string(self):
        assert _parse_float("") is None

    def test_returns_none_for_none(self):
        assert _parse_float(None) is None

    def test_returns_none_for_non_numeric_string(self):
        assert _parse_float("not a number") is None


class TestParseRow:
    def _row(self, **overrides) -> dict:
        base = {
            "SOC": "15-1252",
            "Region": "Bay",
            "Description": "Software Developers",
            "Typical Entry Level Education": "Bachelor's degree",
            "2024 Jobs": "12000",
            "Median Annual Earnings": "145000",
            "2024 - 2029 % Change": "0.08",
            "Average Annual Job Openings": "900",
        }
        base.update(overrides)
        return base

    def test_returns_soc_region_shell_education_and_metrics(self):
        soc, region, shell, education, metrics = _parse_row(self._row())
        assert soc == "15-1252"
        assert region == "Bay"
        assert education == "Bachelor's degree"
        assert shell["soc_code"] == "15-1252"
        assert shell["title"] == "Software Developers"
        assert shell["education_level"] == "Bachelor's degree"
        assert shell["skills"] == []
        assert shell["description"] == ""
        assert shell["regions"] == {}
        assert metrics == {
            "employment": 12000,
            "annual_wage": 145000,
            "growth_rate": 0.08,
            "annual_openings": 900,
        }

    def test_strips_whitespace_from_string_fields(self):
        soc, region, shell, education, _ = _parse_row(
            self._row(
                **{
                    "SOC": "  15-1252  ",
                    "Region": "  Bay  ",
                    "Description": "  Software Developers  ",
                    "Typical Entry Level Education": "  Bachelor's degree  ",
                }
            )
        )
        assert soc == "15-1252"
        assert region == "Bay"
        assert shell["title"] == "Software Developers"
        assert education == "Bachelor's degree"

    def test_returns_none_metrics_when_cells_are_empty(self):
        _, _, _, _, metrics = _parse_row(
            self._row(
                **{
                    "2024 Jobs": "",
                    "Median Annual Earnings": "",
                    "2024 - 2029 % Change": "",
                    "Average Annual Job Openings": "",
                }
            )
        )
        assert metrics == {
            "employment": None,
            "annual_wage": None,
            "growth_rate": None,
            "annual_openings": None,
        }


class TestIsInWorkforceBand:
    def test_keeps_bachelors_degree(self):
        assert _is_in_workforce_band("Bachelor's degree") is True

    def test_keeps_associates_degree(self):
        assert _is_in_workforce_band("Associate's degree") is True

    def test_keeps_postsecondary_nondegree_award(self):
        assert _is_in_workforce_band("Postsecondary nondegree award") is True

    def test_drops_high_school_diploma(self):
        assert _is_in_workforce_band("High school diploma or equivalent") is False

    def test_drops_no_formal_credential(self):
        assert _is_in_workforce_band("No formal educational credential") is False

    def test_drops_masters_degree(self):
        assert _is_in_workforce_band("Master's degree") is False

    def test_drops_doctoral_or_professional_degree(self):
        assert _is_in_workforce_band("Doctoral or professional degree") is False

    def test_drops_some_college_no_degree(self):
        assert _is_in_workforce_band("Some college, no degree") is False

    def test_drops_na_education_level(self):
        assert _is_in_workforce_band("N/A") is False

    def test_excluded_set_covers_every_rejection(self):
        for level in EXCLUDED_EDUCATION:
            assert _is_in_workforce_band(level) is False
