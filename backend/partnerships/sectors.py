"""Sector registry — industry → middle-skill target SOC set.

A Sector is the demand-side half of an aggregated landscape (see landscape.py):
the authoritative set of occupations a Strong Workforce priority industry maps
to. SOCs come from the BACCC / COE Bay Region sector definitions, filtered to
MIDDLE-SKILL per the BACCC regional priority plan (the occupations community-
college CTE actually targets), committed in data/sector_socs.csv.

A Sector carries NO program (TOP) scope. The feeding TOP universe is DERIVED:
the vocational/CTE TOPs (ontology.crosswalks.is_vocational) that the TOP-CIP-SOC
crosswalk reaches to the sector's SOCs. So a sector is, fundamentally, a SOC set
plus presentation identity — composed with a MemberSet (landscape.py) into a
`member × sector` landscape instance whose id/route is "{member}-{sector}".

Source of truth: data/sector_socs.csv is derived from ~/Desktop/cc_dataset/
baccc_sectors/ (the per-sector COE crosstabs), Skill Level == "Middle Skill".
non_cte_stem is intentionally absent — it has zero middle-skill SOCs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_SECTOR_SOCS_PATH = Path(__file__).parent / "data" / "sector_socs.csv"


@lru_cache(maxsize=1)
def _load_sector_socs() -> dict[str, tuple[str, ...]]:
    """{sector_id: (soc, ...)} of middle-skill SOCs, from sector_socs.csv."""
    by: dict[str, list[str]] = {}
    with open(_SECTOR_SOCS_PATH, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header: sector_id,soc,title
        for sid, soc, _title in reader:
            by.setdefault(sid, []).append(soc)
    return {sid: tuple(socs) for sid, socs in by.items()}


@dataclass(frozen=True)
class Sector:
    """One Strong Workforce priority industry. `socs` (the middle-skill target
    occupations) is the demand anchor; the feeding CTE-TOP universe is derived
    downstream via is_vocational ∩ crosswalk-reachable(socs)."""

    id: str      # URL/id segment: "{member}-{id}"
    label: str   # display label (masthead, report header)
    accent: str  # industry brand accent (placeholder colors pending design)

    @property
    def socs(self) -> tuple[str, ...]:
        return _load_sector_socs().get(self.id, ())


# id → (label, accent). SOCs join from sector_socs.csv by id; identity lives in
# code. Accents are placeholder industry colors pending design confirmation.
_SECTOR_META: list[tuple[str, str, str]] = [
    ("adm",           "Advanced Manufacturing",                 "#d9544d"),
    ("biotech",       "Life Sciences / Biotech",                "#2bb3a3"),
    ("health",        "Health",                                 "#3fb27f"),
    ("ict",           "ICT / Digital Media",                    "#5a9bd4"),
    ("atl",           "Advanced Transportation & Logistics",    "#c98a3a"),
    ("agwet",         "Ag, Water & Environmental Technologies", "#6fae54"),
    ("business",      "Business & Entrepreneurship",            "#c9a84c"),
    ("ecu",           "Energy, Construction & Utilities",       "#d08a3a"),
    ("edhd",          "Education & Human Development",          "#b06fd0"),
    ("public_safety", "Public Safety",                          "#5e6a9d"),
    ("retail",        "Retail, Hospitality & Tourism",          "#d06a9b"),
    ("unassigned",    "Unassigned CTE",                         "#8a8f9c"),
]

SECTORS: dict[str, Sector] = {
    sid: Sector(id=sid, label=label, accent=accent)
    for sid, label, accent in _SECTOR_META
}
