"""Guard: the one supply number.

Program supply for a landscape coordinate resolves through ONE canonical function
— ``quantities.supply_over_socs`` (projected annual awards over the DEDUPED
in-scope feeder set, averaged over the recent-award-years window). Every surface
that reports that supply must equal that one number. This pins the three
INDEPENDENT paths that render it:

  - the occupation landscape's ``aggregate.combined_supply_total`` (landscape_build),
  - the programs landscape's ``total_supply`` (landscape_programs),
  - the MCP engine's member supply (``engine.supply`` → ``supply_over_socs``).

Each has diverged historically, which is why this guard exists:
  - the occupation builder summed per-(college×SOC)-cell supply over the course-
    tagged pipeline — dropping untagged feeders AND double-counting a feeder that
    serves several SOCs (SVAMP read 360 vs the true 118);
  - the programs treemap sized on the single latest award year (SVAMP read 185 vs
    118), off the shared projection every other supply surface uses.

The invariant is STRUCTURAL: all three read the same feeders over the same window,
so it holds on ANY graph — including the partial eval seed, where a coordinate
whose programs are absent gives 0 == 0 == 0, still consistent. The test asserts
agreement, never a specific magnitude, so it is data-independent.

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
def test_dashboard_and_canonical_supply_agree_for_every_live_coordinate():
    """For every published landscape coordinate, the two dashboard builders and the
    canonical supply function report the identical projected annual supply — the
    one number that the 360-bug and the 185-bug each broke on a different surface."""
    from partnerships import quantities as Q
    from partnerships.landscape import routable_specs
    from partnerships.landscape_build import build_landscape
    from partnerships.landscape_programs import build_programs_landscape
    from partnerships.resolve import resolve

    for spec in routable_specs():
        rspec = resolve(spec)
        cols, socs = list(rspec.colleges), list(rspec.socs)
        canonical = Q.supply_over_socs(cols, socs, spec=rspec)
        occ = build_landscape(rspec).aggregate.combined_supply_total
        prog = build_programs_landscape(rspec).total_supply
        assert occ == canonical == prog, (
            f"supply diverges for {spec.id}: "
            f"occupation-landscape={occ}, canonical supply_over_socs={canonical}, "
            f"programs-landscape={prog}"
        )


@requires_graph
def test_mcp_member_supply_routes_through_the_same_canonical_number():
    """The MCP measure resolves member supply through the SAME canonical function:
    ``engine.supply(sel, over='member')`` equals ``supply_over_socs`` over the
    Selection's own member colleges + sector occupations. Uses a real member×sector
    coordinate (SMCCD × Advanced Manufacturing); skips if it isn't live here."""
    from mcp_server import engine
    from partnerships import quantities as Q

    sel = engine.select("smccd", "adm")
    if sel is None:                       # coordinate not live on this graph — nothing to assert
        pytest.skip("smccd×adm coordinate is not live on this graph")
    mcp = engine.supply(sel, over="member")
    canonical = Q.supply_over_socs(sel.member_colleges, sel.sector_socs, spec=sel.spec)
    assert mcp == canonical, f"MCP member supply {mcp} diverges from canonical {canonical}"
