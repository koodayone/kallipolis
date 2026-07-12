"""
COE-grounded supply and demand lookups for SWP LMI context.

Supply data: supply_by_top.csv (COE-published 3-year avg completions by TOP6 × college × award level)
Demand data: occupational_demand_coe.csv (COE-published regional occupational projections by SOC)

Both files are published by the California Community Colleges Centers of Excellence.
"""
from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent


# ── COE publication vintage (source-derived) ────────────────────────────
# The qualifier triple (source · granularity · vintage) that grounds every
# figure needs the *temporal edition* of the COE data. That vintage is a
# file-level fact carried in the CSV column names ("2024 Jobs", "2020-2021"…)
# which the row loaders below discard. It is parsed here once and exported so
# consumers (e.g. the MCP provenance layer) can state it honestly rather than
# reconstruct it or, worse, omit it. No behavior change to the loaders.

def _read_header(filename: str) -> list[str]:
    with open(_DATA_DIR / filename, newline="", encoding="utf-8") as f:
        return [c.strip() for c in next(csv.reader(f))]


def _derive_demand_vintage() -> str:
    base = window = None
    for col in _read_header("occupational_demand_coe.csv"):
        m = re.match(r"(\d{4})\s+Jobs$", col)
        if m:
            base = m.group(1)
        m = re.search(r"(\d{4})\s*-\s*(\d{4})", col)
        if m and "Change" in col:
            window = f"{m.group(1)}–{m.group(2)}"
    if base and window:
        return f"COE occupational demand — {base} base-year employment, {window} projection"
    return "COE occupational demand — vintage unavailable"


def _derive_supply_vintage() -> str:
    years = [c for c in _read_header("supply_by_top.csv") if re.fullmatch(r"\d{4}-\d{4}", c)]
    if years:
        return f"COE projected completions — {len(years)}-yr avg, {years[0]}→{years[-1]}"
    return "COE projected completions — vintage unavailable"


COE_DEMAND_VINTAGE: str = _derive_demand_vintage()
COE_SUPPLY_VINTAGE: str = _derive_supply_vintage()


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

    # Los Angeles — supply CSV uses "LA" abbreviation and drops "City"
    # suffix on several names. Without these explicit entries, the
    # heuristic strip in _normalize_college produces names like "Los
    # Angeles Harbor" (vs CSV's "LA Harbor") and "Pasadena City" (vs
    # CSV's "Pasadena"), which fall through to zero supply hits and
    # silently drop these 9 colleges from every (college, SOC) supply
    # lookup.
    "East Los Angeles College": "East LA",
    "Long Beach City College": "Long Beach",
    "Los Angeles Harbor College": "LA Harbor",
    "Los Angeles Mission College": "LA Mission",
    "Los Angeles Pierce College": "LA Pierce",
    "Los Angeles Southwest College": "LA Swest",
    "Los Angeles Trade-Technical College": "LA Trade",
    "Pasadena City College": "Pasadena",
    "West Los Angeles College": "West LA",

    # Other colleges — the auto-strip heuristic produces a name that
    # doesn't match the supply CSV's shorter variant. Same root cause
    # as the LA block above.
    "Modesto Junior College": "Modesto",
    "Monterey Peninsula College": "Monterey",
    "Riverside City College": "Riverside",
    "San Bernardino Valley College": "San Bernardino",
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
