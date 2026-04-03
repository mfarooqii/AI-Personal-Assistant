"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logger import setup_logging
from app.memory.database import init_db
from app.routes import chat, tasks, memory, voice, settings as settings_routes, workflows
from app.routes import onboarding, integrations, browser, extension, logs as logs_routes
from app.scheduler.engine import scheduler

# Initialise logging before anything else so all startup messages are captured
setup_logging(settings.DATA_DIR / "logs", debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    await init_db()
    scheduler.start()
    yield
    # ── Shutdown ──
    scheduler.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # narrowed in production via env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(browser.router, prefix="/api/browser", tags=["browser"])
app.include_router(extension.router,      prefix="/api/extension",    tags=["extension"])
app.include_router(logs_routes.router,    prefix="/api/logs",         tags=["logs"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}
