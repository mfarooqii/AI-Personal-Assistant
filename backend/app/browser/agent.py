"""
Browser Agent — AI-driven navigation and data extraction.

This is the "brain" that sits on top of BrowserEngine and decides what to
click, type, scroll, or extract at each step.  It works in a loop:

    1.  Observe  →  get page state (interactive elements + text)
    2.  Think    →  send state + task to the local AI model
    3.  Act      →  execute the action the model chose
    4.  Repeat until the task is done or user intervention is needed

The agent uses the accessibility-tree approach (numbered element map) so
any 7 B text model can drive it — no vision model required.
"""

import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, AsyncGenerator
from enum import Enum

from app.agents.ollama_client import chat_completion
from app.config import settings
from app.browser.engine import BrowserEngine

log = logging.getLogger(__name__)

# Model used for browser reasoning — defaults to the reasoning model
BROWSER_MODEL = getattr(settings, "MODEL_BROWSER", None) or settings.MODEL_REASONING


# ── Data types ────────────────────────────────────────────

class ActionKind(str, Enum):
    navigate       = "navigate"
    click          = "click"
    type           = "type"
    press_key      = "press_key"
    scroll         = "scroll"
    extract        = "extract"
    wait_for_user  = "wait_for_user"
    done           = "done"
    back           = "back"


@dataclass
class BrowserAction:
    kind: ActionKind
    thought: str = ""
    element_id: Optional[int] = None
    text: str = ""
    key: str = ""
    direction: str = "down"
    extracted_data: dict = field(default_factory=dict)
    url: str = ""


@dataclass
class BrowserEvent:
    """Streamed to frontend via WebSocket."""
    type: str           # screenshot | status | action | interactive | result | complete | error
    message: str = ""
    screenshot: str = ""     # base64
    url: str = ""
    title: str = ""
    data: dict = field(default_factory=dict)
    actions_taken: int = 0
    total_actions: int = 0


# Websites where we show the actual page to the user rather than
# extracting data into our own layout.
SHOW_ON_SITE = {"amazon.com", "ebay.com", "walmart.com", "etsy.com"}


# ── Prompts ───────────────────────────────────────────────

PLANNER_PROMPT = """You are an AI task planner for a browser automation agent.
Given a user's request, determine:
1. Which website to visit
2. Whether the user is likely already signed in or needs to sign in
3. Step-by-step plan to accomplish the task

Output JSON only:
{{
  "website": "https://...",
  "needs_login": true/false,
  "login_url": "https://... (only if needs_login is true)",
  "plan": ["step 1", "step 2", ...],
  "extract_to_app": true/false,
  "reasoning": "brief explanation"
}}

Rules:
- For email: use gmail.com, outlook.live.com, or mail.yahoo.com
- For shopping: use amazon.com directly
- extract_to_app = true for emails (we summarize in our app)
- extract_to_app = false for shopping results (show on the actual site)
"""

NAVIGATOR_PROMPT = """You are a browser automation agent. You control a web browser to complete tasks for the user.

Current task: {task}
Current plan step: {plan_step}

Page info:
  URL:   {url}
  Title: {title}

Interactive elements on screen:
{elements}

Visible text (truncated):
{page_text}

History of actions taken so far:
{action_history}

Decide the SINGLE next action. Output JSON only:
{{
  "thought": "brief reasoning about what you see and what to do",
  "action": "navigate|click|type|press_key|scroll|extract|wait_for_user|done|back",
  "element_id": <int or null — which numbered element to interact with>,
  "text": "<text to type, or URL for navigate>",
  "key": "<key name for press_key: Enter, Tab, etc.>",
  "direction": "<up or down for scroll>",
  "extracted_data": {{}}
}}

Rules:
- If you see a login/sign-in page and user hasn't logged in yet, choose "wait_for_user" and explain what they need to do.
- For search bars, first click the element, then type the query, then press Enter.
- Use "extract" when you've reached the target data and want to pull it out.
- Use "done" when the task is completely finished.
- Use "scroll" to see more content below the fold.
- Use "back" to go to previous page if you took a wrong turn.
- When extracting email data, include: subject, from, date, snippet for each email.
- When extracting product data, include: name, price, rating, reviews, url for each product.
- ONLY output valid JSON. No markdown, no explanation outside the JSON.
"""

EXTRACTOR_PROMPT = """You are a data extraction agent. Extract structured data from this webpage content.

Task: {task}
URL: {url}

Page text:
{page_text}

Extract the relevant data as JSON. The format depends on the task:

For emails:
{{
  "emails": [
    {{"subject": "...", "from": "...", "date": "...", "snippet": "...", "is_unread": true/false, "importance": "high|normal|low"}}
  ],
  "summary": "Brief summary of what you found"
}}

For products/shopping:
{{
  "products": [
    {{"name": "...", "price": "...", "rating": 4.5, "reviews": 150, "url": "...", "image": "..."}}
  ],
  "summary": "Brief summary of search results"
}}

For general content:
{{
  "content": "extracted text",
  "summary": "brief summary"
}}

Output ONLY valid JSON.
"""


