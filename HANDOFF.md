# HANDOFF.md — Agent Task Queue

**Purpose**: Single source of truth for work handoffs between EC2 (Panacea/Ralph) and MacBook (Claude Code).

**Last Updated**: 2026-03-23

## CRITICAL: Read These Files At Session Start

| File | Why |
|------|-----|
| `docs/ARCHITECTURE-DECISIONS.md` | Cross-agent conventions, E10 quality rules, interface-first standards |
| `docs/SYSTEM-STATE.md` | What's built, what's broken, DO NOT REDO list |
| `docs/session-history.md` | What was done in recent sessions |

---

## Session 16 Summary — March 23, 2026

### What Was Built (for Clawdbot and Ralph awareness):

**Infrastructure & Data:**
- Demo line (855) 239-9364 — consolidated: AI voice receptionist + missed-call text-back. Old (239) 457-0662 retired.
- Hunter.io + Snov.io enrichment waterfall replacing Apollo enrichment (Apollo enrichment broken — pivot to Hunter/Snov)
- EC2 canonical `pipeline.db` with multi-tower schema — single source of truth for all deals, outreach, and intake
- 8 new pipeline endpoints added to `agent_bridge_api` — Clawdbot can now query pipeline directly
- `pipeline.marceausolutions.com` multi-tower kanban dashboard replaced: outreach-analytics (8794), client-tracker (8795), sales-pipeline (8785)

**Payments & Conversion:**
- Stripe $297/mo product live — price ID: `price_1TECrADeeD1eRvzzyYKnO7z5`, payment link: `https://buy.stripe.com/9B66oH7tBaeI0Wk8H8g360f`
- `marceausolutions.com/start` — client intake form (submits to `pipeline.marceausolutions.com/api/intake`)

**Outreach Assets:**
- Leave-behind PDF updated — pricing corrected to monthly retainer ($500-2,000 setup + $500-1,000/mo)
- Phone blitz list: 40 HVAC leads with phones at `projects/shared/lead-scraper/output/phone_blitz_2026-03-24.csv`
- Tuesday in-person route: 12 stops at `projects/shared/lead-scraper/output/inperson_route_2026-03-25.csv`
- Segment analysis: 56 Apollo leads ready to email + 18 new from Hunter enrichment = 74 total

**Website:**
- `ai-automation.html` updated: "Start Your Free 2-Week Trial →" primary CTA added above Calendly, links to `marceausolutions.com/start`
- Pricing corrected to monthly retainer range ($500-$1,000/mo + $500-$2,000 setup)

### What Clawdbot Needs to Know:

**Pipeline API endpoints now available on EC2 (agent_bridge_api):**
- `GET /pipeline/stats` — overall pipeline summary (deals by stage, total value, conversion rate)
- `GET /pipeline/deals` — list all active deals
- `POST /pipeline/deal/add` — add or update a deal (body: `{business_name, email, stage, source, notes}`)
- `POST /pipeline/outreach/log` — log an outreach touch (body: `{deal_id, channel, notes}`)
- `GET /pipeline/followups` — list deals needing follow-up today

**Trigger rules for Clawdbot:**
- When a prospect replies to an email → log via `POST /pipeline/deal/add` with `stage: "Replied"`
- When William asks "pipeline status" or "how's the pipeline?" → call `GET /pipeline/stats` and report
- When William asks "who do I follow up with?" → call `GET /pipeline/followups`

---

## Next Session Priority: Live Call Coach (Real-Time Sales Coaching Overlay)

**What William described (Mar 24):** A live coaching overlay that listens to sales calls and suggests the next best response in real time — like the AI interview coaching apps (Final Round AI, Cluely, etc.) but for sales calls.

**Architecture:**
- macOS floating window app (Swift or Electron) — always-on-top, semi-transparent overlay
- Captures mic audio (speakerphone → MacBook mic) in 3-second rolling chunks
- Streams to Whisper (OpenAI) for real-time transcription
- Sends transcript + conversation stage to Claude for next-best-response suggestion
- Displays suggestion in overlay with color-coded stage indicator (Rapport / Pain / Objection / Close)
- **NOT iOS during active call** — iOS blocks all app access to active call audio. Mac speakerphone is the only viable path.

