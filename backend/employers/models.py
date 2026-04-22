from pydantic import BaseModel
from typing import Optional


class EmployerMatch(BaseModel):
    name: str
    sector: Optional[str] = None
    swp_sectors: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    occupations: list[str]
    matching_skills: int
    skills: list[str]


class EmployerDetail(BaseModel):
    name: str
    sector: Optional[str] = None
    swp_sectors: list[str] = []
    priority_sectors_matched: list[str] = []
    description: Optional[str] = None
    website: Optional[str] = None
    regions: list[str]
    occupations: list[dict]


class EmployerQueryRequest(BaseModel):
    query: str
    college: str


class EmployerQueryResponse(BaseModel):
    employers: list[EmployerMatch]
    message: str
    cypher: Optional[str] = None
