"""Phase 4 staged validation: scrape SD county at E+ size with the
full extended CTE_NAICS_CODES (268 entries) and emit a validation
report. No write to graph — this is just a shape check.

Reports:
  - Employer count overall and per-NAICS
  - Sector distribution (via the new lookup)
  - Comparison to current SD/I employer pool (prior baseline)
  - Sample of newly-surfaced employers
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

from neo4j import GraphDatabase

from employers.edd_scrape import (
    CTE_NAICS_CODES, search_naics_codes, DEFAULT_MIN_SIZE,
)


def main() -> None:
    print(f"=== Phase 4 staged validation ===")
    print(f"CTE_NAICS_CODES: {len(CTE_NAICS_CODES)} entries")
    print(f"DEFAULT_MIN_SIZE: {DEFAULT_MIN_SIZE}")

    # Existing SD/I employers in graph for comparison.
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        existing = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: 'SD/I'})
            RETURN e.name AS name, e.naics4 AS naics4, e.swp_sectors AS sectors
            """
        ).data()
    driver.close()
    existing_names = {e["name"].strip().lower() for e in existing}
    print(f"\nBaseline SD/I employers in graph: {len(existing)}")

    # Scrape San Diego county at E+ for ALL CTE_NAICS_CODES.
    naics_list = sorted(CTE_NAICS_CODES.keys())
    print(f"Scraping San Diego county at E+ for {len(naics_list)} NAICS...")
    results: dict[str, list[str]] = {}
    new_count = 0
    for naics in naics_list:
        try:
            emps = search_naics_codes("San Diego", [naics],
                                       min_size="E", max_pages_per_code=3)
        except Exception as e:
            results[naics] = []
            continue
        names = [(e.get("name") or "?").strip() for e in emps]
        results[naics] = names

    Path("/app/staged_sd_results.json").write_text(json.dumps(results, indent=2))

    # Aggregate
    total_pairs = sum(len(v) for v in results.values())
    nonzero_naics = sum(1 for v in results.values() if v)
    all_emps = set()
    for v in results.values():
        for n in v:
            all_emps.add(n.lower().strip())
    new_emps = all_emps - existing_names

    # Per-sector counts via the lookup
    sector_count: Counter = Counter()
    for naics, emps in results.items():
        sectors = CTE_NAICS_CODES[naics][2]
        for sector in sectors:
            sector_count[sector] += len(emps)

    print(f"\n=== SD County scrape results at E+ ===")
    print(f"NAICS with >=1 employer: {nonzero_naics}/{len(naics_list)}")
    print(f"Total (NAICS, employer) pairs: {total_pairs}")
    print(f"Distinct employers: {len(all_emps)}")
    print(f"New employers (not in baseline): {len(new_emps)}")
    print(f"\nPer-SWP-sector employer counts (multi-sector tags counted per sector):")
    for sector, n in sector_count.most_common():
        print(f"  {n:>5}  {sector}")

    print(f"\nSample of 10 newly-surfaced employers:")
    new_emps_list = sorted(new_emps)
    for n in new_emps_list[:10]:
        print(f"  - {n}")
    print(f"\n(Wrote /app/staged_sd_results.json with full per-NAICS detail)")


if __name__ == "__main__":
    main()
