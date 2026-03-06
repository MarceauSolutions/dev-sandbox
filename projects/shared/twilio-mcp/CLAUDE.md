# Twilio MCP

**Version**: See `pyproject.toml` | **Status**: Built | **Type**: MCP Package
**MCP name**: `io.github.wmarceau/twilio-mcp`

## What It Does
MCP server giving Claude direct access to the Twilio SMS inbox. Check incoming replies, send SMS, summarize reply sentiment (hot leads, opt-outs), get campaign stats, forward important messages to personal phone.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |

## Tools
| Tool | What |
|------|------|
| `check_sms_inbox` | Check incoming SMS replies from cold outreach |
| `send_sms` | Send SMS to a number |
| `get_sms_reply_summary` | Categorize replies (hot, cold, opt-out) |
| `get_hot_leads` | Get interested leads needing follow-up |
| `get_campaign_stats` | View outreach campaign stats |
| `forward_message_to_phone` | Forward important messages to personal phone |

## Prerequisites
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` in `.env`
- Primary number: `+1 855 239 9364` (toll-free, A2P registered)

## Note
For programmatic SMS in scripts, use `execution/twilio_sms.py` directly. This MCP is for interactive use in Claude conversations.

## Related
- Twilio script: `execution/twilio_sms.py`
- Inbox monitor: `execution/twilio_inbox_monitor.py`
- Lead scraper: `projects/shared/lead-scraper/`
