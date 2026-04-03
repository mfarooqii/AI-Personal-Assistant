"""
Aria structured logging.

Three sinks:
  1. Colorised console
  2. Rotating file at ~/.aria/logs/aria.log
  3. Two in-memory ring buffers: backend (Python) + frontend (browser)

Three output formats served by get_backend_logs / get_frontend_logs:
  raw    — raw structured entry (id, level, module, message, …)
  human  — plain-English rewrite of the message, with time_ago + component
  ai     — human + likely_cause + suggested_action, ideal for LLM context

Also intercepts stdlib logging so uvicorn, fastapi, httpx, sqlalchemy all
flow through the same pipeline.
"""

from __future__ import annotations

import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Module display names
# ---------------------------------------------------------------------------

_MODULE_NAMES: dict[str, str] = {
    "app.routes.chat":          "Chat API",
    "app.routes.browser":       "Browser Agent",
    "app.routes.extension":     "Extension",
    "app.routes.tasks":         "Task Queue",
    "app.routes.memory":        "Memory",
    "app.routes.voice":         "Voice",
    "app.routes.settings":      "Settings",
    "app.routes.workflows":     "Workflows",
    "app.routes.onboarding":    "Onboarding",
    "app.routes.integrations":  "Gmail",
    "app.routes.logs":          "Logs API",
    "app.agents.router":        "Agent Router",
    "app.agents.executor":      "Agent Executor",
    "app.agents.ollama_client": "Ollama Client",
    "app.agents.registry":      "Agents",
    "app.memory.manager":       "Memory Manager",
    "app.memory.database":      "Database",
    "app.browser.engine":       "Browser Engine",
    "app.browser.agent":        "Browser AI",
    "app.browser.detect":       "Intent Detect",
    "app.tools.executor":       "Tool Executor",
    "app.tools.registry":       "Tools",
    "app.scheduler.engine":     "Scheduler",
    "app.utils.logger":         "Logger",
    "uvicorn":                  "HTTP Server",
    "uvicorn.access":           "HTTP Access",
    "uvicorn.error":            "Server Error",
    "fastapi":                  "FastAPI",
}


def _module_label(module: str) -> str:
    if module in _MODULE_NAMES:
        return _MODULE_NAMES[module]
    for prefix, name in _MODULE_NAMES.items():
        if module.startswith(prefix):
            return name
    parts = module.split(".")
    return parts[-1].replace("_", " ").title() if parts else module


# ---------------------------------------------------------------------------
# Time helper
# ---------------------------------------------------------------------------

def _time_ago(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc) - dt).total_seconds()
        if delta < 10:   return "just now"
        if delta < 60:   return f"{int(delta)}s ago"
        if delta < 3600: return f"{int(delta / 60)}m ago"
        if delta < 86400: return f"{int(delta / 3600)}h ago"
        return f"{int(delta / 86400)}d ago"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Message humanization
# ---------------------------------------------------------------------------

_HTTP_PAT = re.compile(
    r'"(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (/[^\s"]*) HTTP/[\d.]+" (\d+)'
)
_HTTP_STATUS: dict[int, str] = {
    200: "OK", 201: "Created", 204: "No content",
    301: "Redirect", 302: "Redirect",
    400: "Bad request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not found", 405: "Method not allowed",
    422: "Invalid input data", 429: "Rate limited",
    500: "Server error", 502: "Bad gateway",
    503: "Service unavailable", 504: "Gateway timeout",
}


def _humanize_message(msg: str) -> str:
    m = _HTTP_PAT.search(msg)
    if m:
        method, path, code = m.group(1), m.group(2), int(m.group(3))
        status = _HTTP_STATUS.get(code, str(code))
        tick = "✓" if code < 400 else "✗"
        return f"{tick} {method} {path} — {status}"
    low = msg.lower()
    if "connection refused" in low:
        return ("Cannot connect to Ollama AI model (port 11434)"
                if "11434" in msg else
                "Connection refused — a required service is unreachable")
    if "no module named" in low:
        pkg = msg.split("No module named")[-1].strip().strip("' \"")
        return f"Missing Python package: {pkg}"
    if "importerror" in low:
        return f"Python import failed: {msg}"
    if "operationalerror" in low:
        return "Database operation failed"
    if "timeouterror" in low or "timed out" in low:
        return "Operation timed out"
    if "filenotfounderror" in low:
        tail = msg.split(":")[-1].strip() if ":" in msg else msg
        return f"File not found: {tail}"
    if "startup complete" in low or "application startup complete" in low:
        return "✓ Aria server is ready"
    if "shutting down" in low:
        return "Aria server is shutting down"
    if "started server process" in low:
        return "HTTP server process started"
    return msg


