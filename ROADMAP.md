# Aria Desktop — Product Roadmap & Ticket Backlog

> **Version:** 1.0 | **Updated:** April 2026 | **Status:** Active Development

---

## Vision

Aria is an **AI Operating System** — a desktop application that acts as a personal AI employee. It can browse any website, manage credentials, execute multi-step workflows, and be controlled remotely via Telegram or WhatsApp. It replaces Zapier, n8n, a browser agent, and a personal assistant in one local, private application.

**Core promise:** Say "email my boss I'm running late" from WhatsApp while away, and Aria executes it — opens Gmail, composes the email, sends it, and confirms back to you. No cloud. No subscriptions. Runs on your machine.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      ARIA DESKTOP (Electron)                     │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   React UI      │  │  Built-in       │  │  System Tray    │  │
│  │   Dashboard     │  │  Browser Tabs   │  │  Background     │  │
│  │   Chat / Logs   │  │  (Playwright)   │  │  Mode           │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           └───────────────────┬┘                    │           │
│                        ┌──────┴──────────────────────┘           │
│                        │   Electron Main Process                  │
│  ┌─────────────────────┴──────────────────────────────────────┐  │
│  │                   FastAPI Backend (embedded)                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │  15+     │  │ Workflow │  │ Cred.    │  │ Scheduler │  │  │
│  │  │  Agents  │  │  Engine  │  │  Vault🔒 │  │ (cron)    │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │ Browser  │  │  Dev/QA  │  │  Memory  │  │   Logs    │  │  │
│  │  │  Agent   │  │  Agent   │  │   RAG    │  │  Viewer   │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────┘
                                   │ Remote Command Channels
                    ┌──────────────┼──────────────┐
                    │              │              │
             ┌──────┴─────┐ ┌─────┴──────┐ ┌────┴───────┐
             │  Telegram  │ │  WhatsApp  │ │   Email    │
             │  Bot API   │ │ Cloud API  │ │  Webhooks  │
             └────────────┘ └────────────┘ └────────────┘
```

---

## Ticket Format

Each ticket follows this structure:
- **ARIA-XYZ** — unique ID (1xx = Phase 1, 2xx = Phase 2, etc.)
- **Priority**: P0 (blocker) | P1 (critical) | P2 (important) | P3 (nice-to-have)
- **Effort**: XS (< 2h) | S (half day) | M (1 day) | L (2–3 days) | XL (1 week)
- **Acceptance Criteria**: checkboxes that must ALL pass before ticket is closed
- **Test**: how to manually verify it works

---

## Current State (Already Built ✅)

| Area | Status | Notes |
|------|--------|-------|
| 15 AI Agents + Router | ✅ Done | Chat, research, code, memory, browser, etc. |
| Workflow Engine (10 workflows) | ✅ Done | Triggerable via chat keywords |
| Adaptive Dashboard (16 layouts) | ✅ Done | Auto-renders based on AI response |
| Playwright Browser Agent | ✅ Done | Screenshot-based, works but UX needs improvement |
| Gmail OAuth Integration | ✅ Done | Read/send/list emails |
| Scheduler | ✅ Done | Background task execution |
| Voice I/O (STT + TTS) | ✅ Done | Whisper + edge-tts |
| RAG Memory | ✅ Done | Semantic search over stored memories |
| Onboarding Wizard | ✅ Done | Profession-adaptive first-run setup |
| Chrome Extension | ✅ Done | Manifest V3, action executor via backend |
| System Logging | ✅ Done | `loguru` + `/api/logs` + LogsView in UI |

---

## Phase 1: Electron Desktop Shell

**Goal:** Wrap the existing web app in a native desktop application with system tray support and background execution.

**Why first:** Everything else (vault, tray notifications, remote execution) requires Electron's OS-level access.

---

### ARIA-101 · Electron Main Process

| Field | Value |
|-------|-------|
| Priority | P0 | 
| Effort | M |
| Dependencies | None |

**Goal:** Create the Electron app shell that loads our React frontend and embeds the FastAPI backend as a subprocess.

**What to build:**
- `electron/main.js` — creates `BrowserWindow`, spawns Python backend, polls `/api/health` before showing window
- `electron/preload.js` — exposes safe IPC bridge to renderer (no `nodeIntegration`)
- `electron/package.json` — Electron deps + start scripts
- Root `package.json` — `concurrently` script to run Vite + Electron together for dev
- Production: `electron-builder` config to package everything into `.deb`, `.AppImage`, `.dmg`, `.exe`

**Acceptance Criteria:**
- [ ] `npm run electron:dev` starts both Vite dev server and Electron window
- [ ] Electron window loads `http://localhost:3000` in dev mode
- [ ] Backend Python process is spawned as a child of Electron main
- [ ] Backend health endpoint is polled; window only shows after backend is ready
- [ ] Closing the Electron window also kills the Python backend subprocess
- [ ] App title shows "Aria" with correct icon

