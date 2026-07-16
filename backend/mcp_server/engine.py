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
from mcp_server.scope import scope_for


@dataclass
class Selection:
    """A resolved coordinate scope — WHO (college-sets + derived region) and, when sector-scoped, the
    sector's occupation-set. The concrete inputs every measure needs, resolved once."""
    member: str
    entry: dict                 # the scope-catalog entry
    instance_id: str            # the coordinate's instance id (raw spec.id) — for view_links
    spec: object                # the RESOLVED LandscapeSpec (awards-gate applied) — the forms' `rspec`
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
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        member_colleges=list(rspec.colleges),
        region_colleges=list(region_member(region).colleges),
        sector_id=sid,
        sector_socs=list(SECTORS[sid].socs),
        sector_label=SECTORS[sid].label,
    )
