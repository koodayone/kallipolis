"""The Phase-A refactor guard: every analytical surface still produces its snapshotted output,
byte-for-byte. A failure means the engine-unification changed a number or a structure — which, in
Phase A, is a regression (Phase A preserves output). In Phase B the snapshots are regenerated as a
signed-off diff. Deterministic (proven by the twice-capture self-check in characterization_surfaces).
"""
from __future__ import annotations

import json
import os

import pytest

from evals.characterization_surfaces import SNAP_DIR, capture, _blob


def _graph_available() -> bool:
    if "NEO4J_URI" not in os.environ:
        return False
    try:
        from ontology.schema import get_driver
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


requires_graph = pytest.mark.skipif(not _graph_available(), reason="no reachable Neo4j graph")


def _first_diff(a, b, path=""):
    """First differing (path, snapshot_value, current_value) — the actionable drift, not just a key."""
    if type(a) is not type(b):
        return (path or ".", a, b)
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                return (f"{path}.{k}", "<missing>", b[k])
            if k not in b:
                return (f"{path}.{k}", a[k], "<missing>")
            d = _first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return (f"{path}[len]", len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = _first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return (path or ".", a, b) if a != b else None


@requires_graph
def test_surfaces_match_snapshots():
    snaps = {p.stem: json.loads(p.read_text()) for p in SNAP_DIR.glob("*.json")}
    assert snaps, "no snapshots — run `python -m evals.characterization_surfaces` first"
    cur = capture()
    missing = sorted(set(snaps) - set(cur))
    changed = sorted(k for k in snaps if k in cur and _blob(snaps[k]) != _blob(cur[k]))
    if missing or changed:
        lines = []
        if missing:
            lines.append(f"MISSING (surface no longer produced): {missing}")
        for k in changed[:8]:
            p, was, now = _first_diff(snaps[k], cur[k])
            lines.append(f"CHANGED {k}  @ {p}:  snapshot={was!r} -> current={now!r}")
        if len(changed) > 8:
            lines.append(f"... and {len(changed) - 8} more changed")
        pytest.fail(f"{len(changed)} surface(s) drifted vs snapshot:\n" + "\n".join(lines))
