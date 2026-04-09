import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import (
    ProposalList, ProposalRequest, NarrativeProposal, ReportRequest, IngestRequest,
    SwpProjectRequest, SwpProject, LmiContext,
)
from workflows.partnerships import run_targeted_proposal, stream_targeted_proposal
from workflows.swp import get_lmi_context, stream_swp_project
from workflows.report import run_report
from workflows.ingestion import run_ingest

router = APIRouter()


@router.post("/partnerships/targeted", response_model=NarrativeProposal)
async def targeted_partnership(req: ProposalRequest):
    try:
        return await run_targeted_proposal(req.employer, req.college, req.engagement_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/partnerships/targeted/stream")
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


@router.post("/swp/lmi-context", response_model=LmiContext)
async def swp_lmi_context(req: SwpProjectRequest):
    """Pre-fetch LMI demand/supply data for the SWP context panel."""
    try:
        return get_lmi_context(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/swp/project/stream")
async def swp_project_stream(req: SwpProjectRequest):
    """Phase 3: stream SWP sections as they complete.

    SSE event types:
      data: {"type": "lmi", "lmi_context": {...}}       — LMI data, sent immediately
      data: {"type": "section", "section": {...}}        — each section as Claude completes it
      data: {"done": true}                               — generation finished
      data: {"error": "..."}                             — on failure
    """
    def event_generator():
        try:
            for kind, payload in stream_swp_project(req):
                if kind == "lmi":
                    yield f'data: {{"type": "lmi", "lmi_context": {payload.model_dump_json()}}}\n\n'
                elif kind == "section":
                    yield f'data: {{"type": "section", "section": {payload.model_dump_json()}}}\n\n'
            yield f'data: {{"done": true}}\n\n'
        except Exception as e:
            yield f'data: {{"error": {json.dumps(str(e))}}}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/report")
async def report(req: ReportRequest):
    """Legacy report endpoint — SWP now uses /swp/project/stream."""
    try:
        return await run_report(req.report_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest(req: IngestRequest):
    try:
        return await run_ingest(req.document_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
