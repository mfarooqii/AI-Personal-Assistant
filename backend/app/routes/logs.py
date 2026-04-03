"""
/api/logs — structured log viewer.

Paths:
  GET    /api/logs/backend    — Python/server logs   (?format=raw|human|ai)
  GET    /api/logs/frontend   — Browser/JS logs      (?format=raw|human|ai)
  POST   /api/logs/frontend   — Receive log batch from the browser
  DELETE /api/logs            — Clear both buffers
  GET    /api/logs/stream     — SSE stream of all new entries (both sources)
  GET    /api/logs            — Legacy alias → /backend raw
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Body, Query
from fastapi.responses import StreamingResponse

from app.utils.logger import (
    _backend_buffer,
    _frontend_buffer,
    add_frontend_log,
    clear_all_logs,
    get_backend_logs,
    get_frontend_logs,
    get_log_buffer,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Backend logs  —  GET /api/logs/backend
# ---------------------------------------------------------------------------

@router.get("/backend")
async def backend_logs(
    fmt: str = Query("human", alias="format", description="raw | human | ai"),
    limit: int = Query(300, ge=1, le=1000),
    level: str = Query("ALL", description="ALL | DEBUG | INFO | WARNING | ERROR"),
    search: Optional[str] = Query(None, description="Search message or module"),
    after_id: Optional[int] = Query(None, description="Only entries newer than this id"),
):
    entries = get_backend_logs(limit=limit, level=level, search=search,
                               after_id=after_id, fmt=fmt)
    return {"logs": entries, "total": len(entries), "source": "backend", "format": fmt}


# ---------------------------------------------------------------------------
# Frontend logs  —  GET + POST /api/logs/frontend
# ---------------------------------------------------------------------------

@router.get("/frontend")
async def frontend_logs(
    fmt: str = Query("human", alias="format", description="raw | human | ai"),
    limit: int = Query(300, ge=1, le=1000),
    level: str = Query("ALL"),
    search: Optional[str] = Query(None),
    after_id: Optional[int] = Query(None),
):
    entries = get_frontend_logs(limit=limit, level=level, search=search,
                                after_id=after_id, fmt=fmt)
    return {"logs": entries, "total": len(entries), "source": "frontend", "format": fmt}


@router.post("/frontend")
async def receive_frontend_logs(entries: list = Body(...)):
    """Receive a batch of log entries posted by the browser."""
    if not isinstance(entries, list):
        entries = [entries]
    add_frontend_log(entries)
    return {"received": len(entries)}


# ---------------------------------------------------------------------------
# Clear  —  DELETE /api/logs
# ---------------------------------------------------------------------------

@router.delete("")
async def clear_logs():
    clear_all_logs()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# SSE stream  —  GET /api/logs/stream
# ---------------------------------------------------------------------------

@router.get("/stream")
async def stream_logs():
    """Server-Sent Events — pushes new entries from both sources every 500 ms."""

    async def _generate():
        last_b: int = _backend_buffer[-1]["id"]  if _backend_buffer  else 0
        last_f: int = _frontend_buffer[-1]["id"] if _frontend_buffer else 0
        while True:
            await asyncio.sleep(0.5)
            new_b = get_backend_logs(limit=50, after_id=last_b, fmt="human")
            new_f = get_frontend_logs(limit=50, after_id=last_f, fmt="human")
            for e in reversed(new_b):
                yield f"data: {json.dumps({**e, 'source': 'backend'})}\n\n"
                last_b = max(last_b, e["id"])
            for e in reversed(new_f):
                yield f"data: {json.dumps({**e, 'source': 'frontend'})}\n\n"
                last_f = max(last_f, e["id"])

    return StreamingResponse(_generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Legacy alias  —  GET /api/logs  (raw format, existing code unaffected)
# ---------------------------------------------------------------------------

@router.get("")
async def get_logs_legacy(
    limit: int = Query(300, ge=1, le=1000),
    level: str = Query("ALL"),
    search: Optional[str] = Query(None),
    after_id: Optional[int] = Query(None),
):
    """Backward-compatible endpoint. Prefer /backend or /frontend."""
    entries = get_log_buffer(limit=limit, level=level, search=search, after_id=after_id)
    return {"logs": entries, "total": len(entries)}

