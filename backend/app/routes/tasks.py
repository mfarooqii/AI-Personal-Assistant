"""
Task routes — submit, monitor, and list background tasks.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.memory.database import get_db
from app.memory.models import Task
from app.scheduler.queue import task_queue

router = APIRouter()


class TaskRequest(BaseModel):
    description: str
    priority: int = 5
    scheduled_for: Optional[str] = None  # ISO datetime


@router.post("")
async def create_task(req: TaskRequest):
    scheduled = None
    if req.scheduled_for:
        scheduled = datetime.fromisoformat(req.scheduled_for)
    task_id = await task_queue.submit(req.description, priority=req.priority, scheduled_for=scheduled)
    return {"task_id": task_id, "status": "submitted"}


@router.get("/{task_id}")
async def get_task(task_id: str):
    status = await task_queue.get_status(task_id)
    if not status:
        return {"error": "Task not found"}
    return status


@router.get("")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).order_by(Task.created_at.desc()).limit(50)
    )
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "description": t.description[:100],
            "status": t.status,
            "agent": t.assigned_agent,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "scheduled_for": t.scheduled_for.isoformat() if t.scheduled_for else None,
        }
        for t in tasks
    ]
