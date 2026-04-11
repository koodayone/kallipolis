"""Unit tests for courses.scrape_curricunet — CurricUNET course parser.

CurricUNET (Acadea) is the curriculum management platform used by roughly
73 California community colleges. Each course outline is served as an
HTML "DynamicReport" page with section headers, labeled fields, and SLO
list items. These tests exercise the pure parser logic without hitting
any CurricUNET instance.

Coverage:
  - CurricUNETCourseParser._parse_title handles the "CODE - Name" shape
    with dashes, em-dashes, and numeric-period course numbers.
  - CurricUNETCourseParser._parse_title derives a department acronym from
    the code prefix.
  - _parse_title does not clobber the course fields when the input does
    not match the expected shape.
"""

from __future__ import annotations

from courses.scrape_curricunet import CurricUNETCourseParser


class TestParseTitle:
    def test_standard_dash_separated_title(self):
        p = CurricUNETCourseParser()
        p._parse_title("CDEV 67 - Child, Family, and Community")
        assert p.course.code == "CDEV 67"
        assert p.course.name == "Child, Family, and Community"
        assert p.course.department == "CDEV"

    def test_em_dash_separator(self):
        p = CurricUNETCourseParser()
        p._parse_title("ENGL 1A — Reading and Composition")
        assert p.course.code == "ENGL 1A"
        assert p.course.name == "Reading and Composition"

    def test_en_dash_separator(self):
        p = CurricUNETCourseParser()
        p._parse_title("BIOL 10 – General Biology")
        assert p.course.code == "BIOL 10"
        assert p.course.name == "General Biology"

    def test_letter_suffix_in_course_number(self):
        p = CurricUNETCourseParser()
        p._parse_title("MATH 1A - Calculus I")
        assert p.course.code == "MATH 1A"
        assert p.course.department == "MATH"

    def test_decimal_course_number(self):
        p = CurricUNETCourseParser()
        p._parse_title("ART 10.1 - Drawing Fundamentals")
        assert p.course.code == "ART 10.1"
        assert p.course.name == "Drawing Fundamentals"

    def test_malformed_title_leaves_course_untouched(self):
        p = CurricUNETCourseParser()
        p._parse_title("Not a real course title")
        assert p.course.code == ""
        assert p.course.name == ""
        assert p.course.department == ""
