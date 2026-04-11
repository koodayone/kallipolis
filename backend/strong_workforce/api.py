"""Strong Workforce Program endpoints — LMI context and project generation."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from strong_workforce.models import SwpProjectRequest, LmiContext
from strong_workforce.generate import get_lmi_context, stream_swp_project

router = APIRouter()


@router.post("/lmi-context", response_model=LmiContext)
async def swp_lmi_context(req: SwpProjectRequest):
    """Pre-fetch LMI demand/supply data for the SWP context panel."""
    try:
        return get_lmi_context(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/project/stream")
async def swp_project_stream(req: SwpProjectRequest):
    """Phase 3: stream SWP sections as they complete.

    SSE event types:
      data: {"type": "lmi", "lmi_context": {...}}       — LMI data, sent immediately
      data: {"type": "section", "section": {...}}       — each section as Claude completes it
      data: {"done": true}                              — generation finished
      data: {"error": "..."}                            — on failure
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
