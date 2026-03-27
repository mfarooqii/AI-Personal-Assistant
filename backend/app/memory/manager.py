"""
Memory manager — stores, retrieves, and searches the user's long-term memory.
Uses embedding-based semantic search to find relevant context for each conversation.
"""

import numpy as np
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import MemoryEntry
from app.agents.ollama_client import get_embedding


class MemoryManager:
    """Handles read/write to long-term memory with semantic search."""

    @staticmethod
    async def add(
        db: AsyncSession,
        content: str,
        category: str = "fact",
        importance: float = 0.5,
        source: str = "conversation",
    ) -> MemoryEntry:
        embedding = await get_embedding(content)
        entry = MemoryEntry(
            content=content,
            category=category,
            importance=importance,
            source=source,
            embedding=embedding,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def search(
        db: AsyncSession,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Semantic search over memory entries. Returns top-k relevant memories."""
        query_embedding = await get_embedding(query)
        if query_embedding is None:
            return []

        stmt = select(MemoryEntry)
        if category:
            stmt = stmt.where(MemoryEntry.category == category)
        result = await db.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            return []

        # Cosine similarity ranking
        q_vec = np.array(query_embedding)
        scored = []
        for entry in entries:
            if entry.embedding is None:
                continue
            e_vec = np.array(entry.embedding)
            similarity = float(np.dot(q_vec, e_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(e_vec) + 1e-10))
            # Boost by importance
            score = similarity * 0.8 + entry.importance * 0.2
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        # Update last_accessed
        for _, entry in top:
            await db.execute(
                update(MemoryEntry)
                .where(MemoryEntry.id == entry.id)
                .values(last_accessed=datetime.utcnow())
            )
        await db.commit()

        return [
            {"id": e.id, "content": e.content, "category": e.category, "score": round(s, 3)}
            for s, e in top
        ]

    @staticmethod
    async def get_all(db: AsyncSession, category: Optional[str] = None) -> list[MemoryEntry]:
        stmt = select(MemoryEntry).order_by(MemoryEntry.created_at.desc())
        if category:
            stmt = stmt.where(MemoryEntry.category == category)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, memory_id: str) -> bool:
        entry = await db.get(MemoryEntry, memory_id)
        if entry:
            await db.delete(entry)
            await db.commit()
            return True
        return False
