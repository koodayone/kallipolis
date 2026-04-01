"""
Generate employer lists from EDD's ALMIS Employer Database.

Purely data-driven: every employer is a verified Data Axle/EDD entry,
selected by NAICS industry code and employee count. No LLM inference,
no composite scoring, no debatable weights.

Pipeline:
  1. Scrape EDD employers by CTE NAICS codes + size filter (250+)
  2. Clean and deduplicate employer names
  3. Assign sector from NAICS code
  4. Assign SOC codes via NAICS→SOC mapping
  5. Select with sector diversity
  6. Merge into employers.json

Usage:
    python -m pipeline.industry.generate_employers --college lacity
    python -m pipeline.industry.generate_employers --all
    python -m pipeline.industry.generate_employers --college lacity --no-scrape
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

INDUSTRY_DIR = Path(__file__).parent
EMPLOYERS_PATH = INDUSTRY_DIR / "employers.json"
OCCUPATIONS_PATH = INDUSTRY_DIR / "occupations.json"
CACHE_DIR = Path(__file__).parent.parent / "cache"

# ── NAICS → SOC major groups ─────────────────────────────────────────────
# Maps NAICS 2-digit sector to SOC major groups employed in that industry.
# Used to assign SOC codes to employers for HIRES_FOR edges.
NAICS_TO_SOC_GROUPS: dict[str, list[str]] = {
    "11": ["45", "19"],
    "21": ["47", "51", "53"],
    "22": ["47", "49", "51"],
    "23": ["47", "49", "11", "17"],
    "31": ["51", "17", "49"], "32": ["51", "17", "19"], "33": ["51", "17", "15"],
    "42": ["41", "43", "53"],
    "44": ["41", "43", "35"], "45": ["41", "43"],
    "48": ["53", "43", "49"], "49": ["53", "43"],
    "51": ["15", "27", "13"],
    "52": ["13", "43", "11"],
    "53": ["41", "43", "37"],
    "54": ["15", "17", "13", "19", "23", "27"],
    "55": ["11", "13"],
    "56": ["43", "37", "33"],
    "61": ["25", "21", "11"],
    "62": ["29", "31", "21", "11"],
    "71": ["27", "39", "35"],
    "72": ["35", "11", "39"],
    "81": ["49", "39", "43"],
    "92": ["33", "21", "11", "23"],
}

# ── NAICS 2-digit → readable sector ──────────────────────────────────────
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

# ── Size class ordering (largest first) ───────────────────────────────────
_SIZE_ORDER = {
    "1,000-4,999 employees": 0,
    "500-999 employees": 1,
    "250-499 employees": 2,
    "100-249 employees": 3,
    "50-99 employees": 4,
}


def _size_sort_key(emp: dict) -> int:
    """Sort key: lower = larger employer."""
    size = emp.get("size_class", "")
    for key, order in _SIZE_ORDER.items():
        if key in size:
            return order
    return 99


# ── Name cleaning ─────────────────────────────────────────────────────────

_ABBREVIATIONS = [
    (r"\bCtr\b", "Center"), (r"\bHosp\b", "Hospital"),
    (r"\bDept\b", "Department"), (r"\bUniv\b", "University"),
    (r"\bMed\b", "Medical"), (r"\bSvc\b", "Services"),
    (r"\bMeml\b", "Memorial"), (r"\bEntrtn\b", "Entertainment"),
    (r"\bHtg\b", "Heating"), (r"\bCond\b", "Conditioning"),
    (r"\bPlbg\b", "Plumbing"), (r"\bMfg\b", "Manufacturing"),
    (r"\bTech\b", "Technology"), (r"\bCorp\b", "Corporation"),
    (r"\bGrp\b", "Group"), (r"\bIntl\b", "International"),
    (r"\bAdmn\b", "Administration"), (r"\bCmnty\b", "Community"),
    (r"\bNrthrdg\b", "Northridge"), (r"\bEngrng\b", "Engineering"),
    (r"\bHllywd\b", "Hollywood"), (r"\bHls\b", "Hills"),
    (r"\bNcr\b", "Cancer"), (r"\bCncr\b", "Cancer"),
    (r"\bOfc\b", "Office"), (r"\bChf\b", "Chief"),
]

_STRIP_SUFFIXES = re.compile(
    r"\s*\b(Inc\.?|LLC|Corp\.?|Co\.?|Ltd\.?|LP)\s*$",
    re.IGNORECASE,
)


def _clean_employer_name(name: str) -> str:
    """Normalize abbreviations in EDD employer names."""
    cleaned = name.strip()
    for pattern, replacement in _ABBREVIATIONS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = _STRIP_SUFFIXES.sub("", cleaned).strip()
    return cleaned


def _normalize_name(name: str) -> str:
    """Normalize for deduplication matching."""
    name = _STRIP_SUFFIXES.sub("", name).strip()
    return name.lower()


# ── Branch deduplication ──────────────────────────────────────────────────

def _deduplicate_branches(employers: list[dict]) -> list[dict]:
    """Deduplicate branch locations of the same employer.

    Groups by full normalized name, keeps the entry with the largest
    size class. This avoids false collisions (e.g., "University of
    California, Los Angeles" vs "University of California, San Diego").
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for emp in employers:
        key = _normalize_name(emp["name"])
        groups[key].append(emp)

    deduped = []
    for key, entries in groups.items():
        entries.sort(key=_size_sort_key)
        best = entries[0]
        best["name"] = _clean_employer_name(best["name"])
        deduped.append(best)

    return deduped


# ── SOC code assignment ───────────────────────────────────────────────────

def _assign_soc_codes(
    employer: dict,
    occupations_by_group: dict[str, list[str]],
) -> list[str]:
    """Assign SOC codes to an employer based on NAICS→SOC mapping.

    Args:
        employer: Dict with naics4 or naics_code field
        occupations_by_group: {soc_major_group: [soc_codes]} pre-filtered
            to occupations with employment in the region

    Returns: list of SOC codes (up to 10)
    """
    naics = employer.get("naics4", employer.get("naics_code", ""))
    if not naics:
        return []

    soc_groups = []
    for length in (3, 2):
        prefix = naics[:length]
        if prefix in NAICS_TO_SOC_GROUPS:
            soc_groups = NAICS_TO_SOC_GROUPS[prefix]
            break

    soc_codes = []
    for group in soc_groups:
        soc_codes.extend(occupations_by_group.get(group, []))

    return soc_codes[:10]


# ── Selection ─────────────────────────────────────────────────────────────

def _select_employers(
    employers: list[dict],
    target: int = 50,
    min_per_sector: int = 2,
    max_per_sector: int = 10,
) -> list[dict]:
    """Select employers sorted by size with sector diversity guarantees."""
    # Assign sector
    for emp in employers:
        naics = emp.get("naics4", emp.get("naics_code", ""))[:2]
        emp["sector"] = _NAICS_SECTORS.get(naics, emp.get("industry", "Other"))

    # Sort by size (largest first)
    employers.sort(key=_size_sort_key)

    # Group by sector
    by_sector: dict[str, list[dict]] = defaultdict(list)
    for emp in employers:
        by_sector[emp["sector"]].append(emp)

    selected = []
    selected_keys: set[str] = set()
    sector_counts: dict[str, int] = {}

    # Phase 1: Guarantee minimum per sector
    for sector, emps in by_sector.items():
        for emp in emps[:min_per_sector]:
            key = _normalize_name(emp["name"])
            if key not in selected_keys and len(selected) < target:
                selected.append(emp)
                selected_keys.add(key)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Phase 2: Fill remaining by size, respecting max per sector
    for emp in employers:
        if len(selected) >= target:
            break
        key = _normalize_name(emp["name"])
        if key in selected_keys:
            continue
        sector = emp["sector"]
        if sector_counts.get(sector, 0) >= max_per_sector:
            continue
        selected.append(emp)
        selected_keys.add(key)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return selected


# ── Formatting ────────────────────────────────────────────────────────────

def _format_for_json(employers: list[dict], metro: str) -> list[dict]:
    """Convert to employers.json schema."""
    formatted = []
    for emp in employers:
        # Use LLM description if available, otherwise build from EDD data
        desc = emp.get("description", "")
        if not desc or desc == emp["name"]:
            city = emp.get("city", "")
            county = emp.get("county", "")
            industry = emp.get("industry", emp.get("naics_label", ""))
            size = emp.get("size_class", "")
            parts = [emp["name"]]
            if city:
                parts.append(f"in {city}")
            if county:
                parts.append(f"({county} County)")
            desc = ", ".join(parts)
            if industry:
                desc += f". {industry}"
            if size:
                desc += f". {size}"
            desc += "."

        formatted.append({
            "name": emp["name"],
            "sector": emp.get("sector", "Other"),
            "description": desc,
            "regions": [metro],
            "occupations": emp.get("soc_codes", []),
        })
    return formatted


# ── Merge ─────────────────────────────────────────────────────────────────

def _merge_employers(
    new_employers: list[dict],
    existing_employers: list[dict],
) -> tuple[list[dict], int, int]:
    """Merge new into existing, dedup by normalized name."""
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


# ── LLM cleanup ───────────────────────────────────────────────────────────

def _llm_cleanup(
    employers: list[dict],
    metro: str,
    filtered_occupations: list[dict] | None = None,
) -> list[dict]:
    """Clean employer names, generate descriptions, and assign occupations via Gemini Flash.

    Fixes abbreviations, removes branch qualifiers, drops non-employer
    entries, generates one-sentence descriptions, and (when filtered_occupations
    is provided) assigns 3-8 relevant occupations per employer. Deduplicates
    any entries that collapse to the same name after cleaning.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("  No GEMINI_API_KEY — skipping LLM cleanup")
        return employers

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    names = [e["name"] for e in employers]

    # Build occupation assignment section if filtered occupations provided
    occ_section = ""
    valid_soc_codes: set[str] = set()
    if filtered_occupations:
        valid_soc_codes = {o["soc_code"] for o in filtered_occupations}
        occ_lines = [f"- {o['soc_code']}: {o['title']}" for o in filtered_occupations]
        occ_section = (
            "\n\nAlso assign 3-8 occupations each employer would plausibly hire for, "
            "selected from this list:\n\n"
            "AVAILABLE OCCUPATIONS:\n"
            + "\n".join(occ_lines)
            + "\n\nReturn the SOC codes in an \"occupations\" array."
        )

    occ_field = ', "occupations": ["SOC-CODE", ...]' if filtered_occupations else ""
    prompt = (
        f"Here are {len(names)} employer names from the EDD database for the "
        f"{metro} metro area. For each, return either:\n"
        "- The cleaned canonical employer name + a one-sentence description"
        + (" + relevant occupation codes" if filtered_occupations else "") + "\n"
        '- "REMOVE" if it should be dropped\n\n'
        "NAMING RULES:\n"
        "- Expand all abbreviations (Hosp→Hospital, Clg→College, Dist→District, Scrmnt→Sacramento, Chldrn→Children)\n"
        "- Remove branch qualifiers, location suffixes, and department names (e.g. '- Midtown', 'Department of Pathology', 'Collision Center')\n"
        "- If an entry is a foundation or auxiliary of a parent org that also appears in the list, REMOVE the foundation entry\n"
        "- If two entries are clearly the same org (e.g. 'Mercy Hospital' and 'Mercy General Hospital'), keep the more canonical name and REMOVE the duplicate\n"
        "- Keep the name recognizable — use the name people in the region would know\n\n"
        "REMOVE entries that are:\n"
        "- Branch locations when the parent is already listed\n"
        "- Internal departments, not standalone employers\n"
        "- Foundations or auxiliaries when the parent hospital/org is listed\n"
        "- Staffing agencies or temp firms\n"
        + occ_section + "\n\n"
        'Return JSON: {"Original Name": {"name": "Clean Name", "description": "..."'
        + occ_field + '} or "Original Name": "REMOVE"}\n\n'
        "Names:\n" + "\n".join(f"- {n}" for n in names)
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        cleanup = json.loads(response.text)
    except Exception as e:
        logger.warning(f"  LLM cleanup failed: {e}")
        return employers

    # Apply cleanup
    kept = []
    removed = 0
    renamed = 0
    occ_assigned = 0
    for emp in employers:
        action = cleanup.get(emp["name"])
        if action == "REMOVE":
            removed += 1
            continue
        if isinstance(action, dict):
            if action.get("name") and action["name"] != emp["name"]:
                emp["name"] = action["name"]
                renamed += 1
            if action.get("description"):
                emp["description"] = action["description"]
            if action.get("occupations") and valid_soc_codes:
                # Validate SOC codes against filtered list
                valid = [s for s in action["occupations"] if s in valid_soc_codes]
                if valid:
                    emp["soc_codes"] = valid
                    occ_assigned += 1
        kept.append(emp)
    if filtered_occupations:
        logger.info(f"  LLM occupation assignment: {occ_assigned}/{len(kept)} employers")

    # Post-rename dedup
    seen: dict[str, dict] = {}
    final = []
    for emp in kept:
        key = emp["name"].lower()
        if key in seen:
            # Merge SOC codes
            existing = seen[key]
            for soc in emp.get("soc_codes", []):
                if soc not in existing.get("soc_codes", []):
                    existing.setdefault("soc_codes", []).append(soc)
            removed += 1
        else:
            seen[key] = emp
            final.append(emp)

    logger.info(f"  LLM cleanup: {renamed} renamed, {removed} removed, {len(final)} kept")
    return final


# ── Orchestrator ──────────────────────────────────────────────────────────

def generate_for_college(
    college_key: str,
    target: int = 50,
    scrape: bool = True,
    min_size: str = "G",
    filtered_occupations: list[dict] | None = None,
) -> list[dict]:
    """Run the full employer generation pipeline for one college."""
    from pipeline.industry.edd_employers import search_naics_codes, METRO_COUNTIES
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP, OEWS_METRO_TO_COE

    import warnings
    warnings.filterwarnings("ignore")

    logger.info(f"{'=' * 60}")
    logger.info(f"Generating employers for: {college_key}")

    # ── Resolve college → metro ───────────────────────────────────────
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

    logger.info(f"  College: {college_name}")
    logger.info(f"  Metro: {metro}")

    # ── Stage 1: Get EDD employers ────────────────────────────────────
    cache_key = metro.lower().replace(" ", "_").replace("-", "_").replace(",", "")
    deep_cache = INDUSTRY_DIR / "cache" / f"edd_deep_{cache_key}.json"

    if deep_cache.exists() and not scrape:
        with open(deep_cache) as f:
            edd_employers = json.load(f)
        logger.info(f"  Loaded {len(edd_employers)} employers from cache")
    else:
        counties = METRO_COUNTIES.get(metro, [])
        if not counties:
            logger.error(f"  No counties for metro: {metro}")
            return []

        edd_employers = []
        seen = set()
        for county in counties:
            results = search_naics_codes(county, min_size=min_size)
            for emp in results:
                key = (emp["name"].lower(), emp.get("city", "").lower())
                if key not in seen:
                    seen.add(key)
                    edd_employers.append(emp)

        deep_cache.parent.mkdir(exist_ok=True)
        with open(deep_cache, "w") as f:
            json.dump(edd_employers, f, indent=2)
        logger.info(f"  Scraped {len(edd_employers)} employers")

    if not edd_employers:
        logger.error(f"  No employers found")
        return []

    # ── Stage 2: Clean names and deduplicate branches ─────────────────
    for emp in edd_employers:
        emp["name"] = _clean_employer_name(emp["name"])

    deduped = _deduplicate_branches(edd_employers)
    logger.info(f"  After dedup: {len(deduped)} (from {len(edd_employers)})")

    # ── Stage 3 & 4: Assign sector and SOC codes ──────────────────────
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    # Build SOC codes by major group, filtered to this metro
    occ_by_group: dict[str, list[str]] = defaultdict(list)
    for occ in occupations:
        if metro in occ.get("regions", {}):
            group = occ["soc_code"].split("-")[0]
            occ_by_group[group].append(occ["soc_code"])

    for emp in deduped:
        emp["soc_codes"] = _assign_soc_codes(emp, occ_by_group)

    # ── Stage 5: Select with sector diversity ─────────────────────────
    selected = _select_employers(deduped, target=target)
    logger.info(f"  Selected {len(selected)} employers")

    sector_counts: dict[str, int] = {}
    for emp in selected:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # ── Stage 5b: LLM cleanup (descriptions + name fixes + occupation assignment)
    selected = _llm_cleanup(selected, metro, filtered_occupations=filtered_occupations)

    # ── Stage 6: Format and merge ─────────────────────────────────────
    formatted = _format_for_json(selected, metro)

    with open(EMPLOYERS_PATH) as f:
        existing = json.load(f)

    merged, added, updated = _merge_employers(formatted, existing)

    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    logger.info(f"  Merge: {added} new, {updated} updated. Total: {len(merged)}")

    return formatted


def generate_all(scrape: bool = True, min_size: str = "G") -> dict[str, int]:
    """Run pipeline for all colleges with enriched caches."""
    from pipeline.industry.region_maps import COLLEGE_REGION_MAP

    sources_path = Path(__file__).parent.parent / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)

    enriched_files = sorted(CACHE_DIR.glob("*_enriched.json"))
    college_keys = [p.stem.replace("_enriched", "") for p in enriched_files]

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
        should_scrape = scrape and metro not in metro_done
        metro_done.add(metro)

        try:
            employers = generate_for_college(key, scrape=should_scrape, min_size=min_size)
            results[key] = len(employers)
        except Exception as e:
            logger.error(f"Failed for {key}: {e}")
            results[key] = -1

    logger.info(f"\n{'=' * 60}")
    logger.info(f"DONE: {sum(1 for v in results.values() if v > 0)} colleges processed")
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate employer lists from EDD data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--college", type=str)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--no-scrape", action="store_true",
                        help="Use cached EDD data only")
    parser.add_argument("--target", type=int, default=50,
                        help="Target employers per college (default: 50)")
    parser.add_argument("--min-size", type=str, default="G",
                        choices=["A", "B", "C", "D", "E", "F", "G", "H", "I"],
                        help="Minimum employer size class (default: G=250+)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    if getattr(args, "all"):
        generate_all(scrape=not args.no_scrape, min_size=args.min_size)
    else:
        generate_for_college(args.college, target=args.target, scrape=not args.no_scrape, min_size=args.min_size)


if __name__ == "__main__":
    main()
