"""Layer 3 / Tier C — deterministic semantic-classification & invariant checks.

Tier A (``test_compare.py``) proves the numbers agree AT THE SERVER — the right form is
called by construction. Tier C proves the ANALYST's conversational *walk* routes to the
right coordinate and preserves the generator-algebra invariants (``docs/domain/
generator-algebra.md``) in what it tells the practitioner. The unit is the walk (which
tool / grain / direction it chose), never the number — the seed oracle owns numbers.

Two check kinds:
  * **per-transcript** — one transcript; extends the ``checks.py`` ``run()`` contract.
  * **metamorphic** — a RELATION across a GROUP of transcripts (=, ≤), the one primitive
    ``checks.py`` cannot express. ``run_group`` applies it.

``LAWS`` is the machine-readable manifest ``test_semantic.test_algebra_coverage`` and the
docs-audit verify against the spec doc. Ground-truth discipline (no author bias):
  * classification gates on **call-shape** the analyst self-reports (reliable — it just made
    the call; the judge cross-checks prose);
  * the metamorphic **relations** need no blessed answer — they assert A vs B;
  * on-demand, the relation compares the analyst's self-reported figures (GUARDED); the
    headless CI port swaps in the seed oracle (``characterization.capture``) to hard-gate.
"""
from __future__ import annotations

import re

from evals.conversational.checks import _analyst_turns

# ── the machine-readable law manifest (the spec the doc + coverage test verify) ──
LAWS: dict[str, dict] = {
    "regional_invariance": {"relation": "==", "measure": "gap", "runs_on": "metamorphic",
        "status": "phase-1",
        "doc": "An occupation's regional gap is invariant to which member anchors the query."},
    "grain_nesting": {"relation": "<=", "measure": "member_supply", "runs_on": "metamorphic",
        "status": "phase-1",
        "doc": "A college's own supply into an occupation is ≤ its district's (the district pools it)."},
    "part_le_whole": {"relation": "<=", "measure": "demand", "runs_on": "per-transcript",
        "status": "phase-1",
        "doc": "Served-occupations demand ≤ full-sector demand; addressable pools overlap, never sum."},
    "establish_before": {"relation": "order", "measure": None, "runs_on": "per-transcript",
        "status": "phase-1 (onboarding)",
        "doc": "No scoped measure before the institution coordinate is established."},
    "coordinate_identity": {"relation": "==", "measure": "openings", "runs_on": "metamorphic",
        "status": "phase-2",
        "doc": "A measure at a coordinate is one value however reached (tool-independent)."},
    "forward_reverse": {"relation": "subset", "measure": None, "runs_on": "per-transcript",
        "status": "phase-2",
        "doc": "If program P prepares occupation O, O's feeder set contains P — membership, not magnitude."},
    "absence_not_zero": {"relation": "lang", "measure": None, "runs_on": "per-transcript",
        "status": "phase-2",
        "doc": "A gated/blank field is unknown, never 0; structural-0 (no program) ≠ unknown."},
}

# Analytical forms (produce a scoped measure) vs orienting forms (establish the coordinate).
_ORIENT = {"list_institutions", "institution_overview", "member_portfolio"}
_ANALYZE = {"sector_overview", "supply_demand_gaps", "occupation_profile", "unmet_demand",
            "compare", "program_pathways", "program_coverage", "regional_employers"}

# Graph-free grain fallback for the eval's known members (avoids a neo4j dependency at import).
_GRAIN_FALLBACK = {"smccd": "district", "svamp": "consortium", "baccc": "consortium",
                   "skyline": "college", "canada": "college", "csm": "college",
                   "ccsf": "college", "deanza": "college", "laney": "college"}


def _tool(call: dict) -> str:
    """Bare form name — the analyst may report it with or without the mcp__ prefix."""
    return (call.get("name") or "").split("__")[-1]


def _calls(t: dict) -> list[dict]:
    return [c for turn in _analyst_turns(t) for c in (turn.get("tool_calls") or [])]


def _member_grain(member: str | None) -> str:
    if not member:
        return "region"
    try:                                    # prefer the live catalog when a graph is present
        from mcp_server.scope import scope_catalog
        for e in scope_catalog():
            if e.get("member_id") == member:
                return e.get("member_kind", "unknown")
    except Exception:
        pass
    return _GRAIN_FALLBACK.get(member, "unknown")


def _call_grain(call: dict) -> str:
    return _member_grain((call.get("args") or {}).get("member"))


def _call_direction(call: dict) -> str:
    if _tool(call) == "program_pathways":
        args = call.get("args") or {}
        if args.get("program") or args.get("top6"):
            return "forward"       # program → occupations
        if args.get("soc") or args.get("occupation"):
            return "reverse"       # occupation → programs
    return "aggregate"


def _figure_by_key(t: dict, keyword: str) -> float | None:
    """The analyst's self-reported figure whose label contains ``keyword`` (last wins).
    GUARDED — self-report; the CI port replaces this with the seed oracle."""
    val = None
    for c in _calls(t):
        for k, v in (c.get("figures") or {}).items():
            if keyword in k.lower():
                try:
                    val = float(v)
                except (TypeError, ValueError):
                    pass
    return val


