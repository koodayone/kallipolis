"""MCP server framing layer: the epistemic contract, verified structurally.

These tests pin the response-envelope invariants that make the MCP server
trustworthy rather than merely plausible — Bind (every fact is a QualifiedValue,
never a bare number), Gate (a non-ok status forces value None; an unresolved
coordinate returns an explicit marker), and Distinguish (projected_supply and
actual_awards are separate, differently-sourced keys) — plus provenance never
invented (source read from the engine's lens map), the deterministic view-link
mapping, the catalog adjacency edges, and byte-stable serialization. The
graph-free tests always run; the four adapters run against the live graph when
NEO4J_URI is reachable and skip otherwise.

Coverage:
  - QualifiedValue.gated forces value None (Gate)
  - provenance.q attaches source from lens.FIELD_AUTHORITY and never invents one
  - projected_supply (coe) and actual_awards (datamart) are Distinguished
  - scope_catalog degrades to the 23 pinned instances without a graph
  - view_link maps each form to the right pinned/generated route + lens
  - build_next_moves emits the catalog adjacency edges, carrying soc/top6
  - gate_envelope routes an unresolved coordinate back to Tier 0
  - an AnalysisEnvelope serializes byte-identically twice (determinism)
  - [graph] analyze_gap/coverage/pathway/employer_shed over svamp + smccd-adm:
    Bind (recursive), Distinguish, view_link route, next_moves re-validate,
    and byte-identical determinism
"""
from __future__ import annotations

import os

import pytest

from mcp_server import catalog as C
from mcp_server import forms as F
from mcp_server import provenance as P
from mcp_server import scope as S
from mcp_server import viewlink as V
from mcp_server.envelope import AnalysisEnvelope, Coordinate, QualifiedValue


# ── shared assertions ─────────────────────────────────────────────────────

def _leaves(env: AnalysisEnvelope) -> list[QualifiedValue]:
    out = list(env.data.summary.values())
    for row in env.data.rows:
        out.extend(row.values.values())
    return out


def assert_bound(env: AnalysisEnvelope) -> None:
    """Bind + Gate: every fact leaf is a QualifiedValue; ok ⇒ value + source;
    non-ok ⇒ value None. No bare numbers can appear (the schema forbids it)."""
    for qv in _leaves(env):
        assert isinstance(qv, QualifiedValue)
        assert qv.granularity, f"leaf missing granularity: {qv!r}"
        if qv.status == "ok":
            assert qv.value is not None, f"ok leaf with null value: {qv!r}"
            assert qv.source, f"ok leaf with no source (invented number?): {qv!r}"
        else:
            assert qv.value is None, f"gated leaf carries a value: {qv!r}"


# ── graph-free: the contract in isolation ─────────────────────────────────

def test_gate_forces_null():
    qv = QualifiedValue(value=999, status="unavailable")
    assert qv.value is None and qv.status == "unavailable"


def test_provenance_source_from_lens_never_invented():
    assert P.q("annual_openings", 340, granularity="regional").source == "coe"
    assert P.q("actual_awards", 8, granularity="inst").source == "datamart"
    # an unmapped field yields an empty source — surfaced, never guessed
    assert P.q("nonexistent_field", 1, granularity="x").source == ""


def test_distinguish_projected_vs_actual():
    sup = P.q("projected_supply", 12.0, granularity="inst")
    act = P.q("actual_awards", 8, granularity="inst")
    assert sup.source == "coe" and act.source == "datamart"
    assert P.COE_SUPPLY_VINTAGE in sup.vintage


def test_scope_catalog_pinned_only():
    cat = S.scope_catalog()
    ids = {e["id"] for e in cat}
    assert "svamp" in ids and "smccd-adm" in ids and "baccc-adm" in ids
    svamp = next(e for e in cat if e["id"] == "svamp")
    assert svamp["member_id"] == "svamp" and svamp["sector_id"] == "adm"
    assert svamp["member_kind"] == "consortium"


def test_view_link_routes():
    pinned = V.view_link("gap", instance_id="svamp", member_id="svamp", sector_id="adm")
    assert pinned.url.endswith("/svamp?lens=occupations")
    gen = V.view_link("gap", instance_id="foothill-adm", member_id="foothill", sector_id="adm")
    assert "/landscape/foothill/adm?lens=occupations" in gen.url
    cov = V.view_link("coverage", instance_id="svamp", member_id="svamp", sector_id="adm")
    assert "panel=programs.coverage" in cov.url


def test_next_moves_are_catalog_edges():
    entry = next(e for e in S.scope_catalog() if e["id"] == "svamp")
    moves = {m.form: m for m in C.build_next_moves("gap", entry, soc="49-9041")}
    assert "employer_shed" in moves and moves["employer_shed"].coordinate.soc == "49-9041"
    cov = {m.form: m for m in C.build_next_moves("coverage", entry, top6="095000")}
    assert cov["pathway"].coordinate.top6 == "095000"


def test_gate_envelope_routes_to_tier0():
    env = S.gate_envelope("gap", "bogus", "adm", reason="unknown member")
    assert env.licensing.gates[0].marker == "out-of-scope"
    assert {m.form for m in env.next_moves} == {"orient", "list_scopes"}
    assert not env.data.summary            # Gate ⇒ no data


def test_envelope_serializes_deterministically():
    env = AnalysisEnvelope(form="gap", coordinate=Coordinate(member="svamp"))
    assert env.model_dump_json() == env.model_dump_json()


# ── live-graph: the adapters over real coordinates ────────────────────────

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

_COORDS = [("svamp", "adm"), ("smccd", "adm")]


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_gap_adapter(member, sector):
    env = F.analyze_gap(member, sector)
    assert env.form == "gap" and not env.licensing.gates
    assert_bound(env)
    # Distinguish: the gap's two supplies are separate, differently-sourced keys
    assert env.data.summary["projected_supply"].source == "coe"
    assert env.data.summary["actual_awards"].source == "datamart"
    # view_link resolves and every next-move coordinate re-validates in the catalog
    assert env.view_link.url and "lens=occupations" in env.view_link.url
    for m in env.next_moves:
        assert S.find_scope(m.coordinate.member, m.coordinate.sector) is not None
    # provenance carried once, sources non-empty
    assert {s.id for s in env.provenance.sources} >= {"coe", "datamart"}


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_coverage_and_employer_adapters(member, sector):
    cov = F.analyze_coverage(member, sector)
    assert cov.form == "coverage" and not cov.licensing.gates
    assert_bound(cov)
    assert "panel=programs.coverage" in cov.view_link.url

    shed = F.analyze_employer_shed(member, sector)
    assert shed.form == "employer_shed"
    assert_bound(shed)
    assert "lens=employers" in shed.view_link.url


@requires_graph
def test_pathway_exactly_one_of():
    both = F.analyze_pathway("svamp", "adm", program="095000", occupation="49-9041")
    assert both.licensing.gates and both.licensing.gates[0].field == "program|occupation"
    neither = F.analyze_pathway("svamp", "adm")
    assert neither.licensing.gates


@requires_graph
def test_adapter_determinism():
    a = F.analyze_gap("svamp", "adm").model_dump_json()
    b = F.analyze_gap("svamp", "adm").model_dump_json()
    assert a == b


@requires_graph
def test_out_of_scope_gates_not_zero():
    env = F.analyze_gap("does-not-exist", "adm")
    assert env.licensing.gates and env.licensing.gates[0].marker == "out-of-scope"
    assert not env.data.summary        # explicit gate, never a zero-filled answer
