# Rebuild Gap Analysis: CLAUDE.md vs Current State

**Date**: 2026-03-26 | **Updated**: 2026-04-04 (Anthropic OAuth policy change + audit findings)
**Analysis**: Strategic audit of dev-sandbox against CLAUDE.md multi-tower architecture

## Executive Summary

Current dev-sandbox has **architectural violations** that prevent maximum leverage. The system contains monolithic API servers, cross-tower dependencies, improper tower implementations, and orphaned code from restructuring. A comprehensive audit on 2026-04-03 confirmed the original 5-action plan and added specific findings. On 2026-04-04, Anthropic's OAuth policy change added an urgent infrastructure item (#6).

**Key Finding**: 466KB monolithic Flask server (`agent_bridge_api.py`) contains 100+ endpoints that should be distributed across towers — this single file violates the entire tower independence principle.

**Urgent Finding (2026-04-04)**: Anthropic banned OAuth token usage in third-party tools effective April 4. Clawdbot uses the `@clawdbot/anthropic` molt.bot plugin with Max OAuth tokens (`sk-ant-oat01-...`) — this is now a ToS violation and may already be blocked. Must migrate to either `claude` CLI subprocess calls (zero cost) or API key auth (usage-billed).

## What Has Been Fixed (2026-04-03 Audit Session)

- Recovered lost `/gmail/draft` and `/gmail/search-all` endpoints in `agent_bridge_api.py`
- Recovered `run_full_pipeline()` in sales pipeline orchestrator (was called but never defined)
- Archived stale task trackers: KANBAN.md, TASKS.md, DOCKET.md, focus_chain, NEXT-STEPS-HYBRID-ARCHITECTURE.md
- BoabFit fully re-established (SSL, webhooks, drip system, file recovery)
- HANDOFF.md is now the single source of truth for pending tasks

## Detailed Gap Analysis

### 1. Tower Structure Compliance

#### Compliant Elements
- All 6 core towers exist: `ai-systems/`, `amazon-seller/`, `fitness-influencer/`, `lead-generation/`, `mcp-services/`, `personal-assistant/`
- `boabfit/` exists as active client tower (reinstated 2026-03-31)
- Basic directory structure follows CLAUDE.md
- VERSION and README.md files present in most towers

#### Critical Violations

**amazon-seller Tower:**
- Contains full MCP server implementation (should be in mcp-services)
- `src/LegalAgreement/` and `src/BJKPaperTrail/` contain unrelated files
- CLAUDE.md buried in `src/` instead of tower root
- VERSION still `1.0.0-dev` despite published PyPI package

**fitness-influencer Tower:**
- Contains complete Flask web application (routes, database, templates)
- `social-media/src/` has HVAC campaign code that belongs in `lead-generation/`
- No CLAUDE.md at tower root
- VERSION stuck at `1.0.0-dev` despite substantial code

**ai-systems Tower:**
- `src/` contains website HTML, fire performer images, resume builder
- `src/website-builder/` and `src/web-dev/` are full sub-projects
- `ai-customer-service/` is a complete sub-tower with own CLAUDE.md
- Three different `app.py` files at different nesting levels

**8 of 9 towers missing CLAUDE.md at root** — only ai-systems and boabfit have one.

### 2. Shared Utilities (execution/) Analysis — Updated

#### 15 Tower-Specific Files That Should Move

| File | Belongs In |
|------|-----------|
| `coaching_client_manager.py` | `marceau-solutions/fitness/src/` |
| `coaching_daily_loop.py` | `marceau-solutions/fitness/src/` |
| `coaching_schema.py` | `marceau-solutions/fitness/src/` |
| `webdev_daily_loop.py` | `marceau-solutions/digital/src/` |
| `webdev_project_manager.py` | `marceau-solutions/digital/src/` |
| `batch_outreach.py` | `lead-generation/src/` |
| `followup_prioritizer.py` | `lead-generation/src/` |
| `log_outreach.py` | `lead-generation/src/` |
| `email_sequence_engine.py` | `lead-generation/src/` |
| `daily_priorities_cron.py` | `lead-generation/src/` |
| `voice_engine.py` | `lead-generation/src/` or `ai-systems/src/` |
| `voice_ai_prompts.py` | `lead-generation/src/` |
| `voice_ai_reporter.py` | `lead-generation/src/` |
| `client_questionnaire.py` | Delete — exact copy already in `fitness-influencer/src/` |
| `questionnaire_response_watcher.py` | Delete — exact copy already in `fitness-influencer/src/` |

