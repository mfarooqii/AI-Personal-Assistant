"""
Chat routes — main conversation endpoint with streaming support.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import get_db
from app.memory.models import Conversation, Message
from app.agents.router import route
from app.agents.executor import run, run_stream

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    content: str
    agent: str
    model: str
    tool_calls: Optional[list] = None


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

    # Route to best agent
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

            yield f"data: {json.dumps({'done': True, 'agent': agent.name})}\n\n"

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

    return ChatResponse(
        conversation_id=convo.id,
        content=result["content"],
        agent=result["agent"],
        model=result["model"],
        tool_calls=result.get("tool_calls"),
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
