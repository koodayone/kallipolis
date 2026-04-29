"""
Generate employer lists from EDD's ALMIS Employer Database.

Every employer is a verified Data Axle/EDD entry, selected by NAICS
industry code and employee count. Gemini is used to clean names,
generate descriptions, and assign SOC codes from the regional
occupation list.

The generation unit is the COE region (Bay, CVML, FN, GS, IE/D, LA,
OC, SCC, SD/I). All colleges in a region share one employer pool —
consistent with the Strong Workforce Program's regional consortium
model and with the graph, where every College and Employer attaches
to the region via IN_MARKET.

Pipeline:
  1. Scrape EDD across every county in the COE region (CTE NAICS codes, size 100+)
  2. Clean and deduplicate employer names (deterministic pre-filters)
  3. Assign sector + fallback SOC codes via NAICS→SOC mapping
  4. LLM cleanup via Gemini (names, descriptions, regional SOC codes)
  5. Format and merge into employers.json

Usage:
    python -m employers.generate --region Bay
    python -m employers.generate --region Bay --no-scrape
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

logger = logging.getLogger(__name__)


class LLMCleanupError(RuntimeError):
    """Raised when a Gemini cleanup batch fails after all retries."""


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

# Model used for employer LLM cleanup. Overridable via GEMINI_CLEANUP_MODEL
# so we can route around service-side congestion on any one endpoint
# (`gemini-2.5-flash` has periodic 503 storms; `gemini-2.5-flash-lite`
# is a lighter-weight alternative on a different capacity pool).
# Read at call time — load_dotenv runs in __main__ below, which happens
# AFTER module-level evaluation, so a module-level constant would
# miss .env overrides.
def _gemini_model() -> str:
    return os.environ.get("GEMINI_CLEANUP_MODEL", "gemini-2.5-flash")

# Retry policy for transient Gemini failures.
_GEMINI_MAX_ATTEMPTS = 3
_GEMINI_BACKOFF_BASE_SECONDS = 2.0

# 503 UNAVAILABLE responses from Gemini 2.5 Flash are most often TPM
# quota exhaustion disguised as "high demand" — a single batch can
# burn 30–50k output tokens, and sending 7 back-to-back trips the
# per-minute ceiling on shared tiers. A minimum inter-batch delay
# smooths the request rate enough to stay under quota.
_INTER_BATCH_DELAY_SECONDS = 20.0

# When Gemini returns 503 UNAVAILABLE specifically, treat it as a
# rate-limit signal: wait longer than the generic backoff so the
# per-minute token bucket has time to refill.
_GEMINI_503_BACKOFF_SECONDS = 65.0

EMPLOYERS_PATH = Path(__file__).parent / "employers.json"

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


# ── Formatting ────────────────────────────────────────────────────────────
#
# C13 retired the deterministic NAICS-2 → SOC major-group seed
# (`NAICS_TO_SOC_GROUPS` / `_assign_soc_codes`). That seed predated
# `enrich.py:Pass 3`, which now bounds SOC selection on the BLS OEWS
# NAICS-4 industry-occupation matrix — a much higher-resolution
# institutional source than NAICS-2 → SOC-major-group buckets. The
# scrape pipeline emits records with empty `occupations`; enrich.py
# fills them via the shadow → cutover lifecycle.

def _format_for_json(employers: list[dict], region_code: str) -> list[dict]:
    """Convert to employers.json schema.

    Each output row is tagged with canonical PCAH `swp_sectors` from
    `CTE_NAICS_CODES[naics4][2]` and the originating `naics4` itself.
    NAICS-4 is the institutional anchor for layer 1 (the BLS OEWS
    industry-occupation pool that bounds Pass 3's SOC selection); it
    must persist on every record. The original ingest scraper already
    attaches `naics4` upstream (edd_scrape.py:582-584); writing it
    here keeps the canonical record self-contained for downstream
    consumers (Neo4j ingest, the Pass 3 OES lookup).
    """
    from employers.edd_scrape import CTE_NAICS_CODES

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

        naics4 = emp.get("naics4", emp.get("naics_code", ""))
        swp_sectors = list(CTE_NAICS_CODES.get(naics4, ("", "", []))[2])

        formatted.append({
            "name": emp["name"],
            "sector": emp.get("sector", "Other"),
            "swp_sectors": swp_sectors,
            "naics4": naics4 or None,
            "description": desc,
            "regions": [region_code],
            # Skeleton — `enrich.py:Pass 3` populates `occupations`
            # later from the OES NAICS-bounded industry pool, then
            # cutover.py promotes shadow → canonical.
            "occupations": [],
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

def _build_name_cleanup_prefix(metro: str) -> str:
    """Build the shared prefix for name-cleanup batches.

    C13 simplification: the prompt no longer assigns occupations.
    Layer 1 occupational classification is owned by `enrich.py:Pass 3`
    against the BLS OEWS NAICS-bounded industry pool — a higher-
    resolution institutional source than this batched LLM was using
    (a 700-SOC regional pool sliced into NAICS-2-major-group buckets).
    Generate.py now produces clean name + description; enrich.py
    handles SOC selection downstream.
    """
    return (
        f"You are cleaning employer records for the {metro} metro area.\n\n"
        "For each employer name you receive: clean the name and write a "
        "one-sentence description.\n"
        "- Expand abbreviations (Hosp→Hospital, Clg→College, Dist→District)\n"
        "- Remove branch qualifiers, location suffixes, department names\n"
        "- Keep the name recognizable\n"
        '- Return "REMOVE" for branch duplicates, internal departments, '
        "foundations when parent is listed, staffing agencies.\n"
    )


def _llm_cleanup(employers: list[dict], metro: str) -> list[dict]:
    """Clean employer names + descriptions via Gemini Flash.

    Pre-C13 this function also assigned 3–8 SOC codes from a regional
    pool; that path is retired (see `_build_name_cleanup_prefix`
    docstring). Post-C13 the function emits records with empty
    `soc_codes` (downstream `_format_for_json` writes empty
    `occupations`); `enrich.py:Pass 3` populates the canonical
    occupations field via the shadow → cutover lifecycle.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("  No GEMINI_API_KEY — skipping LLM cleanup")
        return employers

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    names = [e["name"] for e in employers]
    names_block = "\n".join(f"- {n}" for n in names)

    prompt = (
        f"{_build_name_cleanup_prefix(metro)}\n"
        f"Process these {len(names)} employer names:\n\n"
        'Return JSON: {"Original Name": {"name": "Clean Name", '
        '"description": "..."} or "Original Name": "REMOVE"}\n\n'
        f"Names:\n{names_block}"
    )

    last_error: Exception | None = None
    cleanup: dict | None = None
    for attempt in range(1, _GEMINI_MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=_gemini_model(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=65536,
                    temperature=0.1,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            cleanup = json.loads(response.text)
            break
        except Exception as e:
            last_error = e
            if attempt < _GEMINI_MAX_ATTEMPTS:
                is_503 = "503" in str(e) or "UNAVAILABLE" in str(e)
                delay = (
                    _GEMINI_503_BACKOFF_SECONDS
                    if is_503
                    else _GEMINI_BACKOFF_BASE_SECONDS ** attempt
                )
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
        kept.append(emp)

    # Post-rename dedup — uses the unified canonical key, not ad-hoc lowercase.
    seen: dict[str, dict] = {}
    final = []
    for emp in kept:
        key = _canonical_key(emp["name"])
        if key in seen:
            removed += 1
        else:
            seen[key] = emp
            final.append(emp)

    logger.info(f"  LLM cleanup: {renamed} renamed, {removed} removed, {len(final)} kept")
    return final


# ── Orchestrator ──────────────────────────────────────────────────────────

def generate_for_region(
    region_code: str,
    scrape: bool = True,
    min_size: str = "F",
) -> list[dict]:
    """Run the employer generation pipeline for an entire COE region.

    Scrapes all counties in the region, deduplicates, runs LLM cleanup,
    merges into employers.json (unioning regions and occupations on
    name collisions), and returns the formatted employer list.
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

    # ── Stage 3: Assign sector ────────────────────────────────────────
    # Layer 1 SOC assignment retired in C13 — `enrich.py:Pass 3` owns
    # occupations downstream via the OES NAICS-bounded industry pool.
    for emp in deduped:
        naics = emp.get("naics4", emp.get("naics_code", ""))[:2]
        emp["sector"] = _NAICS_SECTORS.get(naics, emp.get("industry", "Other"))

    sector_counts: dict[str, int] = {}
    for emp in deduped:
        sector_counts[emp["sector"]] = sector_counts.get(emp["sector"], 0) + 1
    for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1]):
        logger.info(f"    {sector}: {count}")

    # ── Stage 4: LLM name + description cleanup ──────────────────────
    selected = []
    failed_batches = 0
    total_batches = (len(deduped) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(deduped), BATCH_SIZE):
        batch = deduped[i:i + BATCH_SIZE]
        batch_idx = i // BATCH_SIZE
        if batch_idx > 0:
            # Smooth the request rate to stay under Gemini's per-minute TPM
            # quota. See _INTER_BATCH_DELAY_SECONDS.
            time.sleep(_INTER_BATCH_DELAY_SECONDS)
        logger.info(f"  LLM cleanup batch {batch_idx + 1}/{total_batches} ({len(batch)} employers)")
        try:
            cleaned = _llm_cleanup(
                batch,
                f"{region_display} region of California",
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

    # ── Stage 5: Format and merge into employers.json ────────────────
    formatted = _format_for_json(selected, region_code)

    with open(EMPLOYERS_PATH) as f:
        existing = json.load(f)

    merged, added, updated = _merge_employers(formatted, existing)

    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(merged, f, indent=2)

    logger.info(
        f"  Formatted {len(formatted)} employers for region {region_code}. "
        f"Merge: {added} new, {updated} updated. Total: {len(merged)}"
    )
    return formatted


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
    parser.add_argument("--region", type=str, required=True,
                        help="COE region code to generate for (e.g., Bay, CVML, SCC, IE/D, SD/I, LA, OC, GS, FN)")
    parser.add_argument("--no-scrape", action="store_true",
                        help="Use cached EDD data only")
    parser.add_argument("--min-size", type=str, default="F",
                        choices=["A", "B", "C", "D", "E", "F", "G", "H", "I"],
                        help="Minimum employer size class (default: F=100+)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    result = generate_for_region(
        args.region, scrape=not args.no_scrape, min_size=args.min_size,
    )
    logger.info(f"Region {args.region}: {len(result)} employers generated and merged")


if __name__ == "__main__":
    main()
