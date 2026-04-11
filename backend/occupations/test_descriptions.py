"""Unit tests for occupations/descriptions.py — occupation description generation.

descriptions.py produces the `description` field that occupations.json
carries into the graph. The generator is a two-tier hybrid: a hand-curated
dict of SOC-specific descriptions and a title-pattern fallback for anything
the dict does not cover. These tests guard the pattern fallback (the path
most prone to drift) and pin a few representative dict hits so that an
accidental SPECIFIC_DESCRIPTIONS wipe fails loudly.

Coverage:
  - SOC-specific descriptions are returned verbatim for known entries
  - Pattern fallback handles manager, technician, engineer, analyst, and
    teacher titles
  - "All other" titles get a specialized-duties description
  - Unknown titles still return a non-empty description
"""

from occupations.descriptions import SPECIFIC_DESCRIPTIONS, generate_description


class TestSpecificDescriptions:
    def test_returns_specific_description_for_software_developer(self):
        desc = generate_description("15-1252", "Software Developers")
        assert desc == SPECIFIC_DESCRIPTIONS["15-1252"]
        assert "software" in desc.lower()

    def test_returns_specific_description_for_registered_nurse(self):
        desc = generate_description("29-1141", "Registered Nurses")
        assert desc == SPECIFIC_DESCRIPTIONS["29-1141"]


class TestPatternFallback:
    def test_manager_title_gets_management_description(self):
        desc = generate_description("11-9999", "Operations Managers")
        assert "manag" in desc.lower() or "coordinat" in desc.lower()
        assert desc.endswith(".")

    def test_technician_title_gets_technical_description(self):
        desc = generate_description("99-0001", "Fabrication Technicians")
        assert "technical" in desc.lower()

    def test_engineer_title_gets_engineering_description(self):
        desc = generate_description("99-0002", "Systems Engineers")
        assert "engineering" in desc.lower()

    def test_analyst_title_gets_analysis_description(self):
        desc = generate_description("99-0003", "Market Analysts")
        assert "analyz" in desc.lower() or "decision" in desc.lower()

    def test_all_other_title_gets_specialized_description(self):
        desc = generate_description("99-0004", "Managers, All Other")
        assert "specialized" in desc.lower()

    def test_postsecondary_teacher_gets_college_level_description(self):
        desc = generate_description("25-1125", "History Teachers, Postsecondary")
        assert "college" in desc.lower() or "university" in desc.lower()


class TestFallbackNeverReturnsEmpty:
    def test_unknown_title_returns_non_empty_description(self):
        desc = generate_description("99-9999", "Completely Unknown Title")
        assert isinstance(desc, str)
        assert len(desc) > 0
        assert desc.endswith(".")
