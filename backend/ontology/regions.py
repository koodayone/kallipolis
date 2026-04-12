"""
Centralized region mappings across OEWS metros, COE regions, and frontend regions.

Three coordinate systems exist for California regions:
  1. OEWS metros — fine-grained MSA/MD names from EDD occupational surveys
  2. COE regions — 9 broad regions used by Centers of Excellence demand projections
  3. Frontend regions — UI region slugs in californiaColleges.ts

This module provides the canonical mappings between them.
"""

# OEWS metro name → COE region code
OEWS_METRO_TO_COE: dict[str, str] = {
    # Bay Area
    "San Jose-Sunnyvale-Santa Clara": "Bay",
    "Oakland-Fremont-Berkeley": "Bay",
    "San Francisco-San Mateo-Redwood City": "Bay",
    "Santa Rosa-Petaluma": "Bay",
    "Napa": "Bay",
    "Vallejo": "Bay",
    "Santa Cruz-Watsonville": "Bay",
    "San Rafael": "Bay",
    # Los Angeles
    "Los Angeles-Long Beach-Glendale": "LA",
    # Orange County
    "Anaheim-Santa Ana-Irvine": "OC",
    # San Diego / Imperial
    "San Diego-Chula Vista-Carlsbad": "SD/I",
    "El Centro": "SD/I",
    # Inland Empire / Desert
    "Riverside-San Bernardino-Ontario": "IE/D",
    # Greater Sacramento
    "Sacramento-Roseville-Folsom": "GS",
    "Yuba City": "GS",
    "Chico": "GS",
    "Eastern Sierra-Mother Lode Region": "GS",
    # Central Valley / Mother Lode
    "Fresno": "CVML",
    "Modesto": "CVML",
    "Merced": "CVML",
    "Visalia": "CVML",
    "Hanford-Corcoran": "CVML",
    "Stockton-Lodi": "CVML",
    "Bakersfield-Delano": "CVML",
    # Central Coast (South Central Coast COE)
    "Oxnard-Thousand Oaks-Ventura": "SCC",
    "Salinas": "SCC",
    "San Luis Obispo-Paso Robles": "SCC",
    "Santa Maria-Santa Barbara": "SCC",
    # Far North
    "Redding": "FN",
    "North Coast Region": "FN",
    "North Valley-Northern Mountains Region": "FN",
}

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

# Frontend regionId → COE region code
FRONTEND_TO_COE: dict[str, str] = {
    "bay-area": "Bay",
    "los-angeles": "LA",
    "orange-county": "OC",
    "san-diego": "SD/I",
    "inland-empire": "IE/D",
    "central-valley": "CVML",
    "central-coast": "SCC",
    "greater-sacramento": "GS",
    "north-coast": "FN",
    "far-north": "FN",
    "sierra-nevada": "GS",
}

