"""Characterization snapshots of every live landscape instance — the
no-regression gate (Phase 0) for the member×sector gap-analysis refactor.

The builders are pure functions of (graph, spec); the graph is fixed for the
duration of the refactor, so the ONLY thing that changes across phases is the
code (resolve / build_landscape / the registry). This harness pins the current
output of all 12 live instances (SVAMP + the 11 SMCCD sectors) so any phase that
silently alters a live instance's output fails `check` until intentionally
re-baselined.

It snapshots the LIVE API (the real serving path at http://localhost:8000), not
the builders directly — that avoids host→Neo4j access (the neo4j container
exposes no host port) and pytest-in-container, and it exercises exactly what
users hit. `routable_specs()` imports graph-free, so the instance list stays in
sync without a DB connection.

Refactor loop:
    1. python3 tests/integration/snapshot_landscapes.py capture   # baseline (once)
    2. <make a backend change>  &&  docker compose up -d --build backend
    3. python3 tests/integration/snapshot_landscapes.py check      # exits 1 on drift

Re-baseline (only when an output change is intended): re-run `capture` and review
the fixture diff in the commit.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

# Put backend/ on the path so `partnerships` imports whether run as a script or
# a module — the refactor loop should need no PYTHONPATH ceremony.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from partnerships.landscape import routable_specs  # noqa: E402

SNAP_DIR = Path(__file__).parent / "landscape_snapshots"
# "" = the landscape payload; the two lenses that are non-parameterized builders.
SURFACES = ("", "/programs", "/employers")
DEFAULT_BASE = "http://localhost:8000"


def _fetch(base: str, sid: str, surface: str) -> dict:
    url = f"{base}/partnerships/{sid}{surface}"
    with urllib.request.urlopen(url, timeout=90) as resp:
        return json.load(resp)


def _snapshot(base: str, sid: str) -> dict:
    return {(sfc or "landscape"): _fetch(base, sid, sfc) for sfc in SURFACES}


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, indent=2)


def capture(base: str) -> None:
    SNAP_DIR.mkdir(exist_ok=True)
    specs = routable_specs()
    for spec in specs:
        (SNAP_DIR / f"{spec.id}.json").write_text(_canonical(_snapshot(base, spec.id)))
        print(f"captured {spec.id}")
    print(f"baselined {len(specs)} instances → {SNAP_DIR}")


def check(base: str) -> None:
    specs = routable_specs()
    drift, missing = [], []
    for spec in specs:
        path = SNAP_DIR / f"{spec.id}.json"
        if not path.exists():
            missing.append(spec.id)
            print(f"NO BASELINE  {spec.id}")
            continue
        expected = path.read_text()
        actual = _canonical(_snapshot(base, spec.id))
        if actual == expected:
            print(f"ok           {spec.id}")
        else:
            drift.append(spec.id)
            print(f"DRIFT        {spec.id}")
    if drift:
        print(f"\nFAIL: {len(drift)} instance(s) drifted from baseline: {', '.join(drift)}")
        sys.exit(1)
    if missing:
        print(f"\nWARN: {len(missing)} instance(s) have no baseline: {', '.join(missing)}")
        sys.exit(2)
    print(f"\nPASS: all {len(specs)} instances match baseline")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    base_url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE
    if cmd == "capture":
        capture(base_url)
    elif cmd == "check":
        check(base_url)
    else:
        print(f"usage: {sys.argv[0]} [capture|check] [base_url]")
        sys.exit(64)
