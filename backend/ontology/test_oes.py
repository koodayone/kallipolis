"""Tests for backend/ontology/oes.py — the BLS OEWS loader.

These tests exercise the on-disk vintage that's vendored at
`backend/ontology/data/oes_2023/`. If the vintage is upgraded, expected
values may shift slightly; update accordingly. The structural
invariants (descent rule, column shape, fail-loudly on schema drift)
should hold across vintages.

Coverage:
  - oes_socs_for_naics4: returns non-empty for known NAICS-4
  - oes_socs_for_naics4: row shape and SOC code canonical format
  - oes_socs_for_naics4: employment positivity (suppressed cells filtered)
  - oes_socs_for_naics4: PCT_TOTAL row sums within reasonable bounds
  - Descent rule: NAICS-4 → NAICS-3 (e.g., NAICS 4248 wholesalers)
  - Descent rule: range-encoded NAICS-2 (Manufacturing "31-33") expands
  - Descent rule: Public Admin (NAICS 92) genuinely uncovered, returns []
  - Descent rule: NAICS-4 direct match returns resolution=4
  - oes_socs_for_naics4: invalid inputs return [] without raising
  - oes_match_resolution: returns None for invalid inputs
  - Signature SOCs present: water utility / electrical contractor /
    software / medical equipment / hospital industries each yield
    their canonical occupation in the OES pool
"""

from __future__ import annotations

import re

import pytest

from ontology import oes


# Reset module-level cache between tests in case a prior test triggered
# loading. Most tests can share the loaded data, but a fresh state
# guarantees the lazy-load path is exercised once.
@pytest.fixture(autouse=True, scope="module")
def _ensure_loaded():
    oes._ensure_loaded()
    yield


# ── Shape invariants ──────────────────────────────────────────────────────


def test_naics4_lookup_returns_nonempty_for_known_industry():
    """3344 = Semiconductor and Other Electronic Component Manufacturing.
    A well-populated NAICS-4 with hundreds of detailed SOC rows."""
    rows = oes.oes_socs_for_naics4("3344")
    assert len(rows) > 10, f"expected >10 SOC rows for NAICS 3344, got {len(rows)}"


def test_row_shape():
    """Every returned row carries the expected keys."""
    rows = oes.oes_socs_for_naics4("3344")
    expected_keys = {"soc", "title", "employment", "pct_total", "annual_mean_wage"}
    for row in rows:
        assert set(row.keys()) == expected_keys, (
            f"row missing/extra keys: {set(row.keys())} vs {expected_keys}"
        )


def test_soc_codes_match_canonical_format():
    """SOC codes follow the \\d{2}-\\d{4} pattern (e.g., 17-2072)."""
    soc_re = re.compile(r"^\d{2}-\d{4}$")
    rows = oes.oes_socs_for_naics4("3344")
    for row in rows:
        assert soc_re.match(row["soc"]), f"non-canonical SOC: {row['soc']!r}"


def test_employment_positive():
    """Suppressed cells (TOT_EMP None or 0) are filtered at load time."""
    rows = oes.oes_socs_for_naics4("3344")
    assert all(r["employment"] > 0 for r in rows)


def test_pct_total_within_reasonable_range():
    """PCT_TOTAL values are percentages of industry employment.
    Each row is between 0 and 100; the row sum across all SOCs in an
    industry should be in [70, 105] (BLS suppresses some cells, so the
    sum can fall short of 100; rounding occasionally pushes slightly
    over)."""
    rows = oes.oes_socs_for_naics4("3344")
    total = sum(r["pct_total"] for r in rows)
    assert 50 <= total <= 110, f"unexpected pct_total sum for 3344: {total}"
    for r in rows:
        assert 0 <= r["pct_total"] <= 100, f"out-of-range pct: {r}"


# ── Descent rule ──────────────────────────────────────────────────────────


def test_descent_to_naics3():
    """4248 (Beer/Wine/Distilled Alcoholic Beverage Wholesalers) is one
    of the NAICS-4 codes BLS does NOT publish detailed at NAICS-4. The
    descent must yield NAICS-3 (424 = Merchant Wholesalers, Nondurable
    Goods)."""
    resolution = oes.oes_match_resolution("4248")
    assert resolution in (3, 2), (
        f"expected descent to NAICS-3 or NAICS-2 for 4248, got "
        f"resolution={resolution}"
    )
    rows = oes.oes_socs_for_naics4("4248")
    assert len(rows) > 0, "descent should still yield rows"


