"""Occupation endpoints — labor market demand side."""

from collections import defaultdict
from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from occupations.models import (
    LaborMarketOverview,
    RegionOverview,
    OccupationMatch,
    OccupationDetail,
    SkillDetail,
    OccupationQueryRequest,
    OccupationQueryResponse,
)
from occupations.query import run_occupation_query

router = APIRouter()


@router.get("/overview", response_model=LaborMarketOverview)
def get_labor_market_overview(college: str):
    """Returns regions and top occupations ranked by skill alignment with the college's curriculum."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
                RETURN COALESCE(r.display_name, r.name) AS region,
                       occ.soc_code AS soc_code, occ.title AS title,
                       occ.description AS description, d.annual_wage AS annual_wage,
                       d.employment AS employment,
                       d.growth_rate AS growth_rate,
                       d.annual_openings AS annual_openings,
                       occ.education_level AS education_level,
                       count(DISTINCT sk) AS matching_skills,
                       collect(DISTINCT sk.name) AS skills
                ORDER BY matching_skills DESC
            """, college=college)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail=f"No labor market data for {college}")

        regions: dict[str, list] = defaultdict(list)
        for r in records:
            regions[r["region"]].append(OccupationMatch(
                soc_code=r["soc_code"],
                title=r["title"],
                description=r["description"],
                annual_wage=r["annual_wage"],
                employment=r["employment"],
                growth_rate=r.get("growth_rate"),
                annual_openings=r.get("annual_openings"),
                education_level=r.get("education_level"),
                matching_skills=r["matching_skills"],
                skills=r["skills"],
            ))

        return LaborMarketOverview(
            college=college,
            regions=[
                RegionOverview(region=name, occupations=occs)
                for name, occs in regions.items()
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{soc_code}", response_model=OccupationDetail)
def get_occupation_detail(soc_code: str, college: str):
    """Returns full detail for an occupation including skill alignment with a specific college."""
    driver = get_driver()
    try:
        with driver.session() as session:
            occ_result = session.run("""
                MATCH (occ:Occupation {soc_code: $soc})
                RETURN occ.title AS title, occ.description AS description,
                       occ.education_level AS education_level
            """, soc=soc_code).single()

            if not occ_result:
                raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

            skill_result = session.run("""
                MATCH (occ:Occupation {soc_code: $soc})-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
                RETURN sk.name AS skill,
                       collect(DISTINCT CASE WHEN course IS NOT NULL THEN {code: course.code, name: course.name} END) AS courses
            """, soc=soc_code, college=college).data()

            skills = []
            for r in skill_result:
                courses = [c for c in r["courses"] if c is not None]
                skills.append(SkillDetail(
                    skill=r["skill"],
                    developed=len(courses) > 0,
                    courses=courses,
                ))
            skills.sort(key=lambda s: (not s.developed, s.skill))

            region_result = session.run("""
                MATCH (r:Region)-[d:DEMANDS]->(occ:Occupation {soc_code: $soc})
                RETURN COALESCE(r.display_name, r.name) AS region, d.employment AS employment,
                       d.annual_wage AS annual_wage,
                       d.growth_rate AS growth_rate, d.annual_openings AS annual_openings
                ORDER BY d.employment DESC
            """, soc=soc_code).data()

        return OccupationDetail(
            soc_code=soc_code,
            title=occ_result["title"],
            description=occ_result["description"],
            education_level=occ_result["education_level"],
            skills=skills,
            regions=[{
                "region": r["region"],
                "employment": r["employment"],
                "annual_wage": r.get("annual_wage"),
                "growth_rate": r.get("growth_rate"),
                "annual_openings": r.get("annual_openings"),
            } for r in region_result],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=OccupationQueryResponse)
async def query_occupations(req: OccupationQueryRequest):
    try:
        occupations, message, cypher = await run_occupation_query(req.query, req.college)
        return OccupationQueryResponse(occupations=occupations, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
