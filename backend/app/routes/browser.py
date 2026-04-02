"""
Browser routes — WebSocket for real-time browser streaming + REST helpers.

Endpoints
---------
POST   /api/browser/session         → Start a new browser task
POST   /api/browser/session/resume  → Resume after user login
POST   /api/browser/interact        → User click / type / key in the browser
GET    /api/browser/screenshot      → One-shot screenshot
POST   /api/browser/close           → Close the browser
WS     /api/browser/ws              → Real-time event stream
"""

import asyncio
import json
import logging
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.browser.engine import BrowserEngine
from app.browser.agent import BrowserAgent, BrowserEvent

log = logging.getLogger(__name__)
router = APIRouter()

# ── Singleton session state ──────────────────────────────
# (One browser per Aria instance — local, single-user app)

_engine: Optional[BrowserEngine] = None
_agent:  Optional[BrowserAgent]  = None
_current_task: str = ""
_current_plan: dict = {}
_session_active: bool = False
_waiting_for_user: bool = False


def _get_engine() -> BrowserEngine:
    global _engine
    if _engine is None:
        _engine = BrowserEngine()
    return _engine


def _get_agent() -> BrowserAgent:
    global _agent
    engine = _get_engine()
    if _agent is None:
        _agent = BrowserAgent(engine)
    return _agent


def set_session(task: str, plan: dict) -> None:
    """Called by the chat route to populate the shared session state."""
    global _current_task, _current_plan, _session_active
    _current_task = task
    _current_plan = plan
    _session_active = True


# ── Pydantic models ──────────────────────────────────────

class SessionRequest(BaseModel):
    task: str                 # e.g. "Show me my Gmail inbox"
    provider: str = ""        # e.g. "gmail", "amazon" — optional hint

class InteractRequest(BaseModel):
    action: str               # click | type | key | scroll
    x: int = 0
    y: int = 0
    text: str = ""
    key: str = ""
    direction: str = "down"

class ResumeRequest(BaseModel):
    pass  # body can be empty — just signals "I'm done logging in"


# ── REST endpoints ───────────────────────────────────────

@router.post("/session")
async def start_session(req: SessionRequest):
    """
    Start a new browser task.  The AI plans the steps and returns
    the plan + initial state.  The frontend then connects via WebSocket
    to stream events.
    """
    global _current_task, _current_plan, _session_active, _waiting_for_user

    agent = _get_agent()
    engine = _get_engine()
    await engine.launch()

    _current_task = req.task
    _session_active = True
    _waiting_for_user = False

    # AI creates a browsing plan
    plan = await agent.plan_task(req.task)
    _current_plan = plan

    return {
        "status": "planned",
        "task": req.task,
        "plan": plan,
        "message": f"Opening {plan.get('website', 'browser')}...",
    }


@router.post("/interact")
async def interact(req: InteractRequest):
    """
    Handle a user interaction with the browser panel (click, type, etc.).
    Used during login flows when the user is controlling the browser.
    """
    engine = _get_engine()
    if not engine.is_running:
        return {"error": "Browser not running"}

    if req.action == "click":
        await engine.click_coordinates(req.x, req.y)
    elif req.action == "type":
        await engine.type_text(req.text)
    elif req.action == "key":
        await engine.press_key(req.key or "Enter")
    elif req.action == "scroll":
        await engine.scroll(req.direction)

    screenshot = await engine.screenshot()
    state = await engine.get_page_state()

    return {
        "screenshot": screenshot,
        "url": state.get("url", ""),
        "title": state.get("title", ""),
    }


@router.post("/session/resume")
async def resume_session(req: ResumeRequest):
    """
    Signal that the user has finished logging in.
    The WebSocket stream will pick up from here.
    """
    global _waiting_for_user
    _waiting_for_user = False
    return {"status": "resuming"}


@router.get("/screenshot")
async def get_screenshot():
    """One-shot screenshot of whatever the browser is showing."""
    engine = _get_engine()
    if not engine.is_running:
        return {"error": "Browser not running"}
    screenshot = await engine.screenshot()
    return {"screenshot": screenshot, "url": engine.current_url}


@router.post("/close")
async def close_browser():
    """Close the browser and clean up."""
    global _engine, _agent, _session_active, _waiting_for_user
    if _engine:
        await _engine.close()
    _engine = None
    _agent = None
    _session_active = False
    _waiting_for_user = False
    return {"status": "closed"}


# ── WebSocket ────────────────────────────────────────────

