"""
Electron IPC Bridge — lets the Python browser agent control the
real, user-visible Chromium BrowserView embedded in the Electron app.

When Aria runs as a desktop app (Electron), the agent sends commands here
→ the Electron main process executes them on the live BrowserView
→ user watches every action in real time, no bot detection, no screenshots.

Falls back gracefully if the Electron IPC server is not available
(i.e. when running as a plain web app).
"""

import asyncio
import logging
from typing import Optional

import httpx

log = logging.getLogger(__name__)

ELECTRON_IPC_URL = "http://127.0.0.1:8001"

# Cache the detection result so we only probe once per process lifetime
_electron_available: Optional[bool] = None
_detection_lock = asyncio.Lock()


async def is_available() -> bool:
    """Return True if the Electron IPC server is reachable."""
    global _electron_available
    if _electron_available is not None:
        return _electron_available

    async with _detection_lock:
        if _electron_available is not None:
            return _electron_available
        try:
            async with httpx.AsyncClient(timeout=0.8) as client:
                resp = await client.get(f"{ELECTRON_IPC_URL}/browser/state")
                _electron_available = resp.status_code == 200
        except Exception:
            _electron_available = False

    if _electron_available:
        log.info("Electron IPC bridge detected — using live BrowserView")
    return _electron_available


def reset_detection() -> None:
    """Force re-detection on next call (useful in tests)."""
    global _electron_available
    _electron_available = None


# ── Browser commands ──────────────────────────────────────────────────────────

async def go_back() -> bool:
    """Navigate the BrowserView back in history."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/back", json={})
        return True
    except Exception as e:
        log.error("electron_bridge.go_back: %s", e)
        return False


async def go_forward() -> bool:
    """Navigate the BrowserView forward in history."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/forward", json={})
        return True
    except Exception as e:
        log.error("electron_bridge.go_forward: %s", e)
        return False


async def reload() -> bool:
    """Reload the current page in the BrowserView."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/reload", json={})
        return True
    except Exception as e:
        log.error("electron_bridge.reload: %s", e)
        return False


async def navigate(url: str) -> bool:
    """Navigate the BrowserView to *url*."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/navigate", json={"url": url})
        return True
    except Exception as e:
        log.error("electron_bridge.navigate: %s", e)
        return False


async def click(x: int, y: int) -> bool:
    """Click at viewport coordinates (x, y)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/click", json={"x": x, "y": y})
        return True
    except Exception as e:
        log.error("electron_bridge.click: %s", e)
        return False


async def type_text(text: str) -> bool:
    """Type text into the focused element in the BrowserView."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/type", json={"text": text})
        return True
    except Exception as e:
        log.error("electron_bridge.type_text: %s", e)
        return False


async def press_key(key: str) -> bool:
    """Press a special key (Enter, Tab, Escape, Backspace, ArrowDown, …)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/key", json={"key": key})
        return True
    except Exception as e:
        log.error("electron_bridge.press_key: %s", e)
        return False


async def scroll(direction: str = "down") -> bool:
    """Scroll the current page up or down."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/scroll", json={"direction": direction})
        return True
    except Exception as e:
        log.error("electron_bridge.scroll: %s", e)
        return False


async def get_page_state() -> dict:
    """
    Return the current page's interactive element map + text.
    Same structure as BrowserEngine.get_page_state():
    { url, title, elements: [{id, tag, role, text, x, y, ...}], text }
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"{ELECTRON_IPC_URL}/browser/state")
            return resp.json()
    except Exception as e:
        log.error("electron_bridge.get_page_state: %s", e)
        return {"url": "", "title": "", "elements": [], "text": ""}


async def screenshot() -> str:
    """Return a base64 JPEG screenshot from the BrowserView."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"{ELECTRON_IPC_URL}/browser/screenshot")
            return resp.json().get("screenshot", "")
    except Exception as e:
        log.error("electron_bridge.screenshot: %s", e)
        return ""


async def show(bounds: Optional[dict] = None) -> bool:
    """
    Make the BrowserView visible.
    *bounds* = {x, y, width, height} in screen pixels.
    Pass None to use the default right-panel position.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/show", json={"bounds": bounds})
        return True
    except Exception as e:
        log.error("electron_bridge.show: %s", e)
        return False


async def hide() -> bool:
    """Hide the BrowserView."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(f"{ELECTRON_IPC_URL}/browser/hide", json={})
        return True
    except Exception as e:
        log.error("electron_bridge.hide: %s", e)
        return False


async def send_status(message: str, action: str = "") -> None:
    """
    Push a status/action message to the React UI so the user can see
    what the agent is doing while watching the live browser.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{ELECTRON_IPC_URL}/browser/status",
                json={"message": message, "action": action},
            )
    except Exception:
        pass  # Non-critical — don't interrupt task flow
