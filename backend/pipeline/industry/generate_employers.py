"""
Generate college-specific employer lists via data-driven demand profiling.

Pipeline:
  1. Crosswalk demand profile (TOP→CIP→SOC + COE demand projections)
  2. Scrape EDD major employers for the college's metro
  3. Map employers to demand-profile occupations via NAICS→SOC
  4. Score and select top 30-50 employers
  5. Merge into employers.json

Usage:
    python -m pipeline.industry.generate_employers --college lacity
    python -m pipeline.industry.generate_employers --all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

INDUSTRY_DIR = Path(__file__).parent
EMPLOYERS_PATH = INDUSTRY_DIR / "employers.json"
OCCUPATIONS_PATH = INDUSTRY_DIR / "occupations.json"
CACHE_DIR = Path(__file__).parent.parent / "cache"

MAX_RETRIES = 5
CONCURRENCY = 5

# ── NAICS sector → likely SOC major groups ────────────────────────────────
# Broad mapping from 2-3 digit NAICS to SOC major groups.
# Used to pre-filter which demand-profile occupations an employer might hire for.
NAICS_TO_SOC_GROUPS: dict[str, list[str]] = {
    # Agriculture, Forestry, Fishing
    "11": ["45", "19"],
    # Mining, Utilities, Construction
    "21": ["47", "51", "53"], "22": ["47", "49", "51"], "23": ["47", "49", "11"],
    # Manufacturing
    "31": ["51", "17", "49"], "32": ["51", "17", "19"], "33": ["51", "17", "15"],
    # Wholesale & Retail Trade
    "42": ["41", "43", "53"], "44": ["41", "43", "35"], "45": ["41", "43"],
    # Transportation & Warehousing
    "48": ["53", "43", "49"], "49": ["53", "43"],
    # Information
    "51": ["15", "27", "13"],
    # Finance & Insurance
    "52": ["13", "43", "11"],
    # Real Estate
    "53": ["41", "43", "37"],
    # Professional, Scientific, Technical Services
    "54": ["15", "17", "13", "19", "23", "27"],
    # Management of Companies
    "55": ["11", "13"],
    # Administrative & Support Services
    "56": ["43", "37", "33"],
    # Educational Services
    "61": ["25", "21", "11"],
    # Health Care & Social Assistance
    "62": ["29", "31", "21", "11"],
    # Arts, Entertainment, Recreation
    "71": ["27", "39", "35"],
    # Accommodation & Food Services
    "72": ["35", "11", "39"],
    # Other Services
    "81": ["49", "39", "43"],
    # Public Administration
    "92": ["33", "21", "11", "23"],
}


def _naics_to_soc_groups(naics_code: str) -> list[str]:
    """Map NAICS code to likely SOC major groups."""
    if not naics_code:
        return []
    # Try 3-digit, then 2-digit
    for length in (3, 2):
        prefix = naics_code[:length]
        if prefix in NAICS_TO_SOC_GROUPS:
            return NAICS_TO_SOC_GROUPS[prefix]
    return []


# ── Size class scoring ────────────────────────────────────────────────────

SIZE_CLASS_SCORES = {
    "10,000+ Employees": 5,
    "5,000-9,999 Employees": 4,
    "1,000-4,999 Employees": 3,
    "500-999 Employees": 2,
    "250-499 Employees": 1,
    "100-249 Employees": 1,
}


def _size_score(size_class: str) -> int:
    """Convert size class string to numeric score."""
    for key, score in SIZE_CLASS_SCORES.items():
        if key in (size_class or ""):
            return score
    return 0


# ── Employer name normalization ───────────────────────────────────────────

_STRIP_SUFFIXES = re.compile(
    r"\s*\b(Inc\.?|LLC|Corp\.?|Co\.?|Ltd\.?|LP|Medical Center|Health System|"
    r"Medical Ctr|Health Svc|Hosp|Foundation)\s*$",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    """Normalize employer name for dedup matching."""
    name = _STRIP_SUFFIXES.sub("", name).strip()
    return name.lower()


# ── Main pipeline functions ───────────────────────────────────────────────

def _map_employers_to_occupations(
    edd_employers: list[dict],
    demand_profile: list[dict],
) -> list[dict]:
    """Map EDD employers to demand-profile occupations via NAICS→SOC.

    For each employer, find demand-profile occupations whose SOC major group
    matches the employer's NAICS sector. Returns employers enriched with
    'matched_occupations' field.
    """
    # Index demand profile by SOC major group
    soc_by_group: dict[str, list[dict]] = {}
    for occ in demand_profile:
        group = occ["soc_code"].split("-")[0]
        soc_by_group.setdefault(group, []).append(occ)

    enriched = []
    for emp in edd_employers:
        naics = emp.get("naics_code", "")
        soc_groups = _naics_to_soc_groups(naics)

        matched = []
        for group in soc_groups:
            matched.extend(soc_by_group.get(group, []))

        # Deduplicate and sort by composite score
        seen = set()
        unique_matched = []
        for occ in sorted(matched, key=lambda o: -o["composite_score"]):
            if occ["soc_code"] not in seen:
                unique_matched.append(occ)
                seen.add(occ["soc_code"])

        emp["matched_occupations"] = unique_matched[:10]  # top 10 per employer
        emp["demand_overlap"] = len(unique_matched)
        enriched.append(emp)

    return enriched


def _score_employers(employers: list[dict]) -> list[dict]:
    """Score employers by demand overlap, size, and wage quality."""
    for emp in employers:
        matched = emp.get("matched_occupations", [])
        if not matched:
            emp["employer_score"] = 0
            continue

        demand_score = emp["demand_overlap"]
        size_score = _size_score(emp.get("size_class", ""))
        avg_wage = sum(o["median_wage"] for o in matched) / len(matched)
        avg_openings = sum(o["annual_openings"] for o in matched) / len(matched)

        # Composite: demand breadth × size × wage quality × openings volume
        emp["employer_score"] = demand_score * (1 + size_score) * (avg_wage / 100000) * (avg_openings / 1000)
        emp["avg_wage"] = round(avg_wage)
        emp["avg_openings"] = round(avg_openings)

    employers.sort(key=lambda e: -e.get("employer_score", 0))
    return employers


def _select_employers(
    scored_employers: list[dict],
    target_count: int = 40,
    max_per_sector: int = 8,
) -> list[dict]:
    """Select top employers with sector diversity."""
    # Assign sector from industry or NAICS
    for emp in scored_employers:
        naics = emp.get("naics_code", "")[:2]
        emp["sector"] = _naics_sector(naics, emp.get("industry", ""))

    selected = []
    sector_counts: dict[str, int] = {}

    for emp in scored_employers:
        if len(selected) >= target_count:
            break
        sector = emp["sector"]
        if sector_counts.get(sector, 0) >= max_per_sector:
            continue
        if emp.get("employer_score", 0) <= 0:
            continue
        selected.append(emp)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return selected


def _naics_sector(naics_2: str, industry: str) -> str:
    """Map NAICS 2-digit code to a readable sector name."""
    sectors = {
        "11": "Agriculture", "21": "Mining & Extraction", "22": "Utilities",
        "23": "Construction", "31": "Manufacturing", "32": "Manufacturing",
        "33": "Manufacturing", "42": "Wholesale Trade", "44": "Retail",
        "45": "Retail", "48": "Transportation", "49": "Transportation",
        "51": "Information & Media", "52": "Finance & Insurance",
        "53": "Real Estate", "54": "Professional Services",
        "55": "Management", "56": "Administrative Services",
        "61": "Education", "62": "Healthcare",
        "71": "Arts & Entertainment", "72": "Hospitality",
        "81": "Other Services", "92": "Government",
    }
    return sectors.get(naics_2, industry or "Other")


def _format_for_employers_json(
    selected: list[dict],
    metro: str,
) -> list[dict]:
    """Convert selected EDD employers to employers.json schema."""
    formatted = []
    for emp in selected:
        soc_codes = [o["soc_code"] for o in emp.get("matched_occupations", [])]
        formatted.append({
            "name": emp["name"],
            "sector": emp["sector"],
            "description": f"{emp['name']} in {emp['city']}, {emp['county']} County. Industry: {emp['industry']}.",
            "regions": [metro],
            "occupations": soc_codes,
        })
    return formatted


def _merge_employers(
    new_employers: list[dict],
    existing_employers: list[dict],
) -> list[dict]:
    """Merge new employers into existing list, deduplicating by name."""
    existing_index: dict[str, dict] = {}
    for emp in existing_employers:
        key = _normalize_name(emp["name"])
        existing_index[key] = emp

    added = 0
    merged = 0
    for emp in new_employers:
        key = _normalize_name(emp["name"])
        if key in existing_index:
            # Merge regions and occupations
            existing = existing_index[key]
            for r in emp["regions"]:
                if r not in existing["regions"]:
                    existing["regions"].append(r)
            existing_occs = set(existing.get("occupations", []))
            for soc in emp.get("occupations", []):
                if soc not in existing_occs:
                    existing["occupations"].append(soc)
                    existing_occs.add(soc)
            merged += 1
        else:
            existing_employers.append(emp)
            existing_index[key] = emp
            added += 1

    logger.info(f"  Merge: {added} new, {merged} updated")
    return existing_employers


# ── LLM-based description generation (optional) ──────────────────────────

async def _generate_descriptions(
    employers: list[dict],
) -> list[dict]:
    """Generate one-sentence descriptions for employers via Gemini Flash."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("  No GEMINI_API_KEY — skipping description generation")
        return employers

    client = genai.Client(api_key=api_key)

    # Only generate for employers without a real description
    needs_desc = [e for e in employers if "Industry:" in e.get("description", "")]
    if not needs_desc:
        return employers

    batch_size = 20
    batches = [needs_desc[i:i + batch_size] for i in range(0, len(needs_desc), batch_size)]

    for batch in batches:
        names = "\n".join(f"- {e['name']} ({e['sector']}, {e.get('regions', [''])[0]})" for e in batch)
        prompt = f"For each employer below, write a single sentence describing what they do and their local presence. Return JSON object mapping name to description.\n\n{names}"

        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    temperature=0.3,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            descriptions = json.loads(response.text)
            for emp in batch:
                if emp["name"] in descriptions:
                    emp["description"] = descriptions[emp["name"]]
        except Exception as e:
            logger.warning(f"  Description generation failed: {e}")

    return employers


