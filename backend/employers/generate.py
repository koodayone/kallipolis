"""
Generate employer lists from EDD's ALMIS Employer Database.

Every employer is a verified Data Axle/EDD entry, selected by NAICS
industry code and employee count. Gemini is used to clean names,
generate descriptions, and assign SOC codes from the regional
occupation list.

Pipeline:
  1. Scrape EDD employers by CTE NAICS codes + size filter (100+)
  2. Clean and deduplicate employer names (deterministic pre-filters)
  3. Assign sector + fallback SOC codes via NAICS→SOC mapping
  4. LLM cleanup via Gemini (names, descriptions, regional SOC codes)
  5. Format and merge into employers.json

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
import time
from collections import defaultdict
from pathlib import Path
from ontology.regions import OEWS_METRO_TO_COE

logger = logging.getLogger(__name__)


class LLMCleanupError(RuntimeError):
    """Raised when a Gemini cleanup batch fails after all retries."""


# Career-track education levels excluded from the regional occupation
# pool fed to the LLM. "No formal credential" and "HS diploma" exclude
# roles that don't represent meaningful CTE outcomes; graduate-degree
# levels exclude roles out of scope for community college pathways.
_EXCLUDE_EDUCATION = frozenset({
    "No formal educational credential",
    "High school diploma or equivalent",
    "Some college, no degree",
    "Master's degree",
    "Doctoral or professional degree",
})

# NAICS 4-digit codes whose members are structurally not partnership
# targets. Staffing agencies (5613) and business-support services
# (5614) place workers at other employers; listing them as employers
# creates false positives the LLM would otherwise have to filter out.
_NEVER_EMPLOYER_NAICS = frozenset({"5613", "5614"})

# Name patterns that signal a sub-unit or non-institutional entry
# that should be dropped before the LLM step. These are intentionally
# conservative — the LLM still gets the last word on everything that
# survives.
_DROP_NAME_PATTERNS = [
    re.compile(r"^\s*Dept\s+Of\b", re.IGNORECASE),
    re.compile(r"^\s*County\s+Of\b", re.IGNORECASE),
    re.compile(r"^\s*City\s+Of\b", re.IGNORECASE),
    re.compile(r"^\s*State\s+Of\b", re.IGNORECASE),
]

# SOC code regex — matches e.g. "11-3121" anywhere in a string, so the
# LLM can return bare codes or codes followed by titles with any
# separator (":", " - ", " — ", whitespace).
_SOC_RE = re.compile(r"\b(\d{2}-\d{4})\b")

# Gemini batch size. Gemini 2.5 Flash with 1M context easily handles
# hundreds of employer names in one request; 100 is a conservative
# choice that still cuts request count 3× vs. the prior value of 30.
BATCH_SIZE = 100

# Retry policy for transient Gemini failures.
_GEMINI_MAX_ATTEMPTS = 3
_GEMINI_BACKOFF_BASE_SECONDS = 2.0

EMPLOYERS_PATH = Path(__file__).parent / "employers.json"
OCCUPATIONS_PATH = Path(__file__).parent.parent / "occupations" / "occupations.json"
CACHE_DIR = Path(__file__).parent / "cache"
PIPELINE_CACHE_DIR = Path(__file__).parent.parent / "pipeline" / "cache"

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
    # General institutional
    (r"\bCtr\b", "Center"), (r"\bHosp\b", "Hospital"),
    (r"\bDept\b", "Department"), (r"\bUniv\b", "University"),
    (r"\bMed\b", "Medical"), (r"\bMeml\b", "Memorial"),
    (r"\bInst\b", "Institute"), (r"\bAssn\b", "Association"),
    (r"\bAssoc\b", "Association"), (r"\bFdn\b", "Foundation"),
    (r"\bSch\b", "School"), (r"\bDist\b", "District"),
    (r"\bLbry\b", "Library"),
    # Business / services
    (r"\bSvc\b", "Services"), (r"\bSvcs\b", "Services"),
    (r"\bSrvc\b", "Services"), (r"\bSrvcs\b", "Services"),
    (r"\bSys\b", "System"), (r"\bMgmt\b", "Management"),
    (r"\bGrp\b", "Group"), (r"\bIntl\b", "International"),
    (r"\bAdmn\b", "Administration"), (r"\bAdmin\b", "Administration"),
    (r"\bCmnty\b", "Community"), (r"\bComnty\b", "Community"),
    (r"\bRsrch\b", "Research"), (r"\bDvlpmt\b", "Development"),
    (r"\bGovt\b", "Government"), (r"\bPub\b", "Public"),
    (r"\bRltrs\b", "Realtors"), (r"\bProd\b", "Products"),
    (r"\bProds\b", "Products"), (r"\bInd\b", "Industries"),
    (r"\bBros\b", "Brothers"), (r"\bJr\b", "Junior"),
    (r"\bOfc\b", "Office"), (r"\bChf\b", "Chief"),
    # Construction / trades
    (r"\bHtg\b", "Heating"), (r"\bCond\b", "Conditioning"),
    (r"\bPlbg\b", "Plumbing"), (r"\bMfg\b", "Manufacturing"),
    (r"\bTech\b", "Technology"), (r"\bCorp\b", "Corporation"),
    (r"\bEngrng\b", "Engineering"),
    # Healthcare
    (r"\bHlth\b", "Health"), (r"\bNcr\b", "Cancer"),
    (r"\bCncr\b", "Cancer"),
    # Place names that appear frequently in LA cached data
    (r"\bNrthrdg\b", "Northridge"), (r"\bHllywd\b", "Hollywood"),
    (r"\bHls\b", "Hills"), (r"\bMtn\b", "Mountain"),
]

_STRIP_SUFFIXES = re.compile(
    r"\s*\b(Inc\.?|LLC|Corp\.?|Co\.?|Ltd\.?|LP)\s*$",
    re.IGNORECASE,
)

# Trailing location qualifiers attached to the same employer record by
# EDD — "Kaiser Permanente - Los Angeles" vs "Kaiser Permanente, Fresno"
# should collapse to one canonical key. Matches a trailing dash/comma
# followed by any whitespace-terminated tail.
_TRAILING_LOCATION = re.compile(r"\s*[-,]\s+[A-Za-z][A-Za-z\s]+$")


def _clean_employer_name(name: str) -> str:
    """Normalize abbreviations in EDD employer names."""
    cleaned = name.strip()
    for pattern, replacement in _ABBREVIATIONS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = _STRIP_SUFFIXES.sub("", cleaned).strip()
    return cleaned


def _normalize_name(name: str) -> str:
    """Normalize for deduplication matching. Delegates to _canonical_key."""
    return _canonical_key(name)


def _canonical_key(name: str) -> str:
    """Unified canonical dedup key.

    Strips legal suffixes, trailing location qualifiers, collapses
    whitespace, lowercases. Used as the single normalization scheme for
    branch dedup, post-LLM dedup, and cross-college merge.
    """
    s = name.strip()
    s = _STRIP_SUFFIXES.sub("", s)
    # Apply trailing-location stripping repeatedly (e.g. "Foo - Bar, CA")
    prev = None
    while prev != s:
        prev = s
        s = _TRAILING_LOCATION.sub("", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _should_drop_name(name: str) -> bool:
    """Deterministic pre-filter for names that are never employers."""
    return any(p.search(name) for p in _DROP_NAME_PATTERNS)


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


# ── Formatting ────────────────────────────────────────────────────────────

def _format_for_json(employers: list[dict], metro_or_region: str) -> list[dict]:
    """Convert to employers.json schema."""
    coe_region = OEWS_METRO_TO_COE.get(metro_or_region, metro_or_region)
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
            "regions": [coe_region],
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

def _build_occupation_prefix(metro: str, filtered_occupations: list[dict]) -> str:
    """Build the shared prefix that's cacheable across batches in a run.

    Contains the task framing and the full regional occupation list —
    i.e., everything that's identical from one batch to the next.
    Separating it out lets Gemini context caching eliminate re-sending
    the occupation list with every batch.
    """
    occ_lines = [f"- {o['soc_code']}: {o['title']}" for o in filtered_occupations]
    occ_list = "\n".join(occ_lines)
    return (
        f"You are cleaning employer records for the {metro} metro area.\n\n"
        "For each employer name you receive, perform TWO tasks:\n\n"
        "TASK 1 — CLEAN: clean the name and write a one-sentence description.\n"
        "- Expand abbreviations (Hosp→Hospital, Clg→College, Dist→District)\n"
        "- Remove branch qualifiers, location suffixes, department names\n"
        "- Keep the name recognizable\n"
        '- Return "REMOVE" for branch duplicates, internal departments, foundations when parent is listed, staffing agencies\n\n'
        "TASK 2 — ASSIGN OCCUPATIONS: select 3-8 SOC codes from the list below "
        "that this employer would have ON ITS OWN PAYROLL as direct employees.\n"
        "Only include roles the employer itself employs — not roles performed by "
        "external agencies, contractors, or government services. For example, a "
        "resort does not employ firefighters, and a hospital does not employ police officers.\n"
        "This is REQUIRED for every employer that is not removed.\n\n"
        f"AVAILABLE OCCUPATIONS:\n{occ_list}\n"
    )


def _create_occupation_cache(
    client,
    types_module,
    prefix: str,
) -> str | None:
    """Create a Gemini CachedContent for the shared prefix. Returns its
    resource name, or None if caching is unavailable or fails (e.g., the
    prefix is below the model's minimum cache size).
    """
    try:
        cache = client.caches.create(
            model="gemini-2.5-flash",
            config=types_module.CreateCachedContentConfig(
                contents=[
                    types_module.Content(
                        role="user",
                        parts=[types_module.Part(text=prefix)],
                    )
                ],
                ttl="3600s",
            ),
        )
        logger.info(f"  Gemini context cache created: {cache.name}")
        return cache.name
    except Exception as e:
        logger.info(f"  Gemini context caching unavailable ({e}) — using inline prefix")
        return None


def _llm_cleanup(
    employers: list[dict],
    metro: str,
    filtered_occupations: list[dict] | None = None,
    cached_prefix_name: str | None = None,
) -> list[dict]:
    """Clean employer names, generate descriptions, and assign occupations via Gemini Flash.

    When cached_prefix_name is provided, the per-batch request is
    minimized to the employer names + response-shape directive, and the
    cached prefix (occupation list + task framing) is attached via
    GenerateContentConfig.cached_content.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("  No GEMINI_API_KEY — skipping LLM cleanup")
        return employers

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    names = [e["name"] for e in employers]

    # Build prompt
    valid_soc_codes: set[str] = set()

    if filtered_occupations:
        valid_soc_codes = {o["soc_code"] for o in filtered_occupations}
        names_block = "\n".join(f"- {n}" for n in names)
        response_shape = (
            'Return JSON: {"Original Name": {"name": "Clean Name", "description": "...", "occupations": ["SOC-CODE", ...]} '
            'or "Original Name": "REMOVE"}\n\n'
            'IMPORTANT: Every non-removed employer MUST have an "occupations" array with 3-8 SOC codes.\n\n'
        )
        if cached_prefix_name:
            # Cached prefix carries the task framing + occupation list;
            # per-batch payload is minimal.
            prompt = (
                f"Here are {len(names)} employer names to process for the "
                f"{metro} metro area.\n\n"
                f"{response_shape}"
                f"Names:\n{names_block}"
            )
        else:
            prefix = _build_occupation_prefix(metro, filtered_occupations)
            prompt = (
                f"{prefix}\n"
                f"Process these {len(names)} employer names:\n\n"
                f"{response_shape}"
                f"Names:\n{names_block}"
            )
    else:
        prompt = (
            f"Here are {len(names)} employer names from the EDD database for the "
            f"{metro} metro area. For each, return either:\n"
            "- The cleaned canonical employer name + a one-sentence description\n"
            '- "REMOVE" if it should be dropped (branch duplicate, internal dept, foundation, staffing agency)\n\n'
            "Clean up: abbreviations, branch qualifiers, location suffixes.\n"
            "Keep the name recognizable.\n\n"
            'Return JSON: {"Original Name": {"name": "Clean Name", "description": "..."} '
            'or "Original Name": "REMOVE"}\n\n'
            "Names:\n" + "\n".join(f"- {n}" for n in names)
        )

    last_error: Exception | None = None
    cleanup: dict | None = None
    for attempt in range(1, _GEMINI_MAX_ATTEMPTS + 1):
        try:
            config_kwargs = dict(
                max_output_tokens=65536,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
            if cached_prefix_name:
                config_kwargs["cached_content"] = cached_prefix_name
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            cleanup = json.loads(response.text)
            break
        except Exception as e:
            last_error = e
            if attempt < _GEMINI_MAX_ATTEMPTS:
                delay = _GEMINI_BACKOFF_BASE_SECONDS ** attempt
                logger.warning(
                    f"  LLM cleanup attempt {attempt}/{_GEMINI_MAX_ATTEMPTS} "
                    f"failed: {e}. Retrying in {delay:.1f}s"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"  LLM cleanup failed after {_GEMINI_MAX_ATTEMPTS} attempts: {e}"
                )
    if cleanup is None:
        raise LLMCleanupError(
            f"Gemini cleanup failed for batch of {len(employers)} employers"
        ) from last_error

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
                # Extract SOC codes with a regex — tolerates any wrapping
                # format ("11-3121", "11-3121: Title", "11-3121 - Title").
                raw_socs: list[str] = []
                for s in action["occupations"]:
                    m = _SOC_RE.search(str(s))
                    if m:
                        raw_socs.append(m.group(1))
                valid = [s for s in raw_socs if s in valid_soc_codes]
                if valid:
                    emp["soc_codes"] = valid
                    occ_assigned += 1
        kept.append(emp)
    if filtered_occupations:
        logger.info(f"  LLM occupation assignment: {occ_assigned}/{len(kept)} employers")

    # Post-rename dedup — uses the unified canonical key, not ad-hoc lowercase.
    seen: dict[str, dict] = {}
    final = []
    for emp in kept:
        key = _canonical_key(emp["name"])
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

def _cache_path_for(
    metro: str,
    search_counties: list[str],
    has_override: bool,
) -> Path:
    """Resolve the EDD scrape cache path.

    When the college uses the default metro-derived counties, key by
    metro so sibling colleges in the same OEWS metro share the scrape.
    When the college has a COLLEGE_SEARCH_COUNTIES override, key by
    the county list so the override is honored.
    """
    if has_override:
        slug = "_".join(search_counties).lower().replace(" ", "_")
    else:
        slug = metro.lower().replace(" ", "_").replace("-", "_").replace(",", "")
    return CACHE_DIR / f"edd_deep_{slug}.json"


def generate_for_college(
    college_key: str,
    scrape: bool = True,
    min_size: str = "F",
    filtered_occupations: list[dict] | None = None,
) -> list[dict]:
    """Run the full employer generation pipeline for one college."""
    from employers.edd_scrape import search_naics_codes, METRO_COUNTIES
    from ontology.regions import COLLEGE_REGION_MAP, COLLEGE_COE_REGION

    import warnings
    warnings.filterwarnings("ignore")

    logger.info(f"{'=' * 60}")
    logger.info(f"Generating employers for: {college_key}")

    # ── Resolve college → metro ───────────────────────────────────────
    sources_path = Path(__file__).parent.parent / "pipeline" / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)
    college_info = sources.get("colleges", {}).get(college_key)
    if not college_info:
        logger.error(f"  College {college_key} not in catalog_sources.json")
        return []

    college_name = college_info["name"]
    from ontology.regions import get_college_metros, COLLEGE_SEARCH_COUNTIES
    metros = get_college_metros(college_name)
    if not metros:
        logger.error(f"  {college_name} not in COLLEGE_REGION_MAP")
        return []
    metro = metros[0]  # Primary metro for employer tagging

    logger.info(f"  College: {college_name}")
    logger.info(f"  Metros: {' · '.join(metros)}")

    # ── Stage 1: Get EDD employers ────────────────────────────────────
    # Use college-specific county list if available, otherwise derive from all metros
    override_counties = COLLEGE_SEARCH_COUNTIES.get(college_name)
    has_override = override_counties is not None
    if has_override:
        search_counties = override_counties
    else:
        search_counties = []
        for m in metros:
            for c in METRO_COUNTIES.get(m, []):
                if c not in search_counties:
                    search_counties.append(c)
    logger.info(f"  Search counties: {search_counties}")

    deep_cache = _cache_path_for(metro, search_counties, has_override)
    # Backwards-compatible fallback: earlier runs keyed every cache by the
    # search-counties slug, even when no override was set. Honor that if
    # the metro-keyed file does not yet exist.
    legacy_cache = (
        CACHE_DIR
        / f"edd_deep_{'_'.join(search_counties).lower().replace(' ', '_')}.json"
    )
    if not deep_cache.exists() and legacy_cache.exists():
        deep_cache = legacy_cache

    if deep_cache.exists() and not scrape:
        with open(deep_cache) as f:
            edd_employers = json.load(f)
        logger.info(f"  Loaded {len(edd_employers)} employers from cache")
    else:
        if not search_counties:
            logger.error(f"  No counties to search")
            return []

        edd_employers = []
        seen = set()
        for county in search_counties:
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

    # ── Stage 2: Pre-filter, clean names, and deduplicate branches ────
    # Deterministic pre-filters: drop staffing/business-support NAICS
    # rows and names matching the "never employer" patterns. The LLM
    # step still has final say on everything that survives.
    pre_count = len(edd_employers)
    edd_employers = [
        emp for emp in edd_employers
        if emp.get("naics4", "") not in _NEVER_EMPLOYER_NAICS
        and not _should_drop_name(emp.get("name", ""))
    ]
    if pre_count != len(edd_employers):
        logger.info(
            f"  Pre-filter: dropped {pre_count - len(edd_employers)} rows "
            f"(staffing/business-support NAICS + name patterns)"
        )

    for emp in edd_employers:
        emp["name"] = _clean_employer_name(emp["name"])

    deduped = _deduplicate_branches(edd_employers)
    logger.info(f"  After dedup: {len(deduped)} (from {len(edd_employers)})")

    # ── Stage 3 & 4: Assign sector and SOC codes ──────────────────────
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    coe_region = COLLEGE_COE_REGION.get(college_name)
    regional_occupations = [
        occ for occ in occupations
        if coe_region and coe_region in occ.get("regions", {})
        and occ.get("education_level") not in _EXCLUDE_EDUCATION
    ]
    logger.info(f"  Career-track occupations ({coe_region}): {len(regional_occupations)}")

    # Build SOC codes by major group (fallback if LLM doesn't assign)
    occ_by_group: dict[str, list[str]] = defaultdict(list)
    for occ in regional_occupations:
        group = occ["soc_code"].split("-")[0]
        occ_by_group[group].append(occ["soc_code"])

    # Assign sector labels and fallback SOC codes
    for emp in deduped:
        naics = emp.get("naics4", emp.get("naics_code", ""))[:2]
        emp["sector"] = _NAICS_SECTORS.get(naics, emp.get("industry", "Other"))
        emp["soc_codes"] = _assign_soc_codes(emp, occ_by_group)

    sector_counts: dict[str, int] = {}
    for emp in deduped:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # ── Stage 5: LLM cleanup in batches (dedup, normalize, describe, assign occupations)
    # Use caller-provided filtered_occupations, or fall back to regional occupations
    llm_occupations = filtered_occupations or regional_occupations

    # Create a Gemini context cache for the occupation-list prefix once,
    # then reuse across every batch. If caching fails (model min-token
    # floor, quota, library version), _llm_cleanup falls back to inline.
    cached_prefix_name: str | None = None
    if llm_occupations and os.environ.get("GEMINI_API_KEY"):
        try:
            from google import genai
            from google.genai import types as _gtypes
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            _prefix = _build_occupation_prefix(metro, llm_occupations)
            cached_prefix_name = _create_occupation_cache(_client, _gtypes, _prefix)
        except Exception as e:
            logger.info(f"  Gemini cache setup skipped: {e}")

    selected = []
    failed_batches = 0
    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i:i + BATCH_SIZE]
        try:
            cleaned = _llm_cleanup(
                batch,
                metro,
                filtered_occupations=llm_occupations,
                cached_prefix_name=cached_prefix_name,
            )
            selected.extend(cleaned)
        except LLMCleanupError as e:
            failed_batches += 1
            failing_names = [emp["name"] for emp in batch]
            logger.error(
                f"  LLM cleanup batch {i // BATCH_SIZE} dropped "
                f"({len(batch)} employers): {e}. Names: {failing_names}"
            )
    logger.info(f"  After LLM cleanup: {len(selected)} employers (from {len(deduped)})")
    if failed_batches:
        logger.warning(
            f"  {failed_batches} LLM batches failed — their employers were skipped. "
            f"Re-run with --no-scrape to retry."
        )

    # ── Stage 6: Format and merge ─────────────────────────────────────
    formatted = _format_for_json(selected, metro)

    with open(EMPLOYERS_PATH) as f:
        existing = json.load(f)

    merged, added, updated = _merge_employers(formatted, existing)

    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)
    logger.info(f"  Merge: {added} new, {updated} updated. Total: {len(merged)}")

    return formatted


