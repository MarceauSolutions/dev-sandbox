# ARCHITECTURE-DECISIONS.md
## Cross-Agent Knowledge Sync

> This file captures key conventions and decisions that ALL agents (Clawdbot on EC2, Claude Code on Mac, Ralph) must follow. Read this at session start.

---

## Output Format Conventions

| Output Type | Format | Tool/Method |
|-------------|--------|-------------|
| Reports & Guides | **Branded PDF** | `execution/branded_pdf_engine.py` with appropriate template |
| Workout Plans | Branded PDF | `workout_program` template |
| Medical Documents | Branded PDF | `generic_document` template |
| Dashboards | Standalone web app | Fixed localhost URL + `scripts/[name].sh` |
| Alerts | SMS or Email | Twilio / SMTP |
| Automations | n8n workflow | localhost:5678 |

**NEVER:** Plain markdown files as final deliverables, CLI-only tools, "run this command to check"

---

## Domain/Hosting Tiers

| Tier | Use Case | Example |
|------|----------|---------|
| **Tier 1: GitHub Pages** | Static sites, client websites | marceausolutions.com |
| **Tier 2: Subdomain** | Internal tools, APIs, demos | n8n.marceausolutions.com, demo.marceausolutions.com |
| **Tier 3: Localhost** | Dev/testing only | localhost:8080 |

---

## PDF Generation Rules

1. **Always use branded_pdf_engine.py** for any document deliverable
2. Available templates: `workout_program`, `nutrition`, `progress`, `onboarding`, `peptide`, `challenge`, `generic_document`
3. Generate JSON data file → Run engine → Output branded PDF
4. Never use raw pandoc/weasyprint for client-facing documents

**Command:**
```bash
python3.9 execution/branded_pdf_engine.py --template [template] --input data.json --output output.pdf
```

---

## 3-Agent Protocol

### Sync Points
- **HANDOFF.md** — Task handoffs between agents
- **ARCHITECTURE-DECISIONS.md** (this file) — Conventions and standards
- **CLAUDE.md** — Execution rules (same on Mac and EC2)

### Knowledge Flow
```
Mac (Claude Code) ──git push──> GitHub ──auto-sync──> EC2 (Clawdbot)
                                   │
                                   └──> Ralph (PRD-driven tasks)
```

### What Gets Committed
- ALL decisions about conventions
- ALL architectural choices  
- Session summaries (docs/sessions/)
- Any knowledge that other agents need

---

## Medical Document Standards (William's Condition)

- Dystonia-related guides → `docs/medical/dystonia/` or `docs/medical/cannabis/`
- Always branded PDF format
- Include: condition context, evidence-based recommendations, practical protocols

---

## Quality Standards

### E10 — Best-Path Evaluation (ALL AGENTS)
Never default to the easiest implementation. Before building ANYTHING, answer:
1. Who is the end user and how will they interact with this?
2. What existing infrastructure is the natural fit?
3. How does this need to scale?
4. What are the real constraints? (energy levels, dystonia, new job 7-3 starting April 6)
5. Is there a consolidation opportunity?

**Quick test:** "Would William use this on a low-energy day from his phone?" If no, wrong design.

### Quality Benchmark
The **dystonia research digest** is the gold standard — it autonomously chose scheduling, branded PDF, auto-open, zero manual steps. Every deliverable must match that bar. "Just the easy path" is not acceptable.

### Interface-First (Non-Negotiable)
- Automations → **n8n**
- Reports/guides → **branded PDF** (`execution/branded_pdf_engine.py`)
- Alerts → **SMS or email** (Twilio/SMTP)
- Dashboards → **standalone web app** with launch script

---

## Calendar Conventions

- William's daily schedule lives on the **"Time Blocks"** calendar (not primary)
- Calendar ID: `c_710cb4eceeac036e44157b8626fe6447b430ce3fd0100020d4b32fc44af1f164@group.calendar.google.com`
- Appointments (Dr. Herrington, etc.) and milestones go on **primary** (wmarceau@marceausolutions.com)
- Therapy goes on **wmarceau26@gmail.com** calendar
- Time Blocks has NO default reminders — set `reminders: {useDefault: false, overrides: [{method: "popup", minutes: 5}]}` on every event
- **Always check ALL calendars** before creating/modifying events

---

## Accountability System

- Morning/EOD check-ins via n8n → Telegram → Clawdbot parses replies
- Activity logging via `execution/accountability_handler.py`
- Gamification state in `/home/clawdbot/clawd/gamification/`
- Google Sheets for tracking: "Challenge Leads" spreadsheet
- 90-day plan: March 17 – June 7, 2026

---

## API Keys & Tokens

- All keys in `.env` (root of dev-sandbox, same on Mac and EC2)
- Google token: `token.json` — Gmail (read/send/compose/modify) + Calendar + Sheets (all scopes)
- OAuth client: `credentials.json`
- Refresh tokens on Mac via `google_auth_setup.py`, then push to sync to EC2

---

## Sync Architecture

### Mac → EC2 (Automatic)
1. Claude Code runs `git push origin main`
2. PostToolUse hook (`post-push-ec2-sync.sh`) fires
3. SSHes to EC2, runs `git pull origin main --rebase` as clawdbot user
4. n8n "GitHub-Push-to-Telegram" sends notification

### EC2 → Mac (Manual)
- Clawdbot commits and pushes to GitHub
- Mac must `git pull` manually or Claude Code pulls at session start

### EC2 Self-Sync
- Cron: `*/30 * * * *` runs `sync-agent.sh --auto-sync`
- Catches anything the PostToolUse hook missed

### Gap Awareness
- If push happens from GitHub web UI or another machine, EC2 won't auto-pull until next cron (30 min max delay)
- PostToolUse hook is fire-and-forget — no verification of success
- Sync log: `/tmp/post-push-ec2-sync.log` (cleared on reboot)

---

## Session Start Checklist (ALL AGENTS)

1. [ ] `git pull origin main` — Get latest
2. [ ] Check `git log --oneline origin/main..HEAD` — Push any unpushed commits
3. [ ] Read `docs/ARCHITECTURE-DECISIONS.md` — Know the conventions
4. [ ] Read `HANDOFF.md` — Check for pending tasks
5. [ ] Read `docs/SYSTEM-STATE.md` — Know what's built/broken
6. [ ] Check project-specific `CLAUDE.md` if working on a project

---

*Last Updated: 2026-03-22*