**Key files:**
- `electron/main.js`
- `electron/preload.js`
- `electron/package.json`
- `package.json` (root, new)

**Test:** Run `npm run electron:dev`. Aria window opens. Chat works. Closing window does not leave orphan Python processes.

---

### ARIA-102 · System Tray & Background Mode

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-101 |

**Goal:** Aria runs in the system tray and continues executing tasks when the window is closed.

**What to build:**
- Tray icon with context menu: Open Aria | New Task | Status | Quit
- Clicking "X" hides window instead of quitting
- Tray icon badge shows pending task count
- Right-click menu → "Status" shows current running agent/workflow
- `electron/tray.js` module

**Acceptance Criteria:**
- [ ] Closing window moves app to system tray (does not quit)
- [ ] Tray icon appears in taskbar/menubar
- [ ] Right-click shows context menu with Open, New Task, Quit
- [ ] "Open" re-shows the window
- [ ] "Quit" fully terminates app + backend
- [ ] Tray tooltip shows "Aria — X tasks running" or "Aria — idle"

**Key files:**
- `electron/tray.js`

**Test:** Close window. Tray icon visible. Tasks submitted before close continue executing. Open from tray.

---

### ARIA-103 · Native OS Notifications

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | S |
| Dependencies | ARIA-101 |

**Goal:** Aria sends native desktop notifications when tasks complete, errors occur, or reminders fire.

**What to build:**
- Electron `Notification` API wrapper in `electron/main.js`
- IPC channel: renderer sends `notify` event → main process fires OS notification
- Backend sends notification events to frontend via existing SSE/WebSocket
- Notification types: `task_complete`, `task_error`, `reminder`, `agent_message`

**Acceptance Criteria:**
- [ ] Task completion triggers OS notification with task summary
- [ ] Error in agent triggers "⚠️ Aria Error" notification
- [ ] Reminder triggers notification with reminder text + time
- [ ] Clicking notification opens/focuses Aria window
- [ ] Notifications work when Aria is in tray (window hidden)

**Test:** Submit a task from chat. Minimize window. Task completion fires notification. Clicking it brings back window.

---

### ARIA-104 · Auto-Start on Boot

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | XS |
| Dependencies | ARIA-101 |

**Goal:** Aria starts automatically when the user logs in, starting minimized to tray.

**What to build:**
- `electron/main.js`: use `app.setLoginItemSettings()` for cross-platform auto-start
- Settings toggle in the Aria UI (on/off)
- On first launch, ask user if they want auto-start
- `--hidden` CLI flag to start minimized to tray

**Acceptance Criteria:**
- [ ] Can toggle auto-start from Aria Settings view
- [ ] When enabled, Aria appears in system startup list
- [ ] Auto-started Aria begins in tray (no window shown immediately)
- [ ] Works on Linux (via `~/.config/autostart/aria.desktop`), macOS, Windows

**Test:** Enable auto-start. Log out and back in. Aria tray icon appears.

---

### ARIA-105 · Deep Link Handler (`aria://`)

| Field | Value |
|-------|-------|
| Priority | P3 |
| Effort | S |
| Dependencies | ARIA-101 |

**Goal:** Custom URL scheme `aria://` to open specific views or trigger tasks from external links.

**Examples:**
- `aria://task?run=daily_report` — triggers a workflow
- `aria://chat?msg=check my email` — opens chat with prefilled message
- `aria://workflow?id=xyz` — opens workflow detail

**Acceptance Criteria:**
- [ ] `aria://chat?msg=hello` opens Aria and sends "hello" to chat
- [ ] `aria://task?run=<workflow_id>` triggers the workflow
- [ ] Works from browser, terminal, other apps
- [ ] Handles app-not-running case (launches and then handles link)

---

### ARIA-106 · App Packaging & Installer

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | L |
| Dependencies | ARIA-101, ARIA-102 |

**Goal:** Single-click installer for Linux, macOS, and Windows that bundles Python, Ollama, and all dependencies.

**What to build:**
- `electron-builder` config in `electron/package.json`
- Bundle Python venv + all pip deps into the app package
- Include Ollama binary (or auto-download on first launch)
- Linux: `.deb` + `.AppImage`
- macOS: `.dmg` with codesigning
- Windows: `.exe` NSIS installer
- First-run wizard: downloads required Ollama models (llama3.2, etc.)

