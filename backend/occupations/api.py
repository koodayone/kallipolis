"""Occupation endpoints — labor market demand side."""

from collections import defaultdict
from fastapi import APIRouter, HTTPException
from ontology.schema import get_driver
from ontology.crosswalks import (
    cte_reachable_socs,
    load_cip_titles,
    load_top_titles,
    top6_to_cips_for_soc,
)
from occupations.models import (
    LaborMarketOverview,
    RegionOverview,
    OccupationMatch,
    OccupationDetail,
    CipMatch,
    CourseAlignment,
    TopAlignmentGroup,
    OccupationQueryRequest,
    OccupationQueryResponse,
)
from occupations.query import run_occupation_query

# SAM A/B/C/D = occupational classification per CCCCO MIS Data Element
# Dictionary. Filters out gen-ed feeders (SAM E) from the system-wide
# pathway query so the universe of "TOPs that feed this SOC" stays
# bounded to workforce-development action surface. Mirrors the asymmetric
# filter in partnerships._gather_curriculum_crosswalk.
SAM_OCCUPATIONAL = ["A", "B", "C", "D"]

router = APIRouter()


@router.get("/overview", response_model=LaborMarketOverview)
def get_labor_market_overview(college: str):
    """Returns regions and the CTE-reachable, regionally-demanded
    occupations for the college, tagged by curriculum-alignment status.

    Surfaces both aligned occupations (college has at least one
    PREPARES_FOR-aligned course) and gap occupations (regionally
    demanded and CTE-reachable globally, but no aligned curriculum at
    this college). Honest workforce-alignment surface — gaps are real
    institutional signal, not noise to drop. Mirrors the relaxed
    filter in partnerships.opportunity.build_sector_index.
    """
    driver = get_driver()
    cte_socs = list(cte_reachable_socs())
    try:
        with driver.session() as session:
            # OPTIONAL MATCH on the PREPARES_FOR + CONTAINS chain so SOCs
            # without aligned curriculum at this college still surface.
            # CTE filter (`occ.soc_code IN $cte_socs`) preserves the
            # workforce-development scope — non-CTE SOCs (gen-ed roles,
            # etc.) would otherwise flood the list.
            result = session.run("""
                MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                WHERE occ.soc_code IN $cte_socs
                OPTIONAL MATCH (occ)<-[:PREPARES_FOR]-(course:Course {college: $college})
                                <-[:CONTAINS]-(dept:Department)
                RETURN COALESCE(r.display_name, r.name) AS region,
                       occ.soc_code AS soc_code, occ.title AS title,
                       occ.description AS description, d.annual_wage AS annual_wage,
                       d.employment AS employment,
                       d.growth_rate AS growth_rate,
                       d.annual_openings AS annual_openings,
                       occ.education_level AS education_level,
                       count(DISTINCT course) AS aligned_course_count,
                       count(DISTINCT dept) AS aligned_department_count
            """, college=college, cte_socs=cte_socs)
            records = result.data()

        if not records:
            raise HTTPException(status_code=404, detail=f"No labor market data for {college}")

        regions: dict[str, list] = defaultdict(list)
        for r in records:
            course_count = r["aligned_course_count"]
            regions[r["region"]].append(OccupationMatch(
                soc_code=r["soc_code"],
                title=r["title"],
                description=r["description"],
                annual_wage=r["annual_wage"],
                employment=r["employment"],
                growth_rate=r.get("growth_rate"),
                annual_openings=r.get("annual_openings"),
                education_level=r.get("education_level"),
                aligned_course_count=course_count,
                aligned_department_count=r["aligned_department_count"],
                alignment_status="aligned" if course_count > 0 else "gap",
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

            # System-wide TOP6 pathway: every TOP6 that ANY college has a
            # SAM A/B/C/D PREPARES_FOR course under for this SOC. Defines
            # the universe of TOPs that institutionally feed the SOC;
            # whichever subset this college teaches becomes the taught
            # set, the remainder surfaces as untaught (curriculum-
            # development surface). Mirrors the global query in
            # partnerships._gather_curriculum_crosswalk — same Cypher,
            # same SAM filter, same source of truth.
            global_top_rows = session.run("""
                MATCH (c:Course)-[r:PREPARES_FOR]->(:Occupation {soc_code: $soc})
                WHERE c.sam_code IN $sam_codes
                RETURN DISTINCT r.via_top AS top6
            """, soc=soc_code, sam_codes=SAM_OCCUPATIONAL).data()

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
        cip_titles = load_cip_titles()
        by_top: dict[str, list[CourseAlignment]] = defaultdict(list)
        for c in aligned_courses:
            by_top[c.via_top or ""].append(c)

        taught_top6 = {tc for tc in by_top if tc}
        global_top6 = {row["top6"] for row in global_top_rows if row.get("top6")}

        # Universe = taught ∪ global. Drop blanks; we don't render
        # courses-without-TOP as a standalone group (rare edge case).
        all_top6 = (taught_top6 | global_top6)
        all_top6.discard("")

        aligned_top_groups: list[TopAlignmentGroup] = []
        for top6 in all_top6:
            courses = sorted(by_top.get(top6, []), key=lambda c: c.code)
            taught = top6 in taught_top6
            cip_codes = top6_to_cips_for_soc(top6, soc_code)
            cips = [
                CipMatch(code=cip, title=cip_titles.get(cip, ""))
                for cip in cip_codes
            ]
            aligned_top_groups.append(TopAlignmentGroup(
                top_code=top6,
                top_title=top_titles.get(top6, ""),
                taught=taught,
                courses=courses,
                cips=cips,
            ))

        # Sort: taught first (strongest concentration first within
        # taught), then untaught (alphabetical by TOP code). Keeps "what
        # we teach" front-loaded, with the system pathway visible below.
        aligned_top_groups.sort(key=lambda g: (
            0 if g.taught else 1,
            -len(g.courses),
            g.top_code,
        ))

        return OccupationDetail(
            soc_code=soc_code,
            title=occ_result["title"],
            description=occ_result["description"],
            education_level=occ_result["education_level"],
            aligned_top_groups=aligned_top_groups,
            aligned_course_count=len(aligned_courses),
            # Total TOP6 groups in the section (taught + untaught) so the
            # "Show all N program areas" affordance reflects what's
            # actually displayable. Previously counted only taught
            # groups; the rename to drop "aligned_" would ripple across
            # employers/api.ts and is deferred.
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
