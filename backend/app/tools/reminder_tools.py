"""
Reminder tool — creates scheduled reminders in the database.
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.memory.models import Reminder


async def create(
    db: AsyncSession,
    message: str,
    trigger_at: str,
    recurring: Optional[str] = None,
) -> dict:
    """Create a new reminder."""
    try:
        dt = datetime.fromisoformat(trigger_at)
    except ValueError:
        return {"error": f"Invalid datetime format: {trigger_at}. Use ISO format like '2026-03-27T15:00:00'"}

    reminder = Reminder(
        message=message,
        trigger_at=dt,
        recurring=recurring,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    return {
        "created": True,
        "id": reminder.id,
        "message": message,
        "trigger_at": dt.isoformat(),
        "recurring": recurring,
    }
