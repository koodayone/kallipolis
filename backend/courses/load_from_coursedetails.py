"""Statewide course-inventory loader sourced from the CCC Data Mart
Course Details report.

Replaces the per-catalog PDF extraction path for course nodes. The
upstream is `backend/ontology/coursedetails/CourseDetails_combined_*.csv`
produced by `courses.combine_course_details`, which itself is a clean
concatenation of the manually-exported Data Mart CSVs.

Why a separate module from courses.load:
  - load_college() is per-college, takes Gemini-extracted course dicts,
    and resolves TOP codes via MCF lookup. CourseDetails arrives
    statewide, already TOP-coded by the Chancellor's Office, with SAM
    classification and section counts the PDF path never had.
  - Keeping the modules separate preserves the old loader during
    migration and keeps each path's data lineage traceable end-to-end.

What this loader writes (idempotent via MERGE):
  (:College {name})
  (:Department {name})
  (:Course {code, college})  ← composite key, same as existing
  (:College)-[:OFFERS]->(:Department)
  (:Department)-[:CONTAINS]->(:Course)

Course node properties (sourced verbatim where possible; derived where
labeled):
  code, college                   — composite key, from CSV
  name                            — from "Course Title"
  top_code                        — 6-digit, parsed in combine step
  top_description                 — text portion of TOP Code
  sam_code                        — A/B/C/D/E from CB09 (single letter)
  is_cte                  derived — is_cte_top6(top_code)
  department              derived — top_to_department_name(top_code)
  units_min, units_max            — from "Minimum/Maximum Units"
  transfer_status                 — from "Transfer Status"
  credit_status                   — from "Credit Status"
  ge_status                       — from "General Education Status"
  sections_count                  — from "Sections Count" (int)
  term                            — from "Term" (e.g. "Fall 2025")
  control_number                  — institutional ID "CCC000nnnnnn"
                                    (joins to PCF for program affiliation)
  source                  literal — "data_mart_course_details"

Properties NOT set by this loader (preserved if previously written by
courses.load): description, prerequisites, learning_outcomes,
course_objectives, url, catalog_section. CourseDetails doesn't carry
these. A future enrichment pass through workforce-dev partners is the
intended source.

Usage (from backend container or local with API_DB env vars set):
    python -m courses.load_from_coursedetails
    python -m courses.load_from_coursedetails --csv path/to/CourseDetails_combined.csv
    python -m courses.load_from_coursedetails --college "Allan Hancock"  # subset for smoke test
    python -m courses.load_from_coursedetails --dry-run  # report only
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from neo4j import Driver, GraphDatabase

from ontology.crosswalks import is_cte_top6, top_to_department_name
from ontology.prepares_for import materialize_prepares_for
from ontology.regions import ensure_college_region_link

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_from_coursedetails")

# Path resolution works whether this is run from the repo root on the
# host (where `backend/` is a sibling) or from inside the backend
# container (where `/app` is the backend root). __file__.parent.parent
# is the backend directory in both cases.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = BACKEND_ROOT / "ontology" / "coursedetails" / "CourseDetails_combined_fall2025.csv"
DEFAULT_NAME_MAP = BACKEND_ROOT / "ontology" / "coursedetails" / "datamart_to_canonical.json"

SOURCE_TAG = "data_mart_course_details"


def load_name_mapping(path: Path) -> tuple[dict[str, str], set[str]]:
    """Read the Data Mart → canonical college name mapping. Returns
    (mapping, excluded_set). The excluded_set lists Data Mart names
    intentionally not loaded (e.g. continuing-ed entities)."""
    with path.open() as fh:
        data = json.load(fh)
    mapping = data.get("mapping", {})
    excluded = set(data.get("_excluded_from_load", []))
    return mapping, excluded


@dataclass
class LoadStats:
    rows_seen: int = 0
    rows_skipped: int = 0
    colleges_seen: set[str] = field(default_factory=set)
    courses_loaded: int = 0
    departments_created: int = 0
    contains_edges: int = 0
    offers_edges: int = 0
    sam_dist: Counter = field(default_factory=Counter)
    skipped_reasons: Counter = field(default_factory=Counter)


def _to_int(s: str) -> int | None:
    try:
        return int(s.strip())
    except (ValueError, AttributeError):
        return None


def _to_float(s: str) -> float | None:
    try:
        return float(s.strip())
    except (ValueError, AttributeError):
        return None


def load_csv(
    csv_path: Path,
    name_map: dict[str, str],
    excluded: set[str],
    college_filter: str | None = None,
) -> tuple[list[dict], Counter]:
    """Read the cleaned CourseDetails CSV, applying the Data Mart →
    canonical name mapping. Rows whose Data Mart college name is in
    `excluded` are skipped. Rows with a college not in `name_map` and
    not in `excluded` are also skipped (with a warning) — adding new
    colleges requires updating the mapping deliberately. Returns
    (rows, skip_counts)."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CourseDetails CSV not found at {csv_path}")
    rows: list[dict] = []
    skips: Counter = Counter()
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            dm_name = row.get("College", "").strip()
            if dm_name in excluded:
                skips["excluded_college"] += 1
                continue
            canonical = name_map.get(dm_name)
            if canonical is None:
                skips["unmapped_college"] += 1
                logger.warning(f"Unmapped college (skipping): {dm_name!r}")
                continue
            if college_filter and canonical != college_filter and dm_name != college_filter:
                continue
            row["_dm_college"] = dm_name
            row["College"] = canonical
            rows.append(row)
    return rows, skips


