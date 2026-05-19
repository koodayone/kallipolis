"""Pydantic shapes for the occupation-centric Partnerships surface.

The Partnerships node is a sector→occupation navigation surface: the
``SectorIndex`` powers the accordion; clicking an occupation generates
an ``OpportunityReport`` framed around the multi-employer engagement
opportunity the regional alignment data identifies. The supporting
evidence shapes (occupation, course, department, student, supply,
attribution) are composed into both the report and the tabular SWP
evidence block within it.
"""

from pydantic import BaseModel
from typing import Literal, Optional


# ── Evidence primitives (composed into OpportunityReport) ─────────────────


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
    # single TOP6; some span several.
    via_top: list[str] = []
    # The CIP codes that mediate the chain Course → TOP6 → CIP → SOC.
    # Composed from `top6_to_cip` over the via_top set.
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


class CrosswalkTop(BaseModel):
    """A 6-digit TOP code in the Curriculum Alignment pathway view.

    Renders as a pill-badge in the leftmost column of the hero
    visualization. The `taught_at_college` flag drives the visual
    distinction between TOPs the college actively teaches (filled,
    brand-colored) and TOPs in the institutional prep set that the
    college doesn't teach (outlined, dimmed) — the curriculum-
    development surface.

    Keyed at TOP6 (the granularity CCCCO PCAH's TOP→CIP crosswalk
    actually operates at) rather than TOP4 (a display abbreviation).
    The 4-digit family can still be derived in the frontend by
    substring(code, 0, 4) for visual grouping if desired.
    """
    code: str                   # 6-digit TOP code, e.g., "070200"
    name: str                   # 6-digit title, e.g., "Computer Information Systems"
    taught_at_college: bool
    cips: list[str]             # CIP codes this TOP bridges to (filtered to those reaching the SOC)


class CrosswalkCip(BaseModel):
    """A federal CIP code in the Curriculum Alignment pathway view.

    Renders as a pill-badge in the middle column of the hero
    visualization, with a locked institutional color (regardless of
    college brand) signalling "this is the federal taxonomy bridge."
    The `active` flag distinguishes CIPs reachable through at least
    one taught TOP4 (full opacity, CIP→SOC line rendered) from CIPs
    only reachable through missing TOPs (dimmed, no CIP→SOC line).
    """
    code: str                   # CIP code, e.g., "15.0507"
    title: str                  # e.g., "Environmental/Environmental Engineering Technology"
    active: bool                # reachable through ≥ 1 taught TOP4