#### 9 Exact-Duplicate Files (byte-for-byte identical in execution/ and tower src/)

| File | Duplicate Location | Action |
|------|-------------------|--------|
| `twilio_inbox_monitor.py` | `lead-generation/src/` | Delete tower copy |
| `gmail_reply_watcher.py` | `personal-assistant/src/` | Delete tower copy |
| `twilio_sms.py` | `lead-generation/src/` | Delete tower copy |
| `branded_pdf_engine.py` | `fitness-influencer/src/` | Delete tower copy |
| `pdf_router.py` | `fitness-influencer/src/` | Delete tower copy |
| `client_questionnaire.py` | `fitness-influencer/src/` | Delete execution/ copy |
| `questionnaire_response_watcher.py` | `fitness-influencer/src/` | Delete execution/ copy |
| `revenue_analytics.py` | `fitness-influencer/src/` | Delete tower copy |
| `google_auth_setup.py` | `fitness-influencer/src/` | Delete tower copy |

#### Broken Import Chains

| Script | Broken Import | Real Location |
|--------|--------------|---------------|
| 6+ files in lead-generation/src/ | `from execution.auto_iterator import ...` | `projects/lead-generation/src/auto_iterator.py` |
| 3 scripts in scripts/ | `from execution.stripe_payments import ...` | `projects/fitness-influencer/src/stripe_payments.py` |

### 3. Code Fragmentation

**BoabFit split across 3 locations** (FIXED — consolidated to `projects/boabfit/` as primary):
- `projects/boabfit/` — primary tower
- `projects/shared/boabfit/` — requirements doc
- `projects/shared/client-lead-systems/boabfit/` — lead nurture Flask service

**Flames of Passion split across 3 locations:**
- `client-sites/flamesofpassionentertainment.com/`
- `projects/flames-of-passion/`
- `projects/ai-systems/src/assets/images/` (fire performer images)

**Website builder documented at wrong path:**
- Docs reference `projects/website-builder/` — actual code at `projects/ai-systems/src/website-builder/`

### 4. Root-Level Cleanup Needed

| File | Where It Belongs |
|------|-----------------|
| `git_save_log.md` | `logs/` |
| `lead-magnet-capture-export.json` | `data/` or `projects/lead-generation/data/` |
| `premium-waitlist-capture-export.json` | `data/` or `projects/lead-generation/data/` |
| `COACHING_TRACKER_SHEET_ID.txt` | `config/` |
| `SOCIAL_MEDIA_SHEET_ID.txt` | `config/` |
| `marceau-favicon-32x32.png` | `assets/` |
| `marceau-favicon.ico` | `assets/` |
| `make-pdf.sh` | `scripts/` |
| `COMPANY_ON_LAPTOP_FULL_CONTEXT_SUMMARY.md` | `docs/archive/` |
| `MAC-MINI-VS-EC2-ANALYSIS.md` | `docs/archive/` |

### 5. Orphaned Directives

**14 directives in `directives/` with no matching tower:**
- `ai-customer-service.md`, `fitness_influencer_operations.md`, `hvac_distributors.md`, `mcp_aggregator.md`, `onboard_client.md`, `sales_crm.md`, `email_analyzer.md`, `interview_prep.md`, `uber_lyft_comparison.md`, `website-tool-integration.md`, `convert_markdown_to_pdf.md`, `generate_naples_weather_report.md`, `md_to_pdf.md`, `pptx_interactive_edit.md`

These are mostly **skill directives**, not tower directives. They should be in a separate directory (e.g., `directives/skills/`).

## Action Plan: Prioritized 5-Item Implementation

