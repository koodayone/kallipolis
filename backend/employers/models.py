from pydantic import BaseModel
from typing import Optional


class EmployerMatch(BaseModel):
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    occupations: list[str]
    matching_skills: int
    skills: list[str]


class EmployerDetail(BaseModel):
    name: str
    sector: Optional[str] = None
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
