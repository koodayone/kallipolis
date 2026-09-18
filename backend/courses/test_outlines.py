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
  - an Outline round-trips through JSON, link-check stamps included; an older cache file without them still loads
  - eLumen: a start term maps to its catalog year, and the catalog course link is built from the record's curriculum id
  - CourseLeaf (Coast CCD / Orange Coast): the same parser under the host's heading profile — state COR field names,
    approval date, assignments from three headings, a broken "&nbsp;" rejoined, titles not re-cased
  - CurriQunet (San Diego CCD / Mesa): outcomes and objectives from "Outcome Text" / "Objective Text" pairs, lecture and
    laboratory content from the tail's subdivided blocks, assignments from the body with its field labels dropped
  - CurriQunet catalog page: a subject page's course entity ids, keyed by course code, inactive rows dropped
"""

import json

from courses.outlines import (Outline, elumen_catalog_url, elumen_catalog_year, parse_courseleaf, parse_curricunet_index,
                              parse_curricunet_outline, parse_curriqunet_catalog_courses, parse_curriqunet_outline,
                              parse_elumen_course, pick_active)

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
    o = Outline("C", "elumen", "X 1", "T", "d", ["s"], ["o"], ["c"], ["l"], ["a"], "https://u", "Fall 2026", "2025-01-01", "2026-09-16",
                link_ok=True, link_checked="2026-09-17")
    assert Outline(**json.loads(json.dumps(o.__dict__))) == o
    old = {k: v for k, v in o.__dict__.items() if k not in ("link_ok", "link_checked")}      # a cache file from before the check
    assert Outline(**old).link_ok is None


def test_elumen_catalog_year_and_link():
    assert elumen_catalog_year("Fall 2026") == "2026-2027" and elumen_catalog_year("2026FA") == "2026-2027"
    assert elumen_catalog_year("Spring 2026") == "2025-2026" and elumen_catalog_year("2026SP") == "2025-2026"
    assert elumen_catalog_year("Winter 2027") == "2026-2027" and elumen_catalog_year("") == ""
    d = {"curriculumId": "DMTD084A.", "startTerm": {"name": "Fall 2026"}, "uuid": "u"}
    assert elumen_catalog_url("deanza.elumenapp.com", d) == "https://deanza.elumenapp.com/catalog/2026-2027/course/dmtd084a"
    assert elumen_catalog_url("deanza.elumenapp.com", {"uuid": "u"}) == ""                     # no id or term: no catalog link
    o = parse_elumen_course({**d, "code": "DMT D084A."}, college="De Anza College", host="deanza.elumenapp.com", org_entity_id=8, catalog_link=True)
    assert o.source_url.endswith("/catalog/2026-2027/course/dmtd084a")
    o = parse_elumen_course({**d, "code": "DMT D084A."}, college="De Anza College", host="deanza.elumenapp.com", org_entity_id=8)
    assert o.source_url == "https://deanza.elumenapp.com/public/?orgEntityId=8&uuid=u"          # the default stays the public view


COURSELEAF_COAST = """
<h1>NDT A110: Basic Electroencephalography</h1>
<table><tr><td>Curriculum Committee Approval Date</td><td>11/15/2023</td></tr><tr><td>Top Code</td><td>121200 - Electro-Neurodiagnostic Technology</td></tr></table>
<h2>Course Description</h2><p>Fundamentals of EEG, including application of electrodes.</p>
<h2>Course Level Student Learning Outcome(s)</h2><ol><li>Identify and define observed basic EEG rhythms.</li><li>Prepare a patient for an EEG recording.</li></ol>
<h2>Course Objectives</h2><ol><li>1. Measure and apply the 21 standard EEG electrodes.</li><li>I *Scans Competencies</li><li>II +Scans Foundations</li></ol>
<h2>Lecture Content</h2><p>Introduction What is EEG? Basic Rhythms of EEG</p>
<h2>Lab Content</h2><p>1. Square Wave Calibration nb</p><p>sp; 2. Bio-Calibration</p>
<h2>Method(s) of Instruction</h2><p>Lecture (02)</p>
<h2>Reading Assignments</h2><p>Required textbook reading (2 hours/week)</p>
<h2>Writing Assignments</h2><p>Research reports.</p>
<h2>Out-of-class Assignments</h2><p>Skills homework.</p>
<h2>Demonstration of Critical Thinking</h2><p>Homework assignments.</p>
"""


def test_courseleaf_coast_profile_reads_state_cor_headings():
    o = parse_courseleaf(COURSELEAF_COAST, college="Orange Coast College", code="NDT A110",
                         url="https://catalog.cccd.edu/courses/ndt-a110/", host="catalog.cccd.edu")
    assert o.title == "Basic Electroencephalography" and o.approved == "11/15/2023" and o.effective == ""
    assert o.description == "Fundamentals of EEG, including application of electrodes."
    assert o.outcomes == ["Identify and define observed basic EEG rhythms.", "Prepare a patient for an EEG recording."]
    assert o.objectives == ["1. Measure and apply the 21 standard EEG electrodes."]
    assert o.content == ["Introduction What is EEG? Basic Rhythms of EEG"]
    assert o.lab == ["1. Square Wave Calibration 2. Bio-Calibration"]
    assert o.assignments == ["Required textbook reading (2 hours/week)", "Research reports.", "Skills homework."]


def test_courseleaf_foothill_profile_is_the_default():
    o = parse_courseleaf(COURSELEAF, college="Foothill College", code="ENGR 61A", url="u")
    assert o.title == "Introduction To Semiconductor Technology" and o.assignments == []


CURRIQUNET_SDCCD = """
<div>All Fields</div><div>NDTE 101 - Basic Electroencephalography</div><div>Cover</div>
<div>Course Number</div><div>101</div><div>Subject</div><div>NDTE</div><div>Course Title</div><div>Basic Electroencephalography</div>
<div>Catalog Description</div><div>This course covers the fundamentals of electroencephalography (EEG).</div><div>Short Desc (100 Characters or Less)</div><div>Fundamentals.</div>
<div>Student Learning Outcomes</div><div>Learning Outcomes</div><div>Group Title</div><div>Mesa</div>
<div>Outcome Text</div><div>Students will be able to identify anatomical landmarks.</div>
<div>This SLO maps to the following Institutional Learning Outcomes (ILOs), please check all that apply:</div>
<div>Outcome Text</div><div>Students will be able to identify basic waveforms and artifacts.</div>
<div>Student Learning Objectives</div><div>Upon successful completion of the course the student will be able to:</div>
<div>Objective Text</div><div>Set up the International 10/20 system.</div><div>Objective Text</div><div>Complete an accurate patient history.</div>
<div>Disciplines</div><div>Minimum Qualification</div>
<div>Content</div><div>Course Lecture Content (Use outline format)</div><div>Lecture Content</div><div>Introduction</div><div>EEG defined</div>
<div>Laboratory Content</div><div>Introduction to EEG Equipment</div><div>Course Lab/Activity Content</div>
<div>Assignments</div><div>Reading Assignments</div><div>Optional Text</div><div>Assignments</div><div>Course textbook</div>
<div>Writing Assignments</div><div>Optional Text</div><div>Assignments</div><div>Homework assignment completion</div>
<div>Appropriate Assignments that Demonstrate Critical Thinking</div><div>Optional Text</div><div>Assignments</div><div>Lab practicums on a mannequin head.</div>
<div>Methods of Evaluation</div><div>Evaluation Method</div>
<div>ASSIST Preview</div><div>Prefix NDTE</div><div>Course Number 101</div>
<div>Content The following topics are included in the framework of the course.</div>
<div>Lecture Content</div><div>Introduction</div><div>EEG defined</div>
<div>Laboratory Content</div><div>Introduction to EEG Equipment</div><div>Lab Content</div>
<div>Course Description</div><div>This course covers the fundamentals of electroencephalography (EEG).</div>
<div>Outline Approval Date</div><div>Outline Effective Date</div><div>Prerequisites</div><div>Objectives</div><div>Assignments</div><div>Other Information</div>
"""


def test_curriqunet_sdccd_report_layout():
    o = parse_curriqunet_outline(CURRIQUNET_SDCCD, college="San Diego Mesa College", url="u")
    assert o.code == "NDTE 101" and o.title == "Basic Electroencephalography"
    assert o.description == "This course covers the fundamentals of electroencephalography (EEG)."
    assert o.outcomes == ["Students will be able to identify anatomical landmarks.",
                          "Students will be able to identify basic waveforms and artifacts."]
    assert o.objectives == ["Set up the International 10/20 system.", "Complete an accurate patient history."] and o.notes == ""
    assert o.content == ["Introduction", "EEG defined"] and o.lab == ["Introduction to EEG Equipment"]
    assert o.assignments == ["Course textbook", "Homework assignment completion", "Lab practicums on a mannequin head."]
    assert o.approved == "" and o.effective == ""


def test_curriqunet_catalog_page_yields_course_entity_ids():
    text = ('<div class="container-fluid course-summary-wrapper" data-course-id="12830"><b class="course-subject-code">NDTE </b>'
            '<b class="course-number">101 </b><b class="course-title">Basic Electroencephalography</b>'
            '<span data-catalog-status-base="Active"></span><span class="course-description">Fundamentals of EEG.</span></div>'
            '<div class="container-fluid course-summary-wrapper" data-course-id="99"><b class="course-subject-code">NDTE </b>'
            '<b class="course-number">090 </b><b class="course-title">Old</b><span data-catalog-status-base="Historical"></span></div>')
    page = {"body": [{"presentationtype": "richtext", "text": "<h1>NDTE</h1>"}, {"presentationtype": "curriculum", "text": text}]}
    assert parse_curriqunet_catalog_courses(page) == {
        "NDTE 101": {"entity_id": 12830, "title": "Basic Electroencephalography", "description": "Fundamentals of EEG."}}