### #1 CRITICAL: Dismantle Monolithic API Server
**Status:** 0% — Not started
**Why**: `agent_bridge_api.py` is the single largest architectural violation (13,200+ lines)
**Risk**: HIGH — this is the n8n Python Bridge, breaking it breaks all automations
**Action**:
- Extract Gmail endpoints → `personal-assistant/src/gmail_api.py`
- Extract SMS endpoints → `lead-generation/src/sms_api.py`
- Extract file/git operations → `ai-systems/src/file_operations.py`
- Extract n8n/ClickUp → appropriate towers
- **Do NOT delete** until all n8n workflows are re-pointed
- Must be done incrementally — one endpoint group at a time with testing

### #2 REBUILD: Tower Purification (amazon-seller, fitness-influencer, ai-systems)
**Status:** 0% — Not started
**Action**:
- Move MCP server from amazon-seller to mcp-services
- Extract website HTML from ai-systems/src/
- Move HVAC campaign code from fitness-influencer/social-media/ to lead-generation/
- Move video editing artifacts from mcp-services/upwork-mcp/ to fitness-influencer/
- Restructure lead-generation/ as a full-service internal agency (see Architecture Decision below)

**Architecture Decision (2026-04-09): Lead Generation as Internal Agency**
`lead-generation/` serves all towers like an advertising agency — owns the shared infrastructure (pipeline DB, SMS/email delivery, enrichment, campaign tracking) but maintains per-tower profiles with audience-specific messaging, templates, scoring criteria, and outreach strategy. Each tower's outreach needs are different (HVAC business owners respond to different messaging than fitness influencers). Structure:
```
lead-generation/
├── src/              # Shared engine (delivery, tracking, scoring, enrichment)
├── towers/           # Per-tower strategy + creative
│   ├── digital/      # AI services clients (HVAC, med spa, dentist)
│   ├── fitness/      # Fitness coaching clients (gym owners, influencers)
│   └── labs/         # Product launches (DumbPhone Lock, etc.)
└── workflows/        # Campaign orchestration
```
Each `towers/` subdirectory has: `audience.json`, `templates/`, `scoring.json`, `strategy.md`. The engine reads the tower config to know how to target, what to say, and how to score leads for that tower.

### #3 REFACTOR: execution/ Directory Cleanup
**Status:** 0% — Not started
**Action**:
- Move 15 tower-specific files to owning towers (see list above)
- Delete 9 exact-duplicate files
- Fix 2 broken import chains (auto_iterator, stripe_payments)
- Promote auto_iterator.py to execution/ (6+ consumers)

### #4 CLEANUP: Root-Level Organization
**Status:** 0% — Not started
**Action**:
- Move 10 root-level stray files to proper locations
- Delete `projects/marceau-solutions/website/` (empty)
- Move skill directives to `directives/skills/`
- Archive stale docs in `docs/archive/`

### #5 IMPLEMENT: Tower Communication Protocols
**Status:** 0% — Not started
**Action**:
- Create `projects/shared/communication.py` with protocol definitions
- Add CLAUDE.md to all towers missing it (8 of 9)
- Update VERSION files where stale
- Implement protocol validation

### #6 URGENT: Panacea — Unified EC2 Agent with Grok Strategic Layer (Phase 0.5)
**Status:** 0% — Not started
**Why**: Three problems solved at once:
1. Anthropic banned third-party OAuth tokens (April 4, 2026) — Clawdbot will break
2. Clawdbot and Ralph are redundant engines (both run Claude on EC2)
3. Grok is isolated as an external advisor requiring manual copy-paste relay

**Risk**: HIGH — Clawdbot could stop working at any time without warning
**Cost**: $0 for Claude reasoning (Max subscription covers `claude` CLI). Grok API calls via `XAI_API_KEY` are usage-billed but minimal (~$1-5/month for strategic consultations).

#### The Problem (Three-in-One)
- **Clawdbot** uses a third-party framework (molt.bot) with Max OAuth tokens to call Anthropic — banned as of April 4
- **Ralph** is a separate headless `claude -p` agent on EC2 with separate trigger logic — redundant with Clawdbot's Claude engine
- **Grok** is the strategic brain but has no hands — William manually relays between Grok and execution agents. The orchestrator scripts (`grok_orchestrator.py`, `grok_claude_orchestrator.py`, `three_agent_orchestrator.py`) exist but nobody runs them automatically

