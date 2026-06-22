"""L1 — the lens model: the ontology projected over a scope, as one neutral,
provenance-carrying data structure that BOTH artifacts render from.

The architecture is one substrate, two renderers (see
[memory: project_artifact_architecture]):

    L0 ontology (graph)  ──build_lens(scope)──▶  L1 LensModel  ──▶  dashboard (explore)
                                                              └──▶  report  (persuade)

The cardinal rule: a renderer never computes its own numbers — it selects from
the LensModel. If the dashboard and the report each reached into the graph their
own way they would drift and contradict each other, which is fatal to a
credibility product. So this module is the single projection both consume.

Design commitments (deliberate, see compare-clustered.html):
  - The OCCUPATION is the atom. Rows are occupation-grain and ranked by annual
    openings — the clean, demand-side signal. No clustering headline (clustering
    would conflate distinct jobs/wages/employers); no opinionated score
    (anchor/member/peripheral is gone). The connected-component machinery is
    plumbing for the partner graph, never a unit the user sees.
  - Supply is shown per-SOC as the PARTNER GRAPH (which consortium schools feed
    this occupation) and is NEVER summed across occupations into an aggregate
    gap — a program feeding three SOCs contributes to each, so a cross-occupation
    sum would double-count. Lead with openings; supply is the coalition signal.
  - PROVENANCE is first-class: every figure traces to its institutional authority
    (see SOURCES / FIELD_AUTHORITY). The authoritative grounding is the value
    proposition; both surfaces cite it.

A scope is `(member, slice)`:
  - slice = sector  → the whole field of occupations (the dashboard's view)
  - slice = play    → a curated occupation set + a title (the report's view); the
    play inherits the sector's pool + region and just narrows the occupations.

Competencies (O*NET KSA) are intentionally absent here — they are not in the
graph; they are editorial Spec-side enrichment authored into a report, not L1.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Sequence

from ontology.crosswalks import top6_to_soc
from ontology.schema import get_driver
from partnerships import members
from partnerships.clusters import cluster_expanded_spec
from partnerships.employer_relevance import rank_employers
from partnerships.graph_reads import (
    latest_academic_year,
    program_award_series,
    program_awards,
    program_enrollment_series,
    program_names,
    regional_demand,
)
from partnerships.registry import spec_for
from partnerships.resolve import resolve
from partnerships.sectors import SECTORS

EMPLOYERS_PER_OCC = 8


# ── Provenance — the institutional authority behind each figure ───────────────
@dataclass(frozen=True)
class SourceRef:
    id: str
    authority: str
    role: str


SOURCES: dict[str, SourceRef] = {
    "onet": SourceRef("onet", "O*NET (U.S. Dept. of Labor)", "selects occupations + titles"),
    "coe": SourceRef("coe", "Centers of Excellence", "regional demand, wage, growth"),
    "datamart": SourceRef("datamart", "CCCCO DataMart", "program supply (awards)"),
    "graph_bls": SourceRef("graph_bls", "BLS OEWS staffing patterns", "employer relevance"),
}

# Which authority grounds each lens field — identical for every occupation, so it
# lives once on the model rather than being repeated per row.
FIELD_AUTHORITY: dict[str, str] = {
    "title": "onet",
    "description": "onet",
    "annual_openings": "coe",
    "median_wage": "coe",
    "growth_rate": "coe",
    "feeders": "datamart",
    "employers": "graph_bls",
}


# ── The neutral lens model (artifact-agnostic) ────────────────────────────────
@dataclass(frozen=True)
class MemberRef:
    id: str
    name: str
    kind: str  # college | district | region | consortium


@dataclass(frozen=True)
class LensFeeder:
    """One (college, program) that feeds this occupation, with its latest-year
    completers. `is_member` is a FACT — does this college belong to the scope
    member — never a role or a score."""
    college: str
    top6: str
    program: str
    awards: int
    is_member: bool


@dataclass(frozen=True)
class LensEmployer:
    name: str
    naics4: str | None
    relevance: float  # this firm's BLS staffing share (pct_total) for THIS soc


@dataclass(frozen=True)
class LensOccupation:
    """The atom. Demand [COE], partner graph [DataMart], employers [graph/BLS]."""
    soc: str
    title: str
    description: str | None
    region: str
    annual_openings: int          # the ranking key
    median_wage: int              # regional occupational median (demand-side, NOT grad earnings)
    growth_rate: float
    feeders: list[LensFeeder]     # the partner graph — who feeds this occupation
    member_feeds: bool            # does the scope member feed it?
    employers: list[LensEmployer]


@dataclass(frozen=True)
class LensProgram:
    """Program-grain supply over time — one (college, TOP6) that feeds the scope's
    occupations, with its full award + enrollment series. Drives the report's
    award/enrollment trend tables and the dashboard's program trends. Distinct
    from `LensFeeder` (occupation-grain, latest-year): a program appears here even
    if its current awards are 0 but it has enrollment (a live, not-yet-completing
    pipeline). Series are NEVER summed across occupations — this is program-grain."""
    college: str
    top6: str
    program: str
    is_member: bool
    socs: list[str]               # the scope occupations this program feeds (crosswalk edges)
    awards: dict[str, int]        # {academic_year -> awards}, full history
    enrollment: dict[str, int]    # {term -> count}, full history


@dataclass(frozen=True)
class LensSlice:
    kind: str           # "sector" | "play"
    id: str
    label: str
    title: str | None = None


@dataclass(frozen=True)
class LensScope:
    member: MemberRef
    regions: tuple[str, ...]
    slice: LensSlice
    partner_universe: tuple[str, ...]  # the colleges in the pool (the partner candidates)


@dataclass(frozen=True)
class LensModel:
    scope: LensScope
    occupations: list[LensOccupation]  # ranked by annual_openings desc
    programs: list[LensProgram] = field(default_factory=list)       # supply over time
    award_years: list[str] = field(default_factory=list)            # axis, sorted asc
    enrollment_terms: list[str] = field(default_factory=list)       # axis, sorted asc
    sources: list[SourceRef] = field(default_factory=lambda: list(SOURCES.values()))

    def to_dict(self) -> dict:
        return {
            "scope": {
                "member": vars(self.scope.member),
                "regions": list(self.scope.regions),
                "slice": vars(self.scope.slice),
                "partner_universe": list(self.scope.partner_universe),
            },
            "occupations": [
                {
                    "soc": o.soc, "title": o.title, "description": o.description,
                    "region": o.region, "annual_openings": o.annual_openings,
                    "median_wage": o.median_wage, "growth_rate": o.growth_rate,
                    "member_feeds": o.member_feeds,
                    "feeders": [vars(f) for f in o.feeders],
                    "employers": [vars(e) for e in o.employers],
                }
                for o in self.occupations
            ],
            "programs": [vars(p) for p in self.programs],
            "award_years": list(self.award_years),
            "enrollment_terms": list(self.enrollment_terms),
            "field_authority": FIELD_AUTHORITY,
            "sources": [vars(s) for s in self.sources],
        }


# ── A play — the curated occupation set behind a report ───────────────────────
@dataclass(frozen=True)
class Play:
    """The editorial selection a report renders: a title + a curated SOC set,
    scoped to a sector (which supplies the pool + region). "Data proposes, human
    confirms": an O*NET title→SOC match proposes the set; a human authors it here."""
    id: str
    title: str
    sector: str
    socs: tuple[str, ...]


