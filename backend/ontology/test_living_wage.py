"""Unit tests for ontology.living_wage — MIT's county living wage, bundled.

The bundle is fetched from livingwage.mit.edu by `fetch_bundle` and committed; these tests
pin what the report relies on without touching the network.

Coverage:
  - the bundle holds all 58 California counties with a stated data year
  - a county resolves with or without the " County" suffix; the headline is one adult, no children
  - Santa Clara's headline figure is the one the Foothill evaluations quote
  - an unknown county is None, never a guess
  - the page parser reads the household table and the data year, and never takes the 2,080 hours figure for a year
  - every county the college map names is in the bundle
"""

from ontology.living_wage import HEADLINE, HOURS_PER_YEAR, HOUSEHOLDS, _load, _parse_county, living_wage
from ontology.regions import COLLEGE_COUNTY


def test_bundle_covers_california_with_a_vintage():
    rows = _load()
    assert len(rows) == 58
    assert all(r.vintage.isdigit() and r.vintage.startswith("20") and r.vintage != "2080" for r in rows.values())
    assert all(set(r.hourly) == set(HOUSEHOLDS) for r in rows.values())


def test_lookup_and_headline():
    a = living_wage("Santa Clara"); b = living_wage("Santa Clara County")
    assert a is b and a.county == "Santa Clara County" and a.fips == "06085"
    assert a.headline == a.hourly[HEADLINE] and a.headline == 38.0
    assert a.hourly["1a1c"] > a.headline > a.hourly["2a2w0c"]       # a child costs; a second earner shares
    assert a.url.endswith("/counties/06085")


def test_unknown_county_is_none():
    assert living_wage("Nowhere") is None


def _page(sentence="The living wage shown is the hourly rate … working full-time or 2080 hours per year. Data as of 2026."):
    cells = lambda vals: "".join(f"<td>${v}</td>" for v in vals)
    return f"""<html><head><title>Living Wage Calculation for Santa Clara County, California</title></head><body>
    <h1>Living Wage Calculation for Santa Clara County, California</h1><p>{sentence}</p>
    <table><tr><th></th><th colspan="4">1 ADULT</th><th colspan="4">2 ADULTS(1 WORKING)</th><th colspan="4">2 ADULTS(BOTH WORKING)</th></tr>
    <tr><td>Living Wage</td>{cells(['38.00','69.42','94.79','128.52','47.86','58.09','61.42','75.24','23.93','36.84','48.41','64.07'])}</tr>
    <tr><td>Poverty Wage</td>{cells(['7.67','10.40','13.13','15.87','10.40','13.13','15.87','18.60','5.20','6.57','7.93','9.30'])}</tr>
    <tr><td>Minimum Wage</td>{cells(['16.90'] * 12)}</tr></table></body></html>"""


def test_parse_county_reads_the_table_and_the_year_but_not_the_hours():
    county, vintage, lw, pov, mw = _parse_county(_page())
    assert county == "Santa Clara County" and vintage == "2026"
    assert set(lw) == set(HOUSEHOLDS) and lw[HEADLINE] == 38.0 and lw["1a1c"] == 69.42 and pov == 7.67 and mw == 16.9
    assert _parse_county(_page("working 2080 hours per year."))[1] == ""          # only the hours figure: no year, not "2080"
    assert _parse_county(_page("no year here"))[1] == ""
    assert HOURS_PER_YEAR == 2080 and living_wage("Santa Clara").headline_annual == 38.0 * 2080


def test_every_college_county_is_in_the_bundle():
    missing = sorted(c for c in set(COLLEGE_COUNTY.values()) if living_wage(c) is None)
    assert missing == []