**Stage detection logic:**
- Rapport → suggest warmth/mirroring questions
- Pain discovery → suggest deeper dig questions
- Objection → surface relevant objection handler from playbook
- Close → suggest specific closing language

**Build alongside** the sales intelligence layer — both need accumulated call data.

---

## Next Session Priority: Sales Intelligence Layer

**What William described (Mar 24):** Build a data accumulation + analytics system on top of the pipeline that gets smarter over time. Full spec:

1. **Conversion analytics by segment** — close rate by industry, company size, city, lead source, outreach channel. Roll-up view in the pipeline dashboard.
2. **Script-to-outcome correlation** — track which email template + call script + objection handling approach led to which outcome. Over time surfaces "T1 HVAC + no website → template_A converts at 18%".
3. **Cost per acquisition** — track API costs (Apollo, email enrichment, Anthropic scoring) + estimated time per deal to compute true CAC.
4. **Heat map clustering** — visual density map: which company profiles (industry × size × systems background) are highest-convert. Input to prioritization.
5. **Call scheduling intelligence** — surface highest-likelihood-to-convert deals first based on accumulated segment data.
6. **Full pipeline funnel metrics** — scrape → enrich → email → call → in-person → proposal → close. Drop-off rate at each stage.

**Architecture decision needed:** Does this live as a new tab in `pipeline.marceausolutions.com` or a separate `analytics.marceausolutions.com`? Lean toward pipeline tab — less URL sprawl.

**Data foundation already exists:** `deals` (industry, tier, size), `outreach_log` (channel), `activities` (stage progression), `email_template` column, call outcomes in activities. Just needs aggregation layer + schema additions for script tracking.

**DO NOT build until:** At least 10-20 logged call outcomes exist. Analytics on 0 data is useless. Let the call blitz generate data first.

---

## Current Sprint: AI Client Acquisition (March 23 – April 5)

**Goal**: Land 1 AI systems client before William starts new job on April 6.
**New job**: Electrical technician, Collier County Wastewater, 7am-3pm weekdays.
**After April 6**: Training at 3pm, side hustle work evenings/weekends. All current goals continue.

---

## For Panacea (EC2, Telegram — formerly Clawdbot)

### Standing Orders:
- Morning accountability: 5:00am ET (n8n — cron `0 0 9 * * 1-6`)
- EOD check-in: 7pm ET (n8n)
- Weekly report: Sunday 7pm ET (n8n)
- Treatment day detector: daily 5am ET (n8n)
- Parse replies per accountability_handler.py rules
- Monitor upgrade triggers per Knowledge Base

### Quality Enforcement:
- **SOUL.md v2.1.0** now includes E10, interface-first, and quality benchmark sections
- Every recommendation must pass: "Is this the right interface for William's life, not just the easiest to code?"
- When building anything: n8n > CLI script, branded PDF > markdown, SMS > "check this command"

### Gmail Capability:
- `token.json` now has full Gmail scopes: read, send, compose, modify, drafts
- Can create email drafts via Google API (see SOUL.md for code example)
- Can send via SMTP (credentials in .env)

### MANDATORY — Handoff State Protocol:
- **On every session start**: Read this file + check `execution/agent_comms.py` for pending messages
- **On every session end**: Update this file with what was done, push to GitHub
- **When William asks something meant for Claude Code**: Add to "For Claude Code" section, push
- **When completing a task**: Move to "Completed Tasks" with date

---

## For Ralph (EC2, PRD-driven)

### Task 1: Content Batch Processing Pipeline Test
**Priority**: Medium | **Complexity**: 7/10 | **Status**: Ready

1. Check if FitAI backend video modules run standalone on EC2
2. Process a test video through: silence removal → output
3. If FitAI modules need FastAPI context, use `execution/video_jumpcut.py`
4. Report results below under Completed Tasks

### Task 2: Cold Outreach Feed in Sales Pipeline (NEW — Session 2026-03-23)
**Priority**: High | **Complexity**: 5/10 | **Status**: Ready

