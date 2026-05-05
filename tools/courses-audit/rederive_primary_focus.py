"""Re-derive Student.primary_focus from Student.primary_top6 using the
TOP4 manual lookup, replacing the stale overlay-derived values that
predate the TOP4 architectural pivot.

Background: pre-pivot, `primary_focus` was the catalog-overlay department
name of the courses a student concentrated in (e.g.,
"Computer Information Systems", "Air Conditioning, Refrigeration, and
Environmental Control Technology"). After the pivot, Course.department
is the TOP4 program name from cc-top-code-manual.pdf (e.g.,
"Computer Software Development", "Refrigeration and Air Conditioning").
The two are different strings for the same concept, so existing
Student.primary_focus values no longer match any current Department node
— ~62% of students in the graph today.

This script reads each Student's primary_top6 (still authoritative) and
writes a fresh primary_focus from the same manual table the courses
loader uses, so Student.primary_focus matches Course.department
post-pivot. No student regeneration; pure metadata rewrite.

Usage:
    docker exec kallipolis-backend-1 python /tmp/rederive_primary_focus.py
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# In-container vs in-repo path detection (mirrors rederive_departments.py).
BACKEND = Path("/app") if Path("/app/ontology").is_dir() else Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from neo4j import GraphDatabase  # noqa: E402

from ontology.crosswalks import top_to_department_name  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rederive_pf")

NEO4J_URI = "bolt://kallipolis-neo4j-1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "kallipolis_dev"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change but don't write")
    args = ap.parse_args()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as s:
        # Pull every Student that has a primary_top6 to derive from.
        rows = s.run("""
            MATCH (st:Student)
            WHERE st.primary_top6 IS NOT NULL AND st.primary_top6 <> ''
            RETURN st.uuid AS uuid, st.primary_top6 AS top6,
                   st.primary_focus AS old_pf
        """).data()

    total = len(rows)
    if total == 0:
        logger.warning("No Student nodes with primary_top6. Nothing to do.")
        return 0

    # Compute the new primary_focus value per student.
    updates: list[dict] = []
    unchanged_with = no_change = no_match = 0
    drift_buckets: dict[tuple[str, str], int] = {}
    for r in rows:
        new_pf = top_to_department_name(r["top6"])
        old_pf = r["old_pf"] or ""
        if not new_pf:
            no_match += 1
            continue
        if new_pf == old_pf:
            no_change += 1
            continue
        updates.append({"uuid": r["uuid"], "primary_focus": new_pf})
        drift_buckets[(old_pf, new_pf)] = drift_buckets.get((old_pf, new_pf), 0) + 1
        unchanged_with += 1

    print(f"Students total: {total}")
    print(f"  no primary_top6 in TOP4 manual:   {no_match}")
    print(f"  primary_focus already correct:    {no_change}")
    print(f"  primary_focus updated:            {len(updates)}")
    print()
    print("Top 15 drift buckets (old_pf → new_pf, count):")
    for (old, new), n in sorted(drift_buckets.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:>6d}  {old!r:50s} → {new!r}")

    if args.dry_run or not updates:
        print("\n(dry-run — no writes)")
        driver.close()
        return 0

    # Apply updates in chunks. Each batch UNWINDs and SETs primary_focus.
    CHUNK = 500
    written = 0
    with driver.session() as s:
        for i in range(0, len(updates), CHUNK):
            batch = updates[i:i + CHUNK]
            s.run("""
                UNWIND $batch AS row
                MATCH (st:Student {uuid: row.uuid})
                SET st.primary_focus = row.primary_focus
            """, batch=batch)
            written += len(batch)
    print(f"\nWrote {written} primary_focus updates.")
    driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
