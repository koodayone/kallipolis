"""Reconciliation gate for the graph ontology (Step 3a).

Proves the loader (ontology.sector_graph) mirrors the Python ontology into the graph FAITHFULLY — every
Sector CONTAINS / OFFERS set, the crosswalk, and each authored Composition match the code. This is the gate
that makes the 3b read-swap safe: once graph == code is proven, swapping a read from Python to the graph is
byte-identical by construction.

@requires_graph: runs against a reachable Neo4j; skips locally without one.
"""
import os

import pytest


def _graph_available() -> bool:
    if "NEO4J_URI" not in os.environ:
        return False
    try:
        from ontology.schema import get_driver
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


requires_graph = pytest.mark.skipif(not _graph_available(), reason="no reachable Neo4j graph")


@requires_graph
def test_ontology_materializes_faithfully():
    """Load the ontology into the graph and assert it reproduces the code. The only permitted 'discrepancy'
    is `pending_hollow` — sector occupations that have no demand node yet (created in 3b), a known gap, not a
    loader error. Idempotent: safe to run alongside the rest of the graph-backed suite."""
    from ontology import sector_graph

    sector_graph.load()
    diffs = sector_graph.reconcile()
    real = [d for d in diffs if not d.startswith("pending_hollow")]
    assert not real, "graph ontology diverges from code:\n" + "\n".join(real)


@requires_graph
def test_covers_read_swap_reproduces_code():
    """The 3b COVERS read-swap: ``sector_covers`` reads the same sector membership the code holds
    (``SECTORS[sid].socs``) — byte-identical, which is what makes routing ``addressable_socs`` through it
    safe. The completeness gate keeps it faithful either way: graph-native when every sector SOC is node-
    backed, else it delegates to the git source. (Guards the lesson the crosswalk read-swap taught — read a
    relation from the graph only when the graph carries its full codomain.)"""
    from ontology import sector_graph
    from partnerships.sectors import SECTORS

    sector_graph.load()
    sector_graph._sector_covers_cache = None               # drop any cache captured before this load
    for sid, sec in SECTORS.items():
        assert sector_graph.sector_covers(sid) == set(sec.socs), f"COVERS read diverges from code for {sid}"


@requires_graph
def test_crosswalk_read_swap_matches_csv_on_our_universe():
    """The 3b crosswalk read-swap: restricted to our node set, the graph read (``crosswalk_socs``)
    reproduces the CSV crosswalk (``top6_to_soc``) exactly. That is the property every consumer relies on —
    they all intersect the crosswalk with sector/spec SOCs, which are nodes — so the swap is byte-identical
    whether the completeness gate reads the graph (complete) or falls back to the CSV (partial, e.g. the
    seed). Corrects the earlier over-revert: the crosswalk's *analyzed* codomain is the curated node set,
    which the full graph node-backs; edges into non-node SOCs are outside every computation we run."""
    from ontology import sector_graph
    from ontology.crosswalks import crosswalk_socs, top6_to_soc, _load_top_to_cip
    import ontology.crosswalks as cw
    from ontology.schema import get_driver

    sector_graph.load()
    cw._crosswalk_socs_cache = None                        # drop any cache captured before this load
    tops = list(_load_top_to_cip().keys())
    with get_driver().session() as s:
        nodes = {r["x"] for r in s.run("MATCH (o:Occupation) RETURN o.soc_code AS x")}
    graph, csv = crosswalk_socs(tops), top6_to_soc(tops)
    for t in set(graph) | set(csv):
        assert (graph.get(t, set()) & nodes) == (csv.get(t, set()) & nodes), \
            f"crosswalk read-swap diverges (intersected with the node set) for TOP {t}"


@requires_graph
def test_vocational_read_swap_reproduces_csv():
    """The 3b is_vocational read-swap: on a graph carrying the ProgramFamily/vocational layer,
    ``_vocational_top6_graph`` reads the same vocational set the CSV holds (``_load_vocational_top6``) —
    byte-identical, since ``pf.vocational`` is materialized from that CSV. Completeness-gated: graph-native
    when the full ProgramFamily universe is node-backed (the eval seed carries it in full, so this runs the
    graph path here), else the CSV."""
    from ontology import sector_graph
    from ontology.crosswalks import _vocational_top6_graph, _load_vocational_top6
    import ontology.crosswalks as cw

    sector_graph.load()
    cw._vocational_from_graph = None                       # drop any cache captured before this load
    graph_voc = _vocational_top6_graph()
    if graph_voc is not None:                              # complete graph → assert the graph-native read
        assert graph_voc == _load_vocational_top6(), "vocational read-swap diverges from the CSV"


@requires_graph
def test_scopes_is_the_home_classification_boundary():
    """The SCOPES edge-set IS the PCAH home classification (the P2 read-swap that retires excluded_tops): a
    program that crosswalks to an AM occupation but is NOT home-classified to adm (Commercial Music → arts/
    media, not manufacturing) is simply not in adm's portfolio — chosen by the authority, not hand-excluded."""
    from ontology import sector_graph

    sector_graph.load()
    scopes_adm = sector_graph.sector_scopes("adm")
    # 100500 Commercial Music crosswalks to an AM SOC but homes elsewhere → never in adm's portfolio.
    assert sector_graph.home_sector_by_top6().get("100500") != "adm"
    assert "100500" not in scopes_adm


def test_home_sector_classification_and_partition():
    """DataVista HOME classification (graph-free). Every family maps to a valid Sector id (or the
    `global_trade` slug). Post-P2, `sector_scopes` IS the home portfolio (membership chosen by the
    publication); the crosswalk then partitions the reachable feeders into native (home=sector, the R set),
    cross-sector (home elsewhere — dropped as noise), and unclassified. Pins the AM partition + the
    charter-home derivation against silent DataVista drift."""
    from ontology.sector_graph import home_sector_by_top6, sector_scopes
    from ontology.crosswalks import top6_to_soc, _load_top_to_cip, is_vocational
    from partnerships.sectors import SECTORS

    h = home_sector_by_top6()
    assert len(h) == 274                                        # the full DataVista TOP-Codes-to-Sectors publication
    assert all(sid in SECTORS or sid == "global_trade" for sid in h.values())

    # sector_scopes = the chosen home portfolio (the PCAH classification, verbatim).
    assert sector_scopes("adm") == {t for t, sid in h.items() if sid == "adm"}
    assert len(sector_scopes("adm")) == 27

    # The crosswalk partitions the VOCATIONAL feeders that reach an AM occupation by their home sector.
    xwalk = top6_to_soc(list(_load_top_to_cip()))
    adm_socs = set(SECTORS["adm"].socs)
    reach = {t for t, socs in xwalk.items() if (socs & adm_socs) and is_vocational(t)}
    native = reach & sector_scopes("adm")                      # home=adm AND feeds AM — the R set
    cross = {t for t in reach if h.get(t) not in (None, "adm")}  # feeds AM, home elsewhere → dropped as noise
    uncl = {t for t in reach if t not in h}                    # feeds AM but absent from the publication
    assert len(native) == 22                                   # matches the dashboard/plan (adm feeders R)
    assert "095690" in uncl                                    # Digital Fabrication — feeds AM, unclassified (P3 flag)
    assert cross                                               # real cross-sector bleed exists (Electro-Mech → ecu, …)
    # SVAMP's charter families are distant-home (never native to adm) → auto-flaggable, not a hand-list.
    for charter in ("043000", "094600", "094800"):
        assert h[charter] != "adm"
