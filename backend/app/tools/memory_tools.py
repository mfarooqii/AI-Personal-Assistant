"""
Memory tools — wrappers for the memory manager that fit the tool-calling interface.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.manager import MemoryManager


async def search(db: AsyncSession, query: str, category: Optional[str] = None) -> dict:
    results = await MemoryManager.search(db, query, limit=5, category=category)
    return {"memories": results}


async def store(
    db: AsyncSession,
    content: str,
    category: str = "fact",
    importance: float = 0.5,
) -> dict:
    entry = await MemoryManager.add(db, content, category, importance)
    return {"stored": True, "id": entry.id, "content": content}
