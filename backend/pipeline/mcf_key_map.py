"""
Mapping between catalog PDF keys (used in cache filenames) and MCF keys (used in
MasterCourseFile_{key}.csv filenames). Both naming conventions exist because the
catalog_sources.json uses condensed keys while MCF files use snake_case from the
Chancellor's Office college names.

Usage:
    from pipeline.mcf_key_map import pdf_to_mcf_key, mcf_to_pdf_key
"""

# PDF cache key → MCF filename key
# Only entries where the keys differ are listed.
# If a PDF key is not in this dict, assume the MCF key is identical.
_PDF_TO_MCF = {
    "berkeleycc": "berkeley_city",
    "cerrocoso": "cerro_coso",
    "contracosta": "contra_costa",
    "coppermountain": "copper_mountain_college",
    "cosumnesriver": "cosumnes_river",
    "csm": "san_mateo",
    "delta": "san_joaquin_delta",
    "deanza": "deanza",
    "diablo": "diablo_valley",
    "elac": "east_la",
    "elcamino": "el_camino",
    "evergreen": "evergreen_valley",
    "featherriver": "feather_river",
    "folsomlake": "folsom_lake",
    "fresnocity": "fresno_city",
    "goldenwest": "golden_west",
    "imperialvalley": "imperial",
    "irvinevalley": "irvine",
    "lacity": "la_city",
    "laharbor": "la_harbor",
    "laketahoe": "lake_tahoe",
    "lamission": "la_mission",
    "lapierce": "la_pierce",
    "lasouthwest": "la_swest",
    "laspositas": "las_positas",
    "lattc": "la_trade",
    "lavalley": "la_valley",
    "longbeach": "long_beach",
    "losmedanos": "los_medanos",
    "morenovalley": "moreno_valley",
    "mtsac": "mt_san_antonio",
    "mtsanjacinto": "mt_san_jacinto",
    "napavalley": "napa",
    "orangecoast": "orange_coast",
    "riohondo": "rio_hondo",
    "sacramentocity": "sacramento_city",
    "sanjosecity": "san_jose_city",
    "santaana": "santa_ana",
    "santamonica": "santa_monica",
    "santarosa": "santa_rosa",
    "santiagocanyon": "santiago_canyon",
    "sbcc": "santa_barbara",
    "sbvalley": "san_bernardino",
    "sdcity": "san_diego_city",
    "sdmesa": "san_diego_mesa",
    "sdmiramar": "san_diego_miramar",
    "victorvalley": "victor_valley",
    "westla": "west_la",
    "westvalley": "west_valley",
    "westhillscoalinga": "coalinga_college",
    "westhillslemoore": "lemoore_college",
    "craftonhills": "crafton_hills",
    "allanhancock": "allan_hancock",
    "americanriver": "american_river",
    "antelopevalley": "antelope_valley",
    "reedley": "reedley_college",
}

# Build reverse mapping
_MCF_TO_PDF = {v: k for k, v in _PDF_TO_MCF.items()}


def pdf_to_mcf_key(pdf_key: str) -> str:
    """Convert a catalog PDF key to the corresponding MCF filename key."""
    return _PDF_TO_MCF.get(pdf_key, pdf_key)


def mcf_to_pdf_key(mcf_key: str) -> str:
    """Convert an MCF filename key to the corresponding catalog PDF key."""
    return _MCF_TO_PDF.get(mcf_key, mcf_key)
