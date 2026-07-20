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
  - reachable_only : keep SOCs a member program in the spec's program portfolio
                     (composition.programs, or the sector's home_sector set) reaches
  - non_empty_only : keep SOCs whose reaching member program has AWARDS
                     (completers) in the LATEST reported year — awards are the
                     supply metric and supply is the current year's completers, so
                     enrollment-only AND dormant (older-year-only) programs aren't
                     realized supply. The same gate runs at the program grain in
                     landscape_programs.relevant_tops (such programs never enter the
                     matrix/treemap).
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict

from ontology.crosswalks import crosswalk_socs
from ontology.schema import get_driver
from partnerships.graph_reads import regional_demand
from partnerships.landscape import LandscapeSpec
from partnerships.quantities import (
    member_program_tops,
    producing_top_colleges,
    producing_tops,
)
from partnerships.sectors import (
    ALL_OTHER_SOCS,
    EXPERIENCE_5YR_SOCS,
    PROMOTION_SOCS,
    SectorRule,
)


def soc_in_demand(
    soc: str, *, openings: float | None, wage: float | None, rule: SectorRule
) -> bool:
    """Demand-quality gate for ONE occupation — member-independent (openings/wage × region).

    The single birthplace of the in_demand predicate: sector_lenses composes it over a SOC set to derive
    the in_demand lens, and the landscape build stamps each cell with it so a surface can split priority
    (in-demand) occupations from the rest. Two gates, NO curated exceptions: openings must strictly exceed
    the floor (`>`), wage meets it (`>=`). Curated priority (a sector authority naming a strategic occupation
    below the floor) belongs to the AUTHORED composition path — which marks all its SOCs in-demand and never
    reaches this gate — not to this default rule, so the default priority bar reads exactly as its criteria
    state. (The non-declining-growth gate was dropped 2026-07-18 — a declining field can still be a real,
    staffable market — so growth no longer gates.)"""
    if rule.min_openings and (openings or 0) <= rule.min_openings:
        return False
    if rule.min_wage and (wage or 0) < rule.min_wage:
        return False
    return True


def sector_lenses(spec: LandscapeSpec) -> dict:
    """The sector's occupation-set at each decomposed grain — the WHATs a surface can project:
      full      — the sector's occupations (PCAH membership)
      in_demand — full ∩ demand-quality (real openings, near-living-wage, non-declining): "is there a market?"
      served    — full ∩ member-engaged (reachable, active, consortium-floor): "is the member in it?"
      effective — in_demand ∩ served (the set the dashboard shows today)
    Identity (every lens = full) for an AUTHORED spec (SVAMP's occupations are hand-picked = final) or a
    no-rule spec, trusted as authored — the lenses derive a subset only when the occupations are derived."""
    rule = spec.soc_rule
    full = tuple(spec.socs)
    socs = list(spec.socs)
    if spec.composition.is_authored or rule is None or not rule.active:
        return {"full": full, "in_demand": full, "served": full, "effective": full}

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

    # The member's offered programs (reachability) and their PRODUCING subset both resolve through the
    # shared gate (quantities.producing_tops / producing_top_colleges), so resolve, relevant_tops and
    # _soc_feeders decide "which programs count" ONE way. "Producing" = a feeding program with AWARDS in the
    # latest reported year — supply is the current year's completers, the same year the coverage-matrix cells
    # display; a program that awarded only in older years is dormant and drops (e.g. 210530 Industrial &
    # Transp. Security), so a row never shows all-empty latest cells. top_colleges gives the distinct
    # producing colleges per occupation for the min_colleges floor. Step 2 widens the window + unions
    # enrollment in those two helpers, in one place.
    prog_tops = member_program_tops(tuple(spec.colleges))
    active_tops = producing_tops(spec.colleges, prog_tops)
    top_colleges = producing_top_colleges(spec.colleges, prog_tops)

    # SOC -> reachable / active via the spec's IN-SCOPE TOPs the member offers —
    # in_scope is membership in the spec's program portfolio (composition.programs when
    # authored, else the sector's home_sector set), so this stays consistent with the
    # displayed feeder universe (relevant_tops).
    voc = spec.in_scope_tops()
    reachable: set[str] = set()
    active: set[str] = set()
    soc_colleges: dict[str, set[str]] = defaultdict(set)
    for top6, fed in crosswalk_socs(voc).items():
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

    # The effective set = trainable-sector-membership ∩ IN-DEMAND ∩ SERVED. The two gates are named and
    # independent (order-free), so the decomposition is explicit and each is separately usable as a lens:
    # `in_demand` asks "is there a real market?" (occupation × region — member-independent); `served` asks
    # "is the member in it?" (member × sector). Their intersection is what the dashboard shows today; Phase
    # B exposes each on its own so a small effective set reads as "small market" vs "I don't serve it".
    def in_demand(soc: str) -> bool:
        # The demand-quality gate lives in the module-level soc_in_demand (one birthplace, shared with the
        # landscape build's per-cell stamp); here it's composed over the SOC set.
        return soc_in_demand(
            soc, openings=openings.get(soc), wage=wages.get(soc), rule=rule
        )

    def served(soc: str) -> bool:
        # Member-engaged gate: the member offers a feeding program (reachable), actively graduates into it
        # (active), and — for a genuine multi-college consortium — enough colleges produce it that there is
        # a partnership to broker (the consortium floor; single-college occupations are self-contained and
        # justified by demand alone, so out of scope for the consortium's coordination view).
        if rule.reachable_only and soc not in reachable:
            return False
        if rule.non_empty_only and soc not in active:
            return False
        if min_colleges > 1 and len(soc_colleges.get(soc, ())) < min_colleges:
            return False
        return True

    in_demand_socs = tuple(soc for soc in socs if in_demand(soc))
    served_socs = tuple(soc for soc in socs if served(soc))
    effective = tuple(soc for soc in socs if in_demand(soc) and served(soc))
    return {"full": full, "in_demand": in_demand_socs, "served": served_socs, "effective": effective}


def effective_socs(spec: LandscapeSpec) -> tuple[str, ...]:
    """The sector rule's effective set = in_demand ∩ served — the dashboard's current WHAT. A thin
    projection of sector_lenses so the decomposition has one birthplace."""
    return sector_lenses(spec)["effective"]


def resolve(spec: LandscapeSpec) -> LandscapeSpec:
    """Return spec with .socs narrowed to its sector rule's set (sector-derived instances).
    Identity — and no graph access — for an AUTHORED spec (SVAMP's occupations are the curation, never
    filtered) or a no-rule spec. This branches on the Composition, not the rule, so an authored spec may
    still carry an active rule (its programs run the universal gate; only its occupation set stays final).

    Every view — single-college self-view AND multi-college consortium — narrows to the SERVED set (the
    occupations the member offers AND actively graduates into). The priority-job in_demand gate (openings /
    wage / growth) is no longer a HARD FILTER that deletes rows; it is a display-time PRIORITY HIGHLIGHT the
    surface applies over served (LandscapeCell.in_demand + Landscape.demand_criteria), so the coordination
    priorities (= effective = served ∩ in_demand) lead by default and the rest collapse one click away rather
    than vanish. One rule everywhere — show served, highlight in_demand — replaces the served-vs-effective
    fork: a college reading itself and a consortium reading its region now share a WHAT. effective survives
    only as the highlighted subset, still exposed by sector_lenses / effective_socs for callers that need it."""
    if spec.composition.is_authored or spec.soc_rule is None or not spec.soc_rule.active:
        return spec
    socs = sector_lenses(spec)["served"]
    return dataclasses.replace(spec, socs=socs)