#### The Solution: Panacea
One unified agent on EC2 that replaces Clawdbot, absorbs Ralph, and integrates Grok as a mandatory strategic layer.

**Architecture: 2 agents, Grok built-in**

| Agent | Platform | Role |
|-------|----------|------|
| **Claude Code (Mac)** | MacBook, VS Code / terminal | Interactive development with William |
| **Panacea (EC2)** | EC2, headless | Autonomous agent: Telegram + webhooks + cron. Grok consults on every AI request. |

**Grok is not a separate agent.** Grok is a strategic reasoning layer inside Panacea that is consulted on every request that requires AI thinking. No router decides when to use Grok — it's always consulted. The only things that bypass Grok are structured data operations (accountability number parsing, status lookups) that don't require strategic reasoning.

#### Grok-Always Architecture (High Sensitivity, No False Negatives)

```
William sends Telegram message(s) to @W_marceaubot
  → Panacea receives message (python-telegram-bot)

  → STAGE 1: MESSAGE ASSEMBLY (buffer)
    Solves: messages that bleed across multiple sends (phone typing)
    → Message arrives → append to buffer → start/reset 5-second timer
    → Another message arrives → append to buffer → reset 5s timer
    → Message ends with "." → fire immediately, assemble complete prompt
    → 5 seconds of silence → fire, assemble complete prompt
    → Result: one complete prompt from 1 or more messages

  → STAGE 2: STRUCTURED PRE-FILTERS (no AI, no Grok)
    These are measurement, not diagnosis. Pure data operations:
    → Accountability parser (Rules 1-8): "7" → log energy, "87,1,2,3" → log EOD
    → Status commands: "status", "scorecard", "goals" → read metrics, format, return
    → Pipeline shortcuts: "followups" → query agent_bridge_api, return
    → If any pre-filter matched: handle directly, respond, DONE

  → STAGE 3: GROK STRATEGIC CONSULTATION (ALWAYS, for every AI request)
    Every prompt that reaches this stage goes to Grok. No exceptions.
    → Call Grok API (XAI_API_KEY, grok-3-latest):
      Prompt: "William says: {message}. Current context: {system state summary}.
              What is the strategic priority here? What should the executor focus on?
              What pitfalls should it avoid? Be concise — 2-3 sentences."
    → Grok returns strategic direction
    → Cost: ~$0.003-0.01 per consultation (Grok API is cheap for short exchanges)

  → STAGE 4: TASK MANAGEMENT (queue + interrupt)
    Solves: concurrent requests, mid-task redirection
    → Is a claude -p process currently running?
      → NO  → start claude -p with Grok direction + prompt
      → YES → queue the prompt, reply: "Working on your previous request.
               I'll handle this next, or send 'stop' to cancel current task."
    
    Control keywords (bypass the buffer — acted on immediately):
      → "stop" / "cancel" → kill running claude -p, advance queue
         If queue empty → reply: "Cancelled. What do you need?"
         If queue has items → start next queued task
      → "add: {context}" → appends to running task's follow-up buffer.
         When current claude -p finishes, relay automatically sends a follow-up:
         "Previous result: {result}. Additional context from William: {add message}"
         This runs as a new claude -p with --resume to continue the session.

  → STAGE 5: CLAUDE CODE EXECUTION (with Grok's direction)
    → Subprocess: claude -p "{grok_direction}\n\nUser request: {prompt}"
    → Claude Code executes autonomously: edits files, runs bash, git, web search, deploys
    → Has full access to CLAUDE.md, memory system, all skills/SOPs, tower structure
    → Response returned via stdout
    → Session continuity via --resume with per-Telegram-chat session IDs

  → STAGE 6: RESPONSE DELIVERY
    → Send Claude Code's response back to William on Telegram
    → If task produced artifacts (PDFs, deploys): send links/files via Telegram or email
    → If queued tasks exist: start next task automatically

KEYWORD REFERENCE:
  | Keyword          | Stage   | Behavior                                        |
  |------------------|---------|-------------------------------------------------|
  | Regular text     | Buffer  | Append to buffer, 5s timer                      |
  | Text ending "."  | Buffer  | Fire buffer immediately                         |
  | "stop" / "cancel"| Task    | Kill running task, advance queue (bypass buffer) |
  | "add: ..."       | Task    | Append context for running task (bypass buffer)  |

ADDITIONAL INPUT CHANNELS (same Stages 3-6, different trigger):
  → Webhook (replaces Ralph): POST /task with PRD body → Grok consults → Claude executes
  → Cron: scheduled tasks → Grok consults → Claude executes
  → n8n: workflow triggers → Grok consults → Claude executes
```

