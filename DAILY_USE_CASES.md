# Aria — Daily Use Cases: 8 Hours → 2 Hours
**Version:** 1.0  
**Date:** March 2026

> A normal person's workday, profession by profession. What they do, what Aria does for them, and what's left for them to do.

---

## How to Read This Document

Each profession shows:
- **The 8-hour day** — the real breakdown of where time goes
- **Aria's role** — exactly which tasks Aria handles, automates, or accelerates
- **The 2-hour day** — what the human actually needs to do with their judgment and presence
- **The ROI** — time saved per week, per year

---

## 01 — Software Developer / Programmer

### The 8-Hour Day
| Task | Time |
|---|---|
| Reading and understanding a ticket / requirement | 45 min |
| Setting up or context-switching into the codebase | 30 min |
| Writing boilerplate, repetitive code structures | 90 min |
| Debugging — reading errors, tracing, searching Stack Overflow | 90 min |
| Writing unit tests | 45 min |
| Code review — reading others' PRs | 45 min |
| Writing PR descriptions, comments, changelogs | 30 min |
| Meetings (standup, sprint planning, retro) | 60 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Ticket analysis:** Reads the Jira/GitHub issue, explains the scope, flags ambiguities, and suggests an implementation approach before the dev writes a single line — *saves 30 min*
- **Codebase onboarding:** "I need to add rate limiting to the auth routes" → Aria searches the indexed repo, shows exactly which files to touch and why — *saves 25 min*
- **Boilerplate generation:** Generates controllers, models, API endpoints, database migrations from a description — *saves 60-75 min*
- **Debugging:** Developer pastes an error. Aria reads it, searches the codebase, identifies the likely root cause and suggests the fix with context — *saves 60 min*
- **Test generation:** "Write tests for this function" — Aria writes the test cases including edge cases, following the existing test patterns in the repo — *saves 35 min*
- **PR description:** Given the diff, Aria writes the PR description, changelog entry, and inline review comments automatically — *saves 25 min*
- **Code review assist:** Aria reads incoming PRs and highlights issues, anti-patterns, and security concerns — *saves 30 min*

### The 2-Hour Day
- Architecture decisions that require judgment (30 min)
- Actual creative problem solving for the hard parts (45 min)
- Standups and critical meetings (30 min)
- Final review of what Aria generated (15 min)

### ROI
- **Time saved per week:** ~30 hours
- **Equivalent to:** Aria does the work of 3 junior developers for repetitive tasks

---

## 02 — Content Creator / YouTuber / Podcaster

### The 8-Hour Day
| Task | Time |
|---|---|
| Research — finding topics, trends, competitor content | 90 min |
| Scripting / outlining | 90 min |
| Thumbnail copy and concept ideation | 30 min |
| Filming / recording | 60 min |
| Editing captions and descriptions | 45 min |
| Posting to multiple platforms (YouTube, Instagram, TikTok, Twitter) | 45 min |
| Replying to comments and DMs | 60 min |
| Analytics review and planning next content | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Research:** "Find the top performing videos in my niche from the last 30 days — what topics are trending and what's the hook they use?" → Aria does the search, compares, summarizes — *saves 70 min*
- **Scripting:** Given a topic and your brand voice (learned from previous scripts), Aria writes a structured script with hook, body, CTA — *saves 60-75 min*
- **Thumbnail copy:** Generates 5 thumbnail text options in your style based on what's worked before — *saves 25 min*
- **Descriptions and captions:** Transcribes the video, generates the YouTube description, chapter markers, SEO tags, and platform-specific captions for each social post — *saves 40 min*
- **Cross-platform posting:** Repurposes one piece of content into a Twitter thread, LinkedIn post, Instagram caption, and TikTok hook — simultaneously — *saves 40 min*
- **Comment management:** Reads all comments, categorizes them (positive/questions/complaints), drafts replies in your voice — *saves 45 min*
- **Analytics brief:** Every Monday, a plain-language summary: "Your top 3 videos this week, why they likely performed well, and what to make next" — *saves 25 min*

