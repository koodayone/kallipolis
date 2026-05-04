"""Occupation endpoints — labor market demand side."""

from collections import defaultdict
from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from ontology.crosswalks import load_top_titles
from occupations.models import (
    LaborMarketOverview,
    RegionOverview,
    OccupationMatch,
    OccupationDetail,
    CourseAlignment,
    TopAlignmentGroup,
    OccupationQueryRequest,
    OccupationQueryResponse,
)
from occupations.query import run_occupation_query

router = APIRouter()


@router.get("/overview", response_model=LaborMarketOverview)
def get_labor_market_overview(college: str):
    """Returns regions and occupations ranked by curriculum alignment via
    the institutional TOP-SOC crosswalk (PREPARES_FOR edges)."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                      <-[:PREPARES_FOR]-(course:Course {college: $college})<-[:CONTAINS]-(dept:Department)
                RETURN COALESCE(r.display_name, r.name) AS region,
                       occ.soc_code AS soc_code, occ.title AS title,
                       occ.description AS description, d.annual_wage AS annual_wage,
                       d.employment AS employment,
                       d.growth_rate AS growth_rate,
                       d.annual_openings AS annual_openings,
                       occ.education_level AS education_level,
                       count(DISTINCT course) AS aligned_course_count,
                       count(DISTINCT dept) AS aligned_department_count
                ORDER BY aligned_course_count DESC
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
                aligned_course_count=r["aligned_course_count"],
                aligned_department_count=r["aligned_department_count"],
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
    """Returns full detail for an occupation including the courses and
    departments at this college whose TOP code institutionally aligns
    with the SOC via the Chancellor's Office TOP-CIP-SOC crosswalk."""
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

            course_result = session.run("""
                MATCH (occ:Occupation {soc_code: $soc})<-[r:PREPARES_FOR]-(c:Course {college: $college})
                RETURN c.code AS code, c.name AS name, c.department AS department,
                       r.via_top AS via_top
                ORDER BY c.department, c.code
            """, soc=soc_code, college=college).data()

            aligned_courses = [
                CourseAlignment(
                    code=r["code"],
                    name=r["name"],
                    department=r["department"] or "Unknown",
                    via_top=r["via_top"],
                )
                for r in course_result
            ]

            region_result = session.run("""
                MATCH (r:Region)-[d:DEMANDS]->(occ:Occupation {soc_code: $soc})
                RETURN COALESCE(r.display_name, r.name) AS region, d.employment AS employment,
                       d.annual_wage AS annual_wage,
                       d.growth_rate AS growth_rate, d.annual_openings AS annual_openings
                ORDER BY d.employment DESC
            """, soc=soc_code).data()

        # Group aligned courses by their TOP6 — the institutional pivot
        # that mediates each course→occupation pathway.
        top_titles = load_top_titles()
        by_top: dict[str, list[CourseAlignment]] = defaultdict(list)
        for c in aligned_courses:
            by_top[c.via_top or ""].append(c)

        aligned_top_groups = [
            TopAlignmentGroup(
                top_code=tc,
                top_title=top_titles.get(tc, ""),
                courses=sorted(courses, key=lambda c: c.code),
            )
            for tc, courses in by_top.items()
        ]
        # Strongest program-area concentration first; alphabetical tie-break.
        aligned_top_groups.sort(key=lambda g: (-len(g.courses), g.top_code))

        return OccupationDetail(
            soc_code=soc_code,
            title=occ_result["title"],
            description=occ_result["description"],
            education_level=occ_result["education_level"],
            aligned_top_groups=aligned_top_groups,
            aligned_course_count=len(aligned_courses),
            aligned_program_area_count=len(aligned_top_groups),
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
