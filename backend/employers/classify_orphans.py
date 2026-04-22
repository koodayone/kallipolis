"""One-shot: classify the 357 truly-orphan employers.

These employers have no cache evidence in any retag tier (exact, suffix,
substring) — their NAICS4 cannot be recovered. To finish the unclassified
cleanup, we fall back on the NAICS-2 ``sector`` field (already on every
employer from the original EDD scrape) and apply a layered decision:

  1. NAICS-2 maps cleanly to a single SWP sector → auto-tag with that
     sector (Healthcare → Health, Education → Education and Human
     Development, Construction → Energy/Construction/Utilities, etc.).
  2. NAICS-2 is clearly out of SWP scope → drop the employer entirely
     (Finance, Real Estate, Arts/Entertainment, etc. — same scope
     treatment as ``drop_out_of_scope.py``).
  3. NAICS-2 is ambiguous (Government, Professional Services) → apply
     name-pattern rules. Government resolves to Public Safety, Health,
     or Education and Human Development based on keyword matches;
     Professional Services resolves to Energy/Construction/Utilities
     or Advanced Manufacturing for engineering/industries patterns.
     Unmatched ambiguous records are dropped.
  4. Manufacturing NAICS-2 with food-industry name keywords is
     redirected to Agriculture, Water and Environmental Technologies
     (dairy processors, meat packers, etc. would otherwise be tagged
     as Advanced Manufacturing).

Precision tradeoff: classifying from NAICS-2 + name heuristics loses
the NAICS4 specificity we have for cache-recovered employers. The
``sector`` field on each record remains as the display label; only
``swp_sectors`` is filled in. This is clearly a last-resort tier — the
alternative is leaving 357 employers as "Unclassified" in the atlas.

Usage::

    python3 -m employers.classify_orphans --dry-run
    python3 -m employers.classify_orphans
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter

from employers.retag_sectors import (
    EMPLOYERS_PATH,
    _build_canonical_key_index,
    _filter_substring_candidates,
    _retag_key,
    recover_naics4_set,
)

logger = logging.getLogger(__name__)


# NAICS-2 ``sector`` field → SWP sector. These are the unambiguous
# mappings where the NAICS-2 grouping aligns cleanly with exactly one
# SWP sector.
SECTOR_FIELD_MAP: dict[str, str] = {
    "Healthcare": "Health",
    "Hospitality & Food Service": "Retail, Hospitality and Tourism",
    "Education": "Education and Human Development",
    "Manufacturing": "Advanced Manufacturing",  # food override applied below
    "Construction": "Energy, Construction and Utilities",
    "Wholesale": "Global Trade",
    "Transportation": "Advanced Transportation and Logistics",
    "Information & Media": "Information and Communication Technologies - Digital Media",
    "Agriculture": "Agriculture, Water and Environmental Technologies",
}

# NAICS-2 sectors that don't fit any SWP sector. Employers in these
# categories are dropped rather than tagged.
DROP_SECTORS: set[str] = {
    "Finance",
    "Arts & Entertainment",
    "Other Services",
    "Administrative Services",
    "Retail",
    "Real Estate",
}

# Manufacturing sub-pattern: food/beverage producers that got NAICS-2
# "Manufacturing" should be Agriculture/Water/Environmental, not
# Advanced Manufacturing.
MANUFACTURING_FOOD_PATTERN = re.compile(
    r"\b(food|foods|cheese|meat|beef|dairy|beverage|beverages|winery|wines?|spirits|bottling|bakery|bakeries|brewing|brewery|produce|poultry|seafood)\b",
    re.IGNORECASE,
)

# Government name-pattern rules. Order matters — the first matching
# pattern wins. Unmatched government employers are dropped.
GOV_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(school district|office of education|unified)\b", re.I),
     "Education and Human Development"),
    (re.compile(r"\b(sheriffs?|police|fire|corrections?|penitentiary|court|district attorney|public defender|detention|jail|probation|lifeguards?)\b", re.I),
     "Public Safety"),
    (re.compile(r"(department of (public )?health|health and human services|human services agency|health services agency|environmental health|medical|hospital)", re.I),
     "Health"),
    (re.compile(r"(public works|environmental protection|environmental enforcement)", re.I),
     "Energy, Construction and Utilities"),
    (re.compile(r"(social services|adoptions|veterans|rehabilitation|children and families|centers for children)", re.I),
     "Education and Human Development"),
]

# Professional Services name-pattern rules. Same semantics.
PRO_SERVICES_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(engineer|engineering|surveyor|environmental services)\b", re.I),
     "Energy, Construction and Utilities"),
    (re.compile(r"\bindustries\b", re.I),
     "Advanced Manufacturing"),
]


def _classify(emp: dict) -> tuple[str, str | None]:
    """Return (action, swp_sector) where action ∈ {'tag', 'drop', 'leave'}."""
    sector = emp.get("sector")
    name = emp["name"]

    if sector in DROP_SECTORS:
        return "drop", None

    if sector == "Manufacturing":
        if MANUFACTURING_FOOD_PATTERN.search(name):
            return "tag", "Agriculture, Water and Environmental Technologies"
        return "tag", "Advanced Manufacturing"

    if sector in SECTOR_FIELD_MAP:
        return "tag", SECTOR_FIELD_MAP[sector]

    if sector == "Government":
        for pat, swp in GOV_PATTERNS:
            if pat.search(name):
                return "tag", swp
        return "drop", None

    if sector == "Professional Services":
        for pat, swp in PRO_SERVICES_PATTERNS:
            if pat.search(name):
                return "tag", swp
        return "drop", None

    # Unknown sector — leave untouched (shouldn't happen)
    return "leave", None


def classify(dry_run: bool = False) -> dict:
    from employers.edd_scrape import CTE_NAICS_CODES

    index = _build_canonical_key_index()
    substring_candidates = _filter_substring_candidates(index)

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    kept: list[dict] = []
    tag_counts: Counter = Counter()
    drop_counts: Counter = Counter()
    left_counts: Counter = Counter()

    for emp in employers:
        # Skip already-tagged employers
        if emp.get("swp_sectors"):
            kept.append(emp)
            continue
        # Skip employers whose NAICS4 is recoverable (should have been
        # tagged by retag_sectors, but defensively: they're not orphan)
        key = _retag_key(emp["name"])
        naics_set, _ = recover_naics4_set(
            key, index, substring_candidates, CTE_NAICS_CODES
        )
        if naics_set:
            kept.append(emp)
            continue

        action, swp = _classify(emp)
        if action == "tag":
            emp["swp_sectors"] = [swp]
            tag_counts[swp] += 1
            kept.append(emp)
        elif action == "drop":
            drop_counts[emp.get("sector") or "(none)"] += 1
            # Not appending to kept — this is the drop
        else:
            left_counts[emp.get("sector") or "(none)"] += 1
            kept.append(emp)

    stats = {
        "before": len(employers),
        "after": len(kept),
        "tagged": sum(tag_counts.values()),
        "dropped": sum(drop_counts.values()),
        "left": sum(left_counts.values()),
        "tag_by_sector": dict(tag_counts.most_common()),
        "drop_by_sector": dict(drop_counts.most_common()),
        "left_by_sector": dict(left_counts.most_common()),
    }

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(kept, f, indent=2)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify truly-orphan employers")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = classify(dry_run=args.dry_run)

    print("=" * 60)
    print("ORPHAN CLASSIFICATION RESULTS")
    print("=" * 60)
    print(f"  before:   {stats['before']}")
    print(f"  after:    {stats['after']}")
    print(f"  tagged:   {stats['tagged']}")
    print(f"  dropped:  {stats['dropped']}")
    if stats["left"]:
        print(f"  left:     {stats['left']} (unknown sector, untouched)")
    print()
    if stats["tag_by_sector"]:
        print("  Newly tagged (by SWP sector):")
        for s, n in stats["tag_by_sector"].items():
            print(f"    {n:4d}  {s}")
        print()
    if stats["drop_by_sector"]:
        print("  Dropped (by NAICS-2 sector field):")
        for s, n in stats["drop_by_sector"].items():
            print(f"    {n:4d}  {s}")
    if args.dry_run:
        print()
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