def load_into_neo4j(
    driver: Driver,
    rows: list[dict],
    dry_run: bool = False,
) -> LoadStats:
    """MERGE course inventory into Neo4j. Per-row MERGE keyed on
    (code, college). Departments derived from TOP code via the
    existing taxonomy crosswalk."""
    stats = LoadStats()

    # Ensure the constraint the existing loader relies on is in place.
    if not dry_run:
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT course_code_college IF NOT EXISTS "
                "FOR (c:Course) REQUIRE (c.code, c.college) IS UNIQUE"
            )

    # Group by college so we can write College/Department once per
    # college and stream Course writes inside.
    by_college: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        college = row.get("College", "").strip()
        if not college:
            stats.rows_skipped += 1
            stats.skipped_reasons["no_college"] += 1
            continue
        by_college[college].append(row)
        stats.rows_seen += 1
        stats.colleges_seen.add(college)
        stats.sam_dist[row.get("sam_code", "")] += 1

    for college, college_rows in by_college.items():
        # Pre-derive course records and the set of departments we need
        # before opening the session.
        records: list[dict] = []
        departments: set[str] = set()
        for r in college_rows:
            code = r.get("Course ID", "").strip()
            name = r.get("Course Title", "").strip()
            if not code or not name:
                stats.rows_skipped += 1
                stats.skipped_reasons["missing_code_or_title"] += 1
                continue
            top_code = r.get("top_code", "").strip()
            dept = top_to_department_name(top_code) or "" if top_code else ""
            if dept:
                departments.add(dept)
            records.append({
                "code": code,
                "college": college,
                "name": name,
                "top_code": top_code,
                "top_description": r.get("top_description", "").strip(),
                "sam_code": r.get("sam_code", "").strip(),
                "is_cte": is_cte_top6(top_code) if top_code else False,
                "department": dept,
                "units_min": _to_float(r.get("Minimum Units", "")) or 0.0,
                "units_max": _to_float(r.get("Maximum Units", "")) or 0.0,
                "transfer_status": r.get("Transfer Status", "").strip(),
                "credit_status": r.get("Credit Status", "").strip(),
                "ge_status": r.get("General Education Status", "").strip(),
                "sections_count": _to_int(r.get("Sections Count", "")) or 0,
                "term": r.get("Term", "").strip(),
                "control_number": r.get("Control Number", "").strip(),
                "source": SOURCE_TAG,
            })

        if dry_run:
            stats.courses_loaded += len(records)
            stats.departments_created += len(departments)
            continue

        with driver.session() as session:
            # College node — only set name properties; metadata like
            # region/city is owned by the existing onboarding pathway.
            # MERGE without ON CREATE clauses preserves whatever's there.
            session.run(
                "MERGE (col:College {name: $name}) "
                "ON CREATE SET col.created_at = timestamp()",
                name=college,
            )

            # Departments + College->OFFERS->Department.
            for dept in departments:
                session.run(
                    """
                    MATCH (col:College {name: $college})
                    MERGE (d:Department {name: $dept})
                    MERGE (col)-[:OFFERS]->(d)
                    """,
                    college=college, dept=dept,
                )
                stats.departments_created += 1
                stats.offers_edges += 1

            # Courses — single MERGE per record, all properties set in
            # one statement so the node is fully populated before
            # CONTAINS edges are added.
            for r in records:
                session.run(
                    """
                    MERGE (c:Course {code: $code, college: $college})
                    SET
                        c.name = $name,
                        c.top_code = $top_code,
                        c.top_description = $top_description,
                        c.sam_code = $sam_code,
                        c.is_cte = $is_cte,
                        c.department = $department,
                        c.units_min = $units_min,
                        c.units_max = $units_max,
                        c.transfer_status = $transfer_status,
                        c.credit_status = $credit_status,
                        c.ge_status = $ge_status,
                        c.sections_count = $sections_count,
                        c.term = $term,
                        c.control_number = $control_number,
                        c.source = $source
                    """,
                    **r,
                )
                stats.courses_loaded += 1

                if r["department"]:
                    session.run(
                        """
                        MATCH (d:Department {name: $dept})
                        MATCH (c:Course {code: $code, college: $college})
                        MERGE (d)-[:CONTAINS]->(c)
                        """,
                        dept=r["department"], code=r["code"], college=college,
                    )
                    stats.contains_edges += 1

        # Region link reuses the existing helper. Idempotent.
        ensure_college_region_link(driver, college)

        # Materialize PREPARES_FOR edges from Course.top_code → Occupation
        # (via the institutional TOP-SOC crosswalk). The labor-market
        # API requires these to populate `aligned_course_count`. Failing
        # silently here would produce a working graph that returns
        # empty UI panels — a non-obvious failure mode.
        try:
            materialize_prepares_for(driver, college)
        except Exception as e:
            logger.warning(f"materialize_prepares_for failed for {college}: {e}")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV,
                        help=f"Path to combined CourseDetails CSV (default: {DEFAULT_CSV})")
    parser.add_argument("--name-map", type=Path, default=DEFAULT_NAME_MAP,
                        help=f"Path to Data Mart → canonical name JSON (default: {DEFAULT_NAME_MAP})")
    parser.add_argument("--college", help="Limit to one college (for smoke testing). "
                                          "Accepts either Data Mart or canonical name.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse + report; don't touch Neo4j")
    args = parser.parse_args()

    name_map, excluded = load_name_mapping(args.name_map)
    logger.info(f"Loaded name map: {len(name_map)} mappings, {len(excluded)} excluded")

    rows, csv_skips = load_csv(args.csv, name_map, excluded, college_filter=args.college)
    logger.info(f"Loaded {len(rows):,} rows from {args.csv} (CSV-stage skips: {dict(csv_skips)})")
    if args.college:
        logger.info(f"  filtered to college: {args.college}")

    if args.dry_run:
        stats = load_into_neo4j(driver=None, rows=rows, dry_run=True)  # type: ignore[arg-type]
    else:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            logger.error("NEO4J_PASSWORD not set")
            return 1
        driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            stats = load_into_neo4j(driver, rows, dry_run=False)
        finally:
            driver.close()

    logger.info("=" * 60)
    logger.info(f"Rows seen:           {stats.rows_seen:,}")
    logger.info(f"Rows skipped:        {stats.rows_skipped:,}  {dict(stats.skipped_reasons)}")
    logger.info(f"Colleges:            {len(stats.colleges_seen):,}")
    logger.info(f"Courses loaded:      {stats.courses_loaded:,}")
    logger.info(f"Departments touched: {stats.departments_created:,}")
    logger.info(f"OFFERS edges:        {stats.offers_edges:,}")
    logger.info(f"CONTAINS edges:      {stats.contains_edges:,}")
    logger.info(f"SAM distribution:    {dict(sorted(stats.sam_dist.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
