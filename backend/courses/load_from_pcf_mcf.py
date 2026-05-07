"""Statewide course-inventory loader from the INNER JOIN of PCF and MCF.

Replaces the term-pinned CourseDetails-based load with a fuller course
inventory: every course that's in an Active program (PCF "Course Status"
= Active) AND has an MCF entry (so it's institutionally classified
with TOP code, SAM, units, credit status). Loses the "Fall 2025
sections count" currency signal in exchange for ~1.45x more courses
per college on average — particularly for de-emphasized or off-cycle
courses that didn't run this term but are part of active programs.

Inputs:
  - PCF: cc_dataset/programcoursefiles/ProgramCourseFile_<key>.csv
  - MCF: backend/ontology/mastercoursefiles/MasterCourseFile_<key>.csv
  - Name map: backend/ontology/coursedetails/datamart_to_canonical.json

Join rules:
  - PCF rows: filter to Course Status = Active, dedupe by Course Control
    Number (a course in multiple programs collapses to one row).
  - MCF rows: keep latest entry per Control Number by Issue/Update Date.
  - Inner join on Control Number. Course Title comes from PCF (MCF lacks
    titles). All other classification fields come from MCF (the
    institutional record-of-truth).

Course node properties written:
  code, college                — composite key, code from PCF "Course Id"
  name                         — from PCF "Course Title"
  control_number               — from PCF/MCF (CCC000nnnnnn)
  top_code                     — 6-digit, from MCF "TOP Code"
  top_description    derived   — TOP6 → title via load_top_titles()
  sam_code                     — single letter A/B/C/D/E from MCF "SAM Status"
  is_cte             derived   — is_cte_top6(top_code)
  department         derived   — top_to_department_name(top_code)
  units_min, units_max         — from MCF Min/Max Units (float)
  credit_status                — from MCF "Credit Status" (D/C/N etc.)
  source             literal   — "pcf_mcf_inner_join"

Properties NOT set (preserved if previously written by another loader):
  description, prerequisites, learning_outcomes, course_objectives, url,
  catalog_section, transfer_status, ge_status, sections_count, term.

Usage (from inside backend container with /app mount):
    python -m courses.load_from_pcf_mcf
    python -m courses.load_from_pcf_mcf --pcf-dir /cc_dataset/programcoursefiles
    python -m courses.load_from_pcf_mcf --college "Allan Hancock"   # smoke
    python -m courses.load_from_pcf_mcf --dry-run
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

from ontology.crosswalks import is_cte_top6, top_to_department_name, load_top_titles
from ontology.prepares_for import materialize_prepares_for
from ontology.regions import ensure_college_region_link

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_from_pcf_mcf")

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PCF_DIR = Path("/cc_dataset/programcoursefiles")
FALLBACK_PCF_DIR = Path.home() / "Desktop" / "cc_dataset" / "programcoursefiles"
DEFAULT_MCF_DIR = BACKEND_ROOT / "ontology" / "mastercoursefiles"
DEFAULT_NAME_MAP = BACKEND_ROOT / "ontology" / "coursedetails" / "datamart_to_canonical.json"

SOURCE_TAG = "pcf_mcf_inner_join"


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


def _to_float(s: str) -> float:
    try:
        return float((s or "").strip() or 0)
    except ValueError:
        return 0.0


def _resolve_pcf_dir(arg: Path) -> Path:
    """Allow the PCF dir to live in either the canonical container path
    or the host-side fallback so the script runs in both environments."""
    if arg.exists():
        return arg
    if FALLBACK_PCF_DIR.exists():
        logger.info(f"PCF dir {arg} not found — falling back to {FALLBACK_PCF_DIR}")
        return FALLBACK_PCF_DIR
    raise FileNotFoundError(f"PCF dir not found at {arg} or {FALLBACK_PCF_DIR}")


def load_name_map(path: Path) -> tuple[dict[str, str], set[str]]:
    with path.open() as fh:
        data = json.load(fh)
    return data.get("mapping", {}), set(data.get("_excluded_from_load", []))


def read_pcf(path: Path) -> tuple[str, dict[str, dict]]:
    """Returns (data_mart_college_name, {control_number: {code, name, top_code}}).
    Filters to Course Status = Active, dedupes by Course Control Number."""
    by_cn: dict[str, dict] = {}
    college = ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            college = (row.get("College") or "").strip()
            if (row.get("Course Status") or "").strip() != "Active":
                continue
            cn = (row.get("Course Control Number") or "").strip()
            if not cn or cn in by_cn:
                continue
            by_cn[cn] = {
                "code": (row.get("Course Id") or "").strip(),
                "name": (row.get("Course Title") or "").strip(),
                "top_code_pcf": (row.get("Course TOP Code") or "").strip(),
            }
    return college, by_cn


def read_mcf(path: Path) -> dict[str, dict]:
    """Returns {control_number: {top_code, sam_code, units_min, units_max,
    credit_status, date}}. Latest-dated row per Control Number wins."""
    by_cn: dict[str, dict] = {}
    if not path.exists():
        return by_cn
    with path.open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            cn = (row.get("Control Number") or "").strip()
            if not cn:
                continue
            date = (row.get("Issue/Update Date") or "").strip()
            existing = by_cn.get(cn)
            if existing and existing["date"] >= date:
                continue
            top = (row.get("TOP Code") or "").strip()
            # Pad 4-digit codes to 6 (some MCF rows still carry pre-2010
            # 4-digit codes; partnership traversals key on 6).
            if len(top) == 4:
                top = top + "00"
            by_cn[cn] = {
                "top_code": top,
                "sam_code": (row.get("SAM Status") or "").strip().upper()[:1],
                "units_min": _to_float(row.get("Minimum Units") or ""),
                "units_max": _to_float(row.get("Maximum Units") or ""),
                "credit_status": (row.get("Credit Status") or "").strip(),
                "date": date,
            }
    return by_cn


def collect_records(
    pcf_dir: Path,
    mcf_dir: Path,
    name_map: dict[str, str],
    excluded: set[str],
    college_filter: str | None = None,
) -> tuple[list[dict], Counter]:
    """Walk every PCF file, INNER JOIN against its MCF, produce flat
    Course records with canonical college names. Returns (records, skip_counts)."""
    top_titles = load_top_titles()
    records: list[dict] = []
    skips: Counter = Counter()

    for pcf_path in sorted(pcf_dir.glob("ProgramCourseFile_*.csv")):
        dm_college, pcf = read_pcf(pcf_path)
        if not pcf:
            skips["empty_pcf"] += 1
            continue

        if dm_college in excluded:
            skips["excluded_college"] += len(pcf)
            continue
        canonical = name_map.get(dm_college)
        if canonical is None:
            skips["unmapped_college"] += len(pcf)
            logger.warning(f"Unmapped college (skipping {len(pcf)} rows): {dm_college!r}")
            continue
        if college_filter and canonical != college_filter and dm_college != college_filter:
            continue

        # Locate MCF by the same backend key the PCF file uses.
        key = pcf_path.name.replace("ProgramCourseFile_", "").replace(".csv", "")
        mcf_path = mcf_dir / f"MasterCourseFile_{key}.csv"
        mcf = read_mcf(mcf_path)
        if not mcf:
            skips["no_mcf_file"] += len(pcf)
            logger.warning(f"No MCF for {dm_college} ({key}); skipping {len(pcf)} PCF rows")
            continue

        # INNER JOIN by Control Number.
        for cn, p in pcf.items():
            m = mcf.get(cn)
            if m is None:
                skips["no_mcf_match"] += 1
                continue
            if not p["code"] or not p["name"]:
                skips["missing_code_or_title"] += 1
                continue
            top_code = m["top_code"]
            dept = top_to_department_name(top_code) if top_code else ""
            records.append({
                "code": p["code"],
                "college": canonical,
                "name": p["name"],
                "control_number": cn,
                "top_code": top_code,
                "top_description": top_titles.get(top_code, "") if top_code else "",
                "sam_code": m["sam_code"],
                "is_cte": is_cte_top6(top_code) if top_code else False,
                "department": dept or "",
                "units_min": m["units_min"],
                "units_max": m["units_max"],
                "credit_status": m["credit_status"],
                "source": SOURCE_TAG,
            })

    return records, skips


def load_into_neo4j(
    driver: Driver,
    records: list[dict],
    dry_run: bool = False,
) -> LoadStats:
    stats = LoadStats()

    if not dry_run:
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT course_code_college IF NOT EXISTS "
                "FOR (c:Course) REQUIRE (c.code, c.college) IS UNIQUE"
            )

    by_college: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_college[r["college"]].append(r)
        stats.rows_seen += 1
        stats.colleges_seen.add(r["college"])
        stats.sam_dist[r["sam_code"] or "?"] += 1

    for college, college_records in by_college.items():
        departments = {r["department"] for r in college_records if r["department"]}
        if dry_run:
            stats.courses_loaded += len(college_records)
            stats.departments_created += len(departments)
            continue

        with driver.session() as session:
            session.run(
                "MERGE (col:College {name: $name}) "
                "ON CREATE SET col.created_at = timestamp()",
                name=college,
            )

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

            for r in college_records:
                session.run(
                    """
                    MERGE (c:Course {code: $code, college: $college})
                    SET
                        c.name = $name,
                        c.control_number = $control_number,
                        c.top_code = $top_code,
                        c.top_description = $top_description,
                        c.sam_code = $sam_code,
                        c.is_cte = $is_cte,
                        c.department = $department,
                        c.units_min = $units_min,
                        c.units_max = $units_max,
                        c.credit_status = $credit_status,
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

        ensure_college_region_link(driver, college)
        try:
            materialize_prepares_for(driver, college)
        except Exception as e:
            logger.warning(f"materialize_prepares_for failed for {college}: {e}")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcf-dir", type=Path, default=DEFAULT_PCF_DIR)
    parser.add_argument("--mcf-dir", type=Path, default=DEFAULT_MCF_DIR)
    parser.add_argument("--name-map", type=Path, default=DEFAULT_NAME_MAP)
    parser.add_argument("--college", help="Limit to one college (Data Mart or canonical name)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pcf_dir = _resolve_pcf_dir(args.pcf_dir)
    name_map, excluded = load_name_map(args.name_map)
    logger.info(f"PCF dir: {pcf_dir}  MCF dir: {args.mcf_dir}")
    logger.info(f"Name map: {len(name_map)} mappings, {len(excluded)} excluded")

    records, skips = collect_records(pcf_dir, args.mcf_dir, name_map, excluded, args.college)
    logger.info(f"Collected {len(records):,} records  skips={dict(skips)}")
    if args.college:
        logger.info(f"  filtered to college: {args.college}")

    if args.dry_run:
        stats = load_into_neo4j(driver=None, records=records, dry_run=True)  # type: ignore[arg-type]
    else:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USERNAME", os.environ.get("NEO4J_USER", "neo4j"))
        pwd = os.environ.get("NEO4J_PASSWORD")
        if not pwd:
            logger.error("NEO4J_PASSWORD not set")
            return 1
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        try:
            stats = load_into_neo4j(driver, records, dry_run=False)
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
