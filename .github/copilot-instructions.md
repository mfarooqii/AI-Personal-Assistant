# Aria — Copilot Instructions

## Quick Start & Dev Commands

```bash
# First-time setup
chmod +x setup.sh && ./setup.sh

# Start everything (backend :8000, frontend :3000)
./start.sh

# Or via Docker
ollama pull llama3.2 && ollama pull phi4-mini && ollama pull nomic-embed-text
docker-compose up -d
```

**Backend** (FastAPI + uvicorn):
```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (Vite + React):
```bash
cd frontend
npm run dev       # dev server on :3000
npm run build     # production build
npm run preview   # preview production build
```

No test suite exists yet. Manual testing via `http://localhost:3000`.

---

## Architecture

**Aria** is a local AI personal assistant with a morphing UI — the frontend renders different view components depending on what the user asks for.

```
User message
    → FastAPI backend (/routes/chat.py)
    → Agent Router (phi4-mini, fast): classifies intent → picks specialist agent
    → Agent Executor: calls Ollama model + iterates tool calls until done
    → Layout Engine (phi4-mini): classifies response → picks frontend view type
    → SSE stream back to React frontend
    → DashboardRenderer mounts the matching view component
```

**Key layers:**
- `backend/app/agents/registry.py` — Defines `AgentSpec` (name, model_key, tools, system_prompt). All agents registered here.
- `backend/app/agents/router.py` — Uses `MODEL_SMALL` (phi4-mini) to JSON-classify which agent handles the message.
- `backend/app/agents/executor.py` — Runs the selected agent in a tool-calling loop. Supports both Ollama native tool calling and ReAct `<tool_call>...</tool_call>` fallback.
- `backend/app/agents/layout_engine.py` — After the agent responds, classifies which UI layout to use (16 layout types: chat, news_article, calendar, kanban, finance, etc.)
- `backend/app/tools/registry.py` — Tool definitions with JSON schemas. `backend/app/tools/executor.py` dispatches by name.
- `backend/app/memory/manager.py` — SQLite-backed semantic memory using `nomic-embed-text` embeddings + cosine similarity (numpy, no vector DB).
- `frontend/src/components/DashboardRenderer.tsx` — Switches on `layout` field to mount the right view component.

**Data flow for a web search request:**
1. Router → `researcher` agent (uses `MODEL_REASONING`)
2. Pre-retrieval pipeline fires for `researcher`/`general`/`planner` agents (fetches web content before model generates)
3. Agent calls `web_search` or `news_search` tools → `web_scrape` for full content
4. Layout engine → `news_article` or `search_results` layout
5. Frontend renders structured view with citations

**User data** is stored in `~/.aria/` (SQLite `aria.db`, logs, voice cache, downloads). Never in the repo.

---

## Key Conventions

### Model Assignment Pattern
Models are assigned by role, not by name, via `settings.MODEL_*` keys. Agents specify `model_key="MODEL_REASONING"` (not a literal model name). This lets users swap models in `.env` without touching code.

```python
# In AgentSpec — always use a model key, never a hardcoded model name
AgentSpec(name="researcher", model_key="MODEL_REASONING", ...)
```

Default model roles:
- `MODEL_SMALL` (phi4-mini) — routing, classification, layout decisions
- `MODEL_CHAT` (llama3.2) — general conversation
- `MODEL_REASONING` (llama3.2 / deepseek-r1) — research, planning, finance
- `MODEL_CODE` (qwen2.5-coder) — coding tasks
- `MODEL_EMBEDDING` (nomic-embed-text) — memory semantic search

### ReAct Fallback for Models Without Native Tool Calling
Models listed in `MODELS_WITHOUT_NATIVE_TOOLS` (in `executor.py`) use `<tool_call>{...}</tool_call>` text tags instead of Ollama's native tool-calling API. When adding a new model that returns 400 errors on tool calls, add its name prefix to this set.

### Adding a New Agent
1. `register(AgentSpec(...))` in `registry.py`
2. The router automatically picks it up — no other wiring needed
3. Add the agent name to `_RETRIEVAL_AGENTS` in `executor.py` if it should pre-fetch web content

### Adding a New Tool
1. Define the tool function in `backend/app/tools/` (e.g., `web.py`)
2. Register it in `tools/registry.py` with a JSON schema
3. Add the tool name to the relevant agent's `tools: list[str]` in `registry.py`

### Adding a New UI Layout
1. Add the layout type + description to `LAYOUT_TYPES` in `layout_engine.py`
2. Create `frontend/src/components/views/MyView.tsx`
3. Add a case to `DashboardRenderer.tsx`

### Configuration
All config in `backend/app/config.py` via `pydantic-settings`. Every field can be overridden via `.env` or environment variable. `settings` is a module-level singleton — import and use directly.

### Memory
Memory is categorized (`fact`, `preference`, `event`, etc.) and scored by importance (0–1). `MemoryManager.search()` runs cosine similarity over all entries in SQLite — no external vector DB. Embeddings stored as JSON arrays in the DB.

### Streaming
Chat responses stream via SSE. The backend yields chunks as `data: {...}\n\n`. The frontend consumes via `EventSource`. Layout directives are sent as a final non-content SSE event after streaming completes.
