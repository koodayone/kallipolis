"""Canonical quantity resolvers — the single computation layer beneath BOTH stacks.

Every named quantity that appears on more than one surface — the dashboard builders
(``partnerships.landscape_*``) and the MCP forms (``mcp_server.forms``) — resolves through
ONE function here: one feeder rule, one query, one aggregation. Surfaces *compose* these; they
never re-derive a shared figure. This is the sibling of the gate design — a machinist gap must
be one number no matter which surface serves it, or a caller inherits an incoherent ontology.

This module lives in ``partnerships`` (beneath ``mcp_server``, above ``landscape``) so both
stacks import DOWN into it without a cycle: the resolvers need ``LandscapeSpec.in_scope`` /
``_term_excluded`` (partnerships concepts) and so cannot sink into ``ontology``, but they must
not stay in ``mcp_server`` where the builders can't reach them. ``mcp_server.canonical`` is a
thin back-compat shim re-exporting this module.

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

from dataclasses import dataclass
from functools import lru_cache

from ontology.crosswalks import is_vocational, top6_to_soc
from ontology.schema import get_driver
from partnerships.landscape import _term_excluded

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


def gap(demand, supply) -> int:
    """THE single gap expression: annual regional openings − annual supply, rounded to a
    whole opening. Openings and supply are each treated as 0 when absent, so a SOC with
    demand but no supply reports the full opening count (not a crash), and vice-versa.
    Every surface that reports a gap composes this, so the arithmetic can't drift."""
    return int(round((demand or 0) - (supply or 0)))


def vintage(years: tuple[str, ...]) -> str:
    """The honest vintage string for a supply window — stated, not faked."""
    if len(years) == 1:
        return f"DataMart completions — {years[0]}"
    return f"{len(years)}-yr avg DataMart completions ({years[-1]}…{years[0]})"


# ── OFFERING — the college roster for a program (referential integrity, layer 2) ──
# `colleges_offering` disagreed across tools because occupation_profile counted Program
# NODES while the builders counted 09 COURSES (a demonstrable undercount — colleges that
# award a credential but have no course records were dropped). One canonical roster here,
# program-grain, matching the dashboard's coverage-matrix classification (covered = enrolled
# AND awarded; partial = one; gap = on the books but neither). Every tool composes it, so the
# count and the named set agree.

@dataclass(frozen=True)
class CollegeCell:
    """One (college × program) supply cell — the roster atom. `college` IS the display label;
    `awards` is the latest reported year, matching the coverage-matrix cell."""
    college: str
    has_program: bool
    enrolled: bool
    awards: int

    @property
    def coverage(self) -> str:
        if self.enrolled and self.awards > 0:
            return "covered"
        if self.enrolled or self.awards > 0:
            return "partial"
        return "gap"     # on the books but no current activity (dormant)


@lru_cache(maxsize=1024)
def _top_roster(colleges: tuple[str, ...], top6: str, latest: str) -> tuple[CollegeCell, ...]:
    """Per-college supply cells for ONE program over the colleges — THE canonical roster.
    Program-grain: a Program node + latest-year awards + enrollment presence (same non-excluded
    terms as the coverage matrix). Computed once, so every tool's roster and count agree."""
    with get_driver().session() as s:
        prog = {r["c"] for r in s.run(
            "MATCH (p:Program) WHERE p.college IN $c AND p.top6=$t RETURN DISTINCT p.college AS c",
            c=list(colleges), t=top6).data()}
        aw = {r["c"]: r["n"] for r in s.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear) "
            "WHERE p.college IN $c AND p.top6=$t AND ay.year=$y "
            "RETURN p.college AS c, toInteger(sum(coalesce(a.count,0))) AS n",
            c=list(colleges), t=top6, y=latest).data()}
        en_rows = s.run(
            "MATCH (p:Program)-[e:ENROLLED]->(term:Term) "
            "WHERE p.college IN $c AND p.top6=$t "
            "RETURN p.college AS c, term.term AS term, toInteger(coalesce(e.count,0)) AS n",
            c=list(colleges), t=top6).data()
    enrolled = {r["c"] for r in en_rows if r["n"] > 0 and r["term"] and not _term_excluded(r["term"])}
    cols = prog | enrolled | set(aw)
    cells = [CollegeCell(college=c, has_program=c in prog, enrolled=c in enrolled, awards=aw.get(c, 0))
             for c in cols]
    cells.sort(key=lambda x: (-x.awards, x.college))
    return tuple(cells)


def college_roster(colleges, top6: str) -> tuple[CollegeCell, ...]:
    """The canonical per-college roster for a program, sorted by awards — includes any college
    with a program, enrollment, or awards (never silently dropped, unlike OES suppression)."""
    yrs = recent_award_years(1)
    return _top_roster(tuple(sorted(set(colleges))), top6, yrs[0] if yrs else "")


def colleges_with_program(colleges, top6: str) -> int:
    """Program-grain count of colleges offering a program (a Program node exists) — the
    canonical replacement for the course-based n_colleges_offering undercount."""
    return sum(1 for c in college_roster(colleges, top6) if c.has_program)


def colleges_actively_awarding(colleges, top6: str) -> int:
    """Colleges producing completers in the latest year — the stricter 'active' count."""
    return sum(1 for c in college_roster(colleges, top6) if c.awards > 0)


def active_feeders(colleges, soc: str) -> frozenset[str]:
    """A SOC's supporting programs WITH CURRENT SUPPLY — is_vocational crosswalk feeders that
    awarded a completer in the latest year. Mirrors the builders' `_awarded_tops` gate, so
    occupation_profile's supporting-program set matches program_pathways/program_coverage
    (a program on the books but dormant, e.g. 123000 Nursing, is excluded here as it is there)."""
    return frozenset(t for t in feeders(colleges, soc)
                     if colleges_actively_awarding(colleges, t) > 0)
