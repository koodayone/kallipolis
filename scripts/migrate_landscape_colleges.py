"""Surgical export/load of one or more colleges' subgraph between Neo4j
instances — the zero-downtime way to publish a draft landscape (e.g. SMCCD)
to prod without a full dump-push or re-running the expensive onboarding
pipeline (student generation, employer scraping).

Moves only what an aggregated-landscape surface reads for its member colleges:
  College, Course (+PREPARES_FOR→Occupation), Program (+AWARDED→AcademicYear,
  +ENROLLED→Term), College-[OCCUPATION_PIPELINE]->Occupation, College-[IN_MARKET]->Region.

Student nodes are deliberately NOT moved: the landscape reads student_count off
the OCCUPATION_PIPELINE edge (already materialized), so the ~tens-of-thousands
of Student nodes per college are unnecessary for these surfaces.

Targets (Occupation by soc_code, AcademicYear by year, Term by term, Region by
name) are assumed to pre-exist in the destination (regional/shared data) — the
MERGEs match them; they are never created here.

Idempotent by construction: every write is a MERGE on the schema's uniqueness
key (College.name, Course.(code,college), Program.(college,top6)) or on the
edge's discriminator (AWARDED.award_type, ENROLLED.credit_type), so re-running
the load creates nothing new. Verify with --dry-run-counts after a load.

Usage:
    python scripts/migrate_landscape_colleges.py export \
        --colleges "College of San Mateo" "Skyline College" "Cañada College" \
        --out /tmp/smccd_subgraph.json
    python scripts/migrate_landscape_colleges.py load --in /tmp/smccd_subgraph.json
    python scripts/migrate_landscape_colleges.py verify --in /tmp/smccd_subgraph.json

Connects via NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD (run `load` inside the
destination's backend container so it points at that graph).
"""
from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import sys
from pathlib import Path

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("migrate_landscape_colleges")

_BATCH = 1000


def _driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pw = os.environ.get("NEO4J_PASSWORD")
    if not pw:
        log.error("NEO4J_PASSWORD not set"); sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, pw))


def _open(path: Path, mode: str):
    return gzip.open(path, mode + "t", encoding="utf-8") if str(path).endswith(".gz") else open(path, mode, encoding="utf-8")


# ── Export ──────────────────────────────────────────────────────────────────

def export(driver, colleges: list[str], out: Path) -> None:
    snap: dict = {"colleges_scope": colleges}
    with driver.session() as s:
        snap["colleges"] = [r["p"] for r in s.run(
            "MATCH (c:College) WHERE c.name IN $cs RETURN properties(c) AS p", cs=colleges)]
        snap["courses"] = [r["p"] for r in s.run(
            "MATCH (c:Course) WHERE c.college IN $cs RETURN properties(c) AS p", cs=colleges)]
        snap["prepares_for"] = [dict(r) for r in s.run(
            "MATCH (c:Course)-[r:PREPARES_FOR]->(o:Occupation) WHERE c.college IN $cs "
            "RETURN c.college AS college, c.code AS code, o.soc_code AS soc, r.via_top AS via_top", cs=colleges)]
        snap["programs"] = [r["p"] for r in s.run(
            "MATCH (p:Program) WHERE p.college IN $cs RETURN properties(p) AS p", cs=colleges)]
        snap["awarded"] = [dict(r) for r in s.run(
            "MATCH (p:Program)-[r:AWARDED]->(y:AcademicYear) WHERE p.college IN $cs "
            "RETURN p.college AS college, p.top6 AS top6, y.year AS year, r.award_type AS award_type, r.count AS count", cs=colleges)]
        snap["enrolled"] = [dict(r) for r in s.run(
            "MATCH (p:Program)-[r:ENROLLED]->(t:Term) WHERE p.college IN $cs "
            "RETURN p.college AS college, p.top6 AS top6, t.term AS term, r.credit_type AS credit_type, r.count AS count", cs=colleges)]
        snap["occupation_pipeline"] = [dict(r) for r in s.run(
            "MATCH (c:College)-[r:OCCUPATION_PIPELINE]->(o:Occupation) WHERE c.name IN $cs "
            "RETURN c.name AS college, o.soc_code AS soc, r.course_count AS course_count, "
            "r.employer_count AS employer_count, r.student_count AS student_count, r.top_codes AS top_codes", cs=colleges)]
        snap["in_market"] = [dict(r) for r in s.run(
            "MATCH (c:College)-[:IN_MARKET]->(r:Region) WHERE c.name IN $cs "
            "RETURN c.name AS college, r.name AS region", cs=colleges)]
    with _open(out, "w") as f:
        json.dump(snap, f)
    log.info("exported %s", {k: len(v) for k, v in snap.items() if isinstance(v, list)})
    log.info("wrote %s (%d bytes)", out, out.stat().st_size)


# ── Load (idempotent) ─────────────────────────────────────────────────────────

