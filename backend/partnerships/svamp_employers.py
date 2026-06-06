"""SVAMP Employers lens — the advanced-manufacturing employers of the Bay Area,
geocoded, for the regional employer map (the demand-side dual of the State
Atlas's college map).

Curation (v1, to iterate): a Bay-region employer appears when it
  • is in the Advanced Manufacturing SWP sector (`swp_sectors`), and
  • hires (curated `IDENTITY_HIRES_FOR`) for ≥1 of the 12 SVAMP SOCs, and
  • has geocoded coordinates inside the Bay frame.
Ranked by SVAMP-SOC breadth. We have no employee headcount, so "top" means
most advanced-manufacturing-relevant, not largest (see the lens conversation).
`shown` vs `total` is reported so a partly-ungeocoded set never reads as
complete (no silent truncation).
"""

from __future__ import annotations

from pydantic import BaseModel

from ontology.crosswalks import load_naics4_titles
from ontology.regions import COE_REGION_DISPLAY
from ontology.schema import get_driver
from partnerships.svamp import SVAMP_SOCS, SVAMP_SECTOR, _resolve_region

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


class SvampEmployersResult(BaseModel):
    region: str
    region_display: str
    sector: str
    employers: list[SvampEmployer]
    shown: int                    # plotted (geocoded + in-frame)
    total: int                    # curated candidates (incl. not-yet-geocoded)


def build_svamp_employers() -> SvampEmployersResult:
    region = _resolve_region()
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (r:Region {name: $region})<-[:IN_MARKET]-(e:Employer)
                  -[:IDENTITY_HIRES_FOR]->(o:Occupation)
            WHERE o.soc_code IN $socs AND $sector IN e.swp_sectors
            WITH e, collect(DISTINCT o.soc_code) AS socs
            RETURN e.name AS name, e.lat AS lat, e.lng AS lng,
                   e.sector AS sector, e.naics4 AS naics4,
                   e.website AS website, e.description AS description, socs
            """,
            region=region, socs=list(SVAMP_SOCS), sector=SVAMP_SECTOR,
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
        socs = sorted(r["socs"])
        employers.append(SvampEmployer(
            name=r["name"], lat=lat, lng=lng,
            sector=r["sector"], naics4=r["naics4"],
            naics_title=titles.get(r["naics4"]),
            website=r["website"], description=r["description"],
            socs=socs, soc_count=len(socs),
        ))
    employers.sort(key=lambda e: (-e.soc_count, e.name))

    return SvampEmployersResult(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        sector=SVAMP_SECTOR,
        employers=employers,
        shown=len(employers),
        total=len(rows),
    )
