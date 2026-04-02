"""
Database models for persistent memory, conversations, tasks, and user profile.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Boolean, Integer, JSON, ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.memory.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


# ── Conversations ────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=new_id)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=new_id)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant | system | tool
    content = Column(Text, nullable=False)
    model_used = Column(String, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ── Long-Term Memory ────────────────────────────────────

class MemoryEntry(Base):
    """
    Stores important facts, preferences, and context the assistant learns
    about the user over time. Embeddings enable semantic search.
    """
    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True, default=new_id)
    category = Column(String, nullable=False)             # preference | fact | event | person | finance
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)               # stored as list[float]
    importance = Column(Float, default=0.5)               # 0-1, for retrieval ranking
    source = Column(String, default="conversation")       # conversation | manual | tool
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_memory_category", "category"),)


# ── Tasks ────────────────────────────────────────────────

class Task(Base):
    """
    Queued tasks that the assistant plans, routes to agents, and executes.
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=new_id)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")            # pending | running | completed | failed
    priority = Column(Integer, default=5)                 # 1 (highest) – 10 (lowest)
    assigned_agent = Column(String, nullable=True)
    tools_used = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)       # for deferred / scheduled tasks


# ── User Profile ─────────────────────────────────────────

class UserProfile(Base):
    """
    Stores user preferences, budget info, personal details the user shares.
    Single-row table (one user per instance).
    """
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, default=1)
    name = Column(String, nullable=True)
    profession = Column(String, nullable=True)             # "doctor", "student", "engineer", etc.
    priorities = Column(JSON, default=list)                 # ["email", "calendar", "news", "tasks"]
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)
    preferences = Column(JSON, default=dict)              # {theme, language, voice_speed, …}
    monthly_budget = Column(JSON, nullable=True)           # {income, categories: {food, rent, …}}
    health_profile = Column(JSON, nullable=True)           # {dietary_restrictions, allergies, …}
    location = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Reminders ────────────────────────────────────────────

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=new_id)
    message = Column(Text, nullable=False)
    trigger_at = Column(DateTime, nullable=False)
    recurring = Column(String, nullable=True)              # daily | weekly | monthly | cron:...
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
