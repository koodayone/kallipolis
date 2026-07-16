"""Tier A — the substrate invariants the conversational eval sits on top of.

Before any PROSE is graded, the numbers must be correct, consistent across tools, and consistent
with the DASHBOARD. These are deterministic property tests; a failure here is a computation /
envelope / data bug, never a DOCTRINE fix. Grading a conversation on a broken substrate wastes
iterations tuning the prompt against a wrong number — so Tier A gates the conversational eval.

Reuses ``evals.characterization.capture``, which computes each figure BOTH ways — the canonical MCP
path (``CAN.*``) and the dashboard/report builder path — so corroboration is a direct comparison.
Cross-tool referential integrity for the compare surface is asserted in
``mcp_server/test_compare.py`` (the ``referential`` tests); this module adds the dashboard⇄MCP leg.
"""
from __future__ import annotations

import os

import pytest

from evals.characterization import GOLDEN_COORDS, capture


def _graph() -> bool:
    if "NEO4J_URI" not in os.environ:
        return False
    try:
        from ontology.schema import get_driver
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


requires_graph = pytest.mark.skipif(not _graph(), reason="no reachable Neo4j graph")

# The two surfaces now resolve feeders through the ONE canonical rule — LandscapeSpec.in_scope plus
# the latest-year awards gate (adjudication A of the coordinate-kernel migration), applied in the
# kernel (quantities._soc_feeders) for the MCP path and in relevant_tops for the dashboard. The
# former feeder-rule seam (is_vocational vs in_scope — up to 278/yr on some occupations, e.g. RN's
# generic Nursing TOP 123000) is CLOSED: MCP supply == dashboard supply to rounding across the golden
# set (which now includes the former divergers). This band is rounding-only; a divergence beyond it
# reopens the seam and is a real computation drift.
_CORROBORATION_BAND = 0.05


@requires_graph
@pytest.mark.parametrize("coord", GOLDEN_COORDS)
def test_dashboard_mcp_corroboration(coord):
    """The supply figure the MCP returns == the figure the dashboard builder shows, to within
    rounding. The two-window trust invariant, ASSERTED rather than snapshotted: the shared
    ``quantities`` layer should make both surfaces agree."""
    d = capture(*coord)
    if not d.get("in_scope"):
        pytest.skip(f"{coord} out of scope")
    mcp = d["canonical"]["supply_3yr"]
    dash = d["builder"]["consortium_supply"]
    assert mcp is not None and dash is not None, f"{coord}: a surface returned no supply"
    assert abs(mcp - dash) < _CORROBORATION_BAND, (
        f"{coord}: dashboard⇄MCP divergence — MCP supply {mcp} vs dashboard {dash} exceeds the "
        f"{_CORROBORATION_BAND} rounding band; this is a real computation drift, not rounding")
