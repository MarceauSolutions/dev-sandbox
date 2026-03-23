# Session History & Learnings

Running log of significant learnings, decisions, and patterns discovered during development sessions.

---

## 2026-03-23: AI Client Sprint — Infrastructure Overhaul & Outreach Pipeline — Session 16

**Context:** AI client acquisition sprint, Day 1. Goal: land 1 paying AI systems client before new Collier County job starts April 6. Session focused on building the full commercial infrastructure — data layer, payments, lead enrichment, outreach assets, and website conversion.

**What Was Built:**

**Data & Infrastructure:**
- **EC2 canonical `pipeline.db`** — multi-tower SQLite schema with deals, outreach_log, intake_submissions tables. Single source of truth replacing scattered CSVs and separate per-tool databases
- **8 new pipeline API endpoints** on `agent_bridge_api.py` — Clawdbot can now query pipeline status, log deal updates, pull follow-up lists without Claude Code being present
- **`pipeline.marceausolutions.com` overhauled** — replaced 3 separate dashboards (outreach-analytics 8794, client-tracker 8795, sales-pipeline 8785) with one unified multi-tower kanban

**Lead Enrichment:**
- **Hunter.io + Snov.io waterfall** — replaces Apollo enrichment (Apollo enrichment API broken/insufficient). Hunter finds emails from domain → Snov.io as fallback. 18 new valid emails found from existing prospect list
- **Segment analysis complete** — 56 Apollo leads validated and segmented by industry (HVAC, plumbing, dental, med spa, restaurant). 74 total actionable prospects with verified emails
- **Phone blitz list**: 40 HVAC leads with phone numbers at `projects/shared/lead-scraper/output/phone_blitz_2026-03-24.csv`
- **Tuesday in-person route**: 12 stops mapped at `projects/shared/lead-scraper/output/inperson_route_2026-03-25.csv`

**Payments & Conversion:**
- **Stripe $297/mo product live** — price ID `price_1TECrADeeD1eRvzzyYKnO7z5`, payment link `https://buy.stripe.com/9B66oH7tBaeI0Wk8H8g360f`
- **`marceausolutions.com/start`** — client intake form deployed, submits directly to `pipeline.marceausolutions.com/api/intake`, auto-creates deal in pipeline.db

**Demo Infrastructure:**
- **Demo line (239) 457-0662** — fully operational. TwiML voicemail greeting, text-back fires within 10 seconds, William receives Telegram alert on every call. n8n workflow "Missed Call Text-Back DEMO" (ID: `5uIyvR23VGVzX4IO`) active

**Website & Outreach Assets:**
- **`ai-automation.html` updated** — "Start Your Free 2-Week Trial →" CTA added as primary action above Calendly, links to `/start`
- **Pricing corrected** — monthly retainer updated to $500-$1,000/mo + $500-$2,000 setup (was showing $295 flat)
- **Leave-behind PDF** — pricing updated to match retainer model, reprinted for Tuesday visits

**Key Learning — Build for the System, Not the Sprint:**
Every tool built today was designed to work across all towers with minimal customization. The pipeline.db schema, the API endpoints, the intake form — all are tower-agnostic and can serve fitness, digital, and labs clients equally. Compare to Session 14 approach (dystonia digest was built just for that use case). The multi-tower architecture means adding a new business line costs hours, not days.

**Commits:**
- `session 16: website CTA, handoff update, session history, task status updates`

---

## 2026-03-22: Dystonia Research Digest Full Product Build — Session 14

**Context:** The dystonia research digest existed only as a CLI email script (`execution/dystonia_research_digest.py`) running via Mac launchd. No web frontend, no archive, no EC2 deployment, no subdomain. Built the full product.

**What Was Built:**
- **FastAPI web dashboard** at `projects/marceau-solutions/labs/dystonia-digest/` (port 8792)
  - Dashboard with stats, recent digests, top categories
  - Browse/search archived digests and papers
  - Paper detail views with PubMed/DOI links
  - Category management (add/enable/disable/delete search queries)
  - On-demand digest trigger button
  - Dark+gold branded UI matching Marceau Solutions theme
- **SQLite archive** — every digest run persisted with papers, categories, dedup tracking
- **PDF generation** via `branded_pdf_engine.py` (generic_document template)
- **EC2 deployment** — systemd service `dystonia-digest.service`, nginx proxy to `dystonia.marceausolutions.com`
- **n8n workflow** `Dystonia-Research-Digest-Daily` (`pUuUxu5s37UPkxyq`) — daily 7am ET, triggers digest, checks status, Telegram notification if papers found
- **Launch script** `scripts/dystonia-digest.sh` for local development
- **Email recipient** added: `angelamarceau2@gmail.com` alongside `wmarceau@marceausolutions.com`

**DNS Pending:** `dystonia.marceausolutions.com` A record needs to be added in Namecheap pointing to `34.193.98.97`. Then run certbot for SSL.

**Architecture Decision:**
- Core search logic stays in `execution/dystonia_research_digest.py` (shared utility, backward compatible)
- Web app imports from it via `digest_runner.py` wrapper that adds DB persistence + PDF
- n8n replaces Mac launchd as scheduler — EC2-resident, no dependency on Mac being awake

**Process Learning — New Rule E12:**
This system was originally left half-built: working email script but no frontend, no deployment, no archive. Created E12 ("Complete the deployment") to prevent this pattern of stopping at "code works locally" instead of finishing through to deployed+verified+documented.

---

## 2026-03-21: Accountability System Deployment + PDF Organization — Session 13

**Context:** Built out the complete accountability system that had been fully spec'd but never deployed (E11 violation). Also organized all generated PDFs with auto-routing.

**Accountability System — Fully Deployed:**
- **Morning-Accountability-Checkin** (`XNrR99vPCUp89X8L`): 5:00am ET Mon-Sat. Calls `execution/accountability_handler.py --type morning_briefing` via agent bridge. Includes Google Calendar events, pending tasks (from FitAI tasks.json), weekly metrics, day-specific focus.
- **EOD-Accountability-Checkin** (`0Zf8nNv1AphA0W6s`): 7pm ET Mon-Fri. Sends EOD prompt.
- **Weekly-Accountability-Report** (`krxeoSZMMPBZGAPv`): 7pm ET Sunday. Full scorecard with totals vs targets from Sheets, auto-detects win/focus areas, writes to Weekly Summary tab.
- **Reply Handler**: Clawdbot's SOUL.md updated with accountability parsing instructions. Runs `execution/accountability_handler.py --type parse --text "MESSAGE"` for pattern detection.
- **Milestone Checking**: Built into EOD handler — auto-checks cumulative outreach (500 threshold) and first meeting, marks Milestones tab.
- **Calendar Integration**: `token_marceausolutions.json` on EC2, fetches today's events for morning briefing.
- **Todo System**: Uses existing FitAI `tasks.json` as single source of truth. Telegram commands: "todo add", "tasks", "done #N", "remove #N". Clawdbot can also add tasks proactively.

**Key Architecture Decision:**
- Reply handling via Clawdbot SOUL.md + Python script (NOT n8n webhook) because Clawdbot owns the Telegram bot connection. n8n Telegram Trigger would conflict with Clawdbot's polling. n8n webhook activation via CLI/DB doesn't register webhooks properly.
- Agent bridge at localhost:5010 used by n8n to call Python scripts on EC2.

**PDF Organization System:**
- `execution/pdf_router.py`: Auto-routes PDFs by template type + keyword analysis (12+ categories)
- Hooked into `branded_pdf_engine.py` — auto-copies to organized folder on generation
- Folder structure:
  - `fitness/content/{workout-programs,nutrition-guides,education,lead-magnets,offers}`
  - `docs/medical/{dystonia,peptides,herbal-medicine,billing-disputes}`
  - `docs/business/{guides,legal,reports}`
- Moved all existing PDFs to correct locations (large files symlinked)

**Files Created/Modified:**
- `execution/accountability_handler.py` (new, 700+ lines)
- `execution/pdf_router.py` (new, 200 lines)
- `execution/branded_pdf_engine.py` (modified — auto-route hook)
- Clawdbot SOUL.md on EC2 (accountability + todo instructions appended)
- 3 n8n workflows upgraded (Morning, EOD, Weekly)
- `docs/SYSTEM-STATE.md` updated with accountability workflows
- 25+ PDFs organized into correct folder structure

**Commits (6):**
- `26b42668` feat: accountability handler script for Clawdbot Sheets logging
- `bc1fee99` feat: add milestone checking to accountability handler EOD flow
- `e1993194` docs: add accountability system workflows to SYSTEM-STATE.md
- `d72d7501` feat: add calendar, todo list, and morning briefing to accountability system
- `cf272d48` feat: PDF routing system + organized content folder structure

---

## 2026-03-06: Company on a Laptop — Session 12 (Diagnostic Hardening + False Positive Elimination)

**Context:** Comprehensive diagnostic + hardening pass after session 11. Root cause analysis on recurring Telegram cred staleness, n8n crash-loop, and health_check.py false positives.

**Fixed:**
- **n8n crash-loop**: Task runner subprocess hardcodes `/home/ec2-user/.local/bin/n8n` path. After MemoryMax=700M SIGTERM, symlink was missing → crash-loop on restart. Fix: `ln -s /usr/bin/n8n ~/.local/bin/n8n` on EC2.
- **GitHub→Telegram stale cred**: `RlAwU3xzcX4hifgj` credential had wrong token (recurring issue). Re-patched via Python urllib PATCH to n8n REST API + bounced workflow. Shell/SSH corrupts token — must patch from Mac via Python urllib.
- **Coaching-Payment-Welcome fitai nodes**: Set `continueRegularOutput=true` — fitai.marceausolutions.com call failures no longer block the main flow.
- **Monthly-Workflow-Backup**: Was missing n8n Internal API Key cred → 401 on first step. Created `n8n Internal API Key` credential (id `3A3taZTvXAzm3ARI`).
- **health_check.py false positives**: "11 workflow errors" included pre-fix historical errors. Rewrote to check latest execution per erroring workflow, exclude inactive workflows, classify as "actively failing" (<6h) vs "stale failure" (>6h, not yet re-verified).

**Added to health_check.py:**
- Telegram bot token validation: `api.telegram.org/bot{token}/getMe` + check latest GitHub→Telegram execution status
- `--repatch-telegram` CLI flag: patches cred + bounces workflow in one command
- n8n restart threshold raised: warn ≤6 (was ≤3), fail >6

**Verified:**
- health_check.py: 0 false positives, "No active workflow failures" ✓
- Telegram monitoring: catches stale cred before it causes silent alert failures

**Key Learnings:**
39. **n8n task runner hardcodes binary path** — after MemoryMax SIGTERM or manual kill, symlink at `~/.local/bin/n8n` must exist or n8n crash-loops on restart. Check this before every n8n restart.
40. **SSH shell corrupts Telegram token patches** — only patch n8n credentials via Python urllib from Mac. Never copy/paste via SSH shell (token gets truncated or modified).
41. **health_check error counts are misleading** — n8n stores ALL historical errors; counting errors in 24h window includes pre-fix errors. Always check latest execution status per workflow for accurate failure state.
42. **Stale Telegram cred is recurring** — n8n Telegram credential `RlAwU3xzcX4hifgj` needs re-patching after heavy session work (rapid workflow bounces trigger token refresh). health_check.py now monitors this automatically.

---

## 2026-03-06: Company on a Laptop — Session 11 (Zero mode:list — All Sheets Nodes Hardened)

**Context:** Completing mode:list → mode:id conversion started in session 10. All Google Sheets nodes across all workflows now use deterministic numeric GIDs.

**Fixed:**
- Converted all 13 remaining `mode:list` Google Sheets nodes across 12 workflows to `mode:id` with verified numeric GIDs. Same runtime-lookup risk as `mode:name` — now eliminated.
- Created 3 missing tabs on Challenge sheet that workflows were writing to but didn't exist: Creator Tool Leads (gid=37201560), Website Design Leads (gid=2082055740), Automation Leads (gid=545218649).
- Extracted bare doc IDs from workflows storing full Google Sheets URLs (with `/edit` suffix) as documentId — URLs cause HTTP 404 from Sheets API, bare IDs work.
- Refreshed expired OAuth token for Sheets API access.
- Bounced all 12 updated workflows via n8n REST API (deactivate → activate).

**Verified:**
- Zero `mode:name`, `mode:list`, or `mode:url` nodes remain across all 37 active workflows (scanned via n8n API).

**Key Learnings:**
36. **mode:list is the same risk as mode:name** — both do runtime Sheets API lookups that can fail under load or when token is stale. The fix is always mode:id with a verified numeric GID.
37. **Workflows often store full Google Sheets URLs as documentId** — strip everything before and after the 44-char ID (`/spreadsheets/d/{id}/edit`). The Sheets API returns 404 if you pass the full URL.
38. **Missing tabs don't error loudly** — if a workflow's target sheet tab doesn't exist, Sheets API returns an error but n8n may not surface it clearly. Always verify tabs exist before converting to mode:id.

