from pydantic import BaseModel
from typing import Optional


class CollegeDepartment(BaseModel):
    department_name: str
    curricula: list[str]


class CollegeSummary(BaseModel):
    college_name: str
    region: str
    departments: list[CollegeDepartment]


class DepartmentSummary(BaseModel):
    department: str
    course_count: int


class CourseSummary(BaseModel):
    name: str
    code: str
    description: str
    learning_outcomes: list[str]
    course_objectives: list[str]
    skill_mappings: list[str]


class CourseQueryRequest(BaseModel):
    query: str
    college: str


class CourseQueryResponse(BaseModel):
    courses: list[CourseSummary]
    message: str
    cypher: Optional[str] = None
