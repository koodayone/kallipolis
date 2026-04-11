from pydantic import BaseModel
from typing import Optional


class OccupationMatch(BaseModel):
    soc_code: str
    title: str
    description: Optional[str] = None
    annual_wage: Optional[int] = None
    employment: Optional[int] = None
    growth_rate: Optional[float] = None
    annual_openings: Optional[int] = None
    education_level: Optional[str] = None
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
    skills: list[SkillDetail]
    regions: list[dict]


class OccupationQueryRequest(BaseModel):
    query: str
    college: str


class OccupationQueryResponse(BaseModel):
    occupations: list[OccupationMatch]
    message: str
    cypher: Optional[str] = None
