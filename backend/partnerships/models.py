from pydantic import BaseModel
from typing import Optional


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
    # Optional SOC code chosen by the coordinator in the occupation picker.
    # When provided, the pipeline skips the LLM occupation-selection step
    # and constructs the selected-occupation dict directly from this SOC.
    # When absent, the legacy auto-selection path runs (preserved for
    # backward compatibility).
    selected_occupation_soc: Optional[str] = None


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


class SupplyEstimate(BaseModel):
    """Annual projected program supply for a TOP6 program code, from COE data."""
    top_code: str
    top_title: str
    award_level: str
    annual_projected_supply: float


class DepartmentEnrollment(BaseModel):
    """Total enrolled students for a department at this college."""
    department: str
    student_count: int


class SwpEvidence(BaseModel):
    """Tabular regional supply-demand evidence appended to the partnership artifact.

    Demand: occupations the employer hires for, with regional annual openings (SOC-coded).
    Supply: program completions per TOP6 code, projected from Centers of Excellence data.
    Gap: total annual demand minus total annual projected supply.

    Tabular only — no narrative. The four narrative sections argue the case;
    this block is the empirical foundation any subsequent funding justification
    requires.
    """
    occupations: list[OccupationEvidence] = []
    supply_estimates: list[SupplyEstimate] = []
    department_enrollments: list[DepartmentEnrollment] = []
    total_demand: int = 0       # annual openings (flow)
    total_supply: float = 0.0   # annual projected supply (flow)
    gap: float = 0.0            # demand - supply
    coe_region: str = ""        # the COE region this supply is scoped to


class NarrativeProposal(BaseModel):
    """A partnership opportunity surfaced for a coordinator's review.

    Four narrative sections present the institutional case; structured
    evidence blocks ground each claim. The narrative does meaning;
    the evidence does completeness.
    """
    employer: str
    sector: Optional[str] = None
    selected_occupation: str
    selected_soc_code: Optional[str] = None
    core_skills: list[str] = []
    regions: list[str] = []

    # Four narrative sections (LLM-generated)
    executive_summary: str
    occupational_demand: str
    curriculum_alignment: str
    student_impact: str

    # Evidence blocks (deterministic, populated from the graph and COE data)
    opportunity_evidence: list[OccupationEvidence]
    curriculum_evidence: list[DepartmentEvidence]
    student_evidence: StudentEvidence
    swp_evidence: SwpEvidence
