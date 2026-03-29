# Aria — Product Strategy Document
**Version:** 1.0  
**Date:** March 2026  
**Status:** Living Document

---

## Vision

> "An AI that knows you across time — private, proactive, and present in every tool you use."

The market is full of AI that resets every session, lives in silos, and demands constant re-explanation. Aria's mission is to be the first personal AI with **persistent identity, cross-app context, and proactive intelligence** — running locally, owned by the user, never selling their data.

---

## The Core Problem Nobody Has Solved

Every AI today is **amnesiac and reactive**.

- You re-explain yourself every session
- Your AI in one app knows nothing about what you did in another
- The AI waits to be asked — it never tells you what you need before you know you need it
- Cloud AI harvests the most private moments of your life

**The person who solves persistent, cross-app, proactive personal AI wins the next decade of computing.**

---

## Market Gaps By User Persona

### Medical Students / Doctors / Nurses
- Drug interaction checker that *remembers patient context over time*
- Auto-generate SOAP notes, discharge summaries, referral letters from voice dictation
- ICD-10 / CPT code suggester from symptom descriptions
- Clinical case simulator (practice diagnosis with AI presenting symptoms)
- Contextual drug dosing: "What's the dose for X for a 70kg patient with renal impairment?" — with memory of the patient's current medications
- Study mode: auto-flashcards from uploaded lecture PDFs + spaced repetition scheduler
- **Gap:** No private, HIPAA-friendly, *local* AI for clinical workflow. Epic and major EHRs charge enterprise rates. Solo practitioners and students are completely unserved.

### Engineering Students / Engineers
- Upload a datasheet or spec PDF → instant answers, cross-document comparisons
- Step-by-step problem solving that *teaches*, showing working rather than just delivering answers
- Auto-generate project documentation, test plans, technical specs from descriptions
- System design review from voice or text description
- **Gap:** No AI that understands your codebase AND your project domain simultaneously, over time.

### Programmers / Coders
- GitHub Copilot exists but: no memory of *why* architectural decisions were made, no cross-session reasoning
- Bug pattern recognition: "You've made this same class of error 3 times this month — here's the pattern"
- Auto-generate changelogs, PR descriptions, commit messages from diffs
- Code review assistant that knows your team's conventions from past PRs
- **Gap:** AI with codebase memory + personal habit learning.

### Content Creators / Editors / Writers
- Brand voice memory — learns your style after reading 10 pieces of your work, not generic output
- One-to-five repurposing: blog post → Twitter thread → reel script → newsletter → YouTube script, automatically
- SEO analysis with competitor context stored in memory over time
- Thumbnail copy suggestions based on what's worked for *you* specifically
- **Gap:** AI that knows your audience, your past content performance, and your voice.

### Streamers / YouTubers / Influencers
- Real-time stream assistant: suggest chat responses, flag moderation needs, fact-check claims live
- Auto chapter markers and description from transcript
- Analytics interpretation: "Your Monday uploads perform 40% better — here's the likely cause"
- Collab pitch generator using niche + brand alignment analysis
- **Gap:** An ambient AI co-host that's *present during live content*, not just a post-production editor.

### Tradespeople: Plumbers, Electricians, HVAC
- Photo → diagnosis pipeline: photograph the problem, get probable causes + parts list + repair steps
- NEC / building code quick lookup by country and state
- Job quote generator: describe the work verbally, get a formatted client-ready quote
- Parts ordering assistant connected to supplier catalogs
- **Gap:** Offline-capable, voice-first, photo-first AI for people who work with their hands. 100 million tradespeople worldwide, almost completely unserved by AI.

### Receptionists / Admin Professionals
- Email triage and prioritization with context of *who matters and why*
- Meeting prep brief: "Here's what was discussed last time with this client"
- Auto-draft replies matching tone (formal/casual based on sender history)
- Calendar gap analysis: "You have no buffer before this meeting and travel takes 20 minutes — we have a conflict"
- **Gap:** AI with organizational memory and relationship context, not just personal productivity.

### Students (General)
- Exam prep mode: ingests your notes + syllabus → generates practice tests
- Study session planner based on exam dates + topic weights + your known weak spots
- Progressive hint system: teaches concepts by starting with direction, not the answer
- Cross-topic connection finder: "This concept in chemistry connects to what you studied in biology last week"
- **Gap:** An AI tutor that tracks your weak spots across all subjects over an entire academic year.

