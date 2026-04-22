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
                RETURN emp.name AS name, emp.sector AS sector,
                       COALESCE(emp.swp_sectors, []) AS swp_sectors,
                       emp.description AS description, emp.website AS website,
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
                swp_sectors=r.get("swp_sectors", []) or [],
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
    """Returns full detail for an employer including occupation and skill alignment.

    The priority_sectors_matched field is computed live from
    [s IN emp.swp_sectors WHERE s IN r.priority_sectors] — we do not
    pre-compute it as a scalar property because COE_REGION_PRIORITY_SECTORS
    strings can change between reloads, and a query-time intersection
    stays correct without a graph reload.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            emp_result = session.run(
                "MATCH (e:Employer {name: $name}) "
                "RETURN e.name AS name, e.sector AS sector, "
                "       COALESCE(e.swp_sectors, []) AS swp_sectors, "
                "       e.description AS description, e.website AS website",
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
                "MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region) "
                "RETURN COALESCE(r.display_name, r.name) AS region, "
                "       COALESCE(r.priority_sectors, []) AS priority_sectors",
                name=name,
            ).data()

        # Intersect the employer's SWP sectors with each region's priority
        # list. Preserves ordering from swp_sectors so the "primary sector
        # first" semantic survives the intersection.
        swp_sectors = list(emp_result["swp_sectors"] or [])
        priority_union: set[str] = set()
        for r in region_result:
            for s in r.get("priority_sectors") or []:
                priority_union.add(s)
        priority_sectors_matched = [s for s in swp_sectors if s in priority_union]

        return EmployerDetail(
            name=emp_result["name"],
            sector=emp_result["sector"],
            swp_sectors=swp_sectors,
            priority_sectors_matched=priority_sectors_matched,
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
