"""One-shot: backfill Course.is_cte on existing nodes for the featured colleges.

The loader at courses/load.py now sets is_cte alongside top_code on every
ingested course. This script applies the same derivation to courses that
were loaded before is_cte existed — no need to re-run the full course
ingestion pipeline. Idempotent: re-running produces the same property
state.

Source of truth: the PCAH (Program and Course Approval Handbook) "TOP
Codes to Sectors" file at backend/ontology/data/. See
ontology.crosswalks.is_cte_top6.

Usage:
    cd backend && python -m courses.backfill_is_cte
"""

from __future__ import annotations

import logging

from ontology.crosswalks import is_cte_top6
from ontology.schema import get_driver

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


# The 8 colleges surfaced in preview mode (atlas/state-atlas/featuredColleges.ts).
# Names here match the College.name property in Neo4j.
FEATURED_COLLEGES = [
    "Shasta College",
    "Foothill College",
    "College of the Sequoias",
    "Oxnard College",
    "Compton College",
    "Irvine Valley College",
    "College of the Desert",
    "San Diego City College",
]


def backfill_college(driver, college: str) -> tuple[int, int]:
    """Backfill is_cte for every Course at this college.

    Returns (cte_count, total_count).
    """
    with driver.session() as session:
        records = session.run(
            "MATCH (c:Course {college: $college}) "
            "RETURN c.code AS code, c.top_code AS top_code",
            college=college,
        ).data()

        updates = [
            {"code": r["code"], "is_cte": is_cte_top6(r.get("top_code"))}
            for r in records
        ]

        if updates:
            session.run(
                "UNWIND $batch AS row "
                "MATCH (c:Course {code: row.code, college: $college}) "
                "SET c.is_cte = row.is_cte",
                batch=updates,
                college=college,
            )

        cte_count = sum(1 for u in updates if u["is_cte"])
        return cte_count, len(updates)


def main() -> None:
    driver = get_driver()
    print(f"Backfilling Course.is_cte for {len(FEATURED_COLLEGES)} featured colleges\n")
    grand_cte = 0
    grand_total = 0
    for college in FEATURED_COLLEGES:
        cte, total = backfill_college(driver, college)
        pct = (cte / total * 100) if total else 0
        print(f"  {college:30s}  {cte:4d} CTE / {total:4d} total  ({pct:.0f}%)")
        grand_cte += cte
        grand_total += total
    print(f"\nTotal: {grand_cte}/{grand_total} courses tagged is_cte=true "
          f"({grand_cte / grand_total * 100:.0f}%)")


if __name__ == "__main__":
    main()
