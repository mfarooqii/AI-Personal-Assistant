# Aria — Phase 1 Tickets
> **Goal:** User dictates a task → Aria executes it in a live visible browser → reports back with artifacts
> **Two flagship demos:** Gmail email summary | Full coder pipeline with QA video

---

## Status Legend
✅ Done &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ⏳ Pending &nbsp;|&nbsp; 🔒 Blocked

---

## EPIC A — Electron Desktop App

### ✅ ARIA-P1-A1: Electron App Scaffold
**Priority:** P0 — Foundation for everything  
**Dependencies:** None  
**Status: DONE**

**What:** Create `electron/` directory. Electron main process spawns FastAPI backend, waits for health check, shows a BrowserWindow with the React UI.

**Files:**
- `electron/main.js` — main entry, spawns uvicorn, creates BrowserWindow
- `electron/preload.js` — IPC context bridge
- Root `package.json` — `electron:dev`, `electron:build` scripts

**Acceptance Criteria:**
- [x] `npm run electron:dev` opens a desktop window with Aria UI
- [x] FastAPI starts automatically on port 8000, killed when window closes
- [x] System tray icon: Open / Quit
- [x] Window title: "Aria"
- [x] Health check poll before showing window (no blank flash)

---

### ✅ ARIA-P1-A2: Live Browser Panel (BrowserView)
**Priority:** P0  
**Dependencies:** ARIA-P1-A1  
**Status: DONE**

**What:** Embed real Chromium in the Electron window using `BrowserView`. Backend browser agent sends IPC commands (`NAVIGATE`, `CLICK`, `TYPE`) → Electron executes on the live visible browser. Persistent user profile at `~/.aria/browser_data/`.

**Files:**
- `electron/browser-view.js` — BrowserView lifecycle + IPC command handlers
- `frontend/src/components/BrowserPanel.tsx` — dual-mode: Electron BrowserView + Web WebSocket fallback
- `electron/main.js` — HTTP IPC server on :8001, React IPC handlers
- `backend/app/browser/electron_bridge.py` — Python → Electron HTTP client

**Acceptance Criteria:**
- [x] Toggle button shows/hides browser panel
- [x] Aria navigating a URL shows live real browser (not screenshot)
- [x] User can manually click/type in the browser at any time
- [x] Sessions persist between restarts (Gmail stays logged in)
- [x] Layout: chat left, browser right

---

### ⏳ ARIA-P1-A3: Mid-Task Voice & Chat Interruption
**Priority:** P1  
**Dependencies:** ARIA-P1-A2

**What:** User can speak or type while a browser task is running. Commands like "stop", "go back", "click the second result" are interpreted and executed immediately.

**Files:**
- `backend/app/browser/agent.py` — add `interrupt_queue: asyncio.Queue` to action loop
- `backend/app/routes/chat.py` — route messages to interrupt queue if task in progress
- `frontend/src/components/ChatView.tsx` — "Task in progress" indicator + interrupt input

**Acceptance Criteria:**
- [ ] "Stop" halts task immediately
- [ ] "Go back" navigates back in browser
- [ ] "Click the second link" is parsed and executed
- [ ] Interruption acknowledged in chat
- [ ] Normal chat resumes after interruption

---

### ✅ ARIA-P1-A4: Chat-to-Browser Task Execution
**Priority:** P0 — Core demo capability  
**Dependencies:** ARIA-P1-A2, ARIA-P1-C1  
**Branch:** EPIC-A

**What:** Wire the chat interface directly to the browser agent so users can type natural-language instructions and watch Aria complete them live. Fixes streaming-mode browser routing (currently disabled), expands intent detection patterns, streams agent progress back to chat via SSE, and validates the best local model for browser control.

**The gap today:** `detect_browser_intent` fires only for non-streaming requests and only matches a narrow set of keywords. Tasks like "go to github.com and star this repo" or "sign up on Linear for me" are silently routed to the regular chat agent instead.

**Model selection:** `qwen2.5:7b` as `MODEL_BROWSER`
- Best local model for accessibility-tree navigation + structured JSON tool calls
- Outperforms llama3.2 on multi-step web tasks in benchmarks
- Fallback: `llama3.2` (already default) if qwen2.5 not pulled
- Set in `.env`: `MODEL_BROWSER=qwen2.5`

