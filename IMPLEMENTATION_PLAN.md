# Aria — Implementation Plan
**Version:** 1.0  
**Date:** March 2026  
**Reference:** PRODUCT_STRATEGY.md

Each ticket is self-contained: what to build, how to implement it, how to test it, what to expect, and exactly what tools/libraries to install.

---

## Phase 1 — Core Assistant ✅ COMPLETE

Already built and working:
- FastAPI backend, multi-agent routing, tool calling, web search, SQLite memory, voice I/O, React frontend, Docker

---

## Phase 2 — Memory Layer + Browser Extension

---

### TICKET-201: Temporal Episodic Memory Compression

**What to build:**
A background scheduler that compresses raw conversation history into layered summaries:
- Raw events (already stored in SQLite)
- Daily summaries (auto-generated nightly)
- Weekly abstracts (Sunday nights)
- Monthly themes (1st of each month)
- Persistent user model (continuously updated)

**Implementation:**

Install:
```bash
pip install apscheduler
```

Files to create/modify:
- `backend/app/memory/compressor.py` — compression logic using the LLM
- `backend/app/memory/models.py` — add `MemorySummary` table
- `backend/app/scheduler/engine.py` — register compression jobs
- `backend/app/memory/manager.py` — update retrieval to query all layers

Schema addition:
```sql
CREATE TABLE memory_summaries (
  id TEXT PRIMARY KEY,
  layer TEXT,          -- 'daily' | 'weekly' | 'monthly' | 'user_model'
  period_start DATETIME,
  period_end DATETIME,
  content TEXT,
  embedding BLOB,
  created_at DATETIME
);
```

Compression prompt (daily):
```
You are compressing a day of conversations into a structured daily summary.
Extract: key decisions made, topics discussed, tasks created, emotional tone,
important facts learned about the user. Output JSON.
Conversations: {raw_events}
```

**How to test:**
```bash
# 1. Have 10+ conversations to generate data
# 2. Trigger compression manually:
curl -X POST http://localhost:8000/api/memory/compress/daily

# 3. Query the summary layer:
curl http://localhost:8000/api/memory/summaries?layer=daily

# 4. Ask a question that requires long-term memory:
# "What have I been working on this week?"
# Expected: Answer synthesized from daily summaries, not just raw messages
```

**What to expect:**
- API returns a structured daily summary with topics, decisions, and key facts
- Questions about "this week" or "recently" are answered using compressed memory, not raw search
- Response is faster (searching 7 summaries vs. 100 raw messages)

**Tech required:**
```
apscheduler>=3.10
numpy (already installed — for embedding comparison)
Ollama running llama3.2 (already running)
```

---

### TICKET-202: Semantic Memory Retrieval Upgrade

**What to build:**
Replace keyword-based memory search with proper vector embedding similarity search across all memory layers.

**Implementation:**

Install nothing new — `nomic-embed-text` via Ollama is already available.

Files to modify:
- `backend/app/memory/manager.py` — replace text LIKE search with cosine similarity on embeddings

Algorithm:
1. When user sends a message, embed it with `nomic-embed-text`
2. Compute cosine similarity against all stored memory embeddings
3. Return top-K most relevant memories, weighted by recency and layer
4. Inject into agent system prompt as context

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

**How to test:**
```bash
# 1. Save a memory with a specific fact:
curl -X POST http://localhost:8000/api/memory \
  -d '{"content": "My dog is named Butter and she is a golden retriever"}'

# 2. Ask a semantically related but not keyword-identical question:
# "What kind of pet do I have?" or "Tell me about my animals"
# Expected: Aria surfaces the dog memory even though "dog" wasn't in the query
```

**What to expect:**
- Questions answered using semantically relevant context even when exact words don't match
- Memory retrieval works across all languages
- 3-5x improvement in memory recall accuracy vs. keyword search

**Tech required:**
```
numpy (already installed)
Ollama with nomic-embed-text (already running)
```

---

### TICKET-203: Browser Extension — Core

**What to build:**
A Chrome/Firefox/Edge extension that connects to the local Aria backend (`localhost:8000`) and provides:
- Sidebar chat panel (Ctrl+Shift+A toggle)
- Save page to memory button
- Text selection → action menu (summarize, explain, save, ask)

