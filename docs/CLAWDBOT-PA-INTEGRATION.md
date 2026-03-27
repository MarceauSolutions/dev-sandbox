# Clawdbot ↔ Personal Assistant Integration Protocol

**Date**: March 26, 2026
**Status**: Mac-side API ready. EC2-side (Clawdbot bot code) needs deployment.

## Architecture

```
William → Telegram → Clawdbot (EC2) → HTTP calls → PA Flask API (Mac:5011) → Response
                                    → pipeline.db (EC2 copy) for local queries
```

## Mac-Side API Endpoints (Ready Now)

The Personal Assistant Flask app (port 5011) exposes these endpoints for Clawdbot:

| Endpoint | Method | Clawdbot Trigger | What It Returns |
|----------|--------|------------------|-----------------|
| `/scheduler/today` | GET | "What's my schedule?" | Proposed daily plan with ROI blocks |
| `/scheduler/approve` | POST | "yes schedule" | Creates calendar events, returns confirmation |
| `/scheduler/digest` | GET | "morning briefing" | Full morning digest (pipeline + email + calendar) |
| `/scheduler/health-check` | GET | "system status" | 10-component health check result |
| `/health` | GET | "is PA running?" | Tower health status |

## Clawdbot Command Mapping (To Implement on EC2)

| William Says in Telegram | Clawdbot Does |
|-------------------------|---------------|
| "What's my schedule?" / "schedule" / "plan" | `GET http://MAC_IP:5011/scheduler/today` → format + send |
| "yes schedule" / "approve schedule" | `POST http://MAC_IP:5011/scheduler/approve` → confirm |
| "morning briefing" / "digest" | `GET http://MAC_IP:5011/scheduler/digest` → send digest |
| "system status" / "health" | `GET http://MAC_IP:5011/scheduler/health-check` → send status |
| "pipeline" / "deals" / "leads" | Query local pipeline.db on EC2 (already works) |
| "top leads" | `GET http://MAC_IP:5011/scheduler/today` → extract lead list |

## Network Requirements

For Clawdbot (EC2) to call the PA API (Mac), one of:

1. **Tailscale/ZeroTier VPN** (recommended) — Mac and EC2 on same private network
2. **SSH tunnel** — `ssh -R 5011:localhost:5011 ec2-user@34.193.98.97` (Mac exposes port to EC2)
3. **ngrok** — `ngrok http 5011` (temporary public URL)
4. **Pipeline.db sync only** — Clawdbot reads the EC2 copy of pipeline.db (no HTTP needed for basic queries)

**For now**: Option 4 works for pipeline queries. Options 1-3 needed for schedule/digest.

## Notification Routing (Already Working)

| Notification | Channel | Implementation |
|-------------|---------|----------------|
| HOT lead alert | SMS (Twilio → phone) | `daily_loop.py send_hot_lead_sms()` |
| Morning digest | Telegram (bot → chat) | `unified_morning_digest.py send_telegram()` |
| Pipeline digest | Telegram (bot → chat) | `daily_loop.py stage_digest()` |
| Health alerts | Telegram (bot → chat) | `standardization_enforcer.py send_alert()` |
| Loop degradation | Telegram (bot → chat) | `daily_loop.py record_run_health()` |

**All already working** — these send TO Telegram. The new endpoints enable Clawdbot to QUERY the PA.

## Deployment Steps (for EC2)

1. Choose network option (Tailscale recommended for permanent connection)
2. Add command handlers to Clawdbot's bot code for the Telegram commands above
3. Each handler calls the appropriate PA API endpoint via HTTP
4. Format the JSON response as a readable Telegram message
5. Test: send "schedule" in Telegram → Clawdbot calls PA → returns today's plan

## Handoff to Ralph

This integration requires EC2-side changes to Clawdbot's bot code. Create a handoff:

```bash
python3 execution/three_agent_orchestrator.py handoff --to ralph \
  --task "Add PA schedule query commands to Clawdbot Telegram bot — see docs/CLAWDBOT-PA-INTEGRATION.md"
```
