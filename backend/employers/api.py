"""Employer endpoints — labor market supply side."""

from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from employers.models import (
    EmployerMatch,
    EmployerDetail,
    EmployerQueryRequest,
    EmployerQueryResponse,
)
from employers.query import run_employer_query

router = APIRouter()


@router.get("/", response_model=list[EmployerMatch])
def get_employers(college: str):
    """Returns employers in the college's region ranked by skill alignment."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
                RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                       emp.website AS website,
                       collect(DISTINCT occ.title) AS occupations,
                       count(DISTINCT sk) AS matching_skills,
                       collect(DISTINCT sk.name) AS skills
                ORDER BY matching_skills DESC
            """, college=college)
            records = result.data()

        return [
            EmployerMatch(
                name=r["name"],
                sector=r["sector"],
                description=r["description"],
                website=r["website"],
                occupations=r["occupations"],
                matching_skills=r["matching_skills"],
                skills=r["skills"],
            )
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=EmployerDetail)
def get_employer_detail(name: str, college: str):
    """Returns full detail for an employer including occupation and skill alignment."""
    driver = get_driver()
    try:
        with driver.session() as session:
            emp_result = session.run(
                "MATCH (e:Employer {name: $name}) RETURN e.name AS name, e.sector AS sector, e.description AS description, e.website AS website",
                name=name,
            ).single()

            if not emp_result:
                raise HTTPException(status_code=404, detail=f"Employer {name} not found")

            occ_result = session.run("""
                MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region),
                      (e)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r),
                      (occ)-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
                RETURN occ.title AS title, occ.soc_code AS soc_code, occ.description AS description, d.annual_wage AS annual_wage,
                       sk.name AS skill,
                       CASE WHEN course IS NOT NULL THEN true ELSE false END AS developed,
                       collect(DISTINCT CASE WHEN course IS NOT NULL THEN {code: course.code, name: course.name} END) AS courses
            """, name=name, college=college).data()

            occ_map: dict[str, dict] = {}
            for r in occ_result:
                key = r["soc_code"]
                if key not in occ_map:
                    occ_map[key] = {
                        "title": r["title"],
                        "soc_code": r["soc_code"],
                        "description": r.get("description"),
                        "annual_wage": r["annual_wage"],
                        "skills": [],
                    }
                courses = [c for c in r["courses"] if c is not None]
                occ_map[key]["skills"].append({
                    "skill": r["skill"],
                    "developed": r["developed"],
                    "courses": courses,
                })

            region_result = session.run(
                "MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region) RETURN COALESCE(r.display_name, r.name) AS region",
                name=name,
            ).data()

        return EmployerDetail(
            name=emp_result["name"],
            sector=emp_result["sector"],
            description=emp_result["description"],
            website=emp_result["website"],
            regions=[r["region"] for r in region_result],
            occupations=list(occ_map.values()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=EmployerQueryResponse)
async def query_employers(req: EmployerQueryRequest):
    try:
        employers, message, cypher = await run_employer_query(req.query, req.college)
        return EmployerQueryResponse(employers=employers, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