**Acceptance Criteria:**
- [ ] `npm run build:linux` produces `.AppImage` / `.deb`
- [ ] `.AppImage` runs on fresh Ubuntu 22.04 without any pre-installed deps
- [ ] First launch downloads and sets up Ollama models automatically
- [ ] App size < 2GB (use model download, not bundling)
- [ ] Uninstaller removes all app files (not user data at `~/.aria`)

---

## Phase 2: Built-in Browser Engine

**Goal:** Replace the screenshot-based browser with a real DOM-driven browser that agents can interact with natively. Multiple browser tabs, visible in the UI, agent-controlled.

---

### ARIA-201 · Browser Tab Manager

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | L |
| Dependencies | ARIA-101 |

**Goal:** Backend service that manages multiple Playwright browser contexts/tabs that agents can open, switch between, and close.

**What to build:**
- `backend/app/browser/tab_manager.py` — singleton managing a pool of Playwright pages
- Each tab: `{ id, url, title, screenshot_b64, dom_snapshot, active }`
- Endpoints: `POST /api/browser/tabs` (open), `DELETE /api/browser/tabs/{id}` (close), `GET /api/browser/tabs` (list), `PUT /api/browser/tabs/{id}/activate`
- Tab events streamed via SSE: `tab_opened`, `tab_navigated`, `tab_loaded`, `tab_closed`

**Acceptance Criteria:**
- [ ] Can open 3 simultaneous tabs to different URLs
- [ ] Each tab has an isolated browser context (different cookies/sessions)
- [ ] Tab list endpoint returns current URL, title, loading state
- [ ] Closing a tab frees its Playwright resources
- [ ] Tab manager survives individual tab crashes

**Test:** `POST /api/browser/tabs` with Gmail, Amazon, LinkedIn URLs. Confirm 3 tabs in list. Close one. Confirm 2 remain.

---

### ARIA-202 · Real DOM Browser Panel (No More Screenshots)

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | L |
| Dependencies | ARIA-201 |

**Goal:** Show the actual browser using Playwright's `cdp` (Chrome DevTools Protocol) embedded in the Electron window, not base64 screenshots. Fast, real, native.

**What to build:**
- In Electron: use `<webview>` tag or `BrowserView` to embed an actual Chromium window in the UI
- `electron/browser-view.js` — manages `BrowserView` instances, positions them behind React panels
- Frontend sends IPC commands: `BROWSER_NAVIGATE`, `BROWSER_BACK`, `BROWSER_FORWARD`, `BROWSER_CLOSE`
- Browser view renders at real speed (no screenshot latency)
- React UI overlays controls on top of the browser view

**Acceptance Criteria:**
- [ ] Requesting a URL shows real browser rendering (not a screenshot)
- [ ] Page interactions (click, scroll, type) work in real-time
- [ ] Back/forward navigation works
- [ ] Page finishes loading before agents try to interact
- [ ] Multiple tabs can be switched without re-loading

**Test:** Navigate to YouTube. Video plays. Scroll works. Type in search box. No screenshot delays.

---

### ARIA-203 · Browser Tabs UI in Sidebar

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-201, ARIA-202 |

**Goal:** Show open browser tabs in the Aria sidebar so users can switch between them.

**What to build:**
- New section in `Sidebar.tsx`: "Browser Tabs" with tab list
- Each tab shows: favicon, title (truncated), close button
- Active tab highlighted
- "New Tab" button at top
- Tabs auto-update via polling the `/api/browser/tabs` endpoint

**Acceptance Criteria:**
- [ ] Sidebar shows all open tabs with titles
- [ ] Clicking a tab switches the browser view to that tab
- [ ] Closing from sidebar closes the tab
- [ ] Tab title updates after navigation
- [ ] Empty state message when no tabs open

---

### ARIA-204 · Parallel Agent Browser Execution

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-201 |

**Goal:** Multiple agents can each use their own browser tab simultaneously (e.g., one agent checking Gmail while another searches Amazon).

**What to build:**
- Tab manager assigns a tab to each agent task
- Agent specifies whether it needs an existing tab or a new isolated context
- Parallel workflow steps can run browser operations concurrently
- Queue system: if max tabs (configurable, default 5) reached, new tasks wait

**Acceptance Criteria:**
- [ ] Two simultaneous browser tasks run without interfering
- [ ] Each agent tab holds its own session/cookies
- [ ] `MAX_BROWSER_TABS=5` config setting respected
- [ ] Queued tasks get assigned a tab as soon as one frees up
- [ ] No race conditions in tab assignment (tested with 10 concurrent tasks)

---

### ARIA-205 · Login Detection & Credential Prompt

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-201, ARIA-301 |

**Goal:** When a browser agent detects a login page, it pauses and either uses the credential vault or asks the user.