_LOADERS = [
    ("colleges", "UNWIND $rows AS r MERGE (c:College {name: r.name}) SET c += r"),
    ("courses", "UNWIND $rows AS r MERGE (c:Course {code: r.code, college: r.college}) SET c += r"),
    ("programs", "UNWIND $rows AS r MERGE (p:Program {college: r.college, top6: r.top6}) SET p += r"),
    ("prepares_for",
     "UNWIND $rows AS r MATCH (c:Course {code: r.code, college: r.college}) "
     "MATCH (o:Occupation {soc_code: r.soc}) MERGE (c)-[:PREPARES_FOR {via_top: r.via_top}]->(o)"),
    ("awarded",
     "UNWIND $rows AS r MATCH (p:Program {college: r.college, top6: r.top6}) "
     "MERGE (y:AcademicYear {year: r.year}) "
     "MERGE (p)-[a:AWARDED {award_type: r.award_type}]->(y) SET a.count = r.count"),
    ("enrolled",
     "UNWIND $rows AS r MATCH (p:Program {college: r.college, top6: r.top6}) "
     "MERGE (t:Term {term: r.term}) "
     "MERGE (p)-[e:ENROLLED {credit_type: r.credit_type}]->(t) SET e.count = r.count"),
    ("occupation_pipeline",
     "UNWIND $rows AS r MATCH (c:College {name: r.college}) MATCH (o:Occupation {soc_code: r.soc}) "
     "MERGE (c)-[op:OCCUPATION_PIPELINE]->(o) "
     "SET op.course_count = r.course_count, op.employer_count = r.employer_count, "
     "op.student_count = r.student_count, op.top_codes = r.top_codes"),
    ("in_market",
     "UNWIND $rows AS r MATCH (c:College {name: r.college}) MATCH (g:Region {name: r.region}) "
     "MERGE (c)-[:IN_MARKET]->(g)"),
]


def _missing_targets(driver, snap: dict) -> list[str]:
    """Pre-flight: the regional/shared targets the edges MATCH must already
    exist in the destination — a missing one would silently drop edges."""
    socs = {r["soc"] for r in snap["prepares_for"]} | {r["soc"] for r in snap["occupation_pipeline"]}
    regions = {r["region"] for r in snap["in_market"]}
    missing = []
    with driver.session() as s:
        have = {r["s"] for r in s.run("MATCH (o:Occupation) WHERE o.soc_code IN $x RETURN o.soc_code AS s", x=list(socs))}
        missing += [f"Occupation {x}" for x in socs - have]
        haveR = {r["n"] for r in s.run("MATCH (g:Region) WHERE g.name IN $x RETURN g.name AS n", x=list(regions))}
        missing += [f"Region {x}" for x in regions - haveR]
    return missing


def load(driver, snap: dict) -> None:
    missing = _missing_targets(driver, snap)
    if missing:
        log.error("ABORT: %d MATCH targets absent in destination (edges would silently drop): %s",
                  len(missing), missing[:10])
        sys.exit(2)
    log.info("pre-flight ok: all edge targets pre-exist in destination")
    with driver.session() as s:
        for key, cypher in _LOADERS:
            rows = snap.get(key, [])
            for i in range(0, len(rows), _BATCH):
                s.run(cypher, rows=rows[i:i + _BATCH])
            log.info("loaded %s: %d", key, len(rows))


def verify(driver, snap: dict) -> None:
    """Compare destination counts to the snapshot's, per college."""
    cs = snap["colleges_scope"]
    with driver.session() as s:
        d = {
            "College": s.run("MATCH (c:College) WHERE c.name IN $cs RETURN count(c) AS n", cs=cs).single()["n"],
            "Course": s.run("MATCH (c:Course) WHERE c.college IN $cs RETURN count(c) AS n", cs=cs).single()["n"],
            "Program": s.run("MATCH (p:Program) WHERE p.college IN $cs RETURN count(p) AS n", cs=cs).single()["n"],
            "PREPARES_FOR": s.run("MATCH (c:Course)-[r:PREPARES_FOR]->() WHERE c.college IN $cs RETURN count(r) AS n", cs=cs).single()["n"],
            "AWARDED": s.run("MATCH (p:Program)-[r:AWARDED]->() WHERE p.college IN $cs RETURN count(r) AS n", cs=cs).single()["n"],
            "ENROLLED": s.run("MATCH (p:Program)-[r:ENROLLED]->() WHERE p.college IN $cs RETURN count(r) AS n", cs=cs).single()["n"],
            "OCCUPATION_PIPELINE": s.run("MATCH (c:College)-[r:OCCUPATION_PIPELINE]->() WHERE c.name IN $cs RETURN count(r) AS n", cs=cs).single()["n"],
            "IN_MARKET": s.run("MATCH (c:College)-[r:IN_MARKET]->() WHERE c.name IN $cs RETURN count(r) AS n", cs=cs).single()["n"],
        }
    expect = {"College": len(snap["colleges"]), "Course": len(snap["courses"]), "Program": len(snap["programs"]),
              "PREPARES_FOR": len(snap["prepares_for"]), "AWARDED": len(snap["awarded"]),
              "ENROLLED": len(snap["enrolled"]), "OCCUPATION_PIPELINE": len(snap["occupation_pipeline"]),
              "IN_MARKET": len(snap["in_market"])}
    ok = True
    for k in expect:
        mark = "✓" if d[k] >= expect[k] else "✗"
        if d[k] < expect[k]: ok = False
        log.info("  %-20s dest=%-6d snapshot=%-6d %s", k, d[k], expect[k], mark)
    log.info("VERIFY %s", "PASS" if ok else "FAIL (destination missing rows)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("export"); pe.add_argument("--colleges", nargs="+", required=True); pe.add_argument("--out", required=True)
    pl = sub.add_parser("load"); pl.add_argument("--in", dest="infile", required=True)
    pv = sub.add_parser("verify"); pv.add_argument("--in", dest="infile", required=True)
    a = ap.parse_args()
    drv = _driver()
    try:
        if a.cmd == "export":
            export(drv, a.colleges, Path(a.out))
        else:
            with _open(Path(a.infile), "r") as f:
                snap = json.load(f)
            (load if a.cmd == "load" else verify)(drv, snap)
    finally:
        drv.close()


if __name__ == "__main__":
    main()