## 2026-03-06: Company on a Laptop — Session 9 (Gap Sweep + Silent Error Elimination)

**Context:** Continued iteration — gap scanning after session 8 hardening.

**Built:**
- `check_ai_apis()` in health_check.py — live Anthropic key validation (GET /v1/models, zero token cost) and ElevenLabs character quota check with warn (<80%) / fail (>95%) thresholds.
- Revenue report "Top Clients by Revenue" section — top 5 by `total_charged` using existing `by_customer` dict.
- Twilio balance check added to health_check.py (warn <$10, fail <$5, SSL/CERT_NONE for Mac Python 3.14).

**Fixed:**
- `daily_standup.sh` morning digest command — `python -m projects.shared.personal-assistant.src.morning_digest` fails (dashes in path not valid Python module). Fixed to subshell.
- X-Batch-Image-Generator deactivated — xAI API key returning 403 from EC2 on ALL endpoints (key invalid/expired). Was silently firing Self-Annealing handler 3x/day. To fix: renew key at console.x.ai, then re-activate.
- Workflow count corrected: 37 active (38 - 1 deactivated), 5 inactive.

**Verified healthy:**
- n8n-Health-Check: covers 20 critical workflows, runs 6 AM ET daily
- GitHub→Telegram: 3+ consecutive successes (fix from session 8 holding)
- Daily-Operations-Digest: no errors, pruning successfully (schedule 0 0 13 * * * = 8 AM ET)
- All 35/37 active wireable workflows have Self-Annealing error handler (100% coverage)
- Webdev-Monthly-Checkin: reads from correct tracker sheet, sends SMS 1st of month at 10 AM UTC

**Key Learnings:**
33. **xAI API key validation is not key-existence** — the key existed in `.env` and passed the key-only check, but was returning 403 on ALL xAI endpoints from EC2. The only way to detect this is a live API call. Added to check_api_balances.py pattern for future.
34. **SQLite WAL mode blocks external reads on EC2** — n8n database in WAL mode; sqlite3 from ec2-user returns no output when n8n has the file locked. Use the n8n API or event logs for execution debugging, not direct SQLite queries.
35. **Daily error storm pattern** — a scheduled workflow erroring silently fires Self-Annealing handler repeatedly. Always deactivate broken scheduled workflows rather than leaving them running; this prevents alert fatigue and noise in the error handler executions.

## 2026-03-06: Company on a Laptop — Session 8 (Renewal Tracking + Monitoring Hardening)

**Context:** Continued "company on a laptop" iteration — coverage gap analysis post-session-7b.

**Built:**
- `Stripe-Invoice-Paid` workflow (`unF3M3IfnGPqV0xU`) — fires on subscription renewals only (`billing_reason === 'subscription_cycle'`). Logs to PT Tracker "Billing" tab (columns: Date, Client_Name, Amount, Status=Renewal, Stripe_Payment_ID) + Telegram alert. Self-Annealing wired at creation.
- Stripe webhook `we_1T862eDeeD1eRvzzdYkDJUzb` registered for `invoice.paid`.
- `check_stripe_webhooks()` in health_check.py — verifies all 6 Stripe webhooks are registered + enabled in Stripe. Runs on every full health check.
- Added `www.boabfit.com` to `check_domains()` in health_check.py.
- Added `Stripe-Payment-Failed` + `Stripe-Invoice-Paid` to `key_workflows` in health_check.py.

**Fixed:**
- SYSTEM-STATE.md workflow count updated: 36→38 active, Self-Annealing wiring 34/36→36/38 (100% of wireable).

**Key Learnings:**
28. **Billing sheet column alignment matters** — checked existing `Coaching-Payment-Welcome` "Log Billing" node to get correct column names (Date, Client_Name, Amount, Status, Stripe_Payment_ID) before building invoice.paid workflow. Prevents silently mismatched columns.
29. **Stripe `invoice.paid` fires on ALL invoices**, including initial subscription creation. Filter by `billing_reason === 'subscription_cycle'` to target renewals only. Initial payments are already handled by `checkout.session.completed`.
30. **Stripe webhook health belongs in daily check** — added Stripe API call to health_check.py to verify all 6 expected webhooks are registered and enabled. Without this, a deleted webhook would cause silent revenue loss.
31. **n8n Telegram credential re-patch: always use Python urllib from Mac** — SSH shell variable interpolation can corrupt the token. `$TOKEN` in remote SSH commands may be interpreted differently. Use `python3 -c "from dotenv ... urllib.request.Request(..., method='PATCH')"` directly from Mac. SSH-based patch caused 404 (malformed URL) while Python-based patch works correctly.
32. **Automated payment failure loop**: When Stripe fires `invoice.payment_failed`, look up client phone in PT Tracker → SMS client to update payment method + Telegram to William. Never just alert William manually — automate the client-facing response too.

## 2026-03-06: Company on a Laptop — Session 7b (Stripe Payment Failure Coverage)

**Context:** "I don't care if there's no clients yet — the point is to be ready for clients." Built invoice.payment_failed handler.

**Built:**
- `Stripe-Payment-Failed` workflow (`QMWkhAb8SWMSImc4`) — webhook → extract customer/amount/reason → Telegram alert to William
- Stripe webhook `we_1T85t0DeeD1eRvzzjpNKpvGA` registered for `invoice.payment_failed`
- Wired to Self-Annealing error handler. Now **5 Stripe webhooks** total.

**Key Learning:**
27. **Build for client-readiness, not current state** — "No clients yet" is not a reason to skip critical business logic. Build the full funnel now.

## 2026-03-06: Company on a Laptop — Session 7 (Post-Fix Audit + Health Check Hardening)

**Context:** Seventh pass — verified session 6 commits, diagnosed post-fix workflow errors, hardened health_check.py.

**Critical fixes:**
- **GitHub→Telegram**: 5 errors on every push — "Clawdbot Telegram" n8n cred `RlAwU3xzcX4hifgj` had stale token. Re-PATCHED via n8n API. Token valid per Telegram API.
- **health_check.py**: Added n8n restart counter (>3 restarts/24h = fail) + external domain health (n8n.marceausolutions.com, api, fitai — all 200 OK).

**Root cause analysis of 10 pre-fix errors:**
- All "empty execution data" errors are in `execution_data` table (separate from `execution_entity`). n8n serialized format (array with int refs) — look for string elements for error messages.
- X-Batch: `Cannot read properties of undefined (reading 'disabled')` — pre-crash (16:00 < 17:42 restart). Auto-fixed by n8n reload from DB.
- Challenge-Day7-Upsell: `Could not get parameter` from broken sheetName mode. Pre-fix (13:00 < 20:20 patch).
- Webdev-Monthly-Checkin: `Credential 'RIFdaHtNYdTpFnlu' does not exist` — pre-fix (15:00 < 20:20 patch). Fix confirmed: nodes now reference `mywn8S0xjRx9YM9K`.
- Nurture-Sequence-7Day: `No recipients defined` — test trigger with missing payload. Expected behavior.
- "Could not find property option": n8n telemetry noise on workflow saves. Harmless.
- n8n crash at 17:42 UTC: SIGTERM from our manual restart during session 4. Loaded all SQLite fixes from DB on restart.

**Verified state:**
- Google OAuth auto-refresh working, all 3 launchd jobs loaded, all 3 external domains 200 OK
- Revenue tracking correct: `stripe.Charge.list()` captures both initial + recurring charges — no gap
- `invoice.payment_failed` unhandled — documented as future work (0 clients currently)

**Key Learnings:**
21. **n8n execution data is in `execution_data` table**, not `execution_entity`. JSON array with int-keyed refs. Find strings for actual error messages.
22. **n8n re-reads from DB on restart** — SQLite patches auto-apply after full service restart. No manual bounce needed post-restart.
23. **"Could not find property option"** in n8n logs = telemetry noise on workflow saves. Not execution failures. Ignore.
24. **Telegram bot token in n8n is encrypted** — use n8n credential PATCH API to update. Verify via `curl .../getMe` before patching.
25. **Self-Annealing wiring in `settings` JSON** — `json_set(settings, '$.errorWorkflow', 'WORKFLOW_ID')` to wire. No workflow_history update needed (settings ≠ nodes). Bounce to apply.
26. **flamesofpassionentertainment.com domain blocked** — still on Google Cloud DNS (pre-transfer). No A records. GitHub Pages site live at `marceausolutions.github.io/flames-of-passion-website`. Client/William must add A records (185.199.108-111.153) to unblock.

## 2026-03-06: Company on a Laptop — Session 6 (External Integration Audit)

**Context:** Sixth pass — audited all external integrations (Stripe, Twilio, domains).

**Critical fixes:**
- **Stripe**: deleted stale legacy endpoint (`webhooks.marceausolutions.com` → 404). Added missing `stripe-webdev-payment` webhook (was absent — webdev client payments never triggered onboarding). All 4 Stripe webhooks now active and pointing to n8n.
- **Twilio**: local PT number (+12398803365) and HVAC client number (+12397666129) had empty SMS webhooks — inbound texts were silently dropped. Set both to `sms-response` handler.
- **Voice webhooks**: verified `api.marceausolutions.com/twilio/voice` returns 200 on POST.
- Added "External Integrations" section to SYSTEM-STATE.md with full verified state.

**Key Learnings:**
19. **Always audit Stripe webhooks against n8n webhook paths** — easy to have n8n handler with no Stripe registration (or vice versa). Check: `stripe.com/webhook_endpoints` vs n8n `webhook_entity` table.
20. **Twilio numbers can have empty SMS webhooks** — inbound texts silently dropped, no error. Check all numbers via Twilio API, not just the one you know you're using.

## 2026-03-06: Company on a Laptop — Session 5 (Final Verification)

**Context:** Fifth pass — verified all session 4 fixes held, closed remaining minor gaps.

**Accomplished:**
- GitHub→Telegram confirmed working post session 4 push (20:33 UTC success)
- Revenue report email verified end-to-end (sends to wmarceau@marceausolutions.com)
- Clawdbot weekly restart cron confirmed active (Sun 3am UTC via /etc/cron.d)
- n8n.marceausolutions.com confirmed accessible (HTTP 200) — all Stripe/GitHub webhooks reach n8n
- Webhook registry audit: 27 registered, 1 orphan deleted (workflow 1s52PkA1lY1lHfGP was deleted without webhook cleanup)
- fitai (8001) and voice-api (8000) both healthy
- Nurture-Sequence-7Day: 15:03 UTC error confirmed as test call, not structural — Lead-Magnet-Capture data mapping correct
- n8n-Health-Check verified: SMS + Telegram credentials wired, monitors 10 critical workflows
- Fresh n8n backup committed (40 workflows, post all session 4+5 changes)

**Key Learnings:**
16. **n8n orphan webhook cleanup**: after deleting workflows, run `DELETE FROM webhook_entity WHERE workflowId NOT IN (SELECT id FROM workflow_entity)` to remove stale registrations
17. **voice-api (port 8000)** responds to `GET /` (JSON status), not `/health` — 404 on /health is normal
18. **health_check.py double output with `2>&1`** is a display artifact of exit code 1 in Bash tool, not a real bug

## 2026-03-06: Company on a Laptop — Session 4 (Autonomous Monitoring + Cron Root Fix)

**Context:** Fourth pass — closed the remaining gaps after session 3: autonomous Mac monitoring, in-memory vs DB SQLite fix bug, cron format issues.

**Accomplished:**
- Added 2 Mac launchd jobs: daily health check (7am) + weekly revenue report email (Mon 9am)
- Discovered n8n reads `workflow_history` (not `workflow_entity`) on activation — session 3 SQLite fixes only updated entity, not history. Daily-Operations-Digest couldn't activate for this reason.
- Fixed `workflow_history.nodes` for Daily-Ops corrupted cron version — now activates clean
- Found and fixed 6 workflows with 5-field cron (scheduleTrigger v1.2 requires 6-field with seconds): X-Batch, X-Social-Scheduler (×2), PT-Monday-Checkin, Challenge-Day7, Monthly-Backup
- Found and fixed `triggerAtMonth:1` bug in Webdev-Monthly-Checkin — was only running in January, not monthly
- Bounced all 8 SQLite-patched workflows (deactivate→activate via API) to reload from DB
- Verified X-Batch "Cannot read properties of undefined" was in-memory stale state, now resolved
- All 36 active workflows verified active via API

