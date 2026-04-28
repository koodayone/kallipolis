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
  - Compound BLS titles (comma-separated role-noun lists) do not produce
    stranded commas — _clean_field normalizes the residue, and prominent
    compound SOCs ship hand-crafted overrides
"""

import re

from occupations.descriptions import (
    SPECIFIC_DESCRIPTIONS,
    _clean_field,
    generate_description,
)


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


class TestCleanField:
    """Pin the comma-residue normalization helper that backstops the
    pattern-based generator on compound BLS titles."""

    def test_collapses_consecutive_commas_left_after_role_noun_strip(self):
        # The shape produced by stripping each role-noun out of
        # "Inspectors, Testers, Sorters, Samplers, and Weighers".
        assert _clean_field(", , , samplers, and weighers") == "samplers, and weighers"

    def test_collapses_double_commas_with_intervening_whitespace(self):
        assert _clean_field("foo,  ,  ,  bar") == "foo, bar"

    def test_strips_leading_orphan_commas_and_whitespace(self):
        assert _clean_field("  ,  bar") == "bar"

    def test_strips_trailing_orphan_commas(self):
        assert _clean_field("bar, , ,") == "bar"

    def test_returns_empty_when_input_is_only_commas_and_spaces(self):
        assert _clean_field("  ,  ,  ") == ""

    def test_preserves_well_formed_input(self):
        assert _clean_field("metal and plastic") == "metal and plastic"


class TestCompoundTitleResilience:
    """Regression coverage for the stranded-comma bug in pattern-based
    generation. The bug shipped 16 malformed descriptions to occupations.json
    before P5; these tests ensure neither the helper nor the prominent
    overrides regress."""

    _STRANDED_COMMA = re.compile(r",\s*,|\bin\s*,|\bin\s+and\b")

    def test_inspectors_testers_sorters_samplers_and_weighers_is_clean(self):
        desc = generate_description("51-9061", "Inspectors, Testers, Sorters, Samplers, and Weighers")
        assert not self._STRANDED_COMMA.search(desc), (
            f"Compound title for SOC 51-9061 produced stranded commas: {desc!r}"
        )
        # Hand-crafted override should describe what the role actually does.
        assert "inspect" in desc.lower() or "quality" in desc.lower()

    def test_machine_operators_compound_title_does_not_strand_commas(self):
        # Title with the "Setters, Operators, and Tenders" pattern used to
        # produce ", , and tenders, metal and plastic" residue.
        desc = generate_description(
            "99-9998",
            "Cutting, Punching, and Press Machine Setters, Operators, and Tenders, Metal and Plastic",
        )
        assert not self._STRANDED_COMMA.search(desc), (
            f"Compound machine-operator title produced stranded commas: {desc!r}"
        )

    def test_compound_title_overrides_present_for_known_offenders(self):
        # The four SOCs that ship hand-crafted compound-title overrides.
        for soc in ("51-9061", "51-4122", "51-9012", "51-9124"):
            assert soc in SPECIFIC_DESCRIPTIONS, (
                f"SOC {soc} should ship a hand-crafted override; without it, "
                f"the pattern generator produces stranded commas."
            )
