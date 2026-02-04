# Kanban Board

## Backlog
| Task | Added | Notes |
|------|-------|-------|
| **SECURITY: Enable HTTPS for n8n** | 2026-02-02 | Credentials sent unencrypted over HTTP; use Let's Encrypt |
| **SECURITY: Add IP restriction for n8n admin** | 2026-02-02 | Currently anyone worldwide can attempt login |
| **SECURITY: Enable rate limiting for n8n** | 2026-02-02 | Prevent brute force attacks on login |
| Integrate Clawdbot AI assistant with Voice AI (Twilio) | 2026-01-27 | Could auto-respond to calls/SMS |
| Integrate Clawdbot with existing Twilio phone numbers | 2026-01-27 | WhatsApp Business API or SMS integration |
| Fix DOCKET.md system | 2026-01-27 | Current docket system not working properly |
| Add Ollama embedding support to Clawdbot memory-lancedb | 2026-01-27 | Plugin hardcoded for OpenAI only; Ollama installed on EC2 |

## In Progress
| Task | Started | Notes |
|------|---------|-------|
| (none) | | |

## Done
| Task | Completed | Notes |
|------|-----------|-------|
| Deploy SMS webhook handler to EC2 | 2026-01-26 | |
| Update Twilio SMS webhook URL | 2026-01-26 | |
| Get SSL certificate for api.marceausolutions.com | 2026-01-26 | |
| Set up Clawdbot on EC2 | 2026-01-27 | Running as systemd service |
| Configure Claude Max OAuth for Clawdbot | 2026-01-27 | Uses subscription, not API credits |
| Link WhatsApp to Clawdbot | 2026-01-27 | Personal number linked |
| Configure Telegram to interact with Clawdbot | 2026-01-27 | @W_marceaubot, DM policy "open", memory disabled |
