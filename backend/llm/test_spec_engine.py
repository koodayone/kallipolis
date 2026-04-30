"""Unit tests for the spec engine's render_cypher and interpret_spec layers.

These tests don't hit Gemini or Neo4j — they exercise the deterministic
spec → Cypher and spec → NL templating per feature. The Flash extractor
is the LLM-dependent surface and is exercised by integration tests
(separate file, run on demand).

Coverage:
  - Each feature's render_cypher produces well-formed Cypher containing
    the expected base traversal, parameter references, ORDER BY, and
    LIMIT clauses for representative spec inputs.
  - Each feature's render_cypher returns parameter dicts whose keys
    match the parameter references in the rendered Cypher.
  - Each feature's interpret_spec returns a non-empty sentence that
    mentions the spec's key filters and sort.
  - Spec engine dispatch (`run_spec` not exercised; that's an
    integration concern). The `is_enabled_for` flag respects defaults
    and env-var overrides.
"""
from __future__ import annotations

import os
import re

import pytest

from llm.specs import courses, employers, occupations, students
from llm.specs.base import NumericFilter
from llm.spec_engine import is_enabled_for


# ── Cross-feature helpers ────────────────────────────────────────────


def _params_in_cypher(cypher: str) -> set[str]:
    """Return the set of $-prefixed parameter names referenced in cypher."""
    return set(re.findall(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", cypher))


def _assert_params_consistent(cypher: str, params: dict) -> None:
    """Every $param in cypher must be in `params` (plus the implicit $college)."""
    referenced = _params_in_cypher(cypher)
    referenced.discard("college")  # supplied by spec_engine.run_spec, not render_cypher
    extra = referenced - set(params)
    assert not extra, f"Cypher references undefined params: {extra}"


# ── Occupations ─────────────────────────────────────────────────────


class TestOccupationsRender:
    def test_default_spec_produces_valid_traversal(self):
        spec = occupations.OccupationSpec()
        cypher, params = occupations.render_cypher(spec)
        assert "MATCH (col:College {name: $college})" in cypher
        assert "DEMANDS" in cypher and "REQUIRES_SKILL" in cypher and "DEVELOPS" in cypher
        assert "ORDER BY matching_skills DESC" in cypher
        assert params == {}
        _assert_params_consistent(cypher, params)

    def test_title_filter_with_multi_substring_renders_or(self):
        spec = occupations.OccupationSpec(title_contains=["soft", "engineer"])
        cypher, params = occupations.render_cypher(spec)
        assert "title_q_0" in params and "title_q_1" in params
        assert " OR " in cypher
        assert params["title_q_0"] == "soft"
        _assert_params_consistent(cypher, params)

    def test_sort_field_remaps(self):
        spec = occupations.OccupationSpec(order_by="annual_wage", order_dir="desc")
        cypher, _ = occupations.render_cypher(spec)
        assert "ORDER BY d.annual_wage DESC" in cypher

    def test_limit_appended(self):
        spec = occupations.OccupationSpec(limit=5)
        cypher, _ = occupations.render_cypher(spec)
        assert cypher.rstrip().endswith("LIMIT 5")

    def test_education_level_filter(self):
        spec = occupations.OccupationSpec(education_level="Bachelor's degree")
        cypher, params = occupations.render_cypher(spec)
        assert "occ.education_level = $education_level" in cypher
        assert params["education_level"] == "Bachelor's degree"


class TestOccupationsInterpret:
    def test_default_spec_returns_skill_alignment_phrasing(self):
        text = occupations.interpret_spec(occupations.OccupationSpec())
        assert "skill alignment" in text.lower()

    def test_title_filter_surfaces_in_interpretation(self):
        spec = occupations.OccupationSpec(title_contains=["soft"])
        text = occupations.interpret_spec(spec)
        assert "'soft'" in text

    def test_wage_sort_phrasing(self):
        spec = occupations.OccupationSpec(order_by="annual_wage")
        text = occupations.interpret_spec(spec)
        assert "wage" in text.lower()


# ── Employers ────────────────────────────────────────────────────────


class TestEmployersRender:
    def test_default_spec_produces_full_traversal(self):
        spec = employers.EmployerSpec()
        cypher, params = employers.render_cypher(spec)
        assert "IN_MARKET" in cypher and "HIRES_FOR" in cypher
        assert "REQUIRES_SKILL" in cypher and "DEVELOPS" in cypher
        assert "ORDER BY matching_skills DESC" in cypher
        assert params == {}

    def test_swp_priority_only_renders_intersection_check(self):
        spec = employers.EmployerSpec(swp_priority_only=True)
        cypher, _ = employers.render_cypher(spec)
        assert "ANY(s IN emp.swp_sectors WHERE s IN r.priority_sectors)" in cypher

    def test_sector_with_multi_substring_or(self):
        spec = employers.EmployerSpec(sector_contains=["health", "medical"])
        cypher, params = employers.render_cypher(spec)
        assert " OR " in cypher
        assert params["sector_q_0"] == "health"
        assert params["sector_q_1"] == "medical"
        _assert_params_consistent(cypher, params)


class TestEmployersInterpret:
    def test_default_spec_phrasing(self):
        text = employers.interpret_spec(employers.EmployerSpec())
        assert "skill alignment" in text.lower()

    def test_swp_phrasing(self):
        text = employers.interpret_spec(employers.EmployerSpec(swp_priority_only=True))
        assert "Strong Workforce" in text or "priority" in text.lower()


# ── Courses ──────────────────────────────────────────────────────────


class TestCoursesRender:
    def test_default_spec_uses_plain_match(self):
        spec = courses.CourseSpec()
        cypher, params = courses.render_cypher(spec)
        assert "MATCH (c:Course {college: $college})" in cypher
        assert "DEVELOPS" not in cypher  # no skill filter -> no join
        assert "ORDER BY c.code" in cypher
        assert params == {}

    def test_skill_filter_triggers_develops_join(self):
        spec = courses.CourseSpec(skill_contains=["weld"])
        cypher, _ = courses.render_cypher(spec)
        assert "(c:Course {college: $college})-[:DEVELOPS]->(sk:Skill)" in cypher

    def test_topic_contains_searches_three_properties(self):
        spec = courses.CourseSpec(topic_contains=["weld"])
        cypher, params = courses.render_cypher(spec)
        # Topic search OR's across skill, department, and course name
        assert "sk.name" in cypher and "c.department" in cypher and "c.name" in cypher
        assert params["topic_q_0"] == "weld"

    def test_units_numeric_filter(self):
        spec = courses.CourseSpec(units=NumericFilter(op=">=", value=4))
        cypher, params = courses.render_cypher(spec)
        assert "c.units >= $units_v" in cypher
        assert params["units_v"] == 4

    def test_is_cte_flag(self):
        spec = courses.CourseSpec(is_cte=True)
        cypher, _ = courses.render_cypher(spec)
        assert "c.is_cte = true" in cypher

    def test_transfer_status_in_clause(self):
        spec = courses.CourseSpec(transfer_status_in=["CSU/UC", "UC Only"])
        cypher, params = courses.render_cypher(spec)
        assert "c.transfer_status IN $transfer_statuses" in cypher
        assert params["transfer_statuses"] == ["CSU/UC", "UC Only"]


class TestCoursesInterpret:
    def test_cte_phrasing(self):
        text = courses.interpret_spec(courses.CourseSpec(is_cte=True))
        assert "career and technical education" in text.lower() or "cte" in text.lower()

    def test_units_phrasing(self):
        text = courses.interpret_spec(courses.CourseSpec(units=NumericFilter(op=">=", value=4)))
        assert "4" in text and ("at least" in text.lower() or ">" in text)


# ── Students ─────────────────────────────────────────────────────────


class TestStudentsRender:
    def test_default_spec_uses_plain_anchor(self):
        spec = students.StudentSpec()
        cypher, _ = students.render_cypher(spec)
        assert "MATCH (s:Student)-[:ENROLLED_IN]->(:Course {college: $college})" in cypher
        assert "HAS_SKILL" not in cypher

    def test_primary_focus_single_substring(self):
        spec = students.StudentSpec(primary_focus_contains=["construction technology"])
        cypher, params = students.render_cypher(spec)
        assert params["pf_q_0"] == "construction technology"
        # Single substring should NOT be wrapped in parens
        assert " OR " not in cypher

    def test_primary_focus_multi_substring_or(self):
        spec = students.StudentSpec(primary_focus_contains=["health", "medical"])
        cypher, params = students.render_cypher(spec)
        assert " OR " in cypher
        assert params["pf_q_0"] == "health"

    def test_skill_filter_any_uses_or(self):
        spec = students.StudentSpec(skill_contains=["program", "design"])
        cypher, _ = students.render_cypher(spec)
        # "any" mode -> single MATCH with OR
        assert "MATCH (s:Student)-[:HAS_SKILL]->(sk:Skill)" in cypher
        assert " OR " in cypher

    def test_skill_filter_all_uses_separate_matches(self):
        spec = students.StudentSpec(skill_contains=["program", "design"], skill_filter_mode="all")
        cypher, _ = students.render_cypher(spec)
        assert cypher.count("MATCH (s)-[:HAS_SKILL]->") == 2

    def test_course_anchored_traversal_when_course_filter_set(self):
        spec = students.StudentSpec(course_code_contains="MATH 1A")
        cypher, params = students.render_cypher(spec)
        assert "MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course {college: $college})" in cypher
        # OR fallback: code substring also matched against name
        assert "c.code CONTAINS $code_q OR" in cypher
        assert params["code_q"] == "MATH 1A"

    def test_gpa_numeric_filter(self):
        spec = students.StudentSpec(gpa=NumericFilter(op=">", value=3.5))
        cypher, params = students.render_cypher(spec)
        assert "s.gpa > $gpa_v" in cypher
        assert params["gpa_v"] == 3.5


class TestStudentsInterpret:
    def test_primary_focus_surfaces_in_interpretation(self):
        spec = students.StudentSpec(primary_focus_contains=["engineer"])
        text = students.interpret_spec(spec)
        assert "engineer" in text.lower()

    def test_gpa_filter_surfaces(self):
        spec = students.StudentSpec(gpa=NumericFilter(op=">=", value=3.5))
        text = students.interpret_spec(spec)
        assert "3.5" in text


# ── Feature flag dispatch ─────────────────────────────────────────────


class TestFeatureFlag:
    def test_occupation_default_on(self, monkeypatch):
        monkeypatch.delenv("SPEC_ENGINE_OCCUPATION", raising=False)
        assert is_enabled_for("occupation") is True

    def test_employer_default_on(self, monkeypatch):
        monkeypatch.delenv("SPEC_ENGINE_EMPLOYER", raising=False)
        assert is_enabled_for("employer") is True

    def test_course_default_off(self, monkeypatch):
        monkeypatch.delenv("SPEC_ENGINE_COURSE", raising=False)
        assert is_enabled_for("course") is False

    def test_student_default_off(self, monkeypatch):
        monkeypatch.delenv("SPEC_ENGINE_STUDENT", raising=False)
        assert is_enabled_for("student") is False

    def test_env_override_disables_default_on(self, monkeypatch):
        monkeypatch.setenv("SPEC_ENGINE_OCCUPATION", "0")
        assert is_enabled_for("occupation") is False

    def test_env_override_enables_default_off(self, monkeypatch):
        monkeypatch.setenv("SPEC_ENGINE_COURSE", "1")
        assert is_enabled_for("course") is True
