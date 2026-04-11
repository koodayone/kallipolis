"""Unit tests for occupations/assign_skills.py — taxonomy validation and retry selection.

assign_skills.py calls Gemini Flash in batches to assign skills from the
unified taxonomy to each occupation, then validates the response and retries
any occupation whose post-validation skill count is below the floor. These
tests guard the pure helpers that do the validation and retry-queue math so
that taxonomy drift and floor-rule changes are caught without a Gemini call.

No Gemini client is instantiated in this file. The network-bound pieces
(_assign_batch, _run_initial_pass, _run_retry_pass) are covered by the
integration suite; only the pure partitioning and selection logic is tested
here.

Coverage:
  - Taxonomy filter partitions proposed skills into valid and invalid
  - Taxonomy filter deduplicates valid skills while preserving order
  - Taxonomy filter returns empty lists when the input is empty
  - Floor selector returns SOCs whose skill count is strictly below the floor
  - Floor selector treats missing `skills` keys as below the floor
  - Apply-mapping updates skills and records rejected terms per SOC
  - Apply-mapping leaves unmapped occupations untouched
  - Retry line formatter carries currently-accepted skills and rejected terms
"""

from occupations.assign_skills import (
    MIN_SKILLS,
    _apply_mapping,
    _below_floor,
    _filter_to_taxonomy,
    _format_retry_line,
)

TAXONOMY = {
    "Data Analysis",
    "Project Management",
    "Regulatory Compliance",
    "Patient Assessment",
    "Clinical Documentation",
    "Customer Service",
    "Safety Protocols",
}


class TestFilterToTaxonomy:
    def test_partitions_valid_and_invalid_skills(self):
        valid, invalid = _filter_to_taxonomy(
            ["Data Analysis", "Invented Skill", "Project Management"],
            TAXONOMY,
        )
        assert valid == ["Data Analysis", "Project Management"]
        assert invalid == ["Invented Skill"]

    def test_preserves_input_order_for_valid_skills(self):
        valid, _ = _filter_to_taxonomy(
            ["Project Management", "Data Analysis"],
            TAXONOMY,
        )
        assert valid == ["Project Management", "Data Analysis"]

    def test_deduplicates_repeated_valid_skills(self):
        valid, _ = _filter_to_taxonomy(
            ["Data Analysis", "Data Analysis", "Project Management"],
            TAXONOMY,
        )
        assert valid == ["Data Analysis", "Project Management"]

    def test_returns_empty_lists_for_empty_input(self):
        valid, invalid = _filter_to_taxonomy([], TAXONOMY)
        assert valid == []
        assert invalid == []

    def test_returns_only_invalid_when_nothing_in_taxonomy(self):
        valid, invalid = _filter_to_taxonomy(["Foo", "Bar"], TAXONOMY)
        assert valid == []
        assert invalid == ["Foo", "Bar"]


class TestBelowFloor:
    def test_returns_soc_codes_below_the_floor(self):
        occs = [
            {"soc_code": "A", "skills": ["x"] * (MIN_SKILLS - 1)},
            {"soc_code": "B", "skills": ["x"] * MIN_SKILLS},
            {"soc_code": "C", "skills": ["x"] * (MIN_SKILLS + 3)},
        ]
        assert _below_floor(occs) == ["A"]

    def test_treats_missing_skills_key_as_below_floor(self):
        occs = [{"soc_code": "A"}]
        assert _below_floor(occs) == ["A"]

    def test_respects_custom_floor(self):
        occs = [
            {"soc_code": "A", "skills": ["x", "y"]},
            {"soc_code": "B", "skills": ["x", "y", "z", "w"]},
        ]
        assert _below_floor(occs, floor=3) == ["A"]

    def test_returns_empty_list_when_all_meet_floor(self):
        occs = [{"soc_code": "A", "skills": ["x"] * MIN_SKILLS}]
        assert _below_floor(occs) == []


class TestApplyMapping:
    def test_updates_skills_with_validated_list(self):
        occs = [{"soc_code": "15-1252", "title": "Software Developers", "skills": []}]
        mapping = {"15-1252": ["Data Analysis", "Project Management"]}
        updated, rejected, off_tax = _apply_mapping(occs, mapping, TAXONOMY)
        assert updated == 1
        assert occs[0]["skills"] == ["Data Analysis", "Project Management"]
        assert rejected == {}
        assert off_tax == set()

    def test_records_rejected_terms_by_soc_code(self):
        occs = [{"soc_code": "15-1252", "title": "Software Developers", "skills": []}]
        mapping = {"15-1252": ["Data Analysis", "Not A Real Skill"]}
        updated, rejected, off_tax = _apply_mapping(occs, mapping, TAXONOMY)
        assert updated == 1
        assert occs[0]["skills"] == ["Data Analysis"]
        assert rejected == {"15-1252": ["Not A Real Skill"]}
        assert off_tax == {"Not A Real Skill"}

    def test_leaves_unmapped_occupations_untouched(self):
        occs = [
            {"soc_code": "A", "skills": ["Data Analysis"]},
            {"soc_code": "B", "skills": []},
        ]
        mapping = {"A": ["Project Management"]}
        updated, _, _ = _apply_mapping(occs, mapping, TAXONOMY)
        assert updated == 1
        assert occs[0]["skills"] == ["Project Management"]
        assert occs[1]["skills"] == []


class TestFormatRetryLine:
    def test_includes_current_skills_and_rejected_terms(self):
        occ = {
            "soc_code": "15-1252",
            "title": "Software Developers",
            "description": "Designs and builds software.",
            "education_level": "Bachelor's degree",
            "skills": ["Data Analysis"],
        }
        lines = _format_retry_line(occ, ["Invented Skill"])
        joined = "\n".join(lines)
        assert "SOC 15-1252: Software Developers" in joined
        assert "Bachelor's degree" in joined
        assert "Designs and builds software." in joined
        assert "Data Analysis" in joined
        assert "Invented Skill" in joined

    def test_marks_no_current_skills_when_empty(self):
        occ = {
            "soc_code": "15-1252",
            "title": "Software Developers",
            "skills": [],
        }
        joined = "\n".join(_format_retry_line(occ, []))
        assert "(none)" in joined
