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
    engagement_type: str = ""


class OccupationEvidence(BaseModel):
    title: str
    soc_code: Optional[str] = None
    annual_wage: Optional[int] = None
    employment: Optional[int] = None
    annual_openings: Optional[int] = None
    growth_rate: Optional[float] = None


class CourseEvidence(BaseModel):
    code: str
    name: str
    description: str = ""
    learning_outcomes: list[str] = []
    skills: list[str] = []


class DepartmentEvidence(BaseModel):
    department: str
    courses: list[CourseEvidence]
    aligned_skills: list[str]


class StudentEnrollmentEvidence(BaseModel):
    code: str
    name: str
    grade: str
    term: str


class StudentSummaryEvidence(BaseModel):
    uuid: str
    display_number: int
    primary_focus: str
    courses_completed: int
    gpa: float
    matching_skills: int
    enrollments: list[StudentEnrollmentEvidence] = []
    relevant_skills: list[str] = []


class StudentEvidence(BaseModel):
    total_in_program: int
    with_all_core_skills: int
    top_students: list[StudentSummaryEvidence]


class ProposalJustification(BaseModel):
    curriculum_composition: str
    curriculum_evidence: list[DepartmentEvidence]
    student_composition: str
    student_evidence: StudentEvidence


class AgendaTopic(BaseModel):
    topic: str
    rationale: str


class NarrativeProposal(BaseModel):
    employer: str
    sector: Optional[str] = None
    partnership_type: str
    selected_occupation: str
    selected_soc_code: Optional[str] = None
    core_skills: list[str] = []
    gap_skill: str = ""
    regions: list[str] = []
    opportunity: str
    opportunity_evidence: list[OccupationEvidence]
    justification: ProposalJustification
    roadmap: str
    # Advisory board specific
    selected_occupations: list[str] = []
    advisory_thesis: str = ""
    agenda_topics: list[AgendaTopic] = []
