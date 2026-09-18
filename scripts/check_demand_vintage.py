#!/usr/bin/env python3
"""Does every copy of the COE occupational demand data agree with the bundled export?

    python scripts/check_demand_vintage.py            # files: derived JSON, sector join, eval corpora, authored figures
    python scripts/check_demand_vintage.py --graph    # also the live Neo4j (NEO4J_* env)

Exit non-zero on any disagreement. See backend/ontology/demand_vintage.py for what is
read and docs/pipeline/refreshing-a-bundled-authority.md for the refresh it guards.
"""
import argparse
import sys
from pathlib import Path

# the backend package: beside this script in a checkout, at /app inside the backend image
for _cand in (Path(__file__).resolve().parent.parent / "backend", Path("/app")):
    if (_cand / "ontology").exists():
        sys.path.insert(0, str(_cand))
        break

from ontology.demand_vintage import run_checks  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--graph", action="store_true", help="also compare the live graph's DEMANDS edges")
a = ap.parse_args()
findings = run_checks(graph=a.graph)
for f in findings:
    print(f"{'ok  ' if f.ok else 'FAIL'} {f.check:42} {f.detail}")
bad = [f for f in findings if not f.ok]
print(f"\n{len(findings) - len(bad)} agree, {len(bad)} disagree")
sys.exit(1 if bad else 0)
