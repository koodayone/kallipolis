"""Parallel PARTNERSHIP_ALIGNMENT compute across all colleges.

The sequential `partnerships.compute --all` iterates colleges one at a
time, each materialize call doing College→Region→Employer→Occupation
traversal + per-employer EXISTS subqueries. On a 114-college statewide
load this takes ~50 minutes. Per-college transactions don't collide
(each writes edges from a distinct startNode, different Neo4j locks),
so we can dispatch them across N concurrent workers and get a 3-4x
speedup.

Usage (from inside backend container):
    python /repo/scripts/compute_pa_parallel.py --workers 4
    python /repo/scripts/compute_pa_parallel.py --workers 6 --only "OCCUPATION_PIPELINE"

Each worker shares the same Neo4j driver; the driver's connection pool
manages session-level concurrency.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from neo4j import GraphDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pa_parallel")


def all_colleges(driver) -> list[str]:
    with driver.session() as s:
        return [r["n"] for r in s.run("MATCH (c:College) RETURN c.name AS n ORDER BY n")]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=4,
                   help="Concurrent worker threads (default: 4)")
    p.add_argument("--only", default="partnership_alignment",
                   choices=["partnership_alignment", "occupation_pipeline", "both"],
                   help="Which edge type to materialize")
    args = p.parse_args()

    sys.path.insert(0, "/app")
    from partnerships.compute import (
        materialize_partnership_alignment,
        materialize_occupation_pipeline,
    )

    uri = os.environ["NEO4J_URI"]
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ["NEO4J_PASSWORD"]

    # Driver pool sized for our worker count + a couple of slack
    # connections for Neo4j session lifecycle.
    driver = GraphDatabase.driver(
        uri, auth=(user, pwd), max_connection_pool_size=args.workers + 2,
    )

    try:
        colleges = all_colleges(driver)
        logger.info(f"Found {len(colleges)} colleges, dispatching across {args.workers} workers")

        funcs = []
        if args.only in ("partnership_alignment", "both"):
            funcs.append(("PA", materialize_partnership_alignment))
        if args.only in ("occupation_pipeline", "both"):
            funcs.append(("OP", materialize_occupation_pipeline))

        for tag, fn in funcs:
            logger.info(f"=== {tag} ===")
            t0 = time.time()
            done = 0

            def run_one(college: str, tag=tag, fn=fn):
                t = time.time()
                try:
                    stats = fn(driver, college)
                    return (college, time.time() - t, None,
                            stats.get("edges_created", 0))
                except Exception as e:
                    return (college, time.time() - t, str(e), 0)

            total_edges = 0
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(run_one, c): c for c in colleges}
                for fut in as_completed(futures):
                    college, dt, err, edges = fut.result()
                    done += 1
                    total_edges += edges
                    pct = 100 * done / len(colleges)
                    if err:
                        logger.error(f"[{done}/{len(colleges)}] {college} ({dt:.1f}s) FAILED: {err}")
                    else:
                        logger.info(f"[{done}/{len(colleges)} {pct:.0f}%] {college} ({dt:.1f}s, {edges} edges)")

            elapsed = time.time() - t0
            logger.info(f"=== {tag} done: {total_edges:,} edges in {elapsed:.1f}s "
                        f"({total_edges/max(elapsed,1):.0f} edges/sec) ===")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
