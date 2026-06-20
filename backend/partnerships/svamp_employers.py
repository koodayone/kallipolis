"""SVAMP Employers lens — the advanced manufacturing employers of the Bay Area,
geocoded, for the regional employer map (the demand-side dual of the State
Atlas's college map).

Curation (v3): a region employer appears when it
  • hires (`HIRES_FOR` — the BLS OEWS NAICS→SOC industry matrix) for ≥1 of the
    landscape's SOCs, and
  • sits in the member counties (the district's geographic shed), and
  • has a validated official website (only verifiable partners plot), and
  • has geocoded coordinates inside the Bay frame.
Ranked by RELEVANCE — Σ OES staffing share (`pct_total`) over the landscape's
SOCs, i.e. how prominently the firm's industry hires the target occupations
(employer_relevance.rank_employers, the one law) — then SOC breadth, then name,
and capped to a top-N shortlist per industry. v2 gated on the coarse
`swp_sectors` industry tag and ranked by firm size, which both admitted
tag-but-not-hiring firms and missed genuinely-relevant ones the tag didn't cover;
relevance over the materialized `pct_total` edge is the precise, tag-free signal.
`shown` vs `total` is reported so the shortlist never reads as the whole
candidate pool (no silent truncation).
"""

from __future__ import annotations

from pydantic import BaseModel

from ontology.crosswalks import load_naics4_titles
from ontology.regions import COE_REGION_DISPLAY, counties_by_proximity
from ontology.schema import get_driver
from partnerships.employer_relevance import rank_employers
from partnerships.graph_reads import regional_demand
from partnerships.landscape import LandscapeSpec, SVAMP_SPEC

# Employer-map shortlist cap when an instance sets no explicit top_n (the curated
# SVAMP instance). The map is a partnership shortlist, so a relevance-ranked top-N
# is the useful view — the floor question is moot once we cap from the top.
DEFAULT_EMPLOYER_TOP_N = 25

# Bay frame — coordinates outside it are dropped, so an employer region-tagged
# "Bay" but carrying an out-of-region EDD address (e.g. a San Diego facility)
# never plots off-map. (lat_min, lat_max, lng_min, lng_max)
_BAY_BBOX = (36.8, 38.6, -123.2, -121.0)


class SvampEmployer(BaseModel):
    name: str
    display_name: str | None = None  # public-facing brand; card falls back to name
    lat: float
    lng: float
    sector: str | None = None       # EDD NAICS-2 broad tag — unreliable (can
                                    # disagree with naics4); kept but not surfaced.
    naics4: str | None = None
    naics_title: str | None = None  # authoritative NAICS-4 industry title (matches naics4)
    website: str | None = None
    description: str | None = None
    socs: list[str] = []          # target SOCs this employer hires for, intensity-ordered
    soc_count: int = 0
    soc_titles: dict[str, str] = {}  # {soc_code: BLS title} for label display
    # Σ OES staffing share (pct_total) over the landscape's SOCs — "how prominently
    # this employer's industry hires the target occupations". The map's ranking key.
    relevance: float = 0.0
    size_class: str | None = None  # EDD employee-count band (display only)
    size_rank: int = 0             # ordinal of size_class (9=largest); tiebreaker


class SvampEmployersResult(BaseModel):
    region: str
    region_display: str
    sector: str
    employers: list[SvampEmployer]
    shown: int                    # plotted (geocoded + in-frame)
    total: int                    # curated candidates (incl. not-yet-geocoded)
    shed_counties: list[str] = [] # counties the map drew from (home first); len>1 ⇒ expanded


