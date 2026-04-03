# Aria — Copilot Instructions

## Dev Commands

```bash
# First-time setup
chmod +x setup.sh && ./setup.sh

# Start everything (backend :8000, frontend :3000)
./start.sh

# Docker alternative
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

Aria is a local AI personal assistant with a **morphing UI** — the frontend renders different view components depending on what the user asks for.

```
User message
    → FastAPI backend (/routes/chat.py)
    → Agent Router (MODEL_SMALL / phi4-mini): classifies intent → picks specialist agent
    → Agent Executor: calls Ollama model + iterates tool calls until done
    → Layout Engine (MODEL_SMALL): classifies response → picks frontend view type
    → SSE stream back to React frontend
    → DashboardRenderer.tsx mounts the matching view component
```

### Key Files

| File | Role |
|------|------|
| `backend/app/agents/registry.py` | Defines `AgentSpec` (name, model_key, tools, system_prompt). All agents registered here. |
| `backend/app/agents/router.py` | Uses `MODEL_SMALL` to JSON-classify which agent handles each message. |
| `backend/app/agents/executor.py` | Runs the selected agent in a tool-calling loop. Supports native tool calling + ReAct fallback. |
| `backend/app/agents/layout_engine.py` | After agent responds, classifies which of 16 UI layouts to use. |
| `backend/app/tools/registry.py` | Tool definitions with JSON schemas. |
| `backend/app/tools/executor.py` | Dispatches tool calls by name. |
| `backend/app/memory/manager.py` | SQLite-backed semantic memory using `nomic-embed-text` + cosine similarity. |
| `backend/app/config.py` | Central config via `pydantic-settings`. All fields overridable via `.env`. |
| `frontend/src/components/DashboardRenderer.tsx` | Switches on `layout` field to mount the right view component. |
| `frontend/src/api.ts` | All backend API calls and SSE streaming logic. |

### Request Flow (web search example)

1. Router → `researcher` agent (uses `MODEL_REASONING`)
2. Pre-retrieval pipeline fires (for `researcher`, `general`, `planner` agents) — fetches web content *before* model generates
3. Agent calls `web_search` / `news_search` → `web_scrape` tools
4. Layout engine → `news_article` or `search_results` layout
5. Frontend renders structured view with citations

### User Data

All user data lives in `~/.aria/` (SQLite `aria.db`, logs, voice cache, downloads). Never in the repo.

---

## Key Conventions

### Model Keys, Not Model Names

Agents always specify `model_key="MODEL_REASONING"` (a settings attribute), never a hardcoded model string. This lets users swap models in `.env` without touching code.

```python
# ✅ correct
AgentSpec(name="researcher", model_key="MODEL_REASONING", ...)

# ❌ wrong
AgentSpec(name="researcher", model_key="llama3.2", ...)
```

Default role assignments (from `config.py` / `.env`):

| Key | Default | Purpose |
|-----|---------|---------|
| `MODEL_SMALL` | phi4-mini | Routing, classification, layout decisions |
| `MODEL_CHAT` | llama3.2 | General conversation |
| `MODEL_REASONING` | llama3.2 | Research, planning, finance |
| `MODEL_CODE` | qwen2.5-coder | Coding tasks |
| `MODEL_EMBEDDING` | nomic-embed-text | Memory semantic search |
| `MODEL_BROWSER` | llama3.2 | Browser agent |

### ReAct Fallback for Models Without Native Tool Calling

`MODELS_WITHOUT_NATIVE_TOOLS` in `executor.py` lists model name prefixes that can't use Ollama's native tool-calling API. These models receive a `REACT_TOOL_INSTRUCTIONS` block instructing them to emit `<tool_call>{...}</tool_call>` tags; the executor parses and runs them. When adding a new model that returns 400 errors on tool calls, add its name prefix to this set.

### Adding a New Agent

1. `register(AgentSpec(...))` in `registry.py` — the router picks it up automatically
2. Add to `_RETRIEVAL_AGENTS` in `executor.py` if it should pre-fetch web content before generating

### Adding a New Tool

1. Implement the function in `backend/app/tools/` (e.g., `web.py`)
2. Register with a JSON schema in `tools/registry.py`
3. Add the tool name to the relevant agent's `tools: list[str]` in `registry.py`

### Adding a New UI Layout

1. Add the layout type + description to `LAYOUT_TYPES` dict in `layout_engine.py`
2. Create `frontend/src/components/views/MyView.tsx`
3. Add a `case` to `DashboardRenderer.tsx`

### Memory

`MemoryManager` stores entries with a category, importance score (0–1), and a `nomic-embed-text` embedding. `search()` runs cosine similarity over all SQLite rows — no external vector DB. Embeddings are stored as JSON arrays.

### Streaming

Chat responses stream via SSE. Backend yields `data: {...}\n\n` chunks. The layout directive is sent as a final non-content SSE event after the full response is streamed. Frontend consumes via `EventSource` in `api.ts`.
