"""Unit tests for partnerships pure helpers.

Covers the JSON parser that every LLM-based selection call depends on,
the narrative field parser that wraps it, and the deterministic
department-text builder used to construct LLM prompts.
"""

import pytest

from partnerships.filter import _extract_json
from partnerships.narrative import _build_dept_text, _parse_narrative_fields


class TestExtractJson:
    def test_plain_object(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_object_in_json_code_fence(self):
        raw = '```json\n{"a": 1, "b": 2}\n```'
        assert _extract_json(raw) == {"a": 1, "b": 2}

    def test_object_in_plain_code_fence(self):
        raw = '```\n{"a": 1}\n```'
        assert _extract_json(raw) == {"a": 1}

    def test_object_with_leading_text(self):
        # The LLM sometimes prefixes reasoning before the JSON.
        raw = 'Here is my answer:\n{"selected": "nurse"}'
        assert _extract_json(raw) == {"selected": "nurse"}

    def test_object_with_trailing_text(self):
        raw = '{"selected": "nurse"}\nThat is my choice.'
        assert _extract_json(raw) == {"selected": "nurse"}

    def test_nested_object(self):
        raw = '{"outer": {"inner": [1, 2, 3]}}'
        assert _extract_json(raw) == {"outer": {"inner": [1, 2, 3]}}

    def test_object_with_braces_in_strings(self):
        # Depth tracking must ignore braces inside string literals.
        raw = '{"template": "{{curly}}"}'
        assert _extract_json(raw) == {"template": "{{curly}}"}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            _extract_json("")

    def test_text_without_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            _extract_json("I cannot answer that question.")

    def test_malformed_json_raises(self):
        with pytest.raises(ValueError):
            _extract_json("{bad json without quotes}")


class TestParseNarrativeFields:
    def test_well_formed_response(self):
        raw = """{
            "opportunity": "An opportunity sentence.",
            "justification": {
                "curriculum_composition": "Curriculum claim.",
                "student_composition": "Student claim."
            },
            "roadmap": "Roadmap steps."
        }"""
        result = _parse_narrative_fields(raw)
        assert result["opportunity"] == "An opportunity sentence."
        assert result["justification"]["curriculum_composition"] == "Curriculum claim."
        assert result["justification"]["student_composition"] == "Student claim."
        assert result["roadmap"] == "Roadmap steps."

    def test_missing_opportunity_defaults_to_empty(self):
        raw = '{"justification": {"curriculum_composition": "x", "student_composition": "y"}, "roadmap": "z"}'
        result = _parse_narrative_fields(raw)
        assert result["opportunity"] == ""

    def test_missing_justification_block_defaults_to_empty_strings(self):
        raw = '{"opportunity": "o", "roadmap": "r"}'
        result = _parse_narrative_fields(raw)
        assert result["justification"]["curriculum_composition"] == ""
        assert result["justification"]["student_composition"] == ""

    def test_wrapped_in_markdown_fence(self):
        raw = '```json\n{"opportunity": "o", "justification": {}, "roadmap": "r"}\n```'
        result = _parse_narrative_fields(raw)
        assert result["opportunity"] == "o"
        assert result["roadmap"] == "r"


class TestBuildDeptText:
    def test_empty_evidence(self):
        result = _build_dept_text([], ["python"])
        # Header is always present so callers can diff against it.
        assert "DEPARTMENT-LEVEL CURRICULUM ALIGNMENT:" in result

    def test_single_dept_no_missing_skills(self):
        evidence = [{
            "department": "Computer Science",
            "courses": [{"code": "CS 101"}, {"code": "CS 102"}],
            "aligned_skills": ["python", "algorithms"],
        }]
        result = _build_dept_text(evidence, ["python", "algorithms"])
        assert "Computer Science" in result
        assert "python" in result
        assert "algorithms" in result
        assert "2 courses" in result
        assert "Missing" not in result

    def test_missing_skills_reported(self):
        evidence = [{
            "department": "Computer Science",
            "courses": [{"code": "CS 101"}],
            "aligned_skills": ["python"],
        }]
        result = _build_dept_text(evidence, ["python", "kubernetes"])
        assert "Missing: kubernetes" in result

    def test_multiple_missing_skills_sorted(self):
        evidence = [{
            "department": "CS",
            "courses": [{"code": "CS 101"}],
            "aligned_skills": [],
        }]
        # Sorted alphabetically: docker, kubernetes, python
        result = _build_dept_text(evidence, ["python", "docker", "kubernetes"])
        assert "Missing: docker, kubernetes, python" in result

    def test_multiple_departments_each_listed(self):
        evidence = [
            {
                "department": "CS",
                "courses": [{"code": "CS 101"}],
                "aligned_skills": ["python"],
            },
            {
                "department": "Math",
                "courses": [{"code": "MATH 200"}],
                "aligned_skills": ["linear algebra"],
            },
        ]
        result = _build_dept_text(evidence, ["python", "linear algebra"])
        assert "CS" in result
        assert "Math" in result