class CurriculumCrosswalk(BaseModel):
    """The TOP6 × CIP × SOC pathway data for the Curriculum Alignment
    section's hero visualization.

    Composed deterministically from the institutional chain (CCCCO
    TOP-CIP → NCES CIP-SOC) restricted to courses with SAM A/B/C/D
    (occupational per CCCCO MIS Data Element Dictionary). Headline
    metric: `n_taught` of `n_total` TOP6 codes supporting this SOC.

    Keyed at TOP6 — the granularity CCCCO PCAH actually maps at.
    Previously rolled up to TOP4 for display simplicity, which hid
    cases where a college teaches some 6-digit children of a 4-digit
    family but not others; the crosswalk linkage breaks at TOP6, so
    that's the right unit of analysis.
    """
    tops: list[CrosswalkTop]
    cips: list[CrosswalkCip]
    n_taught: int               # TOP6 codes the college teaches
    n_total: int                # TOP6 codes in the global prep set
    coverage_pct: float         # 100 * n_taught / n_total, rounded


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
    """Tabular regional supply-demand evidence appended to the report.

    Demand: regional annual openings for the SOC (single row).
    Supply: program completions per TOP6 code, projected from Centers of
    Excellence data, for the TOPs the institutional crosswalk maps to
    the SOC.
    Gap: total annual demand minus total annual projected supply.

    Tabular only — no narrative. The four+one narrative sections argue
    the case; this block is the empirical foundation any subsequent
    funding justification requires.
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
    # publication names; the assembly stage fills coe_region and its
    # display form.
    sources: InstitutionalSources = InstitutionalSources()


# ── Sector index (Partnerships view navigation) ───────────────────────────


class OpportunityRow(BaseModel):
    """A single occupation row inside a sector accordion.

    Carries enough metadata for the row to be self-describing without
    the user needing to drill in: count metrics signal alignment depth
    at this college (students, courses, employers); demand metrics
    signal regional market context (annual wage, annual openings, 5-yr
    growth rate from the COE projections); `gap` is the per-row
    triage signal — regional annual openings minus the college's TOP-
    program supply.
    """
    soc_code: str
    title: str
    annual_openings: Optional[int] = None
    annual_wage: Optional[int] = None
    growth_rate: Optional[float] = None
    course_count: int = 0
    student_count: int = 0
    employer_count: int = 0
    gap: Optional[int] = None
    # Two-valued alignment status driving the row's visual treatment:
    # - "aligned": college has at least one PREPARES_FOR-aligned course
    #   (course_count > 0). Renders as a normal navigable opportunity.
    # - "gap":     SOC is regionally demanded AND in the PCAH sector
    #   AND CTE-reachable globally, but the college has NO institutionally
    #   aligned curriculum for it (course_count = 0). Renders distinctly
    #   to surface "no current pathway, regional demand exists" — a
    #   consortia-level opportunity for the college to consider closing.
    # Default "aligned" preserves backward-compat for any caller
    # constructing rows without explicitly tagging.
    alignment_status: Literal["aligned", "gap"] = "aligned"


class SectorEntry(BaseModel):
    """A Strong Workforce sector and the CTE-reachable occupations
    within it that the college's region demands.

    Per the institutional-deference principle: the sector→occupation
    mapping comes from the PCAH TOP-Codes-to-Sectors file walked
    through the TOP-CIP-SOC chain. A SOC may appear under multiple
    sectors when its TOPs are claimed by more than one — matching
    institutional reality, not forcing a partition.
    """
    sector: str
    is_priority: bool = False
    occupations: list[OpportunityRow]


class SectorIndex(BaseModel):
    """The Partnerships view's top-level navigation: every PCAH-
    classified Strong Workforce sector with at least one CTE-reachable,
    regionally-demanded occupation, alphabetically ordered."""
    college: str
    sectors: list[SectorEntry]


# ── Per-occupation Partnership Opportunity Report ─────────────────────────


class PartnershipOpportunityEmployer(BaseModel):
    """An employer in the regional market that hires for this
    occupation, surfaced as a candidate partner in the report's
    Partnership Opportunities section.

    Sorted by the employer's NAICS-4 industry-share for this SOC
    (BLS OEWS PCT_TOTAL) — the institutional measure of how
    prominent this role is in the employer's industry.
    """
    name: str
    sector: Optional[str] = None
    swp_sectors: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    naics4: Optional[str] = None
    naics_title: Optional[str] = None
    industry_share: Optional[float] = None
    aligned_course_count: int = 0


class OpportunityReport(BaseModel):
    """A per-(college, occupation) partnership opportunity report.

    Composed deterministically from the institutional graph: regional
    demand (COE), TOP-grouped curriculum coverage, student impact
    (existing pipeline compute), and the candidate set of regional
    employers hiring for this role.

    Five narrative sections frame the data in employer-agnostic prose
    that points to the multi-employer engagement opportunity the data
    identifies.
    """
    college: str
    sector: Optional[str] = None
    # True when the sector is one of the college's COE region's
    # Strong Workforce Program priority sectors (per the regional
    # consortium designation in PCAH). Surfaced in the report header
    # so coordinators can see at a glance whether SWP funding flows
    # to this occupational area.
    is_sector_priority: bool = False
    soc_code: str
    soc_title: str
    description: Optional[str] = None
    regions: list[str] = []

    # Five narrative sections (deterministic templates, employer-agnostic)
    executive_summary: str
    occupational_demand: str
    curriculum_alignment: str
    student_impact: str
    partnership_opportunities_narrative: str

    # Evidence blocks
    opportunity_evidence: list[OccupationEvidence]
    curriculum_evidence: list[DepartmentEvidence]
    # Hero visualization for the Curriculum Alignment section: the
    # TOP4 × CIP × SOC institutional pathway, marked taught/missing at
    # the TOP4 layer and active/inactive at the CIP layer. See
    # CurriculumCrosswalk for the field semantics.
    curriculum_crosswalk: CurriculumCrosswalk
    student_evidence: StudentEvidence
    swp_evidence: SwpEvidence
    partnership_opportunities: list[PartnershipOpportunityEmployer]
