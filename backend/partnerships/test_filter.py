"""Unit tests for the deterministic occupation selector.

The legacy LLM-based `_select_occupation` was retired (C2) in favor of
a deterministic crosswalk-depth ranker. The selection is itself an
institutional question: of the SOCs the employer hires for, which is
most institutionally aligned with the college's curriculum?

The ranker sorts by:
  1. aligned_course_count DESC — courses with PREPARES_FOR edges to this SOC
  2. annual_openings DESC — regional labor-market demand
  3. soc_code ASC — deterministic tiebreaker

Coverage:
  - Empty occupation_evidence returns {} cleanly
  - Aligned-course-count is the primary sort key (depth wins over volume)
  - Annual openings is the tiebreaker when alignment is equal
  - SOC code is the deterministic final tiebreaker
  - The selected occupation is paired with deterministic core-skills
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_driver(session_responses: list):
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


def _gathered(occupation_evidence, college="Foothill College"):
    """Minimal GatheredContext stub for selector tests."""
    from partnerships.gather import GatheredContext

    return GatheredContext(
        employer_name="Test Corp",
        sector="Manufacturing",
        swp_sectors=["Advanced Manufacturing"],
        description="",
        regions=["Bay"],
        college=college,
        occupation_evidence=occupation_evidence,
    )


class TestSelectOccupationDeterministic:
    def test_empty_occupation_evidence_returns_empty_dict(self):
        from partnerships import filter as flt

        driver, _ = _mock_driver([{"data": []}])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered([]))
        assert result == {}

    def test_alignment_depth_dominates_openings(self):
        """A SOC with 12 aligned courses and 100 openings should beat
        a SOC with 0 aligned courses and 10,000 openings. Institutional
        pathway alignment is the primary signal."""
        from partnerships import filter as flt

        occs = [
            {"title": "Volume Role", "soc_code": "11-1011", "annual_openings": 10000},
            {"title": "Aligned Niche", "soc_code": "51-9061", "annual_openings": 100},
        ]
        # First call: alignment count for both SOCs.
        # Second call: core skills lookup for the winner.
        driver, _ = _mock_driver([
            {"data": [
                {"soc": "11-1011", "aligned_course_count": 0},
                {"soc": "51-9061", "aligned_course_count": 12},
            ]},
            {"data": [{"skill": "Quality Control", "course_count": 12}]},
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered(occs))
        assert result["soc_code"] == "51-9061"
        assert result["title"] == "Aligned Niche"

    def test_openings_break_alignment_tie(self):
        """When alignment is equal, regional openings rank."""
        from partnerships import filter as flt

        occs = [
            {"title": "Lower Demand", "soc_code": "11-1011", "annual_openings": 100},
            {"title": "Higher Demand", "soc_code": "51-9061", "annual_openings": 1000},
        ]
        driver, _ = _mock_driver([
            {"data": [
                {"soc": "11-1011", "aligned_course_count": 5},
                {"soc": "51-9061", "aligned_course_count": 5},
            ]},
            {"data": [{"skill": "Generic", "course_count": 1}]},
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered(occs))
        assert result["soc_code"] == "51-9061"

    def test_soc_code_breaks_final_tie(self):
        """Equal alignment and equal openings — SOC code (lex ASC) wins."""
        from partnerships import filter as flt

        occs = [
            {"title": "B-First", "soc_code": "51-9061", "annual_openings": 500},
            {"title": "A-First", "soc_code": "11-1011", "annual_openings": 500},
        ]
        driver, _ = _mock_driver([
            {"data": [
                {"soc": "51-9061", "aligned_course_count": 5},
                {"soc": "11-1011", "aligned_course_count": 5},
            ]},
            {"data": [{"skill": "Generic", "course_count": 1}]},
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered(occs))
        # 11-1011 < 51-9061 lexicographically.
        assert result["soc_code"] == "11-1011"

    def test_returns_core_skills_for_selected_occupation(self):
        """The selected occupation is paired with deterministic core
        skills from _select_core_skills_for."""
        from partnerships import filter as flt

        occs = [{"title": "Inspectors", "soc_code": "51-9061", "annual_openings": 1000}]
        driver, _ = _mock_driver([
            {"data": [{"soc": "51-9061", "aligned_course_count": 12}]},
            {"data": [
                {"skill": "Quality Control", "course_count": 12},
                {"skill": "Inspection", "course_count": 8},
                {"skill": "Documentation", "course_count": 4},
            ]},
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered(occs))
        assert result["soc_code"] == "51-9061"
        assert result["core_skills"] == ["Quality Control", "Inspection", "Documentation"]

    def test_no_aligned_curriculum_still_returns_top_by_openings(self):
        """When no SOC has any aligned curriculum at this college, the
        highest-openings SOC still wins by tiebreaker. The artifact
        downstream will then honestly surface an empty curriculum_evidence."""
        from partnerships import filter as flt

        occs = [
            {"title": "A", "soc_code": "11-1011", "annual_openings": 200},
            {"title": "B", "soc_code": "51-9061", "annual_openings": 500},
        ]
        driver, _ = _mock_driver([
            {"data": [
                {"soc": "11-1011", "aligned_course_count": 0},
                {"soc": "51-9061", "aligned_course_count": 0},
            ]},
            {"data": []},  # core skills empty
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            result = flt._select_occupation(_gathered(occs))
        assert result["soc_code"] == "51-9061"
        # Empty core_skills is fine; characterization-only signal.
        assert result["core_skills"] == []

    def test_no_llm_call_under_any_branch(self):
        """The deterministic selector must never construct an Anthropic
        client. The institutional-deference commitment forbids LLM
        judgment in the gating layer."""
        from partnerships import filter as flt

        occs = [{"title": "Inspectors", "soc_code": "51-9061", "annual_openings": 100}]
        driver, _ = _mock_driver([
            {"data": [{"soc": "51-9061", "aligned_course_count": 1}]},
            {"data": [{"skill": "Quality Control", "course_count": 1}]},
        ])
        with patch.object(flt, "get_driver", return_value=driver):
            with patch("anthropic.Anthropic") as mock_anthropic:
                flt._select_occupation(_gathered(occs))
                mock_anthropic.assert_not_called()
