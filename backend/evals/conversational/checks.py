"""Deterministic pre-gate — cheap, non-flaky checks on a captured transcript.

Run BEFORE the LLM judge (per ``research/architecture/EVALS-APPROACH.md``): whatever code can
verify, code verifies, so the judge spends only on the irreducibly interpretive dimensions.

A transcript is a dict::

    {"pathway_id": str, "turns": [Turn, ...]}
    Turn (practitioner): {"role": "practitioner", "text": str}
    Turn (analyst):      {"role": "analyst", "text": str, "tool_calls": [Call, ...]}
    Call: {"name": str, "args": {...}, "figures": {label: number, ...},
           "sorted_by": str|None, "view_link": bool, "gated": bool}

The model-under-test subagent reports its own tool calls + the figures it read; v1 trusts that
report and the judge cross-checks. Port to server-side capture for the CI gate.
"""
from __future__ import annotations

import re


def _numbers(text: str) -> set[int]:
    """Rounded integer magnitudes stated in prose ($, %, comma-grouped, and k suffix)."""
    out: set[int] = set()
    for m in re.finditer(r"\$?\d[\d,]*(?:\.\d+)?%?k?", text):
        v = m.group(0).replace("$", "").replace(",", "").replace("%", "").lower()
        mult = 1000 if v.endswith("k") else 1
        try:
            out.add(round(float(v.rstrip("k")) * mult))
        except ValueError:
            pass
    return out


def _analyst_turns(t: dict) -> list[dict]:
    return [x for x in t.get("turns", []) if x.get("role") == "analyst"]


def _all_figures(t: dict) -> set[int]:
    vals: set[int] = set()
    for turn in _analyst_turns(t):
        for c in turn.get("tool_calls", []):
            for v in (c.get("figures") or {}).values():
                try:
                    vals.add(round(float(v)))
                except (TypeError, ValueError):
                    pass
    return vals


def traceability(t: dict) -> dict:
    """Every number the analyst states traces to a figure a tool returned (rounding-tolerant).
    Small numbers (<=12: counts) and years are ignored to cut false positives."""
    figs = _all_figures(t)
    orphans = []
    for turn in _analyst_turns(t):
        for n in _numbers(turn["text"]):
            if n <= 12 or 1990 <= n <= 2035:
                continue
            if not any(abs(n - f) <= max(1, 0.02 * f) for f in figs):
                orphans.append(n)
    return {"check": "traceability", "pass": not orphans, "detail": orphans}


def axis_named(t: dict) -> dict:
    """When a ranking was returned (sorted_by present), the analyst names that axis in prose."""
    misses = []
    for turn in _analyst_turns(t):
        for c in turn.get("tool_calls", []):
            sb = c.get("sorted_by")
            if sb:
                words = [w for w in re.findall(r"[a-z]+", sb.lower()) if len(w) > 3]
                if not any(w in turn["text"].lower() for w in words):
                    misses.append(sb)
    return {"check": "axis_named", "pass": not misses, "detail": misses}


def routing(t: dict) -> dict:
    """A whole-institution ask should route (member_portfolio once), not loop sector_overview."""
    n = sum(1 for turn in _analyst_turns(t) for c in turn.get("tool_calls", [])
            if c.get("name") == "sector_overview")
    looped = "portfolio" in t.get("pathway_id", "") and n > 1
    return {"check": "routing", "pass": not looped, "detail": {"sector_overview_calls": n}}


def view_link_offered(t: dict) -> dict:
    """If a response carried a dashboard view, the analyst offers it (verify with your own eyes)."""
    misses = 0
    for turn in _analyst_turns(t):
        if any(c.get("view_link") for c in turn.get("tool_calls", [])):
            if not re.search(r"view|dashboard|see it|link|verify|your own eyes", turn["text"], re.I):
                misses += 1
    return {"check": "view_link_offered", "pass": misses == 0, "detail": misses}


def no_invented_score(t: dict) -> dict:
    """The analyst never ranks by a 'score'/'index'/'rating'/'composite' — the forbidden blend."""
    hits = [w for turn in _analyst_turns(t)
            for w in re.findall(r"\b(score|index|rating|composite)\b", turn["text"], re.I)]
    return {"check": "no_invented_score", "pass": not hits, "detail": hits}


CHECKS = [traceability, axis_named, routing, view_link_offered, no_invented_score]


def run(transcript: dict) -> dict:
    results = [c(transcript) for c in CHECKS]
    return {"pathway_id": transcript.get("pathway_id"),
            "passed": sum(r["pass"] for r in results), "of": len(results), "results": results}


if __name__ == "__main__":
    import json
    import sys
    for path in sys.argv[1:]:
        print(json.dumps(run(json.load(open(path))), indent=1))
