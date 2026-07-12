"""Tier 0 — scope grounding: the canonical member×sector universe + resolution.

Unifies the two member sources the engine keeps separate — the generated live
catalog (colleges/districts; ``registry.live_catalog``) and the pinned consortia
(``landscape.REGISTRY``: svamp, smccd-*, baccc-*) — into one flat coordinate
universe the *model* resolves fuzzy identity against. There is no server-side
fuzzy matcher (none exists in the codebase, and the consumer is a frontier
model): ``list_scopes`` exposes this universe, the model maps "I'm at Foothill"
→ ``foothill``, and ``orient`` validates the guess.

``scope_for`` turns a resolved (member, sector) into the engine's
``LandscapeSpec`` via ``registry.spec_for``. An unresolvable coordinate yields a
Gate envelope — the emergent scope-first gate (a form needs a coordinate; Tier 0
is how you obtain one; no separate checkpoint).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from partnerships.landscape import MEMBERS, REGISTRY, LandscapeSpec
from partnerships.registry import live_catalog, spec_for
from partnerships.sectors import SECTORS

from mcp_server.envelope import (
    AnalysisEnvelope,
    Coordinate,
    Gate,
    Licensing,
    NextMove,
)

logger = logging.getLogger(__name__)

# Sector display label → id, to decompose bespoke pinned specs (svamp) whose
# instance id carries no sector suffix.
_SECTOR_ID_BY_LABEL = {s.label: sid for sid, s in SECTORS.items()}


def _member_kind(label: str) -> str:
    # A CCD is a district; otherwise the pinned member is a consortium.
    return "district" if "CCD" in label else "consortium"


def _pinned_entries() -> list[dict]:
    """The pinned REGISTRY specs as scope-catalog rows. Bespoke ids (svamp) carry
    no sector suffix, so the sector id is recovered from the spec's display label."""
    out: list[dict] = []
    for inst_id, spec in REGISTRY.items():
        sector_id = _SECTOR_ID_BY_LABEL.get(spec.sector, "")
        if sector_id and inst_id.endswith(f"-{sector_id}"):
            member_id = inst_id[: -(len(sector_id) + 1)]
        else:
            member_id = inst_id                      # bespoke (svamp)
        member = MEMBERS.get(member_id)
        member_label = member.label if member else spec.name
        out.append({
            "id": inst_id,
            "member_id": member_id,
            "member_label": member_label,
            "member_kind": _member_kind(member_label),
            "sector_id": sector_id,
            "sector_label": spec.sector,
            "region": None,
            "pinned": True,
        })
    return out


@lru_cache(maxsize=1)
def scope_catalog() -> tuple[dict, ...]:
    """The unified canonical member×sector universe (pinned ∪ generated live).

    Degrades to pinned-only if the graph is unreachable (the live catalog needs a
    Program scan) — orientation still works; the forms themselves gate on missing
    data. Tuple return so the lru_cache key is hashable."""
    seen: dict[str, dict] = {e["id"]: e for e in _pinned_entries()}
    try:
        for e in live_catalog():                     # generated colleges/districts
            seen.setdefault(e["id"], {**e, "pinned": False})
    except Exception as exc:                          # graph down → pinned-only
        logger.warning("scope_catalog: live_catalog unavailable (%s); pinned-only", exc)
    return tuple(sorted(
        seen.values(),
        key=lambda e: (e["member_kind"], e["member_id"], e["sector_id"]),
    ))


def find_scope(member_id: str, sector_id: str) -> Optional[dict]:
    for e in scope_catalog():
        if e["member_id"] == member_id and e["sector_id"] == sector_id:
            return e
    return None


def sectors_for_member(member_id: str) -> list[dict]:
    """The live sector coordinates for one member — the capability landscape
    ``orient`` presents (R3)."""
    return [e for e in scope_catalog() if e["member_id"] == member_id]


def member_portfolio(member_id: str) -> Optional[dict]:
    """The cheap shaped summary ``institution_overview`` grounds on: the member's
    live sectors, each with the count of distinct feeding TOP6 programs the member
    runs, plus its region. One Program query for the member's TOP6s; each sector's
    candidate TOP set is graph-free (crosswalk-derived), intersected in memory — so
    this stays snappy even for a 26-college consortium. Enumeration (the programs
    themselves) stays behind the per-sector drills: the overview grounds, it does
    not list."""
    sects = sectors_for_member(member_id)
    if not sects:
        return None
    first = scope_for(member_id, sects[0]["sector_id"])
    if first is None:
        return None
    spec0 = first[0]
    from ontology.regions import COE_REGION_DISPLAY
    from ontology.schema import get_driver
    from partnerships.landscape_programs import relevant_tops
    with get_driver().session() as session:
        rows = session.run(
            "MATCH (p:Program) WHERE p.college IN $colleges RETURN DISTINCT p.top6 AS top6",
            colleges=list(spec0.colleges),
        ).data()
    member_tops = {r["top6"] for r in rows}
    sectors: list[dict] = []
    for e in sects:
        resolved = scope_for(member_id, e["sector_id"])
        if resolved is None:
            continue
        cand = set(relevant_tops(resolved[0]).keys())
        sectors.append({
            "sector_id": e["sector_id"],
            "sector_label": e["sector_label"],
            "instance": e["id"],
            "program_count": len(member_tops & cand),
        })
    try:
        region = COE_REGION_DISPLAY.get(spec0.resolve_region(), "")
    except Exception:
        region = ""
    head = sects[0]
    return {
        "member_id": head["member_id"],
        "member_label": head["member_label"],
        "member_kind": head["member_kind"],
        "region": region,
        "sectors": sectors,
    }


def scope_for(member_id: str, sector_id: str) -> Optional[tuple[LandscapeSpec, dict]]:
    """Resolve (member, sector) → (LandscapeSpec, catalog entry), or None if the
    coordinate is not in the universe. Thin over ``registry.spec_for`` — the
    catalog entry's ``id`` is the canonical instance id (handles bespoke svamp)."""
    entry = find_scope(member_id, sector_id)
    if entry is None:
        return None
    spec = spec_for(entry["id"])
    if spec is None:
        return None
    return spec, entry


def coordinate_of(entry: dict, *, soc: Optional[str] = None,
                  top6: Optional[str] = None) -> Coordinate:
    return Coordinate(
        member=entry["member_id"], member_label=entry["member_label"],
        sector=entry["sector_id"], sector_label=entry["sector_label"],
        region=entry.get("region"), soc=soc, top6=top6,
    )


def gate_envelope(form: str, member_id: str, sector_id: str, *, reason: str,
                  marker: str = "out-of-scope") -> AnalysisEnvelope:
    """The emergent scope-first gate: a form called with an unresolvable
    coordinate returns an explicit marker and routes back to Tier 0."""
    from mcp_server.catalog import tool_name  # lazy: catalog imports scope (avoid the cycle)
    coord = Coordinate(member=member_id, sector=sector_id)
    return AnalysisEnvelope(
        form=form,
        coordinate=coord,
        licensing=Licensing(
            gates=[Gate(field="coordinate", marker=marker, reason=reason)]),
        next_moves=[   # form = the callable tool name the model routes to, not the internal id
            NextMove(form=tool_name("orient"), coordinate=coord,
                     rationale="Establish which institution and sector before analysis."),
            NextMove(form=tool_name("list_scopes"), coordinate=coord,
                     rationale="See the member×sector coordinates the system knows."),
        ],
    )
