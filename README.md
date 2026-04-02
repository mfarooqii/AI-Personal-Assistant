<div align="center">

# Aria — One Interface for Everything

**Replace 50 apps with one conversation. Your AI assistant that morphs into whatever you need.**

Like having a personal assistant who can turn into a calendar, a news reader, a task board, a flight search engine, an email client — all by just asking.

Running locally on your machine. Your data stays yours.

[Quick Start](#-quick-start) · [How It Works](#-how-it-works) · [Features](#-features) · [Architecture](#-architecture)

</div>

---

## 💡 The Idea

Computing started with terminals. Then GUIs took over. Now it's time for the next shift: **you talk, the computer transforms.**

Instead of opening Gmail for email, Google Calendar for scheduling, Trello for tasks, Chrome for news, and Excel for data — you open Aria, say what you need, and the interface becomes that thing.

```
You:    "Show me today's news about AI"
Aria:   → screen morphs into a Perplexity-style news article with sources

You:    "What's my schedule this week?"
Aria:   → screen morphs into a calendar view

You:    "Compare flights to Dubai under $500"
Aria:   → screen morphs into a travel comparison table

You:    "Show my tasks"
Aria:   → screen morphs into a Jira-like kanban board
```

**One app. Every shape. Like water.**

---

## 🚀 Quick Start

### First Time Setup

```bash
git clone <your-repo-url> && cd AI-Personal-Assistant
chmod +x setup.sh && ./setup.sh
```

### Start Aria

```bash
./start.sh
```

Open **http://localhost:3000** — Aria will greet you and set itself up through conversation.

### Docker (Alternative)

```bash
ollama pull llama3.2 && ollama pull phi4-mini && ollama pull nomic-embed-text
docker-compose up -d
```

---

## 🎯 How It Works

### For You (The User)

1. **Open Aria** → clean screen with a voice orb and text input
2. **First time?** → Aria asks your name, what you do, what matters to you — sets everything up through chat
3. **Just talk** → type or speak what you need
4. **Screen transforms** → the right interface appears automatically
5. **Connect your accounts** → Gmail, Slack, Calendar — browse everything in one place
6. **It remembers** → your preferences, habits, and context — forever

### For Developers (Under The Hood)

1. **User speaks** → message hits FastAPI backend
2. **Router** classifies intent → picks the best specialist agent (15 agents)
3. **Pre-retrieval** → for news/research, web content is fetched BEFORE the model responds
4. **Agent executes** → calls tools (search, scrape, calculate, remember, etc.)
5. **Layout Engine** classifies the response → picks the right UI view
6. **Frontend morphs** → React renders the matching layout (calendar, kanban, news, finance, etc.)
7. **Memory stores** context for next time

---

## ✨ Features

### Adaptive UI — The Screen Becomes What You Need

| Say This | Screen Becomes |
|----------|---------------|
| "Show me today's news" | Perplexity-style article with summaries + sources |
| "What's my schedule?" | Calendar with events and reminders |
| "Track my expenses" | Financial dashboard with charts |
| "Show my tasks" | Kanban board (like Jira/Trello) |
| "Compare these laptops" | Side-by-side comparison table |
| "Search for hotels in Paris" | Search result cards with prices |
| "Write a blog post about..." | Document editor view |
| "Show me a timeline of..." | Visual timeline |
| "Analyze this data" | Sortable data table |

### 15 Specialist Agents
General chat, Research, Planning, Finance, Health, Coding, Writing, Education, Legal, Real Estate, Design, Data Analysis, DevOps, Marketing, HR — auto-routed by intent.

### Real Web Search
Not hallucinated results. Aria searches the web (SearXNG / DuckDuckGo), scrapes articles, and presents real content with citations — like Perplexity.

### Persistent Memory
Aria remembers your name, budget, dietary restrictions, work schedule, preferences — and uses them automatically in every interaction.

### Voice In/Out
Speak to Aria using the voice orb. Local speech-to-text (Whisper) and text-to-speech (Piper/Edge TTS).

### Gmail & Messaging Integration
Connect your Gmail and messaging apps. Browse emails, reply, and manage conversations — all from Aria.

### 100% Local & Private
Runs on your machine via Ollama. No API keys needed. No data sent to any cloud. Your personal data stays personal.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Voice Orb│  │ Chat View│  │ Sidebar  │  │Adaptive     │ │
│  │ (STT/TTS)│  │(Markdown)│  │ (History)│  │Dashboard    │ │
│  └──────────┘  └──────────┘  └──────────┘  │(11 views)   │ │
│                                             └─────────────┘ │
│  Morphing Views: News │ Calendar │ Finance │ Kanban │ Code  │
│    Search │ Comparison │ Timeline │ Table │ Document │ ...  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────┴─────────────────────────────────────┐
│                    Backend (FastAPI)                           │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐ ┌─────────────┐ │
│  │   Agent Router    │  │ Layout Engine    │ │ Onboarding  │ │
│  │ 15 specialists    │  │ 15 layout types  │ │ Wizard      │ │
│  └────────┬─────────┘  └──────────────────┘ └─────────────┘ │
│           │                                                   │
│  ┌────────▼─────────┐  ┌──────────────────┐ ┌─────────────┐ │
│  │  Pre-Retrieval   │  │  Workflow Engine  │ │Integrations │ │
│  │  Pipeline (RAG)  │  │  10 workflows    │ │Gmail, Slack │ │
│  └────────┬─────────┘  └──────────────────┘ └─────────────┘ │
│           │                                                   │
│  ┌────────▼─────────────────────────────────────────────────┐│
│  │                    Tool System                            ││
│  │ web_search │ news_search │ web_scrape │ calculator       ││
│  │ memory_search │ memory_store │ reminders │ file_io │ sh  ││
│  │ gmail_read │ gmail_send │ gmail_search (coming)          ││
│  └──────────────────────────────────────────────────────────┘│
│                                                               │
│  ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Memory Manager   │ │  Scheduler   │ │   Task Queue     │ │
│  │(Semantic Search) │ │ (Reminders)  │ │   (Background)   │ │
│  └────────┬─────────┘ └──────────────┘ └──────────────────┘ │
└───────────┼──────────────────────────────────────────────────┘
            │
┌───────────▼──────────┐  ┌────────────────────────────────────┐
│   SQLite Database    │  │     Ollama (Local AI Models)       │
│   - Conversations    │  │     - llama3.2 (chat)              │
│   - Memory entries   │  │     - qwen2.5-coder (code)        │
│   - User profile     │  │     - phi4-mini (fast routing)    │
│   - Tasks/Reminders  │  │     - nomic-embed-text (search)   │
│   - OAuth tokens     │  │                                    │
└──────────────────────┘  └────────────────────────────────────┘
```
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
