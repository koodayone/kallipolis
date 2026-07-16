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

SUPPLY — the definition (settled 2026-07-11; store corrected 2026-07-12):
  DataMart award completions across the SOC's feeders, averaged over a year window.
  A feeder is a TOP6 program that (a) the colleges offer, (b) cross-walks to the SOC,
  and (c) is ``is_vocational`` (CTE) — the last clause excludes non-CTE crosswalk noise
  (e.g. Liberal Arts 490100 → Machinists). The default window is the most recent 3 award
  years (``projected_supply``); the single latest year is ``latest_year_supply``.

  COE's own method, reconstructed on better data: COE's published "Annual Projected
  Supply" (supply_by_top.csv) is literally a trailing 3-yr average of DataMart completion
  columns — the SAME method — but frozen on 2020–2023 and covering "All Awards". The
  DataMart program-awards export now matches that scope (award_type "All Awards", not the
  earlier "Chancellor's Office Approved" filter, which under-counted) and runs fresh
  through 2024-25. Where the export is complete the graph equals COE completion-for-
  completion (~96% of COE's cells; the residual is COE-snapshot staleness + adult-ed
  entities outside our 115-CCC universe — see ``evals/completeness_audit.py``). So serving
  supply from the graph is a freshness + coherence choice, not a disagreement about the
  number. The recent-3 window also sidesteps 2020-21 (never scraped before the fix).

  Member (member colleges) and regional (region colleges) supply differ only by
  ``colleges``; the two windows only by ``years``. NOTE: a member-scoped figure that must
  match a dashboard builder resolves the feeder set through ``LandscapeSpec.in_scope`` /
  ``relevant_tops`` (which also resolves the TOP parent/child crosswalk granularity, e.g.
  RN = 123010 not the general 123000) — that precise crosswalk is a partnerships concern,
  tracked separately from this store-level resolver.

Caches are process-lifetime (refresh on a graph reload), matching landscape_build.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ontology.crosswalks import is_vocational, top6_to_soc
from ontology.schema import get_driver
from partnerships.landscape import _term_excluded, _term_sort_key

_SUPPLY_YEARS = 3   # COE's annual-projection method is a 3-year mean

SUPPLY_SOURCE = "datamart"   # supply is now DataMart completions, COE's averaging method


@lru_cache(maxsize=8)   # n∈{1,3} callers — maxsize=1 would thrash between the two windows
def recent_award_years(n: int = _SUPPLY_YEARS) -> tuple[str, ...]:
    """The n most recent award years in the graph (descending) — the window supply
    averages over. Fully-loaded years only in practice (2020-21 is under-loaded, #23)."""
    with get_driver().session() as s:
        return tuple(r["y"] for r in s.run(
            "MATCH (ay:AcademicYear) RETURN ay.year AS y ORDER BY y DESC LIMIT $n", n=n).data())


@lru_cache(maxsize=256)
def _soc_feeders(colleges: tuple[str, ...], spec=None) -> dict[str, frozenset[str]]:
    """{soc -> feeder TOP6s these colleges offer that cross-walk to it}, computed once per
    (college set, spec) so per-SOC feeder lookup is O(1). The one feeder rule.

    Gated by ``spec.in_scope`` when a spec is given — the canonical rule (adjudication A:
    is_vocational + excluded_tops + home-division + CTE-family; e.g. it excludes generic
    Nursing 123000 in favor of 123010). Falls back to the legacy bare ``is_vocational`` gate
    when spec is None; call sites are being migrated to pass spec, after which the fallback
    (and the divergence it leaves) is removed. Does NOT yet apply the latest-year awards gate
    that ``relevant_tops`` layers on for rule-bearing specs — added if the corroboration band
    does not close on the in_scope gate alone (tracked in Phase 1)."""
    with get_driver().session() as s:
        offered = {r["t"] for r in s.run(
            "MATCH (p:Program) WHERE p.college IN $c RETURN DISTINCT p.top6 AS t",
            c=list(colleges)).data()}
    # Awards gate (rule-bearing specs only): a program with no completer in the latest year is
    # dormant supply — dropped, matching relevant_tops/_awarded_tops so the kernel and dashboard
    # resolve one feeder set. Curated specs (SVAMP) carry no rule and keep the full in_scope set.
    rule = getattr(spec, "soc_rule", None) if spec is not None else None
    if rule is not None and getattr(rule, "active", False):
        active = _awarded_by_top(colleges, tuple(recent_award_years(1)))
        offered = {t for t in offered if active.get(t, 0) > 0}
    soc_map = top6_to_soc(list(offered))
    gate = spec.in_scope if spec is not None else is_vocational
    out: dict[str, set] = {}
    for t in offered:
        if gate(t):
            for soc in soc_map.get(t, set()):
                out.setdefault(soc, set()).add(t)
    return {k: frozenset(v) for k, v in out.items()}