# ── per-transcript checks (the checks.py contract) ──
def golden_traversal(t: dict, probe: dict) -> dict:
    """The analyst reached for a right form at the right grain/direction (call-shape, not figure)."""
    g = probe.get("golden")
    if not g:
        return {"check": "golden_traversal", "pass": True, "detail": "no golden (adversarial)"}
    want_forms = set(g.get("forms") or [])
    hits = [c for c in _calls(t) if _tool(c) in want_forms]
    ok_form = bool(hits)
    ok_grain = (g.get("grain") is None) or any(_call_grain(c) == g["grain"] for c in hits)
    ok_dir = (g.get("direction") is None) or any(_call_direction(c) == g["direction"] for c in hits)
    ok = ok_form and ok_grain and ok_dir
    return {"check": "golden_traversal", "pass": ok,
            "detail": {"form": ok_form, "grain": ok_grain, "direction": ok_dir,
                       "called": sorted({_tool(c) for c in _calls(t)})}}


def establish_order(t: dict) -> dict:
    """No analytical call may precede the first orienting call (establish-before-analyze)."""
    seen_orient = False
    for c in _calls(t):
        name = _tool(c)
        if name in _ORIENT:
            seen_orient = True
        elif name in _ANALYZE and not seen_orient:
            return {"check": "establish_order", "pass": False, "detail": f"{name} before establishing"}
    return {"check": "establish_order", "pass": True, "detail": None}


def coordinate_named(t: dict) -> dict:
    """Defensibility: when the analyst reports figures, the prose names the coordinate's scope
    (region / district / college / consortium / statewide) so the practitioner can reconstruct it."""
    if not any(c.get("figures") for c in _calls(t)):
        return {"check": "coordinate_named", "pass": True, "detail": "no figures reported"}
    text = " ".join(x["text"] for x in _analyst_turns(t)).lower()
    named = bool(re.search(r"region|bay area|district|college|consortium|statewide", text))
    return {"check": "coordinate_named", "pass": named, "detail": named}


def surfaced_both_demands(t: dict) -> dict:
    """Two-demand seam: the analyst distinguishes full-sector demand from served-occupations demand."""
    text = " ".join(x["text"] for x in _analyst_turns(t)).lower()
    full_cue = re.search(r"full[- ]sector|whole sector|entire sector|across (all|every) .*occupation|"
                         r"all .*occupations in", text)
    served_cue = re.search(r"already (serve|train|teach)|occupations you (serve|train)|"
                           r"programs you (run|have)|served", text)
    ok = bool(full_cue and served_cue)
    return {"check": "surfaced_both_demands", "pass": ok,
            "detail": {"full_sector_reading": bool(full_cue), "served_reading": bool(served_cue)}}


# ── metamorphic runner (the new primitive) ──
def _apply(relation: str, a: float, b: float) -> bool:
    band = max(1.0, 0.02 * abs(a or b or 1))
    if relation == "==":
        return abs(a - b) <= band
    if relation == "<=":
        return a <= b + band
    raise ValueError(relation)


def run_group(group_id: str, invariant: str, by_role: dict[str, dict],
              oracle=None) -> dict:
    """Apply a metamorphic law across a probe group's transcripts.
    ``by_role`` maps role ('A','B') → transcript. ``oracle(role)`` optionally supplies the
    figure from the seed instead of self-report (the CI hard-gate)."""
    law = LAWS[invariant]
    measure, relation = law["measure"], law["relation"]

    def figure(role, t):
        if oracle is not None:
            return oracle(role)
        return _figure_by_key(t, measure)

    a, b = by_role.get("A"), by_role.get("B")
    if a is None or b is None:
        return {"group": group_id, "invariant": invariant, "pass": None,
                "detail": "group incomplete (missing a role's transcript)"}
    fa, fb = figure("A", a), figure("B", b)
    if fa is None or fb is None:
        return {"group": group_id, "invariant": invariant, "pass": None,
                "detail": f"figure '{measure}' not captured (self-report gap; oracle in CI)"}
    ok = _apply(relation, fa, fb)
    return {"group": group_id, "invariant": invariant, "pass": ok,
            "detail": {"A": fa, "relation": relation, "B": fb}}


# ── driver over a set of captured transcripts ──
def run(transcript: dict, probe: dict | None = None) -> dict:
    """Per-transcript checks for one probe's transcript (adversarial/golden probes)."""
    results = []
    if probe is not None:
        results.append(golden_traversal(transcript, probe))
        if probe.get("seam") == "two_demand":
            results.append(surfaced_both_demands(transcript))
    results.append(establish_order(transcript))
    results.append(coordinate_named(transcript))
    return {"pathway_id": transcript.get("pathway_id"),
            "passed": sum(bool(r["pass"]) for r in results), "of": len(results), "results": results}


if __name__ == "__main__":
    import json
    import sys
    for path in sys.argv[1:]:
        print(json.dumps(run(json.load(open(path))), indent=1))
