"""One-shot: drop out-of-SWP-scope employers from employers.json.

These are employers whose NAICS4 is recoverable from the scrape cache but
is NOT present in the current ``CTE_NAICS_CODES`` map. The NAICS4 codes in
this bucket — Finance, Real Estate, professional services (legal /
accounting / consulting), government administration, civic & religious
orgs, arts venues — were intentionally dropped from CTE scope during the
SWP sector re-baseline (commit f50bc38). Employers scraped under those
codes remain in ``employers.json`` only as legacy artifacts; they do not
fit any SWP sector and cannot be surfaced as partnership candidates in a
CTE-aligned product.

Identification mirrors ``retag_sectors.py``:

  * Walk cache files, build canonical-key → NAICS4 index.
  * For each employer where ``swp_sectors`` is empty, recover NAICS4.
  * Drop iff every recovered NAICS4 is absent from ``CTE_NAICS_CODES``.

Employers with empty ``swp_sectors`` whose NAICS4 is unrecoverable
(Bucket C: name drift or absent from cache) are left untouched — they
need a different remediation path (improved matching, manual tagging).
Employers with populated ``swp_sectors`` are never touched.

Usage::

    python3 -m employers.drop_out_of_scope --dry-run
    python3 -m employers.drop_out_of_scope
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter

from employers.retag_sectors import (
    EMPLOYERS_PATH,
    _build_canonical_key_index,
    _filter_substring_candidates,
    _retag_key,
    recover_naics4_set,
)

logger = logging.getLogger(__name__)


def drop_out_of_scope(dry_run: bool = False) -> dict:
    from employers.edd_scrape import CTE_NAICS_CODES

    index = _build_canonical_key_index()
    substring_candidates = _filter_substring_candidates(index)

    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    kept: list[dict] = []
    dropped: list[tuple[dict, set[str]]] = []

    for emp in employers:
        if emp.get("swp_sectors"):
            kept.append(emp)
            continue
        key = _retag_key(emp["name"])
        naics_set, _ = recover_naics4_set(
            key, index, substring_candidates, CTE_NAICS_CODES
        )
        if not naics_set:
            kept.append(emp)
            continue
        if any(n4 in CTE_NAICS_CODES for n4 in naics_set):
            kept.append(emp)
            continue
        dropped.append((emp, naics_set))

    dropped_naics = Counter()
    for _, naics_set in dropped:
        for n4 in naics_set:
            dropped_naics[n4] += 1

    stats = {
        "before": len(employers),
        "after": len(kept),
        "dropped": len(dropped),
        "dropped_by_naics4": dict(dropped_naics.most_common()),
    }

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(kept, f, indent=2)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop out-of-SWP-scope employers")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = drop_out_of_scope(dry_run=args.dry_run)

    print("=" * 60)
    print("OUT-OF-SCOPE DROP RESULTS")
    print("=" * 60)
    print(f"  before:   {stats['before']}")
    print(f"  after:    {stats['after']}")
    print(f"  dropped:  {stats['dropped']}")
    print()
    print("  NAICS4 dropped (count):")
    for n4, n in stats["dropped_by_naics4"].items():
        print(f"    {n4}  {n:4d}")
    if args.dry_run:
        print()
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
