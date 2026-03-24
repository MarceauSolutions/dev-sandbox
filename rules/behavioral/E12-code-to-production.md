---
rule: E12
name: Code to Production Pipeline
hook: interface-first-guard.sh (warning when creating user-facing .py files)
trigger: After any script is working locally — do not stop there
---

## Rule

A working local script is NOT a shipped product. CLI is NEVER the final interface for William-facing tools. Every tool must go through the full 7-step pipeline before being marked done.

## Why it exists

Tools kept being built as CLI scripts and declared "done." The accountability system was spec'd but never deployed. The dystonia digest was a Mac launchd email script. The multi-Gmail search was a Python CLI. All required rebuilding because the interface decision was skipped.

## The 7-Step Pipeline

```
Step 1: Interface decision FIRST (before writing code)
        → "How will William use this?"
        → See rules/routing/ROUTING.md tree #1
        → CLI is NEVER the answer for William-facing tools

Step 2: Build core logic
        → Python script, API integration, engine
        → Write to projects/[name]/src/ or execution/ (see code-placement rules)

Step 3: Wire to chosen interface
        → Clawdbot: add command handler, deploy to EC2
        → n8n: build workflow, set trigger, test
        → Web app: FastAPI routes, template if needed
        → PDF: correct template + data keys
        → SMS/Email: twilio_sms.py or SMTP pattern

Step 4: Deploy to production
        → EC2 systemd service (for persistent processes)
        → nginx proxy + subdomain + SSL (for web apps)
        → n8n workflow activated (for automations)
        → git push (for Clawdbot to sync)

Step 5: Verify access
        → "Can William use this from his phone right now, without me?"
        → If no → keep building
        → Test with real data, not mocked data

Step 6: Launch script (web apps only)
        → scripts/[name].sh — one command, browser opens
        → Document URL in docs/SYSTEM-STATE.md

Step 7: Documentation
        → Update docs/SYSTEM-STATE.md (URL, port, service name)
        → Update docs/session-history.md
        → Update project CLAUDE.md
```

## Checklist Before Marking Done

```
[ ] Interface decision was made BEFORE coding
[ ] Core logic built and tested locally
[ ] Wired to chosen interface (Clawdbot / n8n / web / PDF / SMS)
[ ] Deployed to EC2 or n8n (not just running on Mac)
[ ] Verified: William can use this from phone without me
[ ] Launch script exists if web app
[ ] SYSTEM-STATE.md updated
```

## Examples

- Lead tracker script works locally → wire to Clawdbot command → deploy → verify via Telegram from phone
- Digest email script works locally → build n8n workflow → activate → verify email arrives tomorrow morning
- PDF generation script works locally → that IS production (branded_pdf_engine.py is already production)
- Dashboard script works locally → build FastAPI → EC2 systemd → nginx → scripts/dashboard.sh → verify
