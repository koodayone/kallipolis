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
    "far-north": "FN",
    "sierra-nevada": "GS",
}

# College name → OEWS metro (used by loader.py for IN_MARKET edges)
# Currently Bay Area only; will expand with OEWS statewide parsing.
COLLEGE_REGION_MAP: dict[str, str] = {
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
    # Sacramento
    "American River College": "Sacramento-Roseville-Folsom",
    "Sacramento City College": "Sacramento-Roseville-Folsom",
    "College of the Sequoias": "Visalia",
    "Compton College": "Los Angeles-Long Beach-Glendale",
    "Mendocino College": "North Coast",
    # Central / South Coast
    "Allan Hancock College": "Santa Maria-Santa Barbara",
    "Santa Barbara City College": "Santa Maria-Santa Barbara",
    # Rural
    "Lake Tahoe Community College": "Eastern Sierra-Mother Lode",
}

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
