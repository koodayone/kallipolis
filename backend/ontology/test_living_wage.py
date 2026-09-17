"""Unit tests for ontology.living_wage — MIT's county living wage, bundled.

The bundle is fetched from livingwage.mit.edu by `fetch_bundle` and committed; these tests
pin what the report relies on without touching the network.

Coverage:
  - the bundle holds all 58 California counties with a stated data year
  - a county resolves with or without the " County" suffix; the headline is one adult, no children
  - Santa Clara's headline figure is the one the Foothill evaluations quote
  - an unknown county is None, never a guess
"""

from ontology.living_wage import HEADLINE, HOUSEHOLDS, _load, living_wage


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
