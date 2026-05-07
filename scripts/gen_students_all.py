"""Drive synthetic student generation across every college that has
courses loaded from CourseDetails.

For each college key in catalog_sources.json:
  1. Look up canonical College.name (matches Course.college in Neo4j)
  2. Query Neo4j for that college's courses (Data Mart-loaded)
  3. Call students.generate.generate_and_load_students with the college
     key, the course list, and the canonical name.

This replaces the old `pipeline/run.py --college X --generate-students`
flow for the student-gen step. It does NOT run curriculum extraction
(courses are already loaded statewide by courses.load_from_coursedetails).

Usage:
    python scripts/gen_students_all.py                 # all colleges
    python scripts/gen_students_all.py --college deanza  # one college
    python scripts/gen_students_all.py --skip-existing  # skip colleges that already have students
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Make backend modules importable.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from neo4j import GraphDatabase

from students.generate import generate_and_load_students  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gen_students_all")

CATALOG_SOURCES = REPO_ROOT / "backend" / "pipeline" / "catalog_sources.json"


def load_college_keys() -> list[tuple[str, str]]:
    """Return [(college_key, canonical_name), ...] from catalog_sources.json."""
    with CATALOG_SOURCES.open() as fh:
        data = json.load(fh)
    items = data.get("colleges", {})
    return [(k, v.get("name", "")) for k, v in items.items() if v.get("name")]


def fetch_courses_for_college(driver, canonical_name: str) -> list[dict]:
    """Pull all Data Mart-loaded courses for a college as dicts in the
    shape generate_students expects: {code, name, top_code, units, ...}."""
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Course {college: $college})
            RETURN c.code AS code, c.name AS name, c.top_code AS top_code,
                   c.sam_code AS sam_code, c.department AS department,
                   c.units_min AS units_min, c.units_max AS units_max,
                   c.transfer_status AS transfer_status,
                   c.credit_status AS credit_status,
                   c.sections_count AS sections_count
            ORDER BY c.code
            """,
            college=canonical_name,
        )
        out = []
        for r in result:
            units = r["units_max"] or r["units_min"] or 3.0
            out.append({
                "code": r["code"],
                "name": r["name"],
                "top_code": r["top_code"] or "",
                "sam_code": r["sam_code"] or "",
                "department": r["department"] or "",
                "units": str(units) if units else "3",
                "transfer_status": r["transfer_status"] or "",
                "credit_status": r["credit_status"] or "",
                "sections_count": r["sections_count"] or 0,
                # Fields the old pipeline supplied that we don't have:
                "description": "",
                "prerequisites": "",
                "learning_outcomes": [],
                "course_objectives": [],
                "url": "",
            })
        return out


def already_has_students(driver, canonical_name: str) -> int:
    with driver.session() as session:
        rec = session.run(
            "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {college: $college}) "
            "RETURN count(DISTINCT s) AS n",
            college=canonical_name,
        ).single()
        return rec["n"] if rec else 0


def run_one(driver, college_key: str, canonical_name: str, num_students: int | None, seed: int) -> dict:
    courses = fetch_courses_for_college(driver, canonical_name)
    if not courses:
        return {"college_key": college_key, "status": "skipped_no_courses"}

    t0 = time.time()
    try:
        stats = generate_and_load_students(
            college_key=college_key,
            courses=courses,
            institution_name=canonical_name,
            driver=driver,
            num_students=num_students,
            seed=seed,
        )
        return {
            "college_key": college_key,
            "canonical": canonical_name,
            "status": "ok",
            "n_courses": len(courses),
            "students_generated": stats.students_generated,
            "enrollments_created": stats.enrollments_created,
            "elapsed_sec": round(time.time() - t0, 1),
        }
    except Exception as e:
        return {
            "college_key": college_key,
            "canonical": canonical_name,
            "status": "error",
            "error": f"{type(e).__name__}: {e}",
            "elapsed_sec": round(time.time() - t0, 1),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--college", help="One college key only (smoke test)")
    parser.add_argument("--num-students", type=int, default=None,
                        help="Override student count (default: from calibration or 3000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip colleges that already have students")
    args = parser.parse_args()

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not pwd:
        logger.error("NEO4J_PASSWORD not set")
        return 1
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    targets = load_college_keys()
    if args.college:
        targets = [(k, n) for k, n in targets if k == args.college]
        if not targets:
            logger.error(f"college key {args.college!r} not found in catalog_sources.json")
            return 1

    results = []
    try:
        for i, (key, name) in enumerate(targets, start=1):
            if args.skip_existing:
                existing = already_has_students(driver, name)
                if existing > 0:
                    logger.info(f"[{i}/{len(targets)}] SKIP {key} ({name}) — {existing:,} students already present")
                    results.append({"college_key": key, "status": "skipped_has_students", "students": existing})
                    continue
            logger.info(f"[{i}/{len(targets)}] {key} ({name}) — running")
            r = run_one(driver, key, name, args.num_students, args.seed)
            logger.info(f"  → {r}")
            results.append(r)
    finally:
        driver.close()

    # Summary
    ok = sum(1 for r in results if r.get("status") == "ok")
    err = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if r.get("status", "").startswith("skipped"))
    total_students = sum(r.get("students_generated", 0) for r in results)
    total_enrollments = sum(r.get("enrollments_created", 0) for r in results)
    logger.info("=" * 70)
    logger.info(f"Results: ok={ok}  error={err}  skipped={skipped}")
    logger.info(f"Total students generated: {total_students:,}")
    logger.info(f"Total enrollments:        {total_enrollments:,}")
    if err:
        logger.info(f"\nErrors:")
        for r in results:
            if r.get("status") == "error":
                logger.info(f"  {r['college_key']:<22} {r['error'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
