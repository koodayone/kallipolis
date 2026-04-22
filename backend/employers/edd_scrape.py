"""
Scrape employers from EDD's ALMIS Employer Database by NAICS code and size.

Two scraping modes:
  1. Major employers (countymajorer.asp) — top ~25 per county, quick overview
  2. Deep search (empResults.aspx) — by NAICS 4-digit code + size filter,
     with ASP.NET form posting for filtering and pagination

Data source: labormarketinfo.edd.ca.gov (Data Axle ALMIS database)

Usage:
    from employers.edd_scrape import deep_search, scrape_region
    employers = deep_search("0604000037", naics4="2382", min_size="E")
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
BASE_URL = "https://labormarketinfo.edd.ca.gov"
MAJOR_URL = f"{BASE_URL}/majorer/countymajorer.asp"
SEARCH_URL = f"{BASE_URL}/aspdotnet/databrowsing/empResults.aspx"
DETAIL_URL = f"{BASE_URL}/aspdotnet/databrowsing/empDetails.aspx"

# Size range codes: A=1-4, B=5-9, C=10-19, D=20-49, E=50-99,
# F=100-249, G=250-499, H=500-999, I=1000-4999
SIZE_CODES = {
    "A": "1-4 employees", "B": "5-9 employees", "C": "10-19 employees",
    "D": "20-49 employees", "E": "50-99 employees", "F": "100-249 employees",
    "G": "250-499 employees", "H": "500-999 employees", "I": "1,000-4,999 employees",
}

# County FIPS codes
COUNTY_CODES: dict[str, str] = {
    "Alameda": "000001", "Alpine": "000003", "Amador": "000005",
    "Butte": "000007", "Calaveras": "000009", "Colusa": "000011",
    "Contra Costa": "000013", "Del Norte": "000015", "El Dorado": "000017",
    "Fresno": "000019", "Glenn": "000021", "Humboldt": "000023",
    "Imperial": "000025", "Inyo": "000027", "Kern": "000029",
    "Kings": "000031", "Lake": "000033", "Lassen": "000035",
    "Los Angeles": "000037", "Madera": "000039", "Marin": "000041",
    "Mariposa": "000043", "Mendocino": "000045", "Merced": "000047",
    "Modoc": "000049", "Mono": "000051", "Monterey": "000053",
    "Napa": "000055", "Nevada": "000057", "Orange": "000059",
    "Placer": "000061", "Plumas": "000063", "Riverside": "000065",
    "Sacramento": "000067", "San Benito": "000069", "San Bernardino": "000071",
    "San Diego": "000073", "San Francisco": "000075", "San Joaquin": "000077",
    "San Luis Obispo": "000079", "San Mateo": "000081", "Santa Barbara": "000083",
    "Santa Clara": "000085", "Santa Cruz": "000087", "Shasta": "000089",
    "Sierra": "000091", "Siskiyou": "000093", "Solano": "000095",
    "Sonoma": "000097", "Stanislaus": "000099", "Sutter": "000101",
    "Tehama": "000103", "Trinity": "000105", "Tulare": "000107",
    "Tuolumne": "000109", "Ventura": "000111", "Yolo": "000113",
    "Yuba": "000115",
}


# CTE-relevant NAICS 4-digit codes, organized by the Strong Workforce
# Program sector framework from the Chancellor's Office PCAH file
# `TOP Codes to Sectors.xlsx` (shipped in-repo at
# backend/ontology/data/). The list below maps each NAICS 4-digit code
# to one or more of the 12 canonical PCAH sectors; the sector string
# set is loaded from the xlsx at import time so this module stays in
# sync with the occupation side of the ontology (which reads the same
# file via backend.ontology.crosswalks._load_pcah_cte_top6).
#
# Every NAICS code in this list maps to at least one SWP sector. Codes
# that don't represent any SWP sector (finance, insurance, real
# estate, legal services outside business-admin support, religious
# and civic organizations, general government administration beyond
# Public Safety and Environmental Quality) are deliberately excluded.
#
# The EDD's naicsect URL parameter uses the NAICS 2-digit code for most
# sectors; manufacturing codes (31/32/33) can use any of the three
# interchangeably.
#
# Staffing and business-support codes (5613, 5614) are excluded because
# their members place workers at other employers rather than hire onto
# their own payroll.
#
# Format: {naics4: (naicsect, label, [swp_sectors])}. The first sector
# in the list is the primary classification; any additional sectors
# reflect legitimate cross-sector representation.


def _load_swp_sectors() -> tuple[str, ...]:
    """Load the canonical SWP sector tuple from the PCAH xlsx.

    Mirrors the occupation side (`_load_pcah_cte_top6`) by reading the
    same file. Excludes the administrative "Unassigned" bucket. Sorted
    alphabetically for determinism.
    """
    # Imported lazily to avoid a circular import at module load; the
    # ontology.crosswalks module does not depend on anything in this
    # package, so this is a one-way dependency.
    from ontology.crosswalks import _load_pcah_cte_top6

    mapping = _load_pcah_cte_top6()
    return tuple(sorted(set(mapping.values()) - {"Unassigned"}))


SWP_SECTORS: tuple[str, ...] = _load_swp_sectors()

# Shorthand used only in CTE_NAICS_CODES to keep row widths readable.
# Strings verbatim from the PCAH xlsx — any edit here must round-trip
# through _load_swp_sectors() (which is enforced by the invariant
# test_every_sector_tag_is_in_swp_sectors).
_AMAT = "Advanced Manufacturing"
_ATL = "Advanced Transportation and Logistics"
_AWET = "Agriculture, Water and Environmental Technologies"
_BE = "Business and Entrepreneurship"
_EHD = "Education and Human Development"
_ECU = "Energy, Construction and Utilities"
_GT = "Global Trade"
_HEALTH = "Health"
_ICT = "Information and Communication Technologies - Digital Media"
_LIFE_SCI = "Life Sciences - Biotechnology"
_PS = "Public Safety"
_RHT = "Retail, Hospitality and Tourism"

CTE_NAICS_CODES: dict[str, tuple[str, str, list[str]]] = {
    # ── Agriculture, Water and Environmental Technologies ───────────
    "1111": ("11", "Agriculture - Oilseed/Grain", [_AWET]),
    "1112": ("11", "Agriculture - Vegetables/Melons", [_AWET]),
    "1113": ("11", "Agriculture - Fruit/Tree Nuts", [_AWET]),
    "1114": ("11", "Agriculture - Greenhouse/Nursery", [_AWET]),
    "1119": ("11", "Agriculture - Other Crops", [_AWET]),
    "1121": ("11", "Agriculture - Cattle", [_AWET]),
    "1122": ("11", "Agriculture - Hogs/Pigs", [_AWET]),
    "1123": ("11", "Agriculture - Poultry/Eggs", [_AWET]),
    "1124": ("11", "Agriculture - Sheep/Goats", [_AWET]),
    "1125": ("11", "Agriculture - Aquaculture", [_AWET]),
    "1129": ("11", "Agriculture - Other Animals", [_AWET]),
    "1151": ("11", "Agriculture - Crop Support", [_AWET]),
    "1152": ("11", "Agriculture - Animal Support", [_AWET]),
    "2213": ("22", "Utilities - Water/Sewer", [_AWET, _ECU]),
    "3111": ("31", "Manufacturing - Animal Food", [_AWET]),
    "3114": ("31", "Manufacturing - Fruit/Vegetable Preserving", [_AWET]),
    "3115": ("31", "Manufacturing - Dairy Products", [_AWET]),
    "3116": ("31", "Manufacturing - Meat Processing", [_AWET]),
    "3117": ("31", "Manufacturing - Seafood Processing", [_AWET]),
    "3118": ("31", "Manufacturing - Bakeries", [_AWET, _BE]),
    "3119": ("31", "Manufacturing - Other Food", [_AWET]),
    "3121": ("31", "Manufacturing - Beverages", [_AWET]),
    "4245": ("42", "Wholesale - Farm Products", [_AWET, _GT]),
    "5621": ("56", "Waste - Collection", [_AWET]),
    "5622": ("56", "Waste - Treatment/Disposal", [_AWET]),
    "9241": ("92", "Environmental Quality - Government", [_AWET]),

    # ── Advanced Manufacturing ──────────────────────────────────────
    "3211": ("32", "Manufacturing - Sawmills/Wood", [_AMAT]),
    "3212": ("32", "Manufacturing - Veneer/Plywood", [_AMAT]),
    "3219": ("32", "Manufacturing - Other Wood Products", [_AMAT]),
    "3231": ("32", "Manufacturing - Printing", [_AMAT]),
    "3261": ("32", "Manufacturing - Plastics", [_AMAT]),
    "3273": ("32", "Manufacturing - Cement/Concrete", [_AMAT]),
    "3323": ("33", "Manufacturing - Architectural Metals", [_AMAT]),
    "3327": ("33", "Manufacturing - Machine Shops", [_AMAT]),
    "3328": ("33", "Manufacturing - Coating/Engraving", [_AMAT]),
    "3329": ("33", "Manufacturing - Other Fabricated Metals", [_AMAT]),
    "3331": ("33", "Manufacturing - Ag/Construction Machinery", [_AMAT, _AWET]),
    "3332": ("33", "Manufacturing - Industrial Machinery", [_AMAT]),
    "3335": ("33", "Manufacturing - Metalworking Machinery", [_AMAT]),

    # ── Advanced Transportation and Logistics ───────────────────────
    "3361": ("33", "Manufacturing - Motor Vehicles", [_ATL, _AMAT]),
    "3363": ("33", "Manufacturing - Motor Vehicle Parts", [_ATL, _AMAT]),
    "3364": ("33", "Manufacturing - Aerospace", [_ATL, _AMAT]),
    "3366": ("33", "Manufacturing - Ship/Boat", [_ATL, _AMAT]),
    "4231": ("42", "Wholesale - Motor Vehicles/Parts", [_ATL, _GT]),
    "4811": ("48", "Transportation - Air", [_ATL, _GT]),
    "4841": ("48", "Transportation - Trucking (General)", [_ATL, _GT]),
    "4842": ("48", "Transportation - Trucking (Specialized)", [_ATL, _GT]),
    "4851": ("48", "Transportation - Transit/Ground Passenger", [_ATL]),
    "4853": ("48", "Transportation - Taxi/Limo", [_ATL]),
    "4854": ("48", "Transportation - School Bus", [_ATL]),
    "4859": ("48", "Transportation - Other Transit", [_ATL]),
    "4881": ("48", "Transportation - Support Activities (Air)", [_ATL, _GT]),
    "4921": ("49", "Transportation - Couriers/Express Delivery", [_ATL, _GT]),
    "4931": ("49", "Transportation - Warehousing/Storage", [_ATL, _GT]),
    "8111": ("81", "Services - Auto Repair/Maintenance", [_ATL]),

    # ── Business and Entrepreneurship ───────────────────────────────
    # Cross-cutting sector housing professional services that serve small
    # and medium businesses as customers, plus personal-service
    # industries with small-operator workforce patterns.
    "5412": ("54", "Professional - Accounting/Tax", [_BE]),
    "5413": ("54", "Professional - Architecture/Engineering", [_BE, _AMAT]),
    "5414": ("54", "Professional - Graphic/Industrial Design", [_BE]),
    "5416": ("54", "Professional - Management/Technical Consulting", [_BE]),
    "5418": ("54", "Professional - Advertising/PR", [_BE]),
    "5617": ("56", "Admin - Janitorial/Landscaping", [_BE, _AWET]),
    "8121": ("81", "Services - Personal Care", [_BE]),

    # ── Education and Human Development ─────────────────────────────
    # K-12 districts are among the largest CTE employers in any region
    # (facilities, operations, food service, transportation, admin).
    # Post-secondary education, educational support services, and
    # social-services sub-sectors round out the sector.
    "6111": ("61", "Education - Elementary/Secondary", [_EHD]),
    "6112": ("61", "Education - Junior Colleges", [_EHD]),
    "6113": ("61", "Education - Colleges/Universities", [_EHD]),
    "6114": ("61", "Education - Business/Management Training", [_EHD, _BE]),
    "6115": ("61", "Education - Technical/Trade Schools", [_EHD]),
    "6116": ("61", "Education - Other Schools", [_EHD]),
    "6117": ("61", "Education - Educational Support Services", [_EHD]),
    "6241": ("62", "Social Services - Individual/Family", [_EHD]),
    "6242": ("62", "Social Services - Community Emergency Relief", [_EHD]),
    "6243": ("62", "Social Services - Vocational Rehab", [_EHD]),
    "6244": ("62", "Social Services - Child Day Care", [_EHD, _BE]),

    # ── Energy, Construction and Utilities ──────────────────────────
    # Canonical SWP taxonomy groups construction with utilities and
    # energy — skilled trades and infrastructure workforce treated as
    # one sector. The per-employer NAICS still distinguishes them for
    # display.
    "2111": ("21", "Mining - Oil/Gas Extraction", [_ECU]),
    "2211": ("22", "Utilities - Electric Power", [_ECU]),
    "2212": ("22", "Utilities - Natural Gas", [_ECU]),
    "2361": ("23", "Construction - Residential", [_ECU]),
    "2362": ("23", "Construction - Commercial", [_ECU]),
    "2371": ("23", "Construction - Utility Systems", [_ECU]),
    "2373": ("23", "Construction - Highway/Street", [_ECU, _ATL]),
    "2379": ("23", "Construction - Other Heavy", [_ECU]),
    "2381": ("23", "Construction - Foundation/Structural", [_ECU, _AMAT]),
    "2382": ("23", "Construction - HVAC/Plumbing/Electrical", [_ECU]),
    "2383": ("23", "Construction - Finishing", [_ECU]),
    "2389": ("23", "Construction - Other Specialty", [_ECU]),
    "3241": ("32", "Manufacturing - Petroleum/Coal", [_ECU, _AMAT]),
    "3334": ("33", "Manufacturing - HVAC Equipment", [_ECU, _AMAT]),
    "3351": ("33", "Manufacturing - Electrical Equipment", [_ECU, _AMAT]),

    # ── Global Trade ────────────────────────────────────────────────
    # Under the canonical taxonomy, Logistics moved to Advanced
    # Transportation and Logistics. Global Trade now covers wholesale
    # distribution chains.
    "4234": ("42", "Wholesale - Professional Equipment", [_GT]),
    "4241": ("42", "Wholesale - Paper/Packaging", [_GT]),
    "4244": ("42", "Wholesale - Grocery/Related", [_GT, _AWET]),
    "4247": ("42", "Wholesale - Petroleum", [_GT, _ECU]),
    "4249": ("42", "Wholesale - Miscellaneous Nondurable", [_GT]),

    # ── Health ──────────────────────────────────────────────────────
    "6211": ("62", "Healthcare - Physician Offices", [_HEALTH]),
    "6212": ("62", "Healthcare - Dental", [_HEALTH]),
    "6213": ("62", "Healthcare - Other Practitioners", [_HEALTH]),
    "6214": ("62", "Healthcare - Outpatient", [_HEALTH]),
    "6215": ("62", "Healthcare - Labs", [_HEALTH, _LIFE_SCI]),
    "6216": ("62", "Healthcare - Home Health", [_HEALTH]),
    "6219": ("62", "Healthcare - Other Ambulatory", [_HEALTH]),
    "6221": ("62", "Healthcare - Hospitals (General)", [_HEALTH]),
    "6222": ("62", "Healthcare - Hospitals (Psych/Substance)", [_HEALTH]),
    "6223": ("62", "Healthcare - Hospitals (Specialty)", [_HEALTH]),
    "6231": ("62", "Healthcare - Nursing Facilities", [_HEALTH]),
    "6232": ("62", "Healthcare - Residential Care", [_HEALTH]),
    "6233": ("62", "Healthcare - Continuing Care", [_HEALTH]),
    "3391": ("33", "Manufacturing - Medical Equipment", [_HEALTH, _LIFE_SCI, _AMAT]),

    # ── Information and Communication Technologies - Digital Media ──
    "3341": ("33", "Manufacturing - Computers", [_ICT, _AMAT]),
    "3344": ("33", "Manufacturing - Semiconductors", [_ICT, _AMAT]),
    "5112": ("51", "IT - Software Publishing", [_ICT]),
    "5121": ("51", "Media - Motion Picture/Video", [_ICT]),
    "5122": ("51", "Media - Sound Recording", [_ICT]),
    "5151": ("51", "Media - Radio/TV Broadcasting", [_ICT]),
    "5171": ("51", "IT - Telecommunications (Wired)", [_ICT]),
    "5172": ("51", "IT - Telecommunications (Wireless)", [_ICT]),
    "5182": ("51", "IT - Data Processing/Hosting", [_ICT]),
    "5191": ("51", "IT - Other Information Services/Web Portals", [_ICT]),
    "5415": ("54", "Professional - Computer Systems Design", [_ICT]),

    # ── Life Sciences - Biotechnology ───────────────────────────────
    "3254": ("32", "Manufacturing - Pharmaceuticals", [_LIFE_SCI, _AMAT]),
    "3345": ("33", "Manufacturing - Instruments", [_LIFE_SCI, _AMAT]),
    "5417": ("54", "Professional - Scientific R&D", [_LIFE_SCI]),

    # ── Public Safety ───────────────────────────────────────────────
    # NAICS 9221 covers police, courts, corrections, and fire per the
    # 2017+ rollup. Some EDD data additionally returns 9222 as a
    # distinct Fire Protection subdivision (non-standard but preserved
    # because the upstream source uses it); both map to Public Safety.
    "9221": ("92", "Government - Justice/Public Order/Safety", [_PS]),
    "9222": ("92", "Government - Fire Protection", [_PS]),
    "5616": ("56", "Admin - Investigation/Security", [_PS]),

    # ── Retail, Hospitality and Tourism ─────────────────────────────
    "4248": ("42", "Wholesale - Beer/Wine/Spirits", [_RHT, _AWET]),
    "4411": ("44", "Retail - Auto Dealers", [_RHT]),
    "4441": ("44", "Retail - Building Materials", [_RHT]),
    "4451": ("44", "Retail - Grocery Stores", [_RHT]),
    "4452": ("44", "Retail - Specialty Food", [_RHT]),
    "4461": ("44", "Retail - Health/Personal Care", [_RHT]),
    "4511": ("45", "Retail - Sporting Goods/Hobby", [_RHT]),
    "4521": ("45", "Retail - Department Stores", [_RHT]),
    "4529": ("45", "Retail - General Merchandise", [_RHT]),
    "7131": ("71", "Arts - Amusement Parks/Arcades", [_RHT]),
    "7139": ("71", "Arts - Other Amusement/Recreation", [_RHT]),
    "7211": ("72", "Hospitality - Hotels/Motels", [_RHT]),
    "7212": ("72", "Hospitality - RV Parks/Camps", [_RHT]),
    "7223": ("72", "Food Service - Special/Caterers", [_RHT, _BE]),
    "7224": ("72", "Food Service - Bars", [_RHT]),
    "7225": ("72", "Food Service - Restaurants", [_RHT]),
}

# Default size filter: 100+ employees (F=100-249, G=250-499, H=500-999, I=1000-4999)
DEFAULT_MIN_SIZE = "F"


# ── HTML parsing ──────────────────────────────────────────────────────────

_ROW_PATTERN = re.compile(
    r'empDetails\.aspx\?menuChoice=emp&(?:amp;)?empid=(\d+)&(?:amp;)?geogArea=(\d+)">'
    r'\s*([^<]+)</a></td>'
    r'<td class="tableData">([^<]*)</td>'    # address
    r'<td class="tableData">([^<]*)</td>'    # city
    r'<td class="tableData">([^<]*)</td>'    # industry
    r'<td class="tableData">([^<]*)</td>',   # size
    re.IGNORECASE,
)


# Sentinel markers present on every empResults.aspx page. Used to
# distinguish a legitimate empty result set from an HTML-structure
# shift that silently broke _ROW_PATTERN or _extract_form_state.
_RESULT_TABLE_SENTINEL = "empDetails.aspx"
_FORM_SENTINEL = "__VIEWSTATE"


def _parse_employer_rows(html: str) -> list[dict]:
    """Parse employer table rows from empResults page.

    Returns an empty list both for "no results" and "markup shift broke
    the selector"; the two cases are distinguishable by inspecting the
    returned list together with the result_table_present flag from
    _is_result_page_recognizable.
    """
    rows = _ROW_PATTERN.findall(html)
    employers = []
    for emp_id, geog, name, addr, city, industry, size in rows:
        size_clean = re.sub(r"\s+", " ", size).strip()
        employers.append({
            "name": name.strip(),
            "address": addr.strip(),
            "city": city.strip(),
            "industry": industry.strip(),
            "size_class": size_clean,
            "emp_id": emp_id.strip(),
            "geog_area": geog.strip(),
        })
    if not employers and _RESULT_TABLE_SENTINEL in html and "tableData" in html:
        logger.warning(
            "  _parse_employer_rows: 0 rows but result table markers present — "
            "EDD page structure may have shifted"
        )
    return employers


def _extract_form_state(html: str) -> dict:
    """Extract ASP.NET form state for POST requests.

    If the sentinel __VIEWSTATE token is present but the regex fails to
    capture, logs a warning so the operator can tell markup drift apart
    from a page that never had form state to begin with.
    """
    state = {}
    for field in ("__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"):
        match = re.search(rf'{field}.*?value="([^"]+)"', html)
        if match:
            state[field] = match.group(1)
    if _FORM_SENTINEL in html and "__VIEWSTATE" not in state:
        logger.warning(
            "  _extract_form_state: __VIEWSTATE token present but regex failed "
            "to capture — EDD form rendering may have shifted"
        )
    return state


# ── Deep search (NAICS + size filtered) ───────────────────────────────────

def deep_search(
    geog_area: str,
    naics_sect: str | None = None,
    naics4: str | None = None,
    min_size: str = "E",
    max_pages: int = 20,
    county_name: str = "",
) -> list[dict]:
    """Search EDD employer database by geography, NAICS code, and size.

    Args:
        geog_area: EDD geography code (e.g., "0604000037" for LA County)
        naics_sect: NAICS 2-digit sector (e.g., "23" for construction)
        naics4: NAICS 4-digit code (e.g., "2382" for HVAC/plumbing/electrical)
        min_size: Minimum size code (A-I). Default "E" = 50+ employees.
        max_pages: Maximum pages to paginate through.
        county_name: County name for logging/metadata.

    Returns: list of employer dicts with name, city, industry, size_class, etc.
    """
    # Build initial URL
    params = {
        "menuChoice": "emp",
        "searchType": "Geography",
        "geogArea": geog_area,
    }
    if naics_sect:
        params["naicsect"] = naics_sect
    if naics4:
        params["naicscode4"] = naics4

    session = requests.Session()

    try:
        # Initial GET
        r = session.get(SEARCH_URL, params=params, verify=False, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"  Failed to load search page: {e}")
        return []

    html = r.text
    form_state = _extract_form_state(html)

    if not form_state.get("__VIEWSTATE"):
        logger.warning(f"  No ViewState found — page structure may have changed")
        return _parse_employer_rows(html)

    # Build size filter — select all size codes >= min_size that exist on this page
    size_order = list(SIZE_CODES.keys())
    min_idx = size_order.index(min_size) if min_size in size_order else 0
    desired_sizes = set(size_order[min_idx:])

    # Parse which size options are actually available on this page
    lb_match = re.search(r"lbEmpSizes.*?</select>", html, re.DOTALL)
    available_sizes = set()
    if lb_match:
        for opt in re.findall(r'value="([A-Z] )"', lb_match.group(0)):
            available_sizes.add(opt.strip())

    selected_sizes = [f"{code} " for code in size_order if code in desired_sizes and code in available_sizes]
    if not selected_sizes:
        logger.info(f"    No size options >= {min_size} available")
        return []

    # POST to apply size filter
    filter_data = {
        "__VIEWSTATE": form_state["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": form_state.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTVALIDATION": form_state.get("__EVENTVALIDATION", ""),
        "master$cphMain$lbEmpSizes": selected_sizes,
        "master$cphMain$btnFilter": "Filter",
    }

    try:
        r2 = session.post(SEARCH_URL, data=filter_data, params=params, verify=False, timeout=30)
        r2.raise_for_status()
    except Exception as e:
        logger.error(f"  Filter POST failed: {e}")
        return _parse_employer_rows(html)

    html = r2.text
    all_employers = _parse_employer_rows(html)

    if not all_employers:
        return []

    # Paginate
    pages_fetched = 1
    for page in range(2, max_pages + 1):
        form_state = _extract_form_state(html)
        if not form_state.get("__VIEWSTATE"):
            break

        # Check if next page button exists
        if "btnGridPagerNext" not in html:
            break

        page_data = {
            "__VIEWSTATE": form_state["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": form_state.get("__VIEWSTATEGENERATOR", ""),
            "__EVENTVALIDATION": form_state.get("__EVENTVALIDATION", ""),
            "master$cphMain$dgpGrid$btnGridPagerNext": "Next",
        }

        try:
            r3 = session.post(SEARCH_URL, data=page_data, params=params, verify=False, timeout=30)
            r3.raise_for_status()
        except Exception as e:
            logger.warning(f"  Pagination failed on page {page}: {e}")
            break

        html = r3.text
        new_rows = _parse_employer_rows(html)
        if not new_rows:
            break
        all_employers.extend(new_rows)
        pages_fetched = page
        time.sleep(0.3)

    # Warn on silent truncation: pagination hit max_pages but another
    # "Next" button is still present, meaning additional results were
    # left unfetched.
    if pages_fetched >= max_pages and "btnGridPagerNext" in html:
        logger.warning(
            f"  Pagination truncated at max_pages={max_pages} for "
            f"{county_name or geog_area} naics4={naics4} — results incomplete"
        )

    # Deduplicate by (name, city)
    seen = set()
    unique = []
    for emp in all_employers:
        key = (emp["name"].lower(), emp["city"].lower())
        if key not in seen:
            seen.add(key)
            emp["county"] = county_name
            unique.append(emp)

    return unique


def search_naics_codes(
    county_name: str,
    naics_codes: list[str] | None = None,
    min_size: str = DEFAULT_MIN_SIZE,
    max_pages_per_code: int = 10,
) -> list[dict]:
    """Search CTE-relevant NAICS 4-digit codes in a county.

    Args:
        county_name: California county name (e.g., "Los Angeles")
        naics_codes: List of NAICS 4-digit codes. If None, uses all CTE_NAICS_CODES.
        min_size: Minimum size code. Default "G" = 250+ employees.
        max_pages_per_code: Max pages to paginate per NAICS code.

    Returns: deduplicated list of employer dicts.
    """
    code = COUNTY_CODES.get(county_name)
    if not code:
        logger.error(f"  Unknown county: {county_name}")
        return []

    if naics_codes is None:
        naics_codes = list(CTE_NAICS_CODES.keys())

    geog = f"0604{code}"
    all_employers: list[dict] = []
    seen_keys: set[tuple] = set()

    for naics4 in naics_codes:
        entry = CTE_NAICS_CODES.get(naics4)
        if entry:
            naics_sect, label, _sectors = entry
        else:
            naics_sect = naics4[:2]
            label = f"NAICS {naics4}"

        logger.info(f"  {county_name} — {label} (NAICS {naics4}, size {min_size}+)")

        results = deep_search(
            geog_area=geog,
            naics_sect=naics_sect,
            naics4=naics4,
            min_size=min_size,
            max_pages=max_pages_per_code,
            county_name=county_name,
        )

        for emp in results:
            key = (emp["name"].lower(), emp["city"].lower())
            if key not in seen_keys:
                seen_keys.add(key)
                emp["naics4"] = naics4
                emp["naics_label"] = label
                all_employers.append(emp)

        if results:
            logger.info(f"    {len(results)} employers ({len(all_employers)} total unique)")
        else:
            logger.debug(f"    0 results for {label}")
        time.sleep(0.5)

    return all_employers


def scrape_region(
    region_code: str,
    naics_codes: list[str] | None = None,
    min_size: str = DEFAULT_MIN_SIZE,
) -> list[dict]:
    """Search all counties in a COE region for CTE-relevant employers.

    The COE region is the institutional unit used by the California Community
    Colleges Chancellor's Office, the Strong Workforce Program, and the
    Centers of Excellence. Each region maps to a fixed set of counties via
    COE_REGION_TO_COUNTIES.
    """
    from ontology.regions import COE_REGION_TO_COUNTIES

    counties = COE_REGION_TO_COUNTIES.get(region_code, [])
    if not counties:
        logger.error(f"Unknown COE region: {region_code}")
        return []

    if naics_codes is None:
        naics_codes = list(CTE_NAICS_CODES.keys())

    logger.info(
        f"Scraping region {region_code} ({len(counties)} counties, "
        f"{len(naics_codes)} NAICS codes, min_size={min_size})"
    )

    all_employers: list[dict] = []
    seen_keys: set[tuple] = set()

    for i, county_name in enumerate(counties, 1):
        logger.info(f"  County {i}/{len(counties)}: {county_name}")
        results = search_naics_codes(county_name, naics_codes, min_size)
        for emp in results:
            key = (emp["name"].lower(), emp["city"].lower())
            if key not in seen_keys:
                seen_keys.add(key)
                all_employers.append(emp)

    logger.info(f"Total unique employers across {region_code}: {len(all_employers)}")

    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = _region_cache_path(region_code, min_size)
    with open(cache_path, "w") as f:
        json.dump(all_employers, f, indent=2)
    logger.info(f"Cached to {cache_path.name}")

    return all_employers


def _region_cache_path(region_code: str, min_size: str = DEFAULT_MIN_SIZE) -> Path:
    sanitized = region_code.lower().replace("/", "_")
    return CACHE_DIR / f"edd_region_{sanitized}_{min_size.lower()}.json"


def load_region_cached(region_code: str, min_size: str = DEFAULT_MIN_SIZE) -> list[dict] | None:
    """Load cached regional EDD employer data."""
    cache_path = _region_cache_path(region_code, min_size)
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        logger.info(f"  Loaded {len(data)} employers from regional cache ({cache_path.name})")
        return data
    return None


# ── Major employers (quick overview, kept for compatibility) ──────────────

def scrape_major_employers(county_code: str, county_name: str = "") -> list[dict]:
    """Scrape the top ~25 major employers for a county (countymajorer.asp)."""
    try:
        r = requests.get(MAJOR_URL, params={"CountyCode": county_code}, verify=False, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch major employers: {e}")
        return []

    html = r.text
    pattern = (
        r'empDetails.*?geogArea=(\d+)&(?:amp;)?empId=(\d+)">\s*\n\s*'
        r'(.+?)</[Aa]>.*?SIZE="2">\s*\n\s*(.+?)\s*\n.*?SIZE="2">\s*\n\s*(.+?)\s*\n'
    )
    matches = re.findall(pattern, html, re.DOTALL)

    employers = []
    for geog, emp_id, name, city, industry in matches:
        employers.append({
            "name": name.strip(),
            "city": city.strip(),
            "industry": industry.strip(),
            "emp_id": emp_id.strip(),
            "geog_area": geog.strip(),
            "county": county_name,
        })
    return employers


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    import warnings
    warnings.filterwarnings("ignore")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m pipeline.industry.edd_employers LA         # major employers")
        print("  python -m pipeline.industry.edd_employers LA 2382    # deep search NAICS 2382")
        print("  python -m pipeline.industry.edd_employers LA all     # all CTE NAICS codes")
        sys.exit(1)

    county = sys.argv[1]
    code = COUNTY_CODES.get(county)
    if not code:
        # Try partial match
        matches = [k for k in COUNTY_CODES if county.lower() in k.lower()]
        if matches:
            county = matches[0]
            code = COUNTY_CODES[county]
        else:
            print(f"Unknown county: {county}")
            sys.exit(1)

    if len(sys.argv) > 2:
        if sys.argv[2] == "all":
            results = search_naics_codes(county, list(CTE_NAICS_CODES.keys()), min_size="E")
        else:
            naics4 = sys.argv[2]
            geog = f"0604{code}"
            results = deep_search(geog, naics_sect=naics4[:2], naics4=naics4, min_size="E", county_name=county)
    else:
        results = scrape_major_employers(code, county)

    print(f"\n{'='*80}")
    print(f"Total: {len(results)} employers")
    print(f"{'='*80}")
    for emp in sorted(results, key=lambda e: e.get("size_class", ""), reverse=True):
        print(f"  {emp['name']:45s} | {emp.get('city', ''):20s} | {emp.get('size_class', ''):22s} | {emp.get('industry', '')}")