# ---------------------------------------------------------------------------
# AI explanation
# ---------------------------------------------------------------------------

def _ai_explain(entry: dict) -> dict:
    """Return structured explanation fields — what happened, why, and how to fix it."""
    msg  = entry["message"]
    module = entry.get("module", "")
    low  = msg.lower()
    component = _module_label(module)

    m = _HTTP_PAT.search(msg)
    if m:
        method, path, code = m.group(1), m.group(2), int(m.group(3))
        if code < 400:
            return {"summary": f"Request to {path} succeeded",
                    "component": component, "likely_cause": None,
                    "suggested_action": None, "is_actionable": False}
        http_fixes: dict[int, tuple[str, str, str]] = {
            422: (f"API rejected the request to {path} — input data is invalid",
                  "The frontend sent a request with missing fields or wrong data types",
                  "Open browser DevTools → Network, replay the request and check the payload"),
            500: (f"The {path} endpoint crashed with a server error",
                  "An unhandled Python exception happened inside this route",
                  "Look for the ERROR log entry just before this one — it has the actual exception"),
            404: (f"Route {path} was not found",
                  "The frontend is calling an API endpoint that hasn't been registered",
                  "Check that the router for this path is included in backend/app/main.py"),
            401: (f"Request to {path} was rejected — not authenticated",
                  "Missing or invalid authentication token",
                  "Re-authenticate or verify the correct credentials are being sent"),
        }
        summary, cause, fix = http_fixes.get(code, (
            f"Unexpected HTTP {code} on {path}",
            f"Server returned status {code}",
            "Check the server logs above for the Python exception that caused this",
        ))
        return {"summary": summary, "component": component,
                "likely_cause": cause, "suggested_action": fix, "is_actionable": True}

    if "connection refused" in low:
        if "11434" in msg:
            return {"summary": "Aria cannot reach the Ollama AI model engine",
                    "component": "Ollama Client",
                    "likely_cause": "Ollama is not running or has crashed",
                    "suggested_action": "Open a terminal and run: ollama serve",
                    "is_actionable": True}
        return {"summary": "A required service refused the connection",
                "component": component,
                "likely_cause": "The target service is not running on the expected port",
                "suggested_action": "Identify which service uses the refused port and restart it",
                "is_actionable": True}

    if "no module named" in low or "importerror" in low:
        pkg = (msg.split("No module named")[-1].strip().strip("' \"")
               if "No module named" in msg else "unknown")
        return {"summary": f"Required Python package '{pkg}' is not installed",
                "component": component,
                "likely_cause": "Package missing from the virtual environment",
                "suggested_action": f"cd backend && source .venv/bin/activate && pip install {pkg}",
                "is_actionable": True}

    if "operationalerror" in low or ("sqlite" in low and "error" in low):
        return {"summary": "Database operation failed",
                "component": "Database",
                "likely_cause": "SQLite file is corrupt, locked, or un-initialized",
                "suggested_action": "Delete ~/.aria/aria.db — Aria will recreate it on next start",
                "is_actionable": True}

    if "timeouterror" in low or "timed out" in low:
        return {"summary": "A task was cancelled because it took too long",
                "component": component,
                "likely_cause": "AI model is overloaded, or a browser action stalled",
                "suggested_action": "Increase TASK_TIMEOUT_SECONDS in backend/.env, or try a simpler task",
                "is_actionable": True}

    if "filenotfounderror" in low:
        return {"summary": "A file required by Aria is missing",
                "component": component,
                "likely_cause": "Expected file or directory hasn't been created yet",
                "suggested_action": "Run ./setup.sh to recreate the required directory structure",
                "is_actionable": True}

    return {"summary": _humanize_message(msg), "component": component,
            "likely_cause": None, "suggested_action": None, "is_actionable": False}


# ---------------------------------------------------------------------------
# In-memory ring buffers  (backend = Python logs, frontend = browser logs)
# ---------------------------------------------------------------------------

_backend_buffer:  list[dict] = []
_frontend_buffer: list[dict] = []
_MAX_BUFFER = 2000
_backend_counter  = 0
_frontend_counter = 0

