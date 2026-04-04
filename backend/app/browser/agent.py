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
    fill           = "fill"        # clear-then-fill a form field (preferred for inputs)
    type           = "type"        # append-style typing (use fill instead for form inputs)
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

PLANNER_PROMPT = """You are a browser task planner. Given a user request, output a MINIMAL, LITERAL execution plan.

CRITICAL RULES:
- Only include steps for what the user EXPLICITLY asked. Never add assumed or follow-up steps.
- If the user says "open X", "go to X", "visit X", or "navigate to X": the ONLY step is "Navigate to the website." Nothing else.
- If the user asks to search for something ON a site: step 1 = navigate, step 2 = search. Two steps max.
- If the user asks to login: step 1 = navigate to login page, step 2 = fill credentials, step 3 = click sign in.
- Do NOT add steps like "browse products", "check results", "read emails" unless user explicitly asked.
- extract_to_app = true ONLY when user asks to summarize/show data inside the app (emails, prices, etc.)
- extract_to_app = false for everything else (just show the live browser)

Output JSON only:
{{
  "website": "https://...",
  "needs_login": false,
  "login_url": "",
  "navigation_only": true/false,
  "plan": ["step 1", "step 2"],
  "extract_to_app": false,
  "reasoning": "one line"
}}

navigation_only = true when user ONLY wants to open/visit a URL (no further actions needed).
"""

