"""Unit tests for ontology/crosswalks.py — the PCAH CTE filter path.

Guards the two loaders introduced to support institutional CTE scoping:
_load_pcah_cte_top4 reads the Chancellor's Office TOP Codes to Sectors
file and normalizes TOP6 integer codes to TOP4 strings matching the
existing top_cip_crosswalk; cte_reachable_socs composes the PCAH TOP4 set
with the existing TOP→CIP→SOC chain to produce the set of SOCs the
ontology recognizes as CTE. Non-goals: exhaustive mapping correctness
(the source data is authoritative) and build_demand_profile end-to-end
(exercised by integration tests).

Coverage:
  - _load_pcah_cte_top4 loads the expected PCAH sector mapping shape
  - TOP6→TOP4 conversion formula yields the same keys the existing crosswalk uses
  - PCAH TOP4 keys overlap substantially with the TOP→CIP crosswalk
  - cte_reachable_socs includes the core CTE trades
  - cte_reachable_socs excludes Bachelor's-entry engineering transfer pathways
  - cte_reachable_socs excludes academic-transfer PhD SOCs
  - cte_reachable_socs is cached and returns the same object across calls
"""

from ontology.crosswalks import (
    _load_pcah_cte_top4,
    _load_top_to_cip,
    cte_reachable_socs,
)


class TestLoadPcahCteTop4:
    def test_returns_nonempty_mapping(self):
        mapping = _load_pcah_cte_top4()
        assert len(mapping) > 100, "PCAH file is expected to have >100 distinct TOP4 codes"

    def test_values_are_sector_strings(self):
        mapping = _load_pcah_cte_top4()
        for top4, sector in mapping.items():
            assert isinstance(top4, str)
            assert isinstance(sector, str)
            assert len(top4) == 4
            assert top4.isdigit()

    def test_known_sectors_present(self):
        mapping = _load_pcah_cte_top4()
        sectors = set(mapping.values())
        assert "Agriculture, Water and Environmental Technologies" in sectors
        assert "Advanced Manufacturing" in sectors
        assert "Energy, Construction and Utilities" in sectors
        assert "Health" in sectors


class TestTop6ToTop4Conversion:
    """The conversion formula is f'{top6 // 100:04d}'.

    Verified against known PCAH entries and against the existing TOP→CIP
    crosswalk, which indexes on the same TOP4 shape.
    """

    def test_agriculture_top6_10100_maps_to_top4_0101(self):
        mapping = _load_pcah_cte_top4()
        # PCAH TOP6 10100 (Agriculture Tech General) → TOP4 "0101"
        assert mapping.get("0101") == "Agriculture, Water and Environmental Technologies"

    def test_cosmetology_top6_300700_maps_to_top4_3007(self):
        mapping = _load_pcah_cte_top4()
        # PCAH TOP6 300700 (Cosmetology and Barbering) → TOP4 "3007"
        assert mapping.get("3007") == "Business and Entrepreneurship"

    def test_pcah_top4_keys_exist_in_top_cip_crosswalk(self):
        """Every PCAH TOP4 should also appear in the existing crosswalk for the composition to work."""
        pcah_keys = set(_load_pcah_cte_top4().keys())
        top_cip_keys = set(_load_top_to_cip().keys())
        # Not required that ALL PCAH TOP4s appear (some CTE programs may have
        # no CIP mapping), but the overlap should be substantial.
        overlap = pcah_keys & top_cip_keys
        assert len(overlap) > len(pcah_keys) * 0.8, (
            f"Only {len(overlap)}/{len(pcah_keys)} PCAH TOP4s map into the crosswalk — "
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
        """PhD-entry SOCs reached only via transfer-academic (non-CTE) TOPs are excluded.

        Note: not *all* PhD-entry SOCs are excluded — some are reachable through
        CTE-sector TOPs (e.g. Medical Scientists 19-1042 via the Health sector's
        TOP 1309). The filter expresses "institutionally classified as CTE,"
        not "does not require graduate credentials." The two are different
        axes by design — education_level remains as node metadata for the
        small minority of high-credential occupations that CTE TOPs touch.
        """
        socs = cte_reachable_socs()
        for soc, name in [
            ("19-2011", "Astronomers"),
            ("19-2012", "Physicists"),
        ]:
            assert soc not in socs, f"{name} ({soc}) should not be in CTE scope"

    def test_returns_same_set_across_calls(self):
        """Cached function — repeated calls should return identical sets."""
        assert cte_reachable_socs() is cte_reachable_socs()
