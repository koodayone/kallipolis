"""One-shot script to re-tag Employer sector fields from cached raw EDD data.

Why this script exists. The employer-side SWP sector taxonomy was
re-baselined in commit f50bc38 (see docs/pipeline/swp-sector-naics.md)
against the canonical PCAH 12-sector list. Existing entries in
employers.json carry a generic NAICS-2 sector label (e.g., "Healthcare",
"Manufacturing", "Retail") that was derived at scrape time but does NOT
carry a canonical PCAH sector tag. Re-scraping everything would cost
hours of EDD time and Gemini tokens; the cleaner path is to recover
each employer's NAICS 4-digit code from the raw scrape caches (which
preserve `naics4`) and re-derive both the display sector and the new
`swp_sectors` list from the updated CTE_NAICS_CODES map.

How it works.
  1. Walk every cache file matching `cache/edd_region_*.raw.json` and
     `cache/edd_deep_*.json`. Both formats preserve `name`, `city`,
     and `naics4` per record.
  2. Apply the same name-cleanup pass that `generate.py` uses at the
     scrape→employers.json transition (`_clean_employer_name` +
     `_canonical_key`) so raw (pre-cleanup) names match the canonical
     post-cleanup names in employers.json.
  3. For each employer in employers.json, look up its NAICS4 via the
     canonical-key index. Re-derive the NAICS-2 display label
     (`sector`) from `_NAICS_SECTORS` and the SWP sector list
     (`swp_sectors`) from `CTE_NAICS_CODES[naics4][2]`.
  4. Multi-cache matches (same canonical-key in multiple regions or
     multiple NAICS4 hits): union the swp_sectors lists across all
     NAICS4s found. Emit a stderr warning for NAICS4 disagreements
     so operators can spot-check.
  5. Missing matches (employer present in employers.json but not in
     any cache): leave `sector` untouched, set `swp_sectors = []`,
     emit a stderr warning. Do not crash.
  6. Write employers.json back in place. Only `sector` and
     `swp_sectors` change; `website`, `description`, `occupations`,
     `regions`, and `name` are untouched.

The script is idempotent — running it twice with no cache or
CTE_NAICS_CODES changes produces the same employers.json.

Usage:
    python3 -m employers.retag_sectors
    python3 -m employers.retag_sectors --dry-run      # print stats only
    python3 -m employers.retag_sectors --verbose       # per-employer trace
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
CACHE_DIR = _THIS_DIR / "cache"
EMPLOYERS_PATH = _THIS_DIR / "employers.json"


# Post-LLM cleanup transforms that `_canonical_key` (the pre-LLM function)
# doesn't know about. The Gemini cleanup step routinely rewrites "&" as
# "and" in employer names ("Fresno Heart & Surgical Hosp" →
# "Fresno Heart and Surgical Hospital"), so a naive canonical-key join
# between pre-cleanup cache records and post-cleanup employers.json
# names misses ~18% of entries. Normalize both variants to a single
# form, and strip stray punctuation the LLM sometimes drops.
_AMPERSAND = re.compile(r"\s*&\s*")
_STRAY_PUNCT = re.compile(r"[.,'`]")


def _retag_key(name: str) -> str:
    """Canonical key for the retag join.

    Extends `_canonical_key` with the post-LLM normalizations needed to
    join pre-cleanup cache names against post-cleanup employers.json
    names. Specifically: collapses "&" to " and ", strips apostrophes
    and other stray punctuation the LLM sometimes drops, collapses
    repeated whitespace.
    """
    from employers.generate import _canonical_key, _clean_employer_name

    cleaned = _clean_employer_name(name)
    key = _canonical_key(cleaned)
    # Normalize ampersand variants to a single form
    key = _AMPERSAND.sub(" and ", key)
    # Strip stray punctuation
    key = _STRAY_PUNCT.sub("", key)
    # Collapse whitespace
    key = re.sub(r"\s+", " ", key).strip()
    return key


def _build_canonical_key_index() -> dict[str, set[str]]:
    """Walk all EDD cache files and build retag_key → {naics4,...}.

    Returns a dict where each key maps to the set of NAICS 4-digit
    codes that cache records with that key were scraped under. Most keys
    resolve to exactly one NAICS4; some legitimately have multiple (e.g.,
    a large employer scraped under several adjacent NAICS codes).
    """
    index: dict[str, set[str]] = defaultdict(set)
    cache_files = sorted(
        list(CACHE_DIR.glob("edd_region_*.raw.json"))
        + list(CACHE_DIR.glob("edd_deep_*.json"))
    )

    for path in cache_files:
        try:
            with open(path) as f:
                records = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Skipping unreadable cache file {path.name}: {e}")
            continue

        if not isinstance(records, list):
            continue

        file_hits = 0
        for rec in records:
            if not isinstance(rec, dict):
                continue
            name = rec.get("name")
            naics4 = rec.get("naics4")
            if not name or not naics4:
                continue
            key = _retag_key(name)
            index[key].add(str(naics4))
            file_hits += 1
        logger.info(f"  {path.name}: {file_hits} records indexed")

    logger.info(f"Indexed {len(index)} distinct canonical keys across {len(cache_files)} cache files")
    return index


def retag(dry_run: bool = False, verbose: bool = False) -> dict:
    """Re-tag every employer in employers.json from cache-recovered NAICS4.

    Returns a stats dict for the caller (matched, missing, multi, etc.).
    """
    from employers.edd_scrape import CTE_NAICS_CODES
    from employers.generate import _NAICS_SECTORS

    index = _build_canonical_key_index()

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    matched = 0
    missing = 0
    multi_naics = 0
    naics_not_in_list = 0
    sector_unchanged = 0
    sector_changed = 0

    # LLM-rewrite fallback suffixes: Gemini commonly appends these to
    # cleaned names in ways that break exact-key joins. Each entry is a
    # suffix to strip (in order) if the exact key misses.
    _LLM_SUFFIX_STRIPS = (" district", " inc", " llc", " corporation", " corp", " co")

    def _try_with_suffix_strips(key: str) -> set[str] | None:
        for suffix in _LLM_SUFFIX_STRIPS:
            if key.endswith(suffix):
                stripped = key[: -len(suffix)].strip()
                hit = index.get(stripped)
                if hit:
                    return hit
        return None

    for emp in employers:
        name = emp["name"]
        key = _retag_key(name)
        naics_set = index.get(key)

        if not naics_set:
            # LLM-suffix fallback: try stripping common appended suffixes
            naics_set = _try_with_suffix_strips(key)

        if not naics_set:
            missing += 1
            emp["swp_sectors"] = []
            if verbose:
                print(f"  MISS  {name!r}", file=sys.stderr)
            continue

        if len(naics_set) > 1:
            multi_naics += 1
            if verbose:
                print(
                    f"  MULTI {name!r} → NAICS4 {sorted(naics_set)!r}",
                    file=sys.stderr,
                )

        # Union swp_sectors across every matched NAICS4. Preserve first-primary
        # ordering so the "first element is the primary" contract holds — use
        # the NAICS4 with the richest sector list as the canonical, and append
        # any additional sectors from the others in a stable order.
        naics_with_tuples = [
            (n4, CTE_NAICS_CODES[n4])
            for n4 in sorted(naics_set)
            if n4 in CTE_NAICS_CODES
        ]
        if not naics_with_tuples:
            # Every recovered NAICS4 is out of the current CTE scope
            # (e.g., a finance code we dropped earlier). Treat like a
            # missing match: leave sector, set swp_sectors = [].
            naics_not_in_list += 1
            emp["swp_sectors"] = []
            if verbose:
                print(
                    f"  OUT-OF-SCOPE {name!r} → NAICS4 {sorted(naics_set)!r} "
                    f"(all dropped from CTE_NAICS_CODES)",
                    file=sys.stderr,
                )
            continue

        # Pick the NAICS4 with the longest sector list as the primary source.
        naics_with_tuples.sort(key=lambda nt: -len(nt[1][2]))
        primary_naics, (naicsect, label, primary_sectors) = naics_with_tuples[0]

        # Union across all matches, preserving primary_sectors order first.
        merged: list[str] = list(primary_sectors)
        for _, (_s, _l, sectors) in naics_with_tuples[1:]:
            for s in sectors:
                if s not in merged:
                    merged.append(s)

        emp["swp_sectors"] = merged

        # Re-derive the NAICS-2 display label from the primary NAICS4.
        naics2 = primary_naics[:2]
        new_sector = _NAICS_SECTORS.get(naics2, emp.get("sector", "Other"))
        old_sector = emp.get("sector")
        if new_sector != old_sector:
            sector_changed += 1
            if verbose:
                print(
                    f"  SECTOR {name!r}: {old_sector!r} → {new_sector!r}",
                    file=sys.stderr,
                )
        else:
            sector_unchanged += 1
        emp["sector"] = new_sector
        matched += 1

    stats = {
        "total": len(employers),
        "matched": matched,
        "missing": missing,
        "multi_naics": multi_naics,
        "naics_not_in_list": naics_not_in_list,
        "sector_changed": sector_changed,
        "sector_unchanged": sector_unchanged,
    }

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(employers, f, indent=2)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-tag employer sectors from cache")
    parser.add_argument("--dry-run", action="store_true", help="Compute stats but don't write")
    parser.add_argument("--verbose", action="store_true", help="Per-employer trace to stderr")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    stats = retag(dry_run=args.dry_run, verbose=args.verbose)

    print("=" * 60)
    print("RE-TAG RESULTS")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:22s}  {v}")
    pct_matched = 100.0 * stats["matched"] / stats["total"] if stats["total"] else 0
    pct_missing = 100.0 * stats["missing"] / stats["total"] if stats["total"] else 0
    print(f"  matched%              {pct_matched:.1f}")
    print(f"  missing%              {pct_missing:.1f}")
    if args.dry_run:
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
