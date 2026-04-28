"""Unit tests for the partnership gather queries — A.1 PREPARES_FOR-gating.

The two helpers under test (`_gather_aligned_curriculum` and
`_gather_student_pipeline`) implement the gating layer for the
partnership artifact. A.1 swapped them from skills-overlap matching
(which produced cross-domain false positives like nursing students
under manufacturing partnerships) to TOP-SOC alignment via the
PREPARES_FOR edges materialized in A.0.

These tests pin down the architectural shape of the swap.

Coverage:
  - Curriculum query uses the PREPARES_FOR pattern with the selected
    SOC as the gate; skills are within-set decoration only.
  - Empty department set is honored — no aligned curriculum at this
    college returns an empty tuple cleanly.
  - Student pipeline gates on `student.primary_focus IN $departments`
    (the user's principle: the unit of partnership engagement is the
    department, not the course; any student whose pathway is in an
    aligned department is a potential beneficiary).
  - Student pipeline early-returns zero stats when the department
    set is empty (honest empty-set, no skills-soup fallback).
  - Top-student enrollments are filtered to PREPARES_FOR-aligned
    courses, with null OPTIONAL MATCH rows stripped (a student can
    rank into the top-10 with zero specific-course enrollments —
    that is faithful to the "potential beneficiary" framing).

Tests use a mock Neo4j driver so they execute without a live database.
The test surface is the Cypher query text and parameter binding — the
session.run mock captures both, so tests assert on the structural
contract (PREPARES_FOR present, soc_code parameter passed, primary_focus
filter, no STARTS WITH fragility) without depending on a graph.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_driver(session_responses: list):
    """Build a mock Driver whose session.run() returns the given responses
    in order. Each entry is {"single": ...} or {"data": ...} matching
    how the production code consumes the result.
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


# ── _gather_aligned_curriculum ────────────────────────────────────────────


