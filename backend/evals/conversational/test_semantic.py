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
    # A probe's invariant is a metamorphic/per-transcript LAW, or None for a pure-classification
    # probe (graded by golden_traversal + the judge, no cross-transcript relation to assert).
    for p in SEMANTIC_PATHWAYS:
        if p["invariant"] is not None:
            assert p["invariant"] in sc.LAWS, p["id"]


def test_classification_probes_carry_a_golden():
    # A probe with no metamorphic law must still be gradeable — it carries a golden traversal.
    for p in SEMANTIC_PATHWAYS:
        if p["invariant"] is None:
            assert p.get("golden"), p["id"]


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


def test_phase2_active_laws_have_coverage():
    # Flipping a law to "phase-2-active" makes the coverage gate REQUIRE a probe for it — the gate
    # that keeps the two new laws honest (a law with no probe cannot silently ship as "done").
    exercised = {p["invariant"] for p in SEMANTIC_PATHWAYS}
    for name, law in sc.LAWS.items():
        if law["status"].startswith("phase-2-active"):
            assert name in exercised, name


def test_named_seams_have_probes():
    seams = {p["seam"] for p in SEMANTIC_PATHWAYS}
    assert {"two_demand", "grain_transitions", "coordinate_identity", "forward_reverse",
            "absence_zero", "comparison_class", "non_summable", "form_topup"} <= seams
    assert ONBOARDING_PATHWAYS   # S7 establish-before-analyze


def test_form_topup_reaches_the_targeted_forms():
    # form → golden: every analytical form the plan targets appears in at least one golden traversal,
    # so no tool the practitioner can route to is left un-probed.
    covered = set()
    for p in SEMANTIC_PATHWAYS:
        if p.get("golden"):
            covered |= set(p["golden"]["forms"])
    want = {"occupation_profile", "compare", "program_pathways", "supply_demand_gaps",
            "sector_overview", "unmet_demand", "regional_employers", "member_portfolio"}
    assert want <= covered, want - covered


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


# ── functional: coordinate_identity (coordinate-AWARE metamorphic) ──
_GID = "coordinate_identity_openings_51-4041"


def _occ_tx(pid, soc, openings):
    """occupation_profile anchored on `soc`, reporting its openings."""
    return {"pathway_id": pid, "turns": [{"role": "analyst", "text": "...",
            "tool_calls": [{"name": "occupation_profile",
                            "args": {"member": "deanza", "occupation": soc},
                            "figures": {"annual_openings": openings}}]}]}


def _compare_row_tx(pid, soc, openings):
    """A compare(occupation, regional_openings) call whose per-SOC row names `soc`'s openings."""
    return {"pathway_id": pid, "turns": [{"role": "analyst", "text": "...",
            "tool_calls": [{"name": "compare",
                            "args": {"member": "deanza", "unit_type": "occupation",
                                     "criterion": "regional_openings", "sector": "adm"},
                            "figures": {f"{soc} Machinists regional_openings": openings,
                                        "51-9161 CNC programmers regional_openings": 210}}]}]}


def test_coordinate_identity_same_via_two_tools_passes():
    grp = {"A": _occ_tx("a", "51-4041", 510), "B": _compare_row_tx("b", "51-4041", 510)}
    assert sc.run_group(_GID, "coordinate_identity", grp)["pass"] is True


def test_coordinate_identity_divergent_fails():
    # B misroutes and reads the gap (466) as openings — a mis-scoped number at the same coordinate.
    grp = {"A": _occ_tx("a", "51-4041", 510), "B": _compare_row_tx("b", "51-4041", 466)}
    assert sc.run_group(_GID, "coordinate_identity", grp)["pass"] is False