@lru_cache(maxsize=512)
def _awarded_by_top(colleges: tuple[str, ...], years: tuple[str, ...]) -> dict[str, int]:
    """{top6 -> total completions (All Awards)} over the colleges and years, once."""
    with get_driver().session() as s:
        rows = s.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear) "
            "WHERE p.college IN $c AND ay.year IN $y "
            "RETURN p.top6 AS t, sum(coalesce(a.count, 0)) AS n",
            c=list(colleges), y=list(years)).data()
    return {r["t"]: r["n"] for r in rows}


def feeders(colleges, soc: str, *, spec=None) -> frozenset[str]:
    """The SOC's feeder TOP6s the colleges offer — the one feeder rule (in_scope when a spec is
    given, adjudication A; legacy is_vocational otherwise)."""
    return _soc_feeders(tuple(sorted(set(colleges))), spec).get(soc, frozenset())


def supply(colleges, soc: str, *, years: tuple[str, ...] | None = None, spec=None) -> float:
    """Canonical annual supply for a SOC over a set of colleges. THE single resolution
    path for every supply figure. Default window = most recent 3 years (projected_supply);
    pass ``years=recent_award_years(1)`` for the latest year (latest_year_supply). ``spec``
    selects the canonical in_scope feeder rule (adjudication A)."""
    yrs = years if years is not None else recent_award_years()
    fs = feeders(colleges, soc, spec=spec)
    if not fs or not yrs:
        return 0.0
    aw = _awarded_by_top(tuple(sorted(set(colleges))), tuple(yrs))
    total = sum(aw.get(t, 0) for t in fs)
    return round(total / len(yrs), 1)


def supply_over_socs(colleges, socs, *, years: tuple[str, ...] | None = None, spec=None) -> float:
    """Aggregate supply over a SET of SOCs (a sector total). Feeders are DEDUPED across
    the SOCs — a TOP6 that feeds several occupations is counted once — so a sector total
    never double-counts, unlike summing per-SOC supply. ``spec`` selects the canonical
    in_scope feeder rule (adjudication A)."""
    yrs = years if years is not None else recent_award_years()
    fs: set[str] = set()
    for soc in socs:
        fs |= feeders(colleges, soc, spec=spec)
    if not fs or not yrs:
        return 0.0
    aw = _awarded_by_top(tuple(sorted(set(colleges))), tuple(yrs))
    return round(sum(aw.get(t, 0) for t in fs) / len(yrs), 1)


def _tops_avg(colleges, tops, years: tuple[str, ...] | None) -> float:
    """UNROUNDED annual awards over tops+colleges. Callers that SUM per-college (the builders'
    seam) must sum this and round ONCE — summing per-college ``round(x, 1)`` values otherwise
    accumulates rounding and breaks referential integrity against the aggregate ``supply()``."""
    yrs = years if years is not None else recent_award_years()
    if not tops or not yrs:
        return 0.0
    aw = _awarded_by_top(tuple(sorted(set(colleges))), tuple(yrs))
    return sum(aw.get(t, 0) for t in tops) / len(yrs)


def supply_over_tops(colleges, tops, *, years: tuple[str, ...] | None = None) -> float:
    """Annual supply over an EXPLICIT set of feeder TOP6s — the builders' basis (they resolve
    feeders via ``LandscapeSpec.in_scope``, a richer rule than the sector crosswalk, so they
    pass their own tops rather than a SOC). Graph awards over those tops+colleges, averaged
    over the window. The store-level twin of ``supply``/``supply_over_socs``; every supply
    figure — per-SOC, per-sector, or per-feeder-set — resolves through this same query."""
    return round(_tops_avg(colleges, tops, years), 1)


# ── Enrollment (the leading-indicator twin of the award functions above) ──────
_ENROLL_TERMS = 3   # trailing window (in same-season terms) the enrollment trend averages over


@lru_cache(maxsize=1)
def _enrollment_terms() -> tuple[str, ...]:
    """Distinct non-excluded enrollment terms, most-recent first. Term strings ("Fall 2025")
    do NOT sort lexically, so order by ``_term_sort_key`` (year, season) — the SAME term axis /
    exclusions (Summer + export-boundary terms) the builders' enrollment trend uses."""
    with get_driver().session() as s:
        terms = [r["t"] for r in s.run("MATCH (t:Term) RETURN DISTINCT t.term AS t").data()]
    return tuple(sorted((t for t in terms if t and not _term_excluded(t)),
                        key=_term_sort_key, reverse=True))