### The 2-Hour Day
- Filming / recording (the actual creative act) (60 min)
- Review and approve Aria's generated content (30 min)
- Strategic decisions: partnerships, direction, audience feedback (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Equivalent to:** Aria replaces a researcher, a social media manager, and a copywriter

---

## 03 — Doctor / General Practitioner

### The 8-Hour Day
| Task | Time |
|---|---|
| Pre-appointment chart review | 60 min |
| Patient appointments (seeing 15-20 patients) | 240 min |
| Writing clinical notes (SOAP format) for each patient | 90 min |
| Prescription and referral letters | 45 min |
| Catching up on lab results, flagging abnormals | 30 min |
| Administrative emails and patient follow-up messages | 45 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Pre-appointment briefs:** "Patient John Doe, 52M, coming in today" → Aria pulls the chart history, last visit summary, outstanding flags, current medications, and allergies into a 30-second brief — *saves 45 min*
- **Clinical note generation:** Doctor dictates verbally during or after the appointment for 2-3 minutes. Aria structures this into a full SOAP note with appropriate medical terminology — *saves 60 min*
- **Prescription drafts:** "Metformin for T2DM, patient has CKD stage 3" → Aria checks the drug handbook, flags the dose adjustment needed, drafts the prescription note — *saves 25 min*
- **Referral letters:** "Refer to cardiology for exertional chest pain" → Aria writes the full referral letter with relevant patient history included — *saves 20 min*
- **Lab result triage:** Aria reads all incoming lab results, flags any critical values, groups normal results, drafts patient follow-up messages for the doctor to approve — *saves 25 min*
- **Patient emails:** Doctor gives a 10-word instruction ("tell him to take ibuprofen and rest, review in a week"). Aria writes the full, appropriately warm patient email — *saves 35 min*

### The 2-Hour Day
- Seeing the patients requiring genuine clinical judgment (60 min for the 20% complex cases)
- Reviewing and signing off Aria's drafts (30 min)
- Procedures that require physical presence (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Direct impact:** More patients seen, less burnout, reduced documentation backlog (a known cause of physician attrition)
- **Note:** All processing is local — HIPAA-sensitive data never leaves the machine

---

## 04 — Lawyer / Legal Professional

### The 8-Hour Day
| Task | Time |
|---|---|
| Contract review — reading and flagging issues | 120 min |
| Legal research — case law, precedents | 90 min |
| Drafting letters, briefs, memos | 90 min |
| Client emails and communication | 45 min |
| Billing — time tracking, invoice preparation | 30 min |
| Case file organization | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Contract review:** Upload a 50-page contract → Aria reads it, flags non-standard clauses, unusual indemnification terms, missing standard protections, and summarizes key obligations in plain English — *saves 80 min*
- **Legal research:** "Find relevant precedents for wrongful termination during probation period in California" → Aria searches, summarizes the relevant cases, and structures an argument outline — *saves 60-70 min*
- **Document drafting:** "Draft a cease and desist letter for trademark infringement, formal tone, include the specific demands" → Full draft in 2 minutes — *saves 50 min*
- **Client email:** Lawyer gives the key point in one sentence. Aria writes the full, appropriately professional client email — *saves 35 min*
- **Billing memo:** At end of day, lawyer describes what they did in 2 minutes of voice. Aria generates the itemized billing memo with time allocations — *saves 25 min*
- **Case file summary:** New case arrives → Aria reads all documents and generates a case summary with key facts, parties, timeline, and open questions — *saves 25 min*

### The 2-Hour Day
- Client meetings requiring trust and relationship (45 min)
- Court appearances and negotiations (45 min)
- Strategic legal judgment — what advice to *actually give* (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Revenue impact:** Lawyer can bill 2x the hours in the same time, or take twice the caseload

---

## 05 — Accountant / Bookkeeper

### The 8-Hour Day
| Task | Time |
|---|---|
| Data entry — categorizing transactions | 90 min |
| Bank reconciliation | 60 min |
| Preparing financial reports | 90 min |
| Client emails and queries | 45 min |
| Tax preparation research | 60 min |
| Invoice generation and follow-up | 45 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Transaction categorization:** Connect to exported bank CSV → Aria categorizes all transactions using pattern recognition and memory of how you categorized similar transactions before — *saves 70 min*
- **Reconciliation:** Aria compares transactions against the ledger, flags discrepancies with explanations — *saves 40 min*
- **Report generation:** "Generate the P&L for Q1 in the format we sent last quarter" → Aria pulls the data and formats the report — *saves 60 min*
- **Client responses:** Client asks "why did my tax bill go up this year?" → Aria reads their file and drafts a plain-language explanation — *saves 35 min*
- **Tax research:** "What's the current deductibility limit for home office expenses in the UK for a sole trader?" → Aria researches current rules — *saves 45 min*
- **Invoice follow-up:** Aria drafts polite, escalating follow-up emails for overdue invoices — *saves 35 min*

### The 2-Hour Day
- Strategic financial advice requiring judgment (45 min)
- Complex client consultations (45 min)
- Reviewing and approving Aria's outputs (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Equivalent to:** Aria replaces a junior bookkeeper for all data-entry and first-pass analysis work

---

## 06 — Teacher / Educator

### The 8-Hour Day
| Task | Time |
|---|---|
| Lesson planning | 60 min |
| Creating worksheets, quizzes, assessments | 60 min |
| Grading and providing written feedback | 90 min |
| Parent and admin emails | 45 min |
| Actual teaching / class time | 90 min |
| Updating progress trackers | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Lesson planning:** "Plan a 45-minute lesson on photosynthesis for 8th grade, aligns with Common Core standard NGSS MS-LS1-6" → Full lesson plan with objectives, activities, discussion questions, materials — *saves 45 min*
- **Assessment creation:** "Create a 10-question quiz on the French Revolution for 10th grade, mix of multiple choice and short answer" → Ready to print in 60 seconds — *saves 45 min*
- **Grading assist:** Teacher marks scores. Aria generates personalized written feedback for each student based on their specific answers — *saves 70 min*
- **Parent emails:** "Draft a note to the parents of Tommy explaining his progress in math and suggesting home practice" → One sentence to Aria, full warm professional email back — *saves 35 min*
- **Progress reports:** Aria reads the grade book and generates per-student narrative progress summaries for report cards — *saves 25 min*
- **Differentiation:** "Adapt this lesson for a student with dyslexia and for a student who is 2 years ahead" → Two adapted versions in minutes — *saves 30 min*

### The 2-Hour Day
- Actually teaching — the human connection with students (90 min)
- High-stakes conversations with parents or admin (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Impact:** Teachers report spending 40-50% of time on administration. Aria cuts that to 10%.

---

## 07 — Marketing Manager

### The 8-Hour Day
| Task | Time |
|---|---|
| Campaign brief writing | 60 min |
| Copywriting — ads, emails, landing pages | 90 min |
| Competitor monitoring | 45 min |
| Analytics review and reporting | 60 min |
| Coordinating with designers and agencies | 45 min |
| Social media management | 45 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Campaign briefs:** Aria generates a structured brief from a 2-sentence description of the goal — *saves 45 min*
- **Copy generation:** 5 ad variants, email subject line A/B tests, landing page body copy — in your brand voice — *saves 70 min*
- **Competitor monitoring:** "What are our top 3 competitors talking about this week?" → Aria searches, summarizes positioning changes, new campaigns, pricing updates — *saves 40 min*
- **Analytics narrative:** Aria reads the raw GA4/Meta/email numbers and writes a plain-language weekly report with insights — "Email opens dropped 12% — likely the subject line, here are 3 better options for this week" — *saves 50 min*
- **Agency briefs and feedback:** Paste an agency proposal → Aria summarizes it and drafts structured feedback — *saves 35 min*
- **Social calendar:** "Plan our social calendar for next 2 weeks based on our product launch on April 10" → Full calendar with post copy for each platform — *saves 40 min*

### The 2-Hour Day
- Strategy decision-making and creative direction (45 min)
- Stakeholder meetings (45 min)
- Reviewing and approving Aria's outputs (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Equivalent to:** Aria replaces a copywriter, a social media coordinator, and a data analyst for routine work

---

## 08 — Customer Support Agent

### The 8-Hour Day
| Task | Time |
|---|---|
| Reading and understanding each ticket | 60 min |
| Researching answers in documentation | 90 min |
| Writing responses | 120 min |
| Escalation decisions | 30 min |
| Logging ticket resolutions | 30 min |
| **Total** | **~8 hrs (50-80 tickets)** |

### What Aria Does
- **Ticket understanding:** Aria reads the ticket, categorizes it (billing / bug / how-to / complaint), identifies the customer's actual problem (often different from what they wrote), and prepares a context brief — *reduces reading time by 60%*
- **Answer research:** Given the ticket category, Aria searches the knowledge base and past resolved tickets for the relevant answer — *saves 70 min*
- **Response drafting:** Aria writes the full response matching the company's tone guidelines and the customer's emotional state (frustrated customers get a more empathetic opening) — *saves 90 min*
- **Escalation suggestion:** "This customer has contacted support 4 times this month and is now threatening to cancel — flag for manager" — Aria identifies escalation patterns automatically
- **Resolution logging:** Aria fills the resolution fields in the ticket system from the conversation

### The 2-Hour Day
- Reviewing and sending Aria's drafted responses (judgment call on what's correct) (60 min)
- Genuinely complex, emotionally charged situations requiring human empathy (45 min)
- Edge cases that require product team input (15 min)

### ROI
- **Throughput:** Agent handles 150+ tickets/day vs. 50-80 without AI
- **Quality:** Consistent tone and accuracy, no 4pm drop in response quality
- **Impact:** 3x support capacity without hiring

---

## 09 — Journalist / Writer / Reporter

### The 8-Hour Day
| Task | Time |
|---|---|
| Story research — reading sources, verifying facts | 120 min |
| Interview prep | 45 min |
| First draft writing | 120 min |
| Editing and fact-checking | 60 min |
| Headlines, subheads, SEO metadata | 30 min |
| Filing and formatting | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Research:** "Background brief on the Port of LA supply chain disruption — key facts, timeline, key players, 3 expert sources to contact" → Full research brief in minutes — *saves 80 min*
- **Interview prep:** "I'm interviewing the CEO of [company] about their Q1 earnings miss — prepare 10 sharp questions" → Aria reads the earnings report and generates pointed questions — *saves 35 min*
- **First draft:** Journalist provides notes and quotes. Aria writes the structured first draft in the appropriate editorial voice — *saves 70-80 min*
- **Fact-check assist:** "Check these 5 statistics in this article" → Aria searches and flags which ones need verification and why — *saves 40 min*
- **Headlines + metadata:** Given the article, Aria generates 5 headline variants, a subhead, and SEO metadata — *saves 25 min*

### The 2-Hour Day
- The interviews themselves (60 min)
- Final editorial voice and judgment calls — the actual journalism (45 min)
- Source relationship management (15 min)

### ROI
- **Time saved per week:** ~30 hours
- **Impact:** Journalist publishes 3x the stories, or goes much deeper on fewer stories

---

## 10 — Project Manager

### The 8-Hour Day
| Task | Time |
|---|---|
| Status update emails and reports | 60 min |
| Meeting preparation and agendas | 30 min |
| Meeting facilitation and note-taking | 90 min |
| Task assignment and tracking | 45 min |
| Stakeholder communication | 60 min |
| Risk identification and mitigation planning | 45 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Status reports:** "Generate the weekly status report for the mobile app project" → Aria reads the project data, writes the executive summary, RAG status, blockers, and next week's plan — *saves 50 min*
- **Meeting agendas:** Given the project context, Aria generates a structured agenda for each recurring meeting — *saves 20 min*
- **Meeting notes:** Aria transcribes the meeting (voice), extracts action items, assigns owners, and generates the follow-up email with minutes — *saves 70 min*
- **Risk log updates:** From meeting notes, Aria identifies new risks and updates the risk register — *saves 30 min*
- **Stakeholder emails:** "Update the exec team on the 2-week delay due to API integration issues" → Aria frames it constructively with the mitigation plan — *saves 40 min*
- **Task health check:** Every morning: "Here's what's overdue, what's at risk, and what needs your attention today" — *saves 30 min*

### The 2-Hour Day
- Decision-making on blockers and trade-offs (45 min)
- Relationship management with key stakeholders (45 min)
- Reviewing Aria-generated comms before sending (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Impact:** PM can run 2-3 projects simultaneously instead of 1

---

## 11 — Sales Representative

### The 8-Hour Day
| Task | Time |
|---|---|
| Prospecting and lead research | 90 min |
| Personalized outreach emails | 90 min |
| CRM updates after each call | 45 min |
| Follow-up sequencing | 45 min |
| Proposal preparation | 60 min |
| Call preparation | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Lead research:** "Research Acme Corp — their current tech stack, recent news, decision maker on LinkedIn, likely pains based on their industry" → 5-minute research brief — *saves 60-70 min*
- **Personalized outreach:** Generic email → Aria rewrites it using the prospect's specific context (recent funding, job post, news item) — *saves 70 min*
- **CRM updates:** Sales rep voice-dictates "Called Sarah, she's interested but budget is frozen until Q3, follow up July 1st" → Aria logs it, creates the follow-up task — *saves 35 min*
- **Follow-up sequences:** Aria creates a 5-email follow-up sequence personalized to the prospect's objections — *saves 35 min*
- **Proposal drafting:** "Proposal for 50-seat SaaS license for a mid-size healthcare company focused on cost reduction" → Aria generates the first draft with relevant case studies — *saves 45 min*
- **Call prep brief:** 10 minutes before a call, Aria generates a one-page brief: who they are, last 3 touch points, their stated objections, suggested talking points — *saves 25 min*

### The 2-Hour Day
- The actual sales calls (the human relationship part) (90 min)
- Reviewing and personalizing Aria's drafts (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Pipeline impact:** Rep reaches 3x more prospects with the same personalization quality

---

## 12 — Graphic Designer / Visual Artist

### The 8-Hour Day
| Task | Time |
|---|---|
| Client brief interpretation and clarification | 45 min |
| Mood boarding and concept research | 60 min |
| Design production | 180 min |
| Client feedback rounds and revisions | 90 min |
| File export and delivery | 30 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Brief clarification:** Client sends a vague brief. Aria asks structured follow-up questions and summarizes the design requirements clearly — *saves 30 min*
- **Concept research brief:** "Mood board direction for a fintech startup targeting Gen Z — reference styles, color psychology, typography trends in this space" → Research brief to guide the designer — *saves 45 min*
- **Copy for designs:** All the text elements (headlines, CTAs, descriptions) that go into the design — Aria writes them — *saves 30 min*
- **Client feedback management:** Client sends confusing feedback ("make it pop more"). Aria interprets it — "they likely mean higher contrast and bolder typography based on the context" — *saves 30 min*
- **Revision emails:** "Tell the client their round 2 feedback has been incorporated and attach the new files" → Aria writes the professional delivery email — *saves 20 min*
- **Invoice generation:** After a project, Aria generates the invoice from project details — *saves 15 min*

### The 2-Hour Day
- Actual creative design work — the irreplaceable human aesthetic judgment (90 min)
- Client relationship and creative direction conversations (30 min)

### ROI
- **Time saved per week:** ~25 hours
- **Impact:** Designer takes 2x the client load or has more time for the creative work they actually enjoy

---

## 13 — HR Manager

### The 8-Hour Day
| Task | Time |
|---|---|
| Job description writing | 60 min |
| CV screening and shortlisting | 90 min |
| Interview scheduling coordination | 45 min |
| Onboarding documentation | 60 min |
| Policy question responses | 45 min |
| Performance review documentation | 60 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Job descriptions:** "Write a JD for a senior data engineer, remote, focus on Python and Spark, emphasize culture" → Full JD with responsibilities, requirements, and benefits in 2 minutes — *saves 50 min*
- **CV screening:** Upload 50 CVs → Aria scores each against the job criteria, produces a shortlist with reasons — *saves 75 min*
- **Interview scheduling:** Aria reads availability from both sides and proposes times, drafts the scheduling emails — *saves 35 min*
- **Onboarding documents:** "Generate the onboarding pack for Ahmed in the engineering team starting Monday" → Checklist, welcome email, first-week schedule, system access list — *saves 50 min*
- **Policy questions:** "Am I entitled to overtime pay if I work more than 8 hours in a day in California?" → Aria answers using the HR policy documents as context — *saves 35 min*
- **Performance review drafts:** Given a manager's bullet points, Aria writes the full structured performance review narrative — *saves 50 min*

### The 2-Hour Day
- Final-round interviews and hiring decisions (60 min)
- Sensitive conversations (performance issues, terminations) — human only (45 min)
- Strategic HR planning (15 min)

### ROI
- **Time saved per week:** ~30 hours
- **Impact:** HR team of 1 can support 3x the headcount

---

## 14 — Real Estate Agent

### The 8-Hour Day
| Task | Time |
|---|---|
| Property listing write-ups | 60 min |
| Market research for pricing | 60 min |
| Client communication (calls, emails, WhatsApp) | 90 min |
| Coordinating viewings and follow-ups | 60 min |
| Offer and negotiation documentation | 60 min |
| **Total** | **~8 hrs** |

### What Aria Does
- **Listing descriptions:** Agent provides the property details and photos (or a voice note tour). Aria writes a compelling, professional listing description for portals and social media — *saves 45 min*
- **Market analysis brief:** "Comparable sales in the W14 postcode, 2-bed apartments, last 90 days" → Aria searches and generates a pricing recommendation brief — *saves 50 min*
- **Client communications:** "Update the Johnsons on the survey outcome and next steps" → Agent gives the facts, Aria writes the warm, professional email — *saves 60 min*
- **Viewing coordination:** Aria manages the back-and-forth scheduling, sends confirmation emails and reminder messages — *saves 45 min*
- **Offer summary:** Buyer makes an offer with conditions → Aria writes the formal offer summary and cover letter to present to the seller — *saves 30 min*

### The 2-Hour Day
- Property viewings — requires physical presence and relationship (90 min)
- Negotiation calls — judgment and trust (30 min)

### ROI
- **Time saved per week:** ~25 hours
- **Impact:** Agent manages 3x the listings with the same time investment

---

## 15 — Small Business Owner

### The 8-Hour Day
| Task | Time |
|---|---|
| Emails — customers, suppliers, staff | 90 min |
| Bookkeeping and invoice management | 60 min |
| Social media and marketing | 60 min |
| Operational decisions (orders, staff, suppliers) | 60 min |
| Customer queries and complaints | 60 min |
| Planning (stock, pricing, growth) | 60 min |
| **Total** | **~8 hrs** |

*Note: For most small business owners, this is actually a 10-12 hour day.*

### What Aria Does
- **Email management:** Aria reads all incoming emails and categorizes them: urgent / needs response / FYI / junk. Drafts responses for the routine ones — *saves 60 min*
- **Bookkeeping:** Uploads receipts via photo, Aria categorizes and logs them. Generates the weekly P&L summary in plain language — *saves 45 min*
- **Social media:** "Create this week's social media posts based on our seasonal promotion ending Friday" → Posts for Instagram, Facebook, Google Business ready to schedule — *saves 45 min*
- **Supplier communication:** "Chase the order from our packaging supplier that was due yesterday" → Aria drafts the professional but firm follow-up — *saves 20 min*
- **Customer complaints:** Aria reads the complaint, drafts a resolution response within your policy, flags if compensation is appropriate — *saves 45 min*
- **Business insight brief:** Every Monday morning: "Here's your week ahead — cash flow position, staff hours, 3 decisions you need to make, and 2 opportunities you're missing" — synthesized from all the data Aria holds

### The 2-Hour Day
- Running the actual business (serving customers, making product, managing staff face-to-face) (90 min)
- The 3 actual decisions that require the owner's judgment (30 min)

### ROI
- **Time saved per week:** ~30 hours
- **Business impact:** Owner gets their evenings and weekends back — the #1 complaint of small business owners
- **Alternative framing:** What used to require hiring a VA, a social media coordinator, and a bookkeeper — Aria replaces all three

---

## Cross-Profession Summary

| Profession | Hours Saved/Day | Tasks AI Handles | What Remains Human |
|---|---|---|---|
| Software Developer | 5-6 hrs | Boilerplate, debugging, docs, testing | Architecture, creativity, decisions |
| Content Creator | 5-6 hrs | Research, scripting, distribution | Filming, creative direction |
| Doctor | 5-6 hrs | Documentation, briefs, admin | Clinical judgment, patient relationships |
| Lawyer | 5-6 hrs | Research, drafting, review | Strategy, court, client relationship |
| Accountant | 5-6 hrs | Data entry, reports, reconciliation | Advice, complex judgment |
| Teacher | 5-6 hrs | Planning, assessment, grading, admin | Teaching, student relationships |
| Marketing Manager | 5-6 hrs | Copy, reports, campaigns, social | Strategy, creative direction |
| Customer Support | 5-6 hrs | Research, drafting, logging | Complex escalations, empathy |
| Journalist | 5-6 hrs | Research, drafts, metadata | Interviews, editorial judgment |
| Project Manager | 5-6 hrs | Reports, minutes, comms, tracking | Decisions, relationships |
| Sales Rep | 5-6 hrs | Research, outreach, CRM, proposals | Calls, relationship building |
| Graphic Designer | 4-5 hrs | Briefs, copy, revisions, admin | Actual design, creative judgment |
| HR Manager | 5-6 hrs | JDs, screening, onboarding, docs | Hiring decisions, sensitive HR |
| Real Estate Agent | 4-5 hrs | Listings, research, comms, scheduling | Viewings, negotiation |
| Small Business Owner | 6-7 hrs | Email, books, social, customer service | Running the actual business |

---

## The Pattern Across All 15 Professions

The work that Aria handles consistently falls into these categories:

1. **Reading and understanding** — emails, documents, tickets, briefs (Aria reads fast and never misses a detail)
2. **Research** — finding information, verifying facts, competitive analysis (Aria searches, synthesizes, and remembers)
3. **First-draft writing** — the blank page is the hardest part; Aria removes it entirely
4. **Formatting and structuring** — taking raw information and making it presentable
5. **Repetitive communication** — scheduling, follow-ups, status updates, routine responses
6. **Logging and tracking** — updating systems, CRMs, logs, records

**What remains human — without exception — across all 15:**

1. **Judgment under uncertainty** — decisions where you don't have all the facts
2. **Physical presence** — the doctor seeing the patient, the agent showing the property
3. **Relationship trust** — the client who wants to talk *to you*, not an AI
4. **Creative vision** — what to make, not how to make it
5. **Responsibility** — signing your name to something, being accountable

The goal of Aria is not to replace these people. It is to **give back the 5-6 hours per day they spend on everything except the reason they chose their profession.**

---

## Implementation Note

Every capability described in this document is achievable with the current Aria architecture. The professions require:
- The memory layer (persistent context across sessions) — TICKET-201
- The browser extension (works where they work, in email and documents) — TICKET-203
- Domain-specific tool packs (medical tools, legal reference, financial calculators) — TICKET-401 to 403
- Voice as first-class input (for doctors, tradespeople, anyone on the go) — already partially built

**The platform is ready. The use cases are defined. Ship it.**
