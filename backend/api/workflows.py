from fastapi import APIRouter, HTTPException
from models import ProposalList, ReportRequest, IngestRequest
from workflows.partnerships import run_partnerships
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
