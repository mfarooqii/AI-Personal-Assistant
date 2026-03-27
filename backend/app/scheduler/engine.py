"""
Task scheduler — handles reminders, scheduled tasks, and deferred workflows.
Runs as a background loop checking for pending tasks/reminders.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional

from sqlalchemy import select, update
from app.memory.database import async_session
from app.memory.models import Reminder, Task


class Scheduler:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: list[Callable] = []

    def on_reminder(self, callback: Callable):
        """Register a callback for when reminders trigger."""
        self._callbacks.append(callback)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self):
        """Main scheduler loop — checks every 30 seconds."""
        while self._running:
            try:
                await self._check_reminders()
                await self._check_scheduled_tasks()
            except Exception as e:
                # Log but don't crash
                print(f"[Scheduler] Error: {e}")
            await asyncio.sleep(30)

    async def _check_reminders(self):
        now = datetime.utcnow()
        async with async_session() as db:
            stmt = select(Reminder).where(
                Reminder.is_done == False,
                Reminder.trigger_at <= now,
            )
            result = await db.execute(stmt)
            due_reminders = result.scalars().all()

            for reminder in due_reminders:
                # Fire callbacks
                for cb in self._callbacks:
                    try:
                        await cb(reminder)
                    except Exception:
                        pass

                # Handle recurring
                if reminder.recurring:
                    next_trigger = self._next_occurrence(reminder.trigger_at, reminder.recurring)
                    await db.execute(
                        update(Reminder)
                        .where(Reminder.id == reminder.id)
                        .values(trigger_at=next_trigger)
                    )
                else:
                    await db.execute(
                        update(Reminder)
                        .where(Reminder.id == reminder.id)
                        .values(is_done=True)
                    )
            await db.commit()

    async def _check_scheduled_tasks(self):
        now = datetime.utcnow()
        async with async_session() as db:
            stmt = select(Task).where(
                Task.status == "pending",
                Task.scheduled_for != None,
                Task.scheduled_for <= now,
            )
            result = await db.execute(stmt)
            due_tasks = result.scalars().all()

            for task in due_tasks:
                # Mark as ready to run — the task queue will pick it up
                await db.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(status="queued", scheduled_for=None)
                )
            await db.commit()

    @staticmethod
    def _next_occurrence(current: datetime, pattern: str) -> datetime:
        if pattern == "daily":
            return current + timedelta(days=1)
        elif pattern == "weekly":
            return current + timedelta(weeks=1)
        elif pattern == "monthly":
            # Approximate
            return current + timedelta(days=30)
        return current + timedelta(days=1)


# Singleton
scheduler = Scheduler()
