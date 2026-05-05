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
    """Returns employers in the college's region ranked by curriculum
    alignment via the institutional TOP-SOC crosswalk.

    Reads the precomputed `PARTNERSHIP_ALIGNMENT` edge (materialized at
    pipeline reload by `partnerships/compute.py`). Each edge carries
    the count of roles the employer hires for in this college's region
    and the count of courses at this college that PREPARES_FOR any of
    those roles. The full per-occupation detail (titles, wages, course
    alignment groups) is on the detail endpoint, fetched only when a
    user expands an employer row.

    The request-time computation this replaces was a College → Region →
    Employer → Occupation × PREPARES_FOR × CONTAINS traversal that
    materialized a multi-million-row cartesian per request — measured
    at 26s for Foothill (Bay region, 311 employers) and timeouts
    (>300s) for LA/OC/SD-region colleges (350+ employers) on the
    e2-medium prod VM.

    `priority_sectors_matched` stays a request-time intersection
    rather than a stored property: COE_REGION_PRIORITY_SECTORS strings
    can be edited without a graph reload, and a query-time computation
    keeps the surface correct without re-materializing the edges.

    No ORDER BY: EmployersView re-sorts the response alphabetically
    by name on the client (see EmployersView.tsx). A backend sort
    would be wasted compute.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region),
                      (col)-[pa:PARTNERSHIP_ALIGNMENT]->(emp:Employer)
                RETURN emp.name AS name, emp.sector AS sector,
                       COALESCE(emp.swp_sectors, []) AS swp_sectors,
                       [s IN COALESCE(emp.swp_sectors, []) WHERE s IN COALESCE(r.priority_sectors, [])] AS priority_sectors_matched,
                       emp.description AS description, emp.website AS website,
                       pa.roles_count AS roles_count,
                       pa.aligned_course_count AS aligned_course_count
            """, college=college)
            records = result.data()

        return [
            EmployerMatch(
                name=r["name"],
                sector=r["sector"],
                swp_sectors=r.get("swp_sectors", []) or [],
                priority_sectors_matched=r.get("priority_sectors_matched", []) or [],
                description=r["description"],
                website=r["website"],
                roles_count=r["roles_count"],
                aligned_course_count=r["aligned_course_count"],
            )
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=EmployerDetail)
def get_employer_detail(name: str, college: str):
    """Returns full detail for an employer including occupation alignment.

    For each occupation the employer hires for, surfaces the courses and
    departments at this college that PREPARES_FOR that occupation via
    the Chancellor's Office TOP-CIP-SOC institutional crosswalk.

    The priority_sectors_matched field is computed live from
    [s IN emp.swp_sectors WHERE s IN r.priority_sectors] — we do not
    pre-compute it as a scalar property because COE_REGION_PRIORITY_SECTORS
    strings can change between reloads, and a query-time intersection
    stays correct without a graph reload.
    """
    from collections import defaultdict
    from ontology.crosswalks import load_naics4_titles, load_top_titles
    from ontology.oes import oes_socs_for_naics4
    from occupations.models import CourseAlignment, TopAlignmentGroup

    naics_titles = load_naics4_titles()
    top_titles = load_top_titles()
    driver = get_driver()
    try:
        with driver.session() as session:
            emp_result = session.run(
                "MATCH (e:Employer {name: $name}) "
                "RETURN e.name AS name, e.sector AS sector, "
                "       COALESCE(e.swp_sectors, []) AS swp_sectors, "
                "       e.description AS description, e.website AS website, "
                "       e.naics4 AS naics4",
                name=name,
            ).single()

            if not emp_result:
                raise HTTPException(status_code=404, detail=f"Employer {name} not found")

            occ_result = session.run("""
                MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region),
                      (e)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r)
                OPTIONAL MATCH (course:Course {college: $college})-[pf:PREPARES_FOR]->(occ)
                OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
                WITH occ, d.annual_wage AS annual_wage,
                     collect(DISTINCT CASE WHEN course IS NOT NULL
                                          THEN {code: course.code, name: course.name,
                                                department: COALESCE(dept.name, ''),
                                                via_top: pf.via_top}
                                          END) AS course_rows
                RETURN occ.title AS title, occ.soc_code AS soc_code,
                       occ.description AS description,
                       annual_wage,
                       [c IN course_rows WHERE c IS NOT NULL] AS aligned_courses
            """, name=name, college=college).data()

            occ_map: dict[str, dict] = {}
            for r in occ_result:
                key = r["soc_code"]
                if key in occ_map:
                    continue
                course_rows = r["aligned_courses"] or []
                # Group by TOP6 — same institutional pivot the occupations
                # endpoint uses, so the alignment block can render the
                # same TopGroupBlock pattern.
                by_top: dict[str, list[CourseAlignment]] = defaultdict(list)
                for c in course_rows:
                    by_top[c.get("via_top") or ""].append(CourseAlignment(
                        code=c["code"],
                        name=c["name"],
                        department=c.get("department") or "Unknown",
                        via_top=c.get("via_top"),
                    ))
                aligned_top_groups = [
                    TopAlignmentGroup(
                        top_code=tc,
                        top_title=top_titles.get(tc, ""),
                        courses=sorted(courses, key=lambda c: c.code),
                    )
                    for tc, courses in by_top.items()
                ]
                aligned_top_groups.sort(key=lambda g: (-len(g.courses), g.top_code))
                occ_map[key] = {
                    "title": r["title"],
                    "soc_code": r["soc_code"],
                    "description": r.get("description"),
                    "annual_wage": r["annual_wage"],
                    "aligned_top_groups": [g.model_dump() for g in aligned_top_groups],
                    "aligned_course_count": len(course_rows),
                    "aligned_program_area_count": len(aligned_top_groups),
                    "industry_share": None,
                }

            region_result = session.run(
                "MATCH (e:Employer {name: $name})-[:IN_MARKET]->(r:Region) "
                "RETURN COALESCE(r.display_name, r.name) AS region, "
                "       COALESCE(r.priority_sectors, []) AS priority_sectors",
                name=name,
            ).data()

        swp_sectors = list(emp_result["swp_sectors"] or [])
        priority_union: set[str] = set()
        for r in region_result:
            for s in r.get("priority_sectors") or []:
                priority_union.add(s)
        priority_sectors_matched = [s for s in swp_sectors if s in priority_union]

        naics4 = emp_result["naics4"]

        # Attach industry-share (BLS OEWS PCT_TOTAL for the employer's
        # NAICS-4) so each occupation carries a "how prominent is this
        # role in this industry" signal. Drives the default sort below
        # — higher-share roles surface first, including the unaligned
        # ones that represent workforce-development opportunities.
        if naics4:
            oes_rows = oes_socs_for_naics4(naics4)
            share_by_soc = {r["soc"]: r["pct_total"] for r in oes_rows if r.get("pct_total")}
            for occ in occ_map.values():
                occ["industry_share"] = share_by_soc.get(occ["soc_code"])

        occupations = sorted(
            occ_map.values(),
            key=lambda o: (-(o.get("industry_share") or 0.0), -(o.get("annual_wage") or 0)),
        )

        return EmployerDetail(
            name=emp_result["name"],
            sector=emp_result["sector"],
            swp_sectors=swp_sectors,
            priority_sectors_matched=priority_sectors_matched,
            description=emp_result["description"],
            website=emp_result["website"],
            naics4=naics4,
            naics_title=naics_titles.get(naics4) if naics4 else None,
            regions=[r["region"] for r in region_result],
            occupations=occupations,
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
