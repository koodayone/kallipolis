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

# The two surfaces corroborate to within one completion. The residual is NOT rounding: the MCP
# resolves an occupation's feeder programs via the is_vocational TOP->SOC crosswalk, while the
# dashboard builder uses the LandscapeSpec.in_scope rule — so where they disagree on a marginal
# program, the supplies differ. (Observed: RN at baccc/health — the crosswalk counts TOP 123000,
# generic Nursing, as an RN feeder; in_scope does not; a 0.7/yr difference.) A divergence BEYOND
# this band is a gross computation drift. Tighten toward 0 only after the two feeder rules are
# unified — a correctness decision (which programs feed an occupation), tracked as a substrate item.
_CORROBORATION_BAND = 1.0


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
