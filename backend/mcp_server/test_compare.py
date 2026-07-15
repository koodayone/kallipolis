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
    fires before any graph resolution, so this is graph-free. Bare 'wage' is deliberately NOT a
    criterion (wage is split into wage_lift / wage_after_2 / wage_after_5), so it still gates and the
    reason enumerates the real menu — no silent guess at which wage figure the caller meant."""
    e1 = F.compare("svamp", unit_type="widget", criterion="x", sector="adm")
    assert e1.licensing.gates and "widget" in e1.licensing.gates[0].reason
    e2 = F.compare("svamp", unit_type="program", criterion="wage", sector="adm")
    assert e2.licensing.gates and "addressable_demand" in e2.licensing.gates[0].reason


# ── graph: the per-criterion battery ───────────────────────────────────────

def _oracle(unit_type, criterion, ctx, uid):
    """Recompute a value from raw CAN.* WITHOUT calling ``criterion.compute`` — an independent
    re-derivation, so a mis-wired compute callable (e.g. member↔region colleges) is caught. Keyed by
    (unit_type, criterion) because a criterion key (supply_share) can live on more than one unit."""
    m, r = ctx.member_colleges, ctx.region_colleges

    if unit_type == "program":
        top6 = uid
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
        if criterion in ("wage_lift", "wage_after_2", "wage_after_5"):
            # The wage oracle reads the CSV (get_wage_outcomes) — the ORIGINAL source, independent
            # of the ProgramWageOutcome graph nodes the criterion resolves through — so this also
            # cross-checks the loader's CSV→graph fidelity, not just the compute wiring. The
            # recipient-cohort selection MIRRORS partnerships.quantities._wage_selection_key.
            from ontology.programs import get_wage_outcomes
            recs = get_wage_outcomes(top6)
            if not recs:
                return None
            w = sorted(recs, key=lambda x: (-(x["n"] or 0), -(x["wage_after_2"] or 0),
                                            x["recipient_type"] or ""))[0]
            if criterion == "wage_after_2":
                return w["wage_after_2"]
            if criterion == "wage_after_5":
                return w["wage_after_5"]
            if w["wage_before"] is None or w["wage_after_2"] is None:
                return None
            return w["wage_after_2"] - w["wage_before"]

    if unit_type == "occupation":
        soc, f = uid, ctx.soc_facts.get(uid, {})
        if criterion == "regional_openings":
            return f.get("annual_openings")
        if criterion == "median_wage":
            return f.get("annual_wage")
        if criterion == "projected_growth":
            return f.get("growth_rate")
        if criterion == "regional_employment":
            return f.get("employment")
        if criterion == "regional_supply":
            return CAN.supply(r, soc)
        if criterion == "supply_gap":
            return CAN.gap(f.get("annual_openings"), CAN.supply(r, soc))
        if criterion == "member_supply_share":
            reg = CAN.supply(r, soc)
            return round(CAN.supply(m, soc) / reg, 3) if reg else None

    if unit_type == "college":
        col = uid
        if criterion == "sector_supply":
            return CAN.supply_over_socs([col], ctx.sector_socs)
        if criterion == "supply_share":
            reg = CAN.supply_over_socs(r, ctx.sector_socs)
            return round(CAN.supply_over_socs([col], ctx.sector_socs) / reg, 3) if reg else None
        if criterion == "sector_enrollment":
            return CAN.enrollment_over_tops([col], ctx.sector_tops)

    raise KeyError((unit_type, criterion))


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
@pytest.mark.parametrize("unit_type,criterion", _CRITERIA)
def test_criterion_battery(unit_type, criterion, member, sector):
    env = F.compare(member, unit_type=unit_type, criterion=criterion, sector=sector)
    if env.licensing.gates:
        pytest.skip(f"no comparable {unit_type}s for ({member}, {sector})")
    rows = env.data.rows
    assert rows, "empty comparison"
    assert env.data.sorted_by and env.data.sorted_by.key == criterion, "sort axis not named structurally"
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
    uid = rows[0].label if unit_type == "college" else rows[0].label.split()[0]
    assert rows[0].values[criterion].value == _oracle(unit_type, criterion, ctx, uid)

    # Law / bounds per criterion.
    for row in rows:
        v = row.values[criterion].value
        if v is None:
            continue
        if criterion in ("supply_share", "member_supply_share"):
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
@pytest.mark.parametrize("member,sector", _COORDS)
def test_referential_integrity_occupation_with_gap(member, sector):
    """An occupation's regional supply and gap are ONE value across compare and supply_demand_gaps —
    for any occupation the member serves, the sector-wide comparison and the member gap view agree,
    because both resolve through the same canonical CAN.supply / CAN.gap."""
    cmp_env = F.compare(member, unit_type="occupation", criterion="supply_gap", sector=sector)
    if cmp_env.licensing.gates:
        pytest.skip("no occupations in fixture")
    checked = 0
    for row in cmp_env.data.rows:
        soc = row.label.split()[0]
        gap = F.analyze_gap(member, sector, soc=soc)
        if not gap.data.rows:
            continue    # the member feeds no program into this occupation — not in the member gap view
        gr = gap.data.rows[0]
        assert row.values["regional_supply"].value == gr.values["regional_supply"].value
        assert row.values["supply_gap"].value == gr.values["gap"].value
        checked += 1
    if checked == 0:
        pytest.skip("no occupation shared between the sector-wide compare and the member gap view")


@requires_graph
def test_gap_soc_query_never_bare_summary():
    """For a soc-filtered gap query, the response is either a member-anchored ROW (member serves the
    occupation) or a GATE routing to occupation_profile (member doesn't) — NEVER a served-sector
    summary under the occupation's coordinate. The misread Tier C caught: supply_demand_gaps(smccd,
    adm, 51-4041) had returned the sector aggregate 422 as the machinists gap."""
    env = F.analyze_gap("smccd", "adm", soc="51-4041")   # smccd serves adm; may not serve machinists
    if env.licensing.gates:                               # unserved → gated, no misleading summary
        assert not (env.data and env.data.summary), "a gated occupation must not ship a sector summary"
        assert any(nm.form == "occupation_profile" for nm in env.next_moves), "gate must route to occupation_profile"
    else:                                                 # served → a real occupation row, not a bare summary
        assert env.data and env.data.rows, "a soc query that isn't gated must return the occupation's row"


@requires_graph
@pytest.mark.parametrize("member,sector", _COORDS)
def test_college_sector_supply_is_conservative(member, sector):
    """Per-college sector supply is conservative: every region college's sector completions sum to
    the region's total — so a college's figure is a real slice of the region, not a reimplementation."""
    env = F.compare(member, unit_type="college", criterion="sector_supply", sector=sector)
    if env.licensing.gates:
        pytest.skip("no colleges in fixture")
    ctx = CMP.build_context(member, sector)
    total = sum(CAN.supply_over_socs([c], ctx.sector_socs) for c in ctx.region_colleges)
    region = CAN.supply_over_socs(ctx.region_colleges, ctx.sector_socs)
    # per-college rounding of the 3-yr average accumulates; conservation holds within a completion
    assert abs(total - region) < 1.0


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
