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

from evals.characterization import (
    COMPARE_GOLDEN_COORDS,
    GOLDEN_COORDS,
    capture,
    capture_compare,
    compare_golden_path,
    golden_path,
)


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


@requires_graph
@pytest.mark.parametrize("coord", COMPARE_GOLDEN_COORDS, ids=lambda c: "_".join(c))
def test_compare_golden(coord):
    """The comparison engine's ranked output must reproduce exactly — any change to a ranking, a
    criterion's value, or the registry is caught here (refresh with `python -m evals.characterization`
    if intended)."""
    path = compare_golden_path(*coord)
    assert path.exists(), (
        f"missing golden {path.name} — generate it with `python -m evals.characterization`")
    want = json.loads(path.read_text())
    got = capture_compare(*coord)
    assert got == want, (
        f"compare characterization drift at {'_'.join(coord)} — if intended, refresh the goldens: "
        f"`python -m evals.characterization`")


@requires_graph
@pytest.mark.parametrize("coord", GOLDEN_COORDS, ids=lambda c: "_".join(c))
def test_dashboard_mcp_supply_corroboration(coord):
    """THE crown-jewel invariant — the one that would have caught gap 440/458/−3972. The
    dashboard builder (consortium_supply) and the MCP resolver (canonical.supply) must
    resolve the SAME member-scoped supply at a coordinate; no surface may re-derive a figure
    the other owns. After S3 both read the one DataMart store, so they agree to the completion.

    Tolerance = 1 completion OR 1%, which absorbs ONLY the §D TOP parent/child crosswalk
    granularity (the builder attributes RN to 123010, the store-level resolver's is_vocational
    crosswalk also counts the general 123000 — a known, separately-tracked ontology-structural
    difference worth <1 completion). A genuine store/rule divergence — the #99/#103 fault — is
    off by hundreds (the CSV-vs-graph split was 716 vs 111), orders of magnitude beyond this."""
    got = capture(*coord)
    if not got.get("in_scope"):
        pytest.skip("out of scope")
    b = got["builder"]["consortium_supply"]
    c = got["canonical"]["supply_3yr"]
    assert abs(b - c) <= 1.0 or abs(b - c) / max(b, c, 1) < 0.01, (
        f"dashboard⇄MCP supply divergence at {'_'.join(coord)}: builder={b} vs canonical={c} — "
        f"the two surfaces re-derive supply from different stores/rules (the #99/#103 fault)")
