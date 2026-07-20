"""MCP server framing layer: the epistemic contract, verified structurally.

These tests pin the response-envelope invariants that make the MCP server
trustworthy rather than merely plausible — Bind (every fact is a QualifiedValue,
never a bare number), Gate (a non-ok status forces value None; an unresolved
coordinate returns an explicit marker), and Distinguish (supply and demand are
separate named keys — projected_supply from DataMart, annual_openings from COE) —
plus provenance never
invented (source read from the engine's lens map), the deterministic view-link
mapping, the catalog adjacency edges, and byte-stable serialization. The
graph-free tests always run; the four adapters run against the live graph when
NEO4J_URI is reachable and skip otherwise.

Coverage:
  - QualifiedValue.gated forces value None (Gate)
  - provenance.q attaches source from lens.FIELD_AUTHORITY and never invents one
  - supply and demand are Distinguished as separate keys (projected_supply vs annual_openings)
  - the four supply/gap tools agree at a coordinate (cross-tool referential integrity)
  - scope_catalog degrades to the 23 pinned instances without a graph
  - view_link maps each form to the right pinned/generated route + lens
  - build_next_moves emits the catalog adjacency edges, carrying soc/top6
  - gate_envelope routes an unresolved coordinate back to Tier 0
  - an AnalysisEnvelope serializes byte-identically twice (determinism)
  - [graph] analyze_gap/coverage/pathway/regional_employers over svamp + smccd-adm:
    Bind (recursive), Distinguish, view_link route, next_moves re-validate,
    and byte-identical determinism
  - [graph] unmet_demand greenfield invariant: every surfaced occupation has member
    supply == 0 (verified independently through CAN.supply) AND clears the quality gate
    (CC-servable education, wage ≥ $50k, ≥ 100 openings/yr), ranked by annual openings
"""
from __future__ import annotations

import os

import pytest

from mcp_server import canonical as CAN
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
    assert P.q("projected_supply", 8.0, granularity="inst").source == "datamart"
    # an unmapped field yields an empty source — surfaced, never guessed
    assert P.q("nonexistent_field", 1, granularity="x").source == ""


def test_distinguish_supply_from_demand():
    """Distinguish (post-collapse): supply is ONE measure (projected_supply, 3-yr-avg DataMart
    completions) and demand (annual_openings) is a separate named key with a DIFFERENT source
    (COE) — the schema never merges the two, so the model can never read supply as demand or
    vice-versa. (The former latest_year_supply / actual_awards split is gone: supply is one
    number now.)"""
    assert P.q("projected_supply", 12.0, granularity="inst").source == "datamart"
    assert P.q("annual_openings", 340, granularity="regional").source == "coe"


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
    # A next-move's `form` is the VERB the model routes to; the coordinate carries the entity/lens the
    # verb dispatches on. gap → regional_employers (navigate·employers lens) + pathway (crosswalk), both
    # carrying the soc; coverage → pathway (crosswalk) carrying the top6 as the entity.
    moves = {m.form: m for m in C.build_next_moves("gap", entry, soc="49-9041")}
    assert moves["navigate"].coordinate.lens == "employers" and moves["navigate"].coordinate.entity == "49-9041"
    assert moves["navigate"].coordinate.soc == "49-9041"
    assert moves["crosswalk"].coordinate.entity == "49-9041"
    cov = {m.form: m for m in C.build_next_moves("coverage", entry, top6="095000")}
    assert cov["crosswalk"].coordinate.top6 == "095000" and cov["crosswalk"].coordinate.entity == "095000"


def test_gate_envelope_routes_to_tier0():
    env = S.gate_envelope("gap", "bogus", "adm", reason="unknown member")
    assert env.licensing.gates[0].marker == "out-of-scope"
    assert {m.form for m in env.next_moves} == {"orient", "list_institutions"}
    assert not env.data.summary            # Gate ⇒ no data


