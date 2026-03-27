<div align="center">

# 🌟 Aria — Your Personal AI Assistant

**A local-first, privacy-respecting AI assistant that actually works for daily life.**

Like "Her" from the movie — but running on your laptop, with your data staying yours.

[Quick Start](#-quick-start) · [Features](#-features) · [Architecture](#-architecture) · [Configuration](#-configuration)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🧠 Persistent Memory** | Remembers your preferences, budget, dietary needs, and context across conversations |
| **🤖 Multi-Agent System** | 7 specialized agents (general, researcher, planner, finance, health, coder, writer) — auto-routes to the best one |
| **🔧 Tool Calling** | Web search, web scraping, file I/O, shell commands, calculator, reminders |
| **🎙️ Voice Interaction** | Hold-to-talk voice input (Whisper STT) + text-to-speech (Piper/Edge TTS) |
| **🔍 Private Web Search** | Self-hosted SearXNG — no tracking, no ads, no data sold |
| **⏰ Reminders & Scheduling** | "Remind me at 3pm" / "Run this task after 10pm" |
| **💰 Budget Tracking** | Track monthly income/expenses, ask "can I eat out tonight?" |
| **🍳 Recipes & Health** | Diet plans, exercise schedules, meal planning |
| **📰 News & Research** | "Show me news about XYZ" → fetched, formatted, summarizable |
| **🚀 Works Offline** | Runs 100% locally via Ollama — no API keys needed |
| **📱 Adaptive UI** | Clean dark interface that adapts to show tables, articles, lists, code |

## 🚀 Quick Start

### One-Command Setup

```bash
git clone <your-repo-url> && cd AI-Personal-Assistant
chmod +x setup.sh && ./setup.sh
```

This will:
1. Check Python & Node.js (install if needed)
2. Install Ollama (local AI server)
3. Auto-detect your RAM and pull appropriate models
4. Set up backend (Python venv + dependencies)
5. Set up frontend (npm install)
6. Create `.env` with optimal settings for your hardware

### Start Aria

```bash
./start.sh
```

Open **http://localhost:3000** — that's it!

### Docker (Alternative)

```bash
# First install Ollama on your host: https://ollama.com
ollama pull llama3.2 && ollama pull phi4-mini && ollama pull nomic-embed-text

docker-compose up -d
# Open http://localhost:3000
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Voice Orb│  │ Chat View│  │ Sidebar  │  │Adaptive │ │
│  │ (STT/TTS)│  │(Markdown)│  │ (History)│  │  Layout │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────┴─────────────────────────────────┐
│                    Backend (FastAPI)                       │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  Agent Router                        │ │
│  │    Analyzes intent → picks best specialist agent     │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             │                                             │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │              Specialist Agents                       │ │
│  │  General │ Researcher │ Planner │ Finance │ Health   │ │
│  │          │ Coder      │ Writer  │                    │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             │                                             │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │                  Tool System                         │ │
│  │  web_search │ web_scrape │ calculator │ file_io     │ │
│  │  memory_search │ memory_store │ reminders │ shell   │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             │                                             │
│  ┌──────────▼────────┐  ┌────────────┐  ┌────────────┐  │
│  │  Memory Manager   │  │ Scheduler  │  │ Task Queue │  │
│  │ (Semantic Search) │  │ (Reminders)│  │ (Async)    │  │
│  └──────────┬────────┘  └────────────┘  └────────────┘  │
└─────────────┼────────────────────────────────────────────┘
              │
┌─────────────▼────────┐  ┌────────────────────────────────┐
│   SQLite Database    │  │   Ollama (Local AI Models)     │
│   - Conversations    │  │   - llama3.2 (chat)            │
│   - Memory entries   │  │   - deepseek-r1 (reasoning)    │
│   - Tasks/Reminders  │  │   - qwen2.5-coder (code)       │
│   - User profile     │  │   - phi4-mini (fast routing)   │
│   - Embeddings       │  │   - nomic-embed-text (search)  │
└──────────────────────┘  └────────────────────────────────┘
```

### How a request flows:

1. **User says**: "Find me the cheapest flight to NYC and hotels near Times Square"
2. **Router** (phi4-mini, fast): classifies → `researcher` agent
3. **Researcher** agent (deepseek-r1, smart): plans steps, calls tools
4. **Tools** execute: `web_search("cheapest flight NYC")` → `web_search("hotels near Times Square")` → `web_scrape(top results)`
5. **Agent** synthesizes results into a comparison table
6. **Memory** stores: "User is interested in NYC trip" for future context
7. **UI** renders the markdown table with links

## ⚙️ Configuration

### Model Selection by Hardware

| RAM | Recommended Setup | Models |
|-----|------------------|--------|
| **8 GB** | Lightweight | `phi4-mini` for everything, `nomic-embed-text` |
| **16 GB** | Standard | `llama3.2` + `phi4-mini` + `nomic-embed-text` |
| **32 GB+** | Full | All models including `deepseek-r1` + `qwen2.5-coder` + `llava` |

Edit `.env` to customize:

```env
MODEL_CHAT=llama3.2          # Main conversation model
MODEL_REASONING=deepseek-r1  # Complex tasks & planning
MODEL_CODE=qwen2.5-coder     # Code generation
MODEL_SMALL=phi4-mini        # Fast routing & classification
MODEL_EMBEDDING=nomic-embed-text  # Memory semantic search
```

### Key Directories

```
~/.aria/                  # All user data (portable!)
  ├── aria.db            # SQLite database
  ├── logs/              # Application logs
  ├── files/             # User files (sandboxed)
  ├── voice_cache/       # TTS audio cache
  └── downloads/         # Downloaded content
```

## 🛠️ Project Structure

```
AI-Personal-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Central configuration
│   │   ├── agents/
│   │   │   ├── registry.py      # Agent definitions (7 specialists)
│   │   │   ├── router.py        # Intent classification & routing
│   │   │   ├── executor.py      # Agent execution with tool loops
│   │   │   └── ollama_client.py # Ollama API client
│   │   ├── memory/
│   │   │   ├── database.py      # Async SQLAlchemy setup
│   │   │   ├── models.py        # DB schema (conversations, memory, tasks)
│   │   │   └── manager.py       # Semantic memory search
│   │   ├── tools/
│   │   │   ├── registry.py      # Tool definitions & schemas
│   │   │   ├── executor.py      # Dynamic tool dispatch
│   │   │   ├── web.py           # Web search & scraping
│   │   │   ├── calculator.py    # Safe math evaluation
│   │   │   ├── filesystem.py    # Sandboxed file I/O
│   │   │   ├── shell.py         # Command execution
│   │   │   ├── memory_tools.py  # Memory read/write
│   │   │   └── reminder_tools.py
│   │   ├── voice/
│   │   │   ├── stt.py           # Whisper speech-to-text
│   │   │   └── tts.py           # Piper/Edge text-to-speech
│   │   ├── scheduler/
│   │   │   ├── engine.py        # Reminder & task scheduler
│   │   │   └── queue.py         # Async task queue
│   │   └── routes/
│   │       ├── chat.py          # Chat + streaming
│   │       ├── tasks.py         # Task management
│   │       ├── memory.py        # Memory CRUD
│   │       ├── voice.py         # STT/TTS endpoints
│   │       └── settings.py      # Profile & system info
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main app with routing
│   │   ├── api.ts               # Backend API client
│   │   ├── components/
│   │   │   ├── HomeView.tsx     # Landing page with voice orb
│   │   │   ├── ChatView.tsx     # Chat interface with markdown
│   │   │   ├── VoiceOrb.tsx     # Voice input component
│   │   │   └── Sidebar.tsx      # Conversation history
│   │   └── index.css            # Global styles + animations
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # Full stack + SearXNG
├── setup.sh                     # One-click setup
├── start.sh                     # One-click start
├── .env.example                 # Configuration template
└── README.md
```

## 🎯 What Makes This Different

| Gap in the Market | Aria's Approach |
|-------------------|-----------------|
| ChatGPT/Claude require internet & subscription | **Runs 100% locally, free forever** |
| Siri/Alexa can't do complex multi-step tasks | **Multi-agent system with tool calling** |
| AI assistants forget everything between sessions | **Persistent semantic memory** |
| Privacy concerns with cloud AI | **Your data never leaves your machine** |
| Complex setup (APIs, tokens, config) | **One script: `./setup.sh`** |
| One model for everything | **Best model for each task** (fast router + specialists) |

## 📄 License

MIT — Do whatever you want with it.
