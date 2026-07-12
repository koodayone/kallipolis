"""
Centralized region mappings for the Kallipolis ontology.

All region-level coordination happens at the COE region granularity — the
institutional unit used by the California Community Colleges Chancellor's
Office, the Strong Workforce Program, and the Centers of Excellence. Nine
regions partition the 58 California counties: Bay, CVML, FN, GS, IE/D,
LA, OC, SCC, SD/I. Every College and every Employer attaches to a Region
node keyed by this code.
"""

# COE region code → display name
COE_REGION_DISPLAY: dict[str, str] = {
    "Bay": "Bay Area",
    "CA": "California",
    "CVML": "Central Valley / Mother Lode",
    "FN": "Far North",
    "GS": "Greater Sacramento",
    "IE/D": "Inland Empire / Desert",
    "LA": "Los Angeles",
    "OC": "Orange County",
    "SCC": "South Central Coast",
    "SD/I": "San Diego / Imperial",
}

# COE region code → SWP priority sectors as named in each region's
# Strong Workforce Program development plan. Sourced from the 2023-2029
# regional plans. GS and FN share the North/Far North consortium plan;
# both receive the same priority set (top 5 by investment allocation).
# "CA" is omitted — it is a statewide aggregate, not a consortium.
# Sector strings are the canonical PCAH names, matching the
# 12-sector list loaded from `backend/ontology/data/TOP Codes to
# Sectors.xlsx`. Every string here must be in that list, enforced by
# backend/ontology/test_regions.py::test_every_priority_sector_is_canonical.
COE_REGION_PRIORITY_SECTORS: dict[str, list[str]] = {
    "Bay": [
        "Advanced Manufacturing",
        "Advanced Transportation and Logistics",
        "Health",
        "Information and Communication Technologies - Digital Media",
        "Public Safety",
        "Education and Human Development",
    ],
    "CVML": [
        "Advanced Manufacturing",
        "Agriculture, Water and Environmental Technologies",
        "Health",
        "Retail, Hospitality and Tourism",
        "Business and Entrepreneurship",
        "Information and Communication Technologies - Digital Media",
    ],
    "FN": [
        "Advanced Manufacturing",
        "Health",
        "Public Safety",
        "Advanced Transportation and Logistics",
        "Energy, Construction and Utilities",
    ],
    "GS": [
        "Advanced Manufacturing",
        "Health",
        "Public Safety",
        "Advanced Transportation and Logistics",
        "Energy, Construction and Utilities",
    ],
    "IE/D": [
        "Advanced Manufacturing",
        "Advanced Transportation and Logistics",
        "Business and Entrepreneurship",
        "Energy, Construction and Utilities",
        "Health",
        "Information and Communication Technologies - Digital Media",
        "Retail, Hospitality and Tourism",
    ],
    "LA": [
        "Advanced Manufacturing",
        "Advanced Transportation and Logistics",
        "Business and Entrepreneurship",
        "Energy, Construction and Utilities",
        "Health",
        "Information and Communication Technologies - Digital Media",
        "Life Sciences - Biotechnology",
        "Retail, Hospitality and Tourism",
    ],
    "OC": [
        "Health",
        "Information and Communication Technologies - Digital Media",
        "Business and Entrepreneurship",
        "Education and Human Development",
        "Energy, Construction and Utilities",
        "Life Sciences - Biotechnology",
    ],
    "SCC": [
        "Advanced Manufacturing",
        "Advanced Transportation and Logistics",
        "Agriculture, Water and Environmental Technologies",
        "Business and Entrepreneurship",
        "Education and Human Development",
        "Energy, Construction and Utilities",
        "Health",
        "Information and Communication Technologies - Digital Media",
        "Life Sciences - Biotechnology",
        "Public Safety",
        "Retail, Hospitality and Tourism",
    ],
    "SD/I": [
        "Advanced Manufacturing",
        "Advanced Transportation and Logistics",
        "Health",
        "Information and Communication Technologies - Digital Media",
    ],
}