**Files:**
- `backend/app/browser/detect.py` — expand patterns to catch "go to X and do Y", "sign up on X", "complete X on website", generic URL detection
- `backend/app/routes/chat.py` — fix browser routing for streaming mode; stream browser agent status events through SSE instead of blocking on WebSocket
- `backend/app/browser/agent.py` — emit agent status messages via `electron_bridge.send_status()` so user sees live progress in chat
- `backend/app/config.py` — ensure `MODEL_BROWSER` default is `qwen2.5` with `llama3.2` fallback

**Acceptance Criteria:**
- [x] "Go to google.com and search for X" → browser opens, search runs, result shown
- [x] "Sign up on [site] with my email [x]" → browser opens, form filled, account created
- [x] "Go to github.com/[repo] and give it a star" → browser navigates and stars
- [x] Agent status shown in chat: "Navigating to…", "Clicking sign up…", "Filling form…"
- [x] Works in streaming mode (default chat mode)
- [x] Browser panel activates automatically (user doesn't need to open it manually)
- [ ] If task fails: clear error message in chat explaining what went wrong
- [ ] Tested with 3 real-world browser tasks, all complete without human intervention

---

## EPIC B — Gmail Intelligence

### ⏳ ARIA-P1-B1: Gmail OAuth Setup Flow
**Priority:** P1  
**Dependencies:** ARIA-P1-A1

**What:** One-click Gmail connection. User says "connect my Gmail" → Aria shows auth link → browser opens → user authorizes → token stored.

**Files:**
- `backend/app/routes/integrations.py` — add `/api/integrations/gmail/auth-url` + `/callback`
- `frontend/src/components/views/IntegrationsView.tsx` — shows connected services

**Acceptance Criteria:**
- [ ] "Connect my Gmail" → clickable auth link appears in chat
- [ ] After authorization, `~/.aria/google_token.json` is saved
- [ ] Aria confirms: "Gmail connected!"
- [ ] Re-auth works without breaking existing token

---

### ⏳ ARIA-P1-B2: Gmail Summary Workflow
**Priority:** P1  
**Dependencies:** ARIA-P1-B1

**What:** Register `gmail_summary` workflow. Filters important+unread emails, reads full content, AI-summarizes each, renders in EmailInboxView. Uses Gmail API (no browser needed).

**Files:**
- `backend/app/workflows/__init__.py` — add `gmail_summary` workflow definition

**Workflow DAG:**
```
Step 1 [TOOL]   gmail_list(query="is:unread is:important", max=20) → email_list
Step 2 [AGENT]  general — summarize each email, flag action items  → summaries
Step 3 [LAYOUT] email_inbox
```

**Acceptance Criteria:**
- [ ] "Summarize my important unread emails" → workflow triggers
- [ ] Only unread + important emails returned (not full inbox)
- [ ] Each email: sender, subject, 1-sentence AI summary, action item flag
- [ ] Renders as EmailInboxView (not plain text)
- [ ] If not authorized: "I need to connect your Gmail first" + setup link

---

## EPIC C — Browser Automation

### ✅ ARIA-P1-C1: Stealth Browser + Persistent Profile
**Priority:** P0  
**Dependencies:** None  
**Status: DONE**

**What:** Replace vanilla Playwright with `patchright` (stealth-patched fork). Use `launch_persistent_context` with `~/.aria/browser_data/` so sessions survive restarts.

**Files:**
- `backend/app/browser/engine.py` — swap playwright → patchright, persistent context
- `backend/requirements.txt` — add `patchright`, remove `playwright`
- `setup.sh` — add `patchright install chromium`

**Acceptance Criteria:**
- [x] `https://bot.sannysoft.com` shows NO automation flags
- [x] Gmail login survives app restart
- [x] All existing browser agent functionality preserved
- [x] `setup.sh` handles patchright install automatically

---

### ⏳ ARIA-P1-C2: Credential Vault
**Priority:** P1  
**Dependencies:** None (standalone module)

**What:** AES-256-GCM encrypted SQLite credential store. PBKDF2 key derivation from master passphrase. Per-request access approval.

**Files:**
- `backend/app/vault/crypto.py` — PBKDF2 key derivation + AES-256-GCM
- `backend/app/vault/store.py` — encrypted SQLite CRUD
- `backend/app/vault/__init__.py`
- `backend/app/routes/vault.py` — REST API

**Acceptance Criteria:**
- [ ] `sqlite3 ~/.aria/vault.db "SELECT * FROM credentials"` → only ciphertext visible
- [ ] Wrong passphrase → graceful failure, no crash
- [ ] Vault auto-locks after 5 minutes idle
- [ ] "Save my LinkedIn password" via Aria chat works

---

### ⏳ ARIA-P1-C3: Login Auto-Fill Checkpoint
**Priority:** P1  
**Dependencies:** ARIA-P1-C1, ARIA-P1-C2

**What:** Browser agent detects login pages, auto-fills from vault or prompts user. Credentials never logged or included in chat history.

**Files:**
- `backend/app/browser/detect.py` — implement `detect_login_form(page_state)` (checks for password fields)
- `backend/app/browser/agent.py` — pause on login detection, check vault, emit `wait_for_user`
- `frontend/src/components/CredentialModal.tsx` — approval modal

**Acceptance Criteria:**
- [ ] Gmail, LinkedIn, GitHub login pages reliably detected
- [ ] Vault credentials auto-fill without user interaction
- [ ] Modal appears for unknown sites
- [ ] "Remember this" → saved to vault
- [ ] Credentials NEVER in chat history, logs, or SSE stream
- [ ] Task continues automatically after successful login

---

### ⏳ ARIA-P1-C4: `browser_task` Tool
**Priority:** P1  
**Dependencies:** ARIA-P1-C1

**What:** Register `browser_task` as a callable tool so any agent/workflow step can invoke the browser.

**Files:**
- `backend/app/tools/browser_tools.py` — async `browser_task(task, url, extract)` function
- `backend/app/tools/registry.py` — register tool
- `backend/app/agents/registry.py` — add to relevant agents

**Acceptance Criteria:**
- [ ] Any agent can call `browser_task` in a tool call
- [ ] Browser panel goes live when called
- [ ] Returns `{url, title, extracted_text, screenshots}`
- [ ] 120s timeout with clean error
- [ ] Works as a workflow TOOL step

---

## EPIC D — Coder Pipeline

### ⏳ ARIA-P1-D1: Code Review Agent
**Priority:** P1  
**Dependencies:** None

**What:** New `code_reviewer` agent using reasoning model. Reviews diffs against checklist, outputs structured verdict + line comments.

**Files:**
- `backend/app/agents/registry.py` — add `code_reviewer` AgentSpec (MODEL_REASONING)
- `backend/app/tools/registry.py` — add `read_git_diff` tool

**System prompt checklist:** logic correctness, edge cases, security (secrets/injection), performance, test coverage

**Acceptance Criteria:**
- [ ] Input: git diff → Output: `{verdict: "APPROVED"|"CHANGES_NEEDED", comments: [{file, line, issue, suggestion}]}`
- [ ] Routes to MODEL_REASONING
- [ ] Catches hardcoded secret, missing null check, SQL injection in test diffs
- [ ] Does NOT hallucinate file/line numbers not in the diff

---

### ⏳ ARIA-P1-D2: QA Agent + Video Recording
**Priority:** P1  
**Dependencies:** ARIA-P1-C1

**What:** `qa_browser` agent that navigates an app, runs a test script, captures console errors, and records the full session as video.

**Files:**
- `backend/app/agents/registry.py` — add `qa_browser` AgentSpec
- `backend/app/browser/engine.py` — add `start_recording()` / `stop_recording()` via Playwright `record_video_dir`
- `backend/app/browser/qa.py` — QA session with console error collection

**Acceptance Criteria:**
- [ ] Navigates URL, performs actions, captures console errors
- [ ] `.mp4`/`.webm` saved to `~/.aria/qa_recordings/`
- [ ] QA report: `{passed, console_errors, video_path, steps_completed}`
- [ ] Video is ≥5 seconds, shows real browser session
- [ ] Console error severity flagged (error vs warning)

---

### ⏳ ARIA-P1-D3: Human-in-the-Loop INPUT Step
**Priority:** P1  
**Dependencies:** None

**What:** Implement `StepType.INPUT` in workflow executor. Workflow pauses, sends question to user via SSE, waits for response, resumes.

**Files:**
- `backend/app/workflows/executor.py` — handle INPUT step with asyncio.Event + per-session queue
- `backend/app/routes/chat.py` — add `POST /api/workflows/{session_id}/respond`
- `frontend/src/components/ChatView.tsx` — render INPUT event as approve/feedback prompt

**Acceptance Criteria:**
- [ ] Workflow pauses at INPUT step, sends question to chat
- [ ] "Approve" → workflow continues
- [ ] "Make these changes: [feedback]" → feedback injected into context, branches back
- [ ] Resumes within 2s of response
- [ ] 10-minute timeout → status set to "waiting for user"

---

### ⏳ ARIA-P1-D4: Parallel Step Execution
**Priority:** P1  
**Dependencies:** None

**What:** Implement `StepType.PARALLEL` in workflow executor using `asyncio.gather`. Multiple agents run concurrently.

**Files:**
- `backend/app/workflows/executor.py` — handle PARALLEL step

**Acceptance Criteria:**
- [ ] 2 parallel agents take max(a,b) time, not sum(a+b) — verified by timing test
- [ ] All outputs merged into context before next step
- [ ] One failure doesn't kill others; failure logged and noted

---

### ⏳ ARIA-P1-D5: Coder Pipeline Workflow
**Priority:** P1  
**Dependencies:** D1, D2, D3, D4

**What:** Full multi-agent coder pipeline registered as a workflow. Planner → Coder → Review+Tests (parallel) → QA+Video → User Gate → Git Commit.

**Files:**
- `backend/app/workflows/__init__.py` — add `coder_pipeline` workflow
- `backend/app/tools/registry.py` — add `read_git_diff`, `git_commit` tools

**Trigger keywords:** "make this change", "complete ticket", "implement", "fix this bug", "add this feature"

**Acceptance Criteria:**
- [ ] Planner identifies correct files from natural-language description
- [ ] Coder saves changes to disk via `file_write`
- [ ] Reviewer catches at least 1 issue in a test scenario
- [ ] CHANGES_NEEDED → retry (max 3 attempts before flagging user)
- [ ] QA video created and path in response
- [ ] User sees diff (CodeView) + QA report + video (VideoPlayerView)
- [ ] "Looks good" → git commit with AI-generated message

---

## EPIC E — Frontend UI

### ⏳ ARIA-P1-E1: Pipeline Status View
**Priority:** P1  
**Dependencies:** ARIA-P1-D5

**What:** Live step-by-step pipeline progress view. SSE-driven real-time updates.

**Files:**
- `frontend/src/components/views/PipelineStatusView.tsx`
- `frontend/src/components/DashboardRenderer.tsx` — add `pipeline_status` case

**Design:**
```
✅ Planner      — "Created 4-step plan"
🔄 Coder        — "Writing auth.py..." (streaming)
⏳ Code Review  — pending
⏳ QA           — pending
```

**Acceptance Criteria:**
- [ ] Appears automatically for workflows with 3+ steps
- [ ] Updates in real-time via SSE
- [ ] Current step: spinner + streaming partial output
- [ ] Completed steps: ✅ + brief summary, expandable
- [ ] Transitions to result view on completion

---

### ⏳ ARIA-P1-E2: Video Player View
**Priority:** P1  
**Dependencies:** ARIA-P1-D2

**What:** Inline video player for QA recordings with QA report alongside it.

**Files:**
- `frontend/src/components/views/VideoPlayerView.tsx`
- `frontend/src/components/DashboardRenderer.tsx` — add `video_player` case

**Acceptance Criteria:**
- [ ] Video plays inline (no external app)
- [ ] Controls: play/pause, seek, volume, fullscreen
- [ ] QA report alongside: status, console errors, steps
- [ ] Download button
- [ ] Supports `.mp4` and `.webm`

---

## Dependency Map

```
A1 ──────────────────────────────────── Foundation
├── A2 ──── A4 (chat→browser) ── A3
│           └── C4 (browser_task tool)
├── B1 ──── B2
├── C1 ──── A4
│   └────── C3 ──── (login auto-fill)
│            └── C2
├── D1 ──────────────────────────────┐
├── D2 (needs C1) ───────────────────┤── D5 ── E1
├── D3 ──────────────────────────────┤          └── E2
└── D4 ──────────────────────────────┘
```

## Sprint Order

| Sprint | Tickets | End State |
|--------|---------|-----------|
| 1 | A1, A2, C1 | ✅ Desktop app opens, live browser works, stealth enabled |
| 2 | **A4** | 🔄 **User types task → Aria browses live → reports back (EPIC-A gate)** |
| 3 | B1, B2 | "Summarize my Gmail" works end-to-end |
| 4 | C2, C3, C4 | Login auto-fill, credential vault, browser_task tool |
| 5 | D1, D2 | Code review agent + QA recording work |
| 6 | D3, D4, D5 | Full coder pipeline runs end-to-end |
| 7 | A3, E1, E2 | Mid-task interruption + Pipeline UI + Video view |

## EPIC-A Completion Checklist

EPIC-A is **complete** when all of the following pass:
- [x] `npm run electron:dev` opens the app
- [x] Live BrowserView embedded, real Chrome, no bot flags
- [x] Sessions persist (login survives restart)
- [ ] User types "go to X and do Y" → browser opens → AI completes task
- [ ] 3 real-world browser tasks tested end-to-end without manual intervention
