"""Unit tests for ontology/regions.py.

Targets the ensure_college_region_link helper, which owns the MERGE
that writes the (College)-[:IN_MARKET]->(Region) edge. That edge is
the precondition for every industry-side traversal — occupation
demand, employer matching, partnership alignment precompute — so any
drift in the helper's behavior silently corrupts downstream queries.
The helper is called from both backend/courses/load.py::load_college
and backend/occupations/load.py::load_industry, and the test below
verifies the two properties that matter independent of a live Neo4j
driver: the mapping-lookup return value, and that the MERGE is
issued against the right college / region / display name when a
mapping exists.

The driver is replaced with a MagicMock so the tests run with zero
network cost. The correctness of the underlying Cypher MERGE is
covered by the load_industry integration path, which has been
emitting the same MERGE since the structure was introduced.

Coverage:
  - ensure_college_region_link returns False and never touches the
    driver when the college has no entry in COLLEGE_COE_REGION
  - ensure_college_region_link returns True, issues exactly one
    MERGE, and passes the canonical COE region code + display name
    when the college has a mapping
  - Repeated calls for an unmapped college remain side-effect-free
"""

from unittest.mock import MagicMock

from ontology.regions import (
    COE_REGION_DISPLAY,
    COLLEGE_COE_REGION,
    ensure_college_region_link,
)


def _mock_driver() -> tuple[MagicMock, MagicMock]:
    """Return (driver_mock, session_mock) wired so `with
    driver.session() as session` yields the session mock."""
    driver = MagicMock(name="driver")
    session = MagicMock(name="session")
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver, session


class TestEnsureCollegeRegionLink:
    def test_returns_false_for_unmapped_college(self):
        driver, _ = _mock_driver()
        result = ensure_college_region_link(driver, "Unmapped Community College")
        assert result is False
        driver.session.assert_not_called()

    def test_returns_true_for_mapped_college(self):
        # Foothill has been in COLLEGE_COE_REGION since the structure
        # existed — a stable anchor for this assertion.
        driver, _ = _mock_driver()
        assert ensure_college_region_link(driver, "Foothill College") is True

    def test_issues_merge_with_canonical_region_and_display(self):
        college = "Foothill College"
        expected_region = COLLEGE_COE_REGION[college]
        expected_display = COE_REGION_DISPLAY[expected_region]

        driver, session = _mock_driver()
        ensure_college_region_link(driver, college)

        session.run.assert_called_once()
        _, kwargs = session.run.call_args
        assert kwargs["college"] == college
        assert kwargs["region"] == expected_region
        assert kwargs["display"] == expected_display

    def test_repeated_unmapped_calls_are_side_effect_free(self):
        driver, _ = _mock_driver()
        for _ in range(3):
            assert ensure_college_region_link(driver, "Nonexistent College") is False
        driver.session.assert_not_called()

    def test_uses_region_code_as_display_when_display_missing(self):
        # Belt and suspenders: if a COE region code were somehow
        # missing from COE_REGION_DISPLAY, the helper should fall back
        # to the code itself rather than crash. We verify this by
        # monkey-patching a synthetic college mapping in-place.
        college = "Synthetic Test College"
        synthetic_region = "ZZ"
        COLLEGE_COE_REGION[college] = synthetic_region
        try:
            driver, session = _mock_driver()
            assert ensure_college_region_link(driver, college) is True
            _, kwargs = session.run.call_args
            assert kwargs["region"] == synthetic_region
            assert kwargs["display"] == synthetic_region
        finally:
            del COLLEGE_COE_REGION[college]
