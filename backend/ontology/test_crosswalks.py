"""Unit tests for ontology/crosswalks.py — the PCAH CTE filter path.

Guards the loaders supporting institutional CTE scoping:
_load_pcah_cte_top6 reads the Chancellor's Office TOP Codes to Sectors
file; _load_top_to_cip parses the TOP6→CIP crosswalk; cte_reachable_socs
composes the PCAH TOP6 set with the TOP6→CIP→SOC chain to produce the
SOC set the ontology recognizes as CTE. Non-goals: exhaustive mapping
correctness (the source data is authoritative) and build_demand_profile
end-to-end (exercised by integration tests).

All four data files (PCAH, TOP→CIP, CIP→SOC, COE demand) ship in-repo,
so every test runs unconditionally — no skipif gates for missing
external datasets.

Coverage:
  - _load_pcah_cte_top6 loads the expected PCAH sector mapping shape
  - TOP6 codes are six-digit strings with leading zeros
  - PCAH TOP6 keys overlap substantially with the TOP→CIP crosswalk
  - cte_reachable_socs includes the core CTE trades
  - cte_reachable_socs excludes Bachelor's-entry engineering transfer pathways
  - cte_reachable_socs excludes academic-transfer PhD SOCs
  - cte_reachable_socs is cached and returns the same object across calls
"""

from ontology.crosswalks import (
    _load_pcah_cte_top6,
    _load_top_to_cip,
    _load_vocational_top6,
    cte_reachable_socs,
    is_cte_top4_family,
    is_vocational,
)


class TestIsVocational:
    """is_vocational — the authoritative TOP6-exact CTE gate (CCCCO Taxonomy of
    Programs 7th Ed vocational asterisk), distinct from the looser
    is_cte_top4_family heuristic which over-includes transfer siblings."""

    def test_loads_expected_count(self):
        # 273 vocational of 408 codes in the 7th Edition.
        assert 250 <= len(_load_vocational_top6()) <= 300

    def test_known_vocational(self):
        for top6 in ("043000", "120800", "300700", "083520", "123010"):
            assert is_vocational(top6), top6

    def test_known_non_vocational_transfer(self):
        for top6 in ("040100", "190500", "083500", "220600", "061200"):
            assert not is_vocational(top6), top6

    def test_exact_excludes_family_false_positives(self):
        # 083500 Physical Education (transfer) shares the 0835 family with the
        # vocational 083520 Fitness Trainer: the family heuristic includes it,
        # the authoritative exact gate does not.
        assert is_cte_top4_family("083500") is True
        assert is_vocational("083500") is False

    def test_none_and_empty(self):
        assert is_vocational(None) is False
        assert is_vocational("") is False


class TestLoadPcahCteTop6:
    def test_returns_nonempty_mapping(self):
        mapping = _load_pcah_cte_top6()
        assert len(mapping) > 100, "PCAH file is expected to have >100 distinct TOP6 codes"

    def test_values_are_sector_strings(self):
        mapping = _load_pcah_cte_top6()
        for top6, sector in mapping.items():
            assert isinstance(top6, str)
            assert isinstance(sector, str)
            assert len(top6) == 6
            assert top6.isdigit()

    def test_known_sectors_present(self):
        mapping = _load_pcah_cte_top6()
        sectors = set(mapping.values())
        assert "Agriculture, Water and Environmental Technologies" in sectors
        assert "Advanced Manufacturing" in sectors
        assert "Energy, Construction and Utilities" in sectors
        assert "Health" in sectors


class TestTop6Keys:
    """TOP6 codes are preserved as six-digit strings with leading zeros.

    Verified against known PCAH entries and against the TOP→CIP crosswalk
    which indexes on the same TOP6 shape.
    """

    def test_agriculture_top6_010100_is_present(self):
        mapping = _load_pcah_cte_top6()
        # PCAH TOP6 10100 (Agriculture Tech General) → "010100"
        assert mapping.get("010100") == "Agriculture, Water and Environmental Technologies"

    def test_cosmetology_top6_300700_is_present(self):
        mapping = _load_pcah_cte_top6()
        # PCAH TOP6 300700 (Cosmetology and Barbering)
        assert mapping.get("300700") == "Business and Entrepreneurship"

    def test_pcah_top6_keys_exist_in_top_cip_crosswalk(self):
        """PCAH TOP6 keys should substantially overlap the crosswalk's TOP6 keys."""
        pcah_keys = set(_load_pcah_cte_top6().keys())
        top_cip_keys = set(_load_top_to_cip().keys())
        overlap = pcah_keys & top_cip_keys
        assert len(overlap) > len(pcah_keys) * 0.8, (
            f"Only {len(overlap)}/{len(pcah_keys)} PCAH TOP6s map into the crosswalk — "
            "suggests a code normalization mismatch."
        )


class TestCteReachableSocs:
    def test_returns_nonempty_set(self):
        socs = cte_reachable_socs()
        assert len(socs) > 100

    def test_includes_core_trades(self):
        socs = cte_reachable_socs()
        trades = {
            "47-2111": "Electricians",
            "51-4121": "Welders",
            "47-2152": "Plumbers",
            "51-4041": "Machinists",
            "47-2031": "Carpenters",
            "49-9021": "HVAC Mechanics",
            "49-3023": "Automotive Service Technicians",
        }
        for soc, name in trades.items():
            assert soc in socs, f"{name} ({soc}) should be in CTE scope"

    def test_excludes_bachelors_engineering_transfer_pathways(self):
        socs = cte_reachable_socs()
        non_cte = {
            "17-2051": "Civil Engineers",
            "17-2141": "Mechanical Engineers",
            "17-2041": "Chemical Engineers",
            "17-2031": "Bioengineers and Biomedical Engineers",
            "17-2081": "Environmental Engineers",
        }
        for soc, name in non_cte.items():
            assert soc not in socs, f"{name} ({soc}) should not be in CTE scope"

    def test_excludes_academic_transfer_terminus(self):
        """PhD-entry SOCs reached only via transfer-academic (non-CTE) TOPs are excluded."""
        socs = cte_reachable_socs()
        for soc, name in [
            ("19-2011", "Astronomers"),
            ("19-2012", "Physicists"),
        ]:
            assert soc not in socs, f"{name} ({soc}) should not be in CTE scope"

    def test_returns_same_set_across_calls(self):
        """Cached function — repeated calls should return identical sets."""
        assert cte_reachable_socs() is cte_reachable_socs()