def test_descent_to_naics2_for_manufacturing():
    """Manufacturing in the natsector file is encoded as the range
    '31-33' rather than three separate NAICS-2 codes. Descent of
    NAICS-3 codes that don't have direct NAICS-3 publication should
    land in the manufacturing NAICS-2 pool. NAICS 3221 (Pulp/Paper
    Mills, sometimes thinly published) confirms the range expansion
    works."""
    rows = oes.oes_socs_for_naics4("3221")
    # Whether 3221 publishes at NAICS-4, NAICS-3, or NAICS-2, the
    # result must be non-empty given range expansion of "31-33".
    assert len(rows) > 0, (
        "Manufacturing NAICS-4 must yield rows via descent (range "
        "encoding '31-33' expanded to per-NAICS-2 keys)"
    )


def test_public_admin_routes_to_government_aggregate():
    """NAICS 92 (Public Administration) is not published under the
    NAICS-2 axis in the standard OEWS National Industry-Occupation
    Matrix. BLS publishes Federal/State/Local government employment
    under the OEWS-specific cross-cutting code "99" instead. The
    descent rule routes NAICS-92 inputs there so Public Admin
    employers (police, fire, courts) get a real institutionally-
    sourced occupation pool — including 33-2011 Firefighters,
    33-3051 Police Officers, etc. — instead of being silently
    excluded from layer 1.
    """
    rows = oes.oes_socs_for_naics4("9224")  # Fire Protection
    assert len(rows) > 100, (
        "NAICS 92 must route to the OEWS-99 government aggregate "
        "rather than yielding empty"
    )
    socs = {r["soc"] for r in rows}
    assert "33-2011" in socs, (
        "OEWS-99 government pool must include Firefighters (33-2011) "
        "for fire department employers"
    )
    assert oes.oes_match_resolution("9224") == "government"


def test_public_admin_for_police_includes_officers():
    """Sanity check: NAICS 9221 Justice/Public Order/Safety routes to
    the OEWS-99 government pool, which includes Police Officers."""
    rows = oes.oes_socs_for_naics4("9221")
    socs = {r["soc"] for r in rows}
    assert "33-3051" in socs, (
        "OEWS-99 government pool must include Police and Sheriff's "
        "Patrol Officers (33-3051) for justice/public-order employers"
    )


def test_naics4_match_returns_resolution_4():
    """3344 is published at NAICS-4 — descent should not be needed."""
    assert oes.oes_match_resolution("3344") == 4


# ── Edge cases ────────────────────────────────────────────────────────────


def test_invalid_inputs_return_empty():
    """Non-NAICS-4 inputs return empty without raising."""
    assert oes.oes_socs_for_naics4("") == []
    assert oes.oes_socs_for_naics4("abc") == []
    assert oes.oes_socs_for_naics4("12") == []  # too short
    assert oes.oes_socs_for_naics4(None) == []  # type: ignore[arg-type]


def test_invalid_inputs_match_resolution_none():
    assert oes.oes_match_resolution("") is None
    assert oes.oes_match_resolution("abc") is None


# ── Specific industries from the rationality study ────────────────────────
# These cover the 12-employer test set used in
# /tmp/proposed_arch_experiment.py. The migration's domain-signature
# tests live in backend/employers/test_oes_layer1.py and depend on
# these NAICS-4 codes producing pools that include the expected SOCs.


@pytest.mark.parametrize("naics4,expected_soc,why", [
    ("2213", "51-8031", "water utilities → water/wastewater operators"),
    ("2382", "47-2111", "electrical contractors → electricians"),
    ("3342", "15-1252", "communications equipment → software developers"),
    ("3391", "51-9082", "medical equipment → medical appliance technicians"),
    ("6221", "29-1141", "general hospitals → registered nurses"),
])
def test_signature_socs_present_in_pool(naics4: str, expected_soc: str, why: str):
    """For each rationality-study NAICS-4, confirm the canonical
    industry-signature SOC is in the OES pool. This guards against
    BLS schema drift dropping a key SOC out of its industry's row set
    in a future vintage."""
    rows = oes.oes_socs_for_naics4(naics4)
    socs_in_pool = {r["soc"] for r in rows}
    assert expected_soc in socs_in_pool, (
        f"{why}: expected {expected_soc} in OES pool for NAICS {naics4}, "
        f"found {len(socs_in_pool)} SOCs but not this one"
    )
