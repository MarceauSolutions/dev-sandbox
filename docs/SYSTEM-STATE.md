# System State — Marceau Solutions

> Live reference for what is running, what is off, and known issues.
> Update this file after any infrastructure change. Last updated: 2026-03-06 (session 12 + xAI key renewal).

---

## ⚠️ COMPLETED WORK — DO NOT REDO

Sessions 1-12 are DONE. Do not restart these efforts. See `docs/session-history.md` for full log.

| What | Status | Session |
|------|--------|---------|
| All n8n mode:name Google Sheets nodes (19) | ✅ Converted to mode:id | 10 |
| All n8n mode:list Google Sheets nodes (13) | ✅ Converted to mode:id | 11 |
| All missing Sheets tabs created | ✅ Done (7 tabs total) | 10-11 |
| Self-Annealing wired to all wireable workflows | ✅ 36/38 (100%) | 7-12 |
| All Stripe webhooks registered + verified | ✅ 6/6 active | 8 |
| health_check.py — full system monitoring | ✅ EC2 + n8n + AI APIs + Telegram + Stripe | 4-12 |
| n8n task runner crash-loop fix | ✅ Symlink in place on EC2 | 12 |
| GitHub→Telegram Telegram cred patched | ✅ Auto-monitored in health_check | 12 |
| xAI API key renewed + X-Batch re-activated | ✅ 38 active workflows | post-12 |
| Mac launchd: daily 7am health check | ✅ Active | 4 |
| Mac launchd: Monday 9am revenue report | ✅ Active | 4 |
| Mac launchd: Sunday 4am n8n backup | ✅ Active | 4 |

**Current state: 38 active workflows, 4 inactive (all intentional), 0 active failures.**

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
| `dystonia-digest` | ACTIVE | Dystonia Research Digest web dashboard (port 8792, dystonia.marceausolutions.com) |
| `stripe-webhook` | STOPPED | Disabled 2026-03-06 — was crash-looping (port conflict with webhook_server.py on 5002). n8n handles Stripe natively. |

### EC2 Resources (as of 2026-03-06 session 2)
- **Disk**: 21G/30G (70%) — freed ~220MB (old SQLite backups + /tmp/jiti cache + journals)
- **Memory**: ~999M-1.1G/1.8G (~54-61%)
- **Journal**: Capped at 500MB (`/etc/systemd/journald.conf.d/size-limit.conf`)
- **n8n memory**: Capped at 700M max, 600M high watermark

---

## n8n Workflows (41 active / 4 inactive)

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
| Dystonia-Research-Digest-Daily | `pUuUxu5s37UPkxyq` | Daily 7am ET research digest → email + archive + Telegram |

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
| Hot-Lead-to-ClickUp | `SzVXrbi1y433799Y` | Route hot leads to CRM (INACTIVE — ClickUp not in stack) |

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
| X-Batch-Image-Generator | `EgLcSeovV58t5OJS` | Batch X post image generation |
| X-Post-Image-Generator | `Hv8ybyKYNYDFwSgm` | Single post image generation |
| Add-Posts-Webhook | `bzt3KFpwWmPbrp34` | Add posts via webhook trigger |
| Weekly-Campaign-Analytics | `M62QBpROE48mEgDC` | Weekly campaign performance report |

### Stripe Event Handlers
| Workflow | ID | Purpose |
|----------|-----|---------|
| Stripe-Payment-Failed | `QMWkhAb8SWMSImc4` | invoice.payment_failed → Telegram alert |
| Stripe-Invoice-Paid | `unF3M3IfnGPqV0xU` | invoice.paid (renewals) → PT Tracker Sheets + Telegram |

### Accountability System (90-Day Plan)
| Workflow | ID | Purpose |
|----------|-----|---------|
| Morning-Accountability-Checkin | `XNrR99vPCUp89X8L` | 6:45am ET Mon-Fri → context-aware morning message with Sheets data |
| EOD-Accountability-Checkin | `0Zf8nNv1AphA0W6s` | 7pm ET Mon-Fri → EOD prompt for outreach/meetings/videos/content |
| Weekly-Accountability-Report | `krxeoSZMMPBZGAPv` | 7pm ET Sunday → full weekly scorecard with totals vs targets |

**Reply handling**: Clawdbot runs `execution/accountability_handler.py --type parse --text "MESSAGE"` for all accountability patterns. Logs to Scorecard Sheet (`1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o`). Milestone checking built into EOD handler.

