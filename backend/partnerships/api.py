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
    """Returns employers ranked by partnership opportunity — skill alignment, gaps, and top occupation.

    Reads the precomputed `PARTNERSHIP_ALIGNMENT` edge. The writer that
    materializes this edge is not currently checked into the repository
    (see docs/architecture/graph-model.md "Known gap"), so on a fresh
    database this endpoint returns an empty opportunities list.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (col:College {name: $college})-[pa:PARTNERSHIP_ALIGNMENT]->(emp:Employer)
                RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                       pa.alignment_score AS alignment_score,
                       pa.gap_count AS gap_count,
                       pa.aligned_skills AS aligned_skills,
                       pa.gap_skills AS gap_skills,
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
                    description=r.get("description"),
                    alignment_score=r["alignment_score"],
                    gap_count=r["gap_count"],
                    aligned_skills=r["aligned_skills"],
                    gap_skills=r["gap_skills"],
                    top_occupation=r.get("top_occupation"),
                    top_wage=r.get("top_wage"),
                    pipeline_size=r.get("pipeline_size"),
                )
                for r in records
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employer-pipeline")
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
                WITH st, count(DISTINCT sk) AS matching_skills
                WHERE matching_skills >= 3
                RETURN count(st) AS pipeline_size
            """, college=college, employer=employer)
            record = result.single()

        return {"pipeline_size": record["pipeline_size"] if record else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employer-occupations")
def get_employer_occupations(employer: str):
    """Returns occupations an employer hires for — lightweight, no skill joins."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (emp:Employer {name: $employer})-[:IN_MARKET]->(r:Region),
                      (emp)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r)
                RETURN occ.title AS title, d.annual_wage AS annual_wage
                ORDER BY d.annual_wage DESC
            """, employer=employer).data()
        return {"occupations": result}
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
        return await run_targeted_proposal(req.employer, req.college, req.engagement_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/targeted/stream")
async def targeted_partnership_stream(req: ProposalRequest):
    def event_generator():
        try:
            for proposal in stream_targeted_proposal(req.employer, req.college, req.engagement_type):
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