**Implementation:**

Create directory: `browser-extension/`

Files:
```
browser-extension/
  manifest.json        # Extension manifest (v3)
  background.js        # Service worker
  content.js           # Injected into pages
  sidebar/
    sidebar.html
    sidebar.css
    sidebar.js
  icons/
    icon16.png
    icon48.png
    icon128.png
```

Key manifest permissions:
```json
{
  "manifest_version": 3,
  "permissions": ["activeTab", "contextMenus", "storage", "sidePanel"],
  "host_permissions": ["http://localhost:8000/*"],
  "content_scripts": [{"matches": ["<all_urls>"], "js": ["content.js"]}]
}
```

Content script behavior:
- On text selection → show floating mini-menu: [Ask Aria] [Save] [Summarize]
- On [Save Page]: extract main article text, POST to `localhost:8000/api/memory`
- On [Ask Aria]: open sidebar with selected text pre-filled in chat input

Sidebar: embed the existing Aria React chat UI in an iframe, or rebuild as vanilla JS.

Backend endpoint needed:
```
POST /api/browser/save-page
  body: { url, title, content, selected_text? }

POST /api/browser/summarize
  body: { content, url }
  returns: { summary }
```

**How to test:**
1. Load extension in Chrome: `chrome://extensions` → Enable Developer Mode → Load Unpacked → select `browser-extension/`
2. Open any news article
3. Press Ctrl+Shift+A → sidebar appears with Aria chat
4. Highlight a paragraph → floating menu appears → click Summarize → summary appears inline
5. Click Save Page → check memory: `curl http://localhost:8000/api/memory/recent`
6. Ask Aria: "What was that article I just saved?" → should recall it

**What to expect:**
- Extension loads without errors in Chrome DevTools
- Sidebar opens and connects to backend (shows green indicator)
- Saved pages appear in memory retrieval
- Selection menu appears within 100ms of releasing mouse button

**Tech required:**
```
Chrome / Firefox / Edge (any current version)
No npm packages needed — vanilla JS for performance
Backend: no new dependencies
```

---

### TICKET-204: Browser Extension — Write Mode

**What to build:**
On any `<textarea>` or `contenteditable` element, show an inline Aria button that opens a compose-assist overlay.

**Features:**
- "Improve this" — rewrites existing text in textarea
- "Reply to this" — reads email/post context, drafts a reply
- "Make it shorter / longer / formal / casual" — tone controls
- Learns your writing style over time (stored in memory layer)

**How to test:**
1. Open Gmail, start composing an email
2. Aria button appears bottom-right of compose window
3. Type a rough draft → click "Make it Formal" → text rewrites in place
4. In a Twitter/X compose box → click "Make it Punchy" → tweet version appears
5. Check memory: `curl http://localhost:8000/api/memory/user-model` → should show learned writing preferences after 5+ uses

**What to expect:**
- Works on Gmail, LinkedIn, Twitter/X, Notion, GitHub, any web form
- Does not activate on search bars or short `<input>` fields (less than 50 chars)
- Rewrite happens in under 3 seconds on llama3.2

**Tech required:**
```
None beyond TICKET-203 infrastructure
```

---

## Phase 3 — CLI + Mobile PWA

---

### TICKET-301: Command Line Interface (CLI)

**What to build:**
A Python CLI installable via pip that talks to the local Aria backend.

```bash
aria "what's on my schedule today"
aria --agent researcher "summarize the latest AI news"
aria --agent coder "explain this error" < traceback.txt
cat meeting_notes.txt | aria "extract action items"
aria memory add "my AWS account ID is 123456789"
aria memory search "AWS"
```

**Implementation:**

Create: `cli/`
```
cli/
  aria_cli/
    __init__.py
    main.py          # Click CLI entry point
    client.py        # HTTP client for backend API
    config.py        # ~/.aria/cli_config.json
  pyproject.toml
  README.md
```

Install:
```bash
pip install click rich httpx
```

Entry point (`main.py`):
```python
import click, httpx, sys
from rich.markdown import Markdown
from rich.console import Console

@click.command()
@click.argument("message", required=False)
@click.option("--agent", default=None)
@click.option("--server", default="http://localhost:8000")
def aria(message, agent, server):
    if not message:
        message = sys.stdin.read().strip()
    # POST to /api/chat
    # Stream response with rich formatting
```

