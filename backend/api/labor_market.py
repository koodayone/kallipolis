"""Labor market API endpoints — Region and Occupation data."""

from collections import defaultdict
from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from models import (
    LaborMarketOverview, RegionOverview, OccupationMatch, OccupationDetail, SkillDetail,
    EmployerMatch, EmployerDetail, EmployerQueryRequest, EmployerQueryResponse,
    OccupationQueryRequest, OccupationQueryResponse,
    PartnershipOpportunity, PartnershipLandscape, PartnershipQueryRequest, PartnershipQueryResponse,
)
from workflows.employer_query import run_employer_query
from workflows.occupation_query import run_occupation_query
from workflows.partnerships_query import run_partnership_query

router = APIRouter()


@router.get("/overview", response_model=LaborMarketOverview)
def get_labor_market_overview(college: str):
    """Returns regions and top occupations ranked by skill alignment with the college's curriculum."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
                RETURN r.name AS region,
                       occ.soc_code AS soc_code, occ.title AS title,
                       occ.description AS description, occ.annual_wage AS annual_wage,
                       d.employment AS employment,
                       count(DISTINCT sk) AS matching_skills,
                       collect(DISTINCT sk.name) AS skills
                ORDER BY matching_skills DESC
            """, college=college)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail=f"No labor market data for {college}")

        # Group by region
        regions: dict[str, list] = defaultdict(list)
        for r in records:
            regions[r["region"]].append(OccupationMatch(
                soc_code=r["soc_code"],
                title=r["title"],
                description=r["description"],
                annual_wage=r["annual_wage"],
                employment=r["employment"],
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


@router.get("/occupation/{soc_code}", response_model=OccupationDetail)
def get_occupation_detail(soc_code: str, college: str):
    """Returns full detail for an occupation including skill alignment with a specific college."""
    driver = get_driver()
    try:
        with driver.session() as session:
            # Get occupation info
            occ_result = session.run("""
                MATCH (occ:Occupation {soc_code: $soc})
                RETURN occ.title AS title, occ.description AS description, occ.annual_wage AS annual_wage
            """, soc=soc_code).single()

            if not occ_result:
                raise HTTPException(status_code=404, detail=f"Occupation {soc_code} not found")

            # Get skills with course alignment
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
            # Sort: developed skills first
            skills.sort(key=lambda s: (not s.developed, s.skill))

            # Get regional demand
            region_result = session.run("""
                MATCH (r:Region)-[d:DEMANDS]->(occ:Occupation {soc_code: $soc})
                RETURN r.name AS region, d.employment AS employment
                ORDER BY d.employment DESC
            """, soc=soc_code).data()

        return OccupationDetail(
            soc_code=soc_code,
            title=occ_result["title"],
            description=occ_result["description"],
            annual_wage=occ_result["annual_wage"],
            skills=skills,
            regions=[{"region": r["region"], "employment": r["employment"]} for r in region_result],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employers", response_model=list[EmployerMatch])
def get_employers(college: str):
    """Returns employers in the college's region ranked by skill alignment."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)<-[:DEVELOPS]-(course:Course {college: $college})
                RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
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
                occupations=r["occupations"],
                matching_skills=r["matching_skills"],
                skills=r["skills"],
            )
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employer/{name}", response_model=EmployerDetail)
def get_employer_detail(name: str, college: str):
    """Returns full detail for an employer including occupation and skill alignment."""
    driver = get_driver()
    try:
        with driver.session() as session:
            # Get employer info
            emp_result = session.run(
                "MATCH (e:Employer {name: $name}) RETURN e.name AS name, e.sector AS sector, e.description AS description",
                name=name,
            ).single()

            if not emp_result:
                raise HTTPException(status_code=404, detail=f"Employer {name} not found")

            # Get occupations with skill alignment
            occ_result = session.run("""
                MATCH (e:Employer {name: $name})-[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
                RETURN occ.title AS title, occ.soc_code AS soc_code, occ.annual_wage AS annual_wage,
                       sk.name AS skill,
                       CASE WHEN course IS NOT NULL THEN true ELSE false END AS developed,
                       collect(DISTINCT CASE WHEN course IS NOT NULL THEN {code: course.code, name: course.name} END) AS courses
            """, name=name, college=college).data()

            # Group by occupation
            occ_map: dict[str, dict] = {}
            for r in occ_result:
                key = r["soc_code"]
                if key not in occ_map:
                    occ_map[key] = {
                        "title": r["title"],
                        "soc_code": r["soc_code"],
                        "annual_wage": r["annual_wage"],
                        "skills": [],
                    }
                courses = [c for c in r["courses"] if c is not None]
                occ_map[key]["skills"].append({
                    "skill": r["skill"],
                    "developed": r["developed"],
                    "courses": courses,
                })

            # Get regions
            region_result = session.run(
                "MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region) RETURN r.name AS region",
                name=name,
            ).data()

        return EmployerDetail(
            name=emp_result["name"],
            sector=emp_result["sector"],
            description=emp_result["description"],
            regions=[r["region"] for r in region_result],
            occupations=list(occ_map.values()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/employers/query", response_model=EmployerQueryResponse)
async def query_employers(req: EmployerQueryRequest):
    try:
        employers, message, cypher = await run_employer_query(req.query, req.college)
        return EmployerQueryResponse(employers=employers, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/occupations/query", response_model=OccupationQueryResponse)
async def query_occupations(req: OccupationQueryRequest):
    try:
        occupations, message, cypher = await run_occupation_query(req.query, req.college)
        return OccupationQueryResponse(occupations=occupations, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Partnership Landscape ────────────────────────────────────────────────────


@router.get("/partnership-landscape", response_model=PartnershipLandscape)
def get_partnership_landscape(college: str):
    """Returns employers ranked by partnership opportunity — skill alignment, gaps, and top occupation."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer)
                      -[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
                OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
                WITH emp, sk, occ,
                     CASE WHEN count(course) > 0 THEN true ELSE false END AS developed
                WITH emp,
                     collect(DISTINCT CASE WHEN developed THEN sk.name END) AS raw_aligned,
                     collect(DISTINCT CASE WHEN NOT developed THEN sk.name END) AS raw_gaps,
                     collect(DISTINCT {title: occ.title, wage: occ.annual_wage}) AS occ_entries
                WITH emp,
                     [x IN raw_aligned WHERE x IS NOT NULL] AS aligned_skills,
                     [x IN raw_gaps WHERE x IS NOT NULL] AS gap_skills,
                     occ_entries[0] AS top_occ
                RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                       size(aligned_skills) AS alignment_score,
                       size(gap_skills) AS gap_count,
                       aligned_skills, gap_skills,
                       top_occ.title AS top_occupation, top_occ.wage AS top_wage
                ORDER BY alignment_score DESC
            """, college=college)
            records = result.data()

        return PartnershipLandscape(
            college=college,
            opportunities=[
                PartnershipOpportunity(
                    name=r["name"],
                    sector=r.get("sector"),
                    description=r.get("description"),
                    alignment_score=r["alignment_score"],
                    gap_count=r["gap_count"],
                    aligned_skills=r["aligned_skills"],
                    gap_skills=r["gap_skills"],
                    top_occupation=r.get("top_occupation"),
                    top_wage=r.get("top_wage"),
                )
                for r in records
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partnership-landscape/pipeline")
def get_employer_pipeline(employer: str, college: str):
    """Returns the student pipeline size for a specific employer — count of students with relevant skills."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (:College {name: $college})-[:IN_MARKET]->(r:Region)<-[:IN_MARKET]-(emp:Employer {name: $employer})
                      -[:HIRES_FOR]->(occ:Occupation)-[:REQUIRES_SKILL]->(sk:Skill)
                      <-[:HAS_SKILL]-(st:Student)
                WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
                RETURN count(DISTINCT st) AS pipeline_size
            """, college=college, employer=employer)
            record = result.single()

        return {"pipeline_size": record["pipeline_size"] if record else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/partnerships/query", response_model=PartnershipQueryResponse)
async def query_partnerships(req: PartnershipQueryRequest):
    try:
        opportunities, message, cypher = await run_partnership_query(req.query, req.college)
        return PartnershipQueryResponse(opportunities=opportunities, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
