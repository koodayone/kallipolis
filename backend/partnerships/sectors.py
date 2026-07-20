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

Source of truth + derivation (defensible, reproducible — not a hand-list):
data/sector_socs.csv is the JOIN of two COE Bay Region publications —
  - WHICH occupations: the middle-skill universe (ontology/occupational_demand_
    middle_skill.csv, the 314 occupations occupations.json is generated from);
  - WHICH sector: the per-sector crosstabs in ~/Desktop/cc_dataset/baccc_sectors/
    (one file per CCCO sector; the files partition SOCs 1:1, so file == sector).
For every occupation in the universe, its sector is the baccc_sectors file it
appears in. This categorizes ALL 314 (verified: universe ⊆ baccc_sectors, files
disjoint), so the sector set exactly covers the universe with no orphans. We do
NOT re-apply the sector files' "Middle Skill" skill-level filter — the universe
already scopes middle-skill, and re-filtering there dropped in-demand, CC-served
occupations the universe keeps (e.g. School Bus / Shuttle Drivers, fed by the
vocational Truck-and-Bus-Driving program, tagged "Below Middle Skill" in the
sector file but present in the demand universe). non_cte_stem is intentionally
absent — no universe occupation maps to it.
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
    min_colleges: int = 1          # keep SOCs >=N distinct member colleges produce (the
                                   # consortium floor: a single-college occupation is
                                   # self-contained — no multi-school partnership to broker,
                                   # and its program is already justified by demand alone)

    @property
    def active(self) -> bool:
        return (self.min_openings > 0 or self.reachable_only or self.non_empty_only
                or self.min_wage > 0 or self.min_colleges > 1)


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
    # When set, the feeder universe is additionally gated to these TOP2 "home"
    # divisions — the Taxonomy of Programs top-level industry categories (e.g.
    # "12" = Health). A clean, self-consistent rule for sectors that map to one
    # division; left empty (use excluded_tops curation) for the TOP-09 sectors
    # (AM/ATL/ECU all share Engineering & Industrial Technologies, separable only
    # at TOP4) and cross-division sectors (ICT spans Media 06 + IT 07 + Arts 10).
    home_divisions: tuple[str, ...] = ()

    @property
    def socs(self) -> tuple[str, ...]:
        return _load_sector_socs().get(self.id, ())

    @property
    def home_programs(self) -> frozenset[str]:
        """The sector's program membership (S_tops) — the vocational program families the CCCCO PCAH
        publication CLASSIFIES as home to this sector. The program-axis twin of `socs`/COVERS: chosen by
        authority, read from the graph's SCOPES edges (via `sector_graph.sector_scopes`, completeness-gated
        with a source fallback), never derived from the crosswalk. `in_scope` reads this for a derived spec;
        `relevant_tops` then restricts it to the actual feeders via the crosswalk. Retires the old
        `excluded_tops` / `home_divisions` derive-then-exclude scope."""
        from ontology.sector_graph import sector_scopes
        return frozenset(sector_scopes(self.id))

    @property
    def addressable_socs(self) -> tuple[str, ...]:
        """The SWP-addressable subset of the sector's occupations: those with a CTE
        crosswalk pathway (reachable from a PCAH-CTE TOP via TOP→CIP→SOC). The
        non-reachable remainder are members of the occupation universe (COE middle-
        skill) with real regional demand but NO community-college program pathway in
        the crosswalk — they belong to the sector taxonomically yet are not Strong-
        Workforce program-building targets, so the demand / supply / gap analysis
        reads this set, not the raw membership. (Occupation→sector MEMBERSHIP lookups
        keep reading `socs`: an occupation still *belongs* to its sector with no pathway.)

        Sector membership is read from the graph's COVERS edges (the 3b read-swap,
        `ontology.sector_graph.sector_covers`), which `sector_graph.load` materializes
        from `socs` and `reconcile` proves equal; it falls back to `socs` when the graph
        carries no ontology. `socs` is itself sorted, so `sorted(...)` here is byte-
        identical to the earlier `socs ∩ cte_reachable`. Membership authority is the
        graph (mirroring the COE middle-skill set); addressability is the CSV crosswalk."""
        from ontology.crosswalks import cte_reachable_socs
        from ontology.sector_graph import sector_covers
        reachable = cte_reachable_socs()
        return tuple(sorted(s for s in sector_covers(self.id) if s in reachable))


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
# (2026-06-12: extended via a per-industry division-faithfulness audit — programs
# from a foreign TOP division bleeding into an industry, e.g. IT into Advanced
# Manufacturing, Vet-Tech/Wine into Health & Business, Construction into Retail.
# Only confident cross-domain bleed was added; dual-named sectors like ICT/Digital
# Media and Ag/Water/Environmental keep their legitimately cross-division feeders.)
_SECTOR_EXCLUDED_TOPS: dict[str, frozenset[str]] = {
    "adm": frozenset({"020100", "050630", "051800", "061400", "061410", "061450", "061460", "070100", "070200", "070700", "070810", "070820", "095220", "100500"}),
    "agwet": frozenset({"092400", "094610"}),
    "atl": frozenset({"050200", "050650", "092400", "094610", "095220", "095600", "210200"}),
    "biotech": frozenset({"095600", "126000", "129900", "210500", "210540"}),
    "business": frozenset({"010210", "010400", "011200", "011510", "051420", "083610", "120820", "130700", "130720", "210200", "300500"}),
    "ecu": frozenset({"070810", "095300", "220610"}),
    "edhd": frozenset({"120100"}),
    "health": frozenset({"010210", "050600", "126000", "130600"}),
    "ict": frozenset({"050900", "061450"}),
    "public_safety": frozenset({"070100", "126000"}),
    "retail": frozenset({"050640", "050650", "094500", "095200", "095700", "130320", "300700"}),
}