#### Why Grok Is Always Consulted

William's directive: **"I don't want our system deciding not to talk to Grok."**

Like a medical test — if the test isn't sensitive enough, it throws false negatives. A router that decides "this is a simple question, skip Grok" will inevitably skip cases where Grok's strategic input would have changed the outcome. You can never measure the cost of a missed consultation.

The cost of always consulting Grok: ~$0.01 per message. The cost of not consulting Grok when you should have: unbounded.

**What bypasses Grok (and why it's not a false negative):**
- Accountability number parsing: "7" → Google Sheets write. This is a measurement, not a decision. Grok has no opinion on logging a number.
- Status/scorecard lookups: "status" → read metrics, format text. This is data retrieval, not strategy.
- Pipeline queries: "followups" → database query. Same — data retrieval.

These are equivalent to reading a thermometer. You don't consult a strategist to read a thermometer. Everything else — every question, every request, every task — Grok sees first.

#### What We Build (7 components)

##### EC2 Components (Panacea)

**Component 1: Telegram Bot Relay** (`projects/personal-assistant/src/panacea_relay.py`)
- Python script using `python-telegram-bot` library
- Receives messages from @W_marceaubot (reuse existing bot token: `8596701493:AAH...`)
- Implements all 6 stages: buffer → pre-filters → Grok → task queue → Claude Code → response
- Accepts webhook inputs for PRD/task execution (replaces Ralph's webhook_server.py)
- Runs as systemd service on EC2 (replaces both `clawdbot.service` and Ralph's webhook)

**Component 2: Grok Strategic Layer** (`projects/personal-assistant/src/grok_strategic_layer.py`)
- Thin wrapper around Grok API via `XAI_API_KEY` (OpenAI-compatible endpoint at `https://api.x.ai/v1`)
- Model: `grok-3-latest` (fast, cheap, strategic)
- Accepts: user message + system state context
- Returns: 2-3 sentence strategic direction for Claude Code
- Includes system state reader: current goals, pipeline status, recent session context
- Timeout: 10 seconds. If Grok is unreachable, log the failure and proceed with Claude Code alone (graceful degradation, not silent skip — the failure is logged and reported)
- **Shared between EC2 and Mac** — same module, same API, same behavior

**Component 3: Accountability Pre-Filter** (port from `clawdbot_handlers.py`)
- Already written — 8 parse rules, Google Sheets logging, milestone checks
- Currently a Python module, just needs to be wired into the new relay
- Zero changes to logic, just import path

**Component 4: Claude Code CLI Integration (EC2)**
- `claude` CLI v2.1.22 already installed on EC2 at `/usr/bin/claude` (confirmed)
- Auth: Max OAuth via `claude` binary (permitted — Anthropic's native app)
- Working directory: `/home/ec2-user/dev-sandbox/` (full repo context via CLAUDE.md)
- Invocation: `claude -p "{grok_direction}\n\nUser: {message}" --output-format json`
- Session continuity: `--resume` flag with per-Telegram-chat session IDs
- Full tool access: bash, read, write, edit, glob, grep, web search

**Component 5: systemd Service** (`panacea.service`)
- Replaces `clawdbot.service` AND Ralph's `webhook_server.py`
- Runs as `ec2-user` (needs repo access)
- Auto-restarts on failure
- Environment: inherits from `/home/ec2-user/dev-sandbox/.env`

##### Mac Components

**Component 6: Grok Hook for Claude Code Interactive** (`scripts/grok_hook.py`)
- Claude Code hook that fires before each response in interactive sessions
- Calls the same `grok_strategic_layer.py` module (Component 2)
- Injects Grok's strategic direction into the conversation context
- Configured in `.claude/settings.json` as a pre-response hook
- William retains full interactive steering — Grok's input is additive, not replacing
- Same "always consulted" rule — every AI response gets Grok's strategic context

**Component 7: Autonomous Mode on Mac** (`scripts/panacea_mac.sh`)
- Wrapper script for `claude -p` on Mac with Grok pre-consultation
- Use case: fire-and-forget tasks on Mac filesystem without babysitting
- Calls Grok first → passes direction to `claude -p` → runs against Mac dev-sandbox
- Example: `./scripts/panacea_mac.sh "refactor the PDF engine to use tower structure"`
- Same engine as EC2 Panacea, different filesystem

#### Capability Comparison (Corrected)

| Capability | Claude Code Interactive (Mac) | Panacea Autonomous (Mac `claude -p`) | Panacea (EC2 via Telegram) |
|---|---|---|---|
| **Reasoning** | Claude (Max) | Claude (Max) | Claude (Max) |
| **Grok strategic layer** | YES — hook on every response | YES — pre-consultation | YES — Stage 3, always |
| **Interaction model** | Real-time steering | Fire-and-forget | Fire-and-forget |
| **Filesystem** | Mac | Mac | EC2 |
| **Bash/git/deploy** | Mac local | Mac local | EC2 direct (no SSH needed) |
| **n8n operations** | Via SSH to EC2 | Via SSH to EC2 | Direct — same machine |
| **Redirect mid-task** | Real-time — type a message, Claude reads it instantly. Continuous steering. | Kill process + restart with new prompt | "stop" keyword kills task. "add: ..." appends context for follow-up. New message queues behind running task. |
| **Concurrent tasks** | One conversation with internal parallelism (subagents). Cannot run two separate sessions simultaneously. | One process at a time. Additional tasks must wait or be scripted separately. | One task at a time per chat. New messages queue. Queue advances when task completes or is cancelled. |
| **Multi-message input** | Native — you type, Claude waits for you to finish | Single prompt (script arg) | 5-second buffer assembles fragments. "." fires immediately. |
| **Availability** | Only when at Mac | Only when at Mac | 24/7 from phone |

#### What Gets Retired
- **Clawdbot**: Node.js binary, molt.bot framework, `@clawdbot/anthropic` plugin, OAuth auth-profiles.json, Clawdbot memory (Ollama + LanceDB), all 54+ Clawdbot skills, `/home/clawdbot/` user directory (archive, don't delete)
- **Ralph**: `webhook_server.py` (port 5002), separate PRD trigger mechanism — absorbed into Panacea's webhook input
- **Grok orchestrator scripts**: `grok_orchestrator.py`, `grok_claude_orchestrator.py`, `three_agent_orchestrator.py` — their logic is absorbed into the Grok strategic layer (Component 2)
- **Three-agent architecture doc**: `docs/THREE-AGENT-ARCHITECTURE.md` — replaced by two-agent + Grok-integrated architecture

#### What Stays (zero changes)
- Telegram bot identity (@W_marceaubot, same bot token)
- Accountability parsing (Rules 1-8) — same Python code, same logic
- Pipeline queries — same agent_bridge_api endpoints
- n8n workflow integrations — none depend on Clawdbot or Ralph internals
- All existing Claude Code skills, SOPs, CLAUDE.md, memory system
- `XAI_API_KEY` already in `.env` — Grok API access already configured

#### New Architecture Summary

```
BEFORE (4 moving parts, manual Grok relay):
  Grok (external) ←→ William (manual copy-paste) ←→ Claude Code (Mac)
                                                  ←→ Clawdbot (EC2, Telegram, OAuth — BANNED)
                                                  ←→ Ralph (EC2, webhooks, claude -p)

AFTER (2 agents, Grok built-in everywhere):
  Claude Code (Mac):
    ├── Interactive: VS Code/terminal sessions with William + Grok hook
    └── Autonomous: claude -p with Grok pre-consultation (scripts/panacea_mac.sh)
  
  Panacea (EC2):
    ├── Input: Telegram (buffered + queued), webhooks, cron, n8n
    ├── Strategy: Grok API (always consulted for AI requests)
    ├── Execution: claude -p (covered by Max subscription)
    ├── Task mgmt: queue, interrupt (stop/cancel), context append (add:)
    └── Output: Telegram, email, SMS, file edits, deploys, git
  
  Grok: not a separate agent — a strategic reasoning layer inside both agents
```

#### Pre-flight (completed 2026-04-04)
- [x] `claude` CLI installed on EC2: YES — v2.1.22 at `/usr/bin/claude`
- [x] Clawdbot currently broken: NO — but enforcement rolling out
- [x] Telegram bot token available: YES — `8596701493:AAH...`
- [x] SOUL.md truncation issue: YES — 26KB→20KB every 30 min
- [x] `XAI_API_KEY` in .env: YES — Grok API access ready
- [ ] `claude -p --resume` session support: needs testing
- [ ] `claude` auth status on EC2: needs verification (`claude auth status`)
- [ ] `python-telegram-bot` library on EC2: needs `pip install python-telegram-bot`

#### Estimated Time: 3-4 hours (build + test + cutover)

## Implementation Plan (Approved 2026-04-03, updated 2026-04-05)

**Execution order:**
```
Phase 0.5 ✅ → Phase 0 ✅ → Phase 1 ✅ → Phase 2 ✅ → Phase 3 ✅ → Phase 4 ✅ → Phase 5 ✅ → Phase 6 ✅ → Phase 7 ⬜ → Phase 8 ⬜
```
**Last updated**: 2026-04-10 (end of session — Phases 0.5 through 6 complete)

**Safety rules**: Git tag before each phase. Import shims after file moves. Mac first, EC2 second. One commit per phase for surgical rollback.

---

### Phase 0.5: Panacea — Unified EC2 Agent + Grok Integration (URGENT)
**Status:** COMPLETE (2026-04-05)
**Priority**: IMMEDIATE — Clawdbot OAuth ban enforcement is live
**Estimated time**: 3-4 hours across 2 sessions
**Depends on**: Nothing — fully independent

**Session A (2-2.5 hours): Build + EC2 Deploy**
1. Verify remaining pre-flight items on EC2:
   - `claude -p --resume` session support
   - `claude auth status` (confirm CLI is authenticated)
   - `pip install python-telegram-bot`
2. Build `grok_strategic_layer.py` (Component 2) — shared module, Grok API wrapper
3. Build `panacea_relay.py` (Component 1) — 6-stage pipeline:
   - Message buffer (5s window, "." fires immediately)
   - Pre-filters (port accountability Rules 1-8 from `clawdbot_handlers.py`)
   - Grok consultation (always, for every AI request)
   - Task queue + interrupt (`stop`/`cancel`, `add:`)
   - Claude Code CLI subprocess (`claude -p` with `--resume`)
   - Response delivery to Telegram
4. Deploy to EC2, create `panacea.service` systemd unit
5. Test on EC2: send test messages to @W_marceaubot

**Session B (1-1.5 hours): Mac Integration + Cutover**
1. Build `grok_hook.py` (Component 6) — Claude Code pre-response hook
2. Build `panacea_mac.sh` (Component 7) — autonomous `claude -p` wrapper for Mac
3. Configure `.claude/settings.json` with Grok hook
4. Stop `clawdbot.service` on EC2
5. Start `panacea.service` on EC2
6. Full test suite:
   - Accountability: "7", "87,1,2,3", "status"
   - Multi-message buffer: send 3 messages, verify concatenation
   - Grok consultation: verify Grok is called (check logs)
   - Task queue: send message while task running, verify queue behavior
   - `stop` keyword: verify kill + queue advance
   - `add:` keyword: verify context append
   - Mac Grok hook: verify Grok consulted in interactive session
7. Keep Clawdbot install intact (rollback path — don't delete until stable for 1 week)

---

### Phase 0: Scaffold + Safety Net
**Status:** COMPLETE
**Estimated time**: 30 minutes
**Depends on**: Nothing

1. Git tag: `pre-rebuild-v1`
2. Create `projects/shared/import_shims/` directory
3. Verify no nested `.git` repos: `find . -name ".git" -type d`
4. Snapshot current state in `docs/session-history.md`

### Phase 1: Root-Level Cleanup
**Status:** COMPLETE
**Estimated time**: 45 minutes
**Depends on**: Phase 0

1. Move 10 root-level stray files to proper locations (see Action #4 list)
2. Move skill directives to `directives/skills/`
3. Archive stale docs in `docs/archive/`
4. Delete empty `projects/marceau-solutions/website/`
5. Git tag: `post-phase-1`

### Phase 2: execution/ — Tower-Specific File Moves
**Status:** COMPLETE
**Estimated time**: 60 minutes
**Depends on**: Phase 1

1. Move 15 tower-specific files from `execution/` to owning towers (see Action #3 list)
2. Create import shims in `execution/` for each moved file (backwards compat during transition)
3. Test: verify no broken imports in active services
4. Git tag: `post-phase-2`

### Phase 3: execution/ — Duplicate Cleanup
**Status:** COMPLETE
**Estimated time**: 30 minutes
**Depends on**: Phase 2

1. Delete 9 exact-duplicate files (see Action #3 list)
2. Fix 2 broken import chains (auto_iterator, stripe_payments)
3. Promote auto_iterator.py to `execution/` (6+ consumers)
4. Git tag: `post-phase-3`

### Phase 4: followup_prioritizer Migration
**Status:** COMPLETE (confirmed — already moved)
**Estimated time**: 30 minutes
**Depends on**: Phase 3

1. Move `followup_prioritizer.py` to correct tower
2. Update all import references
3. Test prioritizer functionality
4. Git tag: `post-phase-4`

### Phase 5: Tower Purification
**Status:** COMPLETE (2026-04-10) — tower purification + lead-gen agency structure
**Estimated time**: 90 minutes
**Depends on**: Phase 4

1. Move MCP server from `amazon-seller/` to `mcp-services/`
2. Extract website HTML from `ai-systems/src/`
3. Move HVAC campaign code from `fitness-influencer/social-media/` to `lead-generation/`
4. Move video editing artifacts from `mcp-services/upwork-mcp/` to `fitness-influencer/`
5. Add CLAUDE.md to all 8 towers missing it
6. Update stale VERSION files
7. Git tag: `post-phase-5`

### Phase 6: Strangler Fig Foundation
**Status:** COMPLETE (2026-04-10) — bridge_v2 scaffold built, deployed on EC2 port 5011, all endpoints tested/passing. EC2 security group fixed (IP change). Sync mechanism verified.
**Estimated time**: 60 minutes
**Depends on**: Phase 0 (can run in parallel with Phases 1-5)

1. Create `bridge_v2/` service scaffold on port 5011
2. Implement health check and routing proxy
3. Deploy alongside monolith `agent_bridge_api.py` on port 5010
4. Verify both services run concurrently without conflict
5. Git tag: `post-phase-6`

### Phase 7: Monolith Migration (Incremental)
**Status:** NOT STARTED — next up (Saturday 2026-04-11)
**Estimated time**: 15 minutes per endpoint group, ~10 groups
**Depends on**: Phase 6

1. Migrate one endpoint group at a time to `bridge_v2/`
2. Re-point n8n workflows from port 5010 → 5011 for migrated endpoints
3. Test each migration individually
4. Each migration is independently reversible
5. When all endpoints migrated: retire monolith
6. Git tag after each group: `post-phase-7-{group}`

### Phase 8: Tower Communication Protocols
**Status:** NOT STARTED — Saturday 2026-04-11 (can run in parallel with Phase 7 since Phase 5 is complete)
**Estimated time**: 60 minutes
**Depends on**: Phase 5 (COMPLETE)

1. Create `projects/shared/communication.py` with protocol definitions
2. Implement protocol validation
3. Wire protocols into existing inter-tower calls
4. Git tag: `post-phase-8`

---

## Execution Notes

- HANDOFF.md is the single source of truth for task status
- Phase 0.5 is URGENT — execute before all other phases
- Phase 6 is independent — can start anytime after Phase 0, in parallel with Phases 1-5
- Each n8n workflow migration in Phase 7 is ~15 minutes and individually reversible
- Session-sized chunks: each phase designed for evening/weekend work (30-90 min)
- Post-April 6 schedule: William at Collier County 7am-3pm, execution in evenings/weekends
