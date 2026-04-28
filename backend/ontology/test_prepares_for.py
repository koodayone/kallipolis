"""Unit tests for ontology.prepares_for — Course→Occupation edge materializer.

The materializer is the load-time step that turns the in-memory TOP6→SOC
crosswalk into graph edges. Each Course's top_code property maps via
ontology.crosswalks.top6_to_soc to a set of SOC codes; one
Course-[:PREPARES_FOR {via_top}]->Occupation edge is written per pair
where the Occupation exists. The edge unblocks partnership Cypher to
gate curriculum and student evidence on TOP-SOC alignment instead of
skills-overlap (the prior gate produced cross-domain false positives:
nursing students surfacing under manufacturing partnerships, etc.).

Tests run against an in-memory neo4j-driver mock so they execute on any
machine, regardless of whether the cc_dataset crosswalk files are
available. The crosswalk itself is mocked at the module boundary so
test fixtures stay deterministic.

Coverage:
  - Idempotency: re-running drops stale PREPARES_FOR edges before writing
  - One TOP6 → many SOCs fans out to one edge per (course, soc) pair
  - via_top property is set on each created edge
  - Stats accurately report dropped, created, and missing-occupation skips
  - Empty top_codes (e.g. occupations pipeline not run yet) is a warning,
    not a failure
  - Pairs whose Occupation is absent in the graph are counted in
    edges_skipped_missing_occupation, not silently lost
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ── Mock-driver fixtures ────────────────────────────────────────────────────
#
# The neo4j Driver / Session / Result interfaces are mocked at the level
# the materializer actually calls — session.run() returns an object with
# .single() and .data(). The test injects a sequence of responses; the
# materializer's Cypher calls are inspected via mock.call_args_list.


def _mock_driver(session_responses: list):
    """Build a mock Driver whose single session returns the given responses
    from session.run() in order. Each entry is a dict {"single": ..., "data": ...}
    where either side is the value to return from the corresponding accessor.
    """
    session = MagicMock()
    runs: list[MagicMock] = []
    for resp in session_responses:
        result = MagicMock()
        if "single" in resp:
            result.single.return_value = resp["single"]
        if "data" in resp:
            result.data.return_value = resp["data"]
        runs.append(result)
    session.run.side_effect = runs

    session_cm = MagicMock()
    session_cm.__enter__ = MagicMock(return_value=session)
    session_cm.__exit__ = MagicMock(return_value=False)

    driver = MagicMock()
    driver.session.return_value = session_cm
    return driver, session


class TestMaterializePreparesFor:
    """Behavior of the edge materializer under varied graph + crosswalk states."""

    def test_writes_one_edge_per_course_soc_pair_with_via_top(self):
        """Two courses sharing TOP 095680, which crosswalks to two SOCs,
        should produce four PREPARES_FOR edges (one per Course×SOC), each
        carrying via_top=095680."""
        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 0}},  # drop stale: zero
            {"data": [{"top_code": "095680", "course_count": 2}]},  # distinct top_codes
            {"data": [{"soc_code": "51-9061"}, {"soc_code": "51-9011"}]},  # occupations present
            {"single": {"n": 4}},  # edges created
        ])
        with patch.object(prepares_for, "top6_to_soc", return_value={"095680": {"51-9061", "51-9011"}}):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["edges_dropped"] == 0
        assert stats["edges_created"] == 4
        assert stats["top_codes"] == 1
        assert stats["soc_codes_in_crosswalk"] == 2
        assert stats["edges_skipped_missing_occupation"] == 0

        # The edge-write Cypher should pass via_top through and match on
        # both top_code (course filter) and soc_code (occupation filter).
        write_call = session.run.call_args_list[-1]
        cypher = write_call.args[0]
        assert "PREPARES_FOR" in cypher
        assert "via_top" in cypher

    def test_drops_stale_edges_before_writing(self):
        """Re-running on a college that already has 12 PREPARES_FOR edges
        should report edges_dropped=12 and a fresh edges_created count."""
        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 12}},  # drop stale
            {"data": [{"top_code": "095680", "course_count": 2}]},
            {"data": [{"soc_code": "51-9061"}]},
            {"single": {"n": 2}},
        ])
        with patch.object(prepares_for, "top6_to_soc", return_value={"095680": {"51-9061"}}):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["edges_dropped"] == 12
        assert stats["edges_created"] == 2
        # First call must be the DELETE; idempotency depends on it.
        first_cypher = session.run.call_args_list[0].args[0]
        assert "DELETE" in first_cypher

    def test_counts_pairs_whose_occupation_is_missing(self):
        """When the crosswalk yields SOCs not present as Occupation nodes
        (e.g. CTE-filtered out at occupation load), each missing pair must
        be counted in edges_skipped_missing_occupation — not silently lost."""
        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 0}},
            {"data": [{"top_code": "095680", "course_count": 1}]},
            # Crosswalk yields 51-9061 and 51-9011, but only 51-9061 is in graph.
            {"data": [{"soc_code": "51-9061"}]},
            {"single": {"n": 1}},  # only one edge actually written
        ])
        with patch.object(prepares_for, "top6_to_soc", return_value={"095680": {"51-9061", "51-9011"}}):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["edges_created"] == 1
        assert stats["edges_skipped_missing_occupation"] == 1
        assert stats["soc_codes_in_crosswalk"] == 2

    def test_no_courses_with_top_returns_early_with_warning(self, caplog):
        """If no Course nodes carry top_code (load order broken), the
        materializer must warn and return without attempting writes."""
        import logging

        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 0}},  # drop stale
            {"data": []},           # no top_codes
        ])
        with caplog.at_level(logging.WARNING, logger="ontology.prepares_for"):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["courses_with_top"] == 0
        assert stats["edges_created"] == 0
        assert any("no Course nodes with top_code" in r.message for r in caplog.records)
        # Only the DELETE + the DISTINCT top_codes query should have run.
        assert session.run.call_count == 2

    def test_top_codes_with_no_crosswalk_entries_writes_zero(self):
        """When every TOP6 returns an empty crosswalk (synthetic seed with
        non-CTE TOPs, for instance), the function returns cleanly without
        executing the write step."""
        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 0}},
            {"data": [{"top_code": "999999", "course_count": 1}]},
        ])
        with patch.object(prepares_for, "top6_to_soc", return_value={}):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["edges_created"] == 0
        assert stats["soc_codes_in_crosswalk"] == 0
        # No occupation pre-flight, no edge write — only DELETE + DISTINCT ran.
        assert session.run.call_count == 2

    def test_many_to_many_fanout_is_preserved(self):
        """Multiple TOPs each crosswalking to overlapping SOCs should
        produce one edge per distinct (Course-via-TOP, SOC) pair. The
        via_top property keeps the audit trail intact."""
        from ontology import prepares_for

        driver, session = _mock_driver([
            {"single": {"n": 0}},
            {"data": [
                {"top_code": "095680", "course_count": 2},
                {"top_code": "094610", "course_count": 1},
            ]},
            {"data": [
                {"soc_code": "51-9061"},
                {"soc_code": "47-2231"},
            ]},
            {"single": {"n": 5}},
        ])
        crosswalk = {
            "095680": {"51-9061"},
            "094610": {"51-9061", "47-2231"},
        }
        with patch.object(prepares_for, "top6_to_soc", return_value=crosswalk):
            stats = prepares_for.materialize_prepares_for(driver, "Foothill College")

        assert stats["top_codes"] == 2
        # Crosswalk yields {51-9061, 47-2231} as the union.
        assert stats["soc_codes_in_crosswalk"] == 2
        # Both SOCs are present, so nothing is skipped.
        assert stats["edges_skipped_missing_occupation"] == 0
        # The pairs UNWIND list passed to the write call must include
        # both TOPs (the Cypher MATCH on top_code disambiguates which
        # courses receive which edges).
        write_call = session.run.call_args_list[-1]
        passed_pairs = write_call.kwargs["pairs"]
        passed_tops = {p["top_code"] for p in passed_pairs}
        assert passed_tops == {"095680", "094610"}


# ── Per-course MCF lookup tests ────────────────────────────────────────────
#
# Pure-Python path; runs without Neo4j or external crosswalk data.


class TestLookupTop6PerCourse:
    """The new helper that returns a per-course mapping (vs. the existing
    set-returning lookup_top6). Required for setting Course.top_code
    one course at a time during load."""

    def test_returns_none_for_courses_not_in_mcf(self):
        from ontology import mcf_lookup

        with patch.object(mcf_lookup, "_load_mcf_index", return_value={}), \
             patch.object(mcf_lookup, "_build_prefix_scan_index", return_value={}):
            result = mcf_lookup.lookup_top6_per_course(["CT 100", "CT 200"], "Foothill")

        assert result == {"CT 100": None, "CT 200": None}

    def test_returns_per_course_top6_on_exact_match(self):
        from ontology import mcf_lookup

        index = {
            ("CT100", "foothill"): "095680",
            ("CT200", "foothill"): "094610",
        }
        with patch.object(mcf_lookup, "_load_mcf_index", return_value=index), \
             patch.object(mcf_lookup, "_build_prefix_scan_index", return_value={}):
            result = mcf_lookup.lookup_top6_per_course(["CT 100", "CT 200"], "Foothill College")

        assert result == {"CT 100": "095680", "CT 200": "094610"}

    def test_falls_back_to_prefix_match(self):
        """Catalog code 'CT100' should match MCF 'CT100AB' via the prefix
        index — same fallback the set-returning lookup does."""
        from ontology import mcf_lookup

        with patch.object(mcf_lookup, "_load_mcf_index", return_value={}), \
             patch.object(
                 mcf_lookup, "_build_prefix_scan_index",
                 return_value={"foothill": [("CT100AB", "095680")]},
             ):
            result = mcf_lookup.lookup_top6_per_course(["CT 100"], "Foothill College")

        assert result == {"CT 100": "095680"}

    def test_existing_set_lookup_delegates_to_per_course(self):
        """lookup_top6 (the original set-returning function) is now a thin
        wrapper around lookup_top6_per_course; verify the contract didn't
        regress."""
        from ontology import mcf_lookup

        index = {
            ("CT100", "foothill"): "095680",
            ("CT200", "foothill"): "094610",
        }
        with patch.object(mcf_lookup, "_load_mcf_index", return_value=index), \
             patch.object(mcf_lookup, "_build_prefix_scan_index", return_value={}):
            result = mcf_lookup.lookup_top6(["CT 100", "CT 200", "MISSING 999"], "Foothill College")

        assert result == {"095680", "094610"}