# ── Member identity (graph-free, from the catalog) ────────────────────────────
@lru_cache(maxsize=256)
def _member_ref(member_id: str) -> MemberRef:
    for name in members.all_colleges():
        if members.college_member(name).id == member_id:
            return MemberRef(member_id, name, "college")
    for d in members.all_districts():
        if members.district_member(d).id == member_id:
            return MemberRef(member_id, d, "district")
    for r in members.all_regions():
        m = members.region_member(r)
        if m.id == member_id:
            return MemberRef(member_id, m.label, "region")
    return MemberRef(member_id, member_id, "consortium")


# ── The projection ────────────────────────────────────────────────────────────
def _project(
    s,
    region: str,
    colleges: Sequence[str],
    in_scope_tops: Sequence[str],
    socs: Sequence[str],
    member_colleges: frozenset[str],
) -> list[LensOccupation]:
    """Project the graph onto the occupation universe. Four reads on the caller's
    session; every per-occupation view is derived in memory so they can't diverge."""
    if not socs:
        return []
    demand = regional_demand(s, region, socs)
    award_rows = program_awards(s, colleges, in_scope_tops, latest_academic_year(s))
    names = program_names(s, in_scope_tops)
    ranked = rank_employers(s, region=region, target_socs=socs)

    # Supply: awarded TOP6 -> [(college, awards)] (latest year).
    top_by_college: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for r in award_rows:
        top_by_college[r["top6"]].append((r["college"], r["n"]))
    awarded = sorted(top_by_college)
    # Which awarded programs feed each SOC (the partner-graph edges).
    t2s = top6_to_soc(awarded) if awarded else {}
    feeders_of = {soc: [t for t in awarded if soc in t2s.get(t, set())] for soc in socs}

    # Employers per SOC, derived from the single ranked read's per-SOC shares.
    emp_by_soc: dict[str, list[tuple[float, object]]] = defaultdict(list)
    for e in ranked:
        for soc, pct in e.soc_pct.items():
            emp_by_soc[soc].append((pct, e))

    occs: list[LensOccupation] = []
    for soc in socs:
        d = demand.get(soc, {})
        feeders = [
            LensFeeder(college=college, top6=t, program=names.get(t, t), awards=n,
                       is_member=college in member_colleges)
            for t in sorted(feeders_of[soc])
            for college, n in sorted(top_by_college[t], key=lambda x: (-x[1], x[0]))
        ]
        emps = sorted(emp_by_soc.get(soc, []), key=lambda pe: (-pe[0], pe[1].name))[:EMPLOYERS_PER_OCC]
        occs.append(LensOccupation(
            soc=soc,
            title=d.get("title") or soc,
            description=d.get("description"),
            region=region,
            annual_openings=d.get("annual_openings") or 0,
            median_wage=d.get("annual_wage") or 0,
            growth_rate=d.get("growth_rate") or 0.0,
            feeders=feeders,
            member_feeds=any(f.is_member for f in feeders),
            employers=[LensEmployer(name=e.name, naics4=e.naics4, relevance=round(pct, 4))
                       for pct, e in emps],
        ))
    occs.sort(key=lambda o: (-o.annual_openings, o.soc))
    return occs


