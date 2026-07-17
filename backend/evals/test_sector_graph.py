"""Reconciliation gate for the graph ontology (Step 3a).

Proves the loader (ontology.sector_graph) mirrors the Python ontology into the graph FAITHFULLY — every
Sector CONTAINS / OFFERS set, the crosswalk, and each authored Composition match the code. This is the gate
that makes the 3b read-swap safe: once graph == code is proven, swapping a read from Python to the graph is
byte-identical by construction.

@requires_graph: runs against a reachable Neo4j; skips locally without one.
"""
import os

import pytest


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
def test_ontology_materializes_faithfully():
    """Load the ontology into the graph and assert it reproduces the code. The only permitted 'discrepancy'
    is `pending_hollow` — sector occupations that have no demand node yet (created in 3b), a known gap, not a
    loader error. Idempotent: safe to run alongside the rest of the graph-backed suite."""
    from ontology import sector_graph

    sector_graph.load()
    diffs = sector_graph.reconcile()
    real = [d for d in diffs if not d.startswith("pending_hollow")]
    assert not real, "graph ontology diverges from code:\n" + "\n".join(real)


@requires_graph
def test_offers_is_the_noise_corrected_boundary():
    """The OFFERS edge-set IS the noise-correction: a vocational family that reaches an AM occupation but is
    marked crosswalk-noise for AM (Commercial Music) is offered by NO sector for AM, so it never enters the
    boundary — the graph fact that retires excluded_tops."""
    from ontology import sector_graph
    from partnerships.sectors import SECTORS

    sector_graph.load()
    offers_adm = sector_graph.sector_offers("adm")
    # 100500 Commercial Music crosswalks to an AM SOC but is adm crosswalk-noise → not offered.
    assert "100500" in SECTORS["adm"].excluded_tops
    assert "100500" not in offers_adm