# COE region → list of California counties. This is the canonical geographic
# partition for employer scraping: every county belongs to exactly one region,
# and every region's employer pool is shared by all colleges in that region.
# Sourced from the Centers of Excellence (coeccc.net), the SWP Regional
# Consortia, and the individual consortium websites (BACCC, CVML, NFNRC,
# LARC, OCRC, SDIC, SCCRC). 58 counties, 9 regions, no overlap.
COE_REGION_TO_COUNTIES: dict[str, list[str]] = {
    # Source: BACCC https://baccc.net/ (28 colleges, 12 counties)
    "Bay": [
        "Alameda", "Contra Costa", "Marin", "Monterey", "Napa", "San Benito",
        "San Francisco", "San Mateo", "Santa Clara", "Santa Cruz", "Solano", "Sonoma",
    ],
    # Source: CVML Consortium https://crconsortium.com/ (15 counties)
    "CVML": [
        "Alpine", "Amador", "Calaveras", "Fresno", "Inyo", "Kern", "Kings",
        "Madera", "Mariposa", "Merced", "Mono", "San Joaquin", "Stanislaus",
        "Tulare", "Tuolumne",
    ],
    # Source: NFNRC https://nfnrc.org/about/ ("Far North" subregion)
    "FN": [
        "Butte", "Del Norte", "Glenn", "Humboldt", "Lake", "Lassen",
        "Mendocino", "Modoc", "Plumas", "Shasta", "Sierra", "Siskiyou",
        "Tehama", "Trinity",
    ],
    # Source: NFNRC https://nfnrc.org/about/ ("North" subregion = Greater Sacramento)
    "GS": [
        "Colusa", "El Dorado", "Nevada", "Placer", "Sacramento",
        "Sutter", "Yolo", "Yuba",
    ],
    # Source: coeccc.net https://coeccc.net/region/inland-empire-desert/
    "IE/D": ["Riverside", "San Bernardino"],
    # Source: LARC https://losangelesrc.org/
    "LA": ["Los Angeles"],
    # Source: OCRC https://ocregionalconsortium.org/
    "OC": ["Orange"],
    # Source: coeccc.net https://coeccc.net/region/san-diego-imperial/
    "SD/I": ["San Diego", "Imperial"],
    # Source: SCC Consortium https://sccrcolleges.org/
    "SCC": ["San Luis Obispo", "Santa Barbara", "Ventura"],
}


# County centroids (approx lat/lng) for the Bay COE region — order the greedy
# expansion of a district's employer pool (home county → nearest county within
# the region) when the home county is too thin for a sector. Bay-only for now
# (the loaded region); counties without a centroid sort last.
_COUNTY_CENTROID: dict[str, tuple[float, float]] = {
    "Santa Clara": (37.23, -121.70), "Alameda": (37.65, -121.92),
    "San Francisco": (37.77, -122.45), "San Mateo": (37.43, -122.35),
    "Contra Costa": (37.93, -121.95), "Sonoma": (38.53, -122.93),
    "Monterey": (36.24, -121.31), "Solano": (38.27, -121.94),
    "Santa Cruz": (37.05, -122.00), "Marin": (38.07, -122.75),
    "Napa": (38.50, -122.33), "San Benito": (36.61, -121.08),
}


def counties_by_proximity(home: tuple[str, ...], region: str) -> list[str]:
    """The region's counties ordered for greedy employer-pool expansion: the
    home county/ies first (distance 0), then the rest by centroid distance to
    the nearest home county. Counties without a centroid sort last (stable).
    Used to widen a thin (district × sector) employer map to the nearest real
    partners within the labor shed, capped at the COE region."""
    import math

    home_cens = [_COUNTY_CENTROID[h] for h in home if h in _COUNTY_CENTROID]

    def dist(c: str) -> float:
        if c in home:
            return 0.0
        cc = _COUNTY_CENTROID.get(c)
        if cc is None or not home_cens:
            return 9e9
        return min(
            math.hypot(cc[0] - h[0], (cc[1] - h[1]) * math.cos(math.radians(cc[0])))
            for h in home_cens
        )

    return sorted(COE_REGION_TO_COUNTIES.get(region, []), key=lambda c: (dist(c), c))