# ── Orchestrator ──────────────────────────────────────────────────────────

def generate_for_college(college_key: str) -> list[dict]:
    """Run the full employer generation pipeline for one college.

    Returns list of new/updated employer dicts.
    """
    from pipeline.industry.crosswalks import build_demand_profile
    from pipeline.industry.edd_employers import scrape_metro, load_cached
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP, OEWS_METRO_TO_COE

    import warnings
    warnings.filterwarnings("ignore")  # suppress SSL warnings from EDD scraping

    logger.info(f"{'=' * 60}")
    logger.info(f"Generating employers for: {college_key}")

    # Resolve college → metro → COE region
    # Load college name from catalog_sources.json
    sources_path = Path(__file__).parent.parent / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)
    college_info = sources.get("colleges", {}).get(college_key)
    if not college_info:
        logger.error(f"  College {college_key} not found in catalog_sources.json")
        return []

    college_name = college_info["name"]
    metro = COLLEGE_REGION_MAP.get(college_name)
    if not metro:
        logger.error(f"  {college_name} not in COLLEGE_REGION_MAP")
        return []

    coe_region = OEWS_METRO_TO_COE.get(metro)
    if not coe_region:
        logger.warning(f"  No COE region for metro {metro}, using statewide")
        coe_region = "CA"

    logger.info(f"  College: {college_name}")
    logger.info(f"  Metro: {metro}")
    logger.info(f"  COE region: {coe_region}")

    # Stage 1: Demand profile
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    profile = build_demand_profile(college_key, occupations, coe_region)
    if not profile:
        logger.error(f"  Empty demand profile")
        return []
    logger.info(f"  Demand profile: {len(profile)} occupations scored")

    # Stage 2: Scrape EDD employers (or load from cache)
    edd = load_cached(metro)
    if edd is None:
        edd = scrape_metro(metro)
    if not edd:
        logger.error(f"  No EDD employers found for {metro}")
        return []

    # Stage 3: Map employers to demand-profile occupations
    mapped = _map_employers_to_occupations(edd, profile[:100])  # top 100 demand occupations
    logger.info(f"  Mapped {sum(1 for e in mapped if e['demand_overlap'] > 0)}/{len(mapped)} employers to demand profile")

    # Stage 4: Score and select
    scored = _score_employers(mapped)
    selected = _select_employers(scored)
    logger.info(f"  Selected {len(selected)} employers")

    # Log sector distribution
    sector_counts: dict[str, int] = {}
    for emp in selected:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # Stage 5: Format and merge
    formatted = _format_for_employers_json(selected, metro)

    with open(EMPLOYERS_PATH) as f:
        existing = json.load(f)

    merged = _merge_employers(formatted, existing)

    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    logger.info(f"  Total employers in JSON: {len(merged)}")

    return formatted