def generate_for_region(
    region_code: str,
    scrape: bool = True,
    min_size: str = "F",
) -> list[dict]:
    """Run the employer generation pipeline for an entire COE region.

    Scrapes all counties in the region, deduplicates, runs LLM cleanup,
    and returns the formatted employer list. Does NOT merge into
    employers.json — the caller decides when and how to merge.
    """
    from employers.edd_scrape import scrape_region, load_region_cached, _region_cache_path
    from ontology.regions import COE_REGION_TO_COUNTIES, COE_REGION_DISPLAY

    import warnings
    warnings.filterwarnings("ignore")

    counties = COE_REGION_TO_COUNTIES.get(region_code)
    if not counties:
        logger.error(f"Unknown COE region: {region_code}")
        return []

    region_display = COE_REGION_DISPLAY.get(region_code, region_code)

    logger.info(f"{'=' * 60}")
    logger.info(f"Generating employers for region: {region_code} ({region_display})")
    logger.info(f"  Counties: {', '.join(counties)}")

    # ── Stage 1: Get EDD employers ────────────────────────────────────
    if not scrape:
        edd_employers = load_region_cached(region_code, min_size)
        if edd_employers is None:
            logger.error(
                f"  No regional cache for {region_code}. "
                f"Run: python -m employers.generate --region {region_code}"
            )
            return []
        logger.info(f"  Loaded {len(edd_employers)} employers from cache")
    else:
        edd_employers = scrape_region(region_code, min_size=min_size)

    if not edd_employers:
        logger.error(f"  No employers found for region {region_code}")
        return []

    # Save pre-LLM raw intermediate
    raw_path = _region_cache_path(region_code, min_size).with_suffix(".raw.json")
    with open(raw_path, "w") as f:
        json.dump(edd_employers, f, indent=2)
    logger.info(f"  Saved pre-LLM raw to {raw_path.name}")

    # ── Stage 2: Pre-filter, clean, deduplicate ───────────────────────
    pre_count = len(edd_employers)
    edd_employers = [
        emp for emp in edd_employers
        if emp.get("naics4", "") not in _NEVER_EMPLOYER_NAICS
        and not _should_drop_name(emp.get("name", ""))
    ]
    if pre_count != len(edd_employers):
        logger.info(
            f"  Pre-filter: dropped {pre_count - len(edd_employers)} rows "
            f"(staffing/business-support NAICS + name patterns)"
        )

    for emp in edd_employers:
        emp["name"] = _clean_employer_name(emp["name"])

    deduped = _deduplicate_branches(edd_employers)
    logger.info(f"  After dedup: {len(deduped)} (from {len(edd_employers)})")

    # ── Stage 3: Assign sector and SOC codes ──────────────────────────
    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    regional_occupations = [
        occ for occ in occupations
        if region_code in occ.get("regions", {})
        and occ.get("education_level") not in _EXCLUDE_EDUCATION
    ]
    logger.info(f"  Career-track occupations ({region_code}): {len(regional_occupations)}")

    occ_by_group: dict[str, list[str]] = defaultdict(list)
    for occ in regional_occupations:
        group = occ["soc_code"].split("-")[0]
        occ_by_group[group].append(occ["soc_code"])

    for emp in deduped:
        naics = emp.get("naics4", emp.get("naics_code", ""))[:2]
        emp["sector"] = _NAICS_SECTORS.get(naics, emp.get("industry", "Other"))
        emp["soc_codes"] = _assign_soc_codes(emp, occ_by_group)

    sector_counts: dict[str, int] = {}
    for emp in deduped:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # ── Stage 4: LLM cleanup ─────────────────────────────────────────
    cached_prefix_name: str | None = None
    if regional_occupations and os.environ.get("GEMINI_API_KEY"):
        try:
            from google import genai
            from google.genai import types as _gtypes
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            _prefix = _build_occupation_prefix(
                f"{region_display} region of California", regional_occupations
            )
            cached_prefix_name = _create_occupation_cache(_client, _gtypes, _prefix)
        except Exception as e:
            logger.info(f"  Gemini cache setup skipped: {e}")

    selected = []
    failed_batches = 0
    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i:i + BATCH_SIZE]
        try:
            cleaned = _llm_cleanup(
                batch,
                f"{region_display} region of California",
                filtered_occupations=regional_occupations,
                cached_prefix_name=cached_prefix_name,
            )
            selected.extend(cleaned)
        except LLMCleanupError as e:
            failed_batches += 1
            logger.error(
                f"  LLM cleanup batch {i // BATCH_SIZE} dropped "
                f"({len(batch)} employers): {e}"
            )
    logger.info(f"  After LLM cleanup: {len(selected)} employers (from {len(deduped)})")
    if failed_batches:
        logger.warning(
            f"  {failed_batches} LLM batches failed — their employers were skipped. "
            f"Re-run with --no-scrape to retry."
        )

    # ── Stage 5: Format (no merge — caller decides) ──────────────────
    formatted = _format_for_json(selected, region_code)

    logger.info(f"  Formatted {len(formatted)} employers for region {region_code}")
    return formatted


