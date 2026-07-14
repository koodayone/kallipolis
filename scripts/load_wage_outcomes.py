#!/usr/bin/env python3
"""Additive load of the statewide graduate-wage outcomes into a Neo4j graph.

Materializes the pooled ``ProgramWageOutcome`` nodes + ``HAS_WAGE_OUTCOME`` edges
(see ``ontology.programs.load_program_wage_outcomes``) WITHOUT a full pipeline
reload or a dump-push — the zero-downtime way to add the wage layer to an already-
loaded graph (e.g. prod, after the code deploy). Idempotent: every write is a MERGE
on the schema key, so re-running creates nothing new. Verify with ``--verify``.

The wage export is pooled STATEWIDE at the TOP6 grain (no college dimension), so
this adds a fixed statewide reference layer independent of which colleges are
loaded. It is self-scoping: nodes are created only for TOP6s some loaded college
offers, so Program nodes must already exist — run it AFTER the Program layer is
present (a full reload also runs this same loader as its Step 4b, so a later reload
is a no-op, not a conflict).

Connects via NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD — run inside the prod IAP
tunnel (or the backend container) to target the prod graph. Always ``--dry-run`` first.

Usage:
    # inspect what would load + the current graph state (writes nothing)
    NEO4J_URI=bolt://localhost:7687 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=… \
        python scripts/load_wage_outcomes.py --dry-run
    # perform the additive load
    NEO4J_URI=… NEO4J_USERNAME=… NEO4J_PASSWORD=… python scripts/load_wage_outcomes.py
    # confirm the layer is present afterward
    NEO4J_URI=… … python scripts/load_wage_outcomes.py --verify
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Put the backend package on the import path: the repo checkout's ``backend/``
# subdir (VM host), or ``/app`` (inside the backend container).
for _cand in (Path(__file__).resolve().parent.parent / "backend", Path("/app")):
    if (_cand / "ontology" / "programs.py").exists():
        sys.path.insert(0, str(_cand))
        break

from neo4j import GraphDatabase

from ontology.programs import _wage_index, load_program_wage_outcomes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("load_wage_outcomes")

# The statewide node's uniqueness key (mirrors ontology/schema.py); created here so
# an additive load into a graph whose schema predates the node still gets the index.
_CONSTRAINT = ("CREATE CONSTRAINT program_wage_outcome_top6_recipient IF NOT EXISTS "
               "FOR (n:ProgramWageOutcome) REQUIRE (n.top6, n.recipient_type) IS UNIQUE")


def _driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pw = os.environ.get("NEO4J_PASSWORD")
    if not pw:
        log.error("NEO4J_PASSWORD not set"); sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, pw))


def _verify(driver) -> None:
    with driver.session() as s:
        n = s.run("MATCH (w:ProgramWageOutcome) RETURN count(w) AS n").single()["n"]
        t = s.run("MATCH (w:ProgramWageOutcome) RETURN count(DISTINCT w.top6) AS n").single()["n"]
        e = s.run("MATCH (:Program)-[r:HAS_WAGE_OUTCOME]->(:ProgramWageOutcome) "
                  "RETURN count(r) AS n").single()["n"]
    log.info("graph has %d ProgramWageOutcome nodes across %d TOP6s, %d HAS_WAGE_OUTCOME edges", n, t, e)


def main() -> None:
    ap = argparse.ArgumentParser(description="Additive load of statewide graduate-wage outcomes.")
    ap.add_argument("--dry-run", action="store_true",
                    help="report the CSV wage universe + current graph state; write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="report the ProgramWageOutcome node/edge counts already in the graph")
    args = ap.parse_args()

    driver = _driver()
    try:
        if args.verify:
            _verify(driver)
            return

        idx = _wage_index()
        csv_records = sum(len(v) for v in idx.values())
        with driver.session() as s:
            prog_tops = s.run("MATCH (p:Program) RETURN count(DISTINCT p.top6) AS n").single()["n"]
        log.info("wage CSV: %d TOP6s, %d recipient-type records; graph has %d Program TOP6s to scope against",
                 len(idx), csv_records, prog_tops)
        if prog_tops == 0:
            log.warning("no Program nodes in the graph — the load would create no edges; "
                        "run the Program layer first.")

        if args.dry_run:
            log.info("--dry-run: no writes. The loader is self-scoping to the graph's Program TOP6s.")
            return

        with driver.session() as s:
            s.run(_CONSTRAINT)   # idempotent
        stats = load_program_wage_outcomes(driver)
        log.info("loaded: %s", stats)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
