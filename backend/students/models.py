from pydantic import BaseModel
from typing import Optional


class StudentEnrollment(BaseModel):
    course_code: str = ""
    course_name: str
    department: str
    grade: str
    term: str
    status: str


class StudentSummary(BaseModel):
    uuid: str
    primary_focus: str
    courses_completed: int
    gpa: float


class CourseRef(BaseModel):
    """A completed course that contributes to a student's competency-profile
    alignment with a specific SOC, grouped under the TOP it travels through."""
    code: str
    name: str


class TopGroup(BaseModel):
    """A TOP6 program area grouping for a student's matched courses against
    a specific SOC. Each TOP code is the institutional pivot that mediates
    Course→Occupation pathway through the Chancellor's Office TOP-CIP and
    BLS/NCES CIP-SOC crosswalks. `top_title` is the program-area name from
    the Chancellor's Office TOP-CIP file; falls back to empty string when
    the code has no title entry, in which case the UI renders the bare code.
    """
    top_code: str
    top_title: str = ""
    courses: list[CourseRef]


class OccupationAlignment(BaseModel):
    """A SOC the student is aligned with by completed coursework, via the
    institutional TOP-SOC crosswalk. Matched courses are pre-grouped by the
    TOP6 each course is institutionally tagged with — making the program-area
    structure of the alignment visible at the rendering layer instead of
    leaving it implicit on each course's `top_code` property."""
    soc_code: str
    title: str
    matched_course_count: int
    matched_top_groups: list[TopGroup]


class StudentDetail(BaseModel):
    uuid: str
    primary_focus: str
    courses_completed: int
    gpa: float
    enrollments: list[StudentEnrollment]
    occupation_alignment: list[OccupationAlignment]


class StudentSummaryPage(BaseModel):
    """Paginated response for the bulk students-by-college endpoint.

    The top-level GET /students/ used to return a bare list of every
    student at a college, which produced ~3 MB JSON payloads at 14K
    students for the larger colleges and dominated first-paint TTFB.
    The endpoint now returns a page slice; callers paginate explicitly.
    `total_count` lets the UI surface "showing 500 of 14,135" and
    `has_more` signals when another page is available.
    """
    students: list[StudentSummary]
    total_count: int
    has_more: bool


class StudentQueryRequest(BaseModel):
    query: str
    college: str


class StudentQueryResponse(BaseModel):
    students: list[StudentSummary]
    message: str
    cypher: Optional[str] = None
