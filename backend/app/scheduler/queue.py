"""
Task queue — manages background execution of multi-step tasks.
"""

import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import async_session
from app.memory.models import Task, Conversation
from app.agents.router import route
from app.agents.executor import run
from app.config import settings


class TaskQueue:
    def __init__(self):
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

    async def submit(
        self,
        description: str,
        conversation_id: Optional[str] = None,
        priority: int = 5,
        scheduled_for: Optional[datetime] = None,
    ) -> str:
        """Submit a new task. Returns task ID."""
        async with async_session() as db:
            task = Task(
                description=description,
                conversation_id=conversation_id,
                priority=priority,
                scheduled_for=scheduled_for,
                status="pending" if scheduled_for else "queued",
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            if not scheduled_for:
                # Execute immediately in background
                asyncio.create_task(self._execute(task.id))

            return task.id

    async def _execute(self, task_id: str):
        """Execute a task — route to best agent and run."""
        async with self._semaphore:
            async with async_session() as db:
                task = await db.get(Task, task_id)
                if not task or task.status not in ("queued", "pending"):
                    return

                # Mark running
                task.status = "running"
                task.started_at = datetime.utcnow()
                await db.commit()

                try:
                    # Route to best agent
                    agent = await route(task.description)
                    task.assigned_agent = agent.name

                    # Execute
                    result = await run(agent, task.description, [], db)

                    task.status = "completed"
                    task.result = result
                    task.tools_used = [tc["tool"] for tc in (result.get("tool_calls") or [])]
                    task.completed_at = datetime.utcnow()

                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                    task.completed_at = datetime.utcnow()

                await db.commit()

    async def get_status(self, task_id: str) -> Optional[dict]:
        async with async_session() as db:
            task = await db.get(Task, task_id)
            if not task:
                return None
            return {
                "id": task.id,
                "status": task.status,
                "description": task.description,
                "agent": task.assigned_agent,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }


task_queue = TaskQueue()
