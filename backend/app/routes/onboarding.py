"""
Onboarding routes — conversational setup wizard.

First-time users get a step-by-step conversation with Aria that builds their profile.
No settings pages. Everything happens through chat.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.memory.database import get_db
from app.memory.models import UserProfile, MemoryEntry
from app.config import settings

router = APIRouter()

# ── Onboarding Steps ─────────────────────────────────────
# Each step: (field_to_set, aria_message, placeholder_hint)

ONBOARDING_STEPS = [
    {
        "id": 0,
        "field": None,
        "message": (
            f"Hey! I'm **{settings.APP_NAME}**, your personal AI assistant. "
            "I run right here on your computer — your data never leaves this machine.\n\n"
            "Let me get to know you so I can be actually useful. This will only take a minute.\n\n"
            "**What's your name?**"
        ),
        "placeholder": "Type your name...",
        "type": "text",
    },
    {
        "id": 1,
        "field": "name",
        "message": "Nice to meet you, {name}! 👋\n\n**What do you do?** (your job, studies, or how you'd describe yourself)\n\nFor example: *doctor, student, software engineer, business owner, teacher, freelancer...*",
        "placeholder": "e.g. Software Engineer",
        "type": "text",
    },
    {
        "id": 2,
        "field": "profession",
        "message": "Got it — {profession}. I'll tailor my tools and suggestions for that.\n\n**What should I help you with most?** Pick everything that applies:",
        "placeholder": "",
        "type": "multi_select",
        "options": [
            {"id": "email", "label": "📧 Email & Messages", "description": "Read, write, and manage emails"},
            {"id": "calendar", "label": "📅 Schedule & Calendar", "description": "Events, reminders, planning"},
            {"id": "news", "label": "📰 News & Research", "description": "Stay updated, search the web"},
            {"id": "tasks", "label": "✅ Tasks & Projects", "description": "Track todos, manage work"},
            {"id": "finance", "label": "💰 Budget & Finance", "description": "Track spending, financial advice"},
            {"id": "writing", "label": "✍️ Writing & Docs", "description": "Draft emails, reports, content"},
            {"id": "coding", "label": "💻 Code & Technical", "description": "Write code, debug, DevOps"},
            {"id": "health", "label": "🏥 Health & Wellness", "description": "Diet, exercise, health tracking"},
            {"id": "learning", "label": "📚 Learning & Study", "description": "Study plans, flashcards, tutoring"},
            {"id": "travel", "label": "✈️ Travel & Booking", "description": "Flights, hotels, trip planning"},
        ],
    },
    {
        "id": 3,
        "field": "priorities",
        "message": "Perfect setup, {name}! Here's what I've configured for you:\n\n{summary}\n\nYou're all set. Just talk to me — I'll transform into whatever you need. Try asking me something!",
        "placeholder": "Ask me anything...",
        "type": "complete",
    },
]


def _build_summary(profile_data: dict) -> str:
    """Build a human-readable summary of the onboarding results."""
    lines = []
    if profile_data.get("name"):
        lines.append(f"- **Name:** {profile_data['name']}")
    if profile_data.get("profession"):
        lines.append(f"- **Role:** {profile_data['profession']}")
    if profile_data.get("priorities"):
        # Map IDs to labels
        label_map = {}
        for step in ONBOARDING_STEPS:
            for opt in step.get("options", []):
                label_map[opt["id"]] = opt["label"]
        prio_labels = [label_map.get(p, p) for p in profile_data["priorities"]]
        lines.append(f"- **Priorities:** {', '.join(prio_labels)}")
    return "\n".join(lines) if lines else "Everything set up!"


@router.get("/status")
async def onboarding_status(db: AsyncSession = Depends(get_db)):
    """Check if onboarding is completed and current step."""
    result = await db.execute(select(UserProfile))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"completed": False, "step": 0, "total_steps": len(ONBOARDING_STEPS)}
    return {
        "completed": profile.onboarding_completed,
        "step": profile.onboarding_step,
        "total_steps": len(ONBOARDING_STEPS),
    }


class StepResponse(BaseModel):
    answer: Optional[str] = None
    selections: Optional[list[str]] = None


@router.post("/step")
async def process_step(req: StepResponse, db: AsyncSession = Depends(get_db)):
    """Process one onboarding step and return the next."""
    result = await db.execute(select(UserProfile))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(id=1, onboarding_step=0)
        db.add(profile)
        await db.flush()

    current_step = profile.onboarding_step

    # Process the answer for the current step
    if current_step == 0:
        # First step — just showing the welcome, no answer to process yet
        pass
    elif current_step == 1:
        # User answered their name
        if req.answer:
            profile.name = req.answer.strip()
            # Store in memory too
            mem = MemoryEntry(
                category="person",
                content=f"User's name is {profile.name}",
                importance=1.0,
                source="onboarding",
            )
            db.add(mem)
    elif current_step == 2:
        # User answered their profession
        if req.answer:
            profile.profession = req.answer.strip()
            mem = MemoryEntry(
                category="fact",
                content=f"User works as a {profile.profession}",
                importance=0.9,
                source="onboarding",
            )
            db.add(mem)
    elif current_step == 3:
        # User selected priorities
        if req.selections:
            profile.priorities = req.selections
            mem = MemoryEntry(
                category="preference",
                content=f"User's top priorities: {', '.join(req.selections)}",
                importance=0.9,
                source="onboarding",
            )
            db.add(mem)

    # Advance to next step
    next_step_idx = current_step + 1 if current_step < len(ONBOARDING_STEPS) - 1 else current_step

    # If we're past the selections step, mark complete
    if current_step >= 3:
        profile.onboarding_completed = True
        profile.onboarding_step = len(ONBOARDING_STEPS) - 1
        await db.commit()

        # Build the final summary
        profile_data = {
            "name": profile.name,
            "profession": profile.profession,
            "priorities": profile.priorities or [],
        }
        summary = _build_summary(profile_data)
        step_data = ONBOARDING_STEPS[-1].copy()
        msg = step_data["message"].format(
            name=profile.name or "there",
            summary=summary,
        )
        return {
            "completed": True,
            "step": step_data,
            "message": msg,
            "profile": profile_data,
        }

    profile.onboarding_step = next_step_idx
    await db.commit()

    # Build the next step's message with profile data
    step_data = ONBOARDING_STEPS[next_step_idx].copy()
    msg = step_data["message"].format(
        name=profile.name or "there",
        profession=profile.profession or "your field",
        summary="",
    )

    return {
        "completed": False,
        "step": step_data,
        "message": msg,
    }


@router.post("/reset")
async def reset_onboarding(db: AsyncSession = Depends(get_db)):
    """Reset onboarding (dev/testing only)."""
    result = await db.execute(select(UserProfile))
    profile = result.scalar_one_or_none()
    if profile:
        profile.onboarding_completed = False
        profile.onboarding_step = 0
        await db.commit()
    return {"reset": True}