### Teenagers
- Social filter: "Is this message I'm about to send going to cause a problem?" — pre-send review
- Career exploration advisor based on what they enjoy
- Private mood journaling with pattern recognition (non-clinical mental health awareness)
- **Gap:** A private, non-judgmental AI companion with no corporate data harvesting — something young people can actually trust.

### Gamers
- Strategy coach with memory of playstyle and recurring mistakes
- Voice-command game data lookups without alt-tabbing
- Clip highlight summarizer: paste a VOD link, get timestamp highlights
- **Gap:** Real-time ambient gaming assistant that doesn't require leaving the game.

---

## The Browser Extension Opportunity

A browser extension connecting to the local Aria backend is one of the highest-leverage features in the product. It turns Aria from a chatbot into **ambient intelligence across the entire internet**.

### What It Enables
| Feature | Description |
|---|---|
| **Page Memory** | Add any webpage to Aria's memory with one click. "What was that article about X I read last week?" |
| **Selection Actions** | Highlight text → summarize / translate / save to memory / explain / expand inline |
| **Research Synthesis** | Browse 10 pages, Aria synthesizes a cross-document summary |
| **Form Intelligence** | Aria knows your details and fills forms context-appropriately |
| **Price / Change Monitoring** | "Tell me when this product drops below $X" — extension monitors passively |
| **Relationship Context** | In a Gmail thread, sidebar shows Aria's memory of that person/company |
| **Live Page Q&A** | Chat with any webpage like a document |
| **Write Mode** | On any text input (LinkedIn, email, Twitter) get Aria suggestions inline |

### Privacy Differentiator
The extension communicates with `localhost:8000` — your own machine. **Nothing is sent to any external server by default.** This is the direct counter to Grammarly, Gemini Sidebar, and every other extension that harvests your browsing data.

---

## Mobile Strategy

### CLI (Command Line Interface)
```bash
aria "what's on my schedule today"
aria "summarize my last meeting notes"
aria --agent coder "refactor this function" < file.py
cat error.log | aria "what went wrong"
```
- Installable via `pip install aria-cli`
- Compiled binary for no-dependency distribution
- Connects to local backend or remote relay

### Android
- Full control: React Native or Flutter app
- Can optionally run a minimal local model via Termux for true on-device AI

### iOS — Bypassing Limitations

| Strategy | Description | Viability |
|---|---|---|
| **PWA** | Deploy Aria frontend as a Progressive Web App. Users add to home screen from Safari. Service workers handle offline. No App Store needed. | ✅ Best option |
| **TestFlight** | Distribute to 10,000 beta users without App Store review | ✅ Good for early access |
| **Remote + Tailscale** | Aria runs on home server, iPhone is thin client over private VPN | ✅ Ideal for power users |
| **EU Sideloading** | iOS 17.4+ allows third-party app stores in the EU | ✅ Real distribution channel |
| **App Clip** | Lightweight iOS feature, no full install required, for specific micro-features | 🟡 Limited scope |
| **Cloud Option** | Self-hosted VPS, connects over HTTPS | ✅ Opt-in for users who want sync |

**Primary recommendation: PWA + local backend + Tailscale for remote access.** This delivers a near-native experience without Apple's gatekeeping.

---

## What Can Be Patented

### The Core Patentable System: Temporal Episodic Memory Compression

The fundamental unsolved problem in personal AI is the mismatch between finite context windows and the infinite span of a human life.

**The architecture:**
1. **Layer 0 — Raw Events:** Full-fidelity storage of all interactions, documents, actions
2. **Layer 1 — Daily Summaries:** Nightly compression of the day's events into structured summaries
3. **Layer 2 — Weekly Abstracts:** Weekly pattern extraction across daily summaries
4. **Layer 3 — Monthly Themes:** Thematic clustering and goal-state inference
5. **Layer 4 — Persistent User Model:** Skills, preferences, relationships, long-term goals

The AI retrieves across all layers simultaneously, selecting the right granularity based on semantic relevance to the current query. **This is novel. Nothing commercially available implements this as a full system.**