**What to build:**
- `backend/app/browser/detect.py` gets a `detect_login_form(page_state)` function
- Login detected → agent pauses + fires `LOGIN_REQUIRED` event to frontend
- Frontend shows modal: "Aria needs to log in to [site]. Use saved credentials? [Yes] [Enter manually] [Skip]"
- If vault has credentials → auto-fill and proceed
- If not → user types credentials (sent securely via IPC, never logged)

**Acceptance Criteria:**
- [ ] Login page on GitHub, Google, LinkedIn, bank sites correctly detected
- [ ] Vault credentials are auto-filled without user interaction
- [ ] Manual entry prompt appears when no vault entry exists
- [ ] "Skip" cancels the sub-task and returns to agent planner
- [ ] Credentials are never stored in chat history or logs

---

### ARIA-206 · File Download Handler

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | S |
| Dependencies | ARIA-201 |

**Goal:** Browser agent can download files and make them available to the user and to other agents (e.g., download a PDF invoice, pass it to the document reader agent).

**What to build:**
- Playwright `page.on('download')` handler in `tab_manager.py`
- Downloads saved to `~/.aria/downloads/` with timestamp prefix
- Download event pushed to frontend: filename, size, path
- Frontend shows download notification with "Open" button
- `file_path` available to agents via `get_last_download()` tool

**Acceptance Criteria:**
- [ ] Navigating to a download URL saves file to `~/.aria/downloads/`
- [ ] Frontend shows download toast with filename
- [ ] Agent can access downloaded file path in next step
- [ ] Large files (>100MB) don't block the event loop

---

## Phase 3: Credential Vault

**Goal:** An AES-256-GCM encrypted credential store that agents can access only with explicit user authorization via a keyword/passphrase. Zero plaintext at rest.

---

### ARIA-301 · Vault Data Model & Encryption Engine

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | None |

**Goal:** Design and implement the encrypted vault storage using `cryptography` (Fernet/AES-GCM).

**What to build:**
- `backend/app/vault/crypto.py` — AES-256-GCM encrypt/decrypt using user's master key
- `backend/app/vault/models.py` — SQLAlchemy model: `VaultEntry(id, site, username_enc, password_enc, notes_enc, created_at, updated_at)`
- Master key is **never stored** — derived from passphrase using PBKDF2-HMAC-SHA256 with stored salt
- `backend/app/vault/manager.py` — CRUD operations that require decrypted master key in memory
- In-memory key cache with 15-minute TTL auto-lock
- `backend/app/routes/vault.py` — REST API

**Acceptance Criteria:**
- [ ] Database column values are ciphertext (verified by reading SQLite directly)
- [ ] Wrong passphrase returns `401` with generic "Invalid passphrase" message
- [ ] Master key is never written to disk, logs, or any persistent storage
- [ ] Vault auto-locks after 15 minutes of inactivity (configurable)
- [ ] PBKDF2 uses minimum 100,000 iterations

**Test:** Add a credential. Open SQLite DB directly with `sqlite3`. Verify column values are hex/base64 ciphertext, not plaintext.

---

### ARIA-302 · Vault UI — Add, View, Delete

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-301 |

**Goal:** A secure credential manager view in the Aria UI.

**What to build:**
- `frontend/src/components/VaultView.tsx`
- Unlock screen: passphrase input (never visible, masked) → POST `/api/vault/unlock`
- Credential list: site icon, username (masked), last-used timestamp
- Add credential form: site, username, password (masked), notes
- Delete with confirmation dialog
- "Copy password" button (copies to clipboard, clears after 30s)
- Auto-lock button

**Acceptance Criteria:**
- [ ] Vault shows locked state until passphrase entered
- [ ] Passwords are masked by default; toggle reveals plaintext
- [ ] "Copy password" works and clears clipboard after 30 seconds
- [ ] Deleting a credential requires typing "DELETE" to confirm
- [ ] Vault view shows "Locked" badge in sidebar when locked

---

### ARIA-303 · Agent Vault Access with User Confirmation

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-301, ARIA-205 |

**Goal:** Define the secure protocol by which agents can request credentials from the vault.

**Protocol:**
1. Agent needs credentials for `linkedin.com`
2. If vault is locked → fire `VAULT_ACCESS_REQUEST` event to frontend
3. Frontend shows modal: "Aria wants to access your LinkedIn credentials to log in. Allow? [Yes, this time] [Always for this site] [Never]"
4. User approves → vault unlocks for that request only → agent gets credentials → vault re-locks
5. Full audit log of all vault access requests

**Acceptance Criteria:**
- [ ] Agent cannot access vault without explicit `VAULT_ACCESS_REQUEST` flow
- [ ] "Always for this site" preference is stored per-domain
- [ ] "Never" blocks that domain permanently (stored in vault settings)
- [ ] All access requests logged to audit table with timestamp, agent, domain, decision
- [ ] Audit log visible in Vault UI

