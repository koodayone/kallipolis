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


class StudentDetail(BaseModel):
    uuid: str
    primary_focus: str
    courses_completed: int
    gpa: float
    enrollments: list[StudentEnrollment]
    skills: list[str]


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
