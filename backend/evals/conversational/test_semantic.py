"""Tier-C semantic eval — the coverage/sufficiency gate + functional checks of the
metamorphic runner and the per-transcript classification checks. Graph-free (no neo4j):
the checks import lazily and fall back, so this gates on every PR."""
from __future__ import annotations

from evals.conversational import semantic_checks as sc
from evals.conversational.semantic_pathways import SEMANTIC_PATHWAYS
from evals.conversational.pathways import ONBOARDING_PATHWAYS

TOOLS = {"orient", "navigate", "crosswalk", "compare", "list_institutions",
         "institution_overview", "member_portfolio", "sector_overview",
         "program_coverage", "program_pathways", "occupation_profile", "supply_demand_gaps",
         "unmet_demand", "regional_employers"}


# ── coverage / sufficiency (the algebra-coverage gate) ──
def test_every_probe_invariant_is_a_law():
    for p in SEMANTIC_PATHWAYS:
        assert p["invariant"] in sc.LAWS, p["id"]


def test_golden_forms_are_real_tools():
    for p in SEMANTIC_PATHWAYS:
        g = p.get("golden")
        if g:
            assert set(g["forms"]) <= TOOLS, p["id"]


def test_metamorphic_groups_are_complete_pairs():
    groups: dict[str, set] = {}
    for p in SEMANTIC_PATHWAYS:
        if p.get("metamorphic_group"):
            groups.setdefault(p["metamorphic_group"], set()).add(p["role"])
    assert groups, "expected at least one metamorphic group"
    for gid, roles in groups.items():
        assert roles == {"A", "B"}, (gid, roles)


def test_phase1_laws_have_coverage():
    exercised = {p["invariant"] for p in SEMANTIC_PATHWAYS}
    if ONBOARDING_PATHWAYS:
        exercised.add("establish_before")   # S7 reuse
    for name, law in sc.LAWS.items():
        if law["status"].startswith("phase-1"):
            assert name in exercised, name


def test_named_seams_have_probes():
    seams = {p["seam"] for p in SEMANTIC_PATHWAYS}
    assert {"two_demand", "grain_transitions"} <= seams
    assert ONBOARDING_PATHWAYS   # S7 establish-before-analyze


# ── functional: metamorphic runner ──
def _tx(pid, figs):
    return {"pathway_id": pid, "turns": [{"role": "analyst", "text": "...",
            "tool_calls": [{"name": "supply_demand_gaps", "args": {"member": "x"}, "figures": figs}]}]}


def test_regional_invariance_equal_passes():
    grp = {"A": _tx("a", {"imm_gap": 391}), "B": _tx("b", {"imm_gap": 391})}
    assert sc.run_group("g", "regional_invariance", grp)["pass"] is True


def test_regional_invariance_divergent_fails():
    grp = {"A": _tx("a", {"gap": 391}), "B": _tx("b", {"gap": 520})}
    assert sc.run_group("g", "regional_invariance", grp)["pass"] is False


def test_grain_nesting_college_le_district_passes():
    grp = {"A": _tx("skyline", {"member_supply": 72}), "B": _tx("smccd", {"member_supply": 200})}
    assert sc.run_group("g", "grain_nesting", grp)["pass"] is True


def test_grain_nesting_violation_fails():
    grp = {"A": _tx("skyline", {"member_supply": 200}), "B": _tx("smccd", {"member_supply": 72})}
    assert sc.run_group("g", "grain_nesting", grp)["pass"] is False


def test_group_incomplete_when_figure_missing():
    grp = {"A": _tx("a", {"gap": 391}), "B": _tx("b", {"unrelated": 5})}
    assert sc.run_group("g", "regional_invariance", grp)["pass"] is None  # capture gap, not a fail


def test_oracle_overrides_self_report():
    grp = {"A": _tx("a", {"gap": 999}), "B": _tx("b", {"gap": 111})}  # self-report would fail
    res = sc.run_group("g", "regional_invariance", grp, oracle=lambda role: 391)
    assert res["pass"] is True and res["detail"]["A"] == 391


# ── functional: per-transcript checks ──
def _turn(text, calls=None):
    return {"role": "analyst", "text": text, "tool_calls": calls or []}


def test_surfaced_both_demands_good():
    t = {"turns": [_turn("Across the full sector the region hires ~8,150; for the occupations you "
                         "already train for it's ~1,240.")]}
    assert sc.surfaced_both_demands(t)["pass"] is True


def test_surfaced_both_demands_conflated_fails():
    t = {"turns": [_turn("Demand for your sector is about 8,150 openings a year.")]}
    assert sc.surfaced_both_demands(t)["pass"] is False


def test_establish_order_orient_first_passes():
    t = {"turns": [_turn("Which institution?", [{"name": "list_institutions", "args": {}}]),
                   _turn("Here's the gap.", [{"name": "supply_demand_gaps", "args": {"member": "smccd"}}])]}
    assert sc.establish_order(t)["pass"] is True


def test_establish_order_analyze_first_fails():
    t = {"turns": [_turn("Here's the gap.", [{"name": "supply_demand_gaps", "args": {"member": "smccd"}}])]}
    assert sc.establish_order(t)["pass"] is False


def test_golden_traversal_form_and_direction():
    probe = {"golden": {"forms": ["supply_demand_gaps", "occupation_profile"], "grain": None,
                        "direction": "aggregate"}}
    t = {"turns": [_turn("...", [{"name": "mcp__x__supply_demand_gaps",
                                  "args": {"member": "smccd", "soc": "51-4041"}}])]}
    assert sc.golden_traversal(t, probe)["pass"] is True


def test_golden_traversal_wrong_form_fails():
    probe = {"golden": {"forms": ["supply_demand_gaps"], "grain": None, "direction": "aggregate"}}
    t = {"turns": [_turn("...", [{"name": "sector_overview", "args": {"member": "smccd"}}])]}
    assert sc.golden_traversal(t, probe)["pass"] is False


def test_coordinate_named():
    good = {"turns": [_turn("The regional gap is 391.", [{"name": "x", "figures": {"gap": 391}}])]}
    bad = {"turns": [_turn("The gap is 391.", [{"name": "x", "figures": {"gap": 391}}])]}
    assert sc.coordinate_named(good)["pass"] is True
    assert sc.coordinate_named(bad)["pass"] is False