def test_coordinate_identity_does_not_collide_with_two_demand():
    # Sector-grain demand (8,150 full vs 1,240 served) has NO SOC coordinate, so the coordinate-aware
    # extractor stays silent → the group is INCOMPLETE (None), never a false ==-fail against S1.
    def demand_tx(pid, val):
        return {"pathway_id": pid, "turns": [{"role": "analyst", "text": "...",
                "tool_calls": [{"name": "sector_overview", "args": {"member": "deanza", "sector": "adm"},
                                "figures": {"sector demand": val}}]}]}
    grp = {"A": demand_tx("a", 8150), "B": demand_tx("b", 1240)}
    assert sc.run_group(_GID, "coordinate_identity", grp)["pass"] is None


def test_coordinate_figure_matches_only_its_soc():
    tx = _compare_row_tx("x", "51-4041", 510)
    assert sc.coordinate_figure(tx, "51-4041") == 510
    assert sc.coordinate_figure(tx, "51-9161") == 210
    assert sc.coordinate_figure(tx, "29-1141") is None   # not named → no figure at that coordinate


# ── functional: forward_reverse membership (⊇, never magnitude) ──
def _fr_turn(text, name, args, figures=None):
    return {"role": "analyst", "text": text,
            "tool_calls": [{"name": name, "args": args, "figures": figures or {}}]}


def test_forward_reverse_edge_corroborated_passes():
    t = {"turns": [
        _fr_turn("095630 prepares students for 51-4041 and 51-9161.",
                 "program_pathways", {"member": "deanza", "sector": "adm", "program": "095630"},
                 {"51-4041 Machinists": 510, "51-9161 CNC": 210}),
        _fr_turn("Machinists are fed by 095630 and 095610.",
                 "program_pathways", {"member": "deanza", "sector": "adm", "occupation": "51-4041"},
                 {"095630 Machine Tool Tech": 23, "095610 Manufacturing": 5})]}
    assert sc.forward_reverse_membership(t)["pass"] is True


def test_forward_reverse_dropped_edge_fails():
    # forward: 095630 → 51-4041, but reverse from 51-4041 omits 095630.
    t = {"turns": [
        _fr_turn("095630 prepares students for 51-4041.",
                 "program_pathways", {"member": "deanza", "sector": "adm", "program": "095630"},
                 {"51-4041 Machinists": 510}),
        _fr_turn("Machinists are fed by 095610 only.",
                 "program_pathways", {"member": "deanza", "sector": "adm", "occupation": "51-4041"},
                 {"095610 Manufacturing": 5})]}
    res = sc.forward_reverse_membership(t)
    assert res["pass"] is False and res["detail"]["violations"]


def test_forward_reverse_vacuous_when_no_reverse():
    t = {"turns": [
        _fr_turn("095630 prepares students for 51-4041.",
                 "program_pathways", {"member": "deanza", "sector": "adm", "program": "095630"},
                 {"51-4041 Machinists": 510})]}
    res = sc.forward_reverse_membership(t)
    assert res["pass"] is True and res["detail"]["edges_checked"] == 0


# ── functional: absence vs zero ──
def test_absence_gated_named_unknown_passes():
    t = {"turns": [_turn("Graduate wages aren't available for this program — that figure is unknown.",
                         [{"name": "compare", "args": {}, "figures": {"wage": None}, "gated": True}])]}
    assert sc.absence_not_zero_language(t)["pass"] is True


def test_absence_gated_read_as_zero_fails():
    t = {"turns": [_turn("Graduate wages are $0 for this program.",
                         [{"name": "compare", "args": {}, "figures": {"wage": None}, "gated": True}])]}
    assert sc.absence_not_zero_language(t)["pass"] is False


def test_absence_structural_zero_framed_passes():
    t = {"turns": [_turn("You run no program feeding machinists, so there's nothing to report there.",
                         [{"name": "occupation_profile", "args": {"occupation": "51-4041"},
                           "figures": {"member_supply": None}}])]}
    assert sc.absence_not_zero_language(t)["pass"] is True


def test_absence_vacuous_when_all_populated():
    t = {"turns": [_turn("The gap is 510.", [{"name": "x", "args": {}, "figures": {"gap": 510}}])]}
    assert sc.absence_not_zero_language(t)["pass"] is True
