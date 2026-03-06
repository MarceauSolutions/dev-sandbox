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

> Full inventory: `python scripts/backup-n8n.py --list`

### Infrastructure — Must Stay Active
| Workflow | ID | Purpose |
|----------|-----|---------|
| Self-Annealing-Error-Handler | `Ob7kiVvCnmDHAfNW` | Fires when any wired workflow errors |
| SMS-Response-Handler-v2 | `G14Mb6lpeFZVYGwa` | Handle inbound SMS (STOP compliance: all 6 keywords) |
| n8n-Health-Check | `QhDtNagsZFUrKFsG` | Periodic n8n self-check |
| GitHub-Push-to-Telegram | `BsoplLFe1brLCBof` | Notify on every git push |
| Daily-Operations-Digest | `Hz05R5SeJGb4VNCl` | Daily business metrics digest |
| Monthly-Workflow-Backup | `2QaQbhIUlL7ctfq4` | n8n workflow DR backup (monthly) |

### PT Coaching — Must Stay Active
| Workflow | ID | Purpose |
|----------|-----|---------|
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | Onboard new PT clients |
| Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | Weekly check-in SMS (Mon 9am ET) |
| Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | Cancellation flow + offboarding |
| Fitness-SMS-Outreach | `89XxmBQMEej15nak` | Outbound prospect outreach via webhook |
| Fitness-SMS-Followup-Sequence | `VKC5cifm595JNcwG` | Multi-step drip after initial outreach |

### Lead Generation & Funnels — Must Stay Active
| Workflow | ID | Purpose |
|----------|-----|---------|
| Lead-Magnet-Capture | `hgInaJCLffLFBX1G` | marceausolutions.com lead magnet submissions |
| Website-Lead-Capture | `WHFIE3Ej7Y3SCtHk` | marceausolutions.com contact form |
| Automation-Lead-Capture | `dATO8F4MoPcpOKiA` | Automation service lead capture |
| Creator-Lead-Capture | `8pvrmdtI0MfPbdsC` | Creator/influencer lead capture |
| Premium-Waitlist-Capture | `j306crRxCmWW3dMo` | Premium product waitlist |
| Challenge-Signup-7Day | `WTZDxLDQuSkIkcqf` | 7-day challenge signup flow |
| Hot-Lead-to-ClickUp | `SzVXrbi1y433799Y` | Route hot leads to CRM |

### Nurture & Conversion
| Workflow | ID | Purpose |
|----------|-----|---------|
| Automation-Nurture-7Day | `cV2e9opfEKR1Tx5v` | 7-day automation nurture sequence |
| Creator-Nurture-7Day | `Fv0tGHevTfVOUnj2` | 7-day creator nurture sequence |
| Nurture-Sequence-7Day | `szuYee7gtQkzRn3L` | General 7-day nurture |
| Website-Nurture-7Day | `tbTB4XmjlvNqrBaQ` | Website lead nurture |
| Follow-Up-Sequence-Engine | `w8PYKJyeozM3qJQW` | Multi-step follow-up engine |
| Non-Converter-Followup | `Y2jfeIlTRDlbCHeS` | Re-engage non-converters |
| Challenge-Day7-Upsell | `Xza1DB4f4PIHw2lZ` | Day 7 challenge upsell trigger |
| Digital-Product-Delivery | `kk7ZjWtjmZgylVzi` | Digital product delivery automation |

### Web Dev Business
| Workflow | ID | Purpose |
|----------|-----|---------|
| Webdev-Payment-Welcome | `5GXwor2hHuij614l` | Onboard new web dev clients |
| Webdev-Monthly-Checkin | `N8HIFsZdE5Go7Lky` | 1st of month SMS to all active clients |
| Webdev-Deploy-Notification | `E0DivEtTGgVZm3v6` | Deploy webhook → client SMS + admin |
| Webdev-Cross-Referral | `eoQMjVYQSibMALaZ` | PT→WebDev cross-business handoff |
| Flames-Form-Pipeline | `mrfVYqg5H12Z2l5K` | Flames client form → Sheets + Telegram |

### Content & Social
| Workflow | ID | Purpose |
|----------|-----|---------|
| X-Social-Post-Scheduler-v2 | `CT5em35LljouaCrU` | X/Twitter post scheduling |
| X-Batch-Image-Generator | `EgLcSeovV58t5OJS` | Batch image generation for X |
| X-Post-Image-Generator | `Hv8ybyKYNYDFwSgm` | Single post image generation |
| Add-Posts-Webhook | `bzt3KFpwWmPbrp34` | Add posts via webhook trigger |
| Weekly-Campaign-Analytics | `M62QBpROE48mEgDC` | Weekly campaign performance report |

### Other Active
| Workflow | ID | Purpose |
|----------|-----|---------|
| Resume-Builder-Webhook | `jxL3AYDNAGDo0Gf7` | Resume builder webhook pipeline |

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

## Operations Commands
```bash
./scripts/daily_standup.sh            # Morning routine (health + revenue + digest + links)
python scripts/health_check.py        # Full check (EC2 + n8n + local) — exits 1 on failure
python scripts/health_check.py --fast # Local only (no SSH)
python scripts/revenue-report.py      # Revenue snapshot (last 7 days)
python scripts/backup-n8n.py          # Export all n8n workflows → backups/YYYY-MM-DD.json
python scripts/backup-n8n.py --list   # List all workflows (no backup)
```

## Known Issues / Open Items
| Item | Priority | Notes |
|------|----------|-------|
| n8n workflow backup | **Medium** | Run `python scripts/backup-n8n.py` weekly + commit. Last backup: NEVER. Old `backup-n8n-workflows.sh` is stale (hardcoded IDs) — use new script. |
| `lead_manager.py:760` | Low | TODO: email notification on CRM stage transitions |
| `amazon_sp_api.py:417` | Low | Hardcoded USD — doesn't support multi-marketplace |
| `agent_bridge_api.py` | Medium | 13,050 lines — modularization planned |
| n8n MCP string/int ID bug | Low | MCP tools expect int IDs, n8n uses strings — use curl via SSH as workaround |
| PT Monday Check-in cron corruption | FIXED 2026-03-06 | Was corrupted with ls output, fixed to 0 14 * * 1 |
| Self-Annealing Switch node | FIXED 2026-03-06 | typeVersion 3 incompatible with n8n 2.4.8, downgraded to v1 |
