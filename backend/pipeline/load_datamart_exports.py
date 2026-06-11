"""Load the per-college DataMart exports (credit + noncredit course enrollment,
and program awards) into Neo4j as Program nodes with ENROLLED / AWARDED edges,
for every catalog college.

Reuses ontology.programs' graph model and leaf/normalization helpers, so records
MERGE idempotently onto the existing SVAMP-pilot graph (matching credit_type /
award_type / term / year keys) instead of duplicating:

    (Department {name})-[:HAS_PROGRAM]->(Program {college, top6})
    (Program)-[:ENROLLED {credit_type}]->(Term {term})       SET count
    (Program)-[:AWARDED  {award_type}]->(AcademicYear {year}) SET count

Sources (per-college, named by backend key):
    ontology/datamart/credit_course_summary/<key>.csv   College->Credit Status->TOP6  x term
    ontology/datamart/ncredit_course_summary/<key>.csv  College->TOP6                 x term  (family=Non-Credit)
    ontology/datamart/program_awards/<key>.csv          College->Award Type->TOP6     x year  (CO-Approved)

College identity: filename stem -> catalog_sources.json name -> Neo4j College.name.
Only colleges that exist as College nodes are loaded.

Usage (inside the backend container, which has Neo4j env + deps):
    python -m pipeline.load_datamart_exports --dry-run
    python -m pipeline.load_datamart_exports --only bakersfield
    python -m pipeline.load_datamart_exports            # all catalog colleges
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import is_cte_top6, load_top_titles, top_to_department_name
from ontology.programs import (
    _name_from_prefix, _name_from_suffix, _to_int, _top6_prefix, _top6_suffix,
)

_YEAR_RANGE = re.compile(r"\d{4}-\d{4}")
_DATAMART = Path(__file__).parent.parent / "ontology" / "datamart"
_CATALOG = Path(__file__).parent / "catalog_sources.json"

CREDIT_DIR = _DATAMART / "credit_course_summary"
NCREDIT_DIR = _DATAMART / "ncredit_course_summary"
AWARDS_DIR = _DATAMART / "program_awards"


def _strip_total(s: str) -> str:
    return re.sub(r"\s+Total$", "", s.strip())


def _read(path: Path) -> list[list[str]]:
    return list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))


def parse_credit(path: Path, college: str) -> list[dict]:
    """College -> Credit Status -> TOP6(prefix) x term, one value column per
    term. credit_type carries the family ('Credit - Degree Applicable' / ...)."""
    rows = _read(path)
    if len(rows) < 2:
        return []
    terms = rows[0][3:]
    out, credit_type = [], None
    for row in rows[1:]:
        c0, c1, c2 = (row + ["", "", ""])[:3]
        if c0.strip().endswith("Total") and c0.strip():
            continue  # college total row; college comes from the filename
        if c1.strip().endswith("Total") and c1.strip():
            credit_type = _strip_total(c1)
            continue
        if not c2.strip():
            continue
        top6 = _top6_prefix(c2)
        if not top6:
            continue
        name = _name_from_prefix(c2)
        for i, term in enumerate(terms):
            ci = 3 + i
            cnt = _to_int(row[ci]) if ci < len(row) else None
            if cnt is not None and term.strip():
                out.append({"college": college, "top6": top6, "name": name,
                            "credit_type": credit_type or "Credit",
                            "term": term.strip(), "count": cnt})
    return out


def parse_noncredit(path: Path, college: str) -> list[dict]:
    """College -> TOP6(prefix) x term (no family tier; credit_type=Non-Credit)."""
    rows = _read(path)
    if len(rows) < 2:
        return []
    terms = rows[0][2:]
    out = []
    for row in rows[1:]:
        c0, c1 = (row + ["", ""])[:2]
        if c0.strip().endswith("Total") and c0.strip():
            continue
        if not c1.strip():
            continue
        top6 = _top6_prefix(c1)
        if not top6:
            continue
        name = _name_from_prefix(c1)
        for i, term in enumerate(terms):
            ci = 2 + i
            cnt = _to_int(row[ci]) if ci < len(row) else None
            if cnt is not None and term.strip():
                out.append({"college": college, "top6": top6, "name": name,
                            "credit_type": "Non-Credit", "term": term.strip(),
                            "count": cnt})
    return out


def parse_awards(path: Path, college: str) -> list[dict]:
    """College -> Award Type -> TOP6(suffix) x academic year."""
    rows = _read(path)
    if len(rows) < 2:
        return []
    years = [(m.group(0) if (m := _YEAR_RANGE.search(h)) else h.strip())
             for h in rows[0][3:]]
    out, award_type = [], None
    for row in rows[1:]:
        c0, c1, c2 = (row + ["", "", ""])[:3]
        if c0.strip().endswith("Total") and c0.strip():
            continue
        if c1.strip().endswith("Total") and c1.strip():
            award_type = _strip_total(c1)
            continue
        if not c2.strip():
            continue
        top6 = _top6_suffix(c2)
        if not top6:
            continue
        name = _name_from_suffix(c2)
        for i, year in enumerate(years):
            ci = 3 + i
            cnt = _to_int(row[ci]) if ci < len(row) else None
            if cnt is not None:
                out.append({"college": college, "top6": top6, "name": name,
                            "award_type": award_type or "Award",
                            "count": cnt, "year": year})
    return out


def gather(keys: list[str], catalog: dict) -> tuple[list[dict], list[dict]]:
    """Parse every college file -> (awards, enroll) record lists, college set to
    the Neo4j College.name (= catalog 'name')."""
    awards, enroll = [], []
    for key in keys:
        college = catalog[key]["name"]
        cf, nf, af = CREDIT_DIR / f"{key}.csv", NCREDIT_DIR / f"{key}.csv", AWARDS_DIR / f"{key}.csv"
        if cf.exists():
            enroll += parse_credit(cf, college)
        if nf.exists():
            enroll += parse_noncredit(nf, college)
        if af.exists():
            awards += parse_awards(af, college)
    return awards, enroll


def load(driver, awards: list[dict], enroll: list[dict]) -> dict:
    """MERGE the Program universe and its measure edges (mirrors
    ontology.programs.load_programs' write path)."""
    with driver.session() as s:
        existing = {r["name"] for r in s.run("MATCH (c:College) RETURN c.name AS name")}
    awards = [a for a in awards if a["college"] in existing]
    enroll = [e for e in enroll if e["college"] in existing]

    top_titles = load_top_titles()
    programs: dict[tuple[str, str], dict] = {}
    for rec in enroll + awards:
        key = (rec["college"], rec["top6"])
        if key not in programs:
            programs[key] = {
                "college": rec["college"], "top6": rec["top6"],
                "name": top_titles.get(rec["top6"]) or rec["name"],
                "top4": rec["top6"][:4], "is_cte": is_cte_top6(rec["top6"]),
                "dept": top_to_department_name(rec["top6"]),
            }
    prog_rows = list(programs.values())

    with driver.session() as s:
        s.run("""
            UNWIND $rows AS p
            MERGE (pr:Program {college: p.college, top6: p.top6})
            SET pr.name = p.name, pr.top4 = p.top4, pr.is_cte = p.is_cte
        """, rows=prog_rows)
        s.run("""
            UNWIND $rows AS p
            MATCH (pr:Program {college: p.college, top6: p.top6})
            MATCH (d:Department {name: p.dept})
            MERGE (d)-[:HAS_PROGRAM]->(pr)
        """, rows=[p for p in prog_rows if p["dept"]])
        s.run("""
            UNWIND $rows AS a
            MATCH (pr:Program {college: a.college, top6: a.top6})
            MERGE (ay:AcademicYear {year: a.year})
            MERGE (pr)-[r:AWARDED {award_type: a.award_type}]->(ay)
            SET r.count = a.count
        """, rows=awards)
        s.run("""
            UNWIND $rows AS e
            MATCH (pr:Program {college: e.college, top6: e.top6})
            MERGE (t:Term {term: e.term})
            MERGE (pr)-[r:ENROLLED {credit_type: e.credit_type}]->(t)
            SET r.count = e.count
        """, rows=enroll)
    return {"programs": len(prog_rows), "awarded": len(awards),
            "enrolled": len(enroll), "colleges": len({p["college"] for p in prog_rows})}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="single backend college key")
    ap.add_argument("--dry-run", action="store_true", help="parse + report, no write")
    args = ap.parse_args()

    catalog = json.loads(_CATALOG.read_text())["colleges"]
    keys = [args.only] if args.only else list(catalog)
    awards, enroll = gather(keys, catalog)
    print(f"parsed {len(keys)} college(s): {len(awards)} award rows, {len(enroll)} enroll rows", flush=True)
    by_ct = {}
    for e in enroll:
        by_ct[e["credit_type"]] = by_ct.get(e["credit_type"], 0) + 1
    print("  enroll by credit_type:", by_ct, flush=True)

    if args.dry_run:
        print("dry run — no write", flush=True)
        return 0

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    try:
        stats = load(driver, awards, enroll)
    finally:
        driver.close()
    print("loaded:", stats, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