# Occupations the BACCC/COE demand data tags as "Work Experience Required:
# 5 years or more" — promotion destinations a worker reaches AFTER a career, not
# entry targets a middle-skill program trains someone INTO. Dropped from every
# landscape's occupation set (resolve.effective_socs) regardless of sector, the
# same editorial reason the demand floor and reachable gate exist: keep the view
# to what a college's programs can actually feed. The full COE 5-years-or-more
# set (28 SOCs across all sectors) is encoded — not just the ones live today —
# so a future sector SOC-list refresh inherits the exclusion. Source: the
# "Work Experience Required" column of the per-sector COE demand exports.
EXPERIENCE_5YR_SOCS: frozenset[str] = frozenset({
    # Management (11-*) — the bulk of the 5+yr set
    "11-1011", "11-1021", "11-2021", "11-2032", "11-2033", "11-3021", "11-3031",
    "11-3051", "11-3061", "11-3071", "11-3111", "11-3121", "11-3131", "11-9013",
    "11-9032", "11-9041", "11-9121", "11-9161",
    # Senior individual contributors / supervisory roles tagged 5+yr
    "15-1241",            # Computer Network Architects
    "23-1021", "23-1023", # Administrative Law Judges; Judges & Magistrates
    "25-9031",            # Instructional Coordinators
    "27-1011", "27-2032", # Art Directors; Choreographers
    "33-2021",            # Fire Inspectors and Investigators
    "35-1011",            # Chefs and Head Cooks
    "47-1011", "47-4011", # First-Line Supervisors of Construction; Building Inspectors
})

# "All Other" residual/catch-all SOCs in the sector universe — non-specific
# roll-up codes (e.g. "Engineering Technologists ..., All Other") that attract
# spurious crosswalk links and aren't a coherent training target. Dropped from
# every sector-derived landscape (resolve.effective_socs), alongside the 5+yr
# experience set. Generated from the sector SOC universe by title match.
ALL_OTHER_SOCS: frozenset[str] = frozenset({
    "17-3019", "17-3029", "19-4099", "29-2099", "29-9099", "31-9099", "33-1099",
    "41-9099", "49-9069", "49-9099", "51-4199", "51-7099", "53-4099",
})

