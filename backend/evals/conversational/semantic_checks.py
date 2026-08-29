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
# Each law names its RELATION, the MEASURE the metamorphic runner compares (None for the
# per-transcript language/order/membership laws), the CHECK that grades it, and its build STATUS
# (the coverage test requires a probe for every phase-1 and phase-2-active law).
LAWS: dict[str, dict] = {
    "regional_invariance": {"relation": "==", "measure": "gap", "runs_on": "metamorphic",
        "status": "phase-1", "check": "run_group",
        "doc": "An occupation's regional gap is invariant to which member anchors the query."},
    "grain_nesting": {"relation": "<=", "measure": "member_supply", "runs_on": "metamorphic",
        "status": "phase-1", "check": "run_group",
        "doc": "A college's own supply into an occupation is ≤ its district's (the district pools it)."},
    "part_le_whole": {"relation": "<=", "measure": "demand", "runs_on": "per-transcript",
        "status": "phase-1", "check": "surfaced_both_demands",
        "doc": "Served-occupations demand ≤ full-sector demand; addressable pools overlap, never sum."},
    "establish_before": {"relation": "order", "measure": None, "runs_on": "per-transcript",
        "status": "phase-1 (onboarding)", "check": "establish_order",
        "doc": "No scoped measure before the institution coordinate is established."},
    # ── Phase 2 (active) ──
    "coordinate_identity": {"relation": "==", "measure": "openings", "runs_on": "metamorphic",
        "status": "phase-2-active", "check": "run_group (coordinate-aware)", "coordinate_aware": True,
        "doc": "A measure at a coordinate is one value however reached (tool-independent) — the "
               "two-window invariant the dashboard/MCP unification is specified by."},
    "forward_reverse": {"relation": "subset", "measure": None, "runs_on": "per-transcript",
        "status": "phase-2-active", "check": "forward_reverse_membership",
        "doc": "If program P prepares occupation O, O's feeder set contains P — membership, never "
               "magnitude (the TOP→CIP→SOC crosswalk is many-to-many and lossy)."},
    "absence_not_zero": {"relation": "lang", "measure": None, "runs_on": "per-transcript",
        "status": "phase-2-active", "check": "absence_not_zero_language",
        "doc": "A gated/blank field is unknown, never 0; a structural 0 (no program) ≠ unknown."},
}

# Analytical forms (produce a scoped measure) vs orienting forms (establish the coordinate).
# Both the coordinate-algebra verbs (orient/navigate/crosswalk/compare) and the retired task-shaped
# tool names are recognized — recorded fixtures pre-date the retirement; live transcripts use verbs.
_ORIENT = {"list_institutions", "orient", "institution_overview", "member_portfolio"}
_ANALYZE = {"navigate", "crosswalk", "compare",
            "sector_overview", "supply_demand_gaps", "occupation_profile", "unmet_demand",
            "program_pathways", "program_coverage", "regional_employers"}

# Graph-free grain fallback for the eval's known members (avoids a neo4j dependency at import).
_GRAIN_FALLBACK = {"smccd": "district", "svamp": "consortium", "baccc": "consortium",
                   "skyline": "college", "canada": "college", "csm": "college",
                   "ccsf": "college", "deanza": "college", "laney": "college"}


# Entity codes carried on a call's args / figure labels — the coordinate a walk landed on.
_SOC_RE = re.compile(r"\b\d{2}-\d{4}\b")     # SOC codes, e.g. 51-4041 (an occupation coordinate)
_TOP6_RE = re.compile(r"\b\d{6}\b")          # TOP6 codes, e.g. 095630 (a program coordinate)


def _tool(call: dict) -> str:
    """Bare form name — the analyst may report it with or without the mcp__ prefix."""
    return (call.get("name") or "").split("__")[-1]


def _call_soc(call: dict) -> str | None:
    """The SOC (occupation) coordinate a call is anchored on, from its args (soc | occupation)."""
    a = call.get("args") or {}
    return a.get("soc") or a.get("occupation")


def _call_program(call: dict) -> str | None:
    """The TOP6 (program) coordinate a call is anchored on, from its args (program | top6)."""
    a = call.get("args") or {}
    return a.get("program") or a.get("top6")


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
    if _tool(call) in ("program_pathways", "crosswalk"):
        args = call.get("args") or {}
        ent = str(args.get("entity") or "")      # crosswalk's dispatch key: SOC "17-3027" vs TOP6 "095000"
        is_soc = "-" in ent
        if args.get("program") or args.get("top6") or (ent and not is_soc):
            return "forward"       # program → occupations
        if args.get("soc") or args.get("occupation") or is_soc:
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