def test_next_moves_name_callable_tools():
    """Routing integrity — the sibling of cross-tool value integrity. Every next-move names
    a tool the model can actually call; internal form-ids like "gap"/"coverage"/"orient" are
    NOT their registered tool names, so every construction site must translate.
    Guards the exact break behind the live 'Unknown tool' snag. Skips where the mcp SDK
    (server registration) isn't importable."""
    try:
        import asyncio
        from mcp_server.server import mcp
    except ModuleNotFoundError:
        pytest.skip("mcp SDK not installed")
    registered = {t.name for t in asyncio.run(mcp.list_tools())}
    # During the additive verb migration the 5 coordinate-algebra verbs are registered but are NOT
    # next-move targets (next_moves still name the legacy tools), so the map's targets must all be
    # registered (⊆), not equal. Post-Phase-5 (legacy tools retired) this returns to ==.
    assert set(C.TOOL_NAME.values()) <= registered, "a TOOL_NAME target is not a registered tool"
    entry = next(e for e in S.scope_catalog() if e["id"] == "svamp")
    for cur in C.EDGES:                    # every adjacency edge's target is callable
        for mv in C.build_next_moves(cur, entry, soc="49-9041", top6="095000"):
            assert mv.form in registered, f"{cur} next-move names non-tool {mv.form!r}"
    gate = S.gate_envelope("gap", "bogus", "adm", reason="x")   # the Tier-0 recovery route
    assert {mv.form for mv in gate.next_moves} <= registered
    for cur in ("gap", "coverage", "pathway"):   # the progressive-disclosure drill is a call target too
        assert F._drill(cur, entry, remaining=9).drill.form in registered, f"{cur} drill names non-tool"


def test_envelope_serializes_deterministically():
    env = AnalysisEnvelope(form="gap", coordinate=Coordinate(member="svamp"))
    assert env.model_dump_json() == env.model_dump_json()


# The retired framing the All-Awards migration replaced: supply IS DataMart completions
# (All Awards) on COE's projection method, so nothing may resurrect the 'projected COE vs
# actual DataMart' contradiction or the earlier CO-approved scope. Static strings here;
# the rendered-licensing counterpart is a graph test below.
_RETIRED_SUPPLY_FRAMING = ("not actual DataMart awards", "CO-approved", "excludes locally-approved")


def test_no_retired_supply_framing_in_catalog():
    statics = [f.guardrail for f in C.FORMS.values()] + [
        C.SAL_PROJECTED_NOT_ACTUAL, C.SAL_MEMBER_ANCHORED, C.SAL_LOSSY_CROSSWALK,
        C.SAL_SMALL_N, C.SAL_STALE_VINTAGE]
    for s in statics:
        for phrase in _RETIRED_SUPPLY_FRAMING:
            assert phrase not in s, f"retired supply framing {phrase!r} in: {s!r}"


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
    # Distinguish: regional supply and the member's share are separate keys (both DataMart
    # completions via the canonical resolver). Grain: the gap denominator is REGIONAL, so
    # regional supply always covers ≥ the member share.
    assert env.data.summary["regional_supply"].source == "datamart"
    assert env.data.summary["member_supply"].source == "datamart"
    assert env.data.summary["regional_supply"].value >= env.data.summary["member_supply"].value
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

    shed = F.analyze_regional_employers(member, sector)
    assert shed.form == "regional_employers"
    assert_bound(shed)
    assert "lens=employers" in shed.view_link.url


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_navigable_forms_link_and_fresh_licensing(member, sector):
    """Navigation + licensing-freshness invariant. Every form with a corroborating dashboard
    view returns view_link.status == 'ok' with a URL — the deep-link DOCTRINE tells the model to
    offer — and no rendered licensing string resurrects the retired supply framing. unmet_demand
    alone has no single view and is 'unavailable' (pinned in its own greenfield test)."""
    for env in (F.sector_overview(member, sector),
                F.analyze_gap(member, sector),
                F.analyze_coverage(member, sector),
                F.analyze_regional_employers(member, sector)):
        assert env.view_link.status == "ok" and env.view_link.url, env.form
        for s in env.licensing.licensed + env.licensing.not_licensed:
            assert not any(p in s for p in _RETIRED_SUPPLY_FRAMING), \
                f"retired framing in {env.form} licensing: {s!r}"


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_sector_overview_adapter(member, sector):
    """The sector-anchor orientation view — sector-WIDE Regime-A aggregate. Not member-anchored:
    it never gates on an empty portfolio, and its totals are plain sums — regional supply ≥ the
    member's share, and the sector gap = regional demand − regional supply, exactly."""
    env = F.sector_overview(member, sector)
    assert env.form == "sector_overview" and not env.licensing.gates
    assert_bound(env)
    s = env.data.summary
    assert s["regional_supply"].value >= s["member_supply"].value          # member ⊆ region
    assert s["gap"].value == int(round(s["regional_demand"].value - s["regional_supply"].value))
    if s["member_share_of_supply"].status == "ok":
        assert 0 <= s["member_share_of_supply"].value <= 1
    # the two sides are never conflated: supply is DataMart, demand is COE
    assert s["regional_supply"].source == "datamart" and s["regional_demand"].source == "coe"
    # PROGRAM-FORWARD: rows are the member's programs, each with its addressable demand
    for r in env.data.rows:
        assert {"member_supply", "addressable_demand", "occupations_fed"} <= set(r.values), r.label


