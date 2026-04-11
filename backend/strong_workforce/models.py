from pydantic import BaseModel
from typing import Optional

from partnerships.models import (
    OccupationEvidence,
    DepartmentEvidence,
    StudentEvidence,
)


class SwpProjectRequest(BaseModel):
    employer: str
    college: str
    partnership_type: str
    # From NarrativeProposal directly
    selected_occupation: str
    selected_soc_code: Optional[str] = None
    core_skills: list[str] = []
    gap_skill: str = ""
    opportunity: str
    opportunity_evidence: list[OccupationEvidence]
    curriculum_composition: str
    curriculum_evidence: list[DepartmentEvidence]
    student_composition: str
    student_evidence: StudentEvidence
    roadmap: str
    # SWP-specific framing
    goal: str
    metrics: list[str]
    apprenticeship: bool = False
    work_based_learning: bool = False


class LmiOccupation(BaseModel):
    soc_code: str
    title: str
    annual_wage: Optional[int] = None
    employment: Optional[int] = None
    growth_rate: Optional[float] = None
    annual_openings: Optional[int] = None
    education_level: Optional[str] = None
    region: str


class SupplyEstimate(BaseModel):
    top_code: str
    top_title: str
    award_level: str
    annual_projected_supply: float


class DepartmentEnrollment(BaseModel):
    department: str
    student_count: int


class LmiContext(BaseModel):
    occupations: list[LmiOccupation]
    supply_estimates: list[SupplyEstimate]
    department_enrollments: list[DepartmentEnrollment] = []
    total_demand: int            # annual openings (flow)
    total_supply: float          # annual projected supply (flow)
    gap: float                   # demand - supply
    gap_eligible: bool


class SwpSection(BaseModel):
    key: str
    title: str
    content: str
    char_limit: Optional[int] = None


class SwpProject(BaseModel):
    employer: str
    college: str
    partnership_type: str
    sections: list[SwpSection]
    lmi_context: LmiContext
    goal: str
    metrics: list[str]
