"""Member — the institutional aggregation unit of a landscape (the "who").

A landscape is `member × sector`. A member is one of:
  - COLLEGE    — a single college
  - DISTRICT   — a CCCCO district's colleges (from the on-disk catalog)
  - REGION     — a COE region's colleges (from COLLEGE_COE_REGION)
  - CONSORTIUM — a hand-defined college set (e.g. SVAMP, which spans four
                 districts within one region)

Resolution is GRAPH-FREE: the `college ⊂ district ⊂ region` hierarchy is read
from the same on-disk authorities the graph loaders use — the college catalog
`backend/pipeline/catalog_sources.json` (college → district, city) and
`ontology.regions` (college → COE region). So enumerating members and their
colleges needs no DB; only the supply-sparsity publish gate (does a member have
a feeding program for a sector?) touches the graph, applied downstream by the
registry generator.

This generalizes `landscape.MemberSet` (today a single hand-defined district,
SMCCD) over the full hierarchy. The existing pinned members — SVAMP (consortium)
and SMCCD (district, id "smccd") — keep their hand-authored identity and URLs
(no regression); the catalog generates the rest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

from ontology.regions import COE_REGION_DISPLAY, COLLEGE_COE_REGION

_CATALOG_PATH = Path(__file__).resolve().parents[1] / "pipeline" / "catalog_sources.json"


class MemberKind(str, Enum):
    COLLEGE = "college"
    DISTRICT = "district"
    REGION = "region"
    CONSORTIUM = "consortium"


@dataclass(frozen=True)
class Member:
    """An institutional aggregation unit a landscape is built over. `colleges`
    is the institutional axis the engine sums supply across; `regions()` is the
    demand/employer axis (read per-region; one region for all but region/state/
    cross-region members)."""

    id: str                          # URL/id segment ("{id}-{sector}")
    label: str                       # masthead identity
    kind: MemberKind
    colleges: tuple[str, ...]        # the member's colleges (full names)
    counties: tuple[str, ...] = ()   # employer-map shed; () = whole region (deferred)

    def regions(self) -> tuple[str, ...]:
        """The COE region(s) the member spans (graph-free, via COLLEGE_COE_REGION)."""
        regs = {COLLEGE_COE_REGION.get(c, "") for c in self.colleges}
        regs.discard("")
        return tuple(sorted(regs))


def _slug(text: str) -> str:
    """URL-safe id slug: lowercase, non-alnum → hyphen. District names KEEP their
    'CCD' so a district id (…-ccd) can never collide with a college backend key —
    e.g. the college 'Riverside City College' (key 'riverside') vs the district
    'Riverside CCD'. Without this the member-id namespace overlaps and the
    /landscape/{member} URL is ambiguous."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@lru_cache(maxsize=1)
def _catalog() -> dict[str, dict]:
    """{college_name: {"district", "city", "key"}} from the on-disk catalog."""
    raw = json.loads(_CATALOG_PATH.read_text())["colleges"]
    return {
        rec["name"]: {"district": rec.get("district", ""), "city": rec.get("city", ""), "key": key}
        for key, rec in raw.items()
        if rec.get("name")
    }


@lru_cache(maxsize=1)
def _district_colleges() -> dict[str, tuple[str, ...]]:
    """{district_name: (college_name, ...)} from the catalog."""
    by: dict[str, list[str]] = {}
    for college, rec in _catalog().items():
        if rec["district"]:
            by.setdefault(rec["district"], []).append(college)
    return {d: tuple(sorted(cs)) for d, cs in by.items()}


# ── Catalog enumeration (graph-free) ──────────────────────────────────────
def all_colleges() -> tuple[str, ...]:
    return tuple(sorted(_catalog()))


def all_districts() -> tuple[str, ...]:
    return tuple(sorted(_district_colleges()))


def all_regions() -> tuple[str, ...]:
    regs = {r for r in COLLEGE_COE_REGION.values() if r and r != "CA"}
    return tuple(sorted(regs))


# ── Member factories ──────────────────────────────────────────────────────
def college_member(name: str) -> Member:
    """A single-college member. id = the catalog backend key (e.g. 'foothill')."""
    rec = _catalog()[name]
    return Member(id=rec["key"], label=name, kind=MemberKind.COLLEGE, colleges=(name,))


def district_member(district_name: str) -> Member:
    """A CCCCO-district member — its catalog colleges. id = slug of the district."""
    return Member(
        id=_slug(district_name),
        label=district_name,
        kind=MemberKind.DISTRICT,
        colleges=_district_colleges()[district_name],
    )


def region_member(region_code: str) -> Member:
    """A COE-region member — all colleges the region map assigns to it."""
    cs = tuple(sorted(c for c, r in COLLEGE_COE_REGION.items() if r == region_code))
    return Member(
        id=_slug(region_code),
        label=COE_REGION_DISPLAY.get(region_code, region_code),
        kind=MemberKind.REGION,
        colleges=cs,
    )
