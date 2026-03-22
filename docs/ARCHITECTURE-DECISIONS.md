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

## Accountability System

- Morning/EOD check-ins via n8n → Telegram
- Activity logging via `execution/accountability_handler.py`
- Gamification state in `/home/clawdbot/clawd/gamification/`
- Google Sheets for tracking: "Challenge Leads" spreadsheet

---

## API Keys & Tokens

- All keys in `/home/clawdbot/dev-sandbox/.env`
- Google tokens: `token.json` (gmail), `token_marceausolutions.json` (calendar), `token_sheets.json`
- Refresh on Mac, push to sync to EC2

---

## Session Start Checklist (ALL AGENTS)

1. [ ] `git pull origin main` — Get latest
2. [ ] Check `git log --oneline origin/main..HEAD` — Push any unpushed commits
3. [ ] Read `ARCHITECTURE-DECISIONS.md` — Know the conventions
4. [ ] Read `HANDOFF.md` — Check for pending tasks
5. [ ] Check project-specific `CLAUDE.md` if working on a project

---

*Last Updated: 2026-03-22*
