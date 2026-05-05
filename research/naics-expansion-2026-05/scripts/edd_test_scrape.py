"""Test EDD presence for high-priority missing NAICS-4 codes.

Targets the Bay region (Santa Clara county) at F+ size floor (100+
employees) — the production scrape's settings — for the priority
missing NAICS identified by the audit.

Reports per-NAICS employer counts and 5 sample names so we can
validate whether EDD has data we can absorb into the search list.
"""

from __future__ import annotations

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")

from employers.edd_scrape import search_naics_codes

PRIORITY_MISSING = [
    "9991",  # Federal Executive Branch
    "9992",  # State Government, excluding Schools and Hospitals
    "9993",  # Local Government, excluding Schools and Hospitals
    "8112",  # Electronic and Precision Equipment Repair
    "8113",  # Commercial and Industrial Machinery Repair
    "8114",  # Personal and Household Goods Repair
    "5411",  # Legal Services
    "5241",  # Insurance Carriers
]


def main() -> None:
    county = sys.argv[1] if len(sys.argv) > 1 else "Santa Clara"
    print(f"\n=== EDD Test Scrape — {county} County, F+ size ===\n")
    for naics in PRIORITY_MISSING:
        print(f"\n--- NAICS {naics} ---")
        try:
            results = search_naics_codes(
                county_name=county,
                naics_codes=[naics],
                min_size="F",
                max_pages_per_code=3,
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        print(f"  Total employers found: {len(results)}")
        for r in results[:8]:
            name = r.get("name") or r.get("business_name") or "(no name)"
            size = r.get("size") or r.get("employee_size") or "?"
            print(f"    [{size}] {name}")


if __name__ == "__main__":
    main()
