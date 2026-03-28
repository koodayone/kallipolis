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
    description: Optional[str] = None
    occupations: list[str]
    matching_skills: int
    skills: list[str]


class EmployerDetail(BaseModel):
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None
    regions: list[str]
    occupations: list[dict]


# ── Student Query models ───────────────────────────────────────────────────


class StudentQueryRequest(BaseModel):
    query: str
    college: str


class StudentQueryResponse(BaseModel):
    students: list[StudentSummary]
    message: str
    cypher: Optional[str] = None


# ── Course Query models ────────────────────────────────────────────────────


class CourseQueryRequest(BaseModel):
    query: str
    college: str


class CourseQueryResponse(BaseModel):
    courses: list[CourseSummary]
    message: str
    cypher: Optional[str] = None


# ── Employer Query models ──────────────────────────────────────────────────


class EmployerQueryRequest(BaseModel):
    query: str
    college: str


class EmployerQueryResponse(BaseModel):
    employers: list[EmployerMatch]
    message: str
    cypher: Optional[str] = None


# ── Occupation Query models ────────────────────────────────────────────────


class OccupationQueryRequest(BaseModel):
    query: str
    college: str


class OccupationQueryResponse(BaseModel):
    occupations: list[OccupationMatch]
    message: str
    cypher: Optional[str] = None


# ── Partnership Landscape models ─────────────────────────────────────────


class PartnershipOpportunity(BaseModel):
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None
    alignment_score: int
    gap_count: int
    pipeline_size: Optional[int] = None
    top_occupation: Optional[str] = None
    top_wage: Optional[int] = None
    aligned_skills: list[str]
    gap_skills: list[str]


class PartnershipLandscape(BaseModel):
    college: str
    opportunities: list[PartnershipOpportunity]


class PartnershipQueryRequest(BaseModel):
    query: str
    college: str


class PartnershipQueryResponse(BaseModel):
    opportunities: list[PartnershipOpportunity]
    message: str
    cypher: Optional[str] = None


class ProposalRequest(BaseModel):
    employer: str
    college: str
    objective: Optional[str] = None


# ── Targeted Proposal models ─────────────────────────────────────────────


class AlignmentDetail(BaseModel):
    department: str
    course_code: str
    course_name: str
    skill: str


class SkillGapDetail(BaseModel):
    skill: str
    required_by: list[str]
    recommended_action: str


class PipelineStats(BaseModel):
    total_students: int
    students_with_3plus_courses: int
    top_skills: list[str]


class EconomicImpact(BaseModel):
    occupations: list[dict]
    aggregate_employment: Optional[int] = None


class TargetedProposal(BaseModel):
    employer: str
    sector: Optional[str] = None
    executive_summary: str
    partnership_type: str
    partnership_type_rationale: str
    curriculum_alignment: list[AlignmentDetail]
    skill_gaps: list[SkillGapDetail]
    student_pipeline: PipelineStats
    economic_impact: EconomicImpact
    next_steps: list[str]