def recent_enrollment_terms(n: int = _ENROLL_TERMS) -> tuple[str, ...]:
    """The n most-recent non-excluded enrollment terms."""
    return _enrollment_terms()[:n]


def same_season_terms(anchor: str | None = None) -> tuple[str, ...]:
    """Non-excluded terms sharing the anchor's season (default: the latest term), most-recent
    first — the seasonally-aligned window the enrollment trend compares WITHIN (Fall vs Falls),
    so a Fall↔Spring comparison never reads as a spurious trend the way a mixed-season ratio would."""
    allt = _enrollment_terms()
    if not allt:
        return ()
    season = (anchor or allt[0]).split()[0]
    return tuple(t for t in allt if t.split()[0] == season)


@lru_cache(maxsize=512)
def _enrolled_by_top(colleges: tuple[str, ...], terms: tuple[str, ...]) -> dict[str, int]:
    """{top6 -> total ENROLLED count} over the colleges and terms, once. The enrollment twin of
    ``_awarded_by_top`` (sums the ``(:Program)-[:ENROLLED]->(:Term)`` edge count)."""
    if not terms:
        return {}
    with get_driver().session() as s:
        rows = s.run(
            "MATCH (p:Program)-[e:ENROLLED]->(t:Term) "
            "WHERE p.college IN $c AND t.term IN $terms "
            "RETURN p.top6 AS top6, toInteger(sum(coalesce(e.count, 0))) AS n",
            c=list(colleges), terms=list(terms)).data()
    return {r["top6"]: r["n"] for r in rows}


def enrollment_over_tops(colleges, tops, *, terms: tuple[str, ...] | None = None) -> float:
    """Average per-term enrollment over a set of TOP6s — Σ ENROLLED count ÷ term count. The
    enrollment twin of ``supply_over_tops`` (Σ awards ÷ year count); every enrollment figure
    resolves through this one query."""
    ts = terms if terms is not None else recent_enrollment_terms()
    if not tops or not ts:
        return 0.0
    en = _enrolled_by_top(tuple(sorted(set(colleges))), tuple(ts))
    return round(sum(en.get(t, 0) for t in tops) / len(ts), 1)


def supply_fn_graph(tops, college: str) -> tuple[list, float]:
    """Adapter matching the builders' ``supply_fn`` seam signature ``(tops, college) ->
    (estimates, total)``, backed by the graph instead of the COE CSV. The estimates list is
    empty — both seam consumers (landscape_build's per-college loop, _consortium_supply's
    member sum) read only the total. Returns the UNROUNDED per-college figure so the caller's
    sum, rounded once, equals the aggregate ``supply()`` exactly (referential integrity).
    This repoints the dashboard/report supply onto the one canonical store (S3): the builders
    sum per-college graph supply exactly as they summed per-college COE completions."""
    return [], _tops_avg([college], set(tops), None)


def gap(demand, supply) -> int:
    """THE single gap expression: annual regional openings − annual supply, rounded to a
    whole opening. Openings and supply are each treated as 0 when absent, so a SOC with
    demand but no supply reports the full opening count (not a crash), and vice-versa.
    Every surface that reports a gap composes this, so the arithmetic can't drift."""
    return int(round((demand or 0) - (supply or 0)))


def program_socs(program: str, within=None) -> frozenset:
    """A program's (TOP6's) is_vocational crosswalk occupations (χ, TOP6→CIP→SOC), optionally
    intersected with a bounding SOC set (a sector's occupations). The supply-side program
    projected DOWN the crosswalk — the occupations a graduate of this program is qualified for."""
    if not is_vocational(program):
        return frozenset()
    socs = top6_to_soc([program]).get(program, set())
    return frozenset(socs & set(within)) if within is not None else frozenset(socs)


def addressable_demand(program: str, sector_socs, demand_by_soc) -> tuple:
    """A program's occupations within the sector and the sum-across pool of their regional
    openings (χ↑) — the demand this program is qualified to compete for. ``demand_by_soc`` is
    {soc: openings}, passed IN (this layer never fetches demand, exactly like ``gap``). The pool
    is summed at FULL value (the crosswalk is a qualification classification, defensible as COE's
    own method); it is a PER-PROGRAM figure and is never summed across programs, because the
    fan-out means programs share occupations. Returns (occupations_in_sector, addressable_demand)."""
    socs = program_socs(program, within=sector_socs)
    return socs, int(round(sum((demand_by_soc.get(s) or 0) for s in socs)))