def _programs(
    s,
    colleges: Sequence[str],
    top_socs: dict[str, set],
    member_colleges: frozenset[str],
) -> tuple[list[LensProgram], list[str], list[str]]:
    """Program-grain supply over time for the TOP6s that feed the scope's
    occupations: the award + enrollment series per (college, TOP6), plus the SOCs
    each feeds (`top_socs`). A program with enrollment but zero current awards
    still appears — a live pipeline."""
    relevant_tops = list(top_socs)
    if not relevant_tops:
        return [], [], []
    aw = program_award_series(s, colleges, relevant_tops)
    en = program_enrollment_series(s, colleges, relevant_tops)
    names = program_names(s, relevant_tops)

    award_years = sorted({r["year"] for r in aw})
    enrollment_terms = sorted({r["term"] for r in en})
    awards: dict[tuple, dict[str, int]] = defaultdict(dict)
    enroll: dict[tuple, dict[str, int]] = defaultdict(dict)
    for r in aw:
        awards[(r["college"], r["top6"])][r["year"]] = r["awards"]
    for r in en:
        enroll[(r["college"], r["top6"])][r["term"]] = r["count"]

    keys = sorted(set(awards) | set(enroll))
    programs = [
        LensProgram(
            college=college, top6=top6, program=names.get(top6, top6),
            is_member=college in member_colleges,
            socs=sorted(top_socs.get(top6, set())),
            awards=dict(awards.get((college, top6), {})),
            enrollment=dict(enroll.get((college, top6), {})),
        )
        for college, top6 in keys
    ]
    return programs, award_years, enrollment_terms


