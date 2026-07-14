"""The comparison engine — the registry-parametrized eval battery.

Every ``(unit_type, criterion)`` in the registry inherits this battery, so a criterion cannot ship
until it passes. That is what makes a *ranking* defensible: each figure is recomputable from raw
canonical primitives, identical across tools, bound to a named authority, correctly ordered, and free
of hidden composites. The battery grows with the registry, not with hand-written per-criterion tests.
"""
from __future__ import annotations

import os

import pytest

from mcp_server import canonical as CAN
from mcp_server import compare as CMP
from mcp_server import forms as F
from mcp_server.envelope import QualifiedValue


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
_CRITERIA = [(ut, c) for ut in CMP.REGISTRY for c in CMP.REGISTRY[ut]]


# ── graph-free: the admissibility invariant (the composite-trap gate) ──────

def test_no_composite_criterion():
    """The no-composite rule, structurally: no registered criterion is a composite, and none binds to
    a field (annual_wage, growth_rate) that would only exist here by weight-averaging a finer grain —
    so the superseded score can never re-enter the registry through data entry."""
    for ut, crits in CMP.REGISTRY.items():
        for c in crits.values():
            assert not c.composite, f"{ut}.{c.key} is a composite"
            assert c.field not in {"annual_wage", "growth_rate"}, f"{ut}.{c.key} binds a weight-averaged field"


def test_register_rejects_composite():
    """_register raises on a composite criterion — the guard is at construction, not only tested."""
    bad = CMP.Criterion("x", "X", "u", "annual_wage", True, True, "inst", lambda ctx, u: 1)
    with pytest.raises(ValueError):
        CMP._register({"x": bad})


def test_compare_gates_unknown():
    """Unknown unit_type / criterion returns an explicit marker enumerating the registry — the gate
    fires before any graph resolution, so this is graph-free."""
    e1 = F.compare("svamp", unit_type="widget", criterion="x", sector="adm")
    assert e1.licensing.gates and "widget" in e1.licensing.gates[0].reason
    e2 = F.compare("svamp", unit_type="program", criterion="wage", sector="adm")
    assert e2.licensing.gates and "addressable_demand" in e2.licensing.gates[0].reason


# ── graph: the per-criterion battery ───────────────────────────────────────

def _oracle(criterion, ctx, top6):
    """Recompute a value from raw CAN.* WITHOUT calling ``criterion.compute`` — an independent
    re-derivation, so a mis-wired compute callable (e.g. member↔region colleges) is caught."""
    m, r = ctx.member_colleges, ctx.region_colleges
    if criterion == "addressable_demand":
        return CAN.addressable_demand(top6, ctx.sector_socs, ctx.demand_by_soc)[1]
    if criterion == "addressable_gap":
        socs = CAN.program_socs(top6, within=ctx.sector_socs)
        return CAN.gap(CAN.addressable_demand(top6, ctx.sector_socs, ctx.demand_by_soc)[1],
                       CAN.supply_over_socs(r, socs))
    if criterion == "completions":
        return CAN.supply_over_tops(m, [top6])
    if criterion == "enrollment":
        return CAN.enrollment_over_tops(m, [top6])
    if criterion == "supply_share":
        reg = CAN.supply_over_tops(r, [top6])
        return round(CAN.supply_over_tops(m, [top6]) / reg, 3) if reg else None
    if criterion == "award_trend":
        base = CAN.supply_over_tops(m, [top6], years=ctx.recent_years)
        return round(CAN.supply_over_tops(m, [top6], years=ctx.latest_years) / base, 2) if base else None
    if criterion == "enrollment_trend":
        base = CAN.enrollment_over_tops(m, [top6], terms=ctx.enroll_recent)
        return round(CAN.enrollment_over_tops(m, [top6], terms=ctx.enroll_latest) / base, 2) if base else None
    raise KeyError(criterion)


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
@pytest.mark.parametrize("unit_type,criterion", _CRITERIA)
def test_criterion_battery(unit_type, criterion, member, sector):
    env = F.compare(member, unit_type=unit_type, criterion=criterion, sector=sector)
    if env.licensing.gates:
        pytest.skip(f"no comparable {unit_type}s for ({member}, {sector})")
    rows = env.data.rows
    assert rows, "empty comparison"
    c = CMP.REGISTRY[unit_type][criterion]

    # Bind + Gate: every leaf a QualifiedValue with granularity; ok ⇒ value + source; non-ok ⇒ None.
    for row in rows:
        for qv in row.values.values():
            assert isinstance(qv, QualifiedValue) and qv.granularity
            if qv.status == "ok":
                assert qv.value is not None and qv.source
            else:
                assert qv.value is None

    # Provenance / authority-trace: the chosen criterion's field is in field_authority.
    assert c.field in env.provenance.field_authority

    # Ranking monotonicity: consecutive ok rows respect higher_is_better; gated rows sort last.
    seen_gated, prev = False, None
    for row in rows:
        v = row.values[criterion].value
        if v is None:
            seen_gated = True
            continue
        assert not seen_gated, "an ok row follows a gated row"
        if prev is not None:
            assert (v <= prev) if c.higher_is_better else (v >= prev), "ranking not monotonic"
        prev = v

    # Computation correctness: rows[0]'s value equals the independent oracle.
    ctx = CMP.build_context(member, sector)
    top6 = rows[0].label.split()[0]
    assert rows[0].values[criterion].value == _oracle(criterion, ctx, top6)

    # Law / bounds per criterion.
    for row in rows:
        v = row.values[criterion].value
        if v is None:
            continue
        if criterion == "supply_share":
            assert 0.0 <= v <= 1.0
        if criterion.endswith("_trend"):
            assert v >= 0   # a ratio of non-negative quantities; 0.0 = the latest period collapsed to zero
        if criterion == "addressable_gap":
            t6 = row.label.split()[0]
            socs = CAN.program_socs(t6, within=ctx.sector_socs)
            assert v == CAN.gap(CAN.addressable_demand(t6, ctx.sector_socs, ctx.demand_by_soc)[1],
                                CAN.supply_over_socs(ctx.region_colleges, socs))


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_referential_integrity_with_sector_overview(member, sector):
    """A program's addressable_demand and completions are ONE value across compare and
    sector_overview — both resolve through the same canonical functions, never a sibling
    reimplementation, so the program view can't drift between the two tools."""
    cmp_env = F.compare(member, unit_type="program", criterion="addressable_demand", sector=sector)
    so = F.sector_overview(member, sector)
    if cmp_env.licensing.gates or not so.data.rows:
        pytest.skip("no programs in fixture")
    cmp_vals = {r.label.split()[0]: (r.values["addressable_demand"].value, r.values["completions"].value)
                for r in cmp_env.data.rows}
    for r in so.data.rows:
        t6 = r.label.split()[0]
        if t6 in cmp_vals:
            assert cmp_vals[t6][0] == r.values["addressable_demand"].value
            assert cmp_vals[t6][1] == r.values["member_supply"].value


@requires_graph
def test_compare_view_link_unavailable():
    """A comparison has no single dashboard view — view_link is 'unavailable', never a broken link."""
    env = F.compare("svamp", unit_type="program", criterion="completions", sector="adm")
    assert env.view_link.status == "unavailable" and env.view_link.url is None


@requires_graph
def test_compare_determinism():
    a = F.compare("svamp", "program", "addressable_gap", "adm").model_dump_json()
    b = F.compare("svamp", "program", "addressable_gap", "adm").model_dump_json()
    assert a == b
