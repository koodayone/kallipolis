"""
Generate college-specific employer lists via data-driven demand profiling.

Pipeline:
  1. Crosswalk demand profile (TOP→CIP→SOC + COE demand projections)
  2. Deep-scrape EDD employers by CTE-relevant NAICS codes + size filter
  3. Map employers to demand-profile occupations via NAICS→SOC
  4. Score and select top employers per college
  5. Merge into employers.json

Usage:
    python -m pipeline.industry.generate_employers --college lacity
    python -m pipeline.industry.generate_employers --all
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

INDUSTRY_DIR = Path(__file__).parent
EMPLOYERS_PATH = INDUSTRY_DIR / "employers.json"
OCCUPATIONS_PATH = INDUSTRY_DIR / "occupations.json"
CACHE_DIR = Path(__file__).parent.parent / "cache"

# ── NAICS sector → likely SOC major groups ────────────────────────────────
# Broad mapping from NAICS 2-digit sector to SOC major groups.
# Used to connect EDD employers (who have NAICS codes) to demand-profile
# occupations (who have SOC codes).
NAICS_TO_SOC_GROUPS: dict[str, list[str]] = {
    "11": ["45", "19"],                          # Agriculture
    "21": ["47", "51", "53"],                    # Mining
    "22": ["47", "49", "51"],                    # Utilities
    "23": ["47", "49", "11", "17"],              # Construction
    "31": ["51", "17", "49"], "32": ["51", "17", "19"], "33": ["51", "17", "15"],  # Manufacturing
    "42": ["41", "43", "53"],                    # Wholesale Trade
    "44": ["41", "43", "35"], "45": ["41", "43"],  # Retail Trade
    "48": ["53", "43", "49"], "49": ["53", "43"],  # Transportation
    "51": ["15", "27", "13"],                    # Information
    "52": ["13", "43", "11"],                    # Finance
    "53": ["41", "43", "37"],                    # Real Estate
    "54": ["15", "17", "13", "19", "23", "27"],  # Professional Services
    "55": ["11", "13"],                          # Management of Companies
    "56": ["43", "37", "33"],                    # Administrative Services
    "61": ["25", "21", "11"],                    # Education
    "62": ["29", "31", "21", "11"],              # Healthcare
    "71": ["27", "39", "35"],                    # Arts/Entertainment
    "72": ["35", "11", "39"],                    # Accommodation/Food
    "81": ["49", "39", "43"],                    # Other Services
    "92": ["33", "21", "11", "23"],              # Government
}


def _naics_to_soc_groups(naics_code: str) -> list[str]:
    """Map a NAICS code to likely SOC major groups."""
    if not naics_code:
        return []
    for length in (3, 2):
        prefix = naics_code[:length]
        if prefix in NAICS_TO_SOC_GROUPS:
            return NAICS_TO_SOC_GROUPS[prefix]
    return []


# ── Size class scoring ────────────────────────────────────────────────────

SIZE_SCORES = {
    "1,000-4,999 employees": 4,
    "500-999 employees": 3,
    "250-499 employees": 2,
    "100-249 employees": 1,
    "50-99 employees": 0.5,
}


def _size_score(size_class: str) -> float:
    for key, score in SIZE_SCORES.items():
        if key in (size_class or ""):
            return score
    return 0


# ── Name normalization ────────────────────────────────────────────────────

_STRIP = re.compile(
    r"\s*\b(Inc\.?|LLC|Corp\.?|Co\.?|Ltd\.?|LP|Medical Center|Health System|"
    r"Medical Ctr|Health Svc|Hosp|Foundation)\s*$",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    return _STRIP.sub("", name).strip().lower()


# ── NAICS to readable sector ─────────────────────────────────────────────

_NAICS_SECTORS = {
    "11": "Agriculture", "21": "Mining", "22": "Utilities",
    "23": "Construction", "31": "Manufacturing", "32": "Manufacturing",
    "33": "Manufacturing", "42": "Wholesale", "44": "Retail",
    "45": "Retail", "48": "Transportation", "49": "Transportation",
    "51": "Information & Media", "52": "Finance",
    "53": "Real Estate", "54": "Professional Services",
    "55": "Management", "56": "Administrative Services",
    "61": "Education", "62": "Healthcare",
    "71": "Arts & Entertainment", "72": "Hospitality & Food Service",
    "81": "Other Services", "92": "Government",
}


def _naics_sector(naics4: str, industry: str = "") -> str:
    return _NAICS_SECTORS.get((naics4 or "")[:2], industry or "Other")


# ── Core pipeline functions ───────────────────────────────────────────────

def _map_employers_to_occupations(
    edd_employers: list[dict],
    demand_profile: list[dict],
) -> list[dict]:
    """Map EDD employers to demand-profile occupations via NAICS→SOC."""
    # Index demand profile by SOC major group
    soc_by_group: dict[str, list[dict]] = defaultdict(list)
    for occ in demand_profile:
        group = occ["soc_code"].split("-")[0]
        soc_by_group[group].append(occ)

    for emp in edd_employers:
        naics = emp.get("naics4", emp.get("naics_code", ""))
        soc_groups = _naics_to_soc_groups(naics)

        matched = []
        for group in soc_groups:
            matched.extend(soc_by_group.get(group, []))

        # Deduplicate and take top by score
        seen = set()
        unique = []
        for occ in sorted(matched, key=lambda o: -o["composite_score"]):
            if occ["soc_code"] not in seen:
                unique.append(occ)
                seen.add(occ["soc_code"])

        emp["matched_occupations"] = unique[:10]
        emp["demand_overlap"] = len(unique)

    return edd_employers


def _score_employers(employers: list[dict]) -> list[dict]:
    """Score employers by demand overlap, size, and wage quality."""
    for emp in employers:
        matched = emp.get("matched_occupations", [])
        if not matched:
            emp["employer_score"] = 0
            continue

        size = _size_score(emp.get("size_class", ""))
        avg_wage = sum(o["median_wage"] for o in matched) / len(matched)
        avg_openings = sum(o["annual_openings"] for o in matched) / len(matched)

        # Composite: demand breadth × (1 + size) × wage × openings
        emp["employer_score"] = emp["demand_overlap"] * (1 + size) * (avg_wage / 100000) * (avg_openings / 1000)
        emp["avg_wage"] = round(avg_wage)
        emp["avg_openings"] = round(avg_openings)

    employers.sort(key=lambda e: -e.get("employer_score", 0))
    return employers


def _select_employers(
    scored: list[dict],
    target: int = 50,
    max_per_sector: int = 10,
    min_per_sector: int = 2,
) -> list[dict]:
    """Select top employers with sector diversity.

    Ensures every CTE sector with available employers gets at least
    min_per_sector representatives before filling remaining slots by score.
    """
    for emp in scored:
        emp["sector"] = _naics_sector(
            emp.get("naics4", emp.get("naics_code", "")),
            emp.get("industry", ""),
        )

    # Group scored employers by sector
    by_sector: dict[str, list[dict]] = defaultdict(list)
    for emp in scored:
        if emp.get("employer_score", 0) > 0:
            by_sector[emp["sector"]].append(emp)

    selected = []
    sector_counts: dict[str, int] = {}
    selected_keys: set[str] = set()

    # Phase 1: Guarantee minimum representation per sector
    for sector, emps in by_sector.items():
        for emp in emps[:min_per_sector]:
            key = emp["name"].lower()
            if key not in selected_keys and len(selected) < target:
                selected.append(emp)
                selected_keys.add(key)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Phase 2: Fill remaining slots by score, respecting max per sector
    for emp in scored:
        if len(selected) >= target:
            break
        if emp.get("employer_score", 0) <= 0:
            continue
        key = emp["name"].lower()
        if key in selected_keys:
            continue
        sector = emp["sector"]
        if sector_counts.get(sector, 0) >= max_per_sector:
            continue
        selected.append(emp)
        selected_keys.add(key)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return selected


def _format_for_json(selected: list[dict], metro: str) -> list[dict]:
    """Convert selected employers to employers.json schema."""
    formatted = []
    for emp in selected:
        soc_codes = [o["soc_code"] for o in emp.get("matched_occupations", [])]
        industry = emp.get("industry", emp.get("naics_label", ""))
        city = emp.get("city", "")
        county = emp.get("county", "")
        size = emp.get("size_class", "")

        desc_parts = [emp["name"]]
        if city:
            desc_parts.append(f"in {city}")
        if county:
            desc_parts.append(f"({county} County)")
        desc = ". ".join(filter(None, [
            ", ".join(desc_parts),
            industry,
            size,
        ])) + "."

        formatted.append({
            "name": emp["name"],
            "sector": emp["sector"],
            "description": desc,
            "regions": [metro],
            "occupations": soc_codes,
        })
    return formatted


def _merge_employers(
    new_employers: list[dict],
    existing_employers: list[dict],
) -> tuple[list[dict], int, int]:
    """Merge new employers into existing, dedup by normalized name.

    Returns: (merged_list, added_count, updated_count)
    """
    index: dict[str, dict] = {}
    for emp in existing_employers:
        index[_normalize_name(emp["name"])] = emp

    added = 0
    updated = 0
    for emp in new_employers:
        key = _normalize_name(emp["name"])
        if key in index:
            existing = index[key]
            for r in emp["regions"]:
                if r not in existing["regions"]:
                    existing["regions"].append(r)
            existing_occs = set(existing.get("occupations", []))
            for soc in emp.get("occupations", []):
                if soc not in existing_occs:
                    existing["occupations"].append(soc)
                    existing_occs.add(soc)
            updated += 1
        else:
            existing_employers.append(emp)
            index[key] = emp
            added += 1

    return existing_employers, added, updated


# ── Orchestrator ──────────────────────────────────────────────────────────

def generate_for_college(
    college_key: str,
    target_employers: int = 50,
    scrape: bool = True,
) -> list[dict]:
    """Run the full employer generation pipeline for one college."""
    from pipeline.industry.crosswalks import build_demand_profile
    from pipeline.industry.edd_employers import search_naics_codes, load_cached, METRO_COUNTIES
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP, OEWS_METRO_TO_COE

    import warnings
    warnings.filterwarnings("ignore")

    logger.info(f"{'=' * 60}")
    logger.info(f"Generating employers for: {college_key}")

    # ── Resolve college → metro → COE region ─────────────────────────
    sources_path = Path(__file__).parent.parent / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)
    college_info = sources.get("colleges", {}).get(college_key)
    if not college_info:
        logger.error(f"  College {college_key} not in catalog_sources.json")
        return []

    college_name = college_info["name"]
    metro = COLLEGE_REGION_MAP.get(college_name)
    if not metro:
        logger.error(f"  {college_name} not in COLLEGE_REGION_MAP")
        return []

    coe_region = OEWS_METRO_TO_COE.get(metro, "CA")

    logger.info(f"  College: {college_name}")
    logger.info(f"  Metro: {metro}")
    logger.info(f"  COE region: {coe_region}")

    # ── Stage 1: Demand profile via crosswalks ────────────────────────
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    profile = build_demand_profile(college_key, occupations, coe_region)
    if not profile:
        logger.error(f"  Empty demand profile")
        return []
    logger.info(f"  Demand profile: {len(profile)} occupations")
    logger.info(f"  Top 5: {', '.join(o['title'][:40] for o in profile[:5])}")

    # ── Stage 2: Get EDD employers ────────────────────────────────────
    # Try deep cache first, then scrape
    edd_cache_key = metro.lower().replace(" ", "_").replace("-", "_").replace(",", "")
    deep_cache = INDUSTRY_DIR / "cache" / f"edd_deep_{edd_cache_key}.json"

    if deep_cache.exists() and not scrape:
        with open(deep_cache) as f:
            edd_employers = json.load(f)
        logger.info(f"  Loaded {len(edd_employers)} employers from deep cache")
    else:
        # Deep search: all CTE NAICS codes, 250+ employees, per county
        counties = METRO_COUNTIES.get(metro, [])
        if not counties:
            logger.error(f"  No counties mapped for metro: {metro}")
            return []

        edd_employers = []
        seen = set()
        for county in counties:
            results = search_naics_codes(county, min_size="G")
            for emp in results:
                key = (emp["name"].lower(), emp.get("city", "").lower())
                if key not in seen:
                    seen.add(key)
                    edd_employers.append(emp)

        # Cache the deep results
        deep_cache.parent.mkdir(exist_ok=True)
        with open(deep_cache, "w") as f:
            json.dump(edd_employers, f, indent=2)
        logger.info(f"  Scraped {len(edd_employers)} employers (cached to {deep_cache.name})")

    if not edd_employers:
        logger.error(f"  No EDD employers found")
        return []

    # ── Stage 3: Map to demand-profile occupations ────────────────────
    mapped = _map_employers_to_occupations(edd_employers, profile[:100])
    with_overlap = sum(1 for e in mapped if e["demand_overlap"] > 0)
    logger.info(f"  Mapped {with_overlap}/{len(mapped)} employers to demand profile")

    # ── Stage 4: Score and select ─────────────────────────────────────
    scored = _score_employers(mapped)
    selected = _select_employers(scored, target=target_employers)
    logger.info(f"  Selected {len(selected)} employers")

    # Sector distribution
    sector_counts: dict[str, int] = {}
    for emp in selected:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # ── Stage 5: Format, merge, save ──────────────────────────────────
    formatted = _format_for_json(selected, metro)

    with open(EMPLOYERS_PATH) as f:
        existing = json.load(f)

    merged, added, updated = _merge_employers(formatted, existing)

    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    logger.info(f"  Merge: {added} new, {updated} updated. Total: {len(merged)}")

    return formatted


def generate_all(scrape: bool = True) -> dict[str, int]:
    """Run pipeline for all colleges with enriched caches."""
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP

    sources_path = Path(__file__).parent.parent / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)

    enriched_files = sorted(CACHE_DIR.glob("*_enriched.json"))
    college_keys = [p.stem.replace("_enriched", "") for p in enriched_files]

    # Deduplicate by metro — don't re-scrape the same metro for each college
    metro_done: set[str] = set()
    results = {}

    for key in college_keys:
        info = sources.get("colleges", {}).get(key)
        if not info:
            continue
        if info["name"] not in COLLEGE_REGION_MAP:
            logger.warning(f"Skipping {key}: not in COLLEGE_REGION_MAP")
            continue

        metro = COLLEGE_REGION_MAP[info["name"]]
        # After first college in a metro, use cache instead of re-scraping
        should_scrape = scrape and metro not in metro_done
        metro_done.add(metro)

        try:
            employers = generate_for_college(key, scrape=should_scrape)
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
    group.add_argument("--college", type=str)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--no-scrape", action="store_true",
                        help="Use cached EDD data only, don't scrape")
    parser.add_argument("--target", type=int, default=50,
                        help="Target number of employers per college (default: 50)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    if getattr(args, "all"):
        generate_all(scrape=not args.no_scrape)
    else:
        generate_for_college(args.college, target_employers=args.target, scrape=not args.no_scrape)


if __name__ == "__main__":
    main()
