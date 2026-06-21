"""Resolve a LandscapeSpec's effective SOC set by applying its sector's
SectorRule (sectors.SectorRule) against live demand + member supply.

This is the durable replacement for hand-deleting rows from sector_socs.csv: the
committed SOC list stays the full generated middle-skill set, and the rule trims
it at request time. Because it reads the live graph (regional demand, member
programs) it is region- and member-aware and survives a sector_socs.csv
regeneration. The curated SVAMP instance carries soc_rule=None and resolves to a
no-op (it is the only soc_rule=None instance today — smccd-adm is hand-built on
the colleges/vocational axes but rule-bearing for SOC narrowing).

The three rule dimensions:
  - min_openings   : keep SOCs whose regional annual openings exceed the floor
  - reachable_only : keep SOCs a member program reaches via the vocational
                     crosswalk (is_vocational TOP, minus the spec's excluded_tops)
  - non_empty_only : keep SOCs whose reaching member program has AWARDS
                     (completers) in the LATEST reported year — awards are the
                     supply metric and supply is the current year's completers, so
                     enrollment-only AND dormant (older-year-only) programs aren't
                     realized supply. The same gate runs at the program grain in
                     svamp_programs.relevant_tops (such programs never enter the
                     matrix/treemap).
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict

from ontology.crosswalks import top6_to_soc
from ontology.schema import get_driver
from partnerships.graph_reads import latest_academic_year, regional_demand
from partnerships.landscape import LandscapeSpec
from partnerships.sectors import (
    ALL_OTHER_SOCS,
    EXPERIENCE_5YR_SOCS,
    GROWTH_EXEMPT_SOCS,
    INCLUDE_SOCS,
    PROMOTION_SOCS,
)


def effective_socs(spec: LandscapeSpec) -> tuple[str, ...]:
    """The spec's SOCs narrowed by its sector rule. Identity (full set) when the
    spec has no active rule."""
    rule = spec.soc_rule
    socs = list(spec.socs)
    if rule is None or not rule.active:
        return tuple(socs)   # curated/no-rule specs (e.g. SVAMP) trusted as authored

    # Sector-derived instances only: drop 5+yr-experience occupations, "all other"
    # catch-all SOCs (non-specific roll-ups), and promotion/management roles
    # (PROMOTION_SOCS — supervisors/managers/detectives a CC doesn't train for;
    # the employer promotes the line worker the CC already produced) before the
    # demand rule. Curated specs above keep their hand-authored SOC set.
    socs = [
        s for s in socs
        if s not in EXPERIENCE_5YR_SOCS
        and s not in ALL_OTHER_SOCS
        and s not in PROMOTION_SOCS
    ]

    region = spec.resolve_region()
    with get_driver().session() as session:
        demand = regional_demand(session, region, socs)
        openings = {s: dr["annual_openings"] for s, dr in demand.items()}
        wages = {s: dr["annual_wage"] for s, dr in demand.items()}
        growth = {s: dr["growth_rate"] for s, dr in demand.items()}
        latest = latest_academic_year(session)
        progs = session.run(
            "MATCH (p:Program) WHERE p.college IN $colleges "
            "RETURN p.college AS college, p.top6 AS top6, "
            "reduce(a=0, x IN [(p)-[r:AWARDED]->(ay:AcademicYear) WHERE ay.year = $latest "
            "| r.count] | a + coalesce(x, 0)) AS aw",
            colleges=list(spec.colleges), latest=latest,
        ).data()

    prog_tops = {r["top6"] for r in progs}
    # "active" = the member offers a feeding program with AWARDS in the LATEST
    # reported year — supply is the current year's completers, the same year the
    # coverage-matrix cells display. A program that awarded in older years but
    # nothing in the latest year is dormant (e.g. 210530 Industrial & Transp.
    # Security), so it isn't counted and a row never shows all-empty latest cells.
    active_tops = {r["top6"] for r in progs if (r["aw"] or 0) > 0}
    # top6 -> member colleges actually awarding completers in it (latest year) —
    # used to count distinct producing colleges per occupation for min_colleges.
    top_colleges: dict[str, set[str]] = defaultdict(set)
    for r in progs:
        if (r["aw"] or 0) > 0:
            top_colleges[r["top6"]].add(r["college"])

    # SOC -> reachable / active via the spec's IN-SCOPE TOPs the member offers —
    # in_scope applies is_vocational, excluded_tops AND the home-division gate, so
    # this stays consistent with the displayed feeder universe (relevant_tops).
    voc = spec.in_scope_tops()
    reachable: set[str] = set()
    active: set[str] = set()
    soc_colleges: dict[str, set[str]] = defaultdict(set)
    for top6, fed in top6_to_soc(voc).items():
        if top6 in prog_tops:
            reachable |= fed
        if top6 in active_tops:
            active |= fed
            for s in fed:
                soc_colleges[s] |= top_colleges[top6]

    # The consortium floor applies only to genuinely multi-college consortia — a
    # small district (e.g. SMCCD's 3 colleges) would be gutted by ">=2 of 3" (a
    # majority, not an outlier filter), so require membership > twice the floor.
    min_colleges = rule.min_colleges if len(spec.colleges) > 2 * rule.min_colleges else 1

    kept = []
    for soc in socs:
        # INCLUDE_SOCS are curated below-floor admissions (sectors.INCLUDE_SOCS):
        # they bypass the openings floor ONLY, still facing every gate below, so a
        # premium multi-college occupation with thin raw openings is admitted but a
        # loss of its supply still drops it.
        if (
            rule.min_openings
            and (openings.get(soc) or 0) <= rule.min_openings
            and soc not in INCLUDE_SOCS
        ):
            continue
        if rule.min_wage and (wages.get(soc) or 0) < rule.min_wage:
            continue
        # Drop declining occupations (negative regional growth) — a shrinking
        # field is poor program-investment strategy — unless structurally
        # important enough to override (GROWTH_EXEMPT_SOCS, e.g. Eng Techs,
        # Carpenters). Growth is a flag, not a hard cut, for those few.
        if (growth.get(soc) or 0) < 0 and soc not in GROWTH_EXEMPT_SOCS:
            continue
        if rule.reachable_only and soc not in reachable:
            continue
        if rule.non_empty_only and soc not in active:
            continue
        # Consortium floor: an occupation must be produced by >= min_colleges
        # distinct member colleges — a single-college occupation is self-contained
        # (no multi-school partnership to broker) and already justified by demand
        # alone, so it's out of scope for the consortium's coordination view.
        if min_colleges > 1 and len(soc_colleges.get(soc, ())) < min_colleges:
            continue
        kept.append(soc)
    return tuple(kept)


def resolve(spec: LandscapeSpec) -> LandscapeSpec:
    """Return spec with .socs narrowed to its sector rule's effective set
    (sector-derived instances). Identity — and no graph access — for a curated/
    no-rule spec (e.g. SVAMP), which is trusted as authored and never filtered."""
    if spec.soc_rule is None or not spec.soc_rule.active:
        return spec
    return dataclasses.replace(spec, socs=effective_socs(spec))
