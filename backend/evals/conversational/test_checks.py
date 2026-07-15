"""Unit tests for the deterministic pre-gate (`checks.py`), pinning the three
false-positive fixes surfaced by the run-1..3 conversational eval:

  * axis_named — the 3-char axis "gap" must not be dropped by the length filter.
  * no_invented_score — a REFUSED blend ("we won't reduce this to one score") is
    correct behavior, not a violation; only a non-negated, actually-produced blend hits.
  * traceability — SOC codes (51-4041), TOP6 codes (093400), and academic-year ranges
    (2022-23) must not leave digit-fragment orphans; a stated magnitude must match a
    negative logged figure (compare on abs).

Each test also pins that the check still CATCHES its genuine failure, so the fix widens
the gate's accuracy without blinding it.
"""
from __future__ import annotations

from evals.conversational import checks


def _analyst(text, tool_calls=None):
    return {"role": "analyst", "text": text, "tool_calls": tool_calls or []}


def _t(analyst_turns, pathway_id="unit"):
    return {"pathway_id": pathway_id, "turns": analyst_turns}


# ── axis_named: the "gap" length bug ──────────────────────────────────────────
def test_axis_named_gap_axis_named_passes():
    call = {"name": "supply_demand_gaps", "sorted_by": "gap"}
    t = _t([_analyst("Ranked by the supply-demand gap, the widest is welders.", [call])])
    assert checks.axis_named(t)["pass"] is True  # regression: was False (len("gap")>3 dropped it)


def test_axis_named_still_catches_unnamed_axis():
    call = {"name": "supply_demand_gaps", "sorted_by": "gap"}
    t = _t([_analyst("The widest one is welders.", [call])])  # never names the axis
    assert checks.axis_named(t)["pass"] is False


# ── no_invented_score: negation-aware polarity ────────────────────────────────
def test_no_invented_score_refusal_passes():
    for refusal in [
        "What I won't do is roll these into a single 'strategic score'.",
        "There's no wage or quality score at the college level to crown one.",
        "I deliberately didn't melt them into one score.",
        "I'd rather show the measures than a fake composite.",
    ]:
        t = _t([_analyst(refusal)])
        assert checks.no_invented_score(t)["pass"] is True, refusal


def test_no_invented_score_actual_blend_fails():
    t = _t([_analyst("I ranked the occupations by a composite score of demand and wage.")])
    r = checks.no_invented_score(t)
    assert r["pass"] is False and "composite" in [h.lower() for h in r["detail"]]


# ── traceability: code/date fragments and signed magnitudes ───────────────────
def _fig_call(figs):
    return {"name": "occupation_profile", "figures": figs}


def test_traceability_soc_code_not_orphaned():
    t = _t([_analyst(
        "Industrial Machinery Mechanics (51-4041) has about 550 openings a year.",
        [_fig_call({"openings": 550})])])
    assert checks.traceability(t)["pass"] is True  # "4041" must not be a phantom orphan


def test_traceability_top_code_not_orphaned():
    t = _t([_analyst(
        "The Machining program (TOP 093400) completes about 40 a year.",
        [_fig_call({"completions": 40})])])
    assert checks.traceability(t)["pass"] is True  # "093400" stripped as a code


def test_traceability_year_range_not_orphaned():
    t = _t([_analyst(
        "Supply is a 3-year average of completions (2022-23 through 2024-25).",
        [_fig_call({})])])
    assert checks.traceability(t)["pass"] is True  # "23"/"25" are date fragments, not figures


def test_traceability_negative_gap_magnitude_matches():
    t = _t([_analyst(
        "The region over-supplies these roles by about 322 a year.",
        [_fig_call({"gap": -322})])])
    assert checks.traceability(t)["pass"] is True  # stated magnitude 322 matches logged -322


def test_traceability_still_catches_real_orphan():
    t = _t([_analyst(
        "Employers post about 5000 openings a year for this role.",
        [_fig_call({"openings": 550})])])  # 5000 traces to nothing
    r = checks.traceability(t)
    assert r["pass"] is False and 5000 in r["detail"]
