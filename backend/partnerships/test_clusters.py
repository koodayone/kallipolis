"""Unit test for statewide cluster-member routing — which regional consortium a single
college expands into (partnerships.clusters._cluster_member_for_college).

Graph-free (COLLEGE_COE_REGION only), so the routing that unlocks statewide peers is
pinned in CI without a graph. The clustering itself is graph-backed and exercised by
the eval characterization suite; this pins only the region → consortium selection.

Coverage:
  - a Bay college routes to the curated `baccc` consortium (not the generic `bay`)
  - one representative college in each of the eight non-Bay COE regions routes to its
    own region member (GS→gs, LA→la, SD/I→sd-i, CVML→cvml, OC→oc, FN→fn, SCC→scc, IE/D→ie-d)
  - every college the region map knows routes to some consortium — no mapped college
    falls back to the solo view (the "all nine COE regions" guarantee)
  - an unmapped college returns None, so the caller keeps the solo view
"""

from ontology.regions import COLLEGE_COE_REGION
from partnerships.clusters import _cluster_member_for_college


def test_bay_college_routes_to_curated_baccc():
    # The Bay keeps the pinned consortium the goldens/clusters were tuned against,
    # even though it is the same 26 colleges as the generic Bay region member.
    assert _cluster_member_for_college("De Anza College") == "baccc"


def test_non_bay_colleges_route_to_their_region_member():
    # One representative college per non-Bay COE region — each routes to the generic
    # region member whose id is the slug of the region code. Together with the Bay
    # case above this covers all nine COE regions.
    assert _cluster_member_for_college("American River College") == "gs"       # Greater Sacramento
    assert _cluster_member_for_college("Long Beach City College") == "la"      # Los Angeles
    assert _cluster_member_for_college("San Diego City College") == "sd-i"     # San Diego / Imperial
    assert _cluster_member_for_college("Bakersfield College") == "cvml"        # Central Valley / Mother Lode
    assert _cluster_member_for_college("Coastline College") == "oc"            # Orange County
    assert _cluster_member_for_college("Butte College") == "fn"                # Far North
    assert _cluster_member_for_college("Allan Hancock College") == "scc"       # South Central Coast
    assert _cluster_member_for_college("Barstow Community College") == "ie-d"  # Inland Empire / Desert


def test_every_mapped_college_routes_to_a_consortium():
    # Statewide totality: no college the COE region map knows falls back to None, so
    # every mapped college expands into a consortium of peers. Guards the "all nine
    # COE regions" claim against a future region code the router can't resolve.
    unrouted = sorted(c for c in COLLEGE_COE_REGION if _cluster_member_for_college(c) is None)
    assert unrouted == [], f"mapped colleges with no consortium route: {unrouted}"


def test_unmapped_college_returns_none():
    assert _cluster_member_for_college("Nonexistent College") is None