---

### ARIA-304 · Remote Vault Unlock via Telegram PIN

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-301, ARIA-401 |

**Goal:** When Aria needs credentials while executing a remote task (triggered via Telegram), it can message the user for their vault PIN without exposing the passphrase.

**Protocol:**
1. Remote task requires vault access
2. Aria sends Telegram message: "I need to access your [site] credentials to complete this task. Reply with your vault PIN to authorize."
3. User replies with vault PIN (separate 4-6 digit PIN from passphrase)
4. Vault unlocks for that one request (60-second window)
5. Aria completes task and confirms

**Acceptance Criteria:**
- [ ] Vault has separate "remote PIN" (4-6 digits) distinct from the full passphrase
- [ ] PIN accepted only once per request (not reusable)
- [ ] 3 wrong PINs → remote access locked for 1 hour
- [ ] PIN request times out after 5 minutes if no response
- [ ] Full remote vault access attempt is audited

---

### ARIA-305 · Vault Import from Chrome / 1Password / Bitwarden

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | M |
| Dependencies | ARIA-302 |

**Goal:** One-click import from Chrome's exported CSV, 1Password CSV, or Bitwarden JSON.

**Acceptance Criteria:**
- [ ] Chrome CSV import works (headers: name, url, username, password)
- [ ] Bitwarden JSON import works
- [ ] Duplicate detection (same site + username → prompt to overwrite)
- [ ] Import preview shows count + duplicates before committing
- [ ] Imported credentials are immediately encrypted at rest

---

## Phase 4: Remote Command Channels

**Goal:** Control Aria from anywhere via Telegram or WhatsApp. Send a message, Aria executes the task on your home computer, sends back the result.

---

### ARIA-401 · Telegram Bot Setup & Message Handler

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-101 (running backend) |

**Goal:** A Telegram bot that receives messages and routes them to Aria's agent system.

**What to build:**
- `backend/app/remote/telegram.py` — `python-telegram-bot` async polling
- Bot token stored in `~/.aria/.env` (never in code)
- Incoming message → same pipeline as chat API (`POST /api/chat`)
- Response streamed back to Telegram as it's generated
- Setup wizard: `GET /api/remote/telegram/setup` returns bot setup instructions

**Acceptance Criteria:**
- [ ] Message to Telegram bot triggers Aria agent
- [ ] Response sent back to same Telegram chat
- [ ] Long responses are split into multiple Telegram messages (4096 char limit)
- [ ] Bot shows "Aria is thinking..." typing status while processing
- [ ] Bot token stored securely (not in git, not in logs)

**Test:** Set up bot with BotFather. Send "What's the weather like?". Receive response in < 10 seconds.

---

### ARIA-402 · Telegram Remote Task Execution

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-401 |

**Goal:** Execute complex multi-step tasks (with browser, file system, APIs) triggered from Telegram.

**What to build:**
- Task queuing: remote tasks go into the scheduler with `source=telegram, reply_to=chat_id`
- Live progress updates: every major step, send a status message to Telegram
- Result delivery: final result sent as text/image/file
- Supported task types: email, browser browsing, code execution, file operations, web search

**Acceptance Criteria:**
- [ ] "Search Amazon for noise-cancelling headphones under $100" → Aria browses → Telegram gets results
- [ ] "Email my boss I'm running late" → Aria sends email → Telegram confirms
- [ ] Progress messages sent at each step (e.g., "Opening Gmail...", "Composing email...", "Sent!")
- [ ] If task fails, user gets a clear error message (not a stack trace)
- [ ] Tasks survive Telegram disconnection (run to completion, deliver when reconnected)

---

### ARIA-403 · Security Layer — PIN Confirmation for Sensitive Actions

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-401 |

**Goal:** Sensitive actions triggered remotely require PIN confirmation to prevent unauthorized use.

**Sensitive actions:** Send email, make purchases, delete files, execute shell commands, access vault, git push.

**Protocol:**
1. Command received via Telegram
2. If action is sensitive → Aria replies: "This action requires confirmation. Reply with your PIN."
3. User replies with PIN (4-6 digit, set during onboarding)
4. Valid PIN → execute action
5. Invalid PIN → reject + notify

**Acceptance Criteria:**
- [ ] Email sending requires PIN
- [ ] Non-sensitive queries (search, read email) don't require PIN
- [ ] PIN is set during onboarding or in Settings
- [ ] 3 wrong PINs block remote access for 30 minutes
- [ ] PIN confirmation request expires after 2 minutes

---

### ARIA-404 · WhatsApp Cloud API Integration

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-401 (same pattern as Telegram) |

