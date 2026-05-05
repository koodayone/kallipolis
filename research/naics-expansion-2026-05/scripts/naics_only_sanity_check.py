"""NAICS-only expansion sanity check (no size change).

Scrapes ONLY the 128 newly-added NAICS at F+ size in San Diego, then
groups new employers by SWP sector with sample names. Shows the
strategic CTE coverage gain without the size-adjustment density gain.
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

from neo4j import GraphDatabase

from employers.edd_scrape import CTE_NAICS_CODES, search_naics_codes

# The 128 NAICS added by the methodology expansion (auto-classified +
# Public Admin + OEWS gov't aggregates). These are the codes whose
# expansion impact we want to assess at F+ size.
EXPANSION_NAICS = [
    "1133", "2121", "2122", "2123", "2131", "2372", "3112", "3113", "3122",
    "3132", "3133", "3149", "3151", "3152", "3161", "3221", "3222", "3270",
    "3311", "3312", "3313", "3314", "3315", "3333", "3336", "3342", "3343",
    "3346", "3352", "3353", "3359", "3362", "3365", "3369", "3379", "3399",
    "4238", "4243", "4251", "4412", "4413", "4442", "4453", "4491", "4492",
    "4550", "4561", "4571", "4572", "4581", "4582", "4591", "4592", "4593",
    "4599", "4812", "4821", "4831", "4832", "4840", "4852", "4855", "4861",
    "4862", "4869", "4871", "4872", "4879", "4882", "4883", "4884", "4885",
    "4889", "4911", "4922", "5131", "5132", "5161", "5162", "5170", "5192",
    "5211", "5222", "5230", "5241", "5242", "5251", "5259", "5310", "5321",
    "5331", "5411", "5419", "5511", "5611", "5612", "5613", "5614", "5615",
    "5619", "5629", "6239", "7111", "7112", "7113", "7114", "7115", "7121",
    "7132", "7213", "8112", "8113", "8114", "8122", "8129", "8131", "8132",
    "8133", "8134", "8139", "9211", "9231", "9251", "9261", "9281", "9991",
    "9992", "9993",
]


def main() -> None:
    print(f"=== NAICS-only sanity check (F+ size) ===")
    print(f"Scraping {len(EXPANSION_NAICS)} new NAICS at F+ in San Diego county")

    # Get baseline employers in SD/I region from graph
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        existing = session.run(
            "MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: 'SD/I'}) "
            "RETURN e.name AS name"
        ).data()
    driver.close()
    existing_names = {e["name"].strip().lower() for e in existing}
    print(f"Baseline SD/I employers in graph: {len(existing)}\n")

    by_naics: dict[str, list[str]] = {}
    new_by_sector: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total_new = 0
    distinct_new: set[str] = set()

    for i, naics in enumerate(EXPANSION_NAICS, 1):
        try:
            emps = search_naics_codes("San Diego", [naics],
                                       min_size="F", max_pages_per_code=3)
        except Exception:
            by_naics[naics] = []
            continue
        names = [(e.get("name") or "?").strip() for e in emps]
        by_naics[naics] = names
        sectors = CTE_NAICS_CODES.get(naics, ("", "", []))[2]
        for name in names:
            if name.lower().strip() in existing_names:
                continue
            distinct_new.add(name.lower().strip())
            total_new += 1
            for sector in sectors:
                new_by_sector[sector].append((name, naics))

    Path("/app/naics_only_results.json").write_text(json.dumps(by_naics, indent=2))

    nonzero = sum(1 for v in by_naics.values() if v)
    print(f"NAICS with ≥1 employer at F+: {nonzero}/{len(EXPANSION_NAICS)}")
    print(f"Distinct NEW employers (not in baseline): {len(distinct_new)}\n")

    print(f"=== New employers by SWP sector (multi-tag counted per sector) ===\n")
    for sector in sorted(new_by_sector.keys(),
                         key=lambda s: -len(new_by_sector[s])):
        emps = new_by_sector[sector]
        # dedupe within sector
        seen = set()
        deduped = []
        for name, naics in emps:
            k = name.lower().strip()
            if k in seen: continue
            seen.add(k)
            deduped.append((name, naics))
        print(f"### {sector} — {len(deduped)} new employers")
        for name, naics in deduped[:15]:
            label = CTE_NAICS_CODES.get(naics, ("", "(?)",))[1]
            print(f"  - {name}  [NAICS {naics} {label[:55]}]")
        if len(deduped) > 15:
            print(f"  ... and {len(deduped) - 15} more")
        print()


if __name__ == "__main__":
    main()
