from pydantic import BaseModel
from typing import Optional


class EmployerMatch(BaseModel):
    name: str
    sector: Optional[str] = None
    swp_sectors: list[str] = []
    priority_sectors_matched: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    occupations: list[str]
    aligned_course_count: int = 0


class EmployerDetail(BaseModel):
    name: str
    sector: Optional[str] = None
    swp_sectors: list[str] = []
    priority_sectors_matched: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    # NAICS-4 industry classification — the institutional pivot that
    # bounds this employer's HIRES_FOR set via the BLS OEWS Industry-
    # Occupation Matrix. `naics_title` is the human-readable industry
    # name from the same OES publication.
    naics4: Optional[str] = None
    naics_title: Optional[str] = None
    regions: list[str]
    occupations: list[dict]


class EmployerQueryRequest(BaseModel):
    query: str
    college: str


class EmployerQueryResponse(BaseModel):
    employers: list[EmployerMatch]
    message: str
    cypher: Optional[str] = None