@router.websocket("/ws")
async def browser_websocket(ws: WebSocket):
    """
    Real-time browser event stream.

    Server → Client events:
        screenshot  — base64 JPEG of current viewport
        status      — "Navigating to gmail.com…"
        action      — "Clicking the search bar"
        interactive — "Please sign in, I'll wait"
        result      — extracted data from page
        complete    — task finished
        error       — something went wrong

    Client → Server events:
        click       — {type:"click", x:500, y:300}
        type        — {type:"type", text:"hello"}
        key         — {type:"key", key:"Enter"}
        scroll      — {type:"scroll", direction:"down"}
        resume      — {type:"resume"}  (user done with login)
        message     — {type:"message", text:"now summarize"}  (follow-up)
    """
    await ws.accept()
    global _waiting_for_user

    agent = _get_agent()
    engine = _get_engine()

    try:
        task = _current_task
        plan = _current_plan

        # If no session was set yet, wait for the client to send task/plan
        if not task:
            try:
                init = await asyncio.wait_for(ws.receive_json(), timeout=10)
                task = init.get("task", "")
                plan = init.get("plan", {})
                if task:
                    set_session(task, plan)
            except asyncio.TimeoutError:
                pass

        if not task:
            await ws.send_json({"type": "error", "message": "No active task. Start a session first."})
            return

        await engine.launch()

        # Run the agent and stream events
        async for event in agent.execute(task, plan):
            payload = _event_to_dict(event)
            await ws.send_json(payload)

            if event.type == "interactive":
                _waiting_for_user = True
                # Wait for user to interact and then resume
                await _wait_and_handle_user_input(ws, agent, engine)
                return  # connection will be re-established or continue

            if event.type == "complete":
                return

        # Listen for follow-up messages after completion
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_json(), timeout=300)
                await _handle_client_message(data, ws, agent, engine)
            except asyncio.TimeoutError:
                break

    except WebSocketDisconnect:
        log.info("Browser WebSocket disconnected")
    except Exception as e:
        log.exception("Browser WebSocket error")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


async def _wait_and_handle_user_input(
    ws: WebSocket,
    agent: BrowserAgent,
    engine: BrowserEngine,
) -> None:
    """
    While the user is interacting (login flow), handle their clicks/types
    and stream screenshots.  When they signal 'resume', continue the task.
    """
    global _waiting_for_user

    # Start periodic screenshot stream so user sees what's happening
    screenshot_task = asyncio.create_task(_stream_screenshots(ws, engine))

    try:
        while _waiting_for_user:
            try:
                data = await asyncio.wait_for(ws.receive_json(), timeout=120)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "status", "message": "Still waiting for you to sign in..."})
                continue

            msg_type = data.get("type", "")

            if msg_type == "resume":
                _waiting_for_user = False
                break
            elif msg_type == "click":
                await engine.click_coordinates(data.get("x", 0), data.get("y", 0))
            elif msg_type == "type":
                await engine.type_text(data.get("text", ""))
            elif msg_type == "key":
                await engine.press_key(data.get("key", "Enter"))
            elif msg_type == "scroll":
                await engine.scroll(data.get("direction", "down"))
    finally:
        screenshot_task.cancel()
        try:
            await screenshot_task
        except asyncio.CancelledError:
            pass

    # Resume the AI agent after login
    async for event in agent.continue_after_login(_current_task, _current_plan):
        await ws.send_json(_event_to_dict(event))


async def _stream_screenshots(ws: WebSocket, engine: BrowserEngine) -> None:
    """Background task: send screenshots every 1.5 s while user is interacting."""
    try:
        while True:
            await asyncio.sleep(1.5)
            if engine.is_running:
                shot = await engine.screenshot()
                state = await engine.get_page_state()
                await ws.send_json({
                    "type": "screenshot",
                    "screenshot": shot,
                    "url": state.get("url", ""),
                    "title": state.get("title", ""),
                })
    except asyncio.CancelledError:
        return
    except Exception:
        return


async def _handle_client_message(
    data: dict,
    ws: WebSocket,
    agent: BrowserAgent,
    engine: BrowserEngine,
) -> None:
    """Handle a message from the client after the main task finishes."""
    msg_type = data.get("type", "")

    if msg_type == "click":
        await engine.click_coordinates(data.get("x", 0), data.get("y", 0))
        shot = await engine.screenshot()
        await ws.send_json({"type": "screenshot", "screenshot": shot})

    elif msg_type == "type":
        await engine.type_text(data.get("text", ""))
        shot = await engine.screenshot()
        await ws.send_json({"type": "screenshot", "screenshot": shot})

    elif msg_type == "message":
        # Follow-up task from user
        global _current_task, _current_plan
        _current_task = data.get("text", "")
        _current_plan = await agent.plan_task(_current_task)
        async for event in agent.execute(_current_task, _current_plan):
            await ws.send_json(_event_to_dict(event))


def _event_to_dict(event: BrowserEvent) -> dict:
    """Convert BrowserEvent dataclass to JSON-safe dict."""
    d = asdict(event)
    # Drop empty screenshot to reduce payload for non-screenshot events
    if not d.get("screenshot"):
        d.pop("screenshot", None)
    return d
