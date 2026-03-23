from pydantic import BaseModel
from typing import Optional


class CurriculumAlignment(BaseModel):
    program_name: str
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


class ProgramSummary(BaseModel):
    program_name: str
    curricula: list[str]


class InstitutionSummary(BaseModel):
    institution_name: str
    region: str
    programs: list[ProgramSummary]


class ReportRequest(BaseModel):
    report_type: str  # "strong_workforce" | "perkins_v"


class IngestRequest(BaseModel):
    document_text: str
    document_type: Optional[str] = None


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
    avg_performance: str  # "Strong" | "Developing" | "Incomplete"


class StudentDetail(BaseModel):
    uuid: str
    primary_focus: str
    courses_completed: int
    avg_performance: str
    enrollments: list[StudentEnrollment]
    skills: list[str]