William sent 91 cold emails today (March 23) to Naples prospects. The follow-up automation fires daily at 9am via Mac launchd. The data lives in `outreach_campaigns.json` on Mac. William needs to see this in `pipeline.marceausolutions.com` without manually adding every lead.

**Goal**: Add a "Cold Outreach" stage to the pipeline kanban, import batch leads from `outreach_campaigns.json`, and show each lead's follow-up status (Day 0/3/7/14/21 sequence).

**Data source** (Mac, synced to EC2 via git):
- `/dev-sandbox/projects/shared/lead-scraper/output/outreach_campaigns.json`
- Schema: `{lead_id, email, business_name, owner_name, template_used, subject, sent_at, status, follow_up_count, notes}`
- `follow_up_count` increments per touch sent (0=Day 0 sent, 1=Day 3 done, 2=Day 7 done, etc.)
- Touch schedule: count 0→Day 3, 1→Day 7, 2→Day 14, 3→Day 21

**What to build in `pipeline.marceausolutions.com` (port 8785 on EC2):**
1. Add `GET /outreach` route — table view of all cold outreach leads with columns:
   - Business Name, Email, Sent Date, Follow-Up Stage, Next Follow-Up Due, Status
2. Add `/outreach/import` endpoint — reads `outreach_campaigns.json` from git-synced path on EC2, upserts into `pipeline.db` under a `cold_outreach` table (not the main deals table — keep separate)
3. Show "Responded" flag if status != "sent" (replies logged by `cold_outreach.py` when it detects a reply)
4. Link from the main pipeline dashboard: "Cold Outreach (91 active)"
5. Mobile-friendly — dark+gold branded, matches existing pipeline UI

**Files to modify on EC2:**
- `/home/ec2-user/sales-pipeline/src/app.py` — add routes
- `/home/ec2-user/sales-pipeline/src/models.py` — add `cold_outreach` table schema
- `/home/ec2-user/sales-pipeline/src/ui.py` — add outreach list template

**Data path on EC2** (git auto-syncs via PostToolUse hook):
`/home/ec2-user/dev-sandbox/projects/shared/lead-scraper/output/outreach_campaigns.json`

### Task 3: FitAI Frontend Redesign
**Priority**: High | **Complexity**: 6/10 | **Status**: Ready

The FitAI frontend at `fitai.marceausolutions.com` loads but looks broken/unusable.
- Frontend files: `/home/ec2-user/fitness-influencer/frontend/`
- Backend API: `http://127.0.0.1:8000/api/` (working, all endpoints healthy)
- nginx now serves frontend static files directly, proxies `/api` to backend
- **Goal**: Make the dashboard visually polished, mobile-friendly, dark+gold branded
- Match the quality of KeyVault™ and Accountability Engine dashboards
- Key pages: Dashboard, Video Upload, Content Calendar, Analytics

---

## For Claude Code (Mac)

### Current Priorities:
1. AI client acquisition sprint support (outreach assets, prospect lists, proposals)
2. Sales Pipeline CRM at pipeline.marceausolutions.com (live, needs prospects added)
3. YouTube video: "I Built a Better Claude Dispatch" (script ready)
4. System maintenance and cross-agent consistency

### MANDATORY — Handoff State Protocol:
- **On every session start**: `git pull origin main` + read this file + check for Panacea messages
- **On every session end**: Update this file with what was done, push to GitHub
- **Always**: After git push, EC2 auto-syncs via PostToolUse hook (30-min cron fallback)

### Session 2026-03-23 In Progress:
- Fixed Panacea X/Twitter API keys (EC2 had stale keys from different app)
- Synced ALL 56 out-of-sync credentials between Mac and EC2
- Built & deployed 5 NEW production SaaS apps:
  - KeyVault™ (keys.marceausolutions.com) — API key management with encryption, health monitoring
  - Accountability Engine (accountability.marceausolutions.com) — 90-day tracker with animated progress rings
  - Sales Pipeline (pipeline.marceausolutions.com) — CRM with kanban, proposals, pre-call briefs
  - ClaimBack™ (claimback.marceausolutions.com) — AI medical billing disputes
  - MailAssist™ (email.marceausolutions.com) — AI email intelligence