# Synonyms a self-reported figure label may use for a coordinate's measure. Deliberately does NOT
# include a bare "demand": a sector-grain demand figure (sector_overview / an aggregate gap) is a
# DIFFERENT coordinate (it carries no SOC), so admitting "demand" would let coordinate_identity
# collide with the two-demand seam. openings is per-occupation, always at a SOC coordinate.
_MEASURE_SYNONYMS = {"openings": ("opening", "regional_openings")}


def coordinate_figure(t: dict, soc: str, measure: str = "openings") -> float | None:
    """The analyst's self-reported figure for ``measure`` AT the coordinate ``soc`` — matched by SOC
    (from the call's own args, OR from a per-SOC row label in a multi-row call like ``compare``)
    BEFORE any equality is asserted. This is what makes ``coordinate_identity`` coordinate-AWARE where
    ``_figure_by_key`` is not: it will never read a *different* occupation's openings, and it stays
    silent (returns None) on a coordinate-less sector-grain demand figure — so it cannot false-fire at
    the two-demand seam (full-sector vs served demand are different coordinates, neither a SOC).
    GUARDED — self-report; the CI port swaps in ``evals.characterization.capture`` (the two-window
    oracle) to hard-gate."""
    keys = _MEASURE_SYNONYMS.get(measure, (measure,))
    val = None
    for c in _calls(t):
        csoc = _call_soc(c)
        for k, v in (c.get("figures") or {}).items():
            klow = k.lower()
            at_soc = (csoc == soc) or (soc in k)     # call anchored on soc, OR the row names it
            if not at_soc:
                continue
            if any(kw in klow for kw in keys):
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


def _named_socs(text: str, figures: dict | None) -> set[str]:
    """SOC codes the analyst names in a turn — from prose AND from the call's figure/row labels."""
    out = set(_SOC_RE.findall(text or ""))
    for k in (figures or {}):
        out |= set(_SOC_RE.findall(k))
    return out


def _named_tops(text: str, figures: dict | None) -> set[str]:
    """TOP6 program codes the analyst names in a turn — from prose AND from figure/row labels."""
    out = set(_TOP6_RE.findall(text or ""))
    for k in (figures or {}):
        out |= set(_TOP6_RE.findall(k))
    return out


def forward_reverse_membership(t: dict) -> dict:
    """Set-membership (⊇), NEVER magnitude. If the analyst says program P prepares students for
    occupation O (a FORWARD ``program_pathways`` anchored on P), and later reads O's programs in
    REVERSE (``program_pathways`` / ``occupation_profile`` anchored on O), then O's feeder set must
    CONTAIN P. The crosswalk is many-to-many and lossy, so we assert only the *edge's* bidirectional
    presence — the analyst may legitimately compress (name 2 of 8 occupations), so we check only the
    edges it actually asserted forward, and only where it went reverse on that occupation. A dropped
    edge (forward said P→O; reverse from O omits P) is the inconsistency this catches."""
    forward: list[tuple[str, set[str]]] = []     # (program P, {SOCs P prepares for})
    reverse: dict[str, set[str]] = {}            # SOC O -> {feeder programs named}
    for turn in _analyst_turns(t):
        text = turn.get("text", "")
        for c in (turn.get("tool_calls") or []):
            if _tool(c) not in ("program_pathways", "pathway", "occupation_profile"):
                continue
            figs = c.get("figures")
            prog, soc = _call_program(c), _call_soc(c)
            if prog:                                      # forward: program → occupations
                forward.append((prog, _named_socs(text, figs)))
            elif soc:                                     # reverse: occupation → programs
                reverse.setdefault(soc, set()).update(_named_tops(text, figs))
    checked, violations = [], []
    for prog, socs in forward:
        for o in socs:
            if o in reverse:                              # only where a reverse read corroborates
                checked.append([prog, o])
                if prog not in reverse[o]:
                    violations.append({"program": prog, "occupation": o,
                                       "reverse_feeders": sorted(reverse[o])})
    detail = {"edges_checked": len(checked), "violations": violations}
    if not checked:
        detail["note"] = "no forward edge had a reverse read to corroborate (vacuous pass)"
    return {"check": "forward_reverse_membership", "pass": not violations, "detail": detail}


# Unknown-language cues: a value the tool did not return must read as unknown, never as 0.
_UNKNOWN_LANG = re.compile(r"unknown|unavailable|not available|don'?t have|no data|not reported|"
                           r"suppress|can'?t say|out of scope|isn'?t (?:tracked|available)", re.I)
