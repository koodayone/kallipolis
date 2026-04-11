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


class StudentQueryRequest(BaseModel):
    query: str
    college: str


class StudentQueryResponse(BaseModel):
    students: list[StudentSummary]
    message: str
    cypher: Optional[str] = None
