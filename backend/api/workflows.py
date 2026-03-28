import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import ProposalList, ProposalRequest, TargetedProposal, ReportRequest, IngestRequest
from workflows.partnerships import run_targeted_proposal, stream_targeted_proposal
from workflows.report import run_report
from workflows.ingestion import run_ingest

router = APIRouter()


@router.post("/partnerships/targeted", response_model=TargetedProposal)
async def targeted_partnership(req: ProposalRequest):
    try:
        return await run_targeted_proposal(req.employer, req.college, req.objective)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/partnerships/targeted/stream")
async def targeted_partnership_stream(req: ProposalRequest):
    def event_generator():
        try:
            for proposal in stream_targeted_proposal(req.employer, req.college, req.objective):
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


@router.post("/report")
async def report(req: ReportRequest):
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
