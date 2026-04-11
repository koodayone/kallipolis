"""Unit tests for courses.scrape — CourseLeaf HTML catalog scraper helpers.

The scrape module targets CourseLeaf-based California community college
catalogs. These tests exercise the HTML parser pieces (title parsing,
COR-field labeling, section flushing) that decide what ends up on a
RawCourse. They do not hit the network; each test drives the parser with
hand-written HTML fragments drawn from shapes we have actually seen at
Foothill and Citrus.

Coverage:
  - CourseOutlineParser._parse_h1 splits "CODE: NAME" titles and derives
    a department from the code prefix, including multi-word prefixes.
  - CourseOutlineParser._assign_cor_field routes COR table labels to the
    right RawCourse attribute across label-phrasing variants.
  - CourseOutlineParser collects learning outcomes and objectives from
    <li> elements under the corresponding h2 section.
  - CourseOutlineIndexParser only picks up /course-outlines/<slug>/ links
    and ignores the index page itself and .pdf files.
"""

from __future__ import annotations

from courses.scrape import (
    CourseOutlineIndexParser,
    CourseOutlineParser,
    RawCourse,
)


class TestParseH1:
    def test_splits_code_and_name(self):
        p = CourseOutlineParser()
        p._parse_h1("ENGL 1A: COMPOSITION")
        assert p.course.code == "ENGL 1A"
        assert p.course.name == "COMPOSITION"

    def test_multi_word_prefix_populates_department(self):
        p = CourseOutlineParser()
        p._parse_h1("C S 1A: OBJECT-ORIENTED PROGRAMMING IN JAVA")
        assert p.course.code == "C S 1A"
        assert p.course.name == "OBJECT-ORIENTED PROGRAMMING IN JAVA"
        assert p.course.department == "C S"

    def test_single_word_prefix_populates_department(self):
        p = CourseOutlineParser()
        p._parse_h1("BUS 10: INTRODUCTION TO BUSINESS")
        assert p.course.department == "BUS"

    def test_title_without_colon_falls_back_to_name_only(self):
        p = CourseOutlineParser()
        p._parse_h1("UNTITLED COURSE")
        assert p.course.name == "UNTITLED COURSE"
        assert p.course.code == ""
        assert p.course.department == ""


class TestAssignCorField:
    def test_units_label_populates_units(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Units", "4")
        assert p.course.units == "4"

    def test_hours_label_populates_hours(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Hours", "3 lec, 3 lab")
        assert p.course.hours == "3 lec, 3 lab"

    def test_advisory_routes_to_prerequisites(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Advisory", "ENGL 100")
        assert p.course.prerequisites == "ENGL 100"

    def test_prerequisite_label_populates_prerequisites(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Prerequisite", "MATH 10")
        assert p.course.prerequisites == "MATH 10"

    def test_transfer_label_populates_transfer_status(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Transfer Status", "CSU/UC")
        assert p.course.transfer_status == "CSU/UC"

    def test_ge_label_populates_ge_area(self):
        p = CourseOutlineParser()
        p._assign_cor_field("GE Area", "1A")
        assert p.course.ge_area == "1A"

    def test_grading_method_label_populates_grading(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Grading Method", "Letter Grade")
        assert p.course.grading == "Letter Grade"

    def test_unknown_label_does_not_populate_any_field(self):
        p = CourseOutlineParser()
        p._assign_cor_field("Whatever", "ignored")
        assert p.course == RawCourse()


class TestLearningOutcomesSection:
    def test_collects_li_items_under_slo_section(self):
        html = (
            "<html><body>"
            "<h1 class='page-title'>CS 1A: Intro</h1>"
            "<h2>Student Learning Outcomes</h2>"
            "<ul>"
            "<li>Write a Python program.</li>"
            "<li>Use control flow.</li>"
            "</ul>"
            "<h2>Course Objectives</h2>"
            "<ul>"
            "<li>Objective one.</li>"
            "</ul>"
            "</body></html>"
        )
        p = CourseOutlineParser()
        p.feed(html)
        p._flush_section()  # flush the final section on EOF
        assert p.course.learning_outcomes == ["Write a Python program.", "Use control flow."]
        assert p.course.course_objectives == ["Objective one."]


class TestCourseOutlineIndexParser:
    def test_collects_slugged_course_outline_links(self):
        html = (
            '<a href="/course-outlines/ENGL-1A/">ENGL 1A</a>'
            '<a href="/course-outlines/BIOL-10A/">BIOL 10A</a>'
        )
        p = CourseOutlineIndexParser()
        p.feed(html)
        assert "/course-outlines/ENGL-1A/" in p.links
        assert "/course-outlines/BIOL-10A/" in p.links

    def test_ignores_pdf_links(self):
        html = '<a href="/course-outlines/ENGL-1A.pdf">PDF</a>'
        p = CourseOutlineIndexParser()
        p.feed(html)
        assert p.links == []

    def test_ignores_the_index_page_itself(self):
        html = '<a href="/course-outlines/">index</a>'
        p = CourseOutlineIndexParser()
        p.feed(html)
        assert p.links == []

    def test_ignores_unrelated_links(self):
        html = '<a href="/about/">About</a><a href="/programs/CS/">CS Program</a>'
        p = CourseOutlineIndexParser()
        p.feed(html)
        assert p.links == []
