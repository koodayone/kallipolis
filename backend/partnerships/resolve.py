"""Resolve a LandscapeSpec's effective SOC set by applying its sector's
SectorRule (sectors.SectorRule) against live demand + member supply.

This is the durable replacement for hand-deleting rows from sector_socs.csv: the
committed SOC list stays the full generated middle-skill set, and the rule trims
it at request time. Because it reads the live graph (regional demand, member
programs) it is region- and member-aware and survives a sector_socs.csv
regeneration. Curated instances (SVAMP, SMCCD-AM) carry soc_rule=None and resolve
to a no-op.

The three rule dimensions:
  - min_openings   : keep SOCs whose regional annual openings exceed the floor
  - reachable_only : keep SOCs a member program reaches via the vocational
                     crosswalk (is_vocational TOP, minus the spec's excluded_tops)
  - non_empty_only : keep SOCs whose reaching member program has real activity
                     (awards or enrollment) — i.e. a non-empty matrix row
"""

from __future__ import annotations

import dataclasses

from ontology.crosswalks import _load_top_to_cip, is_vocational, top6_to_soc
from ontology.schema import get_driver
from partnerships.landscape import LandscapeSpec


def effective_socs(spec: LandscapeSpec) -> tuple[str, ...]:
    """The spec's SOCs narrowed by its sector rule. Identity (full set) when the
    spec has no active rule."""
    rule = spec.soc_rule
    socs = list(spec.socs)
    if rule is None or not rule.active:
        return tuple(socs)

    region = spec.resolve_region()
    with get_driver().session() as session:
        openings = {
            r["soc"]: r["op"]
            for r in session.run(
                "MATCH (rg:Region {name: $rg})-[d:DEMANDS]->(o:Occupation) "
                "WHERE o.soc_code IN $socs "
                "RETURN o.soc_code AS soc, d.annual_openings AS op",
                rg=region, socs=socs,
            ).data()
        }
        progs = session.run(
            "MATCH (p:Program) WHERE p.college IN $colleges RETURN p.top6 AS top6, "
            "reduce(a=0, x IN [(p)-[r:AWARDED]->() | r.count] | a + coalesce(x, 0)) AS aw, "
            "reduce(e=0, x IN [(p)-[r:ENROLLED]->() | r.count] | e + coalesce(x, 0)) AS en",
            colleges=list(spec.colleges),
        ).data()

    prog_tops = {r["top6"] for r in progs}
    active_tops = {r["top6"] for r in progs if (r["aw"] or 0) > 0 or (r["en"] or 0) > 0}

    # SOC -> reachable / active via vocational, non-excluded TOPs the member offers.
    voc = [t for t in _load_top_to_cip() if is_vocational(t) and t not in spec.excluded_tops]
    reachable: set[str] = set()
    active: set[str] = set()
    for top6, fed in top6_to_soc(voc).items():
        if top6 in prog_tops:
            reachable |= fed
        if top6 in active_tops:
            active |= fed

    kept = []
    for soc in socs:
        if rule.min_openings and (openings.get(soc) or 0) <= rule.min_openings:
            continue
        if rule.reachable_only and soc not in reachable:
            continue
        if rule.non_empty_only and soc not in active:
            continue
        kept.append(soc)
    return tuple(kept)


def resolve(spec: LandscapeSpec) -> LandscapeSpec:
    """Return spec with .socs narrowed to its sector rule's effective set.
    Identity for curated / no-rule specs (no graph access)."""
    if spec.soc_rule is None or not spec.soc_rule.active:
        return spec
    return dataclasses.replace(spec, socs=effective_socs(spec))
