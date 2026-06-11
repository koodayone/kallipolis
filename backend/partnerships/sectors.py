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
class SectorRule:
    """Declarative curation of a sector's derived selection space, applied at
    landscape-build time (partnerships.resolve.effective_socs) against live
    demand + member supply. Region- and member-aware, so it re-derives per
    instance and survives a sector_socs.csv regeneration: the committed SOC list
    stays the full generated set; the rule does the trimming.

    All-default = no-op (the sector shows its full middle-skill set)."""

    min_openings: int = 0          # keep SOCs with regional annual openings > this
    reachable_only: bool = False   # keep SOCs a member program reaches via the crosswalk
    non_empty_only: bool = False   # keep SOCs with >=1 member program that has activity
    min_wage: int = 0              # keep SOCs whose regional annual median wage >= this

    @property
    def active(self) -> bool:
        return self.min_openings > 0 or self.reachable_only or self.non_empty_only or self.min_wage > 0


@dataclass(frozen=True)
class Sector:
    """One Strong Workforce priority industry. `socs` (the middle-skill target
    occupations) is the demand anchor; the feeding CTE-TOP universe is derived
    downstream via is_vocational ∩ crosswalk-reachable(socs)."""

    id: str      # URL/id segment: "{member}-{id}"
    label: str   # display label (masthead, report header)
    accent: str  # industry brand accent (placeholder colors pending design)
    # The exact COE/EDD `swp_sectors` tag the Employer nodes carry (the employer
    # pipeline's vocabulary). Diverges from `label`: the display label uses "&"/"/"
    # and a short form, the COE tag spells "and" and uses the full sector name
    # (e.g. label "Energy, Construction & Utilities" → tag "Energy, Construction
    # and Utilities"). Used to match a sector's regional employers. "" = no
    # employer match (the residual catch-all).
    swp_tag: str = ""
    # TOP6 codes dropped from this sector's derived feeder universe — crosswalk
    # artifacts that don't belong to the industry (e.g. an IT program the
    # TOP-CIP-SOC crosswalk maps onto a catch-all SOC). Applied in
    # LandscapeSpec.in_scope on top of the is_vocational gate.
    excluded_tops: frozenset[str] = frozenset()
    # Declarative SOC-selection curation (demand floor / reachable / non-empty),
    # applied at build time. Default = no-op (show the full middle-skill set).
    rule: SectorRule = SectorRule()

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

# Per-sector TOP exclusions — crosswalk-noise feeders dropped from the derived
# universe: a member TOP that reaches the sector through a SINGLE incidental SOC
# AND also feeds >=2 sectors (so its real home is elsewhere). Single-sector
# 1-SOC feeders (e.g. Nursing -> Health) are deliberately NOT excluded — they're
# narrow-but-real programs, not cross-domain artifacts. Derived from the supply-
# noise audit; applied in LandscapeSpec.in_scope on top of the is_vocational gate.
_SECTOR_EXCLUDED_TOPS: dict[str, frozenset[str]] = {
    "adm": frozenset({"020100", "050630", "061400", "061410", "061450", "061460", "070700", "070810", "070820", "095220", "100500"}),
    "agwet": frozenset({"092400", "094610"}),
    "atl": frozenset({"050200", "050650", "092400", "094610", "095220", "095600", "210200"}),
    "biotech": frozenset({"126000", "129900", "210500", "210540"}),
    "business": frozenset({"051420", "120820", "130700", "130720", "210200"}),
    "ecu": frozenset({"070810", "095300", "220610"}),
    "edhd": frozenset({"120100"}),
    "health": frozenset({"050600", "126000", "130600"}),
    "ict": frozenset({"050900", "061450"}),
    "public_safety": frozenset({"070100", "126000"}),
    "retail": frozenset({"050640", "050650", "130320", "300700"}),
}

# Uniform SOC-selection curation = the BACCC/COE "priority job" definition,
# applied to every sector (the SECTORS default below): reachable from a member
# program via the crosswalk, >=50 regional annual openings, and at/above the
# $50k near-living-wage floor. (BACCC Bay living wage is $25.97/hr ~= $54,018;
# the $50k floor deliberately keeps borderline-core CTE pathways — CNA $52.8k,
# EMT $50.3k, welding $51.8k — while cutting the genuinely sub-living-wage.)
# Per-sector overrides go in _SECTOR_RULES.
_DEFAULT_RULE = SectorRule(min_openings=49, reachable_only=True, min_wage=50_000)

_SECTOR_RULES: dict[str, SectorRule] = {}  # per-sector overrides (none currently)

# Canonical COE/EDD swp_sectors tag per sector — the exact string the Employer
# nodes carry (verified against the live graph). Diverges from the display
# `label`, so it is matched separately when selecting a sector's employers.
# `unassigned` has no employer sector and is intentionally absent.
_SECTOR_SWP_TAG: dict[str, str] = {
    "adm":           "Advanced Manufacturing",
    "biotech":       "Life Sciences - Biotechnology",
    "health":        "Health",
    "ict":           "Information and Communication Technologies - Digital Media",
    "atl":           "Advanced Transportation and Logistics",
    "agwet":         "Agriculture, Water and Environmental Technologies",
    "business":      "Business and Entrepreneurship",
    "ecu":           "Energy, Construction and Utilities",
    "edhd":          "Education and Human Development",
    "public_safety": "Public Safety",
    "retail":        "Retail, Hospitality and Tourism",
}

SECTORS: dict[str, Sector] = {
    sid: Sector(
        id=sid, label=label, accent=accent,
        swp_tag=_SECTOR_SWP_TAG.get(sid, ""),
        excluded_tops=_SECTOR_EXCLUDED_TOPS.get(sid, frozenset()),
        rule=_SECTOR_RULES.get(sid, _DEFAULT_RULE),
    )
    for sid, label, accent in _SECTOR_META
}
