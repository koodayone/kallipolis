import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import ProposalList, ReportRequest, IngestRequest
from workflows.partnerships import run_partnerships, stream_partnerships
from workflows.report import run_report
from workflows.ingestion import run_ingest

router = APIRouter()


@router.post("/partnerships", response_model=ProposalList)
async def partnerships():
    try:
        return await run_partnerships()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/partnerships/stream")
async def partnerships_stream():
    def event_generator():
        try:
            for proposal in stream_partnerships():
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