### Other Active
| Workflow | ID | Purpose |
|----------|-----|---------|
| Resume-Builder-Webhook | `jxL3AYDNAGDo0Gf7` | Resume builder webhook pipeline |

### Known Inactive (intentionally off)
| Workflow | ID | Reason |
|----------|-----|--------|
| Hot-Lead-to-ClickUp | `SzVXrbi1y433799Y` | ClickUp not in stack — deactivated 2026-03-06 |
| Weather Notification | `Xbj63cGjToMM8Tgp` | Low priority, on-demand |
| Automated AI YouTube Shorts (Seedance) | `ZaVyQf0C4Ptj4DAQ` | Content pipeline paused |
| Grok Imagine B-Roll Generator | `sYvUyTooDcHQQuKN` | On-demand, no need for always-on |

> 9 dead workflows deleted 2026-03-06: Agent-Orchestrator (Debug/Minimal/Ultra), Naples RE, WhatsApp, MyAIagent, Amazon, X-Scheduler (v1), YouTube Shorts (old).

### Error Workflow Wiring (Self-Annealing)
36 of 38 active workflows wired to `Self-Annealing-Error-Handler` (`Ob7kiVvCnmDHAfNW`). Updated 2026-03-06 session 12.

**Not wired (2 — intentional):** Self-Annealing-Error-Handler (can't self-reference), n8n-Health-Check (circular).

**All other 36 active workflows wired** — 100% of wireable workflows covered.

---

## Three-Agent System

| Agent | Location | Status | Model |
|-------|----------|--------|-------|
| Claude Code | Mac (this session) | ACTIVE | claude-sonnet-4-6 |
| Clawdbot | EC2 systemd | ACTIVE | Anthropic OAuth (model not configurable via clawdbot.json) |
| Ralph | EC2 (PRD-driven) | STANDBY | TBD |

### Clawdbot
- Session rotation: weekly cron (Sun 3am UTC)
- Crash alerts: OnFailure → Telegram notification
- Memory: `mem0-api` on EC2 port 5020 (shared with all agents)

---

## Business Automations

### PT Coaching
- Payment → Stripe → n8n webhook → Welcome SMS
- Monday 9am ET → SMS check-in to all active clients
- Tracker: https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA

### Web Dev
- Payment → Stripe → n8n webhook → Welcome SMS
- Monthly check-in workflow active (1st of month)
- Client Tracker: https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q

### Client Lead Sheets (form submissions routed here)
- HVAC: https://docs.google.com/spreadsheets/d/1Lli3vWKErLR2eUo_623eJbyfohqhaqhKcWndss74eTM
- Square Foot: https://docs.google.com/spreadsheets/d/1Gk-y0G9x30zJnB7YDj1AYmcmaM_Z08pxkw1lodp_8i8

---

## SMS Compliance
- **Primary number**: +1 855 239 9364 (toll-free, A2P registered) → SMS webhook: n8n `sms-response`
- **PT local** (inactive): +1 239 880-3365 → SMS webhook: n8n `sms-response` (FIXED 2026-03-06 — was empty)
- **HVAC client**: +1 239 766-6129 → SMS webhook: n8n `sms-response` (FIXED 2026-03-06 — was empty)
- **Opt-out keywords handled**: STOP, STOPALL, UNSUBSCRIBE, CANCEL, QUIT, END
- **TCPA hours enforced**: 8am–9pm local time (in `execution/twilio_sms.py`)
- **Opt-out flow**: auto-reply confirmation → mark opted_out in Sheets → Telegram alert
- **Voice webhooks**: all numbers → POST `https://api.marceausolutions.com/twilio/voice` (200 OK)

---

## External Integrations (Verified 2026-03-06)

### Stripe Webhooks (6 active, all → n8n.marceausolutions.com)
| Endpoint | Event | Workflow | Stripe ID |
|----------|-------|---------|-----------|
| `/webhook/stripe-payment-welcome` | checkout.session.completed | PT coaching onboard | — |
| `/webhook/stripe-webdev-payment` | checkout.session.completed | WebDev client onboard | — |
| `/webhook/stripe-cancellation` | customer.subscription.deleted | Coaching offboard | — |
| `/webhook/stripe-digital-delivery` | checkout.session.completed | Digital product delivery | — |
| `/webhook/stripe-payment-failed` | invoice.payment_failed | Lookup phone → SMS client + Telegram to William | `we_1T85t0DeeD1eRvzzjpNKpvGA` |
| `/webhook/stripe-invoice-paid` | invoice.paid | Log renewal to PT Tracker + Telegram | `we_1T862eDeeD1eRvzzdYkDJUzb` |

### Twilio Inbound SMS (all → `sms-response`)
| Number | Label | SMS Webhook |
|--------|-------|-------------|
| +1 855-239-9364 | Toll-free A2P (primary) | n8n sms-response |
| +1 239-880-3365 | PT local (inactive outbound) | n8n sms-response |
| +1 239-766-6129 | HVAC client | n8n sms-response |
Voice: all → `https://api.marceausolutions.com/twilio/voice` (POST 200 OK)

### Client Websites (Domain Monitoring)
| Domain | Status | Client |
|--------|--------|--------|
| `swfloridacomfort.com` | HTTP 200 ✓ | SW Florida Comfort HVAC |
| `www.boabfit.com` | HTTP 200 ✓ (301 from apex) | BoabFit |
| `flamesofpassionentertainment.com` | DNS not configured | Flames of Passion (client-blocked) |

### n8n Webhook Domain
- `https://n8n.marceausolutions.com` — public-facing, HTTP 200 ✓
- 29 registered webhooks (added stripe-invoice-paid, stripe-payment-failed)

---

## Operations Commands
```bash
./scripts/daily_standup.sh            # Morning routine (health + revenue + digest + links)
python scripts/health_check.py                  # Full check (EC2 + n8n + local) — exits 1 on failure
python scripts/health_check.py --fast           # Local only (no SSH)
python scripts/health_check.py --repatch-telegram  # Fix stale GitHub→Telegram cred + bounce workflow
python scripts/revenue-report.py      # Revenue snapshot (last 7 days)
python scripts/backup-n8n.py          # Export all n8n workflows → backups/YYYY-MM-DD.json
python scripts/backup-n8n.py --list   # List all workflows (no backup)
```

## Known Issues / Open Items
| Item | Priority | Notes |
|------|----------|-------|
| n8n workflow backup | **Low** | Weekly launchd job active (Sun 4am). Last backup: 2026-03-06 21:20 (40 workflows, post all session 7 fixes including Self-Annealing wiring). Use `python scripts/backup-n8n.py --commit` to backup + auto-commit. |
| Stripe: legacy `webhooks.marceausolutions.com` endpoint | FIXED 2026-03-06 (session 6) | Was returning 404 but still registered in Stripe — removed. Added missing `stripe-webdev-payment` endpoint. All 4 Stripe webhooks now point to n8n. |
| Twilio SMS webhook empty on local PT + HVAC numbers | FIXED 2026-03-06 (session 6) | +12398803365 and +12397666129 had no SMS webhook — inbound texts dropped. Set to `sms-response` handler. |
| `lead_manager.py:760` | Low | TODO: email notification on CRM stage transitions |
| `amazon_sp_api.py:417` | Low | Hardcoded USD — doesn't support multi-marketplace |
| `agent_bridge_api.py` | Medium | 13,050 lines — modularization planned |
| n8n MCP string/int ID bug | Low | MCP tools expect int IDs, n8n uses strings — use curl via SSH as workaround |
| PT Monday Check-in cron corruption | FIXED 2026-03-06 | Was corrupted with ls output, fixed to 0 14 * * 1 |
| Self-Annealing Switch node | FIXED 2026-03-06 | typeVersion 3 incompatible with n8n 2.4.8, downgraded to v1 |
| GitHub→Telegram credential | FIXED 2026-03-06 | "Clawdbot Telegram" n8n credential had stale bot token. Updated via API. Verified working on next push. |
| Deleted Google Sheets credential `RIFdaHtNYdTpFnlu` | FIXED 2026-03-06 | 3 webdev workflows referenced deleted credential. Remapped to `mywn8S0xjRx9YM9K`. |
| X-Batch-Image-Generator broken connection | FIXED 2026-03-06 | `Update Media_URL` pointed to non-existent "Rate Limit (Wait)" node. Fixed via SQLite to "Wait 5s (Rate Limit)". |
| Challenge-Day7-Upsell sheetName lookup | FIXED 2026-03-06 | `mode:name` caused runtime API lookup failure. Changed to `mode:id` (gid=0). |
| Weekly-Campaign-Analytics Twilio type mismatch | FIXED 2026-03-06 | httpBasicAuth cred created (`hS85CMA24G8bUxDY`) for Twilio HTTP node. |
| Follow-Up-Sequence-Engine no credentials | FIXED 2026-03-06 | Google Sheets + 3 Twilio nodes had empty credential refs. Fixed via SQLite. |
| Hot-Lead-to-ClickUp active with no ClickUp stack | FIXED 2026-03-06 | Deactivated. ClickUp not in stack — Hot-Lead-to-ClickUp moved to inactive. |
| Clawdbot invalid `model` key in config | FIXED 2026-03-06 | Top-level `model` key not valid in clawdbot.json schema — caused config reload failures. Removed. |
| Daily-Operations-Digest corrupted cron + no credentials | FIXED 2026-03-06 | Same ls-injection bug as PT Monday Check-in. Fixed cron to `0 0 13 * * *` (8am ET, 6-field). Assigned Gmail/Sheets/SMTP credentials. Fixed workflow_history version. Now active and scheduled. |
| Resume-Builder Email Delivery no Gmail credential | FIXED 2026-03-06 | Gmail node had no credential assigned. Assigned Gmail account (`Fy8WXPJMuD57XWjw`). |
| Follow-Up-Sequence-Engine no credentials | FIXED 2026-03-06 | Twilio (×3) and Google Sheets nodes had empty credentials. All fixed. |
| SQLite cron fixes missing workflow_history update | FIXED 2026-03-06 (session 4) | n8n reads workflow_history (not workflow_entity) on activation. All SQLite node fixes must also update workflow_history.nodes for the current versionId. |
| Webdev-Monthly-Checkin only ran in January | FIXED 2026-03-06 (session 4) | triggerAtMonth:1 in schedule parameters limited workflow to January. Removed field — now runs 1st of every month. |
| 5-field cronExpression in scheduleTrigger nodes | FIXED 2026-03-06 (session 4) | n8n scheduleTrigger (typeVersion 1.2) requires 6-field cron (seconds first). Fixed 6 workflows: X-Batch, X-Social-Scheduler (×2), PT-Monday-Checkin, Challenge-Day7, Monthly-Backup. All bounced and active. |
| SQLite-patched workflows stale in n8n memory | FIXED 2026-03-06 (session 4) | All 8 workflows patched via SQLite in session 3 were bounced (deactivate/activate via API) to reload from DB. |
| Mac has no autonomous health monitoring | FIXED 2026-03-06 (session 4) | Added launchd: daily health check (7am) + weekly revenue report (Mon 9am). Both loaded and registered. |
| GitHub→Telegram stale Telegram credential | FIXED 2026-03-06 (session 7) | "Clawdbot Telegram" cred `RlAwU3xzcX4hifgj` had stale/encrypted token. Re-PATCHED via n8n API. Was causing 5 errors per push. |
| health_check.py missing n8n restart + domain checks | FIXED 2026-03-06 (session 7) | Added n8n restart counter (warns >1, fails >3 restarts/24h) and external domain health (n8n, api, fitai — all 200). |
| invoice.payment_failed unhandled | FIXED 2026-03-06 (session 7b) | Created `Stripe-Payment-Failed` workflow (`QMWkhAb8SWMSImc4`). Stripe webhook `we_1T85t0DeeD1eRvzzjpNKpvGA` registered. Payment failures now trigger Telegram alert to William. |
| flamesofpassionentertainment.com DNS not configured | **Client-blocked** | Domain on Google Cloud DNS (ns-cloud-c1-c4.googledomains.com). No A records pointing to GitHub Pages. Client or William must add A records: 185.199.108-111.153. GitHub Pages site is live at `marceausolutions.github.io/flames-of-passion-website`. |
| 7 workflows not wired to Self-Annealing | FIXED 2026-03-06 (session 7) | Wired 7 remaining workflows (nurture sequences ×4, Add-Posts-Webhook, Resume-Builder, X-Post-Image-Generator). Now 34/36 active workflows wired. Only Self-Annealing + n8n-Health-Check excluded intentionally. |
| Stripe-Payment-Failed no client notification | FIXED 2026-03-06 (session 8) | Updated workflow to: lookup client phone in PT Tracker → SMS client to update payment method → Telegram alert to William. Fully automated payment failure response. |
| invoice.paid unhandled (subscription renewals) | FIXED 2026-03-06 (session 8) | Created `Stripe-Invoice-Paid` (`unF3M3IfnGPqV0xU`). Stripe webhook `we_1T862eDeeD1eRvzzdYkDJUzb` registered. Renewals now log to PT Tracker "Billing" tab + Telegram. Column mapping aligned with Coaching-Payment-Welcome (Date, Client_Name, Amount, Status=Renewal, Stripe_Payment_ID). |
| health_check.py missing Stripe webhook verification | FIXED 2026-03-06 (session 8) | Added `check_stripe_webhooks()` — verifies all 6 Stripe webhooks are registered and enabled in Stripe. Fires as part of full health check. |
| boabfit.com not in domain monitoring | FIXED 2026-03-06 (session 8) | Added `www.boabfit.com` to `check_domains()` in health_check.py. Live at 200. |
| health_check.py key-only AI API checks | FIXED 2026-03-06 (session 9) | Added `check_ai_apis()` — live validation of Anthropic (GET /v1/models, zero token cost) and ElevenLabs (character quota). Fires before Stripe webhooks check. Both keys valid as of session 9. |
| revenue-report.py missing top-client breakdown | FIXED 2026-03-06 (session 9) | Added "Top Clients by Revenue" section (top 5 by total_charged). Uses existing `by_customer` dict from `get_stripe_metrics()`. |
| X-Batch-Image-Generator erroring daily | FIXED 2026-03-06 (session 9 + xAI renewal) | xAI API key was invalid (403). Deactivated session 9. Key renewed 2026-03-06 → all 3 n8n xAI creds updated (R7R9kSbJia6KqFXS, P1H6Vz9nbdj2q1KU, apaXiy1xUNcOIy1S) → workflow re-activated. Now 38 active. |
| Webdev-Monthly-Checkin running DAILY instead of monthly | FIXED 2026-03-06 (session 9) | `{triggerAtDayOfMonth: 1, triggerAtHour: 10}` without `field` key defaults to DAILY in n8n. Was potentially SMS-ing web dev clients every day. Fixed to explicit `cronExpression: "0 0 10 1 * *"` (10 AM ET on 1st of month). Bounced. |
| daily_standup.sh broken morning digest command | FIXED 2026-03-06 (session 9) | `python -m projects.shared.personal-assistant.src.morning_digest` fails (dashes in path). Fixed to subshell `(cd projects/shared/personal-assistant && python -m src.morning_digest --preview)`. |
| All Google Sheets mode:name nodes (19 total) | FIXED 2026-03-06 (session 10) | mode:name does runtime API lookup that can fail under load. Converted ALL 19 nodes across 13 workflows to mode:id with verified GIDs. PT Tracker GIDs: Client Roster=1584175390, Billing=1695379925, Weekly Check-Ins=1875514153. Challenge GIDs: Leads=0. Also created 4 missing tabs: Form_Submissions, SMS_Responses, Follow_Up_Sequences (ops sheet), Premium Waitlist (challenge sheet). |
| All Google Sheets mode:list nodes (13 total) | FIXED 2026-03-06 (session 11) | mode:list does same runtime API lookup as mode:name. Converted all 13 nodes across 12 workflows to mode:id. WebDev Tracker GIDs: Web Dev Clients=1059444855, Cross-Referrals=1513866714. Challenge sheet GIDs: Responses=888740858, Campaign Analytics=1367234528. Created 3 new tabs: Creator Tool Leads=37201560, Website Design Leads=2082055740, Automation Leads=545218649. Zero mode:name/mode:list/mode:url nodes remain across all 37 active workflows. |
| n8n crash-loop on restart (MODULE_NOT_FOUND) | FIXED 2026-03-06 (session 12) | n8n task runner subprocess looks for `/home/ec2-user/.local/bin/n8n` which was missing. Caused 5 rapid crash-restart cycles when MemoryMax=700M was hit during heavy session. Fixed: `ln -s /usr/bin/n8n ~/.local/bin/n8n`. Won't crash on next restart. |
| GitHub→Telegram Clawdbot credential stale again | FIXED 2026-03-06 (session 12) | Same recurring issue: `RlAwU3xzcX4hifgj` token stale. Re-patched via Python urllib from Mac. Bounced workflow. Pattern: patch from Mac only, never SSH. |
| Coaching-Payment-Welcome fitai nodes would block welcome flow | FIXED 2026-03-06 (session 12) | `Create Portal Account` and `Assign Starter Workout` nodes had no `onError` — fitai API failures would stop the whole welcome workflow before sending the client's SMS. Set `continueRegularOutput` on both. Portal account creation is nice-to-have, not critical path. |
| Monthly-Workflow-Backup "List All Workflows" missing API key | FIXED 2026-03-06 (session 12) | httpRequest to localhost:5678 only sent `Accept` header — no API key → 401. Created `httpHeaderAuth` credential "n8n Internal API Key" (id=3A3taZTvXAzm3ARI) and assigned to node. |
