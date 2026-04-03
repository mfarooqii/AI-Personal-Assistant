"""
Browser agent runner for Aria.

Uses the project's own BrowserAgent (patchright-backed in standalone mode,
or Electron BrowserView in desktop mode).

Streams events back as dicts so the chat SSE endpoint can forward them
to the React frontend in real time.
"""

import logging
from typing import AsyncGenerator

log = logging.getLogger(__name__)


async def run_browser_task(task: str) -> AsyncGenerator[dict, None]:
    """
    Run a browser task using Aria's BrowserAgent and stream status events.

    Yields dicts:
        {"type": "status",  "message": "Opening google.com…"}
        {"type": "action",  "message": "Clicking Search button"}
        {"type": "result",  "message": "Here's what I found.", "data": {...}}
        {"type": "done",    "message": "Task complete", "result": "..."}
        {"type": "error",   "message": "Failed: ..."}
    """
    from app.browser.engine import BrowserEngine
    from app.browser.agent import BrowserAgent
    from app.browser import electron_bridge

    engine = BrowserEngine()
    agent  = BrowserAgent(engine)

    try:
        # Show the browser panel in Electron if available
        if await electron_bridge.is_available():
            await electron_bridge.show()

        # Plan the task first
        yield {"type": "status", "message": f"Planning: {task}"}
        plan = await agent.plan_task(task)

        website = plan.get("website", "")
        yield {
            "type":    "status",
            "message": f"Opening {website}..." if website else "Opening browser...",
        }

        # Stream execution events
        async for event in agent.execute(task, plan):
            if event.type == "complete":
                result_text = event.data.get("summary") or event.message or "Task complete."
                yield {"type": "done", "message": "Task complete.", "result": result_text}
            elif event.type == "error":
                yield {"type": "error", "message": event.message}
            else:
                yield {
                    "type":    event.type,
                    "message": event.message or "",
                    "url":     getattr(event, "url", "") or "",
                }

    except Exception as e:
        log.exception("Browser task error: %s", e)
        yield {"type": "error", "message": f"Browser task failed: {e}"}
    finally:
        try:
            await engine.close()
        except Exception:
            pass


async def is_available() -> bool:
    """Always available — uses built-in BrowserAgent, no external deps."""
    return True