def build_svamp_employers(spec: LandscapeSpec = SVAMP_SPEC) -> SvampEmployersResult:
    region = spec.resolve_region()
    expand = spec.employer_threshold > 0 and bool(spec.counties)
    titles = load_naics4_titles()
    la0, la1, lo0, lo1 = _BAY_BBOX

    # Candidate firms ranked by staffing-pattern relevance to the landscape's SOCs
    # (the one law — employer_relevance.rank_employers), web-validated, read once
    # with county/coordinates so the geographic shed resolves in-process. The coarse
    # swp_sectors industry tag is no longer consulted; relevance is the gate. The
    # per-SOC titles reuse the shared regional demand read.
    with get_driver().session() as session:
        ranked = rank_employers(
            session, region=region, target_socs=list(spec.socs),
            require_website=True, with_geo=True)
        soc_title = {s: row["title"]
                     for s, row in regional_demand(session, region, list(spec.socs)).items()}

    # Group geocoded-in-frame firms by county (preserving relevance order); tally
    # web-validated candidates per county (geocoded or not) for the shed `total`.
    by_county: dict[str | None, list[SvampEmployer]] = {}
    web_by_county: dict[str | None, int] = {}
    for e in ranked:
        web_by_county[e.county] = web_by_county.get(e.county, 0) + 1
        if e.lat is None or e.lng is None:                     # not geocoded
            continue
        if not (la0 <= e.lat <= la1 and lo0 <= e.lng <= lo1):  # out of the Bay frame
            continue
        # Order this firm's SOCs by its OES hiring intensity, most representative
        # first, so a "top roles" display shows the occupations central to it.
        socs_ordered = sorted(e.soc_pct, key=lambda s: (-(e.soc_pct[s] or 0.0), s))
        by_county.setdefault(e.county, []).append(SvampEmployer(
            name=e.name, lat=e.lat, lng=e.lng,
            sector=e.sector, naics4=e.naics4, naics_title=titles.get(e.naics4),
            website=e.website, description=e.description,
            relevance=round(e.relevance, 2),
            socs=socs_ordered, soc_count=len(socs_ordered),
            soc_titles={s: soc_title[s] for s in socs_ordered if soc_title.get(s)},
            size_class=e.size_class, size_rank=e.size_rank,
        ))

    # Resolve the geographic shed:
    #  - no county scoping       → the whole region (every county present);
    #  - expansion off (SVAMP)   → the fixed home shed;
    #  - expansion on            → greedily add the NEAREST county until the map
    #                              has `employer_threshold` plottable firms (or
    #                              max_radius counties / the region is exhausted).
    if not spec.counties:
        included = list(by_county.keys())
    elif not expand:
        included = list(spec.counties)
    else:
        included, plotted = [], 0
        for c in counties_by_proximity(spec.counties, region):
            included.append(c)
            plotted += len(by_county.get(c, []))
            if plotted >= spec.employer_threshold:
                break
            if spec.max_radius and len(included) >= spec.max_radius:
                break

    employers = [e for c in included for e in by_county.get(c, [])]
    total = sum(web_by_county.get(c, 0) for c in included)
    # The reach: counties that actually contributed firms (home county first) —
    # a local-vs-regional signal. len == 1 ⇒ a genuinely local map; len > 1 ⇒ the
    # industry isn't dense in the home county and the shed widened.
    shed = [c for c in included if c and by_county.get(c)]

    # The relevance-ranked partnership shortlist: firms whose industry hires the
    # target occupations most prominently. Sort by relevance (Σ pct_total over the
    # SOCs), ties by SOC breadth then name; cap to top_n per industry (default 25 —
    # the curated SVAMP instance carried no cap and would otherwise plot the whole
    # long tail of marginal firms now that the swp_sectors pre-filter is gone).
    employers.sort(key=lambda e: (-e.relevance, -e.soc_count, e.name))
    employers = employers[: (spec.top_n or DEFAULT_EMPLOYER_TOP_N)]

    return SvampEmployersResult(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        sector=spec.sector,
        employers=employers,
        shown=len(employers),      # plotted after geocode-filter + top-N cap
        total=total,               # web-validated candidates in the (resolved) shed
        shed_counties=shed,
    )