# College name → COE region for graph loading (occupation + employer region linking).
# Single string — rural colleges that previously mapped to multiple OEWS metros
# now map to one COE region (e.g. COS → "CVML" instead of ["Visalia", "Fresno"]).
# Covers every college currently featured in the state atlas (logoStacked set).
COLLEGE_COE_REGION: dict[str, str] = {
    # Bay Area
    "Foothill College": "Bay",
    "De Anza College": "Bay",
    "Mission College": "Bay",
    "Evergreen Valley College": "Bay",
    "San Jose City College": "Bay",
    "West Valley College": "Bay",
    "Gavilan College": "Bay",
    "Laney College": "Bay",
    "Merritt College": "Bay",
    "College of Alameda": "Bay",
    "Berkeley City College": "Bay",
    "Chabot College": "Bay",
    "Ohlone College": "Bay",
    "Las Positas College": "Bay",
    "Diablo Valley College": "Bay",
    "Los Medanos College": "Bay",
    "Contra Costa College": "Bay",
    "City College of San Francisco": "Bay",
    "Cañada College": "Bay",
    "College of San Mateo": "Bay",
    "Skyline College": "Bay",
    "Santa Rosa Junior College": "Bay",
    "Napa Valley College": "Bay",
    "Solano Community College": "Bay",
    "Cabrillo College": "Bay",
    "College of Marin": "Bay",
    # Far North
    "College of the Redwoods": "FN",
    "College of the Redwoods (DN)": "FN",
    "Mendocino College": "FN",
    "Shasta College": "FN",
    "Lassen College": "FN",
    "College of the Siskiyous": "FN",
    # Greater Sacramento
    "American River College": "GS",
    "Sacramento City College": "GS",
    "Cosumnes River College": "GS",
    "Folsom Lake College": "GS",
    "Sierra College": "GS",
    "Yuba College": "GS",
    "Woodland Community College": "GS",
    "Lake Tahoe Community College": "GS",
    # Corrected per NFNRC subregion definitions (https://nfnrc.org/about/)
    "Feather River College": "FN",  # Plumas County → NFNRC "Far North"
    "Butte College": "FN",  # Butte County → NFNRC "Far North"
    # Central Valley / Mother Lode
    "Columbia College": "CVML",  # Tuolumne County → CVML Consortium (https://crconsortium.com/)
    "Fresno City College": "CVML",
    "Reedley College": "CVML",
    "Clovis Community College": "CVML",
    "Madera Community College": "CVML",
    "West Hills College Coalinga": "CVML",
    "West Hills College Lemoore": "CVML",
    "Merced College": "CVML",
    "Modesto Junior College": "CVML",
    "San Joaquin Delta College": "CVML",
    "College of the Sequoias": "CVML",
    "Porterville College": "CVML",
    "Bakersfield College": "CVML",
    "Cerro Coso Community College": "CVML",
    "Taft College": "CVML",
    # Central / South Coast
    "Cuesta College": "SCC",
    "Hartnell College": "SCC",
    "Monterey Peninsula College": "SCC",
    "Allan Hancock College": "SCC",
    "Santa Barbara City College": "SCC",
    "Ventura College": "SCC",
    "Oxnard College": "SCC",
    "Moorpark College": "SCC",
    # Los Angeles
    "Los Angeles City College": "LA",
    "Los Angeles Valley College": "LA",
    "Los Angeles Harbor College": "LA",
    "Los Angeles Mission College": "LA",
    "Los Angeles Pierce College": "LA",
    "Los Angeles Southwest College": "LA",
    "Los Angeles Trade-Technical College": "LA",
    "East Los Angeles College": "LA",
    "West Los Angeles College": "LA",
    "Glendale Community College": "LA",
    "Pasadena City College": "LA",
    "Mt. San Antonio College": "LA",
    "Long Beach City College": "LA",
    "El Camino College": "LA",
    "Santa Monica College": "LA",
    "Citrus College": "LA",
    "Rio Hondo College": "LA",
    "Cerritos College": "LA",
    "Compton College": "LA",
    "Antelope Valley College": "LA",
    "College of the Canyons": "LA",
    # Orange County
    "Coastline College": "OC",
    "Cypress College": "OC",
    "Golden West College": "OC",
    "Orange Coast College": "OC",
    "Fullerton College": "OC",
    "Santa Ana College": "OC",
    "Saddleback College": "OC",
    "Irvine Valley College": "OC",
    "Santiago Canyon College": "OC",
    # Inland Empire / Desert
    "College of the Desert": "IE/D",
    "San Bernardino Valley College": "IE/D",
    "Crafton Hills College": "IE/D",
    "Chaffey College": "IE/D",
    "Riverside City College": "IE/D",
    "Norco College": "IE/D",
    "Moreno Valley College": "IE/D",
    "Mt. San Jacinto College": "IE/D",
    "Victor Valley College": "IE/D",
    "Barstow Community College": "IE/D",
    "Palo Verde College": "IE/D",
    "Copper Mountain College": "IE/D",
    # San Diego / Imperial
    "San Diego Mesa College": "SD/I",
    "San Diego City College": "SD/I",
    "San Diego Miramar College": "SD/I",
    "Grossmont College": "SD/I",
    "Cuyamaca College": "SD/I",
    "Palomar College": "SD/I",
    "MiraCosta College": "SD/I",
    "Southwestern College": "SD/I",
    "SD College of Continuing Ed": "SD/I",
    "Imperial Valley College": "SD/I",
}


def ensure_college_region_link(driver, college_name: str) -> bool:
    """Ensure (College {name})-[:IN_MARKET]->(Region {name}) exists.

    The edge that links a college to its COE region is load-bearing
    for every industry-side traversal (occupations, employers,
    partnership alignment). It used to be written only from
    ``occupations/load.py::load_industry``, which meant loading a
    college's curriculum without also re-loading industry left the
    graph in a state where partnership precompute returned zero
    matches. This helper owns the MERGE so both entry points produce
    the edge consistently.

    Idempotent. Returns True if the college has a mapping in
    ``COLLEGE_COE_REGION`` and the edge is now in place (either newly
    created or already present); returns False without touching the
    driver if the college has no mapping.
    """
    coe_region = COLLEGE_COE_REGION.get(college_name)
    if not coe_region:
        return False
    display = COE_REGION_DISPLAY.get(coe_region, coe_region)
    with driver.session() as session:
        session.run(
            """
            MATCH (c:College {name: $college})
            MERGE (r:Region {name: $region})
              ON CREATE SET r.display_name = $display
            MERGE (c)-[:IN_MARKET]->(r)
            """,
            college=college_name,
            region=coe_region,
            display=display,
        )
    return True


