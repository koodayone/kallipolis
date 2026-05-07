"""Snapshot + restore the durable subgraph (Employer / Occupation /
Skill / Region / LaborMarketRegion) so we can wipe Neo4j without
losing the expensive-to-rebuild data.

Why: regional employer scraping costs hours per region; reloading
from a local JSON snapshot is seconds. This script makes the data
movable so we can nuke + reload the database to clean out students
and PDF courses fast.

Usage:
    python scripts/snapshot_subgraph.py dump   --out /tmp/subgraph.json
    python scripts/snapshot_subgraph.py reload --in  /tmp/subgraph.json

Connects via NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD env vars.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("snapshot_subgraph")

# Node labels we preserve. Everything else (Student, College, Department,
# Course) gets recreated by downstream loaders.
LABELS = ["Employer", "Occupation", "Skill", "Region", "LaborMarketRegion"]

# Relationship types we preserve (only those connecting the labels above).
EDGE_TYPES = [
    "HIRES_FOR",            # Employer -> Occupation
    "IDENTITY_HIRES_FOR",   # Employer -> Occupation
    "IN_MARKET",            # Employer -> Region
    "REQUIRES_SKILL",       # Occupation -> Skill
    "OCCUPATION_PIPELINE",  # Occupation -> Occupation
    "DEMANDS",              # Region -> Occupation (or similar)
    "LOCATED_IN",           # Region -> LaborMarketRegion (or similar)
    # HAS_SKILL is excluded because most are Student->Skill (gone) and
    # Course->Skill (gone). Employer->Skill is rare; if you need it,
    # add it back here and re-run.
]


def dump(driver, out_path: Path) -> None:
    snapshot: dict = {"nodes": {}, "edges": {}}

    with driver.session() as session:
        # Dump nodes per label.
        for label in LABELS:
            result = session.run(
                f"MATCH (n:{label}) RETURN id(n) AS nid, properties(n) AS props"
            )
            nodes = [{"id": r["nid"], "props": r["props"]} for r in result]
            snapshot["nodes"][label] = nodes
            logger.info(f"  dumped {len(nodes):,} {label} nodes")

        # Dump edges per type, only those whose endpoints are both in
        # our preserved label set.
        labels_set = "|".join(LABELS)
        for etype in EDGE_TYPES:
            q = (
                f"MATCH (a)-[r:{etype}]->(b) "
                f"WHERE any(l IN labels(a) WHERE l IN $labels) "
                f"  AND any(l IN labels(b) WHERE l IN $labels) "
                f"RETURN id(a) AS src, id(b) AS dst, "
                f"  labels(a) AS src_labels, labels(b) AS dst_labels, "
                f"  properties(r) AS props"
            )
            result = session.run(q, labels=LABELS)
            edges = [
                {
                    "src": r["src"], "dst": r["dst"],
                    "src_label": r["src_labels"][0],
                    "dst_label": r["dst_labels"][0],
                    "props": r["props"],
                }
                for r in result
            ]
            snapshot["edges"][etype] = edges
            logger.info(f"  dumped {len(edges):,} {etype} edges")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=None, separators=(",", ":")))
    logger.info(f"Wrote snapshot to {out_path} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")


def reload(driver, in_path: Path) -> None:
    snapshot = json.loads(in_path.read_text())

    # We need to map old neo4j-internal IDs to new ones as we recreate.
    id_map: dict[int, int] = {}

    with driver.session() as session:
        # Recreate nodes per label. Use a stable property as the key
        # where possible (name for Employer/Region, code for Occupation/
        # Skill if present), and store the old id in a transient
        # `_old_id` property so edge linking can find them. We strip
        # _old_id at the end.
        for label, nodes in snapshot["nodes"].items():
            if not nodes:
                continue
            session.run(
                f"UNWIND $nodes AS n "
                f"CREATE (x:{label}) "
                f"SET x = n.props, x._old_id = n.id",
                nodes=nodes,
            )
            logger.info(f"  recreated {len(nodes):,} {label} nodes")

        # Build the id_map by querying back the new internal ids.
        for label in LABELS:
            result = session.run(f"MATCH (n:{label}) RETURN id(n) AS new_id, n._old_id AS old_id")
            for r in result:
                id_map[r["old_id"]] = r["new_id"]
        logger.info(f"  built id_map: {len(id_map):,} entries")

        # Recreate edges using id_map. We have to do this per type so
        # we can use the relationship label cleanly.
        edge_counts = Counter()
        for etype, edges in snapshot["edges"].items():
            if not edges:
                continue
            payload = [
                {
                    "src_new": id_map.get(e["src"]),
                    "dst_new": id_map.get(e["dst"]),
                    "props": e["props"],
                }
                for e in edges
                if id_map.get(e["src"]) is not None and id_map.get(e["dst"]) is not None
            ]
            if not payload:
                continue
            session.run(
                f"UNWIND $payload AS p "
                f"MATCH (a) WHERE id(a) = p.src_new "
                f"MATCH (b) WHERE id(b) = p.dst_new "
                f"CREATE (a)-[r:{etype}]->(b) "
                f"SET r = p.props",
                payload=payload,
            )
            edge_counts[etype] = len(payload)
            logger.info(f"  recreated {len(payload):,} {etype} edges")

        # Strip the transient _old_id property.
        session.run("MATCH (n) WHERE n._old_id IS NOT NULL REMOVE n._old_id")
        logger.info("  stripped _old_id markers")

    logger.info(f"Reload complete. Edge totals: {dict(edge_counts)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_dump = sub.add_parser("dump")
    p_dump.add_argument("--out", type=Path, required=True)
    p_reload = sub.add_parser("reload")
    p_reload.add_argument("--in", dest="in_path", type=Path, required=True)
    args = parser.parse_args()

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not pwd:
        logger.error("NEO4J_PASSWORD not set")
        return 1
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    try:
        if args.cmd == "dump":
            dump(driver, args.out)
        else:
            reload(driver, args.in_path)
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
