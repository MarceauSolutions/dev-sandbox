---
rule: E10
name: Best-Path Evaluation
hook: interface-first-guard.sh (warning when creating user-facing .py files)
trigger: Before building ANYTHING — tool, script, workflow, or system
---

## Rule

Never default to the easiest implementation. Before writing any code, answer the 5 evaluation questions and choose the right interface, not the fastest-to-code one. CLI is almost never the right answer for William.

## Why it exists

Claude repeatedly chose the fastest-to-code path: terminal scripts, markdown files, manual spreadsheets. The accountability system was built as markdown files. The dystonia digest was a Mac launchd cron script. The multi-Gmail search was a Python CLI. All had to be rebuilt for the correct interface.

## The 5 Questions (answer all before writing code)

**Q1: Who is the end user and how will they interact?**
- William on mobile, low-energy day → Telegram command or SMS (zero friction)
- William at Mac → Web app (still not CLI)
- A client → Branded PDF or email (no login required)
- An automation → Python script called by n8n (fine as CLI, never user-facing)
- Answer determines the interface. CLI is almost never right for William.

**Q2: What existing infrastructure fits?**
- Conversational → Clawdbot (already running EC2)
- Automation → n8n (41+ active workflows)
- Fitness → FitAI (already built)
- Documents → branded_pdf_engine.py (10 templates)
- Alerts → Twilio (A2P registered)
- Build ON these, not beside them

**Q3: How does this need to scale?**
- 1 user, one-time → simple is fine
- 1 user, daily → n8n + SQLite
- Multiple users → proper DB schema now
- Design for the 6-month version

**Q4: What are the real constraints?**
- William has dystonia — some days low energy, left side affected
- Must work from phone on worst-case day
- Naples FL — local market features
- Currently building AI client base — tools must look professional

**Q5: Is there a consolidation opportunity?**
- New capability in Clawdbot > new bot
- New PDF template > new PDF script
- New FitAI feature > separate fitness app
- New n8n node > new workflow

## How to apply

Before writing any .py file for a user-facing feature:
```
Interface decision: [ ] Clawdbot  [ ] n8n  [ ] Web app  [ ] PDF  [ ] SMS/Email
CLI? → STOP, go back to Q1
```

Document your reasoning in the task response: "E10 evaluation: William will use this from phone → Clawdbot command, not CLI"

## Examples

- Building a lead tracker → web app at subdomain (not `python tracker.py`)
- Building a daily digest → n8n workflow (not Mac launchd cron)
- Building a client report → branded PDF (not markdown file)
- Building a lookup tool → Clawdbot command (not CLI script)
