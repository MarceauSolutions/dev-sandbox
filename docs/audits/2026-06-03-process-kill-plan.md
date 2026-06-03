# Process Kill Plan — 2026-06-03

**Goal:** Cut background processes/automations that are not serving current priorities (EPA 608 exam, Marceau Air HVAC launch, job applications).

**Approach:** Conservative kill list — only items that are (a) clearly broken, (b) supposed to already be retired per memory, or (c) tied to ended sprints. Items you may still want (morning digest, hub, dystonia digest, bidirectional sync) are NOT touched.

**Decisions captured:**
- AI phone agent at (855) 239-9364 → **pause poller, keep service deployed** (reactivate when ready for HVAC inbound).
- Execution mode → **review only, do not run**.

---

## Section 1 — Mac Crontab (edit with `crontab -e`)

**Comment out or delete these lines:**

```cron
# Daily follow-up processing - 9 AM EST  (AI client sprint over)
0 9 * * * /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/scripts/daily_followup_cron.sh ...

# Weekly optimization review - Mondays at 9 AM EST  (sprint over)
0 9 * * 1 /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/scripts/weekly_optimization_review.sh ...

# X Platform post processing - Every hour 8 AM to 9 PM EST  (content sprint over, 14 runs/day)
0 8-21 * * * /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation/scripts/x_post_cron.sh ...

# 8x daily outreach scheduler — BROKEN, errors on every run with ModuleNotFoundError
0 6 * * * cd .../lead-scraper && ... outreach_scheduler daily-run --business marceau-solutions
5 6 * * * cd .../lead-scraper && ... outreach_scheduler daily-run --business swflorida-hvac
0 8 * * * cd .../lead-scraper && ... outreach_scheduler process
0 9 * * * cd .../lead-scraper && ... outreach_scheduler process
0 10 * * * cd .../lead-scraper && ... outreach_scheduler process
0 11 * * * cd .../lead-scraper && ... outreach_scheduler process
0 13 * * * cd .../lead-scraper && ... outreach_scheduler process
0 14 * * * cd .../lead-scraper && ... outreach_scheduler process
0 15 * * * cd .../lead-scraper && ... outreach_scheduler process
0 16 * * * cd .../lead-scraper && ... outreach_scheduler process

# Amazon BJK refund reminder (Amazon tower on ice)
0 9 * * * cd /Users/.../dev-sandbox && python3 .../bjk_refund_reminder.py
```

**Keep nothing in crontab after this pass** — the only line that wasn't on the kill list above is more lead-gen. After cleanup, `crontab -l` should print empty (or just leave comments).

---

## Section 2 — Mac LaunchAgents

**Unload + remove these plists:**

```bash
# Lead-gen sprint over — kill 3
launchctl unload ~/Library/LaunchAgents/com.marceau.leadgen.check-responses.plist
launchctl unload ~/Library/LaunchAgents/com.marceau.leadgen.daily-loop.plist
launchctl unload ~/Library/LaunchAgents/com.marceau.leadgen.digest.plist
rm ~/Library/LaunchAgents/com.marceau.leadgen.*.plist

# No active SaaS revenue right now
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.revenue-report.plist
rm ~/Library/LaunchAgents/com.marceausolutions.revenue-report.plist

# Cross-tower-sync — every 5 min, error log is 5.6 MB (it's been failing for weeks)
# Bidirectional sync covers the real need
launchctl unload ~/Library/LaunchAgents/com.marceau.cross-tower-sync.plist
rm ~/Library/LaunchAgents/com.marceau.cross-tower-sync.plist
```

**Keep:** `bidirectional-sync` (15min, EC2 data sync), `hub` (always-on dashboard), `pa.morning-digest` (6:30am briefing), `dystonia-digest` (7am, medical/personal), `backup-n8n` (Sunday 4am DR).

**Verify after:**
```bash
launchctl list | grep marceau
# Expected output: bidirectional-sync, hub, pa.morning-digest, dystonia-digest, backup-n8n only
```

---

## Section 3 — EC2 Services (run on EC2)

**SSH first:**
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97
```

**Kill the Clawdbot zombies (these were supposed to be retired May 16):**

```bash
# Stop + disable + mask so they cannot auto-restart
for svc in clawdbot clawdbot-pa accountability; do
  sudo systemctl stop $svc.service
  sudo systemctl disable $svc.service
  sudo systemctl mask $svc.service   # prevents re-enable by stray scripts
done
```

**Why:** `clawdbot.service` is currently fighting Panacea for the Telegram bot token, logging `getUpdates conflict; retrying in 30s` continuously. This is the exact symptom that triggered the May 16 retirement. Masking prevents it coming back.

**Kill legacy services:**

```bash
# fitai.service — fitness tower on ice
sudo systemctl stop fitai.service
sudo systemctl disable fitai.service

