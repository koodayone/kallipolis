"""Full expanded-methodology scrape for one region.

Scrape every NAICS in the union of:
  - Existing CTE_NAICS_CODES (140)
  - Missing NAICS that appear as top-5 by pct_total for any direct-CTE
    SOC (~127)

At E+ size threshold (50+ employees). Output per-NAICS employer list
for downstream per-SOC aggregation.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

import csv
from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology import oes as _oes
from employers.edd_scrape import search_naics_codes, CTE_NAICS_CODES


def _direct_cte_socs() -> set[str]:
    """Strong CTE + Moderate CTE supported by at least one college."""
    direct = set()
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            edu = row.get("Typical Entry Level Education", "").strip()
            if edu in {"Postsecondary nondegree award", "Associate's degree",
                       "High school diploma or equivalent",
                       "Some college, no degree",
                       "No formal educational credential"}:
                direct.add(row["SOC"])
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        supported = session.run(
            "MATCH (:Course)-[:PREPARES_FOR]->(o:Occupation) "
            "RETURN DISTINCT o.soc_code AS soc"
        ).data()
    driver.close()
    return direct & {r["soc"] for r in supported}


def _build_union_naics(direct_socs: set[str]) -> list[str]:
    _oes._ensure_loaded()
    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    union = set(CTE_NAICS_CODES.keys())
    for soc in direct_socs:
        for naics, _ in soc_to_naics.get(soc, [])[:5]:
            union.add(naics)
    return sorted(union)


def main() -> None:
    county = sys.argv[1] if len(sys.argv) > 1 else "San Diego"
    out_path = sys.argv[2] if len(sys.argv) > 2 else f"/app/full_scrape_{county.replace(' ', '_')}.json"

    direct_socs = _direct_cte_socs()
    union = _build_union_naics(direct_socs)
    logger.info(f"Direct-CTE supported SOCs: {len(direct_socs)}")
    logger.info(f"Union NAICS to scrape: {len(union)}")
    logger.info(f"Scraping {county} at E+ size")

    results: dict[str, list[str]] = {}
    for i, naics in enumerate(union, 1):
        t0 = time.time()
        try:
            employers = search_naics_codes(
                county_name=county,
                naics_codes=[naics],
                min_size="E",
                max_pages_per_code=3,
            )
        except Exception as e:
            results[naics] = []
            logger.warning(f"[{i}/{len(union)}] {naics}: ERROR {e}")
            continue
        results[naics] = [(e.get("name") or "?").strip() for e in employers]
        logger.info(f"[{i}/{len(union)}] {naics}: {len(employers)} employers "
                    f"({time.time()-t0:.1f}s)")
        if i % 20 == 0:
            Path(out_path).write_text(json.dumps(results, indent=2))

    Path(out_path).write_text(json.dumps(results, indent=2))
    nonzero = sum(1 for v in results.values() if v)
    total = sum(len(v) for v in results.values())
    logger.info(f"Wrote {out_path}: {nonzero}/{len(union)} NAICS with employers, "
                f"{total} total")


if __name__ == "__main__":
    main()