def vintage(years: tuple[str, ...]) -> str:
    """The honest vintage string for a supply window — stated, not faked."""
    if len(years) == 1:
        return f"DataMart completions — {years[0]}"
    return f"{len(years)}-yr avg DataMart completions ({years[-1]}…{years[0]})"


# ── Wage outcomes — the pooled statewide graduate-wage cohort (graph-backed) ──
# Read from the ProgramWageOutcome nodes (loaded by ontology.programs), NOT the CSV:
# the comparison engine composes ONLY canonical graph resolvers. Wages are statewide
# and pooled at the TOP6 grain (no college dimension), so these resolve BY TOP6 — a
# member's own-graduate wage is never manufactured.

def _wage_selection_key(rec: dict) -> tuple:
    """The deterministic pick order across a TOP6's recipient-type cohorts: the LARGEST
    award cohort first (max Total Awards n), tiebreak higher 2-yr wage, then recipient
    type ascending. Picks ONE natively-measured median — never a weighted blend across
    recipient types (that would be a composite: a program wage invented by averaging a
    finer grain). The oracle in test_compare re-derives this same key from the CSV."""
    return (-(rec.get("n") or 0), -(rec.get("wage_after_2") or 0), rec.get("recipient_type") or "")


@lru_cache(maxsize=1024)
def _wage_records(top6: str) -> tuple[dict, ...]:
    """A TOP6's pooled statewide graduate-wage cohorts from the graph, most-representative
    first (``_wage_selection_key``). Empty tuple if the program reports no cohort."""
    with get_driver().session() as s:
        rows = s.run(
            "MATCH (w:ProgramWageOutcome {top6: $t}) "
            "RETURN w.recipient_type AS recipient_type, w.wage_before AS wage_before, "
            "w.wage_after_2 AS wage_after_2, w.wage_after_5 AS wage_after_5, "
            "w.n AS n, w.window AS window",
            t=top6).data()
    return tuple(sorted(rows, key=_wage_selection_key))


def program_wage_outcome(top6: str) -> dict | None:
    """THE representative graduate-wage record for a TOP6 program (statewide, pooled) —
    its largest award cohort per ``_wage_selection_key``, or None if none is reported.
    Every wage criterion composes this ONE resolver, so a program's lift and its 2-/5-yr
    levels are read from the SAME cohort (internally consistent) and cannot drift."""
    recs = _wage_records(top6)
    return dict(recs[0]) if recs else None


@lru_cache(maxsize=1)
def wage_window() -> str:
    """The pooled award-cohort window the wage medians span (uniform across the DataMart
    export) — the wage criterion's vintage. '' when no wage outcomes are loaded."""
    with get_driver().session() as s:
        row = s.run("MATCH (w:ProgramWageOutcome) WHERE w.window IS NOT NULL "
                    "RETURN w.window AS win LIMIT 1").single()
    return (row["win"] if row else "") or ""


# ── OFFERING — the college roster for a program (referential integrity, layer 2) ──
# `colleges_offering` disagreed across tools because occupation_profile counted Program
# NODES while the builders counted 09 COURSES (a demonstrable undercount — colleges that
# award a credential but have no course records were dropped). One canonical roster here,
# program-grain, matching the dashboard's coverage-matrix classification (covered = enrolled
# AND awarded; partial = one; gap = on the books but neither). Every tool composes it, so the
# count and the named set agree.

def coverage(enrolled: bool, awards: int, *, awards_only: bool = False) -> str:
    """Classify one (college × program) cell — THE single coverage predicate.

    Default (SVAMP, ruleless): covered = enrolled AND awarding; partial = either signal
    alone; gap = neither. ``awards_only=True`` (rule-bearing instances — BACCC, sector-derived
    SMCCD): a cell enrolled but not yet AWARDING is a gap, not partial (no completer = no
    supply); a cell awarding but no longer enrolled stays partial (real-but-thinning supply).
    Enrollment then only upgrades an awarding cell partial→covered, never creates partial alone."""
    has_award = awards > 0
    if awards_only:
        if has_award and enrolled:
            return "covered"
        if has_award:
            return "partial"
        return "gap"
    if enrolled and has_award:
        return "covered"
    if enrolled or has_award:
        return "partial"
    return "gap"


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
        # ruleless (roster context): enrolled-OR-awarded classification
        return coverage(self.enrolled, self.awards)


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
