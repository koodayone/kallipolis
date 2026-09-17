"""Unit tests for courses.outlines — the course-outline-of-record parsers, one per curriculum vendor.

Parsers are separated from fetchers so they run on fixtures shaped like each system's
output; the network paths are exercised through the cached roster in
partnerships/test_alignment.py.

Coverage:
  - CourseLeaf (Foothill): sections, the effective term, the catalog suffix stripped from the title
  - CurricUNET (Ohlone): wrapped outcome lines rejoined, lecture vs lab content, approval date, no-objectives note
  - CurricUNET index: the Active version of a course is chosen over historical ones
  - eLumen (Mission, De Anza): code normalisation ("DMT D084A." → "DMT 84A"), HTML fields to lists, dates, deep link
  - CurriQunet (Evergreen Valley): content, lab and assignments from the stable trailing block; ILO boilerplate stripped; template-only objectives noted
  - an Outline round-trips through JSON
"""

import json

from courses.outlines import (Outline, parse_courseleaf, parse_curricunet_index, parse_curricunet_outline,
                              parse_curriqunet_outline, parse_elumen_course, pick_active)

COURSELEAF = """
<h1>ENGR 61A: INTRODUCTION TO SEMICONDUCTOR TECHNOLOGY &lt; Foothill College</h1>
<table><tr><td>Effective Term:</td><td>Winter 2024</td></tr><tr><td>Units:</td><td>5</td></tr></table>
<h2>Student Learning Outcomes</h2><ul><li>Upon completion of the course, students will be able to describe stages of the semiconductor manufacturing process.</li></ul>
<h2>Description</h2><p>This course provides an overview of the semiconductor industry.</p>
<h2>Course Objectives</h2><p>The student will be able to:</p><ul><li>Wafer handling</li><li>Demonstrate different wafer handing methods</li></ul>
<h2>Course Content</h2><ul><li>Moving wafers</li><li>Vacuum wands</li></ul>
<h2>Lab Content</h2><p>Not applicable.</p>
<h2>Method(s) of Evaluation</h2><p>Projects</p>
"""


def test_courseleaf_sections_and_effective_term():
    o = parse_courseleaf(COURSELEAF, college="Foothill College", code="ENGR 61A", url="u")
    assert o.title == "Introduction To Semiconductor Technology"
    assert o.effective == "Winter 2024"
    assert o.outcomes == ["Upon completion of the course, students will be able to describe stages of the semiconductor manufacturing process."]
    assert o.objectives == ["Wafer handling", "Demonstrate different wafer handing methods"]
    assert o.content == ["Moving wafers", "Vacuum wands"] and o.lab == []
    assert o.has() == ["outcomes", "objectives", "description", "content"]


CURRICUNET_TEXT = """
                              OHLONE COLLEGE
                          OFFICIAL COURSE OUTLINE
I.     Description of Course:
          1. Department/Course: ETEC - 126                7. Degree/Applicability:
          2. Title: Industrial Internet of                   Credit, Degree Applicable
          4. Units: 3
        11. Catalog Description:
             This course explores smart production line technologies.
II.    Student Learning Outcomes
       Students will be able to:
          1. Identify relevant applications of Internet of Things(IoT) in Manufacturing.
          2. Design a system, component, or process to meet desired needs within realistic
             constraints such as manufacturability
III.   Course Content:
       LECTURE
         A. Industry 4.0
               1. Industry 4.0 architecture
LABORATORY
  A. Fundamentals of Smart Manufacturing
        1. Configuring Virtual Factory
IV.   Course Assignments:
        A. Reading Assignments
               1. Reading of selected course materials.
V.    Methods of Evaluation:
        A. Examinations
                                                                       Approval Date: 12/03/2025
"""


def test_curricunet_outline_sections_wrap_and_dates():
    o = parse_curricunet_outline(CURRICUNET_TEXT, college="Ohlone College", code="ETEC 126", url="u")
    assert o.description == "This course explores smart production line technologies."
    assert o.outcomes[1].startswith("Design a system, component, or process") and "manufacturability" in o.outcomes[1]
    assert "Industry 4.0 architecture" in o.content and "Configuring Virtual Factory" in o.lab
    assert o.assignments and o.approved == "12/03/2025"
    assert o.objectives == [] and "no objectives section" in o.notes


