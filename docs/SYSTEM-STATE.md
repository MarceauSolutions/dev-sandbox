# System State — Marceau Solutions

> Live reference for what is running, what is off, and known issues.
> Update this file after any infrastructure change. Last updated: 2026-03-06.

---

## EC2 Infrastructure (34.193.98.97)

| Service | Status | What It Does |
|---------|--------|-------------|
| `n8n` | ACTIVE | Workflow automation (port 5678) |
| `clawdbot` | ACTIVE | AI assistant via Telegram (@w_marceaubot) |
| `mem0-api` | ACTIVE | Shared agent memory (port 5020) |
| `fitai` | ACTIVE | Fitness influencer platform (fitai.marceausolutions.com) |
| `voice-api` | ACTIVE | Voice AI API |
| `webhook_server.py` | ACTIVE | Ralph webhook handler (port 5002) |
| `stripe-webhook` | STOPPED | Disabled 2026-03-06 — was crash-looping (port conflict with webhook_server.py on 5002). n8n handles Stripe natively. |

### EC2 Resources (as of 2026-03-06)
- **Disk**: 21G/30G (71%)
- **Memory**: ~1.1-1.2G/1.8G (~61-67%)
- **Journal**: Capped at 500MB (`/etc/systemd/journald.conf.d/size-limit.conf`)
- **n8n memory**: Capped at 700M max, 600M high watermark

---

## n8n Workflows (37 active / 12 inactive)

### Critical — Must Stay Active
| Workflow | ID | Status | Purpose |
|----------|-----|--------|---------|
| Self-Annealing-Error-Handler | `Ob7kiVvCnmDHAfNW` | ACTIVE | Fires when any wired workflow errors |
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | ACTIVE | Onboard new PT clients |
| PT-Monday-Check-in | `aBxCj48nGQVLRRnq` | ACTIVE | Weekly client check-in SMS (Mon 9am ET) |
| Webdev-Payment-Welcome | `5GXwor2hHuij614l` | ACTIVE | Onboard new web dev clients |
| SMS-Response-Handler-v2 | `G14Mb6lpeFZVYGwa` | ACTIVE | Handle inbound SMS (STOP compliance: all 6 keywords) |
| n8n-Health-Check | `QhDtNagsZFUrKFsG` | ACTIVE | Periodic n8n self-check |
| GitHub-Push-to-Telegram | `BsoplLFe1brLCBof` | ACTIVE | Notify on every git push |

### Known Inactive (intentionally off)
| Workflow | ID | Reason |
|----------|-----|--------|
| Universal-Agent-Orchestrator-v5.0-Ultra | `1s52PkA1lY1lHfGP` | Dev/test — Ralph handles orchestration |
| Agent-Orchestrator-Debug | `bfHJLnWjyhUESQdU` | Debug build |
| Agent-Orchestrator-Minimal | `xmFDSIrmCO01echh` | Minimal build |
| X-Social-Post-Scheduler | `yBcHFdspRnc4gVUB` | Superseded by v2 (`CT5em35LljouaCrU`) |
| Automated AI YouTube Shorts (Seedance) x2 | `TPDUMHbP3njO2jrN`, `ZaVyQf0C4Ptj4DAQ` | Duplicate — keep one |
| WhatsAppAgent | `T6i0ukvjlet197aC` | Not in active use |
| MyAIagent | `G62V1Uk2yuprxZaB` | Not in active use |
| Naples Real Estate Lead Nurture | `MrYaOZuzF7bJGUt0` | Prospect workflow, not current focus |
| Weather Notification | `Xbj63cGjToMM8Tgp` | Low priority |
| Grok Imagine B-Roll Generator | `sYvUyTooDcHQQuKN` | On-demand, no need for always-on |
| Ultimate Amazon Personal Assistant | `Dv2tGyqE1B59URMJ` | On-demand |

### Error Workflow Wiring (Self-Annealing)
Workflows wired to Self-Annealing-Error-Handler:
- Coaching-Payment-Welcome
- PT-Cancellation-Exit
- Webdev-Payment-Welcome
- Webdev-Monthly-Checkin
- SMS-Response-Handler-v2

---

## Three-Agent System

| Agent | Location | Status | Model |
|-------|----------|--------|-------|
| Claude Code | Mac (this session) | ACTIVE | claude-sonnet-4-6 |
| Clawdbot | EC2 systemd | ACTIVE | claude-opus-4-5 |
| Ralph | EC2 (PRD-driven) | STANDBY | TBD |

### Clawdbot
- Session rotation: weekly cron (Sun 3am UTC)
- Crash alerts: OnFailure → Telegram notification
- Memory: `mem0-api` on EC2 port 5020 (shared with all agents)

---

## Business Automations

### PT Coaching
- Payment → Stripe → n8n webhook → Welcome SMS + ClickUp lead
- Monday 9am ET → SMS check-in to all active clients
- Tracker: https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA

### Web Dev
- Payment → Stripe → n8n webhook → Welcome SMS + ClickUp lead
- Monthly check-in workflow active
- Client Tracker: https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q

### Client Lead Sheets (form submissions routed here)
- HVAC: https://docs.google.com/spreadsheets/d/1Lli3vWKErLR2eUo_623eJbyfohqhaqhKcWndss74eTM
- Square Foot: https://docs.google.com/spreadsheets/d/1Gk-y0G9x30zJnB7YDj1AYmcmaM_Z08pxkw1lodp_8i8

---

## SMS Compliance
- **Number**: +1 855 239 9364 (toll-free, A2P registered)
- **Opt-out keywords handled**: STOP, STOPALL, UNSUBSCRIBE, CANCEL, QUIT, END
- **TCPA hours enforced**: 8am–9pm local time (in `execution/twilio_sms.py`)
- **Opt-out flow**: auto-reply confirmation → mark opted_out in Sheets → Telegram alert

---

## Health Check
```bash
python scripts/health_check.py        # Full check (EC2 + n8n + local)
python scripts/health_check.py --fast # Local only (no SSH)
```

## Known Issues / Open Items
| Item | Priority | Notes |
|------|----------|-------|
| `lead_manager.py:760` | Low | TODO: email notification on CRM stage transitions |
| `amazon_sp_api.py:417` | Low | Hardcoded USD — doesn't support multi-marketplace |
| `agent_bridge_api.py` | Medium | 13,050 lines — modularization planned |
| n8n MCP string/int ID bug | Low | MCP tools expect int IDs, n8n uses strings — use curl via SSH as workaround |
| PT Monday Check-in cron corruption | FIXED 2026-03-06 | Was corrupted with ls output, fixed to 0 14 * * 1 |
| Self-Annealing Switch node | FIXED 2026-03-06 | typeVersion 3 incompatible with n8n 2.4.8, downgraded to v1 |
