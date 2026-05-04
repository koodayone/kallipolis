from pydantic import BaseModel
from typing import Optional


class PartnershipOpportunity(BaseModel):
    name: str
    sector: Optional[str] = None
    # Multi-sector tagging (Doing-What-Matters / SWP framework). swp_sectors
    # is the employer's full set; priority_sectors_matched is the intersection
    # of that set with the college's region's priority sectors, computed
    # live in Cypher so COE_REGION_PRIORITY_SECTORS edits stay visible
    # without a graph reload. Same pattern as the employers landscape
    # endpoint — both views need this for sector grouping with the
    # regional-priority dot indicator.
    swp_sectors: list[str] = []
    priority_sectors_matched: list[str] = []
    description: Optional[str] = None
    # Employer homepage URL — surfaced in the partnership picker view as the
    # "Employer Home Page" link, matching the employers view's affordance.
    website: Optional[str] = None
    # alignment_score is the count of this college's courses with a
    # PREPARES_FOR edge to any of the employer's hires SOCs. gap_count
    # is the count of hires SOCs the college has zero institutionally-
    # aligned curriculum for.
    alignment_score: int
    gap_count: int
    pipeline_size: Optional[int] = None
    top_occupation: Optional[str] = None
    top_wage: Optional[int] = None


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
    # CIP codes the BLS/NCES CIP-SOC crosswalk maps to this SOC. Surfaces
    # the second link in the empirical chain (SOC ↔ CIP) so the artifact
    # can attribute the institutional pathway to its external source.
    cip_codes: list[str] = []


class CourseEvidence(BaseModel):
    code: str
    name: str
    description: str = ""
    learning_outcomes: list[str] = []
    # The TOP6 code this course is institutionally tagged with in the
    # Master Course File. Surfacing it on each course evidence row makes
    # the empirical chain visible at the finest grain (Course →
    # PREPARES_FOR(via_top) → Occupation).
    top_code: Optional[str] = None


class DepartmentEvidence(BaseModel):
    department: str
    courses: list[CourseEvidence]
    # The set of TOP6 codes this department's PREPARES_FOR-aligned
    # courses route through. Most departments concentrate around a
    # single TOP6 (the apprenticeship pattern at Foothill, e.g.,
    # Apprenticeship: Aerospace = TOP 095680); some span several.
    via_top: list[str] = []
    # The CIP codes that mediate the chain Course → TOP6 → CIP → SOC.
    # Composed by gather.py from `top6_to_cip` over the via_top set.
    via_cip: list[str] = []


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
    enrollments: list[StudentEnrollmentEvidence] = []


class StudentEvidence(BaseModel):
    total_in_program: int
    total_in_aligned_departments: int = 0
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


class InstitutionalSources(BaseModel):
    """Named publications and crosswalks that author the categorical
    claims in the partnership artifact.

    The artifact's authority is borrowed entirely from these external,
    institutionally-authored sources. Surfacing them as a structured
    block lets the atlas rendering attribute claims visibly without
    forcing every prose sentence to carry source codes inline. Per the
    institutional-deference principle: the user (a community college
    WFD officer) should be able to verify any categorical claim against
    one of these sources without trusting Kallipolis itself."""

    coe_region: str = ""
    coe_region_display: str = ""
    coe_demand_publication: str = (
        "California Centers of Excellence — Regional Occupational Demand"
    )
    coe_supply_publication: str = (
        "California Centers of Excellence — Annual Program Supply by TOP6"
    )
    top_cip_crosswalk_source: str = (
        "California Community Colleges Chancellor's Office TOP-CIP Crosswalk"
    )
    cip_soc_crosswalk_source: str = (
        "BLS / NCES CIP-SOC Crosswalk"
    )


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
    # Institutional sources block — externally-authored attribution for
    # every categorical claim in the artifact. Defaults populate the
    # publication names; the gather/assembly stage fills coe_region and
    # its display form.
    sources: InstitutionalSources = InstitutionalSources()


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
    regions: list[str] = []

    # Four narrative sections (deterministic templates over graph data)
    executive_summary: str
    occupational_demand: str
    curriculum_alignment: str
    student_impact: str

    # Evidence blocks (deterministic, populated from the graph and COE data)
    opportunity_evidence: list[OccupationEvidence]
    curriculum_evidence: list[DepartmentEvidence]
    student_evidence: StudentEvidence
    swp_evidence: SwpEvidence