NAVIGATOR_PROMPT = """You are a precise browser automation agent. You execute ONE action at a time.

Overall task: {task}
Current step goal: {plan_step}

Page info:
  URL:   {url}
  Title: {title}

Form fields on this page (check current_value BEFORE filling):
{forms}

Interactive elements on screen:
{elements}

Visible text (truncated):
{page_text}

Actions already taken this session:
{action_history}

STRICT RULES:
1. Do ONLY what the current step says. Do NOT anticipate future steps or do extra work.
2. Use "fill" (NOT "type") for ALL input/textarea fields - fill clears first then sets the value.
3. BEFORE filling any field, check its current_value. If it already matches what you need, SKIP IT and click the submit/next button instead.
4. For multi-step forms (e.g. Google: email -> Next -> password -> Sign In), ONE action per turn.
5. If the same action appears in action history already completed, DO NOT repeat it - move to next step.
6. If stuck (same action 2+ times in a row), use "wait_for_user".
7. If the current step is COMPLETE (e.g., you just navigated and step says "navigate"), output action "done".
8. If the task only requires navigation and the page loaded successfully, output action "done" immediately.
9. Only use "wait_for_user" if you genuinely need the user to do something (CAPTCHA, missing credentials).

Output the SINGLE next action as JSON only:
{{
  "thought": "what I see, what's done, why I'm doing this next",
  "action": "navigate|click|fill|press_key|scroll|extract|wait_for_user|done|back",
  "element_id": <int or null>,
  "text": "<text to fill, or URL for navigate>",
  "key": "<key for press_key: Enter, Tab, Escape, etc.>",
  "direction": "<up or down for scroll>",
  "extracted_data": {{}}
}}

ONLY output valid JSON. No markdown, no text outside the JSON.
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
        self._max_actions = 30     # safety cap
        self._last_actions: list[str] = []   # for loop detection

    async def plan_task(self, user_message: str) -> dict:
        """
        Ask the AI to create a browsing plan from the user's request.
        Returns a plan dict with website, steps, login info.
        """
        fallback = {
            "website": "",
            "needs_login": False,
            "navigation_only": False,
            "plan": [user_message],
            "extract_to_app": False,
            "reasoning": "Could not parse plan, using direct approach",
        }
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
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return fallback
            # Ensure required keys exist and are valid types
            if not isinstance(parsed.get("plan"), list) or not parsed["plan"]:
                parsed["plan"] = [user_message]
            if not isinstance(parsed.get("website"), str):
                parsed["website"] = ""
            parsed.setdefault("needs_login", False)
            parsed.setdefault("navigation_only", False)
            parsed.setdefault("extract_to_app", False)
            return parsed
        except Exception as e:
            log.warning("Plan parsing failed: %s", e)
            return fallback

    async def execute(
        self,
        task: str,
        plan: dict,
    ) -> AsyncGenerator[BrowserEvent, None]:
        """
        Execute a browsing task step by step, yielding events.
        """
        await self.engine.launch()
        self._action_history = []
        website = plan.get("website", "")
        steps = plan.get("plan", [task])
        extract_to_app = plan.get("extract_to_app", False)
        navigation_only = plan.get("navigation_only", False)

        # ── Step 1: Navigate to target website ────────────
        if website:
            yield BrowserEvent(type="status", message=f"Opening {website}...")
            nav = await self.engine.navigate(website)
            yield BrowserEvent(
                type="status",
                message=f"Loaded: {nav.get('title', nav.get('url', website))}",
                url=nav["url"],
                title=nav["title"],
            )

        # ── Navigation-only fast path ──────────────────────
        # If the plan is just "open this URL", stop here — don't run the AI loop
        if navigation_only or (len(steps) == 1 and _is_navigation_step(steps[0])):
            state = await self.engine.get_page_state()
            yield BrowserEvent(
                type="complete",
                message=f"Opened {state.get('title', website)}.",
                url=state.get("url", ""),
                title=state.get("title", ""),
                data={"summary": f"Navigated to {state.get('url', website)}"},
            )
            return

        # ── Step 2: Check if login is required ────────────
        if plan.get("needs_login"):
            state = await self.engine.get_page_state()
            if _looks_like_login(state):
                yield BrowserEvent(
                    type="interactive",
                    message="Please sign in. I'll wait here and continue once you're logged in.",
                    url=state["url"],
                    title=state["title"],
                )
                return

        # ── Step 3: Execute plan steps ────────────────────
        task_complete = False

        for step_idx, step in enumerate(steps):
            yield BrowserEvent(
                type="status",
                message=f"Step {step_idx + 1}/{len(steps)}: {step}",
                actions_taken=step_idx,
                total_actions=len(steps),
            )

            self._last_actions = []

            for action_num in range(self._max_actions):
                state = await self.engine.get_page_state()
                forms = await self.engine.analyze_forms()
                action = await self._decide_action(task, step, state, forms)

                # ── Loop detection ──
                action_sig = f"{action.kind.value}:{action.element_id}:{action.text[:30]}"
                self._last_actions.append(action_sig)
                if len(self._last_actions) >= 3 and len(set(self._last_actions[-3:])) == 1:
                    log.warning("Loop detected, breaking: %s", action_sig)
                    yield BrowserEvent(
                        type="interactive",
                        message="I seem to be stuck. Could you check the page and tell me what to do next?",
                        url=state["url"],
                        title=state["title"],
                    )
                    return

                if action.kind == ActionKind.done:
                    task_complete = True
                    break

                if action.kind == ActionKind.wait_for_user:
                    yield BrowserEvent(
                        type="interactive",
                        message=action.thought or "I need you to do something on this page.",
                        url=state["url"],
                        title=state["title"],
                    )
                    return

                if action.kind == ActionKind.extract:
                    extracted = await self._extract_data(task, state)
                    yield BrowserEvent(
                        type="result",
                        message="Here's what I found.",
                        data=extracted,
                        url=state["url"],
                        title=state["title"],
                    )
                    yield BrowserEvent(type="complete", message="Task complete.", data=extracted)
                    return

                yield BrowserEvent(
                    type="action",
                    message=action.thought,
                    url=state["url"],
                )
                await self._run_action(action)
                self._action_history.append(f"[{action.kind.value}] {action.thought}")
                await asyncio.sleep(0.8)

            if task_complete:
                break  # exit the steps loop too

        # ── Final outcome ──────────────────────────────────
        state = await self.engine.get_page_state()

        if extract_to_app and not task_complete:
            # User asked us to summarize/extract data into the app
            extracted = await self._extract_data(task, state)
            yield BrowserEvent(
                type="result",
                message="Here's what I found.",
                data=extracted,
                url=state["url"],
                title=state["title"],
            )
            yield BrowserEvent(type="complete", message="Task complete.", data=extracted)
        else:
            # Just show the browser — task is done, page is visible
            yield BrowserEvent(
                type="complete",
                message="Done." if task_complete else f"Finished on: {state.get('title', '')}",
                url=state.get("url", ""),
                title=state.get("title", ""),
                data={"summary": f"Task completed. Browser is showing: {state.get('url', '')}"},
            )

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

    async def _decide_action(self, task: str, step: str, state: dict, forms: list[dict] | None = None) -> BrowserAction:
        """Ask the AI what to do next given the current page state."""
        elements_text = _format_elements(state.get("elements", []))
        history_text = "\n".join(self._action_history[-10:]) or "(none yet)"
        forms_text = _format_forms(forms or [])

        prompt = NAVIGATOR_PROMPT.format(
            task=task,
            plan_step=step,
            url=state.get("url", ""),
            title=state.get("title", ""),
            forms=forms_text,
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
        elif action.kind == ActionKind.fill:
            # Preferred for form inputs — clears field first then fills
            if action.element_id:
                await self.engine.fill_field(action.element_id, action.text)
            else:
                await self.engine.type_text(action.text)
        elif action.kind == ActionKind.type:
            # Legacy append-style typing — redirects to fill_field if element_id given
            if action.element_id:
                await self.engine.fill_field(action.element_id, action.text)
            else:
                await self.engine.type_text(action.text)
        elif action.kind == ActionKind.press_key:
            await self.engine.press_key(action.key or "Enter")
        elif action.kind == ActionKind.scroll:
            await self.engine.scroll(action.direction)
        elif action.kind == ActionKind.back:
            await self.engine.go_back()


# ── Utilities ─────────────────────────────────────────────

def _format_forms(forms: list[dict]) -> str:
    """Format form structure for the AI prompt."""
    if not forms:
        return "(no forms detected on this page)"
    lines = []
    for form in forms:
        fields = form.get("fields", [])
        submit = form.get("submit_button_text", "Submit")
        lines.append(f"Form (submit: \"{submit}\"):")
        for f in fields:
            label = f.get("label") or f.get("placeholder") or f.get("name") or "?"
            ftype = f.get("type", "text")
            val = f.get("current_value", "")
            req = " [required]" if f.get("required") else ""
            val_str = f' current_value="{val}"' if val else " (empty)"
            lines.append(f"  - {label} ({ftype}){req}{val_str}")
    return "\n".join(lines)


def _format_elements(elements: list[dict]) -> str:
    """Format numbered element list for the AI prompt."""
    if not elements:
        return "(no interactive elements found)"
    lines = []
    for el in elements[:60]:  # cap to keep prompt small
        tag = el.get("tag", "?")
        role = el.get("role", tag)
        parts = [f"[{el['id']}]", role]
        # Label takes priority for inputs
        label = el.get("label", "")
        text = el.get("text", "")
        display = label or text
        if display:
            parts.append(f'"{display}"')
        ph = el.get("placeholder", "")
        if ph and not label:
            parts.append(f'placeholder="{ph}"')
        val = el.get("value", "")
        if val and tag in ("input", "textarea", "select"):
            parts.append(f'value="{val}"')   # show current value clearly
        if el.get("disabled"):
            parts.append("(disabled)")
        if el.get("required"):
            parts.append("(required)")
        if el.get("href"):
            parts.append(f'→ {el["href"][:80]}')
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _is_navigation_step(step: str) -> bool:
    """True when a plan step is only a navigation action (no interaction needed)."""
    step_lower = step.lower()
    nav_phrases = ["navigate to", "go to", "open ", "visit ", "load "]
    action_phrases = ["click", "fill", "type", "search", "login", "sign in", "submit", "scroll", "find", "look for"]
    has_nav = any(step_lower.startswith(p) or f" {p}" in step_lower for p in nav_phrases)
    has_action = any(p in step_lower for p in action_phrases)
    return has_nav and not has_action


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