### Patentable Concepts Table

| # | Concept | Description | Commercial Licensability |
|---|---|---|---|
| 1 | **Temporal Episodic Compression** | Hierarchical time-decay compression of personal AI memory | Very High — every AI company needs this |
| 2 | **Intent Fingerprinting** | Learning a user's behavioral signature from multi-modal inputs to predict unstated needs | High — proactive AI foundation |
| 3 | **Privacy-Preserving Context Federation** | Protocol for sharing AI context across devices without a central server (local-first sync) | High — enterprise + privacy market |
| 4 | **Persona-Adaptive Calibration** | Dynamically adjusts AI response style, depth, vocabulary to the user's real-time state without fine-tuning | Medium — UX layer on any LLM |
| 5 | **Multi-Agent Personal Consensus** | When specialized agents disagree on user intent, a structured debate protocol resolves ambiguity | Medium — agent orchestration |
| 6 | **Ambient Interrupt Optimization** | AI determines the *right moment* to proactively surface information based on behavioral context signals | High — proactive AI timing |

**Patent #1 (Temporal Episodic Compression) is the most commercially licensable.** OpenAI, Google, Apple, Microsoft, and Samsung all need this. Building and patenting it with a working implementation creates leverage over the entire industry.

---

## The 10 Real Market Gaps

After processing millions of conversations, these are the consistent unmet needs:

1. **An AI that knows you across time** — Not 5 messages ago. 6 months ago. Nobody has this.
2. **Proactive, not reactive** — AI that tells you what you need before you ask. Entirely absent from the market.
3. **Privacy-first with full capability** — People are scared of cloud AI for medical/legal/personal data. Local AI is too weak. The bridge between these is unoccupied.
4. **Whole-life integration** — Calendar + email + files + browsing + notes + health + finances in one context. Every tool is siloed.
5. **Voice as a first-class citizen** — Not Siri-style voice (limited, comedic) but voice that handles complex intent, maintains context, and does real work.
6. **Offline + edge AI** — AI that works on a plane, in a hospital, in a field. Local-first is a feature, not a compromise.
7. **The second brain for non-technical people** — Notion and Roam are too complex. An AI that automatically organizes what you tell it, connects dots, and surfaces memories without you building a system.
8. **Professional-grade specialization without enterprise pricing** — Solo doctors, solo lawyers, independent engineers can't afford enterprise AI tools. A democratized professional AI.
9. **AI for the physical world** — 100 million tradespeople have zero good AI tooling. Everything is built for knowledge workers sitting at desks.
10. **Emotional continuity** — AI that remembers you're going through something and adapts tone without being told. Not therapy — contextual awareness. Nobody does this.

---

## Competitive Landscape

| Product | What They Do | What's Missing |
|---|---|---|
| ChatGPT / Claude | General AI, cloud, resets per session | No persistent memory across time, no local, no browser integration |
| GitHub Copilot | Code AI, IDE plugin | No project memory, no cross-session reasoning |
| Notion AI | Document AI, within Notion only | Siloed, no external context, no proactive behavior |
| Grammarly | Writing assistant, browser extension | No intelligence, no memory, harvests data |
| Apple Siri / Google Assistant | Voice commands | Surface-level, no reasoning, no memory |
| Perplexity | Search AI | No memory, no personal context, no action |
| **Aria** | **All of the above, unified, local, memory-first** | — |

---

## Recommended Build Order

```
Phase 1 (Complete):   Core assistant + web search + multi-agent routing         ✅
Phase 2 (Next):       Temporal memory layer + browser extension (highest ROI)
Phase 3:              Mobile PWA + CLI
Phase 4:              Domain packs (medical, legal, trades, creator)
Phase 5:              Patent filing + enterprise licensing
```

---

## Revenue Model (Future)

| Tier | Offering | Price Point |
|---|---|---|
| **Open Source Core** | Self-hosted, full local, community | Free |
| **Aria Cloud** | Cloud-synced, managed hosting, mobile | $10-20/month |
| **Aria Professional** | Domain packs (medical, legal, etc.), priority support | $30-50/month |
| **Aria Enterprise** | On-premise, custom domains, API licensing | Custom |
| **Patent Licensing** | Memory compression tech licensed to AI companies | Negotiated |
