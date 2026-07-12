"""Canonical quantity resolvers — referential integrity across the tool surface.

Every named quantity that appears in more than one tool's payload resolves through
ONE function here: one feeder rule, one query, one aggregation. Tools *compose*
these; they never re-derive a shared figure. This is the sibling of the gate design —
a machinist gap must be one number no matter which tool serves it, or the model
inherits an incoherent ontology.

SUPPLY — the definition (settled 2026-07-11):
  DataMart CO-approved completions across the SOC's feeders, averaged over a year
  window. A feeder is a TOP6 program that (a) the colleges offer, (b) cross-walks to
  the SOC, and (c) is ``is_vocational`` (CTE) — the last clause excludes non-CTE
  crosswalk noise (e.g. Liberal Arts 490100 → Machinists). The default window is the
  most recent 3 award years (``projected_supply`` — COE's annual-projection *method*);
  the single latest year is ``latest_year_supply``. COE's published supply IS DataMart
  CO-approved completions (verified identical where the data is complete), so serving
  it from DataMart is a freshness + coherence choice, not a disagreement about the
  number — and the recent-3-year window sidesteps the graph's under-loaded 2020-21 year
  (task #23). Member (member colleges) and regional (region colleges) supply differ
  only by ``colleges``; the two windows only by ``years``; feeder rule and query are
  identical, so no two callers can disagree.

Caches are process-lifetime (refresh on a graph reload), matching landscape_build.
"""
from __future__ import annotations

from functools import lru_cache

from ontology.crosswalks import is_vocational, top6_to_soc
from ontology.schema import get_driver

_SUPPLY_YEARS = 3   # COE's annual-projection method is a 3-year mean

SUPPLY_SOURCE = "datamart"   # supply is now DataMart completions, COE's averaging method


@lru_cache(maxsize=1)
def recent_award_years(n: int = _SUPPLY_YEARS) -> tuple[str, ...]:
    """The n most recent award years in the graph (descending) — the window supply
    averages over. Fully-loaded years only in practice (2020-21 is under-loaded, #23)."""
    with get_driver().session() as s:
        return tuple(r["y"] for r in s.run(
            "MATCH (ay:AcademicYear) RETURN ay.year AS y ORDER BY y DESC LIMIT $n", n=n).data())


@lru_cache(maxsize=256)
def _soc_feeders(colleges: tuple[str, ...]) -> dict[str, frozenset[str]]:
    """{soc -> is_vocational feeder TOP6s these colleges offer that cross-walk to it},
    computed once per college set so per-SOC feeder lookup is O(1). The one feeder rule."""
    with get_driver().session() as s:
        offered = {r["t"] for r in s.run(
            "MATCH (p:Program) WHERE p.college IN $c RETURN DISTINCT p.top6 AS t",
            c=list(colleges)).data()}
    soc_map = top6_to_soc(list(offered))
    out: dict[str, set] = {}
    for t in offered:
        if is_vocational(t):
            for soc in soc_map.get(t, set()):
                out.setdefault(soc, set()).add(t)
    return {k: frozenset(v) for k, v in out.items()}


@lru_cache(maxsize=512)
def _awarded_by_top(colleges: tuple[str, ...], years: tuple[str, ...]) -> dict[str, int]:
    """{top6 -> total CO-approved completions} over the colleges and years, once."""
    with get_driver().session() as s:
        rows = s.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear) "
            "WHERE p.college IN $c AND ay.year IN $y "
            "RETURN p.top6 AS t, sum(coalesce(a.count, 0)) AS n",
            c=list(colleges), y=list(years)).data()
    return {r["t"]: r["n"] for r in rows}


def feeders(colleges, soc: str) -> frozenset[str]:
    """The SOC's is_vocational feeder TOP6s the colleges offer — the one feeder rule."""
    return _soc_feeders(tuple(sorted(set(colleges)))).get(soc, frozenset())


def supply(colleges, soc: str, *, years: tuple[str, ...] | None = None) -> float:
    """Canonical annual supply for a SOC over a set of colleges. THE single resolution
    path for every supply figure. Default window = most recent 3 years (projected_supply);
    pass ``years=recent_award_years(1)`` for the latest year (latest_year_supply)."""
    yrs = years if years is not None else recent_award_years()
    fs = feeders(colleges, soc)
    if not fs or not yrs:
        return 0.0
    aw = _awarded_by_top(tuple(sorted(set(colleges))), tuple(yrs))
    total = sum(aw.get(t, 0) for t in fs)
    return round(total / len(yrs), 1)


def supply_over_socs(colleges, socs, *, years: tuple[str, ...] | None = None) -> float:
    """Aggregate supply over a SET of SOCs (a sector total). Feeders are DEDUPED across
    the SOCs — a TOP6 that feeds several occupations is counted once — so a sector total
    never double-counts, unlike summing per-SOC supply."""
    yrs = years if years is not None else recent_award_years()
    fs: set[str] = set()
    for soc in socs:
        fs |= feeders(colleges, soc)
    if not fs or not yrs:
        return 0.0
    aw = _awarded_by_top(tuple(sorted(set(colleges))), tuple(yrs))
    return round(sum(aw.get(t, 0) for t in fs) / len(yrs), 1)


def vintage(years: tuple[str, ...]) -> str:
    """The honest vintage string for a supply window — stated, not faked."""
    if len(years) == 1:
        return f"DataMart completions — {years[0]}"
    return f"{len(years)}-yr avg DataMart completions ({years[-1]}…{years[0]})"