# College name → OEWS metro(s) for occupation demand data and IN_MARKET edges.
# Single string for urban colleges, list for rural colleges spanning multiple metros.
COLLEGE_REGION_MAP: dict = {
    "Foothill College": "San Jose-Sunnyvale-Santa Clara",
    "De Anza College": "San Jose-Sunnyvale-Santa Clara",
    "Mission College": "San Jose-Sunnyvale-Santa Clara",
    "Evergreen Valley College": "San Jose-Sunnyvale-Santa Clara",
    "San Jose City College": "San Jose-Sunnyvale-Santa Clara",
    "West Valley College": "San Jose-Sunnyvale-Santa Clara",
    "Gavilan College": "San Jose-Sunnyvale-Santa Clara",
    "Laney College": "Oakland-Fremont-Berkeley",
    "Merritt College": "Oakland-Fremont-Berkeley",
    "College of Alameda": "Oakland-Fremont-Berkeley",
    "Berkeley City College": "Oakland-Fremont-Berkeley",
    "Chabot College": "Oakland-Fremont-Berkeley",
    "Ohlone College": "Oakland-Fremont-Berkeley",
    "Las Positas College": "Oakland-Fremont-Berkeley",
    "Diablo Valley College": "Oakland-Fremont-Berkeley",
    "Los Medanos College": "Oakland-Fremont-Berkeley",
    "Contra Costa College": "Oakland-Fremont-Berkeley",
    "City College of San Francisco": "San Francisco-San Mateo-Redwood City",
    "Cañada College": "San Francisco-San Mateo-Redwood City",
    "College of San Mateo": "San Francisco-San Mateo-Redwood City",
    "Skyline College": "San Francisco-San Mateo-Redwood City",
    "Santa Rosa Junior College": "Santa Rosa-Petaluma",
    "Napa Valley College": "Napa",
    "Solano Community College": "Vallejo",
    "Cabrillo College": "Santa Cruz-Watsonville",
    "College of Marin": "San Rafael",
    # Los Angeles
    "Los Angeles City College": "Los Angeles-Long Beach-Glendale",
    "Citrus College": "Los Angeles-Long Beach-Glendale",
    # Orange County
    "Coastline College": "Anaheim-Santa Ana-Irvine",
    "Cypress College": "Anaheim-Santa Ana-Irvine",
    "Golden West College": "Anaheim-Santa Ana-Irvine",
    "Orange Coast College": "Anaheim-Santa Ana-Irvine",
    # Inland Empire / Desert
    "College of the Desert": "Riverside-San Bernardino-Ontario",
    # Sacramento
    "American River College": "Sacramento-Roseville-Folsom",
    "Sacramento City College": "Sacramento-Roseville-Folsom",
    "College of the Sequoias": ["Visalia", "Fresno"],
    "Compton College": "Los Angeles-Long Beach-Glendale",
    "Mendocino College": ["North Coast", "Santa Rosa-Petaluma"],
    "Lassen College": ["North Valley-Northern Mountains", "Redding"],
    # Central / South Coast
    "Allan Hancock College": "Santa Maria-Santa Barbara",
    "Santa Barbara City College": "Santa Maria-Santa Barbara",
    # Rural
    "College of the Siskiyous": ["North Valley-Northern Mountains", "Redding"],
    "Butte College": ["Chico", "Sacramento-Roseville-Folsom"],
    "Lake Tahoe Community College": ["Eastern Sierra-Mother Lode", "Sacramento-Roseville-Folsom"],
}


def get_college_metros(college_name: str) -> list[str]:
    """Return the OEWS metro(s) for a college as a list."""
    entry = COLLEGE_REGION_MAP.get(college_name, "")
    return entry if isinstance(entry, list) else [entry] if entry else []


# College name → COE region for graph loading (occupation + employer region linking).
# Single string — rural colleges that previously mapped to multiple OEWS metros
# now map to one COE region (e.g. COS → "CVML" instead of ["Visalia", "Fresno"]).
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
    # Los Angeles
    "Los Angeles City College": "LA",
    "Citrus College": "LA",
    "Compton College": "LA",
    # Orange County
    "Coastline College": "OC",
    "Cypress College": "OC",
    "Golden West College": "OC",
    "Orange Coast College": "OC",
    # Inland Empire / Desert
    "College of the Desert": "IE/D",
    # Greater Sacramento
    "American River College": "GS",
    "Sacramento City College": "GS",
    "Butte College": "GS",
    "Lake Tahoe Community College": "GS",
    # Central Valley / Mother Lode
    "College of the Sequoias": "CVML",
    # Central / South Coast
    "Allan Hancock College": "SCC",
    "Santa Barbara City College": "SCC",
    # Far North
    "Mendocino College": "FN",
    "Lassen College": "FN",
    "College of the Siskiyous": "FN",
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


# College name → counties to search for EDD employer data.
# For urban colleges, this defaults to the counties in their OEWS metro.
# For rural colleges, this expands to include adjacent counties where
# students realistically commute for employment.
# If a college is not listed here, the scraper uses METRO_COUNTIES[metro].
COLLEGE_SEARCH_COUNTIES: dict[str, list[str]] = {
    # Rural Far North — Shasta (Redding) is the regional hub
    "Lassen College": ["Lassen", "Shasta", "Tehama", "Plumas"],
    "College of the Siskiyous": ["Siskiyou", "Shasta"],
    "Butte College": ["Butte", "Glenn", "Tehama"],
    # North Coast — Sonoma is the nearest large economy
    "Mendocino College": ["Mendocino", "Lake", "Humboldt", "Sonoma"],
    # Central Valley — adjacent major metros
    "College of the Sequoias": ["Tulare", "Fresno", "Kings"],
    # Sierra — Sacramento is the commutable hub
    "Lake Tahoe Community College": ["El Dorado", "Placer", "Alpine"],
}
