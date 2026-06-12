"""College → CCCCO district hierarchy.

The institutional grouping above a college and below a COE region: the CCCCO
district a college belongs to (Foothill College → Foothill-De Anza CCD). This is
the middle tier of the `college ⊂ district ⊂ region` member hierarchy the
aggregated-landscape engine rolls supply up over.

Authoritative source: `pipeline/catalog_sources.json`, the on-disk college
catalog that already carries the canonical district per college (115/115). The
edge is materialized as `(College)-[:IN_DISTRICT]->(District)` so the hierarchy
is Cypher-queryable — both for the member×sector landscape generator and for the
MCP layer that reasons over the graph.

Idempotent. `District` keys on `name` (the CCCCO district name as the catalog
spells it). `region` lives on the college side already (`COLLEGE_COE_REGION` /
the `IN_MARKET` edge); a district inherits its region from its colleges.
"""

from __future__ import annotations

import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parents[1] / "pipeline" / "catalog_sources.json"


def _catalog_rows() -> list[dict]:
    catalog = json.loads(_CATALOG_PATH.read_text())
    return [
        {"college": rec["name"], "district": rec["district"]}
        for rec in catalog["colleges"].values()
        if rec.get("name") and rec.get("district")
    ]


def load_college_districts(driver) -> int:
    """MERGE `(College)-[:IN_DISTRICT]->(District)` for every catalog college
    whose `College` node exists. Idempotent. Returns the number of (college,
    district) pairs applied from the catalog (a college absent from the graph is
    silently skipped by the MATCH — the count is the catalog size, not the edge
    count; verify edges separately)."""
    rows = _catalog_rows()
    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MATCH (c:College {name: row.college})
            MERGE (d:District {name: row.district})
            MERGE (c)-[:IN_DISTRICT]->(d)
            """,
            rows=rows,
        )
    return len(rows)