@requires_graph
def test_program_addressable_demand_integrity():
    """The same program's addressable demand is ONE number across sector_overview and pathway —
    both resolve the program's occupations through the canonical crosswalk (CAN.program_socs), not
    a sibling resolver, so the program view can never drift between the two tools."""
    m, sec = "svamp", "adm"
    so = F.sector_overview(m, sec)
    if not so.data.rows:
        pytest.skip("no programs in the fixture sector")
    top6 = so.data.rows[0].label.split()[0]
    so_addr = so.data.rows[0].values["addressable_demand"].value
    pw = F.analyze_pathway(m, sec, program=top6)
    assert pw.data.summary["addressable_demand"].value == so_addr, (
        f"{top6} addressable demand drifts: sector_overview={so_addr} "
        f"pathway={pw.data.summary['addressable_demand'].value}")


@requires_graph
@pytest.mark.parametrize("member", ["svamp", "smccd"])
def test_member_portfolio_adapter(member):
    """The member-anchor orientation — the whole institution across every sector in ONE call, so a
    portfolio question never loops a sector tool. Rows = sectors; institution-wide totals are
    Regime-A sums over the DEDUPED union of the member's sectors' occupations. No single dashboard
    corroborates a cross-sector portfolio, so view_link is 'unavailable' (like unmet_demand)."""
    env = F.member_portfolio(member)
    assert env.form == "member_portfolio" and not env.licensing.gates
    assert_bound(env)
    s = env.data.summary
    assert s["gap"].value == int(round(s["regional_demand"].value - s["regional_supply"].value))
    assert s["regional_supply"].value >= s["member_supply"].value
    assert s["sectors"].value == len(env.data.rows)          # one row per sector, no loop
    assert env.view_link.status == "unavailable" and env.view_link.url is None
    assert s["regional_supply"].source == "datamart" and s["regional_demand"].source == "coe"


@requires_graph
def test_entity_forms_view_link_ok():
    """pathway + occupation_profile also corroborate to a dashboard view — pinned via the
    referential-integrity fixture (deanza/adm/51-4041) where a valid occupation resolves."""
    m, sec, soc = "deanza", "adm", "51-4041"
    for env in (F.analyze_pathway(m, sec, occupation=soc), F.occupation_profile(m, soc)):
        assert env.view_link.status == "ok" and env.view_link.url, env.form


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