**Goal:** Same remote control capability via WhatsApp using the free Meta Cloud API.

**What to build:**
- `backend/app/remote/whatsapp.py` — Meta Cloud API webhook receiver + message sender
- Webhook endpoint: `POST /api/remote/whatsapp/webhook`
- Verification endpoint: `GET /api/remote/whatsapp/webhook` (Meta verification challenge)
- Same message routing as Telegram
- Setup wizard with ngrok/cloudflare tunnel instructions

**Acceptance Criteria:**
- [ ] Meta webhook verification passes
- [ ] Incoming WhatsApp messages trigger Aria agents
- [ ] Responses sent back to same WhatsApp number
- [ ] Supports text responses (not limited to buttons/templates for user-initiated conversations)
- [ ] Works with free tier (1000 conversations/month)

---

### ARIA-405 · Remote Status Dashboard (Telegram Commands)

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | S |
| Dependencies | ARIA-401 |

**Goal:** Special bot commands for checking Aria's status and managing running tasks remotely.

**Commands:**
- `/status` — shows running tasks, agent states, system health
- `/tasks` — lists last 10 tasks with status
- `/cancel <task_id>` — cancels a running task
- `/logs` — sends last 20 log lines
- `/models` — shows installed Ollama models
- `/pause` — pauses all Aria background processing

**Acceptance Criteria:**
- [ ] All commands respond within 3 seconds
- [ ] `/status` shows CPU, memory, running tasks count
- [ ] `/cancel` stops a task mid-execution if possible
- [ ] `/logs ERROR` filters to error-level only

---

### ARIA-406 · File Sharing via Remote Channels

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | M |
| Dependencies | ARIA-401 |

**Goal:** User can send files to Aria via Telegram (photos, PDFs, audio), and Aria can send files back (reports, screenshots, code).

**Examples:**
- Send a PDF invoice → Aria extracts amounts, categorizes, adds to expense tracker
- Ask "summarize this document" + attach PDF → Aria reads and summarizes
- Ask for a screenshot of a webpage → Aria sends the screenshot back

**Acceptance Criteria:**
- [ ] Telegram photo attachment triggers vision agent
- [ ] PDF attachment triggers document reader agent
- [ ] Audio message triggers STT + chat agent
- [ ] Aria can send files back (PDFs, images, CSV reports) up to 50MB

---

## Phase 5: Visual Workflow Builder

**Goal:** A drag-and-drop workflow editor where users build complex multi-step automations. Like n8n, but AI-powered — describe what you want, it builds the nodes.

---

### ARIA-501 · Workflow DAG Data Model

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | None (extends existing workflow engine) |

**Goal:** Extend the existing workflow engine to support a proper directed acyclic graph (DAG) with conditional branching.

**Node types:**
- `trigger` — schedule, webhook, chat command, manual
- `browser_action` — navigate, click, extract, fill form
- `api_call` — HTTP GET/POST/PUT with headers and body
- `email` — send/read Gmail, SMTP
- `code` — execute Python snippet
- `ai_decision` — LLM decides which branch to take
- `file_op` — read, write, move, delete files
- `notification` — desktop, Telegram, WhatsApp, email
- `wait` — delay or wait for condition
- `transform` — map/filter data between nodes

**Acceptance Criteria:**
- [ ] DAG model stored in SQLite as JSON
- [ ] Cycles detected and rejected
- [ ] Node outputs typed (string, number, list, dict, file_path)
- [ ] Conditional edges: `if output.contains("fail") → error_branch`
- [ ] Workflow execution engine walks the DAG respecting dependencies

---

### ARIA-502 · Drag-and-Drop Workflow Canvas

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | XL |
| Dependencies | ARIA-501 |

**Goal:** Visual workflow editor using React Flow (or similar) with the node types from ARIA-501.

**What to build:**
- `frontend/src/components/WorkflowBuilderView.tsx`
- Node palette on the left (drag to canvas)
- Canvas: connect nodes with edges, configure each node by clicking
- Node config modals: each node type has its own config UI
- Toolbar: Save, Run, Duplicate, Delete, Export JSON, Import JSON
- Run history panel: last 10 executions with status, duration, errors

**Acceptance Criteria:**
- [ ] Can drag any node type onto the canvas
- [ ] Connecting nodes via edges creates data flow
- [ ] Each node has a config modal with relevant fields
- [ ] "Run" executes the workflow and shows live step-by-step progress
- [ ] Failed nodes highlighted in red with error message
- [ ] Export outputs valid JSON that can be re-imported

---

### ARIA-503 · AI Workflow Generator

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-501 |

**Goal:** User describes workflow in plain language; AI generates the DAG automatically.

