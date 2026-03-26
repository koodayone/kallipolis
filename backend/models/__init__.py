from pydantic import BaseModel
from typing import Optional


class CurriculumAlignment(BaseModel):
    department_name: str
    curriculum_name: str
    relevance_note: str


class PartnershipProposal(BaseModel):
    employer_or_sector: str
    curriculum_alignment: list[CurriculumAlignment]
    student_population_relevance: str
    partnership_type: str
    rationale: str


class ProposalList(BaseModel):
    proposals: list[PartnershipProposal]


class CollegeDepartment(BaseModel):
    department_name: str
    curricula: list[str]


class CollegeSummary(BaseModel):
    college_name: str
    region: str
    departments: list[CollegeDepartment]


class ReportRequest(BaseModel):
    report_type: str  # "strong_workforce" | "perkins_v"


class IngestRequest(BaseModel):
    document_text: str
    document_type: Optional[str] = None


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


class StudentEnrollment(BaseModel):
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


# ── Labor Market models ──────────────────────────────────────────────────────


class OccupationMatch(BaseModel):
    soc_code: str
    title: str
    description: Optional[str] = None
    annual_wage: Optional[int] = None
    employment: Optional[int] = None
    matching_skills: int
    skills: list[str]


class RegionOverview(BaseModel):
    region: str
    occupations: list[OccupationMatch]


class LaborMarketOverview(BaseModel):
    college: str
    regions: list[RegionOverview]


class SkillDetail(BaseModel):
    skill: str
    developed: bool
    courses: list[dict]


class OccupationDetail(BaseModel):
    soc_code: str
    title: str
    description: Optional[str] = None
    annual_wage: Optional[int] = None
    skills: list[SkillDetail]
    regions: list[dict]


class EmployerMatch(BaseModel):
    name: str
    sector: Optional[str] = None
    occupations: list[str]
    matching_skills: int
    skills: list[str]


class EmployerDetail(BaseModel):
    name: str
    sector: Optional[str] = None
    regions: list[str]
    occupations: list[dict]