**Key Learnings:**
13. **n8n SQLite fix rule**: After any SQLite node patch, ALSO update `workflow_history.nodes` for the row matching `workflow_entity.versionId`. Then bounce (deactivate→activate) via API to reload. Failing either step leaves workflows broken.
14. **n8n scheduleTrigger cron format**: `typeVersion 1.2` with `field: "cronExpression"` requires 6-field cron (sec min hour dom month dow). Standard 5-field (without seconds) silently fails with "Invalid cron expression" at activation time.
15. **n8n `triggerAtMonth`**: Setting `triggerAtMonth: N` in schedule interval limits the workflow to that specific month. Omit entirely for "every month" behavior.

## 2026-03-06: Company on a Laptop — Final Deep Audit (Session 3)

**Context:** Third "make it better" pass — exhaustive audit of every active workflow, credential, cron, and error handler.

**Accomplished:**
- Deleted 9 dead inactive workflows (49→40 total) — old orchestrators, Naples RE, WhatsApp, MyAIagent, etc.
- Deactivated Hot-Lead-to-ClickUp (ClickUp not in stack)
- Deep credential scan: fixed Follow-Up-Sequence-Engine (4 creds), Resume-Builder email, Daily-Ops-Digest (4 creds)
- Cron corruption scan: found and fixed Daily-Operations-Digest (was NEVER running — ls-injection bug + no credentials)
- Wired 21 more workflows to Self-Annealing error handler (now 27/35 covered)
- Added Telegram alert to health_check.py — fires when critical failures detected
- Gitignored provider-status.json (runtime file was causing spurious "uncommitted" warnings)
- Cleaned EC2: old SQLite backups (34MB), /tmp/jiti (15MB), inject scripts, journal vacuum (179MB)
- GitHub→Telegram verified working end-to-end on 2 consecutive pushes
- SYSTEM-STATE.md fully updated with all fixes, correct counts, new items

**Key Learnings:**
9. Cron corruption pattern (`ls` injection) can silently affect multiple workflows — always scan ALL schedule nodes after any cron edit.
10. "Active" in n8n ≠ "working" — a workflow can be active with no credentials, broken connections, or corrupt crons, and never error until triggered.
11. The `errorWorkflow` setting is in the `settings` JSON column in SQLite `workflow_entity`, not in `nodes`. Set to error handler workflow ID.
12. Clawdbot `model` field — NOT configurable via `clawdbot.json` (top-level key is invalid per schema). Model determined by auth profile.

## 2026-03-06: Company on a Laptop — Continued Tightening (Iterations 2-N)

**Context:** Continued from full system optimization. Each iteration asked "make it better" — closed remaining operational gaps.

### What Shipped (Iterations 2-N)
- **`scripts/backup-n8n.py`** — new tool replacing stale `backup-n8n-workflows.sh`. API-based export of all 49 workflows to dated JSON. `--list` flag for inventory. `--commit` flag auto-commits + pushes. First backup: `2026-03-06.json`.
- **Weekly launchd job** — `com.marceausolutions.backup-n8n` (Sun 4am) runs `backup-n8n.py --commit`. Backup → commit → push, fully automatic.
- **`health_check.py` git section** — now reports both uncommitted files AND unpushed commits. "Git: clean, fully pushed" is the zero-noise success state.
- **`SYSTEM-STATE.md` workflow inventory** — expanded from 7 documented workflows to all 37 active in 7 categories (Infra, PT, Lead Gen, Nurture, Web Dev, Content, Other).
- **`health_check.py` key_workflows** — expanded from 8 to 13 monitored workflows (added PT Cancellation, Fitness SMS Outreach, WebDev Payment Welcome, WebDev Monthly Checkin, Lead Magnet Capture).
- **`daily_standup.sh` → 5 sections** — added `[4/5] API BALANCES` using existing `check_api_balances.py`. Now shows ElevenLabs chars remaining, API key validity every morning.
- **`backup-n8n-workflows.sh`** — deleted. Stale hardcoded IDs. Replaced completely.
- **`scripts/health-check.py`** — deleted. Old URL checker, superseded by `health_check.py`.
- **`SYSTEM-STATE.md` open items** — n8n backup resolved (was "NEVER", updated to reflect weekly schedule).

### Key Learnings
7. **backup --commit without --push = unpushed commit buildup** — the launchd job runs weekly and the health check would warn "N unpushed commits" every morning. Always close the loop: commit AND push in the same automated job.
8. **Orphaned tools drift** — `check_api_balances.py` and `backup-n8n-workflows.sh` were both "existing tools" that weren't wired into anything. The former got integrated (standup), the latter got deleted. If a tool isn't called from somewhere, it doesn't exist operationally.

---

## 2026-03-06: Company on a Laptop — Full System Optimization

**Context:** Multi-session deep fix. Started with Clawdbot not responding on Telegram (85% context buildup), escalated to full infrastructure audit and optimization pass.

### Fixes Applied
- **Clawdbot 85% context**: cleared by renaming JSONL + resetting sessions.json. Added weekly Sunday 3am UTC restart cron + `OnFailure` crash alert to Telegram.
- **stripe-webhook.service**: stopped after 518,821 crash loops since Feb 14. Root cause: port conflict with webhook_server.py on 5002. n8n handles Stripe natively — service was redundant.
- **PT Monday Check-in (aBxCj48nGQVLRRnq)**: corrupted cron had `ls` output in it. Fixed to `0 14 * * 1` (Mon 9am ET). Now active.
- **Self-Annealing Error Handler (Ob7kiVvCnmDHAfNW)**: was blocked from activation by Switch node typeVersion 3 incompatibility with n8n 2.4.8. Fixed by downgrading to typeVersion 1. Now active.
- **SMS STOP compliance**: added STOPALL + END to SMS-Response-Handler-v2 (was: 4 keywords, now: all 6 required by CTIA/A2P).
- **HVAC + Square Foot form integrations**: Google Sheet IDs wired into `execution/form_handler/business_config.py`. Form submissions now land correctly.
- **journald**: vacuumed 2.4GB, capped at 500MB permanently.
- **n8n memory**: added MemoryMax=700M/MemoryHigh=600M to n8n.service.

### Infrastructure Built
- `scripts/health_check.py`: one-command full system status (EC2 services, disk/memory, all 7 key n8n workflows, Clawdbot context%, .env keys, business links)
- `scripts/daily_standup.sh`: morning routine — health check + digest preview + quick links
- `docs/SYSTEM-STATE.md`: live source of truth for EC2, workflows, SMS compliance, known issues

### Docs Cleanup
- Moved SOPs 25-29 from `docs/` root → `docs/sops/` (all 33 SOPs now in one place)
- Archived 54 stale docs → `docs/archive/legacy-docs-2026/`
- Added CLAUDE.md hubs for 11 projects that were missing them
- Removed: ghost projects (hub/, portfolio/, 5x product-ideas), broken symlinks

### Key Learnings
1. **n8n Switch node v3 incompatibility** — n8n 2.4.8 can't activate workflows with Switch typeVersion 3 using the `outputKey`/conditions block format. Fix: downgrade to typeVersion 1 (simple `dataType: string, value1, rules` format).
2. **systemd StartLimitIntervalSec** must go in `[Unit]` section, not `[Service]`. Putting it in `[Service]` silently does nothing.
3. **n8n API key** — now in `.env` as `N8N_API_KEY`. Don't hardcode. Fallback: `sqlite3 ~/.n8n/database.sqlite 'SELECT apiKey FROM user_api_keys LIMIT 1;'`
4. **Clawdbot session recovery**: stop service → rename `.jsonl` → reset sessions.json to keep only `systemSent` + `skillsSnapshot` → restart.
5. **cron expression corruption** — PT Monday Check-in had shell `ls` output injected into the cron field. Always verify workflow node parameters after bulk edits.
6. **Never call a tracking function inside the summary that reads from the same list** — `fail()` appends to `FAILURES[]`; calling it in the "N failures" summary line would corrupt the count.

### Polish Pass (same session — iterations 2-3)
- **`health_check.py`**: exit code 1 on any failure, FAILURES[] list, execution recency check replacing static URL dump, FAILURES bug fixed in summary
- **`.gitignore`**: OAuth tokens, `*-export.json` lead data, `assets/*.pdf/png`, `personal-assistant/output/` all now ignored — git status is clean
- **Clawdbot SOUL.md** (EC2): `Last Updated` date, script/SOP counts, Active Projects refreshed from parcelLab/BCI → current state (PT coaching, 4 web dev clients)
- **MEMORY.md Decision Log**: 4 new 2026-03-06 entries, 4 oldest dropped (rolling window of 10)

---

## 2026-02-16: GitHub Profile Cleanup + Job Application Blitz (11 Tailored Resumes)

**Context:** William pivoting to job search. Cleaned up GitHub profile for employer visibility, then tailored 11 resume+cover letter packages for specific job postings.

### GitHub Profile Changes (All Live)
- Created **profile README** at `github.com/wmarceau/wmarceau` — professional summary, featured projects, tech stack
- **Archived junk repos:** NewProject, git_practice, excursion-project, AIFitnessWebsite, awesome-mcp-servers (fork)
- **Made Focal-Dystonia- public** — EEG/ML project, fixed description (was "electromyography", corrected to "electroencephalography")
- **Added topics/tags** to all 6 showcase repos (amazon-seller-mcp, Focal-Dystonia-, fitness-influencer-mcp, md-to-pdf-mcp, rideshare-comparison-mcp, hvac-quotes-mcp)
- **Transferred squarefoot-shipping-website** to MarceauSolutions org (keeps Pages live, removes from personal profile)
- **Archived flames-of-passion-website** from personal (org copy still serves GitHub Pages)
- **Pending:** Profile bio/location/hireable + pinned repos need `gh auth refresh -h github.com -s user` (requires browser auth)

### Resumes + Cover Letters Created (all in `projects/shared/resume/output/`)

| # | Company | Role | Match Quality | Files |
|---|---------|------|---------------|-------|
| 1 | Trend Capital Holdings | AI & Automation Specialist | Strong — Naples hybrid, n8n+Zapier+LLM | `*_trend_capital_*` |
| 2 | symplistic.ai | Jr. AI Software Engineer | Strong — Bonita Springs, agentic AI, FGCU alum | `*_symplistic_*` |
| 3 | Garver | AI Development Specialist | Strong — remote, MCP in requirements | `*_garver_ai_*` |
| 4 | Garver | Scheduler I | **Skipped** — construction scheduling, no match | — |
| 5 | Vista Equity Partners | AI-First Orchestration Engineer | **Best match** — n8n, RAG, ChromaDB, Mem0, $90-170K | `*_vista_*` |
| 6 | Piper Companies | AI Automation Engineer | Reach — needs RPA/Fabric, but life sciences angle | `*_piper_*` |
| 7 | Talently | AI Solutions Engineer | Strong — "build vs tool", end-to-end ownership | `*_talently_*` |
| 8 | PharmaForce | Jr. AI Engineer | Strong — Claude Code, agentic systems, healthcare | `*_pharmaforce_*` |
| 9 | Kyo | Integration Engineer | Strong — MCP, Florida resident, FGCU alum | `*_kyo_*` |
| 10 | Oracle | AI Engineer | Good — RAG, monetizable AI, governance | `*_oracle_*` |
| 11 | Abacus.AI | Technical Demo Engineer | Strong — 3yr teaching + AI agent builder | `*_abacus_*` |
| 12 | Convergent | AI Automation Intern | **Skipped** — intern, $1.6K/mo, overqualified | — |
| 13 | Insight Global | AI Engineer | Moderate — LangGraph gap, but RAG transferable | `*_insight_global_*` |
| 14 | Tria Federal | Jr. AI Engineer | Strong — MCP in description, U.S. citizen, FGCU alum | `*_tria_federal_*` |
| 15 | Peraton | GenAI Intern (Graduate) | **Skipped** — requires current Master's/PhD enrollment | — |
| 16 | Healthcasts | AI Engineer | Reach — needs PyTorch/NLP, but healthcare angle | `*_healthcasts_*` |

### Key Patterns
- **Strongest differentiators:** MCP experience (rare), n8n production workflows (73+), biomedical/healthcare background, FGCU alumni network
- **Most common gaps:** LangGraph/LangChain (uses MCP instead), Azure (uses AWS), enterprise RPA tools
- **Best comp opportunities:** Vista ($90-170K), Piper ($190-225K), Abacus ($150K+$30K), Talently ($130-155K)
- **FGCU connections found at:** symplistic.ai, Kyo, Oracle, Insight Global, Tria Federal

---

## 2026-02-15/16: Agent Infrastructure Upgrade — Mem0, Task Classifier, PR Reviews, Ralph v2 PRD

**Context:** Major agent tooling upgrade across all three agents (Claude Code, Clawdbot, Ralph). Implemented cutting-edge AI dev tools after deep research.

