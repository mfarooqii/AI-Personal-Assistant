"""
Chat routes — main conversation endpoint with streaming support.
Integrates the workflow engine and layout engine for adaptive UI.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import get_db
from app.memory.models import Conversation, Message
from app.agents.router import route
from app.agents.executor import run, run_stream
from app.agents.layout_engine import classify_layout
from app.workflows import find_workflow
from app.workflows.executor import execute_workflow
from app.browser.detect import detect_browser_intent

log = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class LayoutDirective(BaseModel):
    layout: str = "chat"
    title: str = ""
    data: Optional[dict] = None


class ChatResponse(BaseModel):
    conversation_id: str
    content: str
    agent: str
    model: str
    tool_calls: Optional[list] = None
    layout: Optional[LayoutDirective] = None


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get or create conversation
    if req.conversation_id:
        convo = await db.get(Conversation, req.conversation_id)
        if not convo:
            raise HTTPException(404, "Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        await db.commit()
        await db.refresh(convo)

    # Save user message
    user_msg = Message(conversation_id=convo.id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()

    # Load conversation history
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == convo.id)
        .order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in result.scalars().all()]

    # ── Browser intent — works in both streaming and non-streaming modes ──────
    browser_intent = detect_browser_intent(req.message)
    if browser_intent:
        if req.stream:
            return _stream_browser_task(req, convo, db)
        else:
            return await _run_browser_task_sync(req, convo, db, browser_intent)

    # ── Check for matching workflow first ──
    workflow = find_workflow(req.message)

    if workflow and not req.stream:
        wf_result = await execute_workflow(workflow, req.message, history[:-1], db)

        assistant_msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content=wf_result["content"],
            model_used=wf_result.get("model", "workflow"),
            tool_calls=wf_result.get("tool_calls"),
        )
        db.add(assistant_msg)
        await db.commit()

        if len(history) <= 2:
            convo.title = req.message[:80]
            await db.commit()

        return ChatResponse(
            conversation_id=convo.id,
            content=wf_result["content"],
            agent=wf_result["agent"],
            model=wf_result.get("model", "workflow"),
            tool_calls=wf_result.get("tool_calls"),
            layout=LayoutDirective(**wf_result.get("layout", {"layout": "chat"})),
        )

    # ── Standard agent routing ────────────────────────────────────────────────
    agent = await route(req.message, history)

    if req.stream:
        async def generate():
            full_content = ""
            async for token in run_stream(agent, req.message, history[:-1], db):
                full_content += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            assistant_msg = Message(
                conversation_id=convo.id,
                role="assistant",
                content=full_content,
                model_used=agent.name,
            )
            db.add(assistant_msg)
            await db.commit()

            layout = await classify_layout(req.message, full_content, agent.name)
            yield f"data: {json.dumps({'done': True, 'agent': agent.name, 'layout': layout, 'conversation_id': str(convo.id)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # Non-streaming
    result = await run(agent, req.message, history[:-1], db)

    assistant_msg = Message(
        conversation_id=convo.id,
        role="assistant",
        content=result["content"],
        model_used=result["model"],
        tool_calls=result.get("tool_calls"),
    )
    db.add(assistant_msg)
    await db.commit()

    if len(history) <= 2:
        convo.title = req.message[:80]
        await db.commit()

    layout = await classify_layout(
        req.message,
        result["content"],
        result["agent"],
        result.get("tool_calls"),
    )

    return ChatResponse(
        conversation_id=convo.id,
        content=result["content"],
        agent=result["agent"],
        model=result["model"],
        tool_calls=result.get("tool_calls"),
        layout=LayoutDirective(**layout),
    )


# ── Browser task helpers ──────────────────────────────────────────────────────

def _stream_browser_task(req: ChatRequest, convo, db) -> StreamingResponse:
    """
    Stream a browser task via SSE.

    Events sent to the frontend:
      {"type": "browser_start", "task": "...", "conversation_id": "..."}
      {"type": "status",  "message": "Navigating to linear.app…"}
      {"type": "action",  "message": "Clicked Sign Up"}
      {"type": "done",    "message": "Task complete", "result": "..."}
      {"type": "error",   "message": "Browser task failed: ..."}
    """
    from app.browser.browseruse_agent import run_browser_task

    async def generate():
        # Immediately tell the frontend to activate the BrowserPanel
        yield f"data: {json.dumps({'type': 'browser_start', 'task': req.message, 'conversation_id': convo.id})}\n\n"

        full_result = ""
        async for event in run_browser_task(req.message):
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] == "done":
                full_result = event.get("result", "Task completed.")
            elif event["type"] == "error":
                full_result = event.get("message", "Browser task failed.")

        # Save result to conversation
        try:
            assistant_msg = Message(
                conversation_id=convo.id,
                role="assistant",
                content=full_result or "Browser task completed.",
                model_used="browser-use",
            )
            db.add(assistant_msg)
            await db.commit()

            if not convo.title:
                convo.title = req.message[:80]
                await db.commit()
        except Exception as e:
            log.error("Failed to save browser task result: %s", e)

        yield f"data: {json.dumps({'done': True, 'agent': 'browser', 'conversation_id': str(convo.id), 'layout': {'layout': 'browser', 'title': 'Browser Task'}})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


async def _run_browser_task_sync(req: ChatRequest, convo, db, browser_intent: dict) -> ChatResponse:
    """Non-streaming browser task — collects all events then returns."""
    from app.browser.browseruse_agent import run_browser_task

    result_text = f"Opening browser for: {req.message}"
    async for event in run_browser_task(req.message):
        if event["type"] == "done":
            result_text = event.get("result", "Task completed.")
            break
        if event["type"] == "error":
            result_text = event.get("message", "Browser task failed.")
            break

    assistant_msg = Message(
        conversation_id=convo.id,
        role="assistant",
        content=result_text,
        model_used="browser-use",
    )
    db.add(assistant_msg)
    await db.commit()

    if not convo.title:
        convo.title = req.message[:80]
        await db.commit()

    return ChatResponse(
        conversation_id=convo.id,
        content=result_text,
        agent="browser",
        model="browser-use",
        layout=LayoutDirective(
            layout="browser",
            title="Browser",
            data={
                "task": req.message,
                "category": browser_intent.get("category", ""),
                "provider_hint": browser_intent.get("provider_hint", ""),
            },
        ),
    )


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)
    )
    convos = result.scalars().all()
    return [
        {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in convos
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "model": m.model_used,
            "tool_calls": m.tool_calls,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]



class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class LayoutDirective(BaseModel):
    layout: str = "chat"
    title: str = ""
    data: Optional[dict] = None


class ChatResponse(BaseModel):
    conversation_id: str
    content: str
    agent: str
    model: str
    tool_calls: Optional[list] = None
    layout: Optional[LayoutDirective] = None


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get or create conversation
    if req.conversation_id:
        convo = await db.get(Conversation, req.conversation_id)
        if not convo:
            raise HTTPException(404, "Conversation not found")
    else:
        convo = Conversation()
        db.add(convo)
        await db.commit()
        await db.refresh(convo)

    # Save user message
    user_msg = Message(conversation_id=convo.id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()

    # Load conversation history
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == convo.id)
        .order_by(Message.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in result.scalars().all()]

    # ── Check for browser intent first (email, shopping, login) ──
    browser_intent = detect_browser_intent(req.message)
    if browser_intent and not req.stream:
        # Create plan using the shared browser singleton & set session state
        from app.routes.browser import _get_agent, _get_engine, set_session

        engine = _get_engine()
        agent_b = _get_agent()
        await engine.launch()
        plan = await agent_b.plan_task(req.message)
        set_session(req.message, plan)

        # Save a short assistant message explaining what's happening
        explanation = (
            f"I'll open a browser to help with this. "
            f"Heading to **{plan.get('website', 'the web')}**..."
        )
        if plan.get("needs_login"):
            explanation += " You'll need to sign in — I'll show you the page."

        assistant_msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content=explanation,
            model_used="browser-agent",
        )
        db.add(assistant_msg)
        await db.commit()

        if len(history) <= 2:
            convo.title = req.message[:80]
            await db.commit()

        return ChatResponse(
            conversation_id=convo.id,
            content=explanation,
            agent="browser",
            model="browser-agent",
            layout=LayoutDirective(
                layout="browser",
                title="Browser",
                data={
                    "task": req.message,
                    "plan": plan,
                    "category": browser_intent.get("category", ""),
                    "provider_hint": browser_intent.get("provider_hint", ""),
                },
            ),
        )

    # ── Check for matching workflow first ──
    workflow = find_workflow(req.message)

    if workflow and not req.stream:
        # Execute the full workflow pipeline
        wf_result = await execute_workflow(workflow, req.message, history[:-1], db)

        # Save assistant message
        assistant_msg = Message(
            conversation_id=convo.id,
            role="assistant",
            content=wf_result["content"],
            model_used=wf_result.get("model", "workflow"),
            tool_calls=wf_result.get("tool_calls"),
        )
        db.add(assistant_msg)
        await db.commit()

        if len(history) <= 2:
            convo.title = req.message[:80]
            await db.commit()

        return ChatResponse(
            conversation_id=convo.id,
            content=wf_result["content"],
            agent=wf_result["agent"],
            model=wf_result.get("model", "workflow"),
            tool_calls=wf_result.get("tool_calls"),
            layout=LayoutDirective(**wf_result.get("layout", {"layout": "chat"})),
        )

    # ── Standard agent routing ──
    agent = await route(req.message, history)

    if req.stream:
        async def generate():
            full_content = ""
            async for token in run_stream(agent, req.message, history[:-1], db):
                full_content += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Save assistant message
            assistant_msg = Message(
                conversation_id=convo.id,
                role="assistant",
                content=full_content,
                model_used=agent.name,
            )
            db.add(assistant_msg)
            await db.commit()

            # Classify layout for the complete response
            layout = await classify_layout(req.message, full_content, agent.name)
            yield f"data: {json.dumps({'done': True, 'agent': agent.name, 'layout': layout})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # Non-streaming
    result = await run(agent, req.message, history[:-1], db)

    # Save assistant message
    assistant_msg = Message(
        conversation_id=convo.id,
        role="assistant",
        content=result["content"],
        model_used=result["model"],
        tool_calls=result.get("tool_calls"),
    )
    db.add(assistant_msg)
    await db.commit()

    # Auto-title conversation from first message
    if len(history) <= 2:
        convo.title = req.message[:80]
        await db.commit()

    # ── Classify layout for adaptive UI ──
    layout = await classify_layout(
        req.message,
        result["content"],
        result["agent"],
        result.get("tool_calls"),
    )

    return ChatResponse(
        conversation_id=convo.id,
        content=result["content"],
        agent=result["agent"],
        model=result["model"],
        tool_calls=result.get("tool_calls"),
        layout=LayoutDirective(**layout),
    )


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)
    )
    convos = result.scalars().all()
    return [
        {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in convos
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "model": m.model_used,
            "tool_calls": m.tool_calls,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
