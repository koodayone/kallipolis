"""Formatting primitives for partnership opportunity narratives.

Style-bearing details for the deterministic prose composed in
``opportunity_narrative.py``. Every stylistic decision the
institutional voice depends on lives here. Templates compose them;
they don't reinvent them.

Public API:
    fmt_count(n, singular[, plural])   — "1 student" / "13,038 students"
    fmt_have(n)                        — "has" / "have"
    fmt_are(n)                         — "is" / "are"
    fmt_wage(wage)                     — "a median annual wage of $99,490"
    fmt_openings(openings)             — "1,470 annual openings"
    fmt_demand_clause(wage, openings)  — composed clause for OD prose

Used by ``opportunity_narrative.py`` as the formatting foundation
for the four-section opportunity report templates.
"""

from __future__ import annotations


def fmt_count(n: int, singular: str, plural: str | None = None) -> str:
    """Render ``N noun`` with correct plural and thousands separator.

    Examples:
        fmt_count(0, "student")       → "0 students"
        fmt_count(1, "student")       → "1 student"
        fmt_count(13038, "student")   → "13,038 students"
        fmt_count(1, "course")        → "1 course"
        fmt_count(354, "course")      → "354 courses"

    Use ``plural`` for irregular nouns where adding "s" is wrong
    (no current cases in the templates, but reserved for safety).
    """
    word = singular if n == 1 else (plural or singular + "s")
    return f"{n:,} {word}"


def fmt_have(n: int) -> str:
    """``"has"`` for n == 1, ``"have"`` otherwise. Verb agreement for the
    count subject in the executive summary's pipeline-proof sentence."""
    return "has" if n == 1 else "have"


def fmt_are(n: int) -> str:
    """``"is"`` for n == 1, ``"are"`` otherwise. Verb agreement for the
    student-impact opener."""
    return "is" if n == 1 else "are"


def fmt_wage(wage: int | float | None) -> str:
    """Format a median annual wage figure for prose use.

    Returns either ``"a median annual wage of $99,490"`` for a real
    figure or ``"unreported median annual wage"`` for a missing one.
    The phrase is meant to slot into ``"an occupation with {…}"``.
    """
    if wage is None:
        return "unreported median annual wage"
    return f"a median annual wage of ${int(wage):,}"


def fmt_openings(openings: int | None) -> str:
    """Format an annual-openings figure for prose use.

    Returns ``"1,470 annual openings"`` or ``"unreported annual
    openings"``. Slots into ``"... and {…} in the {region} region"``.
    """
    if openings is None:
        return "unreported annual openings"
    return f"{int(openings):,} annual opening{'' if int(openings) == 1 else 's'}"


def fmt_demand_clause(wage: int | float | None, openings: int | None) -> str:
    """Compose the wage + openings clause used in the OD section.

    Cases:
        wage + openings present:
            "an occupation with a median annual wage of $X and N annual openings"
        wage missing, openings present:
            "an occupation with N annual openings"
        wage present, openings missing:
            "an occupation with a median annual wage of $X"
        both missing:
            "an occupation"

    Returning the noun-phrase ``"an occupation [with ...]"`` lets the
    caller append the regional attribution cleanly: ``f"{clause} in
    the {region} region according to Centers of Excellence projections."``.
    """
    parts = []
    if wage is not None:
        parts.append(fmt_wage(wage))
    if openings is not None:
        parts.append(fmt_openings(openings))
    if not parts:
        return "an occupation"
    return "an occupation with " + " and ".join(parts)