### What Was Built

1. **Mem0 Shared Memory** (EC2:5020) — Cross-agent memory via REST API
   - ChromaDB + HuggingFace embeddings + Anthropic Haiku LLM
   - Fixed Mem0's temperature+top_p bug with `_get_common_params` monkey-patch
   - Systemd service: `mem0-api.service`, client library: `execution/mem0_client.py`

2. **Haiku Task Classifier** (`execution/task_classifier.py`) — Auto-routes tasks
   - 0-4 → Clawdbot, 5-7 → Agent Team/Claude Code, 8-10 → Ralph
   - ~$0.001/classification, tested with 3 sample tasks

3. **Qodo Merge PR-Agent** (`.github/workflows/pr-agent.yml`) — Automated PR reviews
   - Uses Claude Sonnet via Anthropic key (set as GitHub secret)
   - Auto-describe, auto-review, auto-improve on every PR

4. **AI Monitoring** (`execution/ai_monitoring.py`) — Langfuse + Helicone
   - Langfuse keys configured in `.env` (cloud.langfuse.com, org: Marceausolutions)
   - Helicone key configured in `.env`

5. **Ralph v2 PRD** (`ralph/RALPH-V2-PRD.md`) — 897 lines, 36 stories, 4 phases
   - Rebuild on Claude Agent SDK, Mem0 integration, self-healing, queue management

6. **Agent Teams** enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

7. **Handoff System** (`.claude/commands/handoff.md`) — `/handoff` slash command

### Previous Session (same chain)
- Context7 MCP added to `~/.claude.json`
- n8n GitHub Push → Telegram notification workflow (ID: `BsoplLFe1brLCBof`)
- Telegram MCP configured with API credentials
- Coaching tracker Google Sheet created

### What's Next
- Sign up for Helicone dashboard (key already in .env, explore the UI)
- Start Ralph v2 Phase 1 implementation (Claude Agent SDK core loop)
- Create first PR to test Qodo Merge auto-review
- Explore Langfuse dashboard — traces should appear when monitoring is used

---

## 2026-02-04: Fitness Influencer Content Pipeline + Social Media Automation + EC2 Sync

**Context:** Extended fitness influencer project with peptide video production workflow, enhanced social media automation with peptide content generator, updated n8n EC2 documentation, and synced all progress to GitHub.

### Fitness Influencer Content Pipeline

**Created `projects/marceau-solutions/fitness-influencer/content/Peptide-Video/`**:
- Full post-production checklist for peptide education videos
- B-roll asset organization (Shorts-footage, B-roll folders)
- Production workflow documentation

**Video Editing Enhancements:**
- Updated `execution/video_jumpcut.py` with improved silence detection
- Better handling of audio threshold calibration

### Peptide Content Generator

**Created `projects/shared/social-media-automation/src/peptide_content_generator.py`**:
- Specialized content generator for fitness/peptide education
- Integrates with existing social media automation infrastructure
- Template-driven approach via `templates/fitness-peptide-content.json`

**Updated `config/businesses.json`:**
- Extended configuration for peptide-focused content campaigns
- Added scheduling and targeting parameters

### n8n EC2 Documentation Updates

**Updated `docs/EC2-N8N-SETUP.md`**:
- Clarified that EC2 instance is the ONLY n8n environment
- Added Grok Imagine B-Roll Generator workflow (ID: sYvUyTooDcHQQuKN)
- Updated workflow table with complete list

**n8n Workflow Backup:**
- Created `projects/shared/n8n-workflows/` for local backup of EC2 workflows
- Enables version control and disaster recovery

### New Utilities

**Created `execution/grok_video_gen.py`**:
- Video generation utility using Grok/XAI API
- Supports b-roll and promotional video generation

**Created `projects/shared/personal-assistant/src/ideas_queue.py`**:
- Idea queue management from Telegram/Clawdbot
- Integration with personal assistant digest system

### Amazon Seller Updates

**New folders added:**
- `projects/marceau-solutions/amazon-seller/BJKPaperTrail/` - Business documentation
- `projects/marceau-solutions/amazon-seller/LegalAgreement/` - Contract templates
- `projects/marceau-solutions/amazon-seller/scripts/` - Automation scripts

### Files Updated/Created

- `CLAUDE.md` - Documentation consistency updates
- `.claude/KNOWLEDGE_BASE.md` - Added peptide content and video production knowledge
- `KANBAN.md` - Updated task tracking
- `docs/EC2-N8N-SETUP.md` - EC2-only clarification + new workflow
- `execution/video_jumpcut.py` - Improved silence detection
- `execution/grok_video_gen.py` - NEW: Video generation utility
- `projects/marceau-solutions/fitness-influencer/content/` - NEW: Production assets
- `projects/marceau-solutions/fitness-influencer/src/` - NEW: Project source
- `projects/shared/social-media-automation/src/peptide_content_generator.py` - NEW
- `projects/shared/n8n-workflows/` - NEW: EC2 workflow backups

### EC2 Integration Notes

- All n8n workflows run on EC2 at http://34.193.98.97:5678
- Claude Code MCP configured to connect to EC2 (not local)
- Workflow backups stored locally for version control

---

## 2026-02-02: Upwork Workspace Setup + Proposal System

**Context:** Created separate Upwork workspace for freelance client work, built proposal generation system, applied to first jobs.

### Upwork Workspace Created

**Location:** `~/upwork-projects/` (separate from dev-sandbox)

**Why separate:**
- Client code isolation (NDAs, ownership)
- Parallel Claude instances without conflict
- Clean handoffs to clients
- Different CLAUDE.md (minimal, client-focused)

**Structure:**
```
~/upwork-projects/
├── CLAUDE.md              # Lightweight Upwork-specific instructions
├── SESSION-STATUS.md      # Pipeline tracking
├── clients/               # One folder per client
└── templates/             # Reusable proposal tools
```

### Proposal Generation System

**Created `generate_proposal.py`** - Generates PDF proposals matching dark minimalist Canva template style with:
- Cover page (title, subtitle, prepared for)
- Content page (description, timeline, cost, mockup preview)
- Embedded spreadsheet/dashboard mockup image

**Workflow:** Job posting → Cover letter (md + pdf) → Visual proposal (pdf) → Submit

### Jobs Applied

| Job | Rate | Status |
|-----|------|--------|
| K-12 Facilities Database | $112.50/hr | Submitted (boosted, $12-16k potential) |
| Marketing ROI Tracker | $53.50/hr | Proposal ready, waiting for connects |

### Rate Calculation Strategy

- Don't use round numbers (looks calculated)
- Position 40-60% into client's budget range
- $53.50/hr for $45-75 range (28% in)
- $112.50/hr for $95-135 range (44% in)

### Key Learnings

1. **Hourly vs Fixed:** Client chooses when posting. Can propose milestone structure in cover letter even for hourly jobs.
2. **Boost ROI:** For high-value jobs ($10k+), spending 43 connects (~$6) is worth it.
3. **Connects:** 10 free/month, replies are free after initial proposal.
4. **Skip signals:** Low budget + big scope, "partner" language with employee pay, impossible tech requirements.

### Files Updated

- `~/dev-sandbox/CLAUDE.md` - Added upwork-projects to Home Directory Organization
- `~/upwork-projects/` - New workspace with templates and client folders

---

## 2026-02-02: n8n Completion + Clawdbot Telegram Reconnection + Credential Consolidation

**Context:** Completed n8n setup on EC2, reconnected Clawdbot to Telegram, consolidated Google Cloud credentials, and documented the three-agent architecture.

### n8n Setup Completed

**Accomplished:**
- ✅ Fixed n8n port 5678 access (firewalld was blocking, not just security group)
- ✅ Set `N8N_SECURE_COOKIE=false` for HTTP access
- ✅ Created DNS record: `n8n.marceausolutions.com` → `34.193.98.97`
- ✅ All 7 workflows imported and ready for activation

**Fix for port 5678:**
```bash
# AWS Security Group was open, but EC2 firewalld was blocking
ssh ec2 "sudo firewall-cmd --permanent --add-port=5678/tcp && sudo firewall-cmd --reload"
```

**n8n UI now accessible at:** http://n8n.marceausolutions.com:5678

### Clawdbot Telegram Reconnection

**Problem:** Clawdbot was running but Telegram showed `401 Unauthorized` errors.

**Root Cause:** Old/invalid Telegram bot token in `/home/clawdbot/.clawdbot/clawdbot.json`

**Solution:**
1. Created new Telegram bot via @BotFather
2. Updated token in clawdbot.json:
   ```bash
   ssh ec2 "sudo sed -i 's|OLD_TOKEN|NEW_TOKEN|g' /home/clawdbot/.clawdbot/clawdbot.json"
   ssh ec2 "sudo systemctl restart clawdbot"
   ```
3. Clawdbot now connected to `@W_marceaubot`

**Key Learning:** Clawdbot config is in JSON (`clawdbot.json`), not the `.env` file. The .env only has API keys (Twilio, OpenAI, Google), not channel configs.

### Google Cloud Credential Consolidation

**Problem:** Multiple OAuth clients across multiple projects causing credential sprawl.

**Projects Found:**
- fitness-influencer-assistant (KEEP - unified project)
- n8nAIAgent (deactivated)
- N8nContactForm (deactivated)
- YouTubecreator MCP (deactivated)
- CalendarLink (deactivated)
- My First Project (deactivated)

**Solution:**
- Deactivated API keys in all unused projects
- Use "Fitness AI Assistant Web" (Web application type) for n8n OAuth
- Desktop OAuth clients don't support redirect URIs

**Key Learning:** Google OAuth Web Application type is required for services like n8n that need redirect URIs. Desktop type only works for local apps without callbacks.

### Three-Agent Architecture Clarified

**Architecture:**
```
EC2 Instance ($7/month)
├── Clawdbot (port 3100) - 24/7 Telegram access
└── n8n (port 5678) - Workflow automation

Local Mac (dev-sandbox)
├── Claude Code - Interactive development
└── Ralph - Autonomous multi-story development
```

**Routing:**
| Complexity | Handler |
|------------|---------|
| 0-3 (trivial) | Clawdbot handles directly |
| 4-6 (simple) | Clawdbot builds, commits, pushes |
| 7-10 (complex) | Ralph via PRD |
| Mac-specific | Claude Code (PyPI, MCP Registry) |

### Files Updated
- `.claude/KNOWLEDGE_BASE.md` - Added EC2/Clawdbot/n8n operations section
- `.tmp/n8n-setup-progress.md` - Updated with completion status and lessons learned

### Remaining Tasks
- [ ] Add Google OAuth redirect URI for n8n
- [ ] Configure Telegram credential in n8n
- [ ] Activate 7 n8n workflows
- [ ] Update SOPs 27, 28, 29 for three-agent collaboration

---

## 2026-02-01: n8n EC2 Migration + Source Pointer Analysis + Clawdbot/Ralph Audit

**Context:** Multi-track session - migrated n8n to EC2 for 24/7 availability, completed Source Pointer market viability analysis (SOP 17), and verified Clawdbot/Ralph documentation readiness.

### n8n EC2 Migration

**Accomplished:**
- ✅ Added 2GB swap space to prevent OOM crashes during npm install
- ✅ Installed n8n v2.4.8 on EC2 via npm
- ✅ Created systemd service (`/etc/systemd/system/n8n.service`)
- ✅ Exported 6 workflows from local n8n via MCP
- ✅ Imported all workflows to EC2 via n8n CLI
- ✅ Configured nginx reverse proxy (port 80 → 5678)
- ✅ Enabled SSH TCP forwarding (AllowTcpForwarding yes)
- ✅ Security group port 5678 opened to 0.0.0.0/0

**Unresolved Issue:**
- ❌ Port 5678 not accessible from internet despite all configurations appearing correct
- n8n responds locally with `{"status":"ok"}`
- External connections get "connection reset"
- **Debug command for next session:** `curl -v http://34.193.98.97:5678/healthz`

**Workflows Migrated to EC2:**
| Workflow | ID | Status |
|----------|-----|--------|
| SMS-Response-Handler-v2 | G14Mb6lpeFZVYGwa | Inactive (needs credentials) |
| Form-Submission-Pipeline | MmXDtZMsY9nR5Wrx | Inactive |
| Daily-Operations-Digest | Hz05R5SeJGb4VNCl | Inactive |
| Follow-Up-Sequence-Engine | w8PYKJyeozM3qJQW | Inactive |
| Hot-Lead-to-ClickUp | SzVXrbi1y433799Y | Inactive |
| X-Social-Post-Scheduler | - | Inactive |

