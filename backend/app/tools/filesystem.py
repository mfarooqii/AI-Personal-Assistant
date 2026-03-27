"""
Filesystem tools — sandboxed read/write within the user's data directory.
"""

from pathlib import Path
from app.config import settings

ALLOWED_BASE = settings.DATA_DIR / "files"
ALLOWED_BASE.mkdir(parents=True, exist_ok=True)


def _safe_path(user_path: str) -> Path:
    """Resolve path and ensure it stays within the allowed directory."""
    resolved = (ALLOWED_BASE / user_path).resolve()
    if not str(resolved).startswith(str(ALLOWED_BASE.resolve())):
        raise PermissionError(f"Access denied: path escapes sandbox")
    return resolved


async def read_file(path: str) -> dict:
    safe = _safe_path(path)
    if not safe.exists():
        return {"error": f"File not found: {path}"}
    content = safe.read_text(encoding="utf-8", errors="replace")
    if len(content) > 50000:
        content = content[:50000] + "\n... [truncated]"
    return {"path": path, "content": content}


async def write_file(path: str, content: str) -> dict:
    safe = _safe_path(path)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(content, encoding="utf-8")
    return {"path": path, "written": True, "size": len(content)}
