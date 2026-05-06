"""
COE-grounded supply and demand lookups for SWP LMI context.

Supply data: supply_by_top.csv (COE-published 3-year avg completions by TOP6 × college × award level)
Demand data: occupational_demand_coe.csv (COE-published regional occupational projections by SOC)

Both files are published by the California Community Colleges Centers of Excellence.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent

# ── College name normalization ──────────────────────────────────────────
# Supply CSV uses short names ("Foothill", "Deanza"); Neo4j uses full names
# ("Foothill College", "De Anza College"). This map covers known colleges.

_NEO4J_TO_SUPPLY: dict[str, str] = {
    # Bay Area
    "Foothill College": "Foothill",
    "De Anza College": "Deanza",
    "Mission College": "Mission",
    "Evergreen Valley College": "Evergreen Valley",
    "San Jose City College": "San Jose City",
    "West Valley College": "West Valley",
    "Gavilan College": "Gavilan",
    "Laney College": "Laney",
    "Merritt College": "Merritt",
    "College of Alameda": "Alameda",
    "Berkeley City College": "Berkeley City",
    "Chabot College": "Chabot Hayward",
    "Ohlone College": "Ohlone",
    "Las Positas College": "Las Positas",
    "Diablo Valley College": "Diablo Valley",
    "Los Medanos College": "Los Medanos",
    "Contra Costa College": "Contra Costa",
    "City College of San Francisco": "San Francisco",
    "Cañada College": "Canada",
    "College of San Mateo": "San Mateo",
    "Skyline College": "Skyline",
    "Santa Rosa Junior College": "Santa Rosa",
    "Napa Valley College": "Napa",
    "Solano Community College": "Solano",
    "Cabrillo College": "Cabrillo",
    "College of Marin": "Marin",
    # Los Angeles
    "Los Angeles City College": "LA City",
    "Los Angeles Valley College": "LA Valley",
    "Citrus College": "Citrus",
    "Compton College": "Compton",
    # San Diego / Imperial
    "Imperial Valley College": "Imperial",
    # Orange County
    "Coastline College": "Coastline",
    "Cypress College": "Cypress",
    "Golden West College": "Golden West",
    "Irvine Valley College": "Irvine",
    "Orange Coast College": "Orange Coast",
    # Sacramento
    "American River College": "American River",
    "Sacramento City College": "Sacramento City",
    # Central Valley
    "College of the Sequoias": "Sequoias",
    # Central / South Coast
    "Allan Hancock College": "Allan Hancock",
    "Santa Barbara City College": "Santa Barbara",
    # Far North / Rural
    "Mendocino College": "Mendocino",
    "Lassen College": "Lassen",
    "College of the Siskiyous": "Siskiyous",
    "Butte College": "Butte",
    "Lake Tahoe Community College": "Lake Tahoe",
}


def _normalize_college(college: str) -> str:
    """Map a Neo4j college name to the supply CSV short name."""
    if college in _NEO4J_TO_SUPPLY:
        return _NEO4J_TO_SUPPLY[college]
    # Heuristic fallback: strip common suffixes + periods.
    # Period stripping matters because catalog-side names sometimes
    # carry a period after abbreviated words ("Mt. San Antonio College")
    # while the MCF College column writes them without ("Mt San Antonio").
    # Without this, _normalize_college's index-vs-lookup symmetry breaks
    # for the affected colleges and Stage 2 aborts at 0% TOP6 coverage.
    stripped = (
        college
        .replace(" Community College", "")
        .replace(" College", "")
        .replace("College of the ", "")
        .replace("College of ", "")
        .replace(".", "")
        .strip()
    )
    # Collapse any double-spaces left behind by punctuation stripping.
    return " ".join(stripped.split())


# ── Supply index (TOP-based, per college) ───────────────────────────────

@lru_cache(maxsize=1)
def _load_supply_index() -> dict[tuple[str, str], list[dict]]:
    """
    Parse supply_by_top.csv into an index keyed by (top6, college_name_lower).

    Each value is a list of rows (one per award level) with supply data.
    """
    index: dict[tuple[str, str], list[dict]] = {}
    csv_path = _DATA_DIR / "supply_by_top.csv"

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            if len(row) < 7:
                continue

            top6_with_title = row[0].strip().strip('"')
            college = row[1].strip()
            award_level = row[2].strip()

            # Parse the TOP6 code from "050200 - Accounting"
            parts = top6_with_title.split(" - ", 1)
            if len(parts) < 2:
                continue
            top6 = parts[0].strip()
            top6_title = parts[1].strip()

            # Parse projected supply
            try:
                annual_projected = float(row[6]) if row[6].strip() else 0.0
            except ValueError:
                continue

            if annual_projected <= 0:
                continue

            # Normalize the CSV's college name through the same fallback the
            # lookup uses, so e.g. "Reedley College" in the CSV becomes the
            # short-name "reedley" the lookup will compose. Without this, the
            # 3 colleges whose CSV entry carries a "College" / "Community
            # College" suffix (Clovis, Norco, Reedley as of May 2026) silently
            # produce no supply data — the lookup keys to the stripped name
            # but the index keys to the suffixed name. Same class of bug as
            # the MCF index/lookup asymmetry fixed in commit 0135860.
            college_normalized = _normalize_college(college).lower()
            key = (top6, college_normalized)
            if key not in index:
                index[key] = []
            index[key].append({
                "top6": top6,
                "top6_title": top6_title,
                "award_level": award_level,
                "annual_projected_supply": annual_projected,
            })

    logger.info(f"Loaded supply index: {len(index)} (top6, college) keys")
    return index


# ── Demand index (SOC-based, per region) ────────────────────────────────

@lru_cache(maxsize=1)
def _load_demand_index() -> dict[tuple[str, str], dict]:
    """
    Parse occupational_demand_coe.csv into an index keyed by (soc_code, region_code).
    """
    index: dict[tuple[str, str], dict] = {}
    csv_path = _DATA_DIR / "occupational_demand_coe.csv"

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            if len(row) < 9:
                continue

            region = row[0].strip()
            soc = row[1].strip()
            title = row[2].strip()
            education = row[3].strip()

            try:
                jobs_2024 = int(row[4]) if row[4].strip() else None
            except ValueError:
                jobs_2024 = None

            try:
                growth_rate = float(row[5]) if row[5].strip() else None
            except ValueError:
                growth_rate = None

            try:
                annual_openings = int(row[6]) if row[6].strip() else None
            except ValueError:
                annual_openings = None

            try:
                median_hourly = float(row[7]) if row[7].strip() else None
            except ValueError:
                median_hourly = None

            try:
                median_annual = int(row[8]) if row[8].strip() else None
            except ValueError:
                median_annual = None

            index[(soc, region)] = {
                "soc_code": soc,
                "title": title,
                "education_level": education,
                "jobs_2024": jobs_2024,
                "growth_rate": growth_rate,
                "annual_openings": annual_openings,
                "median_hourly": median_hourly,
                "median_annual_earnings": median_annual,
            }

    logger.info(f"Loaded demand index: {len(index)} (soc, region) keys")
    return index


# ── Public API ──────────────────────────────────────────────────────────

def get_coe_supply(
    top6_codes: set[str],
    college: str,
) -> tuple[list[dict], float]:
    """
    Look up COE-published supply for a college given exact TOP6 codes.

    TOP6 codes come from MCF lookup (mcf_lookup.py), not prefix approximation.
    Returns (supply_estimates, total_supply) where each estimate has:
    top_code, top_title, award_level, annual_projected_supply.
    """
    supply_index = _load_supply_index()
    college_norm = _normalize_college(college).lower()

    estimates: list[dict] = []
    for top6 in sorted(top6_codes):
        rows = supply_index.get((top6, college_norm), [])
        for row in rows:
            estimates.append({
                "top_code": row["top6"],
                "top_title": row["top6_title"],
                "award_level": row["award_level"],
                "annual_projected_supply": row["annual_projected_supply"],
            })

    total = sum(e["annual_projected_supply"] for e in estimates)
    return estimates, total


def get_coe_demand(
    soc_codes: list[str],
    college: str,
) -> tuple[list[dict], int]:
    """
    Look up COE-published demand for occupations in the college's region.

    Returns (occupations, total_demand) where total_demand = sum of annual_openings.
    Falls back to statewide ("CA") data if regional entry is missing.
    """
    from ontology.regions import COLLEGE_COE_REGION

    demand_index = _load_demand_index()
    coe_region = COLLEGE_COE_REGION.get(college, "CA")

    occupations: list[dict] = []
    seen_soc: set[str] = set()

    for soc in soc_codes:
        if soc in seen_soc:
            continue
        seen_soc.add(soc)

        # Try regional first, fall back to statewide
        entry = demand_index.get((soc, coe_region)) or demand_index.get((soc, "CA"))
        if not entry:
            continue

        occupations.append({
            "soc_code": entry["soc_code"],
            "title": entry["title"],
            "annual_wage": entry["median_annual_earnings"],
            "employment": entry["jobs_2024"],
            "growth_rate": entry["growth_rate"],
            "annual_openings": entry["annual_openings"],
            "education_level": entry["education_level"],
            "region": coe_region,
        })

    total = sum(o["annual_openings"] or 0 for o in occupations)
    return occupations, total
