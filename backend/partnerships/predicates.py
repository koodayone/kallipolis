"""The versioned predicate registry — kernel law K2's single home.

v0.2 K2: filters and thresholds are defined once, VERSIONED, and applied identically
wherever a coordinate is evaluated — so a figure can stamp WHICH predicate set produced it
(``envelope.QualifiedValue.predicate_version``) and stay reproducible after predicates evolve.
This module is that single definition; a ``predicate_version`` string indexes it.

Migration status (Phase 0): this registers the CURRENT, *uncontested* predicate sets with NO
behavior change — the values already in force, gathered to one source. The two predicates that
still have two birthplaces are DELIBERATELY NOT registered here yet, because registering a single
value now would silently resolve a §7 adjudication:

- the FEEDER rule — ``is_vocational`` (kernel, ``quantities.feeders``) vs ``LandscapeSpec.in_scope``
  (dashboard, ``landscape_programs.relevant_tops``); unified in Phase 1 (adjudication A).
- the COVERAGE classification — ruleless (enrolled-OR-awarded) vs ``awards_only``
  (``quantities.coverage``); unified in Phase 4 (adjudication D).

They join the registry when their birthplaces are unified, each under an explicit version.
"""
from __future__ import annotations

from dataclasses import dataclass

# The current predicate-set version. Bump when a REGISTERED predicate's *meaning* changes; a
# figure computed under the old set keeps its old stamp, so historical figures stay reproducible.
# The stamp on a QualifiedValue names the version under which the value was computed.
CURRENT = "2026-07"

# ── Greenfield / unmet-demand gates (moved verbatim from mcp_server.forms; identical values) ──
# A greenfield occupation is surfaced only if it clears ALL THREE: community-college-servable entry
# education, a living-wage floor, and a meaningful-demand floor.
CC_SERVABLE_EDUCATION = frozenset({
    "High school diploma or equivalent",
    "Postsecondary nondegree award",
    "Some college, no degree",
    "Associate's degree",
})
WAGE_FLOOR = 50_000       # living-wage floor (USD/yr, occupation median) — screens out low-wage demand
OPENINGS_FLOOR = 100      # meaningful-demand floor (annual regional openings) — screens out thin demand

# ── The "active" completion floor — a program counts as supplying an occupation only with strictly
# more than this many completers in the latest reported year. One rule, three current call sites
# (resolve.active_tops, landscape_programs._awarded_tops, quantities.active_feeders); registered here
# so those sites can converge on one source when feeder resolution is unified (Phase 1/3). ──
LATEST_YEAR_COMPLETER_FLOOR = 0   # strictly greater-than: ">0 completers in the latest year"


@dataclass(frozen=True)
class PredicateSet:
    """The bundle of filter/threshold predicates in force under one version. ``feeder_rule`` and
    ``coverage_rule`` are intentionally absent until their birthplaces are unified (§7 A, D)."""

    version: str
    cc_servable_education: frozenset
    wage_floor: int
    openings_floor: int
    latest_year_completer_floor: int


REGISTRY: dict[str, PredicateSet] = {
    CURRENT: PredicateSet(
        version=CURRENT,
        cc_servable_education=CC_SERVABLE_EDUCATION,
        wage_floor=WAGE_FLOOR,
        openings_floor=OPENINGS_FLOOR,
        latest_year_completer_floor=LATEST_YEAR_COMPLETER_FLOOR,
    ),
}


def current() -> PredicateSet:
    """The predicate set in force. A figure computed under it stamps ``CURRENT``."""
    return REGISTRY[CURRENT]