**How to test:**
```bash
# Install in dev mode:
cd cli && pip install -e .

# Basic chat:
aria "what time is it in Tokyo?"
# Expected: Answer from general agent

# Piped input:
echo "def foo(x): return x*2" | aria --agent coder "add type hints"
# Expected: Returns typed version of function

# Memory:
aria memory add "my cat is named Mochi"
aria memory search "cat"
# Expected: Returns the memory entry

# Agent selection:
aria --agent researcher "latest news on quantum computing"
# Expected: Runs web_search tool, returns formatted news
```

**What to expect:**
- `aria` command available globally after `pip install -e .`
- Responses are rendered as Markdown in the terminal (rich library)
- Streaming output so you see the response as it generates
- Exit code 0 on success, 1 on error

**Tech required:**
```bash
pip install click rich httpx
# In cli/pyproject.toml:
# [project.scripts]
# aria = "aria_cli.main:aria"
```

---

### TICKET-302: Mobile PWA

**What to build:**
Convert the existing React frontend into a fully installable Progressive Web App.

**Changes to make:**
1. Add `public/manifest.json` with app metadata
2. Add service worker (`public/sw.js`) for offline caching
3. Add iOS-specific meta tags for full-screen mode
4. Add "Add to Home Screen" prompt detection
5. Configure Vite to output PWA assets

**Implementation:**

Install:
```bash
cd frontend && npm install vite-plugin-pwa
```

`vite.config.ts` addition:
```typescript
import { VitePWA } from 'vite-plugin-pwa'

plugins: [
  react(),
  VitePWA({
    registerType: 'autoUpdate',
    manifest: {
      name: 'Aria — Personal AI',
      short_name: 'Aria',
      theme_color: '#0f172a',
      background_color: '#0f172a',
      display: 'standalone',
      orientation: 'portrait',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
      ]
    },
    workbox: {
      runtimeCaching: [{
        urlPattern: /^https:\/\/fonts\.googleapis\.com/,
        handler: 'CacheFirst'
      }]
    }
  })
]
```

Add to `index.html`:
```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Aria">
<link rel="apple-touch-icon" href="/icon-192.png">
```

**Remote access setup (to reach home server from phone):**
```bash
# Option 1: Tailscale (recommended, free)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Your machine gets a stable *.ts.net URL — use that as API base from mobile

# Option 2: Cloudflare Tunnel
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
./cloudflared tunnel --url http://localhost:8000
```

**How to test:**
```bash
# Build PWA:
cd frontend && npm run build

# Serve build locally:
npx serve dist -p 3000

# Desktop: Open localhost:3000 in Chrome
# → Three-dot menu → "Install Aria" option should appear
# → Install → opens as standalone window (no browser chrome)

# Mobile: Open the Tailscale URL in Safari on iPhone
# → Share button → "Add to Home Screen"
# → Icon appears on home screen, opens full-screen

# Offline test:
# → Open app → disconnect WiFi → app still loads from cache
# → Type a message → should show "offline, queued" indicator
```

**What to expect:**
- App installs on iOS/Android home screen like a native app
- Full-screen, no browser bars
- Loads from cache when offline
- Push notifications (future ticket)

**Tech required:**
```bash
npm install vite-plugin-pwa workbox-window
# Icons: create 192x192 and 512x512 PNG icons
# Tailscale: free account at tailscale.com
```

---

### TICKET-303: Remote Access & Self-Hosted Cloud Option

**What to build:**
Allow users to optionally host Aria on a VPS and access it from anywhere, with end-to-end encryption and authentication.

**Implementation:**

Add authentication layer:
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

Add to `backend/app/routes/`:
- `auth.py` — JWT-based login: `POST /api/auth/login` returns bearer token
- Middleware: all routes require bearer token if `AUTH_ENABLED=true` in `.env`

Docker deployment target:
```bash
# On a VPS (Ubuntu 22.04 with 4GB RAM minimum):
git clone https://github.com/mfarooqii/AI-Personal-Assistant
cd AI-Personal-Assistant
docker compose up -d

# The docker-compose.yml already exists — just needs Ollama model pulling
docker exec aria-backend ollama pull llama3.2
docker exec aria-backend ollama pull nomic-embed-text
```

