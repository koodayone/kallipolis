"""Test EDD presence in CVML region (Fresno county) for ALL missing
NAICS-4 codes identified by the audit. Reports count + sample per
NAICS so we can assess the composition of employers a methodology
expansion would surface.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from collections import defaultdict
from neo4j import GraphDatabase
import os

from ontology import oes as _oes
from employers.edd_scrape import search_naics_codes, CTE_NAICS_CODES


def _load_missing_naics() -> list[str]:
    _oes._ensure_loaded()
    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        cte_socs = session.run(
            "MATCH (o:Occupation) RETURN o.soc_code AS soc"
        ).data()
    driver.close()

    missing: set[str] = set()
    for r in cte_socs:
        for naics, _ in soc_to_naics.get(r["soc"], [])[:5]:
            if naics not in CTE_NAICS_CODES:
                missing.add(naics)
    return sorted(missing)


def main() -> None:
    county = sys.argv[1] if len(sys.argv) > 1 else "Fresno"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/app/cvml_scrape_results.json"
    min_size = sys.argv[3] if len(sys.argv) > 3 else "F"
    missing = _load_missing_naics()
    logger.info(f"Scraping {len(missing)} missing NAICS codes in {county} "
                f"at size {min_size}+")

    results: dict[str, dict] = {}
    for i, naics in enumerate(missing, 1):
        t0 = time.time()
        try:
            employers = search_naics_codes(
                county_name=county,
                naics_codes=[naics],
                min_size=min_size,
                max_pages_per_code=3,
            )
        except Exception as e:
            results[naics] = {"error": str(e), "count": 0, "sample": []}
            logger.warning(f"[{i}/{len(missing)}] {naics}: ERROR {e}")
            continue
        sample = [e.get("name") or e.get("business_name", "?")
                  for e in employers[:8]]
        results[naics] = {
            "count": len(employers),
            "sample": sample,
        }
        logger.info(f"[{i}/{len(missing)}] {naics}: {len(employers)} employers "
                    f"({time.time()-t0:.1f}s)")
        # Incremental save so partial results survive interrupts.
        if i % 5 == 0:
            Path(out_path).write_text(json.dumps(results, indent=2))

    Path(out_path).write_text(json.dumps(results, indent=2))
    logger.info(f"Wrote {out_path}")
    nonzero = sum(1 for v in results.values() if v.get("count", 0) > 0)
    total_emp = sum(v.get("count", 0) for v in results.values())
    logger.info(f"Summary: {nonzero}/{len(missing)} NAICS returned ≥1 employer; "
                f"{total_emp} total employers across all missing NAICS")


if __name__ == "__main__":
    main()
