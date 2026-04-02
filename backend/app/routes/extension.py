"""
Extension API routes — handles requests from the Chrome extension.

This allows the extension to send page DOM + user queries to Aria's backend,
get AI-generated actions back, and execute them in the browser.
"""

import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.agents.ollama_client import chat_completion
from app.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


class PageState(BaseModel):
    """State of the current webpage"""
    url: str
    title: str
    html: str
    forms: List[Dict[str, Any]] = []
    inputs: List[Dict[str, Any]] = []
    buttons: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    viewport: Dict[str, Any] = {}


class ExtensionTaskRequest(BaseModel):
    """Task request from extension"""
    task: str  # auto, fill_form, extract, navigate, etc.
    query: str  # User's natural language query
    page: PageState


class BrowserAction(BaseModel):
    """Action to execute in browser"""
    type: str  # click, type, select, scroll, navigate, wait, extract
    selector: str | None = None
    target: str | None = None
    text: str | None = None
    value: str | None = None
    url: str | None = None
    direction: str | None = None
    amount: int | None = None
    ms: int | None = None


@router.post("/task")
async def execute_extension_task(req: ExtensionTaskRequest):
    """
    Main entry point for extension tasks.
    
    Extension sends page DOM + user query → AI determines actions → returns action list
    """
    log.info(f"Extension task: {req.task} - '{req.query}' on {req.page.url}")
    
    try:
        # Build context for AI
        context = build_page_context(req.page)
        
        # Create AI prompt
        prompt = f"""You are Aria, an AI assistant that helps users automate web tasks.

USER REQUEST: {req.query}

CURRENT PAGE:
- URL: {req.page.url}
- Title: {req.page.title}

AVAILABLE INPUTS:
{format_inputs(req.page.inputs[:10])}

AVAILABLE BUTTONS:
{format_buttons(req.page.buttons[:10])}

AVAILABLE LINKS:
{format_links(req.page.links[:5])}

TASK: Generate a sequence of browser actions to fulfill the user's request.

AVAILABLE ACTIONS:
- click: {{type: "click", selector: "#element-id"}}
- type: {{type: "type", selector: "#input-id", text: "value to type"}}
- select: {{type: "select", selector: "#select-id", value: "option value"}}
- scroll: {{type: "scroll", direction: "down|up", amount: 500}}
- navigate: {{type: "navigate", url: "https://example.com"}}
- wait: {{type: "wait", ms: 1000}}
- extract: {{type: "extract"}}

Respond with a JSON array of actions. If the task is to extract data, end with an extract action.
If the user needs to login, guide them through it but don't try to fill passwords.

Example for "check my email":
[
  {{"type": "click", "selector": "a[href*='mail']"}},
  {{"type": "wait", "ms": 2000}},
  {{"type": "extract"}}
]

Generate actions array (JSON only, no explanation):"""

        # Get AI response
        response_dict = await chat_completion(
            model=settings.MODEL_REASONING,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        response = response_dict.get("message", {}).get("content", "")
        
        # Parse actions from response
        actions = parse_actions_from_response(response)
        
        # Build response message
        message = generate_response_message(req.query, actions)
        
        return {
            "success": True,
            "message": message,
            "actions": actions,
            "data": None
        }
        
    except Exception as e:
        log.error(f"Extension task failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def build_page_context(page: PageState) -> str:
    """Build a concise context string from page state"""
    parts = [
        f"URL: {page.url}",
        f"Title: {page.title}",
        f"Inputs: {len(page.inputs)}",
        f"Buttons: {len(page.buttons)}",
        f"Links: {len(page.links)}"
    ]
    return " | ".join(parts)


def format_inputs(inputs: List[Dict]) -> str:
    """Format inputs for prompt"""
    if not inputs:
        return "(none)"
    
    lines = []
    for i, inp in enumerate(inputs[:10], 1):
        label = inp.get('label') or inp.get('placeholder') or inp.get('name') or 'input'
        selector = inp.get('selector', '')
        type_str = inp.get('type', 'text')
        lines.append(f"{i}. {label} ({type_str}) - {selector}")
    return "\n".join(lines)


def format_buttons(buttons: List[Dict]) -> str:
    """Format buttons for prompt"""
    if not buttons:
        return "(none)"
    
    lines = []
    for i, btn in enumerate(buttons[:10], 1):
        text = btn.get('text', 'button')[:50]
        selector = btn.get('selector', '')
        lines.append(f"{i}. \"{text}\" - {selector}")
    return "\n".join(lines)


def format_links(links: List[Dict]) -> str:
    """Format links for prompt"""
    if not links:
        return "(none)"
    
    lines = []
    for i, link in enumerate(links[:5], 1):
        text = link.get('text', '')[:50]
        href = link.get('href', '')
        lines.append(f"{i}. \"{text}\" → {href}")
    return "\n".join(lines)


def parse_actions_from_response(response: str) -> List[Dict[str, Any]]:
    """Extract JSON actions array from AI response"""
    import json
    import re
    
    # Try to find JSON array in response
    # Look for [...] pattern
    match = re.search(r'\[[\s\S]*\]', response)
    if match:
        try:
            actions = json.loads(match.group(0))
            if isinstance(actions, list):
                return actions
        except json.JSONDecodeError:
            pass
    
    # Fallback: return extract action
    return [{"type": "extract"}]


def generate_response_message(query: str, actions: List[Dict]) -> str:
    """Generate a human-readable message about what will happen"""
    if not actions:
        return "I'm not sure how to help with that on this page."
    
    if any(a.get('type') == 'navigate' for a in actions):
        return f"I'll navigate to help you with: {query}"
    elif any(a.get('type') == 'click' for a in actions):
        return f"I'll click the necessary elements to: {query}"
    elif any(a.get('type') == 'type' for a in actions):
        return f"I'll fill in the form to: {query}"
    elif all(a.get('type') == 'extract' for a in actions):
        return f"I'll extract the data for: {query}"
    else:
        return f"I'll help you with: {query}"


@router.get("/health")
async def extension_health():
    """Health check endpoint for extension"""
    return {"status": "ok", "extension_api": "ready"}
