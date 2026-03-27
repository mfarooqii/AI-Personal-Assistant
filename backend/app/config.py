"""
Central configuration for the AI Personal Assistant.
All settings can be overridden via environment variables or .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Aria"  # The assistant's name
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATA_DIR: Path = Path.home() / ".aria"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = ""  # auto-set to sqlite in DATA_DIR if empty

    # ── Ollama (local model server) ──────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    # Model assignments — users can override with whatever fits their hardware
    MODEL_CHAT: str = "llama3.2"          # general conversation
    MODEL_REASONING: str = "llama3.2"    # complex reasoning / planning (use llama3.2 for speed)
    MODEL_CODE: str = "qwen2.5-coder"     # code generation
    MODEL_VISION: str = "llava"           # image understanding
    MODEL_EMBEDDING: str = "nomic-embed-text"  # embeddings for memory search
    MODEL_SMALL: str = "phi4-mini"        # fast, lightweight tasks (classification, routing)

    # ── Voice ────────────────────────────────────────────
    VOICE_ENABLED: bool = True
    TTS_MODEL: str = "piper"             # local TTS engine
    STT_MODEL: str = "whisper-base"      # local STT (via faster-whisper)
    WAKE_WORD: str = "aria"

    # ── Web Search ───────────────────────────────────────
    SEARXNG_URL: str = "http://localhost:8888"  # local SearXNG instance
    SEARCH_RESULTS_LIMIT: int = 10

    # ── Task Queue / Scheduler ───────────────────────────
    MAX_CONCURRENT_TASKS: int = 3
    TASK_TIMEOUT_SECONDS: int = 300

    # ── Optional API Keys (for cloud fallback) ───────────
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = self.DATA_DIR / "aria.db"
        return f"sqlite+aiosqlite:///{db_path}"

    def ensure_dirs(self):
        """Create necessary directories."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "logs").mkdir(exist_ok=True)
        (self.DATA_DIR / "voice_cache").mkdir(exist_ok=True)
        (self.DATA_DIR / "downloads").mkdir(exist_ok=True)


settings = Settings()
settings.ensure_dirs()
