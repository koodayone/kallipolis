"""Instance resolution + the publish (supply) gate for member×sector landscapes.

Resolves any landscape instance id to its `LandscapeSpec`:
  - a PINNED id (SVAMP, the SMCCD sectors) → the hand-authored `REGISTRY` entry,
    byte-identical to today;
  - a GENERATED id `"{member}-{sector}"` → composed on demand from the member
    catalog (`partnerships.members`) and the sector registry via `landscape_for`.

And answers the publish predicate: a generated instance is live iff the member
offers ≥1 feeding program for the sector. This is the one graph-dependent step
(`relevant_tops` gives the crosswalk-candidate feeding TOPs graph-free at the
sector level; this confirms the member actually offers one).

Lives outside `landscape.py` to keep that module graph-free and to avoid the
`landscape ↔ svamp_programs` import cycle. The dynamic API route family in
`api.py` calls `spec_for` + `has_supply`; the pinned instances keep their
explicit routes, so this is purely additive.
"""

from __future__ import annotations

from functools import lru_cache

from partnerships import members as members_mod
from partnerships.landscape import REGISTRY, LandscapeSpec, landscape_for
from partnerships.sectors import SECTORS


@lru_cache(maxsize=1)
def _member_index() -> dict[str, members_mod.Member]:
    """{member_id: Member} over the graph-free catalog. Colleges win id
    collisions over districts/regions (the more specific unit)."""
    idx: dict[str, members_mod.Member] = {}
    for code in members_mod.all_regions():
        m = members_mod.region_member(code)
        idx[m.id] = m
    for name in members_mod.all_districts():
        m = members_mod.district_member(name)
        idx[m.id] = m
    for name in members_mod.all_colleges():
        m = members_mod.college_member(name)
        idx[m.id] = m
    return idx


def _parse(instance_id: str) -> tuple[str, str] | None:
    """Split `"{member}-{sector}"` using the closed set of sector ids (none of
    which contain a hyphen), so a hyphenated member id (e.g. 'foothill-de-anza')
    parses correctly. None if no sector suffix matches."""
    for sid in SECTORS:
        if instance_id.endswith(f"-{sid}") and len(instance_id) > len(sid) + 1:
            return instance_id[: -(len(sid) + 1)], sid
    return None


def spec_for(instance_id: str) -> LandscapeSpec | None:
    """The spec for an instance id — pinned `REGISTRY` entry or a generated
    member×sector spec. None if the id doesn't resolve to a known member+sector."""
    if instance_id in REGISTRY:
        return REGISTRY[instance_id]
    parsed = _parse(instance_id)
    if parsed is None:
        return None
    member_id, sector_id = parsed
    member = _member_index().get(member_id)
    sector = SECTORS.get(sector_id)
    if member is None or sector is None:
        return None
    # Member is structurally a MemberSet (id/label/colleges/counties); landscape_for
    # reads only those fields.
    return landscape_for(member, sector, published=True)


def has_supply(spec: LandscapeSpec) -> bool:
    """The publish gate: does a member college offer ≥1 program feeding the
    sector? `relevant_tops` is the crosswalk-candidate set (graph-free); this
    confirms the member actually runs one of those TOP6 programs."""
    # Imported lazily: svamp_programs / ontology.timing use py3.10+ unions, and
    # deferring keeps this module importable under the host's py3.9 so the
    # resolver unit tests (spec_for / _parse) run without a graph.
    from ontology.schema import get_driver
    from partnerships.svamp_programs import relevant_tops

    tops = list(relevant_tops(spec).keys())
    if not tops:
        return False
    with get_driver().session() as session:
        rec = session.run(
            "MATCH (p:Program) WHERE p.college IN $colleges AND p.top6 IN $tops "
            "RETURN count(p) > 0 AS has",
            colleges=list(spec.colleges),
            tops=tops,
        ).single()
    return bool(rec and rec["has"])
