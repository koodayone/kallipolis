"""Partnership endpoints — landscape queries and proposal generation."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ontology.schema import get_driver
from partnerships.models import (
    PartnershipOpportunity,
    PartnershipLandscape,
    PartnershipQueryRequest,
    PartnershipQueryResponse,
    ProposalRequest,
    NarrativeProposal,
)
from partnerships.query import run_partnership_query
from partnerships.generate import run_targeted_proposal, stream_targeted_proposal

router = APIRouter()


@router.get("/landscape", response_model=PartnershipLandscape)
def get_partnership_landscape(college: str):
    """Returns employers ranked by partnership opportunity — institutional
    curriculum alignment via the TOP-SOC crosswalk, gaps, and top occupation.

    Filtered to employers with at least one institutionally-aligned hires
    SOC at this college (`pa.alignment_score > 0`). Per the
    institutional-deference architectural commitment, the partnerships
    surface only shows opportunities where the institutional crosswalk
    establishes a real pathway: at least one of the employer's HIRES_FOR
    occupations has a Course-[:PREPARES_FOR]->Occupation edge from this
    college's catalog. Employers whose hires are entirely uncovered at
    this college are omitted from the landscape view; the underlying
    Employer node remains in the graph for cross-college visibility.

    Reads the precomputed `PARTNERSHIP_ALIGNMENT` edge, materialized at
    ingestion time by `partnerships/compute.py`. If the edge set is
    empty, either ingestion hasn't run for this college or the compute
    step was skipped; rerun `python -m pipeline.reload --region <r>`.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region),
                      (col)-[pa:PARTNERSHIP_ALIGNMENT]->(emp:Employer)
                WHERE pa.alignment_score > 0
                RETURN emp.name AS name, emp.sector AS sector,
                       COALESCE(emp.swp_sectors, []) AS swp_sectors,
                       [s IN COALESCE(emp.swp_sectors, []) WHERE s IN COALESCE(r.priority_sectors, [])] AS priority_sectors_matched,
                       emp.description AS description, emp.website AS website,
                       pa.alignment_score AS alignment_score,
                       pa.gap_count AS gap_count,
                       pa.top_occupation AS top_occupation,
                       pa.top_wage AS top_wage,
                       pa.pipeline_size AS pipeline_size
                ORDER BY pa.alignment_score DESC
            """, college=college)
            records = result.data()

        return PartnershipLandscape(
            college=college,
            opportunities=[
                PartnershipOpportunity(
                    name=r["name"],
                    sector=r.get("sector"),
                    swp_sectors=r.get("swp_sectors", []) or [],
                    priority_sectors_matched=r.get("priority_sectors_matched", []) or [],
                    description=r.get("description"),
                    website=r.get("website"),
                    alignment_score=r["alignment_score"],
                    gap_count=r["gap_count"],
                    top_occupation=r.get("top_occupation"),
                    top_wage=r.get("top_wage"),
                    pipeline_size=r.get("pipeline_size"),
                )
                for r in records
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employer-occupations")
def get_employer_occupations(employer: str, college: str):
    """Returns occupations the employer hires for in the college's region.

    Filtered to occupations with at least one institutionally-aligned
    course at this college (`aligned_course_count > 0`). Per the
    institutional-deference architectural commitment, the picker is a
    guided experience: it only surfaces occupations where the
    Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks
    together establish a real pathway from this college's curriculum
    to that SOC. Coordinators cannot accidentally select an occupation
    for which no aligned curriculum exists and end up with an empty
    artifact; the picker quietly drops those choices.

    The dropped occupations remain in the employer's HIRES_FOR set in
    the graph (cross-college visibility) — the filter is presentation-
    layer only.

    The response is sorted by aligned_course_count DESC, then by
    annual_openings DESC. Coordinators see the deepest institutional
    pathway first; openings tiebreak when alignment depth is equal.
    The first row is the deterministic suggested default the picker
    pre-selects.

    `coe_region` is attached at the top level so callers can surface
    the geographic scope alongside the demand figures when needed.
    """
    from ontology.regions import COLLEGE_COE_REGION

    driver = get_driver()
    try:
        with driver.session() as session:
            rows = session.run("""
                MATCH (col:College {name: $college})-[:IN_MARKET]->(r:Region),
                      (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation),
                      (r)-[d:DEMANDS]->(occ)
                OPTIONAL MATCH (course:Course {college: $college})-[:PREPARES_FOR]->(occ)
                OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
                WITH occ, d,
                     count(DISTINCT course) AS aligned_course_count,
                     count(DISTINCT dept) AS aligned_department_count
                WHERE aligned_course_count > 0
                RETURN occ.title AS title,
                       occ.soc_code AS soc_code,
                       d.annual_wage AS annual_wage,
                       d.annual_openings AS annual_openings,
                       d.growth_rate AS growth_rate,
                       aligned_course_count,
                       aligned_department_count
                ORDER BY aligned_course_count DESC, coalesce(d.annual_openings, 0) DESC
            """, employer=employer, college=college).data()

        return {
            "coe_region": COLLEGE_COE_REGION.get(college, ""),
            "occupations": rows,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=PartnershipQueryResponse)
async def query_partnerships(req: PartnershipQueryRequest):
    try:
        opportunities, message, cypher = await run_partnership_query(req.query, req.college)
        return PartnershipQueryResponse(opportunities=opportunities, message=message, cypher=cypher)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/targeted", response_model=NarrativeProposal)
async def targeted_partnership(req: ProposalRequest):
    try:
        return await run_targeted_proposal(
            req.employer, req.college, req.selected_occupation_soc
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/targeted/stream")
async def targeted_partnership_stream(req: ProposalRequest):
    def event_generator():
        try:
            for proposal in stream_targeted_proposal(
                req.employer, req.college, req.selected_occupation_soc
            ):
                data = proposal.model_dump_json()
                yield f"data: {data}\n\n"
            yield f'data: {{"done": true}}\n\n'
        except Exception as e:
            yield f'data: {{"error": {json.dumps(str(e))}}}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