**Created:** `docs/EC2-N8N-SETUP.md` - Complete setup guide with:
- SSH tunnel instructions (http://localhost:5679 via tunnel)
- Credential setup (SMTP, Google Sheets, Gmail OAuth)
- Webhook URLs for Twilio configuration
- Troubleshooting commands

### Source Pointer Market Viability Analysis (SOP 17)

**4 Parallel Agents Completed:**
1. **Agent 1 (Market Size)**: TAM $47.5B, SAM $2.8-4.2B, SOM $2-8M Year 1-3
2. **Agent 2 (Competition)**: Perplexity main competitor, deep-linking is unique differentiator
3. **Agent 3 (Customer)**: Legal/journalism have 9-10/10 pain, high willingness to pay
4. **Agent 4 (Monetization)**: LTV:CAC ratio 8.4x, $15/mo Pro tier recommended

**Result:** Score 3.9/5 = **CONDITIONAL GO**

**Key Findings:**
- Deep-linking to exact paragraph is killer feature (no competitor has this)
- Target AI skeptics in legal/journalism verticals first
- Position as "research tool" not "AI" to reach skeptics
- Free tier mandatory to build trust

**Created:** `projects/shared/source-pointer/market-analysis/consolidated/VIABILITY-SCORECARD.md`

### Clawdbot/Ralph Documentation Audit

**Status:** 95% Complete - Production Ready

**Documentation Verified:**
- ✅ SOP-27-CLAWDBOT-USAGE.md - Complete decision tree and patterns
- ✅ SOP-28-RALPH-USAGE.md - PRD structure and execution flow
- ✅ SOP-29-THREE-AGENT-COLLABORATION.md - Comprehensive routing matrix
- ✅ CLAWDBOT-CAPABILITIES.md - Full capability inventory
- ✅ CLAWDBOT-OPS-MANUAL.md - System prompt and operations
- ✅ CLAWDBOT-TEST-PLAN.md - 7 test scenarios defined
- ✅ RALPH-CAPABILITIES.md - Architecture and CLI usage

**Minor Gaps (Operational, Not Documentation):**
- Tests 1-7 in CLAWDBOT-TEST-PLAN.md not yet executed
- No execution logs from production use
- Integration checklist not verified in practice

**Next Steps for Clawdbot/Ralph:**
1. Execute Test 1-6 from CLAWDBOT-TEST-PLAN.md when Clawdbot VPS operational
2. Document test results in session-history.md
3. Phase 2 credentials (read-only APIs) after trust established

### Key Learnings

1. **OOM Prevention:** Always add swap space before npm install on small instances
2. **SSH Tunneling:** Use `-L local:localhost:remote` for port forwarding
3. **Market Viability:** 4-agent parallel research (2-3 hours) saves weeks of building wrong thing
4. **Documentation Maturity:** 95% documentation + 0% testing ≠ production ready

### Files Created/Updated

- `docs/EC2-N8N-SETUP.md` - Complete EC2 n8n guide
- `projects/shared/source-pointer/market-analysis/consolidated/VIABILITY-SCORECARD.md`
- `.tmp/n8n-export/*.json` - 6 workflow exports

### Next Session Priority

1. **Debug n8n connectivity:** Run `curl -v http://34.193.98.97:5678/healthz` from Mac
2. **Complete n8n setup:** Access UI, credentials, activate workflows
3. **Update Twilio webhook** to EC2 endpoint

---

## 2026-01-30: n8n Integration + X Social Strategy Pivot + Clawdbot Research

**Context:** Major infrastructure day - integrated n8n workflow automation, Clawdbot delivered extensive research on fitness coaching strategy, Mac Mini vs EC2 analysis, and X social media pivot to "AI Builder in Public".

### n8n Workflow Integration

**Accomplished:**
- Connected n8n MCP to Claude Code (localhost:5678)
- Created 5 new n8n workflows to replace/enhance Python scripts:
  - **SMS-Response-Handler-v2** (G14Mb6lpeFZVYGwa) - Categorizes SMS, logs to Sheets, alerts on hot leads
  - **Form-Submission-Pipeline** (MmXDtZMsY9nR5Wrx) - Scores leads, routes by quality
  - **Daily-Operations-Digest** (Hz05R5SeJGb4VNCl) - 8 AM digest of emails, forms, SMS
  - **Follow-Up-Sequence-Engine** (w8PYKJyeozM3qJQW) - Multi-day follow-up with Wait nodes
  - **Hot-Lead-to-ClickUp** (SzVXrbi1y433799Y) - Creates ClickUp tasks for hot leads
- Added ClickUp credentials to n8n
- Created SOP 30: n8n Workflow Management
- Created `docs/N8N-TRANSITION-PLAN.md` with full migration strategy

**Python Scripts Replaced:**
- `twilio_webhook.py` → SMS-Response-Handler-v2
- `form_webhook.py` → Form-Submission-Pipeline
- `morning_digest.py` → Daily-Operations-Digest
- `follow_up_sequence.py` → Follow-Up-Sequence-Engine

**Key Decision - When to Use n8n vs Python:**
| Use n8n | Use Python |
|---------|------------|
| Webhook handlers | Complex ML/AI logic |
| Scheduled tasks with visual debugging | Statistical analysis |
| Multi-service integrations | Lead scoring algorithms |
| Follow-up sequences (Wait nodes) | Video/image generation |

### Clawdbot Research Deliverables (8 commits today)

**Strategic Analysis:**
1. **Mac Mini vs EC2 Analysis** - Mac Mini wins for personal AI assistant use case
   - Security: Mac Mini (not internet-exposed)
   - Cost: Break-even at ~32 months
   - Recommendation: Mac Mini for Clawdbot, EC2 for production APIs

2. **Amazon FBA vs Current Path** - Strategic decision analysis
   - Continue AI automation focus over FBA pivot

3. **Fitness Coaching Client Acquisition** - New strategy documented
   - Complete handoff for Cline agent
   - Asset audit completed

**X Social Media Pivot:**
- Created `CLAUDE-CODE-HANDOFF.md` (582 lines) - Complete strategy document
- Created `ai-builder-content.json` - New content templates
- Strategy: "AI Builder in Public" vs generic fitness tips
- Frequency: 4 posts/day weekdays, 2 posts/day weekends
- 50% posts with Grok-generated images ($0.07/image)
- Sample posts ready to queue

**Time-Blocked Calendar:**
- Created Jan 30 - Feb 8 calendar with time blocks
- Job prep handoff for Claude Code

### New Communication Patterns

- "Check n8n status" → Verify n8n running, list workflows
- "Create n8n workflow for X" → Use n8n MCP tools
- "Migrate X to n8n" → Follow `docs/N8N-TRANSITION-PLAN.md`

### Files Created/Updated

**n8n:**
- `docs/N8N-TRANSITION-PLAN.md` - Full migration strategy
- `CLAUDE.md` - Added SOP 30, updated documentation map
- n8n workflows (5 created via MCP)

**Clawdbot Commits:**
- `MAC-MINI-VS-EC2-ANALYSIS.md`
- `projects/shared/social-media-automation/CLAUDE-CODE-HANDOFF.md`
- `projects/shared/social-media-automation/templates/ai-builder-content.json`
- Multiple strategy and handoff documents

**Webhook Endpoints** (once n8n workflows activated):
| Endpoint | URL |
|----------|-----|
| SMS Responses | `http://localhost:5678/webhook/sms-response` |
| Form Submissions | `http://localhost:5678/webhook/form-submit` |
| Enroll Follow-up | `http://localhost:5678/webhook/enroll-followup` |
| Hot Lead → ClickUp | `http://localhost:5678/webhook/hot-lead-clickup` |

### Next Steps

1. Activate n8n workflows
2. Update Twilio webhook URL to point to n8n
3. Execute X social media strategy (queue posts)
4. Create n8n workflow for X social posting
5. Sync EC2 server with latest changes

---

## 2026-01-28: Clawdbot OAuth Fix + Troubleshooting Methodology

**Context:** Clawdbot OAuth token expired, needed to fix authentication on headless EC2 server.

**Problem:** Standard OAuth flow (`auth login`) requires browser redirect - impossible on headless servers. Error: "Invalid OAuth Request - Missing redirect_uri parameter"

**What Didn't Work (45 min wasted):**
- `npx @anthropic-ai/claude-code auth login` - redirect error
- Various flags and variations - same error
- Repeated attempts - same result

**What Fixed It (15 min after researching):**
1. **Research:** Searched "anthropic oauth headless", found GitHub issue #7100
2. **Solution:** `setup-token` flow designed for headless servers
   - Mac: `claude setup-token` (generates transferable token)
   - EC2: `clawdbot models auth paste-token --provider anthropic` (accepts pasted token)
3. **Config:** New `anthropic:manual` profile with static token, ordered first

**Key Learnings:**

1. **Rule of Three:** If same approach fails 3 times, STOP and research
2. **Research order:** Official docs → GitHub issues → web search
3. **Understand constraints:** "Headless server" = no browser = OAuth redirect impossible
4. **Error messages tell you something:** "Missing redirect_uri" = OAuth flow can't complete

**Documentation Created:**
- `docs/TROUBLESHOOTING-METHODOLOGY.md` - Research-first approach
- Updated `docs/CLAWDBOT-CAPABILITIES.md` - Correct token flow for headless
- Added Operating Principle #13 to CLAUDE.md

**New Communication Pattern:**
- "Rule of three" / "Stop and research" → Apply troubleshooting methodology

---

## 2026-01-17: Pricing Optimization + Branding Strategy + Development Pipeline Update

**Context:** Optimizing business pricing and branding using multi-agent exploration (SOP 9), formalizing research phase in development pipeline.

**Accomplished:**

1. **Pricing Optimization (SOP 9 - 4 Agents)**
   - Agent 1: Pure Value-Based (3.52/5)
   - Agent 2: Tiered SaaS (3.65/5)
   - Agent 3: Hybrid Model (4.05/5) - **WINNER**
   - Agent 4: Nick Saraev Pure (2.80/5)

   **Final Pricing (7 Stripe Products):**
   - Setup: $2,997 (Starter) / $7,497 (Growth) / $14,997 (Enterprise)
   - Retainers: $747/mo (Maintenance) / $2,247/mo (Partner)
   - Community: $47/mo (Monthly) / $397/yr (Annual)

2. **Branding Optimization (SOP 9 - 4 Agents)**
   - Agent 1: Generalist (2.85/5) - "Jack of all trades" hurts premium pricing
   - Agent 2: Fitness Niche (3.425/5) - Price mismatch with audience
   - Agent 3: AI/Claude Niche (3.625/5) - Strong technical credibility
   - Agent 4: Multi-Brand Landing Pages (4.05/5) - **WINNER**

   **Final Structure:**
   ```
   marceausolutions.com (Parent - AI Automation Agency)
   ├── /developers (PRIMARY - Claude implementations)
   ├── /fitness (SECONDARY - Creator automation)
   ├── /contractors (TERTIARY - Trade business automation)
   └── /community (Claude Framework community)
   ```

   **Primary Positioning:** "Claude Implementation Experts"
   **Tagline:** "AI Automation Systems That Actually Ship"

3. **Development Pipeline Updated (CLAUDE.md)**
   - Added formal RESEARCH phase (-1) before KICKOFF (0)
   - SOP 17 for market viability, SOP 9 for optimization decisions
   - Codifies the research-before-building pattern

4. **Stripe Products Created**
   - All 7 products created in Stripe (test mode)
   - Price IDs needed for payment links (user to provide)

**Files Created/Updated:**
- `CLAUDE.md` - Added research phase to development pipeline
- `projects/claude-framework/market-analysis/pricing-research/FINDINGS.md`
- `projects/claude-framework/market-analysis/pricing-optimization/*/FINDINGS.md` (4 agents)
- `projects/claude-framework/market-analysis/pricing-optimization/consolidated/OPTIMAL-MODEL.md`
- `projects/claude-framework/market-analysis/branding-optimization/*/FINDINGS.md` (4 agents)
- `projects/claude-framework/market-analysis/branding-optimization/consolidated/OPTIMAL-BRANDING.md`
- `docs/autonomous-agent-decision-tree.md`

**Next Steps (for next session):**
1. Get Stripe Price IDs for payment link integration
2. Create payment links for landing pages
3. Execute website changes based on branding decision
4. Build /developers, /fitness, /contractors landing pages

**Key Learning:**
- Research phase is NOT redundant - it's essential for optimization decisions
- Multi-agent exploration (SOP 9) produces better decisions than single-pass analysis
- Self-annealing: Document patterns as they emerge from work

---

## 2026-01-15 (Part 2): Fitness Influencer v1.3.0 - Video Blueprint & COGS Tracker

**Context:** Continuing fitness-influencer development toward subscription launch per GO-NO-GO decision requirements.

**Accomplished:**

1. **Video Blueprint Generator** (`generate_video_blueprint`)
   - Added to MCP server (10th tool, now 12 total)
   - Generates viral video templates with segment-by-segment scripts
   - 5 styles: educational, transformation, day_in_life, before_after, workout_demo
   - Platform-optimized timing (TikTok, Instagram Reels, YouTube Shorts, YouTube)
   - Interactive HTML timeline visualization
   - Script suggestions and visual hints for each segment
   - Cost: FREE

2. **COGS Tracking Dashboard** (`get_cogs_report`, `log_api_usage`)
   - Created `cogs_tracker.py` for API cost monitoring
   - Tracks Grok images ($0.07), Shotstack video ($0.06), video ads ($0.20)
   - Daily and monthly COGS reports with gross margin calculation
   - HTML dashboard generation with alerts
   - Target margin: 60%+ (warns at 55%, critical at 50%)
   - Addresses pre-launch requirement from GO-NO-GO decision

3. **Updated SKILL.md**
   - Added new trigger phrases: "create video blueprint", "video template", "plan my video"
   - Added new capabilities to decision tree
   - Updated script reference table with new tools

**Version:** 1.3.0 (12 MCP tools total)

**Pre-Launch Checklist Progress (from GO-NO-GO):**
- [x] COGS monitoring - Set up API cost tracking dashboard
- [ ] Pricing update - PRO tier to $49/month (pending)
- [ ] Annual billing - Implement annual option (pending)
- [ ] Churn tracking - Cohort analysis (pending)

**Next Steps:**
1. Implement pricing tier updates ($19 STARTER, $49 PRO, $149 AGENCY)
2. Add annual billing option (20% discount)
3. Create onboarding flow
4. Prepare launch content

---

## 2026-01-15: Lead Scraper Enhancement & Project Viability Assessment

**Context:** Enhancing lead-scraper with Apollo.io/LinkedIn integration, assessing all projects for MCP commercialization potential, documenting cloud function deployment model.

**Accomplished:**

1. **Lead Scraper Enhancements**
   - Added `apollo.py` - Apollo.io API integration for LinkedIn enrichment, email finder, company/person search
   - Added `linkedin.py` - Sales Navigator export parsing, LinkedIn URL validation, search URL builder
   - Updated `config.py` with new API key fields (Apollo, Hunter)
   - Added Google Places API key to `.env`: `AIzaSyAViFkLMAp46vJo1CoXanVurYiFNXRp12w`

2. **New Documentation Created**
   - `docs/cloud-function-deployment-analysis.md` - Analysis of serverless model (Modal, Lambda) vs our architecture
   - `docs/optimization-threshold-policy.md` - **10x Rule**: Only optimize if 10x cost reduction OR 10x value increase
   - `docs/project-viability-assessment.md` - All projects scored for MCP commercialization

3. **Deployed New Projects**
   - `time-blocks` v1.0.0 deployed to `/Users/williammarceaujr./time-blocks-prod/`
   - `lead-scraper` v1.0.0 deployed to `/Users/williammarceaujr./lead-scraper-prod/`
   - Fixed `deploy_to_skills.py` to auto-copy templates and create `src/` package structure

4. **Updated CLAUDE.md**
   - Added cloud function model and optimization threshold docs to documentation map

**Project Viability Summary:**

| Project | Score | Verdict |
|---------|-------|---------|
| Lead Scraper | 4.0/5 | **MCP candidate** - $0.25-0.50/lead |
| Amazon Seller | 4.0/5 | **MCP candidate** - per-query pricing |
| MCP Aggregator | 4.2/5 | **Platform priority** - transaction fees |
| Fitness Influencer | 3.6/5 | **Web app** (not MCP) - subscription |
| Others | <3.2 | Personal tools only |

**Key Learnings:**

1. **10x Rule for Optimization**
   - Don't spend 8 hours for 5% improvement
   - Only pursue changes that provide 10x cost reduction or value increase
   - Document in backlog if <10x but still valuable (review quarterly)

2. **Cloud Functions Are Enhancement, Not Replacement**
   - Our DOE architecture is solid for development
   - Cloud functions add pay-per-use monetization channel
   - Best candidates: lead-scraper, mcp-aggregator, email-analyzer
   - Poor candidates: interactive tools (interview-prep, fitness-influencer)

3. **API Key Organization**
   - Lead scraper needs: Google Places ✅, Yelp, Apollo, Hunter
   - Apollo.io provides legitimate LinkedIn data access (50 free credits/mo)
   - Use Apollo instead of scraping LinkedIn directly

**API Keys Still Needed:**
- `YELP_API_KEY` - https://www.yelp.com/developers/v3/manage_app
- `APOLLO_API_KEY` - https://app.apollo.io/#/settings/integrations/api
- `HUNTER_API_KEY` - https://hunter.io/api_keys (optional)

**Next Steps:**
1. Get remaining API keys for lead-scraper
2. Test lead-scraper with Google Places API
3. Continue fitness-influencer development toward subscription launch

---

## 2026-01-13 (Part 2): MCP Registry Publishing & SOPs 11-13

**Context:** Publishing MCPs to PyPI and Claude's MCP Registry marketplace. Created SOPs documenting the complete publishing pipeline.

**Accomplished:**
- Published 3 MCPs to PyPI and Claude MCP Registry:
  - `md-to-pdf-mcp` v1.0.1 → `io.github.wmarceau/md-to-pdf`
  - `amazon-seller-mcp` v1.0.0 → `io.github.wmarceau/amazon-seller`
  - `fitness-influencer-mcp` v1.0.0 → `io.github.wmarceau/fitness-influencer`
- Created SOP 11: MCP Package Structure (converting projects to MCP format)
- Created SOP 12: PyPI Publishing (uploading to PyPI)
- Created SOP 13: MCP Registry Publishing (registering on Claude marketplace)
- Updated Development Pipeline with Step 7 (MCP Registry Publishing)
- Updated Quick Reference table with SOPs 11-13
- Added communication patterns for MCP publishing

**Key Learnings:**

1. **Publishing Order is Critical**
   - PyPI MUST come before MCP Registry
   - MCP Registry validates package exists on PyPI
   - Version in server.json must match PyPI version exactly

2. **Package Structure Requirements**
   - Use underscores in package directory (`fitness_influencer_mcp`)
   - Use hyphens in PyPI package name (`fitness-influencer-mcp`)
   - Relative imports required (`.module` not `module`)
   - Remove sys.path manipulation from server.py

3. **MCP Registry Authentication**
   - Uses GitHub device flow authentication
   - Token expires after ~1 hour
   - Re-run `mcp-publisher login github` on 401 errors

4. **Ownership Verification**
   - Must add `mcp-name: io.github.[user]/[project]` to README
   - Must be near top of file
   - MCP Registry validates this before accepting publish

5. **Version Bumping**
   - PyPI does NOT allow re-uploading same version
   - Must bump version in 3 places: pyproject.toml, server.json, __init__.py
   - Use 1.0.1 if 1.0.0 already published

**Common Errors Fixed:**
| Error | Solution |
|-------|----------|
| `registryType "pip" unsupported` | Use `"pypi"` not `"pip"` |
| `401 Unauthorized` | Re-authenticate: `mcp-publisher login github` |
| `Ownership validation failed` | Add `mcp-name:` line to README |
| `File already exists` on PyPI | Bump version number |
| `Package not found` | Publish to PyPI before MCP Registry |

**New Communication Patterns:**
- "Publish to registry" / "Put on Claude marketplace" → Run SOPs 11-13
- "Make this an MCP" → Run SOP 11 (create package structure)

**Files Created:**
- `projects/md-to-pdf/pyproject.toml` - PyPI build config
- `projects/md-to-pdf/server.json` - MCP Registry manifest
- `projects/md-to-pdf/src/md_to_pdf_mcp/` - Package directory
- `projects/amazon-seller/pyproject.toml`
- `projects/amazon-seller/server.json`
- `projects/amazon-seller/src/amazon_seller_mcp/`
- `projects/fitness-influencer/pyproject.toml`
- `projects/fitness-influencer/server.json`
- `projects/fitness-influencer/src/fitness_influencer_mcp/`

**Files Updated:**
- `CLAUDE.md` - Added SOPs 11-13, updated pipeline, updated quick reference
- `projects/*/README.md` - Added `mcp-name:` ownership verification lines

**Published MCPs:**
| Package | PyPI URL | MCP Registry Name |
|---------|----------|-------------------|
| md-to-pdf-mcp | https://pypi.org/project/md-to-pdf-mcp/1.0.1/ | io.github.wmarceau/md-to-pdf |
| amazon-seller-mcp | https://pypi.org/project/amazon-seller-mcp/1.0.0/ | io.github.wmarceau/amazon-seller |
| fitness-influencer-mcp | https://pypi.org/project/fitness-influencer-mcp/1.0.0/ | io.github.wmarceau/fitness-influencer |

**Tools Used:**
- `python -m build` - Build Python packages
- `twine upload` - Upload to PyPI
- `mcp-publisher` - Publish to MCP Registry (requires Go)

**Next Steps:**
- Test MCPs via Claude Desktop installation
- Publish additional projects (interview-prep, mcp-aggregator)
- Consider GitHub Actions for automated publishing

---

## 2026-01-13: MCP Aggregator Platform Generalization

**Context:** Discovered that MCP Aggregator was developed in parallel with rideshare, baking in 51 rideshare-specific assumptions that blocked non-rideshare services. Executed systematic discovery methodology and parallel agent refactoring.

**Accomplished:**
- Created systematic shortcoming discovery methodology (documented in plan file)
- Analyzed 5 core files: router.py, registry.py, billing.py, schema.sql, rideshare_mcp.py
- Found 51 rideshare-specific assumptions blocking non-rideshare services
- Deployed 4 parallel refactoring agents to fix all shortcomings
- All agents completed successfully with comprehensive changes
- Platform now supports 6 connectivity types, 5 pricing models, 6 scoring profiles
- Updated CHANGELOG.md with v1.1.0-dev documentation
- Verified repository structure (no nested .git repos)
- Committed all changes (48 files, 16,960 insertions)

**Key Learnings:**

1. **Shortcoming Discovery Methodology**
   - Define what current implementation assumes (rideshare characteristics)
   - Define what OTHER services need (HVAC, flights, hotels, etc.)
   - Analyze each file for hardcoded vs configurable values
   - Calculate impact scores for non-rideshare services
   - Prioritize fixes by blocking severity

2. **Platform Core Was Dead Code**
   - `rideshare_mcp.py` bypassed platform core entirely
   - Direct HTTP calls instead of using router.py
   - No health tracking, no billing, no scoring
   - **Fix**: Created `aggregator_mcp.py` that uses platform core

3. **Parallel Agent Deployment**
   - Can deploy 4 agents in parallel using Task tool with subagent_type
   - Each agent gets isolated workspace (agent1/, agent2/, etc.)
   - Agents complete independently, consolidate findings after
   - Much faster than sequential refactoring

4. **Non-Rideshare Service Requirements**
   - Flight search: 3-5s latency (not 100-500ms), $0.10-0.25/call
   - HVAC services: 24-48hr response, email-based, per-RFQ billing
   - Hotels: Commission-based (10-15% of booking value)
   - Payment processors: Webhook-based (inbound events)
   - GraphQL APIs: Query-based (different request structure)

**New Communication Patterns:**
- "Determine shortcomings" → Create discovery methodology, analyze systematically
- "Run parallel agents" → Use Task tool with 4 subagents in single message
- "Platform not working for X" → Check if assumptions from parallel development

**Refactoring Changes:**

**Agent 1 - Platform Core Wiring:**
- Created `mcp-server/aggregator_mcp.py` - New MCP using platform core
- Fixed dead code issue - router.py, registry.py, billing.py now actually used
- Added configurable timeout per-MCP (supports hours for async services)

**Agent 2 - Connectivity Abstraction:**
- Added `ConnectivityType` enum: HTTP, EMAIL, OAUTH, WEBHOOK, GRAPHQL, ASYNC
- Made `endpoint_url` optional (not required for email-based services)
- Added `email_address` and `webhook_path` fields to MCP dataclass
- Validation now connectivity-type-specific

**Agent 3 - Flexible Billing:**
- Added `PricingModel` enum: PER_REQUEST, SUBSCRIPTION, COMMISSION, TIERED, HYBRID
- Added `TierConfig` dataclass for volume-based pricing
- Added fee calculation methods for all pricing models
- Added `subscriptions` and `pricing_tiers` tables to schema

**Agent 4 - Configurable Scoring:**
- Added `ScoringProfile` dataclass with configurable thresholds
- Added 6 scoring profiles: rideshare, travel, food_delivery, async, e_commerce, default
- Latency/cost scoring now uses category-specific thresholds
- Scoring weights configurable per-category

**Results:**
- Flight search (3s latency) now scores 100/100 instead of 30/100
- HVAC services (24hr response) now score fairly
- Email-based services can now register
- Commission-based billing now supported

**Files Created:**
- `projects/mcp-aggregator/mcp-server/aggregator_mcp.py` - New MCP server
- `projects/mcp-aggregator/SHORTCOMING-DISCOVERY-REPORT.md` - Complete analysis
- `projects/mcp-aggregator/agent1-rest-api/` - REST API workspace
- `projects/mcp-aggregator/agent2-accuracy-testing/` - Accuracy testing workspace
- `projects/mcp-aggregator/agent3-platform-core/` - Platform core refactoring

**Files Modified:**
- `projects/mcp-aggregator/agent3-platform-core/workspace/router.py` - ScoringProfile
- `projects/mcp-aggregator/agent3-platform-core/workspace/registry.py` - ConnectivityType
- `projects/mcp-aggregator/agent3-platform-core/workspace/billing.py` - PricingModel
- `projects/mcp-aggregator/agent3-platform-core/workspace/schema.sql` - New tables
- `projects/mcp-aggregator/CHANGELOG.md` - v1.1.0-dev documentation

**Next Steps:**
- Integrate refactored platform core back into main mcp-aggregator/src/
- Test with HVAC service registration (next project)
- Deploy aggregator_mcp.py to Claude Desktop
- Create integration tests for all connectivity types

---

## 2026-01-12 (Part 3): Architecture Conflict Resolution - Phase 1 Complete

**Context:** Comprehensive SOP audit revealed 5 major architectural conflicts. Evaluated 3+ solution options for each conflict, chose optimal solutions, and implemented Phase 1 (Documentation Updates).

**Accomplished:**
- Resolved all architectural conflicts with Two-Tier system
- Created comprehensive architecture guide (1000+ lines)
- Updated all core documentation for consistency
- Verified no remaining conflicts across all SOPs

**Key Decisions:**

1. **Code Location**: Hybrid Architecture (Option C)
   - Shared utilities (2+ projects) → `execution/`
   - Project-specific code → `projects/[name]/src/`
   - Extract to `execution/` only when 2+ projects use code

2. **DOE Application**: Two-Tier Architecture (Option C)
   - Tier 1 (Shared): Strict DOE in `execution/`
   - Tier 2 (Projects): Flexible architecture in `projects/[name]/src/`

3. **Skills Deployment**: -prod repos (Option B)
   - Production: `/Users/williammarceaujr./[name]-prod/` (separate repos)
   - Clean git workflow, can push to GitHub

4. **Version Management**: Comprehensive (Option C)
   - VERSION file + CHANGELOG.md + Git tags (three-way sync)

5. **Testing Artifacts**: Separate by Purpose (Option B)
   - `.tmp/` for temporary files
   - `testing/` for multi-agent tests
   - `demos/` for client outputs

**New Documentation:**
- `docs/architecture-guide.md` (1000+ lines) - Complete Two-Tier Architecture reference
  - Decision trees (where to put code, when to extract, how to deploy)
  - Code organization examples
  - Deployment patterns for both tiers
  - Migration guide from old architecture
  - Troubleshooting Q&A

**Files Updated:**
- `CLAUDE.md` - Architecture section replaced with Two-Tier system
  - Documentation Map updated with architecture-guide.md
  - Development Pipeline clarified (execution/ vs projects/src/)
  - "Where to Put Things" table expanded
  - SOP 1 updated with code organization guidance
- `docs/testing-strategy.md` - Integration with Two-Tier Architecture
  - Testing Environment Setup section updated
  - Architecture notes added
- `docs/COMPREHENSIVE-CONFLICT-AUDIT.md` - Status updated (Phase 1 complete)
- `docs/ARCHITECTURE-CONFLICT-RESOLUTION.md` - Status updated (Resolved)
- `docs/SOP-VERIFICATION.md` - Phase 1 implementation status added

**Architecture Resolution:**

**Before** (Conflicting):
```
execution/*.py - Mixed shared and project-specific code
projects/[name]/src/ - Unclear when to use
Confusion about source of truth
```

**After** (Clear):
```
Tier 1: Shared Utilities (Strict DOE)
  execution/*.py - Shared across 2+ projects

Tier 2: Projects (Flexible Architecture)
  projects/[name]/src/*.py - Project-specific code
```

**Decision Rule**: Default to `projects/[name]/src/`, extract to `execution/` when 2+ projects use it.

**Verification:**
- ✅ All documents reference architecture-guide.md
- ✅ Code organization rules clear across all SOPs
- ✅ Testing strategy aligned with Two-Tier Architecture
- ✅ No conflicting guidance remaining

**Critical Addition - Deployment Timing**:

User identified missing guidance: "When in the development, testing, and deployment process do we deploy to skills?"

**Added explicit deployment timing**:
- Updated `docs/architecture-guide.md` - Added "When to Deploy to Skills" section
  - 6-step pipeline diagram showing deployment at Step 5
  - Prerequisites checklist before deployment
  - Timeline example (Day 1-10 showing deployment on Day 10)
- Updated `CLAUDE.md` - Development Pipeline step 5 with prerequisites
  - "NEVER deploy before Step 3 (testing) is complete!"
  - Post-deployment verification step added (Step 6)
- Updated `docs/testing-strategy.md` - Complete 6-step pipeline
  - CRITICAL TIMING section
  - Location rules for each step (dev-sandbox vs -prod)
  - Example timeline (Monday-Saturday showing Friday deployment)
  - Common mistake vs correct timing

**Key Rule Established**: Deploy to skills ONLY after ALL testing complete (Manual → Multi-Agent → Pre-Deployment → THEN Deploy)

**Critical Clarification - Post-Deployment Testing**:

User asked: "How does testing only in dev-sandbox (DOE method files) affect deployment since we deploy to Claude skills method files? Is it worth testing again after deployment?"

**Answer: YES - Post-deployment testing is CRITICAL, not optional**

**Why**:
- Dev-sandbox structure (`projects/[name]/src/`) ≠ Production structure (`[name]-prod/execution/`)
- Different directory paths can cause import errors
- Different working directories can break relative paths
- Missing dependencies not caught until production
- Deployment process itself can introduce bugs

**What Was Updated**:
- Changed Scenario 4 from "RECOMMENDED" to "ALWAYS REQUIRED"
- Updated CLAUDE.md Development Pipeline (Step 6 required)
- Updated testing-strategy.md Scenario 4 with comprehensive checklists:
  - Deployment Structure Verification (files, paths, imports)
  - Functional Testing (same tests as pre-deployment)
  - Troubleshooting guide for common issues
- Added "Why Post-Deployment Testing is Critical" section to architecture-guide.md
  - Visual comparison of dev vs prod structure
  - 5 things that can go wrong
  - Real example showing import error

**New Testing Rule**:
```
Step 4: Pre-Deployment Verification - in dev-sandbox (tests CODE)
Step 5: DEPLOY to skills
Step 6: Post-Deployment Verification - in -prod (tests DEPLOYMENT + STRUCTURE)
```

Both steps 4 and 6 are ALWAYS REQUIRED.

**Next Phase**: Phase 2 (Code Audit & Reorganization) - Audit `execution/` folder to separate shared vs project-specific scripts

---

## 2026-01-12 (Part 2): Multi-Agent Testing Failure & Testing Strategy

**Context:** MD-to-PDF multi-agent testing failed due to premature testing (before implementation stable and environment resolved)

**Accomplished:**
- Root caused testing failure
- Created comprehensive testing strategy
- Updated all SOPs with testing prerequisites
- Documented lessons learned

**Key Learning:** **Test too early = agents crash**

Prerequisites for multi-agent testing:
1. ✅ Manual testing complete (Scenario 1)
2. ✅ Core implementation stable
3. ✅ Environment issues resolved (library paths, dependencies)
4. ✅ Basic workflows documented
5. ✅ Basic functionality verified

**New Documentation:**
- `docs/testing-strategy.md` (400+ lines) - Single source of truth for all testing
  - Scenario 1: Manual Testing (ALWAYS required)
  - Scenario 2: Multi-Agent Testing (OPTIONAL, after Scenario 1)
  - Scenario 3: Pre-Deployment Verification (ALWAYS required)
  - Scenario 4: Post-Deployment Verification (RECOMMENDED)
  - Decision trees for when to use each
  - Prerequisites checklists
- `projects/md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md` - Root cause analysis

**Files Updated:**
- `CLAUDE.md` - Added TEST step to Development Pipeline (between DEVELOP and DEPLOY)
  - SOP 2 updated with CRITICAL PREREQUISITES
  - SOP 3 updated with testing prerequisites
  - Quick Reference table updated
- `docs/development-to-deployment.md` - Testing references added
- `docs/SOP-VERIFICATION.md` - Verified all SOPs consistent

**Testing Pipeline Established:**
```
Manual Testing → Multi-Agent Testing → Pre-Deployment → Deploy → Post-Deployment
(ALWAYS)         (OPTIONAL)            (ALWAYS)         (Done)   (RECOMMENDED)
```

**Success Example**: email-analyzer (tested after stable implementation)
**Failure Example**: md-to-pdf (tested too early, agents crashed)

---

## 2026-01-12 (Part 1): Documentation Process & MD-to-PDF Project

**Context:** Documenting the complete development-to-deployment pipeline, creating comprehensive reference guides

**Accomplished:**
- Created comprehensive development-to-deployment process guide
- Built Markdown to PDF Converter project following SOP 1
- Enhanced CLAUDE.md with development process references
- Documented repository structure and where files live during each phase

**Key Learnings:**
1. **Documentation process** - Create directive, develop in dev-sandbox, document workflows as you work, deploy when ready
2. **Repository structure** - Development in ONE repo (dev-sandbox), production in separate sibling repos
3. **Document types** - Living (session-history, prompting-guide) vs Stable (SOPs, workflows, directives)
4. **WeasyPrint advantages** - Better CSS support and interactive PDF links than ReportLab
5. **Workflow documentation timing** - Document WHILE completing tasks, not after

**New Documentation:**
- `docs/development-to-deployment.md` - Complete guide from dev through deployment (700+ lines)
  - Repository structure (dev vs prod)
  - Documentation process (5 phases)
  - Common workflows
  - Deployment commands reference
  - Where things live at each stage
  - Quick reference checklists

**New Project: MD-to-PDF Converter**
- `directives/md_to_pdf.md` - Capability SOP with edge cases
- `projects/md-to-pdf/src/md_to_pdf.py` - Full implementation (450+ lines)
- `projects/md-to-pdf/workflows/convert-md-to-pdf.md` - Step-by-step workflow
- `projects/md-to-pdf/README.md` - Project overview
- `projects/md-to-pdf/VERSION` - 0.1.0-dev
- `projects/md-to-pdf/CHANGELOG.md` - Version history

**Files Updated:**
- `CLAUDE.md` - Added development-to-deployment.md to Documentation Map

**Architecture Reinforcement:**
```
Development (ONE repo):
/Users/williammarceaujr./dev-sandbox/
  ├── .git/                    ← Single git repo
  ├── directives/              ← What to do
  ├── projects/[name]/         ← NO .git here!
  └── execution/               ← How to do it

Production (MANY repos):
/Users/williammarceaujr./
  ├── dev-sandbox/             ← Development
  ├── [project]-prod/          ← Deployed skills
  │   └── .git/                ← Separate repos
  └── website-repo/            ← Standalone projects
      └── .git/
```

**Next Steps:**
- Test MD-to-PDF converter with various markdown files
- Deploy v1.0.0 when ready
- Use as reference for future documentation projects

---

## 2026-01-09: DOE Architecture Rollback & Website Builder Social Pipeline

**Context:** Rolling back premature deployments to follow DOE (Directive-Orchestration-Execution) architecture properly. Also completed social media research pipeline for website-builder.

### Part 1: Website Builder Social Research Pipeline

**Accomplished:**
- Built complete social media research → website generation pipeline
- Implemented 5 approaches: Direct API, Web Scraping, Hybrid Search, Manual Input, Multi-Agent
- Selected hybrid approach combining Manual Input + Hybrid Search
- Created personality-driven content generation and styling

**Files Created:**
- `projects/website-builder/src/social_profile_analyzer.py` - Parse social URLs, analyze communication style
- `projects/website-builder/src/web_search.py` - Brave/Tavily web search integration
- `projects/website-builder/src/personality_synthesizer.py` - Brand personality synthesis

**Files Updated:**
- `projects/website-builder/src/research_engine.py` - Added `research_with_social()` method
- `projects/website-builder/src/content_generator.py` - Added `generate_personality_content()`
- `projects/website-builder/src/site_builder.py` - Added `build_personality_site()` with dynamic styling
- `projects/website-builder/src/website_builder_api.py` - Added 4 new endpoints for social workflow
- `projects/website-builder/README.md` - Complete rewrite with architecture diagram
- `projects/website-builder/VERSION` - Updated to 0.2.0

**New Endpoints:**
- `POST /api/research/social` - Research with social profiles
- `POST /api/generate/personality` - Personality-driven content
- `POST /api/build/personality` - Personality-styled site
- `POST /api/workflow/social` - Full social workflow

### Part 2: DOE Architecture Rollback

**Problem:** Jumped the gun deploying marketing pages before projects were ready. Violated DOE pattern.

**Rollback Actions:**
1. Updated root `index.html` → "Coming Soon" page with unified inquiry form
2. Updated `contact.html` → Streamlined with consolidated email/SMS opt-in
3. Removed premature pages: `solutions.html`, `about.html`, `setup_form.html`, `nav-styles.css`, `nav-component.js`
4. Updated `website-repo/index.html` → "Coming Soon" with inquiry form
5. Updated `website-repo/contact.html` → Consistent contact form
6. Removed premature website-repo pages: `fitness.html`, `amazon.html`, `medtech.html`, `all-solutions.html`, `services.html`, `about.html`, `assistant.html`, `testimonials.html`, `blog.html`, `signup.html`, `opt-in.html`

**Key Learnings:**
1. **DOE discipline** - Don't deploy frontend until execution layer is solid
2. **Coming Soon pattern** - Show project previews, collect inquiries, auto opt-in for email/SMS
3. **Consolidated opt-in** - Pre-checked email + SMS checkboxes on all forms
4. **Clean rollback** - Remove premature files rather than leaving broken links

**New Communication Patterns:**
- "Roll back" → Remove premature deployments, show Coming Soon
- "Follow DOE" → Check if Directive exists before deploying Execution
- Form submission → Auto opt-in for both email and SMS (pre-checked)

**Architecture Reminder:**
```
DOE Pattern:
Layer 1: DIRECTIVE (directives/*.md)     → What to do
Layer 2: ORCHESTRATION (You/Claude)      → Decision making
Layer 3: EXECUTION (execution/*.py)      → Deterministic scripts
```

Deploy ONLY when all three layers are solid.

---

## 2026-01-08 (Late Night): Fitness Influencer Dual-AI Chat System

**Context:** Building polished web chat interface for Fitness Influencer AI with dual-AI architecture (Claude + Grok)

**Accomplished:**
- Built dual-AI router combining Claude (intent/routing) and Grok (cost optimization/images)
- Implemented cost confirmation guardrails for operations >$0.10
- Created production-ready chat interface with real API integration
- Deployed Fitness Influencer AI to Railway
- Live at: https://api-production-1edc.up.railway.app

**Key Learnings:**
1. **Dual-AI architecture** - Claude handles NLU/routing, Grok handles images + cost suggestions
2. **Cost guardrails** - $0.10 threshold requires user confirmation, show alternatives
3. **Module imports in Railway** - Use `src.module_name` format with try/except for local dev
4. **python-multipart required** - FastAPI file uploads need this dependency
5. **Railway secrets** - Safe for production, but avoid CLI `--set` (logs to shell history)

**New Communication Patterns:**
- "Perfect the Fitness Influencer" → Focus on web chat, not CLI
- Paid operations → Always show cost + alternatives before executing
- "Why show them CLI?" → Client-facing demos should match delivery format

**Cost Tier System:**
- FREE: Video editing, graphics, email, analytics, workout/nutrition plans
- LOW (<$0.10): 1 AI image ($0.07)
- MEDIUM ($0.10-$0.30): 2-4 AI images ($0.14-$0.28)
- HIGH (>$0.30): Video ads ($0.34+)

**Files Created:**
- `projects/fitness-influencer/src/dual_ai_router.py` - Dual-AI decision router
- `projects/fitness-influencer/src/__init__.py` - Module init
- `projects/fitness-influencer/frontend/chat.html` - Chat interface (updated)
- `projects/fitness-influencer/frontend/dashboard.html` - Tool dashboard
- `projects/fitness-influencer/.env.example` - Environment template
- `projects/fitness-influencer/Procfile` - Railway start command
- `projects/fitness-influencer/railway.toml` - Railway config

**Files Updated:**
- `projects/fitness-influencer/src/chat_api.py` - Dual-AI flow, cost tracking
- `projects/fitness-influencer/requirements.txt` - Added python-multipart

**Deployment:**
- Railway project: fitness-influencer-ai
- Service: api
- Domain: https://api-production-1edc.up.railway.app
- Status: Live and healthy

---

## 2026-01-08 (Night): Interview Prep v1.3.0 Full Deployment

**Context:** Deploying Interview Prep AI Assistant with frontend and website integration

**Accomplished:**
- Deployed Interview Prep v1.3.0 to production
- Frontend deployed to Railway (https://interview-prep-pptx-production.up.railway.app/app)
- Added Interview Prep to website Industries dropdown navigation
- Updated solution card with full AI Assistant capabilities
- Enhanced deployment checklist with security review, pre-deployment verification
- Created MCP server configuration with cost-benefit guidelines
- Documented MCP decision matrix for future deployments

**Key Learnings:**
1. **MCP servers are token-intensive** - Use for external/shared assistants, prefer scripts for personal tools
2. **Full deployment = skill + frontend** - Use `deploy_to_skills.py --full` for one-command deploy
3. **Decision matrix location** - Document in `docs/full-deployment-pipeline.md` for future reference
4. **Industries dropdown** - Edit `nav-component.js` to add new solutions

**Deployment Checklist Additions:**
- Pre-deployment verification (git status, env vars, no hardcoded secrets)
- Security review section (credentials, input validation, API protection)
- Post-deployment monitoring (first hour)
- Documentation section (README, API docs, help text)

**Files Created/Updated:**
- `docs/full-deployment-pipeline.md` - Enhanced deployment checklist
- `.claude/mcp-servers/mcp-config.json` - MCP configuration with cost guidance
- `docs/mcp-integration-opportunities.md` - MCP research and analysis
- `nav-component.js` - Added Interview Prep to Industries dropdown
- `index.html` - Updated solution card to "Interview Prep AI Assistant"
- `.claude/skills/interview-prep/SKILL.md` - Updated to v1.3.0

**Current Status:**
- Production version: 1.3.0
- Development version: 1.4.0-dev
- Frontend: Live at Railway
- Skill: Deployed to `.claude/skills/interview-prep/`

---

## 2026-01-08 (Late Evening): Interview Prep Expansion & Personal AI Assistant

**Context:** Expanding Interview Prep from PowerPoint-only to comprehensive assistant, setting up Personal AI Assistant project

**Accomplished:**
- Expanded Interview Prep scope from "PowerPoint Builder" to full "AI Assistant"
- Built mock interview capability with STAR format evaluation
- Built PDF output generator (cheat sheets, talking points, flashcards, checklists)
- Built intent router for unified conversational interface
- Created Personal AI Assistant project structure
- Updated all documentation to reflect new organization
- Clarified living vs stable documents

**Key Learnings:**
1. **Mock interviews** - Use behavioral/technical/case types, evaluate with STAR format
2. **Intent routing** - Classify user request → route to appropriate workflow
3. **Personal Assistant** - Aggregates all skills, no frontend, Claude Code chat only
4. **Document types** - Living (session-history, prompting-guide, CLAUDE.md) vs Stable (SOPs, workflows)

**New Communication Patterns:**
- "Practice interview with me" → Start mock_interview.py with company/role context
- "Give me a cheat sheet" → Run pdf_outputs.py --output cheat-sheet
- All requests → Route through personal-assistant skill for consistency

**Files Created:**
- `interview-prep-pptx/src/mock_interview.py` - Interactive mock interviews
- `interview-prep-pptx/src/pdf_outputs.py` - Cheat sheets, flashcards, etc.
- `interview-prep-pptx/src/intent_router.py` - Request routing
- `interview-prep-pptx/EXPANDED_SCOPE.md` - Vision for expanded assistant
- `interview-prep-pptx/workflows/mock-interview.md` - Mock interview workflow
- `interview-prep-pptx/workflows/quick-outputs.md` - PDF outputs workflow
- `projects/personal-assistant/README.md` - Personal assistant overview
- `projects/personal-assistant/VERSION` - 1.0.0-dev
- `projects/personal-assistant/CHANGELOG.md` - Version history
- `.claude/skills/personal-assistant/SKILL.md` - Master skill file

**Files Updated:**
- `.claude/skills/interview-prep/SKILL.md` - Expanded capabilities, v1.2.0-dev
- `interview-prep-pptx/VERSION` - Now 1.2.0-dev
- `deploy_to_skills.py` - Added personal-assistant project
- `docs/deployment.md` - Added personal-assistant to architecture
- `CLAUDE.md` - Clarified living vs stable documents

---

## 2026-01-08 (Evening): Versioned Deployment & User Guidance System

**Context:** Building systems for iterative deployment and better user experience

**Accomplished:**
- Created versioned deployment pipeline (like Anthropic ships Claude versions)
- Built user guidance prompts system for interview prep assistant
- Created inference guidelines for intelligent scope extension
- Fixed PowerPoint close-before-open issue
- Updated Brookhaven presentation with consistent theme and enhanced content

**Key Learnings:**
1. **Versioned deployments** - Use VERSION file + CHANGELOG.md per project
2. **Inference guidelines** - Very Low/Low/Medium/High risk determines action
3. **User guidance** - Show next-step prompts after each workflow stage
4. **Theme colors corrected** - #1A1A2E (dark navy), not #003366
5. **Relevance label** - Adobe red #EC1C24 for visual hierarchy

**New Communication Patterns:**
- "Deploy to skills" → Check version, use `deploy_to_skills.py --version X.X.X`
- After any major action → Show user guidance prompts with next options
- Styling changes → Apply to ALL slides (infer consistency)
- Content changes → Only change specified content (don't override user edits)

**Files Created:**
- `docs/versioned-deployment.md` - Complete versioning guide
- `docs/inference-guidelines.md` - When to extend scope vs ask
- `interview-prep-pptx/USER_PROMPTS.md` - User guidance at each stage
- `interview-prep-pptx/VERSION` - Current: 1.1.0-dev
- `interview-prep-pptx/CHANGELOG.md` - Version history
- `execution/download_pptx.py` - Download to ~/Downloads
- `execution/open_pptx.py` - Close previous before opening new
- `execution/enhance_experience_slides.py` - Rich content for slides 14-18

**Scripts Updated:**
- `deploy_to_skills.py` - Added `--status`, `--version` flags
- `live_editor.py` - Added `close_all_presentations()` function
- `apply_navy_theme.py` - Corrected to #1A1A2E

---

## 2026-01-08 (Morning): Interview Prep Workflows & Documentation Reorg

**Context:** Working on Brookhaven National Laboratory presentation, building live editing capabilities

**Accomplished:**
- Created `live_editor.py` for real-time PowerPoint editing
- Created `template_manager.py` for loading existing presentations
- Created `reformat_experience_slides.py` for standardizing slide layouts
- Created `apply_navy_theme.py` for consistent theming
- Built workflow documentation system in `interview-prep-pptx/workflows/`
- Reorganized dev-sandbox documentation structure

**Key Learnings:**
1. **Build workflows as you work** - Document procedures while completing tasks, not after
2. **Experience slide layout:** Title (0.55", 0.3"), Image (0.75", 1.5"), Description (6.55", 1.5"), Relevance (6.55", 4.5")

**New Communication Patterns:**
- "Make slides look like slide X" → Use inspection + reformatting scripts
- "I have the file open" → Start live editing session
- "Don't deploy yet" → Stay in dev-sandbox, iterate locally

**Files Created:**
- `execution/live_editor.py`
- `execution/template_manager.py`
- `execution/reformat_experience_slides.py`
- `execution/apply_navy_theme.py`
- `interview-prep-pptx/workflows/*.md` (6 workflow files)

---

## 2026-01-07: Interview Prep Initial Build

**Context:** Building interview prep PowerPoint generator

**Accomplished:**
- Fixed Railway 500 error (direct module imports vs importlib)
- Combined Steps 1 & 2 into single workflow
- Added slide preview functionality
- Generated first Brookhaven presentation with AI images

**Key Learnings:**
1. Railway needs direct imports, not dynamic importlib
2. Session management helps track iterative edits
3. Grok API costs ~$0.07/image

---

## Adding New Entries

When completing a session with significant learnings:

```markdown
## YYYY-MM-DD: [Brief Title]

**Context:** [What you were working on]

**Accomplished:**
- Item 1
- Item 2

**Key Learnings:**
1. Learning 1
2. Learning 2

**New Communication Patterns:** (if any)
- "User says X" → Do Y

**Files Created:** (if any)
- path/to/file.py
```