**Example:**
> "Every day at 9am, check Shopify for new orders, get payment status from Stripe, update a Google Sheet, and email me a summary."

→ AI generates 5 nodes: Trigger(schedule), Browser(Shopify), Browser(Stripe), Browser(Sheets), Email

**What to build:**
- `POST /api/workflows/generate` — takes description, returns DAG JSON
- Prompt template that knows all node types and their config schemas
- Frontend: "Describe your workflow..." input above the canvas
- Validate generated DAG before adding to canvas

**Acceptance Criteria:**
- [ ] Simple 3-step workflow generated correctly from description
- [ ] Generated workflow is valid (no invalid node types or disconnected nodes)
- [ ] User can edit generated nodes after generation
- [ ] Generation takes < 10 seconds
- [ ] Falls back gracefully if AI produces invalid JSON

---

### ARIA-504 · Workflow Templates Library

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | M |
| Dependencies | ARIA-502 |

**Goal:** Pre-built workflow templates for common use cases, one-click to add to canvas.

**Templates to include:**
1. Daily Sales Report (Shopify → Stripe → Google Sheets → Email)
2. Job Application Tracker (LinkedIn → Airtable/Sheet → Email alert)
3. News Digest (RSS feeds → AI summary → WhatsApp)
4. Expense Tracker (Bank site → categorize → spreadsheet)
5. GitHub PR Reviewer (new PR → AI review → comment on PR)
6. Social Media Scheduler (content queue → post to Twitter/LinkedIn)
7. Customer Support Triage (email inbox → AI classify → route to agent)
8. Code Deploy Monitor (GitHub → build status → Slack/Telegram notification)
9. Price Alert (Amazon product → check price → notify if drops)
10. Health Metrics Tracker (wearable site → extract data → health dashboard)

**Acceptance Criteria:**
- [ ] Template library shows 10+ templates with icon, name, description
- [ ] One click adds template to canvas (pre-configured)
- [ ] Each template has a "preview" showing its nodes
- [ ] User can modify template nodes before saving

---

### ARIA-505 · Workflow Execution History & Replay

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | ARIA-502 |

**Goal:** Full execution history for every workflow run, with the ability to see what each node did and replay from any node.

**What to build:**
- `WorkflowRun` DB model: `id, workflow_id, started_at, completed_at, status, steps_json`
- Each step logged: input, output, duration, error
- History view in UI: list of runs, click to see step-by-step replay
- "Replay from Step" button: re-run from a specific node (useful for debugging)

**Acceptance Criteria:**
- [ ] Every workflow run creates a `WorkflowRun` record
- [ ] Each step's input and output are stored
- [ ] UI shows run history with duration and status
- [ ] "Replay from Step N" works without re-running earlier steps
- [ ] Runs older than 30 days are auto-archived

---

### ARIA-506 · Export & Import Workflows as JSON

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | S |
| Dependencies | ARIA-501 |

**Goal:** Users can export workflows to JSON files and share/import them.

**Acceptance Criteria:**
- [ ] "Export" button downloads a `.aria-workflow.json` file
- [ ] "Import" button accepts `.aria-workflow.json` and adds to library
- [ ] Exported JSON is human-readable and well-commented
- [ ] Import validates schema before adding (no malformed workflows)
- [ ] Workflows can be shared between different Aria installations

---

## Phase 6: Quality, Testing & Release

---

### ARIA-601 · Integration Test Suite

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | L |
| Dependencies | All Phase 1–5 |

**Goal:** Automated `pytest` integration tests for all major agent workflows.

**Test coverage:**
- Each of the 15 agents receives a test message and returns expected structure
- Workflow engine executes each of the 10 built-in workflows end-to-end
- Browser agent navigates to a test site and extracts expected data
- Credential vault: add, retrieve, delete, wrong-passphrase rejection
- Remote channel: mock Telegram message → correct agent execution

**Acceptance Criteria:**
- [ ] `pytest backend/tests/` passes with zero failures on a fresh setup
- [ ] Tests don't require internet access (mock external APIs)
- [ ] Tests complete in under 2 minutes
- [ ] Coverage report shows > 70% line coverage

---

### ARIA-602 · E2E Frontend Tests

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | M |
| Dependencies | ARIA-101 |

**Goal:** Playwright-based E2E tests for the React UI.

**Test cases:**
- Onboarding flow completes successfully
- Sending a chat message shows a response
- Browser panel opens when "check my email" is requested
- Log viewer shows new entries after a request
- Vault locks after timeout

---

### ARIA-603 · Performance Benchmarks

| Field | Value |
|-------|-------|
| Priority | P2 |
| Effort | M |
| Dependencies | None |

**Goal:** Establish performance baselines and catch regressions.