# Structural-zero cues: a real 0 (a verifiable no-program fact) named AS zero-with-a-reason.
_STRUCTURAL_ZERO = re.compile(r"no (?:program|completer|pipeline)|none of (?:your|its)|"
                              r"you (?:don'?t|do not) (?:run|offer|have)|graduates? no one", re.I)


def absence_not_zero_language(t: dict) -> dict:
    """A gated / blank figure is UNKNOWN, never 0; a structural 0 (a member with no program) is a
    real zero that must be named WITH its reason (no program), distinct from unknown. Fires only when
    the transcript actually carries an absent figure (a ``gated`` call, or a ``figures`` value of
    None) — otherwise it passes vacuously, so it never penalizes a fully-populated answer."""
    gated = any(c.get("gated") for c in _calls(t))
    none_figs = any(v is None for c in _calls(t) for v in (c.get("figures") or {}).values())
    if not (gated or none_figs):
        return {"check": "absence_not_zero_language", "pass": True, "detail": "no absent figure"}
    text = " ".join(x.get("text", "") for x in _analyst_turns(t))
    ok = bool(_UNKNOWN_LANG.search(text) or _STRUCTURAL_ZERO.search(text))
    return {"check": "absence_not_zero_language", "pass": ok,
            "detail": {"gated": gated, "none_figures": none_figs,
                       "named_as_unknown_or_structural": ok}}


# ── metamorphic runner (the new primitive) ──
def _apply(relation: str, a: float, b: float) -> bool:
    band = max(1.0, 0.02 * abs(a or b or 1))
    if relation == "==":
        return abs(a - b) <= band
    if relation == "<=":
        return a <= b + band
    raise ValueError(relation)


def run_group(group_id: str, invariant: str, by_role: dict[str, dict],
              oracle=None, figure_fn=None) -> dict:
    """Apply a metamorphic law across a probe group's transcripts.
    ``by_role`` maps role ('A','B') → transcript. ``oracle(role)`` optionally supplies the figure
    from the seed instead of self-report (the CI hard-gate). ``figure_fn(transcript)`` overrides how
    a role's figure is read — used for a coordinate-AWARE law that must match a coordinate before
    comparing (auto-bound below from the group id for ``coordinate_identity``)."""
    law = LAWS[invariant]
    measure, relation = law["measure"], law["relation"]

    # A coordinate-aware law (coordinate_identity) reads its measure only AT the group's coordinate,
    # never by a bare keyword match — so a different occupation's figure, or a coordinate-less
    # sector-grain demand figure, is never compared (the two-demand non-collision guard). The SOC is
    # parsed from the group id (e.g. "coordinate_identity_openings_51-4041"), the convention the
    # phase-1 groups already follow.
    if figure_fn is None and law.get("coordinate_aware"):
        # NB: a bare SOC pattern, NOT _SOC_RE — the group id joins on underscores
        # ("coordinate_identity_openings_51-4041") and \b does not fire between "_" and a digit
        # (both are word chars), so _SOC_RE would miss it and silently fall back to _figure_by_key.
        m = re.search(r"\d{2}-\d{4}", group_id)
        if m:
            soc = m.group(0)
            figure_fn = lambda t: coordinate_figure(t, soc, measure)

    def figure(role, t):
        if oracle is not None:
            return oracle(role)
        if figure_fn is not None:
            return figure_fn(t)
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


# Seam-specific per-transcript checks, beyond the always-on golden_traversal + establish + coordinate.
_SEAM_CHECKS: dict[str, list] = {
    "two_demand": [surfaced_both_demands],
    "forward_reverse": [forward_reverse_membership],
    "absence_zero": [absence_not_zero_language],
}


# ── driver over a set of captured transcripts ──
def run(transcript: dict, probe: dict | None = None) -> dict:
    """Per-transcript checks for one probe's transcript (adversarial/golden/per-transcript probes)."""
    results = []
    if probe is not None:
        results.append(golden_traversal(transcript, probe))
        for chk in _SEAM_CHECKS.get(probe.get("seam"), []):
            results.append(chk(transcript))
    results.append(establish_order(transcript))
    results.append(coordinate_named(transcript))
    return {"pathway_id": transcript.get("pathway_id"),
            "passed": sum(bool(r["pass"]) for r in results), "of": len(results), "results": results}


if __name__ == "__main__":
    import json
    import sys
    for path in sys.argv[1:]:
        print(json.dumps(run(json.load(open(path))), indent=1))