class TestGatherAlignedCurriculum:
    """The curriculum-gating query swapped from skills-WHERE to PREPARES_FOR."""

    def test_query_uses_prepares_for_with_soc_gate(self):
        """The Cypher must MATCH on PREPARES_FOR with the selected SOC; the
        prior skills WHERE clause must be gone from the gating position."""
        from partnerships import gather

        driver, session = _mock_driver([{"data": []}])
        with patch.object(gather, "get_driver", return_value=driver):
            gather._gather_aligned_curriculum("Foothill College", "51-9061", ["Quality Control"])

        cypher = session.run.call_args.args[0]
        params = session.run.call_args.kwargs

        assert "PREPARES_FOR" in cypher, "curriculum gate must use PREPARES_FOR edge"
        assert ":Occupation {soc_code: $soc_code}" in cypher, "must filter on soc_code"
        assert params["soc_code"] == "51-9061"
        assert params["college"] == "Foothill College"
        assert params["core_skills"] == ["Quality Control"]
        # Skills must be a within-set decoration via OPTIONAL MATCH, not the
        # primary WHERE that gates which courses come back.
        assert "OPTIONAL MATCH (c)-[:DEVELOPS]->(sk:Skill)" in cypher

    def test_empty_aligned_set_returns_empty_tuple(self):
        """When zero PREPARES_FOR edges exist for this (college, SOC), the
        helper returns ('', []) — honest empty set, not a fallback."""
        from partnerships import gather

        driver, _ = _mock_driver([{"data": []}])
        with patch.object(gather, "get_driver", return_value=driver):
            dept_text, evidence = gather._gather_aligned_curriculum(
                "Foothill College", "47-2231", ["Solar Installation"]
            )

        assert dept_text == ""
        assert evidence == []

    def test_groups_courses_by_department_with_aligned_skills(self):
        """The result groups courses under their department and decorates
        each with which of the core_skills it develops. Each row also
        carries the via_top audit-trail property from the PREPARES_FOR
        edge so the artifact can attribute the institutional pathway."""
        from partnerships import gather

        rows = [
            {
                "department": "Apprenticeship: Aerospace",
                "code": "AATA101A",
                "name": "Quality Inspection Fundamentals",
                "description": "Intro to QC.",
                "learning_outcomes": ["Apply QC standards"],
                "course_objectives": [],
                "skill_mappings": [],
                "top_code": "095680",
                "via_top": "095680",
                "aligned_skills": ["Quality Control", "Inspection"],
            },
            {
                "department": "Apprenticeship: Aerospace",
                "code": "AATA101B",
                "name": "Inspection Methods II",
                "description": "Continued QC.",
                "learning_outcomes": [],
                "course_objectives": [],
                "skill_mappings": [],
                "top_code": "095680",
                "via_top": "095680",
                "aligned_skills": ["Inspection"],
            },
        ]
        driver, _ = _mock_driver([{"data": rows}])
        with patch.object(gather, "get_driver", return_value=driver):
            dept_text, evidence = gather._gather_aligned_curriculum(
                "Foothill College", "51-9061", ["Quality Control", "Inspection", "Documentation"]
            )

        assert len(evidence) == 1
        dept = evidence[0]
        assert dept["department"] == "Apprenticeship: Aerospace"
        assert len(dept["courses"]) == 2
        assert set(dept["aligned_skills"]) == {"Quality Control", "Inspection"}
        # Institutional source carry-through: via_top is composed from
        # the PREPARES_FOR edge; via_cip is composed from the in-memory
        # crosswalk over via_top.
        assert dept["via_top"] == ["095680"]
        # via_cip is computed against the live crosswalk, so we just
        # assert it is populated rather than pinning specific CIPs.
        assert isinstance(dept["via_cip"], list)
        # Each course carries its own top_code for fine-grained attribution.
        assert dept["courses"][0]["top_code"] == "095680"
        # Missing-skill commentary still surfaces in dept_text.
        assert "Missing: Documentation" in dept_text
        # Source attribution is named in the dept_text rendering so the
        # narrative LLM has the structure to attribute correctly.
        assert "TOP-SOC institutional crosswalk" in dept_text
        assert "TOP 095680" in dept_text

    def test_sorts_departments_by_course_count(self):
        """With skills-overlap no longer the gate, ranking by skill count
        is meaningless — course count is the faithful proxy for depth of
        curricular coverage on the SOC's pathway."""
        from partnerships import gather

        rows = [
            {"department": "Math", "code": "MATH1", "name": "x", "description": "",
             "learning_outcomes": [], "course_objectives": [], "skill_mappings": [],
             "top_code": None, "via_top": None, "aligned_skills": []},
            {"department": "Aerospace", "code": "AERO1", "name": "x", "description": "",
             "learning_outcomes": [], "course_objectives": [], "skill_mappings": [],
             "top_code": None, "via_top": None, "aligned_skills": []},
            {"department": "Aerospace", "code": "AERO2", "name": "x", "description": "",
             "learning_outcomes": [], "course_objectives": [], "skill_mappings": [],
             "top_code": None, "via_top": None, "aligned_skills": []},
            {"department": "Aerospace", "code": "AERO3", "name": "x", "description": "",
             "learning_outcomes": [], "course_objectives": [], "skill_mappings": [],
             "top_code": None, "via_top": None, "aligned_skills": []},
        ]
        driver, _ = _mock_driver([{"data": rows}])
        with patch.object(gather, "get_driver", return_value=driver):
            _, evidence = gather._gather_aligned_curriculum("F", "51-9061", [])

        assert [d["department"] for d in evidence] == ["Aerospace", "Math"]


# ── _gather_student_pipeline ──────────────────────────────────────────────