# Occupations kept despite a negative regional growth rate. The strict rule drops
# declining occupations (building a program for a shrinking field is poor
# investment), but a few override: a thin/flat decline in a high-wage,
# hard-to-automate, family-sustaining role that underpins a critical regional
# industry. Today — Electrical & Electronic Engineering Technologists (17-3023,
# $43/hr, the Bay's hardware/semiconductor/energy technician spine), Carpenters
# (47-2031, $35/hr, 2,500 openings, core building trade), and Electro-Mechanical &
# Mechatronics Technologists (17-3024, the 17-3023 sibling in the adm engineering-
# tech block) — all flat replacement-churn (17-3024 is -1.4%), not dying. Growth
# is a flag here, not a guillotine.
GROWTH_EXEMPT_SOCS: frozenset[str] = frozenset({"17-3023", "47-2031", "17-3024"})

# Promotion / management roles — NOT entry-level, so not a community-college
# training target. A CC produces the line worker; the employer promotes one of
# them into the supervisor/manager seat after years on the job. These double-count
# an entry pipeline at a higher tier (e.g. 49-1011 First-Line Supervisors of
# Mechanics is just the SOC-49 trades — Auto/Diesel/Industrial/Aircraft mechanics
# — re-attributed one rung up). The "5+ years experience" cut alone misses them
# because BLS codes most supervisors as "Less than 5 years"; the clean signal is
# the ROLE, identified deterministically from the baccc_sectors sheet: a
# Supervisor/Manager/Detective title (or SOC-11 Management requiring any prior
# experience), minus a focused-pathway carve-out. A role survives when a DEDICATED
# CTE program trains directly for it (not generic bleed) AND it isn't merely
# double-counting an entry role we already keep:
#   - Construction Managers (11-9021) — construction-management programs.
#   - Food Service Managers (11-9051) — culinary/hospitality-management programs.
#   - First-Line Supervisors of Landscaping (37-1012) — fed by Landscape Design /
#     Horticulture / Nursery programs, and its $22 entry groundskeeper sits BELOW
#     the wage floor, so the $30 crew-lead/contractor role is the green-industry
#     pipeline's only family-sustaining outcome, not a duplicate.
# Administrative Services & Facilities Managers stay cut: identical generic
# Business-Admin feeders (no focused program). Mechanics/production supervisors
# stay cut: they double-count entry trades already in the set. Generated from the
# CSVs' "Work Experience Required" + title; experienced *trades* (Cooks, Crane
# Operators, repairers) deliberately stay — they're entry, not promotion.
PROMOTION_SOCS: frozenset[str] = frozenset({
    "11-1011", "11-1021", "11-1031", "11-2011", "11-2021", "11-2022",
    "11-2032", "11-2033", "11-3012", "11-3013", "11-3021", "11-3031",
    "11-3051", "11-3061", "11-3071", "11-3111", "11-3121", "11-3131",
    "11-9013", "11-9031", "11-9032", "11-9033", "11-9041",
    "11-9071", "11-9072", "11-9081", "11-9111", "11-9121", "11-9131",
    "11-9141", "11-9151", "11-9161", "11-9171", "33-1011", "33-1012",
    "33-1021", "33-1091", "33-3021", "33-9021", "35-1012", "37-1011",
    "39-1013", "39-1014", "39-1022", "41-1011", "41-1012",
    "43-1011", "45-1011", "47-1011", "49-1011", "51-1011", "53-1041",
    "53-1047",
})

# Curated below-floor occupations (set 2026-06-13 from the BACCC consortium clustering
# analysis; the adm engineering-tech block added 2026-06-21). These clear every gate
# EXCEPT the openings floor — premium wage, growing, multi-college, awards-backed, but
# thinner in raw annual openings than the floor allows.
#
# HISTORY: this list once exempted these SOCs from the in_demand openings floor (and one
# from the wage floor). That exemption was REMOVED 2026-07-19: curated priority belongs to
# the AUTHORED composition path (SVAMP, which marks all its SOCs in-demand and never reaches
# the gate), not to the default rule — which now reads EXACTLY as its stated criteria
# (openings > floor AND wage >= floor) for every derived landscape in every region. Baking a
# Bay/SVAMP-strategic list into the global gate silently over-promoted these occupations in
# every other region's landscape (San Diego adm showed 10-openings roles above a ">250"
# bar). See resolve.soc_in_demand. Membership is graph-native (COVERS), unaffected — these
# occupations still show as `served`, now correctly below the priority bar.
#
# The list survives ONLY as the ClusterMap `admitted` badge (clusters.py) marking these
# curated occupations in the cluster view; it no longer gates demand or membership.
# Cluster-extenders: 29-9021 Health Information Technologists, 19-4092 Forensic Science
# Technicians, 49-9051 Electrical Power-Line Installers, 47-2071 Paving/Surfacing Operators,
# 49-9062 Medical Equipment Repairers; standalone 29-1126 Respiratory Therapists; the adm
# block 17-3026 / 17-3024 / 51-9141 (SVAMP advanced-manufacturing technician occupations).
INCLUDE_SOCS: frozenset[str] = frozenset({
    "29-9021", "19-4092", "49-9051", "47-2071", "49-9062", "29-1126",
    "17-3026", "17-3024", "51-9141",
})

