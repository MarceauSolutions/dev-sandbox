# COMPANY ON A LAPTOP — Full Context Summary

**Date:** March 31, 2026
**Author:** Claude Opus (1M context), compiled from full workspace audit
**Purpose:** Single reference document for any AI agent (Claude, Grok, or future) to immediately understand this entire system without follow-up questions.

---

## Table of Contents

1. [Project Vision & Big Picture](#1-project-vision--big-picture)
2. [Core Architecture & Design Principles](#2-core-architecture--design-principles)
3. [Key Components & Current State](#3-key-components--current-state-march-31-2026)
4. [Decision History & Trade-offs](#4-decision-history--trade-offs)
5. [Current Challenges & Blockers](#5-current-challenges--blockers)
6. [How to Work With This Project Effectively](#6-how-to-work-with-this-project-effectively)
7. [Glossary of Key Terms & Files](#7-glossary-of-key-terms--files)

---

## 1. Project Vision & Big Picture

### The Human Behind the System

William Marceau is a 25-year-old entrepreneur in Naples, FL. He has **secondary dystonia** affecting his left side — a neurological condition caused by a brain tumor removed in childhood. This is not background trivia; it is the primary constraint that drives every architectural decision. On bad days, William operates from his phone with limited energy. The system must work when he cannot.

Starting **April 6, 2026**, William begins a full-time job as an electrical technician at Collier County Wastewater, working **7am-3pm weekdays**. Every hour spent babysitting automation is an hour stolen from either his health, his job, or his business.

### The Ultimate Goal

Build a **fully autonomous multi-tower business** that generates enough recurring revenue ($5,000+/month) to replace the day job, fund ongoing medical care for dystonia, and achieve financial independence. The business entity is **Marceau Solutions** — an AI automation consultancy targeting small businesses in Naples, FL (HVAC, medical offices, gyms, restaurants).

### Goal Hierarchy (from `projects/personal-assistant/data/goals.json`)

| Horizon | Goal | Deadline | Key Metrics |
|---------|------|----------|-------------|
| **Short-term** | Land first AI client | April 6, 2026 | 1 signed client, 1 discovery call, warm pipeline |
| **Medium-term** | $5,000/mo recurring | May 15, 2026 → July 2026 | $1,500+ MRR, referral from first client |
| **Long-term** | Replace day job income | December 31, 2026 | $5,000+/mo, 5+ clients, system runs autonomously |
| **Post-April 6** | Run business evenings/weekends | Ongoing | Morning digest at 6:30am, auto-outreach during work hours, manual work only after 3pm |

The long-term goal is **protected** — it cannot be cleared or overwritten by any agent without explicit authorization. This is enforced in `goal_manager.py`.

### The Research-First Mandate

Before executing ANY task, agents must:

1. Check pipeline.db and outcome tracking data first
2. Do NOT execute William's first instinct — validate against data
3. Present 2-3 alternatives with tradeoffs
4. Verify end-to-end before declaring complete
5. Never give false completion signals — "partially done" is honest; "complete" when it's not is a trust violation

This exists because of a pattern William calls **"the babysitting trap"** — having to re-verify and re-ask for the same things across sessions because agents claimed work was done when it wasn't.

### How the Vision Drives Every Decision

Every feature, every automation, every line of code is evaluated against one question: **"Does this move William closer to financial independence while requiring less of his time and energy?"** If the answer is no, it doesn't get built. If it requires CLI commands, it gets rebuilt. If it only works when the Mac is open, it's incomplete.

---

## 2. Core Architecture & Design Principles

### 2.1 The Two Execution Layers

| Layer | Role | Always On? | Details |
|-------|------|------------|---------|
| **Mac (Laptop)** | Development, testing, Mac-specific APIs | No — closed during work hours, hospital stays | Claude Code runs here. Flask PA API on port 5011. Launchd scheduling. |
| **EC2 (AWS)** | 24/7 execution, Telegram bot, cron jobs, n8n | Yes | IP: `34.193.98.97`. SSH: `ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97`. All autonomous systems run here. |

**Important reality check:** The original architecture was "laptop-first." In practice, **EC2 is the primary execution environment**. The Mac is for development; EC2 is where the business runs. Git is the sync mechanism between them.

### 2.2 Multi-Tower Structure

Each "tower" is an independent business unit with its own `src/`, `workflows/`, `VERSION`, and `README.md`. All towers live in a **single git repository** (`dev-sandbox/`) — no nested git repos allowed.

| Tower | Domain | Version | Maturity | Python Files | Lines |
|-------|--------|---------|----------|-------------|-------|
| **lead-generation** | Lead scraping, SMS outreach, sales pipeline | 1.1.0 | Mature | 101 | ~45,000 |
| **personal-assistant** | Email, calendar, digests, goal tracking | 1.2.0 | Mature | 47 | ~21,000 |
| **fitness-influencer** | Video editing, content creation, coaching, PDF engine | 1.0.0-dev | Partial | 137 | ~60,000 |
| **ai-systems** | AI infrastructure, orchestration, monitoring | 1.2.0 → 1.3.1 | Partial | 36 | ~13,500 |
| **amazon-seller** | SP-API integration, inventory, fees | 1.0.0-dev | Stub | 17 | ~4,500 |
| **mcp-services** | MCP servers for Apollo, Canva, Twilio, Upwork | 1.0.0-dev | Stub | 23 | ~7,300 |

**Total:** ~353 Python files, ~225,000+ lines of code across all towers.

**Shared resources:**
- `execution/` — 76 Python files (~35,000 lines) used by 2+ towers. Key: `pipeline_db.py`, `cross_tower_sync.py`, `safe_git_save.py`, `branded_pdf_engine.py`, `agent_bridge_api.py` (4,358 lines — still monolithic).
- `projects/shared/` — Multi-tenant tools: API Key Manager, MD-to-PDF, Photo Processor, Resume Builder.
- `scripts/` — 47 shell scripts + 45 Python scripts for operations and deployment.

### 2.3 Telegram as Central UI

William does not use terminals, dashboards, or web apps for daily operations. **Telegram is the primary interface**, via @w_marceaubot (Clawdbot). This is non-negotiable per rule E10 (Best-Path Evaluation).

The interface hierarchy:
1. **Telegram** — for all conversational commands, status checks, approvals
2. **SMS** — for HOT lead alerts (Twilio, +1-855-239-9364)
3. **Email** — for proposals, agreements, branded PDFs (wmarceau@marceausolutions.com)
4. **Branded PDF** — for any document a client or William would read
5. **Web app** — only for dashboards (FitAI at fitai.marceausolutions.com)
6. **CLI** — NEVER for William. Only acceptable for automation-to-automation calls.

### 2.4 Four-Agent System

| Agent | Platform | Role | Status |
|-------|----------|------|--------|
| **Claude Code** | Mac terminal / VS Code | Development, architecture, code authoring | Active |
| **Clawdbot (Panacea)** | EC2 — Node.js systemd service | Telegram interface, pipeline queries, accountability, notifications | Active 24/7 |
| **Ralph** | EC2 — PRD-driven autonomous builder | Builds features from PRD JSON files, commits to GitHub | Dormant since Jan 28, 2026 |
| **Grok** | External (x.ai API + conversation) | Strategic advisor, architecture decisions, priority setting | Active (advisory only) |

**Agent coordination is the weakest part of the system.** Communication happens via:
- `pipeline.db` — primitive message bus (deals, activities, tower_requests tables)
- `HANDOFF.md` — manual, git-based task handoff
- `tower_protocol.py` — tower_requests table (underdeveloped)
- `agent_comms.py` — endpoints exist but are NOT actively used

There is no event bus, no pub/sub, no reliable handoff protocol. This is a known gap.

### 2.5 Protected Components

These files are **blocked from modification** by the goal_runner safety mechanism. Any command touching them is rejected with "BLOCKED: Command touches protected autonomous core file":

| File | Why It's Protected |
|------|-------------------|
| `projects/lead-generation/src/daily_loop.py` | 9-stage autonomous lead acquisition — the revenue engine |
| `projects/personal-assistant/src/unified_morning_digest.py` | William's daily briefing — his window into the business |
| `projects/personal-assistant/src/system_health_check.py` | Detects when things break before William notices |
| `projects/lead-generation/src/hot_lead_handler.py` | HOT lead SMS alerts — the thing that actually closes deals |
| `execution/safe_git_save.py` | Prevents accidental secret leaks and force-pushes |

Additionally protected (by convention and CLAUDE.md rules):
- `goal_manager.py` — long-term vision is locked (`protected: true`)
- All launchd plist files — Mac scheduling
- All systemd service files — EC2 scheduling
- Branded PDF workflow (`branded_pdf_engine.py` + 10 templates)
- Verified Telegram commands (46+ routes in `clawdbot_handlers.py`)
- `.env` files — never committed, never staged by safe_git_save

### 2.6 Brand Standards

- **Tagline:** "Embrace the Pain & Defy the Odds"
- **Colors:** Dark + Gold `#C9963C` / `#333333`
- **NEVER use:** Green `#22c55e`
- **All client-facing documents:** Branded PDF via `branded_pdf_engine.py`
- **Email:** wmarceau@marceausolutions.com (Google Workspace — ALWAYS use this)
- **Phone:** +1 (239) 398-5676 (personal) | +1 (855) 239-9364 (Twilio, A2P registered)
- **Calendly:** `calendly.com/wmarceau/ai-services-discovery` (AI) | `calendly.com/wmarceau/free-fitness-strategy-call` (fitness)

---

## 3. Key Components & Current State (March 31, 2026)

### 3.1 PA Handler Service (EC2 Port 8786)

**What:** FastAPI wrapper around `clawdbot_handlers.py`, running as systemd service on EC2.

**File:** `/home/clawdbot/pa-handlers/main.py` (66 lines)

```python
# Sets REPO_ROOT, loads .env, imports clawdbot_handlers
# Endpoints: GET /health, POST /route, POST /message, GET /commands
app = FastAPI(title="PA Handler Service", version="2.0")
```

**Systemd:** `/etc/systemd/system/pa-handlers.service` — User=clawdbot, Restart=always, RestartSec=5

**Status:** HEALTHY. Verified working on March 31. Returns 46+ command routes.

**Key Routes in clawdbot_handlers.py (2,285 lines):**

| Category | Commands | Function |
|----------|----------|----------|
| Pipeline | "leads", "pipeline", "deals" | `handle_leads()` — shows hot/warm/cold deals |
| Next Action | "next", "what should i do" | `handle_next()` — ROI-prioritized action |
| Call Prep | "call prep [company]", "who should i call" | `handle_call_prep()`, `handle_call_scripts()` |
| Demo | "demo [industry]" | `handle_demo()` — Grok-powered AI demo generation |
| Proposals | "proposal [company]", "send proposal" | `handle_proposal()`, `handle_send_proposal()` |
| Agreements | "agreement [company]" | `handle_agreement()` — generates service agreement |
| Onboarding | "onboard [company]" | `handle_onboard()` — Stripe link + welcome email |
| Outcomes | "result [company]: [outcome]" | `handle_outcome()` — feeds learning system |
| Learning | "what have you learned" | `handle_learned()` — shows outcome insights |
| Goals | "goals", "goal [action]" | `handle_goals()` — dynamic goal management |
| Away Mode | "away status" | `handle_away_status()` — hospital/work mode |
| Decisions | "decisions", "anything need me" | `handle_decisions()` — items requiring human judgment |
| Schedule | "schedule", "what's my schedule" | `handle_schedule()` — today's plan |
| Digest | "digest", "morning briefing" | `handle_digest()` — full morning digest |
| Health | "health", "system status" | `handle_health()` — 10-component check |
| Reactivate | "reactivate [company]" | `handle_reactivate()` — re-engage cold leads |
| Tasks | "tasks" | `handle_tasks()` — pending tasks |
| Help | "help", "commands" | `handle_help()` — lists all commands |

**Conversational intent parser** (`_parse_conversational_intent()`) handles natural language: "hows the business", "dolphin said they want a proposal", "anything need me today".

### 3.2 Clawdbot (Telegram Bot)

**What:** Node.js CLI tool (not a Go binary, not a Python script) running as systemd service on EC2. Uses Claude Max OAuth for AI responses. Memory via Ollama embeddings (nomic-embed-text, localhost:11434).

**Configuration:** `/home/clawdbot/.clawdbot/clawdbot.json`
- Bot token: `8596701493:AAH...`
- Bot username: `@w_marceaubot`
- William's chat ID: `5692454753`

**Telegram protocol:** Polling (getUpdates), NOT webhooks. Neither Clawdbot nor n8n registers a webhook URL with Telegram. Polling is simpler — no public endpoint needed, no SSL routing for Telegram traffic.

**Message flow:**
```
William (Telegram) → Telegram API → Clawdbot polls getUpdates
  → Accountability parser (Rules 1-8, 4-hour context window)
  → If no match: POST http://127.0.0.1:8786/route → clawdbot_handlers.route_message()
  → Response → Telegram sendMessage API → William sees reply
```

**Accountability system (3 n8n workflows):**

| Workflow | n8n ID | Schedule | What It Does |
|----------|--------|----------|--------------|
| Morning-Accountability-Checkin | `XNrR99vPCUp89X8L` | 6:45am ET Mon-Fri | Sends day context + energy prompt |
| EOD-Accountability-Checkin | `0Zf8nNv1AphA0W6s` | 7:00pm ET Mon-Fri | Sends "reply with your numbers" prompt |
| Weekly-Accountability-Report | `krxeoSZMMPBZGAPv` | 7:00pm ET Sunday | Weekly scorecard to Telegram |

**Accountability parser rules (priority order):**

| Rule | Pattern | Action |
|------|---------|--------|
| 1 | Single number 1-10 | Log morning energy to Sheets |
| 2 | 4 comma-separated numbers | Log EOD metrics (outreach, meetings, videos, content) |
| 3 | "status" / "scorecard" | Return current metrics |
| 4 | Single large number (>10) | Outreach count only |
| 5 | "note: [text]" | Append to Notes column |
| 6 | "trained" / "gym done" | Set Training_Session = true |
| 7 | "done" | Context-dependent |
| 8 | "fix [field] [value]" | Update existing row |

**Known issue:** The n8n Telegram credential (`RlAwU3xzcX4hifgj`) periodically goes stale/corrupted after SSH sessions. Must be re-patched via Python urllib from Mac only. Auto-monitored by `health_check.py`.

### 3.3 Daily Loop (Lead Acquisition Engine)

**File:** `projects/lead-generation/src/daily_loop.py` (991 lines) — **PROTECTED**

**Schedule:** Cron at 9am ET Mon-Fri (13:00 UTC)

**9 Stages:**

| Stage | Name | What It Does |
|-------|------|--------------|
| 0 | COMPLIANCE | Reads CLAUDE.md rules, enforces research-first |
| 0.5 | LEAD GEN | Weekly lead list generation (Mondays only) |
| 1 | DISCOVER | Process leads from pool |
| 2 | SCORE | ML scoring, select top 20% |
| 3 | ENRICH | Verify contact info (Hunter.io, Snov.io waterfall) |
| 4 | OUTREACH | Send initial emails (10/day cap, TCPA hours) |
| 5 | MONITOR | Check Gmail + Twilio for replies |
| 6 | CLASSIFY | Hot/Warm/Cold classification |
| 7 | FOLLOW-UP | 3-touch sequences for non-responders |
| 8 | REPORT | Telegram digest with results |

**Self-monitoring:** Tracks runs in `loop_health.json`, alerts via Telegram after 2 consecutive critical failures, keeps 14-day history.

### 3.4 Morning Digest

**File:** `projects/personal-assistant/src/unified_morning_digest.py` (771 lines) — **PROTECTED**

**Schedule:** Cron at 6:30am ET daily

**Aggregates:**
- Pipeline status (hot leads, stale proposals, deal counts)
- Gmail inbox (unread count, priority emails)
- Google Calendar (today's events)
- Twilio SMS replies
- Goal progress
- Learned preferences (from outcome_learner)
- Stale proposal warnings

**Output:** Single formatted Telegram message with top 3-5 action items.

### 3.5 Pipeline Database (pipeline.db)

**File:** `execution/pipeline_db.py` (636 lines) — SQLite with WAL mode, foreign keys enabled

**Tables:**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `deals` | Sales pipeline | id, tower, company, contact_name, contact_phone, contact_email, industry, stage, proposal_amount, monthly_fee, close_date |
| `outreach_log` | Communication history | deal_id, channel, message_summary, response, follow_up_date |
| `activities` | Deal activity log | deal_id, tower, activity_type, description |
| `proposals` | Proposal tracking | deal_id, title, setup_fee, monthly_fee, pdf_path, status (draft/sent/viewed/accepted/rejected) |
| `call_briefs` | Pre-call research | deal_id, company_research, pain_points, talking_points |
| `trial_metrics` | Trial period data | deal_id, missed_calls, texts_sent, replies, calls_recovered |
| `scheduled_outcomes` | Outcome tracking | deal_id, task_type, scheduled_date, outcome, resulted_in |
| `referrals` | Referral tracking | from_deal_id, referred_company, tower, status |

**Current state:** 205 active deals (108 Contacted, 81 Intake). 5 outcomes recorded (self-improvement threshold met).

**Sync:** Mac → EC2 via `scripts/sync_pipeline_to_ec2.sh` (SCP + service restart). EC2 copy at `/home/clawdbot/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db`.

### 3.6 Self-Improving Learning System

**File:** `projects/personal-assistant/src/outcome_learner.py` (320 lines)

**Current learned preferences** (from `learned_preferences.json`):
```json
{
  "total_outcomes": 5,
  "best_channel": "Call",
  "best_channel_rate": 90.6,
  "recommended_action": "call",
  "industry_rankings": [
    {"industry": "HVAC", "conversion_pct": 100.0, "total": 2}
  ],
  "insights": [
    "Best channel: Call (90.6% response rate)",
    "Stop using: Email (0% response rate after 242 attempts)"
  ]
}
```

**How it works:**
1. William records an outcome: "result Antimidators: meeting_booked" via Telegram
2. `handle_outcome()` saves to `scheduled_outcomes` table
3. `outcome_learner.py` recalculates preferences → saves to `learned_preferences.json`
4. `cross_tower_sync.py` reads preferences → adjusts follow-up timing (3 days default, 2 days with 5+ outcomes)
5. Morning digest references learned preferences for recommendations
6. Daily scheduler adjusts ROI tiers based on industry conversion rates

**Status:** Active with 5 outcomes. Learning is ON. The critical insight already discovered: **calls work, email doesn't** (90.6% vs 0% response rate).

### 3.7 Goal Manager

**File:** `projects/personal-assistant/src/goal_manager.py` (474 lines)

**Features:**
- CRUD for short/medium/long-term goals
- Natural language parsing ("goal short: Land 2 clients by April 15")
- Dynamic deadline extraction
- Vision protection (long-term goal is locked, `protected: true`)
- Progress integration from `goal_progress.py` (reads pipeline.db)
- Research-first context injection for AI decisions

### 3.8 n8n Workflows

**URL:** https://n8n.marceausolutions.com (port 5678 on EC2)
**Stats:** 76 total workflows (67 active)
**Self-Annealing:** Error handler wired to 36/38 workflows (via `Ob7kiVvCnmDHAfNW`)

**Key webhook endpoints (NOT for Telegram — for Stripe/SMS/forms):**
- `/webhook/stripe-payment-welcome` — new client payment
- `/webhook/stripe-cancellation` — subscription cancel
- `/webhook/sms-response` — Twilio inbound SMS
- `/webhook/form-submit` — web form submissions
- 25+ others for follow-ups, hot leads, deliveries

**SSL:** nginx reverse proxy with Let's Encrypt (certbot auto-renew)

### 3.9 EC2 Cron Jobs (17 total)

Key scheduled tasks on EC2 (`clawdbot` user crontab):

| Schedule | Job | Purpose |
|----------|-----|---------|
| 6:30am ET | `unified_morning_digest.py` | Morning Telegram briefing |
| 8:00am ET Monday | `generate_new_lead_list.py` | Weekly lead discovery |
| 9:00am ET Mon-Fri | `daily_loop.py full --for-real` | Full lead acquisition loop |
| Every 30 min | `cross_tower_sync.py --queue-only` | Tower coordination |
| 9:00pm ET | Evening digest | Pipeline summary |
| */5 min | PA health check curl | Service liveness (may conflict with systemd) |

### 3.10 Grok vs Anthropic — What Uses What

| Component | AI Provider | Details |
|-----------|------------|---------|
| Claude Code (Mac) | Anthropic (Opus 4.6) | Development and architecture |
| Clawdbot | Anthropic (Claude Max OAuth) | Telegram conversation AI |
| `handle_demo()` | **Grok (grok-3-mini)** via x.ai API | AI demo generation for prospects |
| `goal_runner.py` | Anthropic (Claude Haiku fallback) | Autonomous goal execution |
| n8n AI nodes | Varies by workflow | Some Anthropic, some Grok |

**Note:** The XAI_API_KEY has intermittent 403 errors. When Grok fails, `goal_runner.py` falls back to Claude Haiku.

### 3.11 Flask PA API (Mac Port 5011)

**File:** `projects/personal-assistant/src/app.py` (234 lines)

**Blueprints:** Gmail, Sheets, SMS, Scheduler, Towers, Health

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/scheduler/today` | GET | Proposed daily plan with ROI blocks |
| `/scheduler/approve` | POST | Create calendar events |
| `/scheduler/digest` | GET | Full morning digest |
| `/scheduler/health-check` | GET | 10-component health check |
| `/gmail/*` | Various | List, read, send, draft, search |
| `/sheets/*` | Various | Read, write, append |
| `/sms/*` | Various | Send, list via Twilio |
| `/towers/process` | POST | Cross-tower request processing |
| `/towers/goals` | GET | Goal progress |
| `/health` | GET | Tower health status |

**Note:** This only runs when the Mac is on. EC2 systems fall back to local execution (importing handlers directly) when the SSH tunnel is down.

### 3.12 Safe Git Save

**File:** `execution/safe_git_save.py` (225 lines) — **PROTECTED**

**Safety rules:**
1. Only stages files already tracked by git (never `git add .`)
2. New files must be added manually first
3. Skips `.env`, `token*.json`, `credentials.json`, `*.db`, `logs/`
4. Pulls before pushing (avoids force-push)
5. Logs every action to `git_save_log.md` (gitignored)
6. Never auto-runs — must be explicitly called

**Never-stage list:** `.env`, `.env.local`, `.env.production`, `token.json`, `token_sheets.json`, `token_marceausolutions.json`, `credentials.json`, all `.db` files, all `.log` files, `node_modules/`, `__pycache__/`.

### 3.13 Fitness Tower Highlights

Despite VERSION 1.0.0-dev, this tower has 137 Python files (~60,000 lines):
- **FitAI:** Live at `fitai.marceausolutions.com` — fitness coaching web app
- **Branded PDF Engine:** `branded_pdf_engine.py` (510 lines) + 13 PDF templates — used by ALL towers for document generation
- **Video Processing:** Jump cuts, B-roll insertion, caption generation, color grading, music mixing
- **Client Management:** Julia (boabfit) and William ($197/mo self-coaching)
- **Stripe Integration:** `stripe_payments.py` (789 lines)
- **No launchd scheduling on Mac** — EC2 cron runs `fitness_daily_loop.py` at 12pm UTC

### 3.14 Execution Directory (Cross-Tower Utilities)

**76 Python files, ~35,000 lines.** Key files:

| File | Lines | Purpose |
|------|-------|---------|
| `agent_bridge_api.py` | 4,358 | Agent communication bridge — still monolithic, target <500 lines |
| `cross_tower_sync.py` | 744 | Inter-tower sync (30-min cron) |
| `pipeline_db.py` | 636 | Pipeline database interface |
| `twilio_handler.py` | 1,045 | SMS/voice handling |
| `email_sequence_engine.py` | 1,028 | Complex email automation |
| `multi_agent_llm.py` | 973 | Multi-agent LLM coordination |
| `branded_pdf_engine.py` | 510 | Templated branded PDF generation |
| `safe_git_save.py` | 225 | Protected git commit wrapper |
| `research_gate.py` | 245 | Pipeline snapshot for AI context injection |
| `tower_protocol.py` | 384 | Inter-tower request queue |
| `goal_runner.py` | 480 | Autonomous goal execution |

---

## 4. Decision History & Trade-offs

### 4.1 Anthropic → Grok/xAI Migration (handle_demo only)

**Decision:** Replace Anthropic API call in `handle_demo()` with Grok (grok-3-mini) via x.ai API.

**Why:** The Anthropic API returned `tool_use` content blocks that the handler wasn't built to parse, causing demo generation to fail. Grok returns plain text completions.

**Trade-off:** Grok's XAI_API_KEY has intermittent 403 errors (William's account issue). Demo generation sometimes fails. However, the handler now works correctly when the API is available.

**What was NOT migrated:** Everything else stays Anthropic — Claude Code (Opus), Clawdbot (Claude Max OAuth), goal_runner (Haiku fallback). Only the demo endpoint changed.

**Incident:** During the Grok switch on March 31, `clawdbot_handlers.py` was accidentally destroyed (reduced from 2,283 lines to 63 lines). Restored from `.backup.20260331-1112`. The surgical replacement was then applied to `handle_demo()` only.

### 4.2 EC2-First Deployment

**Decision:** Run all autonomous systems on EC2, not the Mac.

**Why:** The Mac is closed during work hours (7am-3pm), hospital stays, and sleep. The business cannot stop when the laptop lid closes.

**Trade-off:** Development still happens on Mac (Claude Code), requiring sync scripts. The `sync_pipeline_to_ec2.sh` script handles this, and a PostToolUse hook auto-syncs on every Claude Code action. EC2 → Mac sync is manual (`git pull`).

### 4.3 Polling vs Webhooks (Telegram)

**Decision:** Both Clawdbot and n8n use Telegram polling (getUpdates), not webhooks.

**Why:** Webhooks require a public HTTPS endpoint with valid SSL certificate. While n8n.marceausolutions.com exists with SSL, adding Telegram webhook routing adds complexity. Polling is simpler — Clawdbot just asks Telegram "any new messages?" on a loop.

**Trade-off:** Slightly higher latency (seconds, not milliseconds). Acceptable for a single-user system.

### 4.4 Minimal main.py Wrapper (FastAPI on EC2)

**Decision:** The EC2 PA service is a thin FastAPI wrapper (`main.py`, 66 lines) around the same `clawdbot_handlers.py` used everywhere.

**Why:** Keeps one source of truth for command routing. The wrapper handles HTTP, env loading, and path resolution. The handlers don't need to know they're running behind FastAPI.

**Trade-off:** The handlers must be importable as a plain module (no relative imports, REPO_ROOT env-var aware). This was a source of several bugs during cross-platform deployment.

### 4.5 Pipeline.db as Shared State Bus

**Decision:** SQLite database (`pipeline.db`) serves as the shared state layer between all agents and towers.

**Why:** Simple, portable, no external dependencies. Can be SCP'd between Mac and EC2. WAL mode allows concurrent reads.

**Trade-off:** Not a real message bus. No pub/sub, no event triggers, no transactional guarantees across agents. Tower coordination is eventually consistent at best. This is the system's most significant architectural limitation.

### 4.6 Clawdbot as Node.js (not custom bot)

**Decision:** Use the Clawdbot CLI tool (Node.js, docs.molt.bot/cli) rather than building a custom Telegram bot.

**Why:** Provides built-in Claude Max OAuth, Ollama memory embeddings, complexity scoring, and multi-channel support (Telegram, WhatsApp, iMessage) out of the box.

**Trade-off:** Less control over the bot's internal message processing. The accountability parser and PA handler integration had to be built around Clawdbot's architecture rather than controlling it directly.

### 4.7 Single Git Repository

**Decision:** All towers, scripts, execution utilities, and documentation live in one `dev-sandbox/` git repo.

**Why:** Single source of truth. Easy coordination across towers. No submodule hell. Weekly verification ensures no nested repos appear.

**Trade-off:** Large repo (~225,000 lines). Git operations are slower. Deployment creates separate repos when needed (`~/production/[tower]-prod/`).

### 4.8 Permission/Ownership on EC2

**Decision:** The `clawdbot` user on EC2 has NO Linux password (!! in /etc/shadow). Accessed only via `sudo -u clawdbot` from `ec2-user`.

**Why:** Security. The clawdbot user should only be accessed programmatically, never via SSH password login.

**Trade-off:** Every manual EC2 operation requires `sudo -u clawdbot` prefix. Cron jobs run as clawdbot. Systemd services run as User=clawdbot. The `GATEWAY_AUTH_PASSWORD=marceau2026!` in `.env` is for the Calendar Gateway API, not the Linux user — this caused confusion.

### 4.9 Phased Credential Rollout for Clawdbot

**Decision:** 5-phase credential rollout over 2+ months, starting with file system + git only.

**Phases:**
1. (Current) File system + git only
2. (Week 2-3) Read-only APIs (Google Places, Yelp, Apollo)
3. (Week 4) Low-risk writes (Google Sheets, GitHub)
4. (Week 5-6) SMS/Email with approval workflow
5. (Month 2+) Full autonomy after 30+ days responsible use

**Why:** Trust building. Clawdbot could accidentally send SMS to clients or push bad code.

**Trade-off:** Clawdbot cannot yet independently send emails or SMS — must route through n8n or the PA handler service.

---

## 5. Current Challenges & Blockers

### 5.1 Multi-Agent Coordination Is Ad-Hoc (CRITICAL)

The four agents (Claude Code, Clawdbot, Ralph, Grok) have **no reliable coordination protocol**. Current mechanisms:

| Mechanism | Problem |
|-----------|---------|
| `pipeline.db` | Primitive — no events, no pub/sub, no delivery guarantees |
| `HANDOFF.md` | Manual, git-based, rarely updated |
| `agent_comms.py` | Endpoints exist but are NOT used |
| `tower_protocol.py` | Only used for cross-sell triggers |
| Ralph | **Dormant since January 28** — no active PRD work |

**Impact:** Agents duplicate work, miss handoffs, and William becomes the manual coordinator.

### 5.2 The agent_bridge_api.py Monolith

At 4,358 lines, this file is the largest in the codebase and should be <500 lines (routing only). It accumulates functionality that belongs in towers. Decomposition has been identified as P2 priority but hasn't happened.

### 5.3 XAI API Key Intermittent 403s

The Grok API key periodically returns 403 Forbidden. This affects `handle_demo()` (prospect demo generation) and is a William account issue, not a code issue. The `goal_runner.py` falls back to Claude Haiku, but `handle_demo()` has no fallback — it just fails.

### 5.4 EC2 Cron vs Systemd Conflict

The PA health-check cron (`*/5 * * * * curl -sf http://127.0.0.1:8786/health || restart`) may conflict with the new systemd service (`Restart=always`). Both try to restart the service when it's down. Should remove the cron entry.

### 5.5 Mac/EC2 Sync Is Fragile

- Mac → EC2: PostToolUse hook + `sync_pipeline_to_ec2.sh` (works)
- EC2 → Mac: Manual `git pull` (often forgotten)
- Risk: Mac and EC2 copies of pipeline.db, handlers, or goals.json can diverge

### 5.6 Only 3 of 6 Towers Are Operational

| Tower | Status | Gap |
|-------|--------|-----|
| lead-generation | Mature | None |
| personal-assistant | Mature | None |
| fitness-influencer | Partial | No Mac launchd scheduling. VERSION still 1.0.0-dev despite 137 files. |
| ai-systems | Partial | Flask endpoints exist but not deployed as running service |
| amazon-seller | Stub | No cron, no deployment, no active use |
| mcp-services | Stub | MCP servers built but not published or deployed |

### 5.7 Outcome Data Is Still Thin

5 outcomes recorded (threshold met), but the learning system needs volume to be truly useful. Current insight ("calls work, email doesn't") is valuable but based on small sample. William needs to make more calls and record results.

### 5.8 n8n Telegram Credential Staleness

The Telegram credential in n8n (`RlAwU3xzcX4hifgj`) periodically corrupts. Must be re-patched from Mac via Python urllib (SSH corrupts the encrypted format). This is a recurring operational annoyance.

### 5.9 Documentation vs Reality Drift

The CLAUDE.md describes a "laptop-first" architecture. Reality is EC2-first. The THREE-AGENT-ARCHITECTURE.md describes active Ralph participation. Ralph has been dormant for 2 months. Several docs reference endpoints, workflows, or file paths that have moved or been renamed. The system audits (March 29, 30, 31) are the most accurate snapshots.

---

## 6. How to Work With This Project Effectively

### 6.1 Session Start Checklist (MANDATORY for all agents)

1. `git pull origin main` — sync latest
2. Read `docs/SYSTEM-STATE.md` — live infrastructure state
3. Read `HANDOFF.md` — pending tasks between agents
4. Read `docs/ARCHITECTURE-DECISIONS.md` — conventions
5. Read `projects/personal-assistant/data/goals.json` — current priorities
6. Check this document for full context

**DO NOT REDO** anything listed as completed in SYSTEM-STATE.md (Sessions 1-12).

### 6.2 Rules That Will Save You Hours

| Rule | What It Means | Source |
|------|--------------|--------|
| **E10: Best-Path Evaluation** | Never build CLI tools for William. Always Telegram, SMS, PDF, or web app. Answer the 5 questions first. | `rules/behavioral/E10-best-path.md` |
| **E12: Code to Production** | It's not "built" until William uses it from his phone. Deploy fully or it's not done. | `rules/behavioral/E12-code-to-production.md` |
| **E05: Use APIs Never Delegate** | Don't tell William to "go to this website and click..." — use the API directly. | `rules/behavioral/E05-use-apis-never-delegate.md` |
| **E09: Preflight** | Before building anything, search `execution/` for existing solutions. | `rules/behavioral/E09-preflight.md` |
| **Research-First** | Check pipeline.db and outcomes before recommending approaches. Push back with data. | `CLAUDE.md` |
| **No False Completion** | "Partially done" is honest. "Complete" when it's not is a trust violation. | `CLAUDE.md` |
| **Fix Don't Workaround** | Find root cause. Don't bypass safety checks (--no-verify). Don't add shims. | Memory: `feedback_fix_dont_workaround.md` |
| **Sprint Through Finish** | Don't stop at "code written." Verify from William's perspective. | Memory: `feedback_sprint_through_finish.md` |
| **Deliver to Phone** | Auto-send outputs to phone: SMS for links, email for PDFs. Never just save locally. | Memory: `feedback_deliver_to_phone.md` |
| **Validate Leads** | Deep-validate leads before outreach. Target decision-makers, not reception. | Memory: `feedback_validate_leads_before_outreach.md` |
| **Never Fabricate Outreach** | NEVER say "email sent" or "called yesterday" without PROOF from outreach_log. March 25 incident damaged credibility. | Memory: `feedback_never_fabricate_outreach.md` |

### 6.3 Code Placement Decision Tree

```
Is this script used by 2+ projects?
  YES → execution/
  NO  → projects/[tower]/src/
  UNSURE → Start in projects/[tower]/src/, promote later

Is this a user-facing feature?
  YES → E10 evaluation: Clawdbot command > n8n workflow > web app > PDF > email
  NO  → Python module called by automation (OK as internal script)

Does this generate a document?
  YES → branded_pdf_engine.py with template (NEVER plain markdown)
  NO  → Standard Python module
```

### 6.4 Safe Git Save Protocol

```bash
# Standard commit
bash scripts/save.sh "Added daily loop"

# Preview without committing
bash scripts/save.sh --dry-run

# Include new files
bash scripts/save.sh --include-new "message"
```

**NEVER:**
- `git add .` or `git add -A` (leaks secrets)
- `git push --force` (destroys history)
- Stage `.env`, `token*.json`, `credentials.json`, `*.db`

### 6.5 EC2 Operations

```bash
# SSH to EC2
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97

# Run command as clawdbot
sudo -u clawdbot [command]

# Check PA service
curl http://127.0.0.1:8786/health

# Check n8n
curl https://n8n.marceausolutions.com

# Sync pipeline to EC2
bash scripts/sync_pipeline_to_ec2.sh

# Health check
python3 scripts/health_check.py
```

### 6.6 Calendar Rules

- **Time Blocks** calendar (non-primary): Daily routine schedule
- **Primary** calendar: Appointments, milestones
- **wmarceau26@gmail.com**: Therapy only
- **NO default reminders** on Time Blocks entries
- **Training window:** 6-8pm daily (protected)
- **Calendar Gateway:** EC2 port 5015 — validates all agent calendar operations
- **Post-April 6:** All scheduled blocks between 3pm-10pm only (7am-3pm is Collier County)

### 6.7 Protecting the Autonomous Core

Before modifying ANY of these files, ask William for explicit approval:

1. `daily_loop.py` — the revenue engine
2. `unified_morning_digest.py` — William's daily window
3. `system_health_check.py` — the watchdog
4. `hot_lead_handler.py` — the deal closer
5. `safe_git_save.py` — the safety net

The `goal_runner.py` will **block** any command that touches these files automatically.

---

## 7. Glossary of Key Terms & Files

### Terms

| Term | Definition |
|------|-----------|
| **Tower** | Independent business unit with own src/, workflows/, VERSION. Lives under `projects/`. |
| **Daily Loop** | 9-stage autonomous lead acquisition cycle. Runs at 9am ET Mon-Fri. |
| **HOT Lead** | A lead that responded positively. Triggers SMS alert to William with 1/2/3 reply options. |
| **Pipeline.db** | SQLite database — shared state between all agents and towers. 8 tables. |
| **Outcome** | Result of a sales interaction. Feeds learning system. Valid: conversation, meeting_booked, proposal_sent, client_won, callback, no_show, not_interested. |
| **Learned Preferences** | JSON file of insights derived from outcomes. Currently: calls > email, HVAC converts best. |
| **Tower Protocol** | Inter-tower request queue in pipeline.db `tower_requests` table. |
| **Cross-Tower Sync** | 30-min cron that processes tower requests, checks goals, monitors deals. |
| **Research Gate** | `research_gate.py` — provides pipeline snapshot + outreach effectiveness for AI context injection. |
| **E10** | Rule: Never default to easiest implementation. Answer 5 evaluation questions first. |
| **Safe Git Save** | Protected commit script. Never stages secrets, never force-pushes. |
| **A2P** | Application-to-Person — Twilio's registered SMS type for business messaging. |
| **Clawdbot** | Node.js Telegram bot on EC2. William's primary interface to the entire system. |
| **Panacea** | Alternative name for Clawdbot (used in some docs). |
| **Ralph** | PRD-driven autonomous builder agent on EC2. Currently dormant. |
| **REPO_ROOT** | Environment variable for cross-platform path resolution. Mac auto-detects; EC2 sets to `/home/clawdbot`. |
| **PostToolUse Hook** | Auto-syncs Mac → EC2 on every Claude Code tool action. |
| **Calendar Gateway** | EC2 port 5015 — validates/enforces calendar rules for all agents. |
| **Scorecard Sheet** | Google Sheets (`1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o`) — accountability data from n8n. |

### Key Files Quick Reference

| File | Location | Purpose |
|------|----------|---------|
| `CLAUDE.md` | Root | Master architecture rules |
| `HANDOFF.md` | Root | Agent task handoff queue |
| `goals.json` | `projects/personal-assistant/data/` | Goal hierarchy (protected vision) |
| `learned_preferences.json` | `projects/personal-assistant/data/` | Outcome learning data |
| `pipeline.db` | `projects/lead-generation/sales-pipeline/data/` | Canonical deal database |
| `clawdbot_handlers.py` | `projects/personal-assistant/src/` | 46+ Telegram command routes (2,285 lines) |
| `daily_loop.py` | `projects/lead-generation/src/` | 9-stage lead acquisition (991 lines, PROTECTED) |
| `unified_morning_digest.py` | `projects/personal-assistant/src/` | Morning briefing aggregator (771 lines, PROTECTED) |
| `hot_lead_handler.py` | `projects/lead-generation/src/` | HOT lead SMS alerts (267 lines, PROTECTED) |
| `cross_tower_sync.py` | `execution/` | Tower coordination (744 lines) |
| `pipeline_db.py` | `execution/` | Database interface (636 lines) |
| `safe_git_save.py` | `execution/` | Safe commit wrapper (225 lines, PROTECTED) |
| `branded_pdf_engine.py` | `execution/` | Branded document generation (510 lines) |
| `agent_bridge_api.py` | `execution/` | Agent bridge — monolithic, needs decomposition (4,358 lines) |
| `goal_manager.py` | `projects/personal-assistant/src/` | Dynamic goal CRUD with vision protection (474 lines) |
| `outcome_learner.py` | `projects/personal-assistant/src/` | Self-improving outcome analysis (320 lines) |
| `app.py` | `projects/personal-assistant/src/` | Flask PA API — Mac port 5011 (234 lines) |
| `main.py` | EC2: `/home/clawdbot/pa-handlers/` | FastAPI wrapper — EC2 port 8786 (66 lines) |
| `health_check.py` | `scripts/` | Full system health dashboard (1,038 lines) |
| `sync_pipeline_to_ec2.sh` | `scripts/` | Mac → EC2 database + code sync |
| `SYSTEM-STATE.md` | `docs/` | Live infrastructure state (DO NOT REDO completed items) |
| `THREE-AGENT-ARCHITECTURE.md` | `docs/` | Multi-agent design doc |
| `ARCHITECTURE-DECISIONS.md` | `docs/` | Conventions, sync rules, quality standards |
| `CLAWDBOT-PA-INTEGRATION.md` | `docs/` | Telegram → PA handler integration spec |

### EC2 Services Quick Reference

| Port | Service | Status |
|------|---------|--------|
| 5678 | n8n | Active |
| 5011 | PA Flask (via SSH tunnel from Mac) | Mac-dependent |
| 5015 | Calendar Gateway | Active |
| 5020 | mem0-api (shared agent memory) | Active |
| 8786 | PA Handler Service (FastAPI) | Active (systemd) |
| 11434 | Ollama (embeddings) | Active |

### SOPs Quick Reference (33 total, see `docs/sops/INDEX.md`)

Critical SOPs for multi-agent work:
- **SOP 27:** Clawdbot Usage
- **SOP 28:** Ralph Usage
- **SOP 29:** Three-Agent Collaboration
- **SOP 33:** Pre-Flight Checklist (mandatory before EVERY task)

---

## Final Assessment: System Readiness

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Lead Acquisition** | 9/10 | Daily loop, weekly lead gen, response monitoring — all working |
| **Morning Briefing** | 9/10 | Aggregates all data sources, sends at 6:30am |
| **Sales Pipeline** | 8/10 | 205 deals tracked, proposals, call prep, outcomes |
| **Self-Improvement** | 6/10 | Framework working, but only 5 outcomes — needs volume |
| **Multi-Agent Coordination** | 3/10 | Ad-hoc, no event bus, Ralph dormant, HANDOFF.md manual |
| **Client Delivery** | 7/10 | Stripe, onboarding, agreements — built but untested with real client |
| **Mac Independence** | 8/10 | All critical systems run on EC2. Mac needed only for development. |
| **Documentation** | 7/10 | Extensive but drifted from reality in places. Audits are most accurate. |

**Bottom line:** The system is **85% ready** for autonomous operation. The revenue engine (daily loop + hot lead handler + morning digest) works. The critical gap is multi-agent coordination and outcome volume. William needs to make calls, record results, and close deals — the system can't do that part for him.

---

*This document should be re-audited monthly or after any major architectural change. Last verified: March 31, 2026.*