def test_curricunet_index_picks_the_active_version():
    html = ('<tr><td><a href="/Ohlone/reports/course_outline_report.cfm?courses_id=9944">ETEC 126</a> Industrial Internet ** Active **</td></tr>'
            '<tr><td><a href="/Ohlone/reports/course_outline_report.cfm?courses_id=6981">ETEC 126</a> Industrial Internet ** Historical **</td></tr>')
    idx = parse_curricunet_index(html)
    assert [v[0] for v in idx["ETEC 126"]] == [9944, 6981]
    assert pick_active(idx["ETEC 126"]) == 9944


def test_elumen_record_and_code_normalisation():
    d = {"code": "DMT D084A.", "name": "Introduction to CNC Programming", "uuid": "abc",
         "description": "<p>Mill tool path programming.</p>", "startTerm": {"name": "Fall 2026"},
         "committeeApprovalDate": "2025-11-18T00:00:00.000+00:00",
         "csloList": [{"name": "Demonstrate the set up and basic operation of vertical machining centers."}],
         "courseObjectiveList": [{"name": "Describe three axis CNC milling machines. "}],
         "courseOutline": "A. Overview<br/><div>i. Main components</div>", "labOutline": "<ul><li>Dry run part programs</li></ul>",
         "assignments": "1. Lab projects"}
    o = parse_elumen_course(d, college="De Anza College", host="deanza.elumenapp.com", org_entity_id=8)
    assert o.code == "DMT 84A" and o.effective == "Fall 2026" and o.approved == "2025-11-18"
    assert o.description == "Mill tool path programming."
    assert o.objectives == ["Describe three axis CNC milling machines."]
    assert o.content == ["Overview", "Main components"] and o.lab == ["Dry run part programs"] and o.assignments == ["Lab projects"]
    assert o.source_url == "https://deanza.elumenapp.com/public/?orgEntityId=8&uuid=abc"


CURRIQUNET = """
<div>Main Course Discipline MFGT</div><div>Course Number 201</div><div>Course Title Fundamentals of Electronics Short Title 30 Character limit Fund</div>
<div>Catalog Description</div><div>Basic electrical theory.</div><div>Short Schedule Description</div>
<div>Objectives</div><div>Objectives are small steps that lead toward a specific goal.</div><div>Objectives</div>
<div>Student Learning Outcomes</div><div>Upon completion of this course, the student should be able to</div><div>Learning Outcomes</div>
<div>Demonstrate the use of specialized test equipment to obtain measurements from electronic circuits.</div>
<div>This SLO maps to the following Institutional Learning Outcomes (ILOs), please check all that apply:</div>
<div>Inquiry and Reasoning: The student will critically evaluate information.</div>
<div>Methods of Evaluation and Examination</div>
<div>Revision Date</div><div>05/13/2021</div>
<div>Content</div><div>I) Expressing Measurement Data</div><div>Electrical Units</div>
<div>Assignments</div><div>Read assigned chapters in textbook.</div>
<div>Lab Content</div><div>Apply Test Methods to Troubleshoot, Diagnose, and Identify Faults</div>
<div>Course Description</div><div>Basic electrical theory.</div><div>Outline Approval Date</div><div>Outline Effective Date</div><div>Prerequisites</div>
"""


def test_curriqunet_reads_the_stable_tail_block_and_strips_ilo_noise():
    o = parse_curriqunet_outline(CURRIQUNET, college="Evergreen Valley College", url="u")
    assert o.code == "MFGT 201" and o.title == "Fundamentals of Electronics"
    assert o.outcomes == ["Demonstrate the use of specialized test equipment to obtain measurements from electronic circuits."]
    assert o.objectives == [] and "template text" in o.notes
    assert o.content == ["Expressing Measurement Data", "Electrical Units"]
    assert o.lab == ["Apply Test Methods to Troubleshoot, Diagnose, and Identify Faults"]
    assert o.assignments == ["Read assigned chapters in textbook."]
    assert o.approved == "05/13/2021" and o.effective == ""


def test_outline_round_trips_through_json():
    o = Outline("C", "elumen", "X 1", "T", "d", ["s"], ["o"], ["c"], ["l"], ["a"], "https://u", "Fall 2026", "2025-01-01", "2026-09-16")
    assert Outline(**json.loads(json.dumps(o.__dict__))) == o