class BrowserAgent:
    """
    High-level agent that plans and executes browser tasks.

    Yields BrowserEvent objects so callers (WebSocket route) can
    stream progress to the frontend in real time.
    """

    def __init__(self, engine: BrowserEngine) -> None:
        self.engine = engine
        self._action_history: list[str] = []
        self._max_actions = 25     # safety cap

    async def plan_task(self, user_message: str) -> dict:
        """
        Ask the AI to create a browsing plan from the user's request.
        Returns a plan dict with website, steps, login info.
        """
        try:
            resp = await chat_completion(
                model=BROWSER_MODEL,
                messages=[
                    {"role": "system", "content": PLANNER_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
            )
            content = resp.get("message", {}).get("content", "")
            content = _clean_json(content)
            return json.loads(content)
        except Exception as e:
            log.warning("Plan parsing failed: %s", e)
            return {
                "website": "",
                "needs_login": False,
                "plan": [user_message],
                "extract_to_app": True,
                "reasoning": "Could not parse plan, using direct approach",
            }

    async def execute(
        self,
        task: str,
        plan: dict,
    ) -> AsyncGenerator[BrowserEvent, None]:
        """
        Execute a browsing task step by step, yielding events.

        This is the main loop the WebSocket route iterates over::

            async for event in agent.execute(task, plan):
                await ws.send_json(asdict(event))
        """
        await self.engine.launch()
        self._action_history = []
        website = plan.get("website", "")
        steps = plan.get("plan", [task])
        extract_to_app = plan.get("extract_to_app", True)

        # ── Step 1: Navigate to target website ────────────
        if website:
            yield BrowserEvent(type="status", message=f"Opening {website}...")
            nav = await self.engine.navigate(website)
            yield BrowserEvent(
                type="screenshot",
                screenshot=await self.engine.screenshot(),
                url=nav["url"],
                title=nav["title"],
            )

        # ── Step 2: Check if login is required ────────────
        if plan.get("needs_login"):
            state = await self.engine.get_page_state()
            if _looks_like_login(state):
                yield BrowserEvent(
                    type="interactive",
                    message="Please sign in. I'll wait here and continue once you're logged in.",
                    screenshot=await self.engine.screenshot(),
                    url=state["url"],
                    title=state["title"],
                )
                # The execute loop pauses here — the WebSocket route
                # resumes after the user signals they're done logging in.
                return

        # ── Step 3: Execute plan steps ────────────────────
        for step_idx, step in enumerate(steps):
            yield BrowserEvent(
                type="status",
                message=f"Step {step_idx + 1}/{len(steps)}: {step}",
                actions_taken=step_idx,
                total_actions=len(steps),
            )

            # Inner action loop for this step
            for action_num in range(self._max_actions):
                state = await self.engine.get_page_state()
                action = await self._decide_action(task, step, state)

                if action.kind == ActionKind.done:
                    break

                if action.kind == ActionKind.wait_for_user:
                    yield BrowserEvent(
                        type="interactive",
                        message=action.thought or "I need you to do something on this page.",
                        screenshot=await self.engine.screenshot(),
                        url=state["url"],
                        title=state["title"],
                    )
                    return  # pause — frontend will resume

                if action.kind == ActionKind.extract:
                    extracted = await self._extract_data(task, state)
                    yield BrowserEvent(
                        type="result",
                        message="Here's what I found.",
                        screenshot=await self.engine.screenshot(),
                        data=extracted,
                        url=state["url"],
                        title=state["title"],
                    )
                    yield BrowserEvent(type="complete", message="Task complete.", data=extracted)
                    return

                # Execute the action
                yield BrowserEvent(
                    type="action",
                    message=action.thought,
                    screenshot=await self.engine.screenshot(),
                    url=state["url"],
                )
                await self._run_action(action)
                self._action_history.append(
                    f"[{action.kind.value}] {action.thought}"
                )

                # After some actions, give a short pause for page to settle
                await asyncio.sleep(0.5)

        # If we get here without an explicit extract/done, do a final extraction
        state = await self.engine.get_page_state()
        extracted = await self._extract_data(task, state)
        yield BrowserEvent(
            type="result",
            message="Here's what I found.",
            screenshot=await self.engine.screenshot(),
            data=extracted,
            url=state["url"],
            title=state["title"],
        )
        yield BrowserEvent(type="complete", message="Task complete.", data=extracted)

    async def continue_after_login(self, task: str, plan: dict) -> AsyncGenerator[BrowserEvent, None]:
        """
        Resume execution after the user has finished signing in.
        Takes a new screenshot, verifies login succeeded, then
        continues the normal execution flow.
        """
        await asyncio.sleep(1)  # give page a moment
        state = await self.engine.get_page_state()

        if _looks_like_login(state):
            yield BrowserEvent(
                type="interactive",
                message="It looks like you're still on the login page. Please complete sign-in.",
                screenshot=await self.engine.screenshot(),
                url=state["url"],
                title=state["title"],
            )
            return

        yield BrowserEvent(
            type="status",
            message="Sign-in successful! Continuing task...",
            screenshot=await self.engine.screenshot(),
            url=state["url"],
            title=state["title"],
        )

        # Re-run execute with login flag disabled
        plan_no_login = {**plan, "needs_login": False}
        async for event in self.execute(task, plan_no_login):
            yield event

    # ── private helpers ──────────────────────────────────

    async def _decide_action(self, task: str, step: str, state: dict) -> BrowserAction:
        """Ask the AI what to do next given the current page state."""
        elements_text = _format_elements(state.get("elements", []))
        history_text = "\n".join(self._action_history[-8:]) or "(none yet)"

        prompt = NAVIGATOR_PROMPT.format(
            task=task,
            plan_step=step,
            url=state.get("url", ""),
            title=state.get("title", ""),
            elements=elements_text,
            page_text=state.get("text", "")[:3000],
            action_history=history_text,
        )

        try:
            resp = await chat_completion(
                model=BROWSER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a browser automation agent. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = resp.get("message", {}).get("content", "")
            content = _clean_json(content)
            data = json.loads(content)

            return BrowserAction(
                kind=ActionKind(data.get("action", "done")),
                thought=data.get("thought", ""),
                element_id=data.get("element_id"),
                text=data.get("text", ""),
                key=data.get("key", ""),
                direction=data.get("direction", "down"),
                extracted_data=data.get("extracted_data", {}),
                url=data.get("url", ""),
            )
        except Exception as e:
            log.warning("Action parsing failed: %s", e)
            return BrowserAction(kind=ActionKind.done, thought=f"Error deciding action: {e}")

    async def _extract_data(self, task: str, state: dict) -> dict:
        """Use the AI to extract structured data from the current page."""
        prompt = EXTRACTOR_PROMPT.format(
            task=task,
            url=state.get("url", ""),
            page_text=state.get("text", "")[:6000],
        )

        try:
            resp = await chat_completion(
                model=BROWSER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a data extraction agent. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = resp.get("message", {}).get("content", "")
            content = _clean_json(content)
            return json.loads(content)
        except Exception as e:
            log.warning("Extraction failed: %s", e)
            return {"summary": state.get("text", "")[:2000], "error": str(e)}

    async def _run_action(self, action: BrowserAction) -> None:
        """Execute a single browser action."""
        if action.kind == ActionKind.navigate:
            await self.engine.navigate(action.text or action.url)
        elif action.kind == ActionKind.click:
            if action.element_id:
                await self.engine.click_element(action.element_id)
        elif action.kind == ActionKind.type:
            await self.engine.type_text(action.text, action.element_id)
        elif action.kind == ActionKind.press_key:
            await self.engine.press_key(action.key or "Enter")
        elif action.kind == ActionKind.scroll:
            await self.engine.scroll(action.direction)
        elif action.kind == ActionKind.back:
            await self.engine.go_back()


# ── Utilities ─────────────────────────────────────────────

def _format_elements(elements: list[dict]) -> str:
    """Format numbered element list for the AI prompt."""
    if not elements:
        return "(no interactive elements found)"
    lines = []
    for el in elements[:60]:  # cap to keep prompt small
        parts = [f"[{el['id']}]", el.get("role", el.get("tag", "?"))]
        text = el.get("text", "")
        if text:
            parts.append(f'"{text}"')
        ph = el.get("placeholder", "")
        if ph:
            parts.append(f'placeholder="{ph}"')
        if el.get("disabled"):
            parts.append("(disabled)")
        if el.get("href"):
            parts.append(f'→ {el["href"][:80]}')
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _looks_like_login(state: dict) -> bool:
    """Heuristic: does the page look like a sign-in form?"""
    text = (state.get("text", "") + state.get("title", "")).lower()
    url = state.get("url", "").lower()
    signals = ["sign in", "log in", "login", "signin", "password",
               "accounts.google.com", "login.live.com", "login.yahoo.com",
               "ap/signin"]
    return any(s in text or s in url for s in signals)


def _clean_json(text: str) -> str:
    """Strip markdown fences and whitespace from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return text.strip()