# Keep old name so any existing code that directly accesses _log_buffer still works
_log_buffer = _backend_buffer


def _buffer_sink(message) -> None:  # type: ignore[override]
    global _backend_counter
    record = message.record
    _backend_counter += 1
    _backend_buffer.append({
        "id":        _backend_counter,
        "timestamp": record["time"].isoformat(),
        "level":     record["level"].name,
        "module":    record["name"],
        "function":  record["function"],
        "line":      record["line"],
        "message":   record["message"],
    })
    if len(_backend_buffer) > _MAX_BUFFER:
        _backend_buffer.pop(0)


def add_frontend_log(entries: list[dict]) -> None:
    global _frontend_counter
    for entry in entries:
        _frontend_counter += 1
        _frontend_buffer.append({
            "id":        _frontend_counter,
            "timestamp": entry.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "level":     entry.get("level", "info").upper(),
            "module":    "frontend." + entry.get("source", "app").replace(".tsx", "").replace(".ts", ""),
            "function":  entry.get("source", ""),
            "line":      entry.get("line", 0),
            "message":   entry.get("message", ""),
            "stack":     entry.get("stack"),
            "url":       entry.get("url"),
        })
        if len(_frontend_buffer) > _MAX_BUFFER:
            _frontend_buffer.pop(0)


# ---------------------------------------------------------------------------
# Filter + format helpers
# ---------------------------------------------------------------------------

def _apply_filters(
    buf: list[dict],
    limit: int,
    level: Optional[str],
    search: Optional[str],
    after_id: Optional[int],
) -> list[dict]:
    entries = list(buf)
    if after_id is not None:
        entries = [e for e in entries if e["id"] > after_id]
    if level and level.upper() not in ("ALL", ""):
        entries = [e for e in entries if e["level"] == level.upper()]
    if search:
        q = search.lower()
        entries = [e for e in entries
                   if q in e["message"].lower() or q in e["module"].lower()]
    return list(reversed(entries))[:limit]


def _enrich(entry: dict, fmt: str) -> dict:
    if fmt == "raw":
        return entry
    base = {**entry,
            "time_ago":  _time_ago(entry["timestamp"]),
            "component": _module_label(entry["module"])}
    if fmt == "human":
        return {**base, "message": _humanize_message(entry["message"])}
    if fmt == "ai":
        exp = _ai_explain(entry)
        return {**base, **exp, "technical_detail": entry["message"]}
    return base


def get_backend_logs(
    limit: int = 300,
    level: Optional[str] = None,
    search: Optional[str] = None,
    after_id: Optional[int] = None,
    fmt: str = "raw",
) -> list[dict]:
    entries = _apply_filters(_backend_buffer, limit, level, search, after_id)
    return [_enrich(e, fmt) for e in entries]


def get_frontend_logs(
    limit: int = 300,
    level: Optional[str] = None,
    search: Optional[str] = None,
    after_id: Optional[int] = None,
    fmt: str = "raw",
) -> list[dict]:
    entries = _apply_filters(_frontend_buffer, limit, level, search, after_id)
    return [_enrich(e, fmt) for e in entries]


# ---------------------------------------------------------------------------
# Legacy aliases (keep old callers working)
# ---------------------------------------------------------------------------

def get_log_buffer(
    limit: int = 200,
    level: Optional[str] = None,
    search: Optional[str] = None,
    after_id: Optional[int] = None,
) -> list[dict]:
    return get_backend_logs(limit=limit, level=level, search=search,
                            after_id=after_id, fmt="raw")


def clear_log_buffer() -> None:
    _backend_buffer.clear()


def clear_all_logs() -> None:
    _backend_buffer.clear()
    _frontend_buffer.clear()


# ---------------------------------------------------------------------------
# stdlib → loguru bridge
# ---------------------------------------------------------------------------

class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# ---------------------------------------------------------------------------
# Public setup
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Path, debug: bool = False) -> None:
    """Initialise all sinks. Call once at application startup."""
    logger.remove()
    level = "DEBUG" if debug else "INFO"

    logger.add(
        sys.stdout,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    log_file = log_dir / "aria.log"
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        enqueue=True,
    )

    logger.add(_buffer_sink, level="DEBUG", format="{message}")

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "httpx", "sqlalchemy"):
        lib_logger = logging.getLogger(name)
        lib_logger.handlers = [_InterceptHandler()]
        lib_logger.propagate = False

    logger.info("Aria logging ready — level={} log_file={}", level, log_file)