- Created AI Services Pipeline Google Sheet (deal tracking)
- Created 6 Stripe products + payment links ($2K-$5K setup, $500-$1K/mo mgmt)
- Added ™ symbols across all product dashboards
- Fixed Calendly slug (ai-services-discovery → ai-services-discovery-call)
- Fixed FitAI nginx (was showing JSON, now serves frontend)
- Fixed n8n accountability workflows (restarted, crons re-registered)
- Toggled 7 failing n8n workflows (content/analytics — X/YouTube creds need n8n UI fix)
- Made handoff state protocol mandatory for all agents

### Session 2026-03-22 Completed:
- Claude Dispatch evaluation (not adopting — our system is superior)
- YouTube video script written + branded PDF generated
- Gmail token re-authed with full scopes (6 scopes), pushed to EC2
- Added `/gmail/draft` endpoint to agent_bridge_api.py
- Updated Panacea SOUL.md to v2.1.0
- Calendar reorganized: training moved to 3pm

---

## n8n Workflows Needing Attention

| Workflow | Issue | Priority |
|----------|-------|----------|
| X-Social-Post-Scheduler-v2 | X API credential stale in n8n | Low (not sprint-critical) |
| X-Batch-Image-Generator | Same X/xAI credential issue | Low |
| YouTube Analytics Collector | YouTube API credential | Low |
| Weekly-Campaign-Analytics | Error trigger config | Low |
| Challenge-Day7-Upsell | Error trigger config | Low |
| Daily-Operations-Digest | Depends on other workflows | Low |

**Fix method**: Open n8n UI → re-enter credentials for X and YouTube nodes.

---

## Production Services Live

| Service | URL | Port | Status |
|---------|-----|------|--------|
| KeyVault™ | keys.marceausolutions.com | 8793 | ✅ SSL |
| Accountability Engine | accountability.marceausolutions.com | 8780 | ✅ SSL |
| Sales Pipeline | pipeline.marceausolutions.com | 8785 | ✅ SSL |
| Dystonia Digest | dystonia.marceausolutions.com | 8792 | ✅ SSL |
| ClaimBack™ | claimback.marceausolutions.com | 8790 | ✅ SSL |
| MailAssist™ | email.marceausolutions.com | 8791 | ✅ SSL |
| FitAI | fitai.marceausolutions.com | 8000 | ✅ SSL (frontend needs redesign) |
| Company Site | marceausolutions.com | GitHub Pages | ✅ |
| n8n | n8n.marceausolutions.com | 5678 | ✅ SSL |

---

## Completed Tasks

- (2026-03-22) Claude Dispatch evaluation — rejected, our system is better
- (2026-03-22) Panacea three-agent bridge (agent_comms.py, CLAUDE-CODE-BRIDGE.md)
- (2026-03-22) Project tracker (execution/project_tracker/)

## Pending Handoff — 2026-03-26 21:13

**Task**: Wire clawdbot_handlers.py into Clawdbot Telegram bot on EC2. File at projects/personal-assistant/src/clawdbot_handlers.py. See docs/CLAWDBOT-PA-INTEGRATION.md for full spec. Requires: import route_message from clawdbot_handlers, call it in message handler, return response if not None.

**Context**:
```json
{}
```

**Status**: Pending — Ralph to pick up

**Deployment steps for Ralph**:
1. `git pull` on EC2 to get `projects/personal-assistant/src/clawdbot_handlers.py`
2. Copy or symlink `clawdbot_handlers.py` into Clawdbot's working directory
3. In Clawdbot's main message handler, add:
   ```python
   from clawdbot_handlers import route_message
   # In handle_message():
   pa_response = route_message(text)
   if pa_response:
       bot.send_message(chat_id, pa_response, parse_mode="Markdown")
       return  # PA handled it
   ```
4. William starts SSH tunnel on Mac: `bash scripts/tunnel-to-ec2.sh`
5. Test: send "schedule" in Telegram → should return today's ROI plan

**Full spec**: `docs/CLAWDBOT-PA-INTEGRATION.md`

---
