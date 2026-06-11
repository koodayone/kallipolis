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
from ontology.regions import COE_REGION_DISPLAY, counties_by_proximity
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
    contact_name: str | None = None   # EDD/Data Axle exec contact — free from the detail scrape
    contact_title: str | None = None  # …and their title (CEO/Owner/GM) — the outreach hook


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
    driver = get_driver()
    # Pull the region's relevant, web-validated firms WITH their county once; the
    # geographic shed (home, or greedily widened) is then resolved in-process.
    # Widening in the query (a growing $counties list) would mean N round-trips;
    # one region read + an in-memory county walk is simpler and the relevant set
    # per sector is small (hundreds, not millions).
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (r:Region {name: $region})<-[:IN_MARKET]-(e:Employer)
                  -[h:HIRES_FOR]->(o:Occupation)
            WHERE o.soc_code IN $socs AND $sector IN e.swp_sectors
              AND e.website IS NOT NULL   // only website-validated firms plot
            WITH e, collect(DISTINCT {code: o.soc_code, title: o.title, pct: h.pct_total}) AS soc_meta
            RETURN e.name AS name, e.county AS county, e.lat AS lat, e.lng AS lng,
                   e.sector AS sector, e.naics4 AS naics4,
                   e.website AS website, e.description AS description, soc_meta,
                   e.size_class AS size_class, e.size_rank AS size_rank,
                   e.contact_name AS contact_name, e.contact_title AS contact_title
            """,
            region=region, socs=list(spec.socs),
            sector=spec.swp_tag or spec.sector,  # COE employer-tag vocabulary
        ).data()

    titles = load_naics4_titles()
    la0, la1, lo0, lo1 = _BAY_BBOX
    # Group geocoded-in-frame employers by county; tally web-validated candidates
    # per county (geocoded or not) for the shed `total`.
    by_county: dict[str | None, list[SvampEmployer]] = {}
    web_by_county: dict[str | None, int] = {}
    for r in rows:
        web_by_county[r["county"]] = web_by_county.get(r["county"], 0) + 1
        lat, lng = r["lat"], r["lng"]
        if lat is None or lng is None:                     # not geocoded
            continue
        if not (la0 <= lat <= la1 and lo0 <= lng <= lo1):  # out of the Bay frame
            continue
        # Order an employer's sector-SOCs by OES industry share (most
        # representative occupations first), so a "top N" display shows the roles
        # central to the firm — not an alphabetical accident. Ties / null pct
        # fall back to code order.
        meta = sorted(r["soc_meta"], key=lambda m: (-(m.get("pct") or 0.0), m["code"]))
        emp = SvampEmployer(
            name=r["name"], lat=lat, lng=lng,
            sector=r["sector"], naics4=r["naics4"],
            naics_title=titles.get(r["naics4"]),
            website=r["website"], description=r["description"],
            socs=[m["code"] for m in meta], soc_count=len(meta),
            soc_titles={m["code"]: m["title"] for m in meta if m.get("title")},
            size_class=r.get("size_class"), size_rank=r.get("size_rank") or 0,
            contact_name=r.get("contact_name"), contact_title=r.get("contact_title"),
        )
        by_county.setdefault(r["county"], []).append(emp)

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

    # "Top N by size" — the sizable firms are the viable partnership targets.
    # Largest-first (size_rank), break ties by SOC breadth then name. spec.top_n
    # caps each industry's shortlist (None = uncapped, e.g. SVAMP).
    employers.sort(key=lambda e: (-e.size_rank, -e.soc_count, e.name))
    if spec.top_n:
        employers = employers[: spec.top_n]

    return SvampEmployersResult(
        region=region,
        region_display=COE_REGION_DISPLAY.get(region, region),
        sector=spec.sector,
        employers=employers,
        shown=len(employers),      # plotted after geocode-filter + top-N cap
        total=total,               # web-validated candidates in the (resolved) shed
        shed_counties=shed,
    )
