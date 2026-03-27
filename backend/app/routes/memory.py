"""
Memory routes — view, search, and manage long-term memory.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import get_db
from app.memory.manager import MemoryManager

router = APIRouter()


class MemoryAddRequest(BaseModel):
    content: str
    category: str = "fact"
    importance: float = 0.5


class MemorySearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 5


@router.post("/add")
async def add_memory(req: MemoryAddRequest, db: AsyncSession = Depends(get_db)):
    entry = await MemoryManager.add(db, req.content, req.category, req.importance)
    return {"id": entry.id, "stored": True}


@router.post("/search")
async def search_memory(req: MemorySearchRequest, db: AsyncSession = Depends(get_db)):
    results = await MemoryManager.search(db, req.query, req.limit, req.category)
    return {"results": results}


@router.get("")
async def list_memories(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    entries = await MemoryManager.get_all(db, category)
    return [
        {
            "id": e.id,
            "content": e.content,
            "category": e.category,
            "importance": e.importance,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await MemoryManager.delete(db, memory_id)
    return {"deleted": deleted}