**How to test:**
```bash
# 1. Set AUTH_ENABLED=true in .env
# 2. Create a user:
curl -X POST http://localhost:8000/api/auth/register \
  -d '{"username": "me", "password": "secure_password_here"}'

# 3. Login:
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d '{"username":"me","password":"secure_password_here"}' | jq -r .token)

# 4. Use token:
curl http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "hello"}'
# Expected: 200 with response

# 5. Without token:
curl http://localhost:8000/api/chat -d '{"message": "hello"}'
# Expected: 401 Unauthorized
```

**What to expect:**
- All API endpoints return 401 without a valid token when auth is enabled
- Auth is opt-in (defaults to disabled for local use)
- Token expires after 7 days (configurable)

**Tech required:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
# VPS: DigitalOcean $12/month droplet (2vCPU, 2GB RAM) minimum
# For GPU inference: RunPod, vast.ai, or Lambda Labs for cost efficiency
```

---

## Phase 4 — Domain Packs

---

### TICKET-401: Medical Domain Pack

**What to build:**
A specialized agent mode and toolset for medical students and practitioners.

**New tools to add:**
- `drug_lookup(drug_name)` — queries OpenFDA API for drug info, interactions, dosing
- `icd_lookup(symptoms)` — ICD-10 code search
- `medical_calculator(type, params)` — BMI, GFR, CHADS2, Wells score, etc.
- `soap_note_generator(patient_input)` — structures free text into SOAP format

**New agent to add in `registry.py`:**
```python
AgentDefinition(
    name="medical",
    description="Medical assistant for clinical reference, drug lookup, SOAP notes, and case analysis",
    system_prompt="""You are a clinical AI assistant. Always include appropriate medical disclaimers.
    Do not make diagnoses. Provide evidence-based information only. When uncertain, recommend
    consulting a qualified healthcare professional.""",
    tools=["drug_lookup", "icd_lookup", "medical_calculator", "soap_note_generator", "web_search"],
    model_key="MODEL_REASONING"
)
```

**How to test:**
```bash
# Drug lookup:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What is the dose of metformin for a patient with CKD stage 3?"}'
# Expected: Agent routes to 'medical', calls drug_lookup, returns dose + renal adjustment

# SOAP note:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Generate a SOAP note: 45yo male, chest pain 2 hours, diaphoretic, BP 150/90"}'
# Expected: Formatted SOAP note with S/O/A/P sections

# Drug interaction:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Is there an interaction between warfarin and ibuprofen?"}'
# Expected: Yes, explanation of bleeding risk, evidence-based recommendation
```

**What to expect:**
- Medical agent triggered for any clinical-sounding query
- Drug info sourced from OpenFDA (no API key needed for basic queries)
- All responses include appropriate disclaimers
- SOAP notes are formatted and exportable

**Tech required:**
```bash
# OpenFDA API — free, no key needed for basic queries
# https://api.fda.gov/drug/label.json

pip install httpx  # already installed
```

---

### TICKET-402: Code Intelligence Pack

**What to build:**
Upgrade the coder agent with repo-level awareness — index a codebase and answer questions about it.

**New tools:**
- `index_repo(path)` — walks a directory, chunks files, stores embeddings
- `search_repo(query)` — semantic search across indexed codebase
- `explain_error(traceback)` — analyzes error with codebase context
- `generate_tests(function_code)` — writes unit tests for a function

**How to test:**
```bash
# Index this project:
curl -X POST http://localhost:8000/api/tools/index-repo \
  -d '{"path": "/home/farooqi/Documents/Repo/AI-Personal-Assistant/backend"}'

# Ask about the codebase:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Where is the web search tool defined and how does it work?"}'
# Expected: Finds backend/app/tools/web.py, explains the search function

