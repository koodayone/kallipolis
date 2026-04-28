"""Promote shadow enrichment fields to canonical fields for verified employers.

After enrich.py populates _description / _occupations / _swp_sector on
verified employers, this script promotes those values to the canonical
fields that load.py reads:
    _description  → description
    _occupations  → occupations
    _swp_sector   → swp_sectors[0]

Operates only on employers with identity_verified=True AND all three
shadow fields populated. Other employers are left untouched — including
deferred employers (enrichment_attempted=True without identity_verified)
which keep their existing canonical fields but will be excluded from
Neo4j load by load.py's strict filter.

Usage:
    python3 -m employers.cutover --dry-run
    python3 -m employers.cutover
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EMPLOYERS_PATH = Path(__file__).parent / "employers.json"

_SHADOW_FIELDS = ("_description", "_occupations", "_swp_sector")


def cutover(dry_run: bool = False) -> dict:
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    promoted = 0
    skipped_unverified = 0
    skipped_partial_shadow = 0

    for e in employers:
        if not e.get("identity_verified"):
            skipped_unverified += 1
            continue
        desc = e.get("_description")
        occs = e.get("_occupations")
        sect = e.get("_swp_sector")
        if not (desc and occs and sect):
            skipped_partial_shadow += 1
            continue
        # Promote shadow → canonical.
        e["description"] = desc
        e["occupations"] = list(occs)
        e["swp_sectors"] = [sect]
        # Mark this employer as fully promoted by THIS enrichment cycle.
        # load.py requires this flag for any enrichment_attempted employer
        # — it's how we distinguish "verified but cutover skipped (shadow
        # incomplete)" from "verified and fully promoted." The former
        # would still have stale OLD canonical fields; we don't want to
        # ship those.
        e["enrichment_promoted"] = True
        # Drop shadow fields — they served their A/B purpose, no longer needed.
        for f in _SHADOW_FIELDS:
            e.pop(f, None)
        promoted += 1

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(employers, f, indent=2)

    return {
        "total": len(employers),
        "promoted": promoted,
        "skipped_unverified": skipped_unverified,
        "skipped_partial_shadow": skipped_partial_shadow,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote shadow enrichment fields to canonical fields."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Report counts without modifying employers.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = cutover(dry_run=args.dry_run)

    print("=" * 60)
    print("CUTOVER COMPLETE" if not args.dry_run else "CUTOVER (dry run)")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:28s}  {v}")


if __name__ == "__main__":
    main()
