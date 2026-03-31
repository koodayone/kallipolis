"""
Scrape employers from EDD's ALMIS Employer Database by NAICS code and size.

Two scraping modes:
  1. Major employers (countymajorer.asp) — top ~25 per county, quick overview
  2. Deep search (empResults.aspx) — by NAICS 4-digit code + size filter,
     with ASP.NET form posting for filtering and pagination

Data source: labormarketinfo.edd.ca.gov (Data Axle ALMIS database)

Usage:
    from pipeline.industry.edd_employers import deep_search, scrape_metro
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

# OEWS metro → counties
METRO_COUNTIES: dict[str, list[str]] = {
    "Los Angeles-Long Beach-Glendale": ["Los Angeles"],
    "San Jose-Sunnyvale-Santa Clara": ["Santa Clara", "San Benito"],
    "Oakland-Fremont-Berkeley": ["Alameda", "Contra Costa"],
    "San Francisco-San Mateo-Redwood City": ["San Francisco", "San Mateo"],
    "Santa Rosa-Petaluma": ["Sonoma"],
    "Napa": ["Napa"],
    "Vallejo": ["Solano"],
    "Santa Cruz-Watsonville": ["Santa Cruz"],
    "San Rafael": ["Marin"],
    "Sacramento-Roseville-Folsom": ["Sacramento", "Placer", "El Dorado", "Yolo"],
    "Fresno": ["Fresno"],
    "Bakersfield-Delano": ["Kern"],
    "San Diego-Chula Vista-Carlsbad": ["San Diego"],
    "Riverside-San Bernardino-Ontario": ["Riverside", "San Bernardino"],
    "Anaheim-Santa Ana-Irvine": ["Orange"],
    "Stockton-Lodi": ["San Joaquin"],
    "Modesto": ["Stanislaus"],
    "Oxnard-Thousand Oaks-Ventura": ["Ventura"],
    "Salinas": ["Monterey"],
    "Visalia": ["Tulare"],
    "Redding": ["Shasta"],
    "Chico": ["Butte"],
    "Merced": ["Merced"],
    "Hanford-Corcoran": ["Kings"],
    "Yuba City": ["Sutter", "Yuba"],
    "El Centro": ["Imperial"],
    "San Luis Obispo-Paso Robles": ["San Luis Obispo"],
    "Santa Maria-Santa Barbara": ["Santa Barbara"],
}

# CTE-relevant NAICS 4-digit codes mapped to sector labels
# These are the industries where CC graduates are most commonly hired
CTE_NAICS_CODES: dict[str, str] = {
    # Healthcare
    "6211": "Healthcare - Physician Offices",
    "6212": "Healthcare - Dental",
    "6213": "Healthcare - Other Practitioners",
    "6214": "Healthcare - Outpatient",
    "6215": "Healthcare - Labs",
    "6216": "Healthcare - Home Health",
    "6219": "Healthcare - Other Ambulatory",
    "6221": "Healthcare - Hospitals (General)",
    "6222": "Healthcare - Hospitals (Psych/Substance)",
    "6223": "Healthcare - Hospitals (Specialty)",
    "6231": "Healthcare - Nursing Facilities",
    "6232": "Healthcare - Residential Care",
    "6233": "Healthcare - Continuing Care",
    # Construction / Trades
    "2361": "Construction - Residential",
    "2362": "Construction - Commercial",
    "2371": "Construction - Utility Systems",
    "2372": "Construction - Land Subdivision",
    "2373": "Construction - Highway/Street",
    "2379": "Construction - Other Heavy",
    "2381": "Construction - Foundation/Structural",
    "2382": "Construction - HVAC/Plumbing/Electrical",
    "2383": "Construction - Finishing",
    "2389": "Construction - Other Specialty",
    # Manufacturing
    "3111": "Manufacturing - Food (Animal)",
    "3112": "Manufacturing - Food (Grain/Oil)",
    "3113": "Manufacturing - Food (Sugar/Confection)",
    "3114": "Manufacturing - Food (Fruit/Vegetable)",
    "3115": "Manufacturing - Food (Dairy)",
    "3116": "Manufacturing - Food (Meat)",
    "3118": "Manufacturing - Food (Bakeries)",
    "3119": "Manufacturing - Food (Other)",
    "3121": "Manufacturing - Beverages",
    "3241": "Manufacturing - Petroleum/Coal",
    "3251": "Manufacturing - Basic Chemicals",
    "3254": "Manufacturing - Pharmaceuticals",
    "3259": "Manufacturing - Other Chemicals",
    "3261": "Manufacturing - Plastics",
    "3271": "Manufacturing - Clay/Glass",
    "3311": "Manufacturing - Iron/Steel",
    "3312": "Manufacturing - Steel Products",
    "3314": "Manufacturing - Nonferrous Metals",
    "3315": "Manufacturing - Foundries",
    "3321": "Manufacturing - Forging/Stamping",
    "3322": "Manufacturing - Cutlery/Handtools",
    "3323": "Manufacturing - Architectural Metals",
    "3324": "Manufacturing - Boilers/Tanks",
    "3325": "Manufacturing - Hardware",
    "3326": "Manufacturing - Springs/Wire",
    "3327": "Manufacturing - Machine Shops",
    "3328": "Manufacturing - Coating/Engraving",
    "3329": "Manufacturing - Other Fabricated Metals",
    "3331": "Manufacturing - Ag/Construction Equipment",
    "3332": "Manufacturing - Industrial Machinery",
    "3333": "Manufacturing - Commercial Equipment",
    "3334": "Manufacturing - HVAC Equipment",
    "3335": "Manufacturing - Metalworking Machinery",
    "3336": "Manufacturing - Engines/Turbines",
    "3339": "Manufacturing - Other Machinery",
    "3341": "Manufacturing - Computers",
    "3342": "Manufacturing - Communications Equipment",
    "3343": "Manufacturing - Audio/Video Equipment",
    "3344": "Manufacturing - Semiconductors",
    "3345": "Manufacturing - Instruments",
    "3346": "Manufacturing - Magnetic Media",
    "3351": "Manufacturing - Electrical Equipment",
    "3353": "Manufacturing - Electrical Transmission",
    "3359": "Manufacturing - Other Electrical",
    "3361": "Manufacturing - Motor Vehicles",
    "3362": "Manufacturing - Motor Vehicle Bodies",
    "3363": "Manufacturing - Motor Vehicle Parts",
    "3364": "Manufacturing - Aerospace",
    "3365": "Manufacturing - Railroad",
    "3366": "Manufacturing - Ship/Boat",
    "3369": "Manufacturing - Other Transportation",
    # Automotive
    "4411": "Automotive - Dealers",
    "4412": "Automotive - Other Dealers",
    "8111": "Automotive - Repair/Maintenance",
    # IT / Media
    "5112": "IT - Software Publishing",
    "5171": "IT - Telecommunications (Wired)",
    "5172": "IT - Telecommunications (Wireless)",
    "5174": "IT - Satellite",
    "5182": "IT - Data Processing/Hosting",
    "5191": "IT - Other Information Services",
    "5415": "IT - Computer Systems Design",
    "5112": "Media - Software Publishing",
    "5121": "Media - Motion Picture/Video",
    "5122": "Media - Sound Recording",
    "5151": "Media - Radio/TV Broadcasting",
    # Food Service / Hospitality
    "7211": "Hospitality - Hotels/Motels",
    "7212": "Hospitality - RV Parks/Camps",
    "7221": "Food Service - Restaurants (Full)",
    "7222": "Food Service - Restaurants (Limited)",
    "7223": "Food Service - Special Food Services",
    "7224": "Food Service - Bars",
    # Personal Care
    "8121": "Personal Care - Personal Services",
    "8122": "Personal Care - Laundry/Cleaning",
    # Public Safety (government)
    "9221": "Public Safety - Courts",
    "9222": "Public Safety - Police/Fire",
    "9223": "Public Safety - Corrections",
    # Education
    "6111": "Education - Elementary/Secondary",
    "6112": "Education - Junior Colleges",
    "6113": "Education - Colleges/Universities",
    "6114": "Education - Business Schools/Training",
    "6115": "Education - Technical Schools",
    "6116": "Education - Other Schools",
    "6117": "Education - Support Services",
    # Agriculture
    "1111": "Agriculture - Crop Production (Oilseed/Grain)",
    "1112": "Agriculture - Crop Production (Vegetable)",
    "1113": "Agriculture - Crop Production (Fruit/Tree)",
    "1114": "Agriculture - Crop Production (Greenhouse)",
    "1119": "Agriculture - Crop Production (Other)",
    "1121": "Agriculture - Cattle",
    "1122": "Agriculture - Hog/Pig",
    "1123": "Agriculture - Poultry/Egg",
    "1129": "Agriculture - Other Animals",
    "1131": "Agriculture - Timber",
    "1132": "Agriculture - Forest Nurseries",
    "1141": "Agriculture - Fishing",
    "1142": "Agriculture - Aquaculture",
    "1151": "Agriculture - Crop Support",
    "1152": "Agriculture - Animal Support",
    "1153": "Agriculture - Forestry Support",
}


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


def _parse_employer_rows(html: str) -> list[dict]:
    """Parse employer table rows from empResults page."""
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
    return employers


def _extract_form_state(html: str) -> dict:
    """Extract ASP.NET form state for POST requests."""
    state = {}
    for field in ("__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"):
        match = re.search(rf'{field}.*?value="([^"]+)"', html)
        if match:
            state[field] = match.group(1)
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
        time.sleep(0.3)

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
    naics_codes: list[str],
    min_size: str = "E",
    max_pages_per_code: int = 10,
) -> list[dict]:
    """Search multiple NAICS 4-digit codes in a county.

    Args:
        county_name: California county name (e.g., "Los Angeles")
        naics_codes: List of NAICS 4-digit codes to search
        min_size: Minimum size code. Default "E" = 50+ employees.
        max_pages_per_code: Max pages to paginate per NAICS code.

    Returns: deduplicated list of employer dicts.
    """
    code = COUNTY_CODES.get(county_name)
    if not code:
        logger.error(f"  Unknown county: {county_name}")
        return []

    geog = f"0604{code}"
    all_employers: list[dict] = []
    seen_keys: set[tuple] = set()

    for naics4 in naics_codes:
        naics_sect = naics4[:2]
        label = CTE_NAICS_CODES.get(naics4, f"NAICS {naics4}")
        logger.info(f"  Searching {county_name} — {label} (NAICS {naics4}, size {min_size}+)")

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

        logger.info(f"    Found {len(results)} employers ({len(all_employers)} total unique)")
        time.sleep(0.5)

    return all_employers


def search_metro(
    metro: str,
    naics_codes: list[str] | None = None,
    min_size: str = "E",
) -> list[dict]:
    """Search all counties in a metro area for CTE-relevant employers.

    If naics_codes is None, uses all CTE_NAICS_CODES.
    """
    counties = METRO_COUNTIES.get(metro, [])
    if not counties:
        logger.warning(f"No county mapping for metro: {metro}")
        return []

    if naics_codes is None:
        naics_codes = list(CTE_NAICS_CODES.keys())

    logger.info(f"Searching {metro} ({len(counties)} counties, {len(naics_codes)} NAICS codes)")

    all_employers: list[dict] = []
    seen_keys: set[tuple] = set()

    for county_name in counties:
        results = search_naics_codes(county_name, naics_codes, min_size)
        for emp in results:
            key = (emp["name"].lower(), emp["city"].lower())
            if key not in seen_keys:
                seen_keys.add(key)
                all_employers.append(emp)

    logger.info(f"Total unique employers across {metro}: {len(all_employers)}")

    # Cache
    CACHE_DIR.mkdir(exist_ok=True)
    cache_key = metro.lower().replace(" ", "_").replace("-", "_").replace(",", "")
    cache_path = CACHE_DIR / f"edd_deep_{cache_key}.json"
    with open(cache_path, "w") as f:
        json.dump(all_employers, f, indent=2)
    logger.info(f"Cached to {cache_path.name}")

    return all_employers


def load_cached(metro: str, deep: bool = False) -> list[dict] | None:
    """Load cached EDD employer data for a metro."""
    prefix = "edd_deep_" if deep else "edd_"
    cache_key = metro.lower().replace(" ", "_").replace("-", "_").replace(",", "")
    cache_path = CACHE_DIR / f"{prefix}{cache_key}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        logger.info(f"  Loaded {len(data)} employers from cache ({cache_path.name})")
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
