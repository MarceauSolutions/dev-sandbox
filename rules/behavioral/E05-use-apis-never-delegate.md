---
rule: E05
name: Use APIs, Never Delegate
hook: no-delegation-guard.sh (BLOCKING for "you should", "you'll need to", "manually")
trigger: Any time about to tell William to do something manually that a tool or API could handle
---

## Rule

Check `.env`, `execution/`, and MCP tools BEFORE telling William to do anything manually. If the capability exists in the stack, use it. Never say "you'll need to log into X" or "you should manually Y" without first exhausting the automated options.

## Why it exists

Repeated pattern of Claude saying "you'll need to manually do X" for tasks that had API solutions already configured in `.env` or `execution/`. This defeats the purpose of the automation stack.

## How to apply

Before telling William to do anything manually:
1. Check `.env` — does a relevant API key exist?
2. Check `execution/` — `python scripts/inventory.py search <capability>`
3. Check available MCP tools (Gmail, Google Calendar, etc.)
4. Check `docs/SYSTEM-STATE.md` — is there an existing system for this?

If all 4 checks come up empty → then (and only then) tell William the manual step, AND explain why automation isn't available.

## Tooling available in the stack

| Capability | Tool |
|------------|------|
| Send email | `execution/send_onboarding_email.py` (SMTP) |
| Send SMS | `execution/twilio_sms.py` |
| Generate PDF | `execution/branded_pdf_engine.py` |
| Read Gmail | MCP Gmail tools (`gmail_search_messages`, etc.) |
| Google Calendar | MCP Calendar tools |
| Google Sheets | Sheets API via token.json |
| Lead enrichment | Apollo API (key in .env) |
| Create Telegram message | Clawdbot API |
| n8n workflow trigger | n8n webhook |

## Examples

- Need to email a client → use `execution/send_onboarding_email.py` SMTP pattern, not "you should send an email"
- Need to check calendar → use MCP gcal_list_events, not "check your calendar"
- Need to send a lead follow-up SMS → use `execution/twilio_sms.py`, not "text them on your phone"