# voice-api.service — legacy, replaced by ai-phone-agent
sudo systemctl stop voice-api.service
sudo systemctl disable voice-api.service
```

**Keep running:** `n8n`, `panacea`, `bridge-v2`, `ai-phone-agent`, `ai-phone-dashboard`, `mem0-api`, `sms-webhook`.

**EC2 crontab cleanup (`crontab -e` as ec2-user):**

```cron
# Comment out:
# Spanish daily drill (one-shot, not active learning right now)
30 19 * * 1-5 python3 /home/clawdbot/dev-sandbox/scripts/spanish_daily_drill.py ...

# The one-shot clawdbot verify cron already fired May 23, can be deleted
7 13 23 5 * /home/ec2-user/dev-sandbox/scripts/verify_clawdbot_retired.sh ...
```

**Keep:** `*/30 * * * * /home/clawdbot/scripts/sync-agent.sh --auto-sync` (git sync, critical).

**Verify after:**
```bash
systemctl list-units --type=service --state=running | grep -iE "(clawd|accountability|fitai|voice-api)"
# Expected: nothing
```

---

## Section 4 — n8n Workflows (deactivate, don't delete)

**Open n8n: https://n8n.marceausolutions.com**

**Deactivate (flip the toggle off) — these are tied to ended sprints:**

| Workflow | Reason |
|---|---|
| `ElevenLabs Call Poller` | **720 runs/day**. Paused per your decision. Reactivate when ready for HVAC inbound. |
| `Hot-Lead-to-ClickUp` | ClickUp not in stack per memory; already dead-flagged. |
| `Cold Email Follow-Up Sequence` | AI client sprint ended. |
| `Calendly-Booking-Alert` | No active Calendly campaigns. |
| `Missed Call Text-Back DEMO` | Demo workflow, not production. |
| `Treatment-Day-Detector` | Not currently used. Confirm — if you're using this for Botox tracking, keep. |
| `Follow-Up-Sequence-Engine` | No active sequences. |
| `Questionnaire Response Watcher` | 288 runs/day. Confirm what it watches — if BOABFIT-related, deactivate. |

**Keep active:**
- `SMS-Response-Handler-v2` (Twilio STOP compliance, **required by carrier**)
- `Monthly-Workflow-Backup` (DR)
- `n8n-Health-Check`
- `GitHub Push → Telegram Notification`
- `Dystonia-Research-Digest-Daily`
- `Website-Lead-Capture` (will catch marceauair.com leads when site goes up)
- `Inbound-Lead-Router`
- `Stripe-Invoice-Paid` / `Stripe-Payment-Failed`
- `Weekly-Campaign-Analytics`
- `Weekly-Memory-Health-Check`

---

## Section 5 — Expected Impact

**Mac:**
- Crontab fires drop from ~25 cron events/day → 0.
- LaunchAgent fires drop from ~370/day (mostly cross-tower-sync every 5min + bidirectional every 15min) → ~96/day (bidirectional only) + 4 scheduled (hub always-on doesn't count, the others fire once daily/weekly).
- Removes the constant `ModuleNotFoundError` log spam in `outreach.log`.

**EC2:**
- Frees ~400 MB RAM (clawdbot gateway alone uses 350 MB).
- Eliminates the Telegram getUpdates conflict spam in Panacea logs.
- Removes 2 services that are CPU-busy-but-doing-nothing-useful.

**n8n:**
- Cuts roughly **1,015 executions/day** (720 ElevenLabs + 288 questionnaire + the others).
- That's a real reduction in API/webhook traffic and DB write volume.

**Anthropic API usage (the actual concern):**
- The Mac cron + LaunchAgent items above do NOT directly hit the Anthropic API — they're lead-gen and sync scripts. The actual API consumers that will continue running unchanged: `panacea` (your Telegram interface), `pa.morning-digest` (daily 6:30am), `bridge-v2` (n8n callbacks).
- If usage-limit relief is still insufficient after this pass, the next-tier cut is the `pa.morning-digest` (which uses Anthropic) — but losing the daily briefing is a meaningful UX hit. Recommend leaving it and seeing the post-cleanup baseline first.

---

## Section 6 — Re-audit checklist (after execution)

```bash
# Mac
crontab -l                                    # should be empty
launchctl list | grep marceau                 # ~5 entries left
ls ~/Library/LaunchAgents/com.marceau*.plist  # ~5 files left

# EC2
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 \
  'systemctl list-units --type=service --state=running | grep -iE "marceau|clawd|panacea|n8n|bridge|fitai|voice|phone|sync|mem0"'
# Expected services: n8n, panacea, bridge-v2, ai-phone-agent, ai-phone-dashboard, mem0-api, sms-webhook
# NOT expected: clawdbot, clawdbot-pa, accountability, fitai, voice-api

# n8n — count active workflows
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 \
  'sudo sqlite3 /home/ec2-user/.n8n/database.sqlite "SELECT COUNT(*) FROM workflow_entity WHERE active=1;"'
# Expected: ~10 (down from 18)
```

---

## Open questions before executing

1. **Treatment-Day-Detector** — is this tied to your Botox tracking? If yes, keep.
2. **Questionnaire Response Watcher** — 288 runs/day. What does it watch? Likely BOABFIT/coaching, but confirm before killing.
3. **Spanish daily drill cron on EC2** — keep for language learning, or kill?
