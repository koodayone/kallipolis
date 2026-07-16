"""The unified selection engine (Phase A).

`select(coordinate) → Selection` is the ONE resolution path — the preamble every form currently
duplicates inline (`scope_for` → `resolve` → region → college-sets → sector occupations). Centralizing
it is the structural fix for the C class: two forms can no longer resolve the "same" coordinate
differently, because there is one resolution. This phase wraps the existing resolvers verbatim — NO
number change; the characterization net proves each form's output is byte-for-byte unchanged as it moves
onto `select`. `aggregate` (the measure dispatch over a Selection) follows once the forms are on `select`.

Coordinate shape (see research/architecture/UNIFIED-ENGINE-PLAN.md): ⟨WHO, WHAT, WHEN, MEASURE⟩. `select`
resolves WHO (a college-set, with its region derived) and the WHAT's sector occupation-set. The
member-only (portfolio/greenfield) and occupation-anchored (occupation_profile) shapes are folded in as
their forms are converted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ontology.regions import COE_REGION_DISPLAY
from partnerships.members import region_member
from partnerships.resolve import resolve
from partnerships.sectors import SECTORS
from mcp_server import canonical as CAN
from mcp_server.scope import scope_for, sectors_for_member


@dataclass
class Selection:
    """A resolved coordinate scope — WHO (college-sets + derived region) and, when sector-scoped, the
    sector's occupation-set. The concrete inputs every measure needs, resolved once."""
    member: str
    entry: dict                 # the scope-catalog entry
    instance_id: str            # the coordinate's instance id (raw spec.id) — for view_links
    spec: object                # the RESOLVED LandscapeSpec (awards-gate applied) — the forms' `rspec`
    raw_spec: object            # the pre-resolve LandscapeSpec (before the awards-gate) — forms that keep both
    region: str
    region_display: str
    member_colleges: list
    region_colleges: list
    sector_id: Optional[str] = None
    sector_socs: Optional[list] = None
    sector_label: Optional[str] = None


def select(member: str, sector: str) -> Optional[Selection]:
    """Resolve a member×sector coordinate to its Selection — the shared preamble, once. Returns None
    when the coordinate isn't live (the caller emits its own gate, preserving its message)."""
    resolved = scope_for(member, sector)
    if resolved is None:
        return None
    spec, entry = resolved
    rspec = resolve(spec)
    region = rspec.resolve_region()
    sid = entry["sector_id"]
    return Selection(
        member=member,
        entry=entry,
        instance_id=spec.id,
        spec=rspec,
        raw_spec=spec,
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        member_colleges=list(rspec.colleges),
        region_colleges=list(region_member(region).colleges),
        sector_id=sid,
        sector_socs=list(SECTORS[sid].socs),
        sector_label=SECTORS[sid].label,
    )


def select_member(member: str) -> Optional[Selection]:
    """Resolve a member-only coordinate (all sectors) — the base resolution the portfolio/greenfield/
    occupation-profile forms share. Uses the member's FIRST sector to obtain its spec/region/colleges
    (sector_socs=None); those forms apply their own per-sector or occupation logic. Carries the RAW spec
    (not awards-gated), matching what those forms use for the base scope. Returns None when the member
    doesn't resolve — the caller distinguishes 'no such institution' from 'unresolvable' for its gate."""
    sects = sectors_for_member(member)
    if not sects:
        return None
    resolved = scope_for(member, sects[0]["sector_id"])
    if resolved is None:
        return None
    spec0, entry = resolved
    region = spec0.resolve_region()
    return Selection(
        member=member,
        entry=entry,
        instance_id=spec0.id,
        spec=spec0,
        raw_spec=spec0,
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        member_colleges=list(spec0.colleges),
        region_colleges=list(region_member(region).colleges),
        sector_id=None,
        sector_socs=None,
        sector_label=None,
    )


# ── aggregate: the measure family over a Selection (pure dispatch to the quantity kernel) ──
# Small, named measure functions rather than a stringly-typed aggregate() — together they are the
# `aggregate(subgraph, measure)` half of the engine. Each is a thin, single-birthplace composition over
# the Selection's resolved scope, so a form states WHICH measure, never re-derives WHICH colleges/socs/
# spec. `supply` is the measure the C seam was about — one call now decides it.

def supply(sel: "Selection", *, over: str = "region", soc: Optional[str] = None,
           socs: Optional[list] = None, years=None) -> float:
    """Projected completions over the Selection's scope. `over` picks the college-set (region | member);
    occupation-anchored over one `soc`, an explicit `socs`, or (default) the sector's occupation-set —
    gated by the Selection's spec (the canonical in_scope feeder rule)."""
    colleges = sel.region_colleges if over == "region" else sel.member_colleges
    if soc is not None:
        return CAN.supply(colleges, soc, spec=sel.spec, years=years)
    return CAN.supply_over_socs(colleges, sel.sector_socs if socs is None else socs,
                                spec=sel.spec, years=years)
