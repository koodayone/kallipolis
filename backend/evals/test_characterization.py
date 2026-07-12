"""Characterization goldens — the committed quantities at the golden coordinates must
reproduce exactly. Drift is either an intended behavior change (refresh the goldens with
`python -m evals.characterization`) or a regression to catch. These lock the CURRENT
builder-vs-canonical divergence so the Phase-2 unification diff is legible; see
evals/characterization.py and research/architecture/EVALS-APPROACH.md.

@requires_graph: runs against the seeded CI Neo4j; skips locally without a reachable one.
"""
import json
import os

import pytest

from evals.characterization import GOLDEN_COORDS, capture, golden_path


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


@requires_graph
@pytest.mark.parametrize("coord", GOLDEN_COORDS, ids=lambda c: "_".join(c))
def test_characterization_golden(coord):
    path = golden_path(*coord)
    assert path.exists(), (
        f"missing golden {path.name} — generate it with `python -m evals.characterization`")
    want = json.loads(path.read_text())
    got = capture(*coord)
    assert got == want, (
        f"characterization drift at {'_'.join(coord)} — if intended, refresh the goldens: "
        f"`python -m evals.characterization`")
