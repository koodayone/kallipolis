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

# COE region code → SWP priority sectors as named in each region's
# Strong Workforce Program development plan. Sourced from the 2023-2029
# regional plans. GS and FN share the North/Far North consortium plan;
# both receive the same priority set (top 5 by investment allocation).
# "CA" is omitted — it is a statewide aggregate, not a consortium.
COE_REGION_PRIORITY_SECTORS: dict[str, list[str]] = {
    "Bay": [
        "Advanced Manufacturing",
        "Advanced Transportation",
        "Health",
        "ICT / Digital Media",
        "Public Safety",
        "Education",
    ],
    "CVML": [
        "Advanced Manufacturing",
        "Agriculture, Water & Environmental Technologies",
        "Health",
        "Retail, Hospitality & Tourism",
        "Business & Entrepreneurship",
        "ICT / Digital Media",
    ],
    "FN": [
        "Advanced Manufacturing",
        "Health",
        "Public Safety",
        "Advanced Transportation & Logistics",
        "Energy, Construction & Utilities",
    ],
    "GS": [
        "Advanced Manufacturing",
        "Health",
        "Public Safety",
        "Advanced Transportation & Logistics",
        "Energy, Construction & Utilities",
    ],
    "IE/D": [
        "Advanced Manufacturing",
        "Advanced Transportation & Logistics",
        "Business & Entrepreneurship",
        "Energy, Construction & Utilities",
        "Health",
        "ICT / Digital Media",
        "Retail, Hospitality & Tourism",
    ],
    "LA": [
        "Advanced Manufacturing",
        "Advanced Transportation & Logistics",
        "Business & Entrepreneurship",
        "Energy, Construction & Utilities",
        "Health",
        "ICT / Digital Media",
        "Life Sciences & Biotechnology",
        "Retail, Hospitality & Tourism",
    ],
    "OC": [
        "Health",
        "ICT / Digital Media",
        "Business & Entrepreneurship",
        "Education & Human Development",
        "Energy, Construction & Utilities",
        "Life Sciences & Biotechnology",
    ],
    "SCC": [
        "Advanced Manufacturing",
        "Advanced Transportation",
        "Agriculture, Water & Environmental Technologies",
        "Business & Entrepreneurship",
        "Education",
        "Energy, Construction & Utilities",
        "Health",
        "ICT / Digital Media",
        "Life Sciences & Biotechnology",
        "Public Safety",
        "Retail, Hospitality & Tourism",
    ],
    "SD/I": [
        "Advanced Manufacturing",
        "Advanced Transportation & Logistics",
        "Health",
        "ICT / Digital Media",
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


# College name → OEWS metro(s) for occupation demand data and IN_MARKET edges.
# Single string for urban colleges, list for rural colleges spanning multiple metros.
# Covers every college currently featured in the state atlas (logoStacked set).
COLLEGE_REGION_MAP: dict = {
    # Bay Area — Silicon Valley
    "Foothill College": "San Jose-Sunnyvale-Santa Clara",
    "De Anza College": "San Jose-Sunnyvale-Santa Clara",
    "Mission College": "San Jose-Sunnyvale-Santa Clara",
    "Evergreen Valley College": "San Jose-Sunnyvale-Santa Clara",
    "San Jose City College": "San Jose-Sunnyvale-Santa Clara",
    "West Valley College": "San Jose-Sunnyvale-Santa Clara",
    "Gavilan College": "San Jose-Sunnyvale-Santa Clara",
    # Bay Area — East Bay
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
    # Bay Area — San Francisco / Peninsula
    "City College of San Francisco": "San Francisco-San Mateo-Redwood City",
    "Cañada College": "San Francisco-San Mateo-Redwood City",
    "College of San Mateo": "San Francisco-San Mateo-Redwood City",
    "Skyline College": "San Francisco-San Mateo-Redwood City",
    # Bay Area — North Bay / outer
    "Santa Rosa Junior College": "Santa Rosa-Petaluma",
    "Napa Valley College": "Napa",
    "Solano Community College": "Vallejo",
    "Cabrillo College": "Santa Cruz-Watsonville",
    "College of Marin": "San Rafael",
    # North Coast (FN)
    "College of the Redwoods": "North Coast Region",
    "College of the Redwoods (DN)": "North Coast Region",
    "Mendocino College": ["North Coast Region", "Santa Rosa-Petaluma"],
    # Far North (FN)
    "Shasta College": "Redding",
    "Lassen College": ["North Valley-Northern Mountains Region", "Redding"],
    "College of the Siskiyous": ["North Valley-Northern Mountains Region", "Redding"],
    # Sierra Nevada (GS)
    "Feather River College": "Eastern Sierra-Mother Lode Region",
    "Columbia College": "Eastern Sierra-Mother Lode Region",
    "Lake Tahoe Community College": ["Eastern Sierra-Mother Lode Region", "Sacramento-Roseville-Folsom"],
    # Greater Sacramento
    "American River College": "Sacramento-Roseville-Folsom",
    "Sacramento City College": "Sacramento-Roseville-Folsom",
    "Cosumnes River College": "Sacramento-Roseville-Folsom",
    "Folsom Lake College": "Sacramento-Roseville-Folsom",
    "Sierra College": "Sacramento-Roseville-Folsom",
    "Woodland Community College": "Sacramento-Roseville-Folsom",
    "Yuba College": "Yuba City",
    "Butte College": ["Chico", "Sacramento-Roseville-Folsom"],
    # Central Valley / Mother Lode
    "Fresno City College": "Fresno",
    "Reedley College": "Fresno",
    "Clovis Community College": "Fresno",
    "Madera Community College": "Fresno",
    "West Hills College Coalinga": "Fresno",
    "Merced College": "Merced",
    "Modesto Junior College": "Modesto",
    "San Joaquin Delta College": "Stockton-Lodi",
    "West Hills College Lemoore": "Hanford-Corcoran",
    "College of the Sequoias": ["Visalia", "Fresno"],
    "Porterville College": "Visalia",
    "Bakersfield College": "Bakersfield-Delano",
    "Cerro Coso Community College": "Bakersfield-Delano",
    "Taft College": "Bakersfield-Delano",
    # Central / South Coast
    "Cuesta College": "San Luis Obispo-Paso Robles",
    "Hartnell College": "Salinas",
    "Monterey Peninsula College": "Salinas",
    "Allan Hancock College": "Santa Maria-Santa Barbara",
    "Santa Barbara City College": "Santa Maria-Santa Barbara",
    "Ventura College": "Oxnard-Thousand Oaks-Ventura",
    "Oxnard College": "Oxnard-Thousand Oaks-Ventura",
    "Moorpark College": "Oxnard-Thousand Oaks-Ventura",
    # Los Angeles
    "Los Angeles City College": "Los Angeles-Long Beach-Glendale",
    "Los Angeles Valley College": "Los Angeles-Long Beach-Glendale",
    "Los Angeles Harbor College": "Los Angeles-Long Beach-Glendale",
    "Los Angeles Mission College": "Los Angeles-Long Beach-Glendale",
    "East Los Angeles College": "Los Angeles-Long Beach-Glendale",
    "West Los Angeles College": "Los Angeles-Long Beach-Glendale",
    "Pasadena City College": "Los Angeles-Long Beach-Glendale",
    "Mt. San Antonio College": "Los Angeles-Long Beach-Glendale",
    "Long Beach City College": "Los Angeles-Long Beach-Glendale",
    "El Camino College": "Los Angeles-Long Beach-Glendale",
    "Santa Monica College": "Los Angeles-Long Beach-Glendale",
    "Citrus College": "Los Angeles-Long Beach-Glendale",
    "Rio Hondo College": "Los Angeles-Long Beach-Glendale",
    "Cerritos College": "Los Angeles-Long Beach-Glendale",
    "Compton College": "Los Angeles-Long Beach-Glendale",
    "Antelope Valley College": "Los Angeles-Long Beach-Glendale",
    "College of the Canyons": "Los Angeles-Long Beach-Glendale",
    # Orange County
    "Coastline College": "Anaheim-Santa Ana-Irvine",
    "Cypress College": "Anaheim-Santa Ana-Irvine",
    "Golden West College": "Anaheim-Santa Ana-Irvine",
    "Orange Coast College": "Anaheim-Santa Ana-Irvine",
    "Fullerton College": "Anaheim-Santa Ana-Irvine",
    "Santa Ana College": "Anaheim-Santa Ana-Irvine",
    "Saddleback College": "Anaheim-Santa Ana-Irvine",
    "Irvine Valley College": "Anaheim-Santa Ana-Irvine",
    # Inland Empire / Desert
    "College of the Desert": "Riverside-San Bernardino-Ontario",
    "San Bernardino Valley College": "Riverside-San Bernardino-Ontario",
    "Crafton Hills College": "Riverside-San Bernardino-Ontario",
    "Chaffey College": "Riverside-San Bernardino-Ontario",
    "Riverside City College": "Riverside-San Bernardino-Ontario",
    "Norco College": "Riverside-San Bernardino-Ontario",
    "Moreno Valley College": "Riverside-San Bernardino-Ontario",
    "Mt. San Jacinto College": "Riverside-San Bernardino-Ontario",
    "Victor Valley College": "Riverside-San Bernardino-Ontario",
    "Barstow Community College": "Riverside-San Bernardino-Ontario",
    "Palo Verde College": "Riverside-San Bernardino-Ontario",
    "Copper Mountain College": "Riverside-San Bernardino-Ontario",
    # San Diego / Imperial
    "San Diego Mesa College": "San Diego-Chula Vista-Carlsbad",
    "San Diego City College": "San Diego-Chula Vista-Carlsbad",
    "San Diego Miramar College": "San Diego-Chula Vista-Carlsbad",
    "Grossmont College": "San Diego-Chula Vista-Carlsbad",
    "Cuyamaca College": "San Diego-Chula Vista-Carlsbad",
    "Palomar College": "San Diego-Chula Vista-Carlsbad",
    "MiraCosta College": "San Diego-Chula Vista-Carlsbad",
    "Southwestern College": "San Diego-Chula Vista-Carlsbad",
    "SD College of Continuing Ed": "San Diego-Chula Vista-Carlsbad",
    "Imperial Valley College": "El Centro",
}


def get_college_metros(college_name: str) -> list[str]:
    """Return the OEWS metro(s) for a college as a list."""
    entry = COLLEGE_REGION_MAP.get(college_name, "")
    return entry if isinstance(entry, list) else [entry] if entry else []


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
    "East Los Angeles College": "LA",
    "West Los Angeles College": "LA",
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
