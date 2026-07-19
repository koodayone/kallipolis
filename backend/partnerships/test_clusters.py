"""Unit test for statewide cluster-member routing — which regional consortium a single
college expands into (partnerships.clusters._cluster_member_for_college).

Graph-free (COLLEGE_COE_REGION only), so the routing that unlocks statewide peers is
pinned in CI without a graph. The clustering itself is graph-backed and exercised by
the eval characterization suite; this pins only the region → consortium selection.

Coverage:
  - a Bay college routes to the curated `baccc` consortium (not the generic `bay`)
  - non-Bay colleges route to their own region member (GS→gs, LA→la, SD/I→sd-i, CVML→cvml)
  - an unmapped college returns None, so the caller keeps the solo view
"""

from partnerships.clusters import _cluster_member_for_college


def test_bay_college_routes_to_curated_baccc():
    # The Bay keeps the pinned consortium the goldens/clusters were tuned against,
    # even though it is the same 26 colleges as the generic Bay region member.
    assert _cluster_member_for_college("De Anza College") == "baccc"


def test_non_bay_colleges_route_to_their_region_member():
    assert _cluster_member_for_college("American River College") == "gs"    # Greater Sacramento
    assert _cluster_member_for_college("Long Beach City College") == "la"   # Los Angeles
    assert _cluster_member_for_college("San Diego City College") == "sd-i"  # San Diego / Imperial
    assert _cluster_member_for_college("Bakersfield College") == "cvml"     # Central Valley / Mother Lode


def test_unmapped_college_returns_none():
    assert _cluster_member_for_college("Nonexistent College") is None