@requires_graph
def test_empty_member_sector_gates_not_zero():
    """A member with no active program in a sector (SMCCD / agriculture) must GATE with an explicit
    marker — never a 0-readable 'no demand'. The Bay has ag/water/environmental demand, but this
    member-anchored view is scoped to what SMCCD serves — and its peninsula colleges run no ACTIVE
    (recent completers OR enrollment) agriculture program — so it must SAY so, not report gap=0.
    (SMCCD / business is NO LONGER the empty example: the P2 home_sector read-swap correctly recovered
    its Accounting / Business Administration / Real Estate programs that the old excluded_tops machinery
    had masked — so it now reads as active, which is why this pins agriculture instead.)"""
    for fn, name in ((F.analyze_gap, "gap"), (F.analyze_coverage, "coverage")):
        env = fn("smccd", "agwet")
        g = env.licensing.gates
        assert g and g[0].marker == "unavailable" and "greenfield" in g[0].reason, name
        assert not env.data.summary, f"{name} returned zero-filled data instead of a gate"
        assert {m.form for m in env.next_moves} <= {"orient"}


@requires_graph
def test_cross_tool_referential_integrity():
    """Referential integrity — the gate-tests' sibling. A named quantity at a resolved
    coordinate is ONE value no matter which tool serves it, and gap = regional_demand −
    regional_supply everywhere. Fixture: deanza/adm/51-4041, the divergence that motivated
    the canonical resolver (was gap 440 / pathway 458 / occupation_profile −3972)."""
    m, sec, soc = "deanza", "adm", "51-4041"
    g = F.analyze_gap(m, sec, soc=soc).data.rows[0].values
    p = F.analyze_pathway(m, sec, occupation=soc).data.summary
    o = F.occupation_profile(m, soc).data.summary
    # (a) same-named quantities are value-identical across every tool that serves them
    for key in ("member_supply", "regional_supply", "gap"):
        vals = {g[key].value, p[key].value, o[key].value}
        assert len(vals) == 1, f"{key} disagrees across tools: {vals}"
    # (b) regional demand agrees too — the gap/pathway framing names it regional_demand,
    #     the occupation_profile raw-demand vector names it annual_openings: one number.
    demand = lambda d: (d.get("regional_demand") or d["annual_openings"]).value
    assert len({demand(g), demand(p), demand(o)}) == 1, "regional demand disagrees across tools"
    # (c) gap = regional demand − regional supply, exactly, in every tool
    for v in (g, p, o):
        assert v["gap"].value == int(round((demand(v) or 0) - v["regional_supply"].value))
    # (d) all supply resolves through the one canonical DataMart source
    assert {g["regional_supply"].source, p["regional_supply"].source,
            o["regional_supply"].source} == {"datamart"}


