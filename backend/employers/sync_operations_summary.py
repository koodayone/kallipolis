"""One-shot sync of ``operations_summary`` from employers.json to Neo4j.

Reads each employer's ``operations_summary`` from the JSON and writes it
to the matching Employer node via MATCH/SET. Does NOT touch any other
property and does NOT MERGE/CREATE missing nodes — it only updates
operations_summary on Employer nodes that already exist in the graph.

Use this when you've run ``employers.characterize`` to populate the
JSON and want the property reflected on already-loaded Employer nodes
without re-running the full load pipeline (which would also re-MERGE
descriptions, websites, IN_MARKET edges, HIRES_FOR edges, etc.).

Usage:
    python -m employers.sync_operations_summary
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ontology.schema import close_driver, get_driver

logger = logging.getLogger(__name__)

EMPLOYERS_PATH = Path(__file__).parent / "employers.json"


def sync() -> dict:
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    pairs = [
        {"name": e["name"], "operations_summary": e.get("operations_summary")}
        for e in employers
        if e.get("operations_summary")
    ]
    logger.info(
        f"Syncing operations_summary for {len(pairs)} employers (out of "
        f"{len(employers)} in employers.json)"
    )

    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                """
                UNWIND $pairs AS p
                MATCH (e:Employer {name: p.name})
                SET e.operations_summary = p.operations_summary
                RETURN count(e) AS updated
                """,
                pairs=pairs,
            )
            updated = result.single()["updated"]
    finally:
        close_driver()

    skipped = len(pairs) - updated
    logger.info(f"Updated {updated} Employer nodes; {skipped} not present in graph")
    return {"updated": updated, "skipped": skipped, "json_total": len(pairs)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = sync()
    print()
    for k, v in stats.items():
        print(f"  {k:14s}  {v}")