def generate_all() -> dict[str, int]:
    """Run pipeline for all colleges with enriched caches."""
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP

    # Find all colleges with enriched caches
    enriched_files = sorted(CACHE_DIR.glob("*_enriched.json"))
    college_keys = [p.stem.replace("_enriched", "") for p in enriched_files]

    # Load catalog sources to map keys to names
    sources_path = Path(__file__).parent.parent / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)

    results = {}
    for key in college_keys:
        info = sources.get("colleges", {}).get(key)
        if not info:
            logger.warning(f"Skipping {key}: not in catalog_sources.json")
            continue
        if info["name"] not in COLLEGE_REGION_MAP:
            logger.warning(f"Skipping {key}: {info['name']} not in COLLEGE_REGION_MAP")
            continue

        try:
            employers = generate_for_college(key)
            results[key] = len(employers)
        except Exception as e:
            logger.error(f"Failed for {key}: {e}")
            results[key] = -1

    logger.info(f"\n{'=' * 60}")
    logger.info(f"DONE: {sum(1 for v in results.values() if v > 0)} colleges processed")
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate college-specific employer lists")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--college", type=str, help="College key (e.g., lacity)")
    group.add_argument("--all", action="store_true", help="Process all colleges")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    if getattr(args, "all"):
        generate_all()
    else:
        generate_for_college(args.college)


if __name__ == "__main__":
    main()
