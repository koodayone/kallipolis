"""The gate constants for greenfield / unmet-demand and the completer floor — one home.

Formerly a VERSIONED predicate registry (kernel law K2): filters/thresholds defined once and versioned, so a
figure could stamp WHICH predicate set produced it and stay reproducible as predicates evolved. The unified
engine made that unnecessary — there is one rule now, so there is nothing to version or tell figures apart.
The registry / ``PredicateSet`` / ``predicate_version`` stamp machinery was deleted; this module is just the
constants the gates read.
"""
from __future__ import annotations

# ── Greenfield / unmet-demand gates ──────────────────────────────────────────
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

# The "active" completion floor — a program counts as supplying an occupation only with strictly more than
# this many completers in the window. The unified gate itself lives in quantities.producing_tops; this names
# the threshold it enforces (> 0).
LATEST_YEAR_COMPLETER_FLOOR = 0
