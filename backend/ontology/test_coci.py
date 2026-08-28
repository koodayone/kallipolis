"""Unit tests for ontology/coci.py — the CCCCO Curriculum Inventory loader.

`coci_award_tier` is deliberately a SEPARATE parser from `ontology.programs.award_tier`
(that one feeds `award_type_sort_key`, which the dashboard's programs panel uses for
ordering, so widening it to a second dialect would put a shipped surface at risk). The
two share only the `AWARD_TIERS` vocabulary. This file is what keeps them from drifting
apart without coupling them, so the same credential can never be labelled two different
ways on one page.

The bundled export ships in-repo (`data/coci_programs.csv.gz`), so every test runs
unconditionally — no skipif gates. Non-goals: whether a college's approved award set is
factually complete (COCI is authoritative), and the exact current unit requirement, which
COCI deliberately does NOT own — its unit fields are approval-time snapshots, so surfaces
render `award_band()` and link to the college catalog instead.

Coverage:
  - the bundled export loads and its vintage is stated
  - every non-blank COCI award string maps into the shared AWARD_TIERS vocabulary
  - COCI and DataMart dialects agree tier-for-tier across all six tiers
  - the "A.S. T Degree" space form is a transfer degree (a 1,548-row regression)
  - every certificate award type renders a unit band, and bands name both calendars
  - degrees carry no band
  - the college map is total (115), explicit, and handles the irregulars
  - TOP CODE parses out of COCI's combined label
  - Foothill 121000 surfaces the 2024 Respiratory Care B.S., highest credential first
  - offered_only drops Inactive but keeps Teachout
"""
import csv
import gzip

import pytest

from ontology.coci import (COCI_VINTAGE, OFFERED_STATUSES, STATUS_TEACHOUT, _COLLEGE_CODE,
                           _DATA, _top6, award_band, awards_for, coci_award_tier, coci_code)
from ontology.programs import AWARD_TIERS, award_tier


def _rows():
    with gzip.open(_DATA, "rt", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_bundle_loads():
    rows = _rows()
    assert len(rows) == 29402
    assert "2026-08-27" in COCI_VINTAGE


def test_every_award_maps_into_the_shared_vocabulary():
    """No COCI award string may produce a tier the report cannot order or label."""
    bad = {r["AWARD"] for r in _rows()
           if r["AWARD"].strip() and coci_award_tier(r["AWARD"]) not in AWARD_TIERS}
    assert not bad, f"award strings outside AWARD_TIERS: {sorted(bad)[:5]}"


@pytest.mark.parametrize("coci_str,datamart_str,tier", [
    # The pairs that must agree, one per tier. If either dialect is edited and these stop
    # matching, the report would label the same credential two different ways in one page.
    ("Certificate of Achievement requiring 8S/12Q to fewer than 16S/24Q units",
     "Certificate requiring 8 to fewer than 16 semester units", "certificate"),
    ("Certificate of Achievement requiring 30S/45Q to fewer than 60S/90Q units",
     "Certificate requiring 30 to < 60 semester units", "certificate"),
    ("A.S. Degree", "Associate of Science (A.S.) degree", "associate degree"),
    ("A.A. Degree", "Associate of Arts (A.A.) degree", "associate degree"),
    ("Baccalaureate of Science (B.S.) Degree.",
     "Baccalaureate of Science (B.S.) degree", "baccalaureate"),
    ("Noncredit program", "Noncredit award requiring < 48 hours", "noncredit award"),
    # The 1,548-row trap: COCI writes the hyphen form AND the space form.
    ("A.A- T Degree", "Associate in Arts for Transfer (A.A.-T) Degree", "transfer degree"),
    ("A.S. T Degree", "Associate in Science for Transfer (A.S.-T) Degree", "transfer degree"),
])
def test_dialects_agree(coci_str, datamart_str, tier):
    assert coci_award_tier(coci_str) == tier
    assert award_tier(datamart_str) == tier


def test_space_form_transfer_degree_is_not_an_associate_degree():
    """Regression: a regex matching only "A.A- T" mis-filed 1,548 rows as associate."""
    n = sum(1 for r in _rows() if r["AWARD"].strip() == "A.S. T Degree")
    assert n > 1000
    assert coci_award_tier("A.S. T Degree") == "transfer degree"


def test_every_certificate_band_renders():
    """The band is what surfaces print instead of the stale raw unit fields, so a
    certificate that produced no band would silently lose its unit information."""
    missing = {r["AWARD"] for r in _rows()
               if "Certificate" in r["AWARD"] and not award_band(r["AWARD"])}
    assert not missing, f"certificate award types with no band: {sorted(missing)}"


def test_bands_are_calendar_explicit():
    """Never a bare "units" — Foothill is a quarter college and DataMart's labels are
    semester-normalized, so an unqualified number would be ambiguous on the page."""
    b = award_band("Certificate of Achievement requiring 8S/12Q to fewer than 16S/24Q units")
    assert b == "8–16 semester / 12–24 quarter units"
    assert award_band("A.S. Degree") == ""       # degrees carry no approved band


def test_degrees_have_no_band():
    assert all(not award_band(r["AWARD"]) for r in _rows() if "Degree" in r["AWARD"])


def test_college_map_is_total_and_explicit():
    """Every mapped code must exist in the export; the irregulars are the point."""
    codes = {r["COLLEGE"].strip() for r in _rows()}
    unknown = {v for v in _COLLEGE_CODE.values() if v not in codes}
    assert not unknown, f"mapped to codes absent from COCI: {sorted(unknown)}"
    assert len(_COLLEGE_CODE) == 115
    assert coci_code("City College of San Francisco") == "SAN FRANCISCO CITY"
    assert coci_code("Los Angeles Trade-Technical College") == "L.A. TRADE-TECH"
    assert coci_code("Cañada College") == "CANADA"
    assert coci_code("Not A College") is None


def test_top6_parses_the_combined_label():
    assert _top6("1210.00* Respiratory Care/Therapy") == "121000"
    assert _top6("0102.10* Veterinary Technician (Licensed)") == "010210"
    assert _top6("") == ""


def test_awards_for_foothill_respiratory_therapy():
    """The case the section exists for: an Active B.S. with no conferrals in our window."""
    got = awards_for("Foothill College", "121000")
    titles = [a.title for a in got]
    assert "Respiratory Care" in titles
    bs = next(a for a in got if a.title == "Respiratory Care")
    assert bs.tier == "baccalaureate"
    assert bs.approved == "2024-05-30"
    assert got[0].tier == "baccalaureate"       # highest credential first


def test_offered_only_drops_inactive():
    """Foothill's Landscape Technician certificate is Inactive and must not read as offered."""
    offered = {a.title for a in awards_for("Foothill College", "010900")}
    every = {a.title for a in awards_for("Foothill College", "010900", offered_only=False)}
    assert "Landscape Technician" in every
    assert "Landscape Technician" not in offered
    assert all(a.status in OFFERED_STATUSES for a in awards_for("Foothill College", "010900"))


def test_teachout_is_kept_not_collapsed():
    """Teachout is the most useful review signal COCI carries; it must survive the filter."""
    assert STATUS_TEACHOUT in OFFERED_STATUSES
    n = sum(1 for r in _rows() if r["STATUS"] == STATUS_TEACHOUT)
    assert n > 500
