from pydantic import BaseModel
from typing import Literal, Optional


class CourseAlignment(BaseModel):
    """A single college course that PREPARES_FOR an occupation, via the
    Chancellor's Office TOP-CIP-SOC institutional crosswalk."""
    code: str
    name: str
    department: str
    via_top: Optional[str] = None


class OccupationMatch(BaseModel):
    soc_code: str
    title: str
    description: Optional[str] = None
    annual_wage: Optional[int] = None
    employment: Optional[int] = None
    growth_rate: Optional[float] = None
    annual_openings: Optional[int] = None
    education_level: Optional[str] = None
    aligned_course_count: int = 0
    aligned_department_count: int = 0
    # Mirrors the partnerships view's two-valued alignment tag:
    # "aligned" — college has at least one PREPARES_FOR-aligned course
    # "gap"     — SOC is regionally demanded and CTE-reachable, but the
    #             college has no aligned curriculum. Surfaced honestly
    #             rather than silently dropped from the view.
    alignment_status: Literal["aligned", "gap"] = "aligned"


class RegionOverview(BaseModel):
    region: str
    occupations: list[OccupationMatch]


class LaborMarketOverview(BaseModel):
    college: str
    regions: list[RegionOverview]


class CipMatch(BaseModel):
    """A federal CIP code that bridges a TOP6 to a SOC via the NCES
    CIP-SOC crosswalk. Surfaced under each TOP in the Curriculum
    Alignment view as the federal-side rationale for why the system
    treats this TOP as feeding the SOC — especially useful when the
    institutional crosswalk (PCAH TOP→CIP) is incomplete and the
    federal pathway is the only evidence the system can offer."""
    code: str
    title: str = ""


class TopAlignmentGroup(BaseModel):
    """A TOP6 program area that institutionally feeds the queried
    occupation, with the courses at the queried college that map
    through it. The course code prefix carries the department
    affiliation — no separate department field needed at this grain.

    Surfaces both taught and untaught TOPs: `taught=True` means the
    college has at least one PREPARES_FOR course under this TOP6 for
    this SOC; `taught=False` means the system-wide pathway includes
    this TOP6 but the college doesn't currently teach a course under
    it. Untaught rows are the curriculum-development surface — gaps
    inside the larger gap-or-alignment row.
    """
    top_code: str
    top_title: str = ""
    # Default True for backward compatibility with other consumers
    # (Employers view) that hand a TopAlignmentGroup-shaped dict to
    # the shared TopGroupBlock React component without surfacing the
    # untaught case.
    taught: bool = True
    courses: list[CourseAlignment]
    # Federal CIPs that bridge this TOP6 to the SOC via NCES CIP-SOC.
    # Drives the per-TOP CIP rail in the Occupations view. Empty when
    # the (TOP6, SOC) pair has no NCES bridge — should be rare for
    # surfaced TOPs since the TOPs are derived from the bridge itself.
    cips: list[CipMatch] = []


class OccupationDetail(BaseModel):
    soc_code: str
    title: str
    description: Optional[str] = None
    education_level: Optional[str] = None
    aligned_top_groups: list[TopAlignmentGroup]
    aligned_course_count: int
    aligned_program_area_count: int
    regions: list[dict]


class OccupationQueryRequest(BaseModel):
    query: str
    college: str


class OccupationQueryResponse(BaseModel):
    occupations: list[OccupationMatch]
    message: str
    cypher: Optional[str] = None