# Uniform SOC-selection curation = the strict BACCC priority-occupation standard
# (set 2026-06-12; thresholds simplified 2026-07-18): median wage at least
# $50,000/yr, more than 250 regional annual openings, under 5 years of prior work
# experience (EXPERIENCE_5YR_SOCS drop in resolve), and no "all other" catch-alls
# (ALL_OTHER_SOCS). The non-declining-GROWTH gate was DROPPED 2026-07-18 — a
# declining field can still be a real, staffable market a member trains for, so
# growth no longer gates in_demand (GROWTH_EXEMPT_SOCS is now vestigial). non_empty_only
# is ON: an occupation is shown only if >=1 member program actually has AWARDS
# (completers) feeding it — awards are the supply metric, so an occupation with
# enrollment but no graduates is dropped along with the completely-blank rows (an
# occupation with zero consortium supply — e.g. Flight Attendants, which has no CC
# training pathway — is dropped rather than rendered as an all-gap row).
# reachable_only stays OFF; non_empty_only is the stricter activity gate. Operator note: the rule keeps openings > min_openings and wage
# >= min_wage, so 250 / 50_000 gate at "openings >= 251" and "wage >= $50,000".
# Per-sector overrides go in _SECTOR_RULES.
_DEFAULT_RULE = SectorRule(
    min_openings=250, min_wage=50_000, reachable_only=False, non_empty_only=True,
    min_colleges=2,
)

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

# Per-sector "home" TOP2 division(s) — the Taxonomy of Programs top-level industry
# category a sector maps to (Manual, 7th Ed.). When set, the feeder universe is
# gated to these divisions (in_scope), so the sector only draws programs the
# manual files under its own industry. Only set where the sector maps cleanly to
# a division — Health is TOP 12, Retail/Hospitality is TOP 13 (Family & Consumer
# Sciences), Transport (ATL) is TOP 09 (Engineering & Industrial Technologies),
# Business is TOP 05 (Business & Management). The TOP2 gate drops out-of-division
# bleed (e.g. TOP-05 Business programs leaking into Transport, or Construction /
# Paralegal / Cosmetology leaking into Business) but does NOT separate the three
# 09-rooted sectors (AM/ATL/ECU) from each other — that still needs TOP4
# excluded_tops, so the two mechanisms are complementary. Business's 05 gate is
# clean (every occupation keeps a 05 feeder); ATL's 09 gate intentionally drops
# Logisticians (13-1081), a regional-plan ATL occupation whose only feeder is
# Business (no 09 pipeline trains logisticians). AM/ECU keep their out-of-division
# cleanup in excluded_tops for now; ICT spans divisions (Media 06 + IT 07 + Arts
# 10) so it has no single home.
_SECTOR_HOME_DIV: dict[str, tuple[str, ...]] = {
    "health": ("12",),
    "retail": ("13",),
    "business": ("05",),
    "atl": ("09",),
}

SECTORS: dict[str, Sector] = {
    sid: Sector(
        id=sid, label=label, accent=accent,
        swp_tag=_SECTOR_SWP_TAG.get(sid, ""),
        excluded_tops=_SECTOR_EXCLUDED_TOPS.get(sid, frozenset()),
        rule=_SECTOR_RULES.get(sid, _DEFAULT_RULE),
        home_divisions=_SECTOR_HOME_DIV.get(sid, ()),
    )
    for sid, label, accent in _SECTOR_META
}
