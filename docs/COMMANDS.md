# Aria — Command Helpbook
> Quick reference for every command you need. Bookmark this.

---

## 📁 Project Structure

```
AI-Personal-Assistant/          ← project root (run most commands from here)
├── backend/                    ← FastAPI + Python backend
│   └── venv/                   ← Python virtual environment
├── frontend/                   ← React + Vite frontend
├── electron/                   ← Electron desktop app
├── modelfiles/                 ← Custom Ollama model definitions
├── docs/                       ← Project docs and tickets
├── package.json                ← Electron scripts (run from root)
├── start.sh                    ← Web mode launcher
└── setup.sh                    ← First-time setup
```

---

## 🚀 Launch Commands

### Desktop App (Electron) — Recommended
```bash
# From: project root
cd ~/Documents/Repo/AI-Personal-Assistant
npm run electron:dev
```
> Starts Vite frontend on :3000, waits, then opens the Electron window.
> Backend auto-starts inside Electron. One command, everything runs.

### Web Mode (Browser)
```bash
# From: project root
./start.sh
```
> Starts backend on :8000 and frontend on :3000.
> Open http://localhost:3000 in your browser.

---

## ⚙️ Backend Commands

All backend commands run from the `backend/` folder with venv activated.

```bash
cd ~/Documents/Repo/AI-Personal-Assistant/backend
source ..venv/bin/activate
```

| Task | Command |
|------|---------|
| Start backend | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Start backend (no reload) | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Check backend health | `curl http://localhost:8000/api/health` |
| Install dependencies | `pip install -r requirements.txt` |
| Install patchright browser | `python -m patchright install chromium` |

---

## 🖥️ Frontend Commands

All frontend commands run from the `frontend/` folder.

```bash
cd ~/Documents/Repo/AI-Personal-Assistant/frontend
```

| Task | Command |
|------|---------|
| Start dev server (:3000) | `npm run dev` |
| Build for production | `npm run build` |
| Preview production build | `npm run preview` |
| Install dependencies | `npm install` |

---

## 🖥️ Electron Commands

All Electron commands run from the **project root**.

```bash
cd ~/Documents/Repo/AI-Personal-Assistant
```

| Task | Command |
|------|---------|
| Start desktop app (dev) | `npm run electron:dev` |
| Build desktop app | `npm run electron:build` |
| Install Electron dependencies | `npm install` |

---

## 🤖 Ollama Commands

```bash
# Check Ollama is running
ollama list

# Start Ollama server (if not running)
ollama serve

# Pull a model
ollama pull llama3.2
ollama pull phi4-mini
ollama pull qwen2.5
ollama pull qwen2.5-coder
ollama pull nomic-embed-text

# Create custom model from Modelfile
ollama create qwen2.5-browser -f modelfiles/qwen2.5-browser.Modelfile

# Re-create after editing a Modelfile
ollama rm qwen2.5-browser
ollama create qwen2.5-browser -f modelfiles/qwen2.5-browser.Modelfile

# Test a model in terminal
ollama run qwen2.5-browser
ollama run qwen2.5-browser "navigate to google.com and search for AI news"

# See model details / current settings
ollama show qwen2.5-browser
ollama show qwen2.5-browser --modelfile

# Remove a model
ollama rm <model-name>
```

### Models currently in Aria

| Model | Role | Used for |
|-------|------|----------|
| `llama3.2` | Chat + Reasoning | General conversation, planning |
| `phi4-mini` | Router | Intent classification, fast tasks |
| `qwen2.5-coder` | Code | Code generation, review |
| `qwen2.5-browser` | Browser | Web navigation, form filling |
| `nomic-embed-text` | Embedding | Memory semantic search |
| `qwen3.5-max` | — | Available, not yet assigned |
| `deepseek-r1` | — | Available (slower, better reasoning) |

---

## 🛠️ Setup (First Time Only)

```bash
cd ~/Documents/Repo/AI-Personal-Assistant

# Full one-click setup (installs everything)
chmod +x setup.sh && ./setup.sh

# Or manually:
# 1. Backend
cd backend
python3 -m venv venv
source ..venv/bin/activate
pip install -r requirements.txt
python -m patchright install chromium
cd ..

# 2. Frontend
cd frontend && npm install && cd ..

# 3. Electron
npm install

# 4. Ollama models
ollama pull llama3.2
ollama pull phi4-mini
ollama pull qwen2.5
ollama pull nomic-embed-text
ollama create qwen2.5-browser -f modelfiles/qwen2.5-browser.Modelfile
```

---

## 🐳 Docker (Alternative)

```bash
cd ~/Documents/Repo/AI-Personal-Assistant

# Start everything in Docker
docker-compose up -d

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f
docker-compose logs -f backend
```

---

## 🔍 Debug & Diagnostics

```bash
# Check what's running on key ports
lsof -i :8000    # backend
lsof -i :3000    # frontend
lsof -i :8001    # Electron IPC server
lsof -i :9222    # CDP (browser-use ↔ Electron)
lsof -i :11434   # Ollama

# Kill a stuck process on a port
kill $(lsof -t -i :8000)

# Check backend logs live (if started manually)
cd backend && source ..venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Test browser-use CDP connection
curl http://localhost:9222/json
# Expected: JSON list of open Chrome tabs

# Test Ollama API directly
curl http://localhost:11434/api/tags
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5-browser","prompt":"hello","stream":false}'

# Test backend chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"go to google.com","stream":false}'

# Reset browser-use session (if agent gets stuck)
# Just close and reopen the Electron app — sessions are persistent
```

---

## 📋 Environment Config

```bash
# Edit model assignments (no code changes needed)
nano ~/Documents/Repo/AI-Personal-Assistant/.env
```

Key `.env` variables:

```env
MODEL_CHAT=llama3.2
MODEL_REASONING=llama3.2
MODEL_CODE=qwen2.5-coder
MODEL_BROWSER=qwen2.5-browser
MODEL_SMALL=phi4-mini
MODEL_EMBEDDING=nomic-embed-text

OLLAMA_BASE_URL=http://localhost:11434
```

> **Swap a model without touching code:** just change the value here and restart the backend.

---

## 📁 Data & Logs

```bash
# User data lives here (never in the repo)
ls ~/.aria/
# aria.db        — conversation history + memory
# browser_data/  — persistent browser sessions (stays logged in)
# qa_recordings/ — QA videos
# logs/

# View conversation DB
sqlite3 ~/.aria/aria.db ".tables"
sqlite3 ~/.aria/aria.db "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

---

## 🌿 Git

```bash
# Current branch / status
git status
git branch

# Switch to EPIC-A branch
git checkout EPIC-A

# Commit with Copilot trailer
git add -A
git commit -m "feat: your message here

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

# Push
git push origin EPIC-A
```