# Error analysis:
echo "TypeError: slice indices must be integers" | \
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d @- <<< '{"message": "Explain this error in the context of my codebase: TypeError: slice indices must be integers"}'
# Expected: Identifies the exact line in web.py, explains the fix
```

**What to expect:**
- Indexing 1000 files takes ~2 minutes
- Repo search answers questions about architecture, functions, dependencies
- Error explanations reference actual code in the repo
- Generated tests follow the testing patterns already in the codebase

**Tech required:**
```bash
pip install pathspec  # for .gitignore-aware file walking
# Ollama nomic-embed-text already running
```

---

### TICKET-403: Creator Domain Pack

**What to build:**
Tools for content creators, writers, and social media professionals.

**New tools:**
- `repurpose_content(content, formats)` — converts one piece to multiple formats
- `brand_voice_analyze(samples)` — learns writing style from examples, stores in memory
- `seo_analyze(url_or_text)` — keyword density, readability score, improvement suggestions
- `social_post_generator(topic, platform, tone)` — generates platform-native posts

**How to test:**
```bash
# Repurpose content:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Repurpose this blog post into a Twitter thread and a LinkedIn post: [paste article]"}'
# Expected: Two outputs, platform-appropriate style and length

# Brand voice:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Learn my writing style from these 3 samples: [samples]"}'
# Then:
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Write a tweet about AI in my voice"}'
# Expected: Tweet matches the learned style, not default AI style
```

**What to expect:**
- Brand voice is stored in memory layer and persists across sessions
- Platform-native output (Twitter: under 280 chars with hashtags, LinkedIn: professional long-form)
- Repurposing preserves the key message while adapting format and tone

**Tech required:**
```bash
# No new dependencies
# Optionally: pip install readability-lxml for real SEO analysis
```

---

## Phase 5 — Patent & Enterprise

---

### TICKET-501: Patent Documentation

**What to build:**
Document the Temporal Episodic Compression system with enough technical specificity to support a provisional patent application.

**Deliverables:**
1. Technical specification document (10-15 pages)
2. System diagrams (architecture, data flow, retrieval algorithm)
3. Claims draft (at least 3 independent claims, 10+ dependent claims)
4. Prior art search results

**Process:**
1. File a **Provisional Patent Application** with USPTO (~$320 for micro-entity)
2. This gives 12 months of "patent pending" status
3. Within 12 months, file the full Non-Provisional application ($800-$2000 for micro-entity)
4. Full examination takes 2-3 years

**What to expect:**
- Provisional gives immediate IP protection for 12 months for ~$320
- "Patent pending" status can be used in marketing immediately
- Full patent if granted provides 20 years of IP protection

**Resources:**
```
USPTO Provisional Application: https://www.uspto.gov/patents/basics/types-patent-applications/provisional-application-patent
Patent search: https://patents.google.com
File yourself (pro se): https://www.uspto.gov/patents/apply
Filing fee (micro-entity, under $10M revenue): ~$320
```

---

## Running the Full Stack

```bash
# 1. Start backend:
cd /home/farooqi/Documents/Repo/AI-Personal-Assistant/backend
source venv/bin/activate
uvicorn app.main:app --port 8000

# 2. Start frontend:
cd /home/farooqi/Documents/Repo/AI-Personal-Assistant/frontend
npm run dev

# 3. Verify everything:
curl http://localhost:8000/api/health

# 4. Load the extension:
# Chrome → chrome://extensions → Load Unpacked → select browser-extension/

# 5. Install CLI:
cd /home/farooqi/Documents/Repo/AI-Personal-Assistant/cli
pip install -e .
aria "hello"
```

---

## Ticket Summary

| Ticket | Feature | Phase | Effort | Priority |
|---|---|---|---|---|
| TICKET-201 | Temporal Memory Compression | 2 | High | Critical |
| TICKET-202 | Semantic Memory Retrieval | 2 | Medium | Critical |
| TICKET-203 | Browser Extension Core | 2 | High | Critical |
| TICKET-204 | Browser Extension Write Mode | 2 | Medium | High |
| TICKET-301 | CLI | 3 | Medium | High |
| TICKET-302 | Mobile PWA | 3 | Medium | High |
| TICKET-303 | Remote Access + Auth | 3 | Medium | High |
| TICKET-401 | Medical Domain Pack | 4 | High | Medium |
| TICKET-402 | Code Intelligence Pack | 4 | High | Medium |
| TICKET-403 | Creator Domain Pack | 4 | Medium | Medium |
| TICKET-501 | Patent Documentation | 5 | Very High | High |
