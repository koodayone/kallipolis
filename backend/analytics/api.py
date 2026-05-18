"""Lightweight analytics beacon.

Accepts page-view events from the frontend and appends them as
structured JSON lines to a rotating log file. The backend captures
the client IP server-side so the frontend never handles it.

Log file: backend/logs/analytics.jsonl
Format per line:
  { "ts": "...", "ip": "...", "site": "...", "path": "...", "referrer": "..." }
"""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

# ── Log setup ────────────────────────────────────────────────────────────

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_analytics_logger = logging.getLogger("kallipolis.analytics")
_analytics_logger.setLevel(logging.INFO)
_analytics_logger.propagate = False

_handler = RotatingFileHandler(
    _LOG_DIR / "analytics.jsonl",
    maxBytes=50 * 1024 * 1024,  # 50 MB
    backupCount=5,
)
_handler.setFormatter(logging.Formatter("%(message)s"))
_analytics_logger.addHandler(_handler)


# ── Schema ───────────────────────────────────────────────────────────────

class BeaconPayload(BaseModel):
    path: str
    referrer: str = ""
    site: str = ""  # "app" or "atlas" — set by the frontend


# ── Endpoint ─────────────────────────────────────────────────────────────

def _client_ip(request: Request) -> str:
    """Best-effort client IP, respecting X-Forwarded-For behind Caddy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/beacon", status_code=204)
async def beacon(payload: BeaconPayload, request: Request):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ip": _client_ip(request),
        "site": payload.site,
        "path": payload.path,
        "referrer": payload.referrer,
    }
    _analytics_logger.info(json.dumps(entry, separators=(",", ":")))
    return