def generate_all(scrape: bool = True, min_size: str = "F") -> dict[str, int]:
    """Run pipeline for all colleges with enriched caches."""
    from ontology.regions import COLLEGE_REGION_MAP

    sources_path = Path(__file__).parent.parent / "pipeline" / "catalog_sources.json"
    with open(sources_path) as f:
        sources = json.load(f)

    enriched_files = sorted(PIPELINE_CACHE_DIR.glob("*_enriched.json"))
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
    # Load .env so GEMINI_API_KEY is available when invoked directly
    # (pipeline/run.py already does this, but `python -m employers.generate`
    # bypasses that entry point).
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Generate employer lists from EDD data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--college", type=str,
                       help="Generate for a single college (legacy per-metro path)")
    group.add_argument("--region", type=str,
                       help="Generate for an entire COE region (e.g., SCC, CVML, Bay)")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--no-scrape", action="store_true",
                        help="Use cached EDD data only")
    parser.add_argument("--min-size", type=str, default="F",
                        choices=["A", "B", "C", "D", "E", "F", "G", "H", "I"],
                        help="Minimum employer size class (default: F=100+)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    if args.region:
        result = generate_for_region(
            args.region, scrape=not args.no_scrape, min_size=args.min_size,
        )
        logger.info(f"Region {args.region}: {len(result)} employers generated (not merged)")
    elif getattr(args, "all"):
        generate_all(scrape=not args.no_scrape, min_size=args.min_size)
    else:
        generate_for_college(args.college, scrape=not args.no_scrape, min_size=args.min_size)


if __name__ == "__main__":
    main()