@requires_graph
@pytest.mark.parametrize("member", ["svamp", "smccd"])
def test_unmet_demand_greenfield_invariant(member):
    """The greenfield invariant — the whole point of unmet_demand: every surfaced occupation is
    one the member's REGION demands but the member supplies ZERO completers for, re-verified
    independently through the canonical resolver (CAN.supply == 0), AND clears the quality gate
    (CC-servable education, wage ≥ $50k, ≥ 100 openings/yr). Proves the tool can never surface an
    occupation the member already serves, and never a below-threshold role."""
    env = F.unmet_demand(member)
    assert env.form == "unmet_demand" and not env.licensing.gates
    assert_bound(env)
    # coordinate: member echoed, region derived, no soc (a region-wide list, not one occupation)
    assert env.coordinate.member == member and env.coordinate.region and env.coordinate.soc is None
    # no dashboard corroborates a region-wide greenfield list — an honest 'unavailable' marker,
    # never a fabricated link
    assert env.view_link.status == "unavailable" and env.view_link.url is None
    # resolve the member's colleges the SAME way the form does, to re-verify supply independently
    sects = S.sectors_for_member(member)
    spec0, _ = S.scope_for(member, sects[0]["sector_id"])
    member_colleges = list(spec0.colleges)
    assert env.data.rows, "expected at least one greenfield occupation for the fixture members"
    for row in env.data.rows:
        soc = row.label.split()[0]
        # (a) greenfield: member supply is ZERO through the canonical resolver (the invariant)
        assert CAN.supply(member_colleges, soc) == 0, f"{soc} is NOT greenfield for {member}"
        # (b) the row states that zero too (Distinguish: it's projected_supply, member share)
        assert row.values["member_supply"].value == 0
        # (c) quality gate: living-wage, meaningful-demand, CC-servable education
        assert row.values["annual_wage"].value >= F._WAGE_FLOOR
        assert row.values["annual_openings"].value >= F._OPENINGS_FLOOR
        assert row.values["typical_education"].value in F._CC_SERVABLE_EDUCATION
        # (d) not a promotion role — a CC can't launch a program for supervisor/manager SOCs, so
        # greenfield never suggests a curriculum that can't exist (same exclusion as the gap view)
        from partnerships.sectors import PROMOTION_SOCS
        assert soc not in PROMOTION_SOCS, f"{soc} is a promotion role, not a greenfield opportunity"
    # ranked by annual openings (descending), median wage breaks ties — the decomposed NAMED axis,
    # not a hidden openings×wage "opportunity" product; the axis is also named structurally.
    assert env.data.sorted_by and env.data.sorted_by.key == "annual_openings"
    ranks = [(r.values["annual_openings"].value, r.values["annual_wage"].value) for r in env.data.rows]
    assert ranks == sorted(ranks, reverse=True)
    # n_unmet is the pre-truncation count; the top-N rows never exceed it
    assert env.data.summary["n_unmet"].value >= len(env.data.rows)
    # provenance carried once, spanning demand (coe) + supply (datamart)
    assert {s.id for s in env.provenance.sources} >= {"coe", "datamart"}
    # the next-move drills into a surfaced occupation via navigate(entity=<soc>) — sector-agnostic,
    # so the occupation view resolves (no sector on the coordinate)
    assert any(m.form == "navigate" and m.coordinate.entity and not m.coordinate.sector
               for m in env.next_moves)


@requires_graph
def test_offering_referential_integrity():
    """Defect-1 sibling for `colleges_offering`: a supporting program's college count agrees
    across tools, and no count is emitted without a nameable roster. BACCC == the Bay region,
    so occupation_profile (regional) and program_pathways (consortium) must show the SAME
    supporting programs + counts for a SOC; program_coverage's row for that TOP must match too."""
    soc, top = "29-1141", "123010"
    o = {r.label.split()[0]: r for r in F.occupation_profile("baccc", soc).data.rows}
    p = {r.label.split()[0]: r for r in F.analyze_pathway("baccc", "health", occupation=soc).data.rows}
    c = {r.label.split()[0]: r for r in F.analyze_coverage("baccc", "health").data.rows}
    # (1) same supporting-program TOP set for the SOC (the 123000 divergence is gone)
    assert set(o) == set(p), f"supporting programs disagree: {set(o)} vs {set(p)}"
    assert top in o and top in c
    cwp = lambda row: row.values["colleges_with_program"].value
    assert cwp(o[top]) == cwp(p[top]) == cwp(c[top]), "colleges_with_program disagrees across tools"
    # (2) no count without a nameable set — a roster is present and never exceeds the total
    for row in (o[top], p[top], c[top]):
        assert row.roster, "a count was emitted with no roster"
        assert 0 < len(row.roster) <= cwp(row)
        assert all(cell.values["projected_supply"].value is not None for cell in row.roster)  # never dropped
    # (3) the roster's projected supply reconciles with the aggregate within projection
    # rounding — each per-college figure rounds to 0.1 and the aggregate rounds once, so the
    # sums agree up to accumulated rounding; the point is no college is silently dropped.
    from mcp_server import canonical as CAN
    from partnerships.members import region_member
    from partnerships.resolve import resolve
    cols = region_member(resolve(S.scope_for("baccc", "health")[0]).resolve_region()).colleges
    full = CAN.college_roster(cols, top)
    roster_sum = sum(cell.projected for cell in full)
    assert abs(roster_sum - p[top].values["projected_supply"].value) <= 0.1 * len(full) + 0.1