# ── The public entry point ────────────────────────────────────────────────────
@lru_cache(maxsize=512)
def build_lens(member_id: str, *, sector: str | None = None, play: Play | None = None,
               extra_colleges: tuple[str, ...] = ()) -> LensModel:
    """Project the ontology onto a `(member, slice)` scope → the neutral LensModel.

    Exactly one of `sector` (dashboard: the whole field) or `play` (report: a
    curated occupation set + title) must be given. A single-college member is
    expanded to its consortium pool, so the partner graph spans peer schools.

    Result-memoized: the projection is deterministic for a fixed graph, so repeated
    (member, slice) requests serve the cached LensModel near-instantly. The returned
    model is shared and read-only — callers must not mutate it. Process-lifetime;
    a graph data load should restart the backend (init_schema) to refresh, matching
    the precompute serving cache + cluster_map memoization in this layer.
    """
    if (sector is None) == (play is None):
        raise ValueError("pass exactly one of sector= or play=")
    sector_id = sector if sector is not None else play.sector

    # Generated members resolve as "{member}-{sector}"; pinned single-instance
    # consortia (e.g. SVAMP, whose charter IS one sector) resolve as the bare id.
    base = spec_for(f"{member_id}-{sector_id}") or spec_for(member_id)
    if base is None:
        raise LookupError(f"no landscape spec for {member_id}-{sector_id}")

    member_colleges = frozenset(base.colleges)
    # Expand a lone college to its consortium so the partner graph has peers.
    pool = cluster_expanded_spec(base, sector_id) if len(base.colleges) == 1 else base
    region = pool.resolve_region()
    in_scope = list(pool.in_scope_tops())
    colleges = list(pool.colleges)
    # Charter partners outside the cluster pool (e.g. a SVAMP member the BACCC
    # expansion doesn't reach) — added to the supply scope so their programs are
    # readable even when carried by enrollment rather than awards. is_member stays
    # False; they are partners, not the scope member.
    for c in extra_colleges:
        if c not in colleges:
            colleges.append(c)

    if sector is not None:
        socs = list(resolve(pool).socs)
        slice_ = LensSlice(kind="sector", id=sector_id,
                           label=SECTORS[sector_id].label if sector_id in SECTORS else sector_id)
    else:
        socs = list(dict.fromkeys(play.socs))  # dedup, preserve authored order
        slice_ = LensSlice(kind="play", id=play.id, label=play.title, title=play.title)

    # The TOP6s feeding the scope's occupations — the program universe for the
    # supply-over-time series (graph-free crosswalk lookup).
    soc_set = set(socs)
    t2s = top6_to_soc(list(in_scope)) if in_scope else {}
    top_socs = {t: (t2s.get(t, set()) & soc_set) for t in in_scope if t2s.get(t, set()) & soc_set}

    with get_driver().session() as s:
        occupations = _project(s, region, colleges, in_scope, socs, member_colleges)
        programs, award_years, enrollment_terms = _programs(
            s, colleges, top_socs, member_colleges)

    scope = LensScope(
        member=_member_ref(member_id),
        regions=(region,) if region else (),
        slice=slice_,
        partner_universe=tuple(sorted(colleges)),
    )
    return LensModel(scope=scope, occupations=occupations, programs=programs,
                     award_years=award_years, enrollment_terms=enrollment_terms)


if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "foothill"
    sec = sys.argv[2] if len(sys.argv) > 2 else "adm"
    print(json.dumps(build_lens(mid, sector=sec).to_dict(), indent=2))
