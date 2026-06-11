"""SVAMP Employers lens — the advanced manufacturing employers of the Bay Area,
geocoded, for the regional employer map (the demand-side dual of the State
Atlas's college map).

Curation (v2): a region employer appears when it
  • is in the landscape's SWP sector (`swp_sectors`), and
  • hires (`HIRES_FOR` — the BLS OEWS NAICS→SOC industry matrix) for ≥1 of the
    landscape's SOCs, and
  • sits in the member counties (the district's geographic shed), and
  • has a validated official website (only verifiable partners plot), and
  • has geocoded coordinates inside the Bay frame.
Ranked largest-first by EDD size band (`size_rank`), then OEWS hiring intensity
(Σ pct_total) / SOC breadth. v1 gated on the LLM-curated `IDENTITY_HIRES_FOR`
overlay, which is sparse (needs website enrichment) and left most district
sector maps empty; the full `HIRES_FOR` matrix is complete and deterministic,
so every sector map populates. `IDENTITY_HIRES_FOR` still drives the per-employer
detail view (what *this* firm hires), where firm-specificity matters.
`shown` vs `total` is reported so a partly-ungeocoded set never reads as
complete (no silent truncation).
"""

from __future__ import annotations

from pydantic import BaseModel

from ontology.crosswalks import load_naics4_titles
from ontology.regions import COE_REGION_DISPLAY
from ontology.schema import get_driver
from partnerships.landscape import LandscapeSpec, SVAMP_SPEC

# Bay frame — coordinates outside it are dropped, so an employer region-tagged
# "Bay" but carrying an out-of-region EDD address (e.g. a San Diego facility)
# never plots off-map. (lat_min, lat_max, lng_min, lng_max)
_BAY_BBOX = (36.8, 38.6, -123.2, -121.0)


class SvampEmployer(BaseModel):
    name: str
    lat: float
    lng: float
    sector: str | None = None       # EDD NAICS-2 broad tag — unreliable (can
                                    # disagree with naics4); kept but not surfaced.
    naics4: str | None = None
    naics_title: str | None = None  # authoritative NAICS-4 industry title (matches naics4)
    website: str | None = None
    description: str | None = None
    socs: list[str] = []          # SVAMP SOCs this employer hires for (curated)
    soc_count: int = 0
    soc_titles: dict[str, str] = {}  # {soc_code: BLS title} for label display
    size_class: str | None = None  # EDD employee-count band (the viability proxy)
    size_rank: int = 0             # ordinal of size_class (9=largest); drives ranking


class SvampEmployersResult(BaseModel):
    region: str
    region_display: str
    sector: str
    employers: list[SvampEmployer]
    shown: int                    # plotted (geocoded + in-frame)
    total: int                    # curated candidates (incl. not-yet-geocoded)


def build_svamp_employers(spec: LandscapeSpec = SVAMP_SPEC) -> SvampEmployersResult:
    region = spec.resolve_region()
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (r:Region {name: $region})<-[:IN_MARKET]-(e:Employer)
                  -[h:HIRES_FOR]->(o:Occupation)
            WHERE o.soc_code IN $socs AND $sector IN e.swp_sectors
              AND (size($counties) = 0 OR e.county IN $counties)
              AND e.website IS NOT NULL   // only website-validated firms plot
            WITH e, collect(DISTINCT {code: o.soc_code, title: o.title, pct: h.pct_total}) AS soc_meta
            RETURN e.name AS name, e.lat AS lat, e.lng AS lng,
                   e.sector AS sector, e.naics4 AS naics4,
                   e.website AS website, e.description AS description, soc_meta,
                   e.size_class AS size_class, e.size_rank AS size_rank
            """,
            region=region, socs=list(spec.socs),
            sector=spec.swp_tag or spec.sector,  # COE employer-tag vocabulary
            counties=list(spec.counties),        # geographic shed (county scoping)
        ).data()

    titles = load_naics4_titles()
    la0, la1, lo0, lo1 = _BAY_BBOX
    employers: list[SvampEmployer] = []
    for r in rows:
        lat, lng = r["lat"], r["lng"]
        if lat is None or lng is None:                     # not geocoded
            continue
        if not (la0 <= lat <= la1 and lo0 <= lng <= lo1):  # out of the Bay frame
            continue
        # Order an employer's sector-SOCs by OES industry share (most
        # representative occupations first), so a "top N" display shows the
        # roles central to the firm — not an alphabetical accident. Ties / null
        # pct (e.g. SVAMP's curated picks) fall back to code order.
        meta = sorted(r["soc_meta"], key=lambda m: (-(m.get("pct") or 0.0), m["code"]))
        socs = [m["code"] for m in meta]
        soc_titles = {m["code"]: m["title"] for m in meta if m.get("title")}
        employers.append(SvampEmployer(
            name=r["name"], lat=lat, lng=lng,
            sector=r["sector"], naics4=r["naics4"],
            naics_title=titles.get(r["naics4"]),
            website=r["website"], description=r["description"],
            socs=socs, soc_count=len(socs), soc_titles=soc_titles,
            size_class=r.get("size_class"), size_rank=r.get("size_rank") or 0,
        ))
    # "Top N by size" — the sizable firms are the viable partnership targets.
    # Rank largest-first (size_rank), break ties by SOC breadth then name; SVAMP
    # carries no size data so size_rank is 0 there and the order falls back to
    # the prior SOC-breadth ranking. spec.top_n caps each industry's shortlist
    # (None = uncapped, e.g. SVAMP).
    employers.sort(key=lambda e: (-e.size_rank, -e.soc_count, e.name))
    if spec.top_n:
        employers = employers[: spec.top_n]

    return SvampEmployersResult(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        sector=spec.sector,
        employers=employers,
        shown=len(employers),      # plotted after geocode-filter + top-N cap
        total=len(rows),           # all web-validated candidates in the shed (geocoded or not)
    )