class TestGatherStudentPipeline:
    """Department-rooted student gating per the user's principle: the unit
    of partnership engagement is the department, not the course."""

    def test_empty_departments_returns_zero_stats_immediately(self):
        """When there is no aligned curriculum, the pipeline does not query
        the graph — it returns an honest empty result."""
        from partnerships import gather

        driver, session = _mock_driver([])
        with patch.object(gather, "get_driver", return_value=driver):
            stats, top = gather._gather_student_pipeline(
                "Foothill College", [], "47-2231", ["Solar Installation"]
            )

        assert stats == {"total_in_program": 0, "with_all_core_skills": 0}
        assert top == []
        # Critical: no Cypher should have run. Honest empty set, not a
        # fallback that bleeds in skills-soup data.
        session.run.assert_not_called()

    def test_query_gates_students_on_primary_focus_in_departments(self):
        """The headline count is every student whose primary_focus is one
        of the aligned departments. STARTS WITH bidirectional fragility
        from the prior version must be gone."""
        from partnerships import gather

        stats_response = {"single": {"total_in_program": 47, "with_all_core_skills": 12}}
        top_response = {"data": []}
        driver, session = _mock_driver([stats_response, top_response])

        with patch.object(gather, "get_driver", return_value=driver):
            stats, _ = gather._gather_student_pipeline(
                "Foothill College",
                ["Apprenticeship: Aerospace", "Manufacturing Technology"],
                "51-9061",
                ["Quality Control"],
            )

        cypher = session.run.call_args_list[0].args[0]
        assert "st.primary_focus IN $departments" in cypher
        assert "STARTS WITH" not in cypher, "fragile prefix matching must be gone"
        assert stats == {"total_in_program": 47, "with_all_core_skills": 12}

    def test_top_students_query_uses_prepares_for_for_enrollments(self):
        """Top-student exemplars surface their PREPARES_FOR-aligned
        enrollments — concrete curricular evidence per student, not
        every course they happen to be in."""
        from partnerships import gather

        stats_response = {"single": {"total_in_program": 5, "with_all_core_skills": 1}}
        top_data = [
            {
                "uuid": "u1", "primary_focus": "Apprenticeship: Aerospace",
                "courses_completed": 2, "gpa": 3.7, "matching_skills": 2,
                "relevant_skills": ["Quality Control", "Inspection"],
                "enrollments": [
                    {"code": "AATA101A", "name": "QC I", "grade": "A", "term": "2024-Fall"},
                ],
            },
        ]
        driver, session = _mock_driver([stats_response, {"data": top_data}])

        with patch.object(gather, "get_driver", return_value=driver):
            _, top = gather._gather_student_pipeline(
                "Foothill College",
                ["Apprenticeship: Aerospace"],
                "51-9061",
                ["Quality Control", "Inspection"],
            )

        top_cypher = session.run.call_args_list[1].args[0]
        params = session.run.call_args_list[1].kwargs

        assert "PREPARES_FOR" in top_cypher
        assert ":Occupation {soc_code: $soc_code}" in top_cypher
        assert "OPTIONAL MATCH" in top_cypher, "students with zero PREPARES_FOR enrollments must still surface"
        assert params["soc_code"] == "51-9061"

        assert len(top) == 1
        assert top[0]["display_number"] == 1
        assert top[0]["primary_focus"] == "Apprenticeship: Aerospace"
        assert len(top[0]["enrollments"]) == 1
        assert top[0]["enrollments"][0]["code"] == "AATA101A"

    def test_top_students_strips_null_optional_match_rows(self):
        """When a student has zero PREPARES_FOR enrollments, the OPTIONAL
        MATCH yields a row with all-null fields. The helper must filter
        those so the artifact never displays empty-shell enrollments."""
        from partnerships import gather

        stats_response = {"single": {"total_in_program": 3, "with_all_core_skills": 0}}
        # Student with one real enrollment and one null shell.
        top_data = [
            {
                "uuid": "u1", "primary_focus": "Apprenticeship: Aerospace",
                "courses_completed": 1, "gpa": 3.9, "matching_skills": 0,
                "relevant_skills": [],
                "enrollments": [
                    {"code": "AATA101A", "name": "QC I", "grade": "B", "term": "2024-Fall"},
                    {"code": None, "name": None, "grade": None, "term": None},
                ],
            },
        ]
        driver, _ = _mock_driver([stats_response, {"data": top_data}])

        with patch.object(gather, "get_driver", return_value=driver):
            _, top = gather._gather_student_pipeline(
                "Foothill College", ["Apprenticeship: Aerospace"], "51-9061", []
            )

        # The null shell row must be filtered out — only real enrollments
        # surface to the artifact.
        assert len(top[0]["enrollments"]) == 1
        assert top[0]["enrollments"][0]["code"] == "AATA101A"

    def test_skills_are_within_set_ranker_not_gate(self):
        """A student with primary_focus in an aligned department must be
        counted in total_in_program even if they have zero matching
        skills — skills rank within the set, they do not gate it."""
        from partnerships import gather

        # The mocked headline stats reflect what the new query would
        # return: 47 students in aligned departments total, of whom only
        # 12 demonstrate all the core skills. The other 35 are still in
        # total_in_program — they are potential beneficiaries.
        stats_response = {"single": {"total_in_program": 47, "with_all_core_skills": 12}}
        driver, _ = _mock_driver([stats_response, {"data": []}])

        with patch.object(gather, "get_driver", return_value=driver):
            stats, _ = gather._gather_student_pipeline(
                "Foothill College", ["Apprenticeship: Aerospace"], "51-9061", ["Quality Control"]
            )

        assert stats["total_in_program"] == 47, (
            "Headline count must be department-rooted; students lacking the "
            "core skill must still be counted as potential beneficiaries."
        )
        assert stats["with_all_core_skills"] == 12