**Benchmarks:**
- Chat response first token: < 500ms
- Agent routing (detect + route): < 200ms
- Browser page load to first action: < 3s
- Vault encrypt/decrypt: < 10ms
- Workflow trigger to first step: < 1s

---

### ARIA-604 · Security Audit

| Field | Value |
|-------|-------|
| Priority | P0 |
| Effort | M |
| Dependencies | ARIA-301, ARIA-401 |

**Goal:** Systematic review of authentication, encryption, and injection vulnerabilities.

**Checklist:**
- [ ] No plaintext secrets in logs (`backend/app/utils/logger.py` filters passwords)
- [ ] Remote channel PIN brute-force protection (rate limiting)
- [ ] Vault PBKDF2 iterations verified
- [ ] No shell injection in tool executor (all subprocess calls use list args, never `shell=True`)
- [ ] CORS restricted to `localhost` only in production build
- [ ] All SQL uses parameterized queries (no f-string SQL)
- [ ] Telegram webhook verified with secret token

---

### ARIA-605 · Error Recovery & Graceful Degradation

| Field | Value |
|-------|-------|
| Priority | P1 |
| Effort | M |
| Dependencies | None |

**Goal:** Every agent and workflow step handles errors gracefully and can retry with exponential backoff.

**What to build:**
- Retry decorator with exponential backoff for HTTP calls and browser actions
- Dead letter queue for failed tasks (retry up to 3 times, then archive)
- Graceful error messages in UI (not raw Python tracebacks)
- Network timeout handling for Ollama calls
- Browser page crash recovery (reopen tab and restart step)

---

## Milestones

| Milestone | Tickets | Target | Outcome |
|-----------|---------|--------|---------|
| **M1: Desktop Alpha** | ARIA-101, 102, 103 | Week 1 | App runs as native desktop in system tray |
| **M2: Real Browser** | ARIA-201, 202, 203, 205 | Week 2 | Full DOM browser, login detection, multi-tab |
| **M3: Secure Vault** | ARIA-301, 302, 303 | Week 2 | Encrypted credentials, agent-accessible |
| **M4: Remote Control** | ARIA-401, 402, 403 | Week 3 | Control Aria from Telegram anywhere |
| **M5: WhatsApp** | ARIA-404, 406 | Week 3 | WhatsApp command channel + file sharing |
| **M6: Workflow Builder** | ARIA-501, 502, 503 | Week 4-5 | Visual n8n-style builder |
| **M7: Templates** | ARIA-504, 505 | Week 5 | 10 pre-built workflow templates |
| **M8: Release Ready** | ARIA-106, 601, 604 | Week 6 | Packaged installer, passing tests, security audit |

---

## Testing Strategy

### How to Test Each Phase

**Phase 1 — Shell:**
```bash
# After ARIA-101:
npm run electron:dev  # Should open Aria in a window, not browser
ps aux | grep uvicorn  # Should show backend running as child process

# After ARIA-102:
# Close window → app stays in tray
# Right-click tray → context menu appears
```

**Phase 2 — Browser:**
```bash
# After ARIA-201:
curl -X POST http://localhost:8000/api/browser/tabs -d '{"url":"https://google.com"}'
curl http://localhost:8000/api/browser/tabs  # Should list 1 tab

# After ARIA-205:
# Ask chat: "log into GitHub"
# Should see login detection modal in UI
```

**Phase 3 — Vault:**
```bash
# After ARIA-301:
# Add a credential via UI
sqlite3 ~/.aria/aria.db "SELECT password_enc FROM vault_entries LIMIT 1;"
# Output should be base64 ciphertext, NOT the actual password
```

**Phase 4 — Remote:**
```bash
# After ARIA-401:
# Send message to your Telegram bot: "what time is it?"
# Should receive response within 10 seconds

# Security test:
# Send "send an email to test@example.com saying hello"
# Should receive PIN confirmation request before sending
```

**Phase 5 — Workflows:**
```bash
# After ARIA-502:
# Build a 3-node workflow: Trigger → Web Search → Email
# Click Run → should see step-by-step execution in UI
# Check workflow run history
```

### Logging During Testing

The log viewer (`/api/logs`) shows real-time agent execution. Always have it open in a separate window when testing. Filter by `ERROR` level first to spot failures quickly.

---

## Quick Start for Next Session

```bash
# Start everything
cd /home/farooqi/Documents/Repo/AI-Personal-Assistant
./start.sh

# Run backend only (for dev)
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Run frontend only
cd frontend && npm run dev

# Check logs
curl 'http://localhost:8000/api/logs?level=ERROR&limit=50' | python3 -m json.tool

# Run tests (once written)
cd backend && pytest tests/ -v
```
