"""
Settings routes — manage models, user profile, system info.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.memory.database import get_db
from app.memory.models import UserProfile
from app.agents.ollama_client import list_models, is_ollama_available
from app.config import settings

router = APIRouter()


@router.get("/system")
async def system_info():
    ollama_ok = await is_ollama_available()
    models = await list_models() if ollama_ok else []
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ollama_available": ollama_ok,
        "installed_models": [m.get("name", "") for m in models],
        "configured_models": {
            "chat": settings.MODEL_CHAT,
            "reasoning": settings.MODEL_REASONING,
            "code": settings.MODEL_CODE,
            "vision": settings.MODEL_VISION,
            "embedding": settings.MODEL_EMBEDDING,
            "small": settings.MODEL_SMALL,
        },
    }


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[dict] = None
    monthly_budget: Optional[dict] = None
    health_profile: Optional[dict] = None


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"exists": False}
    return {
        "exists": True,
        "name": profile.name,
        "location": profile.location,
        "timezone": profile.timezone,
        "preferences": profile.preferences,
        "monthly_budget": profile.monthly_budget,
        "health_profile": profile.health_profile,
    }


@router.put("/profile")
async def update_profile(req: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    if req.name is not None:
        profile.name = req.name
    if req.location is not None:
        profile.location = req.location
    if req.timezone is not None:
        profile.timezone = req.timezone
    if req.preferences is not None:
        profile.preferences = req.preferences
    if req.monthly_budget is not None:
        profile.monthly_budget = req.monthly_budget
    if req.health_profile is not None:
        profile.health_profile = req.health_profile

    await db.commit()
    return {"updated": True}
