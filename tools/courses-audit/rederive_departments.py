"""Re-derive Course.department on every existing Course node from its
top_code via the Chancellor's Office Taxonomy of Programs Manual.

Runs after the architectural pivot from per-college overlays to the
manual-grounded TOP4 → name table (`backend/ontology/data/top4_names.json`).
This script does NOT re-scrape; it reads top_code values already in Neo4j
and writes new department values + Department nodes + CONTAINS edges,
then sweeps stale CONTAINS edges and orphan Department nodes.

Usage:
    docker exec kallipolis-backend-1 python /tmp/rederive_departments.py
    docker exec kallipolis-backend-1 python /tmp/rederive_departments.py --college sbcc
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Detect in-container vs in-repo layout.
BACKEND = Path("/app") if Path("/app/ontology").is_dir() else Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from neo4j import GraphDatabase  # noqa: E402

from ontology.crosswalks import top_to_department_name  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rederive")

NEO4J_URI = "bolt://kallipolis-neo4j-1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "kallipolis_dev"

COLLEGES = [
    "Shasta College", "College of the Siskiyous", "Lassen College",
    "Mendocino College", "Butte College", "Sacramento City College",
    "Lake Tahoe Community College", "Foothill College",
    "Berkeley City College", "Napa Valley College", "Hartnell College",
    "College of the Sequoias", "Merced College",
    "Cerro Coso Community College", "Santa Barbara City College",
    "Oxnard College", "Compton College", "Los Angeles Valley College",
    "Irvine Valley College", "College of the Desert",
    "San Diego City College", "Imperial Valley College",
]


def rederive_for(driver, college: str) -> dict:
    """Re-derive Course.department for one college and re-stitch
    Department nodes + edges. Returns stats."""
    with driver.session() as s:
        rows = s.run(
            "MATCH (c:Course {college: $col}) "
            "RETURN c.code AS code, c.top_code AS top_code, "
            "c.department AS old_dept",
            col=college,
        ).data()
        if not rows:
            return {"college": college, "skipped": "no Course nodes"}

        # Compute new department per course
        updates = []
        for r in rows:
            new_dept = top_to_department_name(r["top_code"]) or ""
            updates.append({
                "code": r["code"],
                "department": new_dept,
            })

        # Apply Course.department updates in a single UNWIND
        s.run(
            """
            UNWIND $batch AS row
            MATCH (c:Course {code: row.code, college: $col})
            SET c.department = row.department
            """,
            batch=updates, col=college,
        )

        # Create the Department nodes that we now need
        new_depts = sorted({u["department"] for u in updates if u["department"]})
        for d in new_depts:
            s.run(
                """
                MATCH (col:College {name: $col})
                MERGE (d:Department {name: $d})
                MERGE (col)-[:OFFERS]->(d)
                """,
                col=college, d=d,
            )

        # MERGE CONTAINS edges from each Department to its Courses
        s.run(
            """
            MATCH (c:Course {college: $col})
            WHERE c.department IS NOT NULL AND c.department <> ''
            MATCH (d:Department {name: c.department})
            MERGE (d)-[:CONTAINS]->(c)
            """,
            col=college,
        )

        # Drop stale CONTAINS edges (Department.name != Course.department)
        stale_contains = s.run(
            """
            MATCH (col:College {name: $col})
            MATCH (c:Course {college: col.name})
            MATCH (d:Department)-[rel:CONTAINS]->(c)
            WHERE d.name <> c.department OR c.department IS NULL OR c.department = ''
            DELETE rel
            RETURN count(rel) AS n
            """,
            col=college,
        ).single()["n"]

        # Drop OFFERS edges to departments that no longer have courses
        # for this college
        stale_offers = s.run(
            """
            MATCH (col:College {name: $col})-[rel:OFFERS]->(d:Department)
            WHERE NOT EXISTS { MATCH (d)-[:CONTAINS]->(:Course {college: col.name}) }
            DELETE rel
            RETURN count(rel) AS n
            """,
            col=college,
        ).single()["n"]

        # Stats
        depts_after = s.run(
            """
            MATCH (d:Department)-[:CONTAINS]->(c:Course {college: $col})
            WHERE c.top_code IS NOT NULL AND c.top_code <> ''
            RETURN count(DISTINCT d) AS n
            """,
            col=college,
        ).single()["n"]

    return {
        "college": college,
        "courses": len(rows),
        "departments_after": depts_after,
        "stale_contains_dropped": stale_contains,
        "stale_offers_dropped": stale_offers,
    }


def cleanup_orphans(driver) -> int:
    with driver.session() as s:
        r = s.run(
            "MATCH (d:Department) "
            "WHERE NOT (d)-[:CONTAINS]->(:Course) "
            "DETACH DELETE d "
            "RETURN count(d) AS n"
        ).single()
        return r["n"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--college", help="single college name (e.g., 'Foothill College')")
    args = ap.parse_args()

    targets = [args.college] if args.college else COLLEGES
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print(f"{'college':35s} {'courses':>8s} {'depts':>6s} {'stale-CONTAINS':>14s} {'stale-OFFERS':>13s}")
    print("-" * 90)
    for col in targets:
        s = rederive_for(driver, col)
        if "skipped" in s:
            print(f"{col:35s} (skipped: {s['skipped']})")
            continue
        print(f"{col:35s} {s['courses']:>8d} {s['departments_after']:>6d} "
              f"{s['stale_contains_dropped']:>14d} {s['stale_offers_dropped']:>13d}")

    orphans = cleanup_orphans(driver)
    print(f"\nOrphan Department nodes removed (global sweep): {orphans}")
    driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
