"""Unit tests for occupations/generate.py — COE CSV parsing and CTE scope filtering.

generate.py is the upstream step of the occupations pipeline: it parses the
Centers of Excellence occupational demand CSV and emits occupations.json in
the exact shape the loader expects. Inclusion is gated by the institutional
CTE scope filter (COE ∩ PCAH CTE TOP→CIP→SOC) — see ontology/crosswalks.py.

Coverage:
  - Numeric coercion handles int cells, float cells, empty cells, and junk
  - Row extraction returns the expected (soc, region, shell, metrics) tuple
  - Row extraction strips whitespace from SOC, region, title, and education fields
  - generate_from_coe keeps SOCs inside the CTE-reachable set and drops the rest
"""

import csv
from pathlib import Path

import pytest

from occupations.generate import (
    _parse_float,
    _parse_int,
    _parse_row,
    generate_from_coe,
)
from ontology.crosswalks import CIP_SOC_PATH, TOP_CIP_PATH

# generate_from_coe applies the CTE scope filter, which composes the
# external TOP→CIP and CIP→SOC crosswalks (see ontology/crosswalks.py).
# Skip the end-to-end class on machines that don't have those files.
_HAS_EXTERNAL_DATASET = TOP_CIP_PATH.exists() and CIP_SOC_PATH.exists()
_skip_external = pytest.mark.skipif(
    not _HAS_EXTERNAL_DATASET,
    reason="requires external cc_dataset (TOP→CIP, CIP→SOC crosswalks)",
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

    def test_returns_soc_region_shell_and_metrics(self):
        soc, region, shell, metrics = _parse_row(self._row())
        assert soc == "15-1252"
        assert region == "Bay"
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
        soc, region, shell, _ = _parse_row(
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
        assert shell["education_level"] == "Bachelor's degree"

    def test_returns_none_metrics_when_cells_are_empty(self):
        _, _, _, metrics = _parse_row(
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


@_skip_external
class TestGenerateFromCoe:
    """End-to-end test that the CTE scope filter admits trades and excludes pre-engineering.

    Uses a synthetic CSV with a handful of representative SOCs. Depends on
    ontology.crosswalks.cte_reachable_socs() returning the real CTE universe,
    which covers the asserted SOCs at runtime.
    """

    HEADER = [
        "SOC",
        "Region",
        "Description",
        "Typical Entry Level Education",
        "2024 Jobs",
        "Median Annual Earnings",
        "2024 - 2029 % Change",
        "Average Annual Job Openings",
    ]

    FIXTURE_ROWS = [
        # Trades — should be included
        ["47-2111", "CA", "Electricians", "High school diploma or equivalent", "85080", "74600", "0.0920", "9330"],
        ["51-4121", "CA", "Welders, Cutters, Solderers, and Brazers", "High school diploma or equivalent", "30160", "57150", "0.0236", "3190"],
        ["47-2152", "CA", "Plumbers, Pipefitters, and Steamfitters", "High school diploma or equivalent", "53940", "66740", "0.0429", "5140"],
        # Current-scope degree programs — should be included
        ["15-1252", "CA", "Software Developers", "Bachelor's degree", "203000", "145000", "0.17", "15000"],
        ["29-1141", "CA", "Registered Nurses", "Bachelor's degree", "315000", "125000", "0.06", "22000"],
        # Degree-only roles — included too: generate applies NO education or
        # crosswalk-reachability filter. The COE middle-skill publication is the
        # authority for which SOCs appear, so curation lives upstream in the source
        # file (in production it would not list these); generate is 1:1 with it.
        ["17-2051", "CA", "Civil Engineers", "Bachelor's degree", "40000", "110000", "0.04", "2500"],
        ["17-2141", "CA", "Mechanical Engineers", "Bachelor's degree", "30000", "105000", "0.03", "2000"],
        ["19-2011", "CA", "Astronomers", "Doctoral or professional degree", "200", "140000", "0.05", "15"],
    ]

    def _write_csv(self, tmp_path: Path) -> Path:
        csv_path = tmp_path / "coe.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.HEADER)
            w.writerows(self.FIXTURE_ROWS)
        return csv_path

    def test_includes_every_source_soc(self, tmp_path):
        """generate_from_coe is 1:1 with its source file: every SOC the COE
        middle-skill publication tracks becomes a node, with no derived filter.
        This replaces an earlier COE-∩-CTE-reachable filter, which both admitted
        non-middle-skill occupations via crosswalk over-reach AND dropped
        middle-skill occupations the crosswalk could not reach. Curation — which
        occupations are middle-skill — is the COE designation, applied upstream in
        the source file, not a reachability filter here. So even Bachelor's/Doctoral
        rows in the input surface (production's source simply would not list them)."""
        csv_path = self._write_csv(tmp_path)
        result = generate_from_coe(csv_path)
        socs = {o["soc_code"] for o in result}

        assert socs == {r[0] for r in self.FIXTURE_ROWS}, \
            "generate must return exactly the source file's SOCs — no derived filter"

    def test_preserves_education_level_on_surviving_rows(self, tmp_path):
        """education_level stays on the node as metadata even though it no longer gates inclusion."""
        csv_path = self._write_csv(tmp_path)
        result = generate_from_coe(csv_path)
        by_soc = {o["soc_code"]: o for o in result}
        assert by_soc["47-2111"]["education_level"] == "High school diploma or equivalent"
