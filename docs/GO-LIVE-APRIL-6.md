# Go-Live Checklist & Daily Operation Guide

**For**: William Marceau Jr.
**Effective**: April 6, 2026 (Collier County start date)
**System**: Modular Multi-Tower Company on a Laptop

---

## Go-Live Checklist (One-Time, Before April 6)

Run each command from `~/dev-sandbox/`:

| # | Action | Command | Status |
|---|--------|---------|--------|
| 1 | Verify launchd jobs loaded | `launchctl list \| grep marceau` | Should show 4+ jobs |
| 2 | Gmail re-auth (if not done) | `python3 scripts/reauth_gmail.py` | Opens browser once |
| 3 | Verify .env has Telegram token | `grep TELEGRAM_BOT_TOKEN .env` | Must show value |
| 4 | Test morning digest | `cd projects/personal-assistant && python3 -m src.unified_morning_digest --preview` | Should show pipeline + email + calendar |
| 5 | Test daily loop | `cd projects/lead-generation && python3 -m src.daily_loop full --dry-run` | Should show 4/4 stages pass |
| 6 | Test health check | `cd projects/personal-assistant && python3 -m src.system_health_check` | Should show HEALTHY |
| 7 | Laptop must stay open/awake | System Preferences → Energy → Prevent sleep when display is off | Launchd needs the Mac awake |

---

## What You Will See Each Day

### 6:30am — Morning Digest (Telegram)

A single message that looks like this:

```
☀️ MORNING DIGEST — Monday, April 7

🟢 SYSTEM HEALTH: All checks pass

📊 PIPELINE
  250 Contacted → 230 Prospect → 12 Qualified → 2 Trial Active
  Outreached (24h): 8
  Auto follow-ups today: 3

📧 EMAIL (7 unread)
  ⭐ Stripe: Payment received ($197.00)
  ⭐ Naples Med Spa: Re: AI Automation

📅 TODAY (2 events)
  • 12:00 PM: Lunch
  • 06:00 PM: Training (blocked)

✅ ACTION ITEMS
  📧 2 priority email(s) to review
  📤 3 auto follow-ups scheduled (no action needed)
```

**Your action**: Read it. Takes 60 seconds. If there's a hot lead or priority email, handle it during lunch break.

### During Work Hours (7am–3pm) — System Runs Autonomously

| Time | What Happens | You Do |
|------|-------------|--------|
| 9:00am | Daily loop discovers leads, scores, sends outreach | Nothing |
| Every 15 min | System checks for replies to outreach | Nothing |
| If HOT lead replies | You get an SMS on your phone | See below |

### HOT Lead SMS Alert

If a prospect replies with interest, you'll get an SMS that looks like:

```
🔥 HOT LEAD

Naples Med Spa — Dr. Sarah Johnson
"This sounds interesting, can we talk this week?"

Score: 0.85 | Med Spa | Naples

Reply:
1 = Send Calendly link
2 = I'll call them now
3 = Pass
```

**Your action**: Reply with one digit.
- **1** = System sends a personalized Calendly link to the prospect. They book a time. You get a calendar event.
- **2** = System texts you their phone number. You call them when free.
- **3** = System marks them as not interested. No further contact.

### 5:30pm — Pipeline Digest (Telegram)

```
📊 PIPELINE DIGEST — April 7

Today's Loop:
  Discovered: 15 | Outreached: 8
  Follow-ups sent: 3
  Replies: 1 (🔥1 hot)

🔥 Hot Leads (1):
  • Naples Med Spa — Dr. Sarah Johnson [schedule_call]

📈 Pipeline: 252 Contacted → 232 Prospect → 13 Qualified

📅 Tomorrow: 4 auto follow-ups scheduled
```

**Your action**: Read it. 60 seconds. No action unless a hot lead is waiting.

---

## When Things Go Wrong

### You see 🔴 SYSTEM HEALTH in the morning digest

The digest will say which component failed:
```
🔴 SYSTEM HEALTH: Issues detected
  ⚠️ daily_loop: consecutive failures: 2
  ⚠️ gmail_token: scope error
```

**Your action**: Open terminal when you get home and run:
```bash
cd ~/dev-sandbox/projects/personal-assistant
python3 -m src.system_health_check
```
This shows exactly what's broken. Most issues self-heal on the next run.

### You get a "DAILY LOOP DEGRADED" Telegram alert

This means the acquisition loop has failed 2 days in a row. You'll see:
```
⚠️ DAILY LOOP DEGRADED

Failed 2 days in a row.
Failing stages: discover_score, follow_up

Errors:
  • discover_score: Apollo API timeout
  • follow_up: No leads file found

Check logs: projects/lead-generation/logs/
Manual run: python -m src.daily_loop full --dry-run
```

**Your action**: Run the manual command to diagnose. Usually it's a temporary API issue that resolves itself.

### Laptop goes to sleep / restarts

Launchd jobs resume automatically on wake. No action needed. If you reboot, verify:
```bash
launchctl list | grep marceau
```

---

## Weekly Maintenance (5 min, Sunday evening)

| Task | Command | Why |
|------|---------|-----|
| Check pipeline health | `cd projects/lead-generation && python3 -m src.daily_loop status` | See deal flow |
| Review loop health history | `cat projects/lead-generation/logs/loop_health.json \| python3 -m json.tool` | Spot degradation trends |
| Check for new hot leads missed | `cd projects/lead-generation && python3 -c "from src.hot_lead_handler import check_pending_handoffs; check_pending_handoffs()"` | Catch any leads that fell through |

---

## Emergency Commands

| Situation | Command |
|-----------|---------|
| Re-run daily loop manually | `cd projects/lead-generation && python3 -m src.daily_loop full --for-real` |
| Re-send morning digest | `cd projects/personal-assistant && python3 -m src.unified_morning_digest` |
| Check response monitoring | `cd projects/lead-generation && python3 -m src.daily_loop check-responses` |
| Full system health | `cd projects/personal-assistant && python3 -m src.system_health_check` |
| View pipeline status | `cd projects/lead-generation && python3 -m src.daily_loop status` |
| Reinstall launchd jobs | `bash projects/lead-generation/launchd/install.sh && bash projects/personal-assistant/launchd/install.sh` |

---

## What the System Does NOT Do (Human Required)

| Action | Why Human | How You'll Know |
|--------|-----------|-----------------|
| Set pricing on proposals | Every client is different | You manually draft/approve proposals |
| Sign contracts | Legal commitment | You send the agreement yourself |
| Conduct discovery calls | Relationship + rapport | Calendar event + prep packet in digest |
| Cold SMS outreach | TCPA violation risk ($500-$1,500/msg) | System only uses email for cold outreach |
| Respond to angry/threatening messages | Reputation risk | System flags opt-outs and escalates |
| Override calendar blocks | Only you know your energy/dystonia state | System respects your blocks |

---

---

## Week 1 Monitoring Plan (April 6-12)

### What to Watch in the First 3 Morning Digests

**Digest 1 (Monday April 7, 6:30am)**:
- Confirm it arrives on Telegram. If not → run `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.unified_morning_digest --preview` to diagnose.
- Check `🟢 SYSTEM HEALTH: All checks pass` appears at top. If `🔴`, see the specific failed component.
- Confirm pipeline numbers show (proves pipeline.db is accessible).
- Confirm email count is non-zero (proves Gmail API working).

**Digest 2 (Tuesday April 8)**:
- Check `Outreached (24h)` shows a real number (proves 9am daily loop ran and sent emails).
- Check `Auto follow-ups today` shows a count (proves follow-up sequences are advancing).
- If either shows 0: check `~/dev-sandbox/projects/lead-generation/logs/daily-loop.log` for errors.

**Digest 3 (Wednesday April 9)**:
- By now you should have baseline confidence. If all 3 digests arrived with real data, the system is stable.
- Check for any `⚠️ CLAUDE.md VIOLATIONS` line — should not appear if system is clean.

### How to Verify the Daily Loop Ran Successfully

Check the log file (takes 10 seconds):
```bash
tail -20 ~/dev-sandbox/projects/lead-generation/logs/daily-loop.log
```

You should see:
```
DAILY LOOP COMPLETE: 6/6 stages succeeded
Health: 6/6 passed, consecutive failures: 0
```

If it says fewer than 6/6, check the error log:
```bash
tail -30 ~/dev-sandbox/projects/lead-generation/logs/daily-loop-error.log
```

### What to Do if Health Check or Enforcer Shows Violations

1. **`🔴 SYSTEM HEALTH: Issues detected`** in the digest:
   - Run: `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check`
   - It tells you exactly which component failed (launchd, Gmail, Twilio, pipeline, etc.)
   - Most issues self-heal on next run. If persistent, check the specific log file.

2. **`⚠️ CLAUDE.md VIOLATIONS`** in the digest:
   - Run: `python3 ~/dev-sandbox/execution/standardization_enforcer.py`
   - It lists specific violations with fix instructions.
   - This should never appear if you haven't manually modified the codebase.

3. **`⚠️ DAILY LOOP DEGRADED`** Telegram alert:
   - This fires after 2 consecutive failures of critical stages.
   - Run: `cd ~/dev-sandbox/projects/lead-generation && python3 -m src.daily_loop full --dry-run`
   - Watch which stage fails. Usually a temporary API issue (Apollo, Twilio).

### First Evening Supervised Run (Recommended: Monday April 7, ~4pm)

After your first day at work, run the loop once with live sending and watch:

```bash
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop full --for-real 2>&1 | tee /tmp/first-live-run.log
```

Watch for:
- Stage 1-4: Did it discover and send real outreach emails? Check your sent mail.
- Stage 5-6: Did it check for replies correctly?
- Stage 7: Did follow-up sequences advance?
- Stage 8a: Any cross-tower handoffs triggered?
- Stage 9: Any new tower proposals detected?

If everything looks good, the system runs unattended from Tuesday onward.

### Quick Reference: One Command for Any Issue

```bash
cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check
```

This single command checks everything: launchd jobs, pipeline.db, Gmail, Twilio, daily loop health, and env vars. It tells you exactly what's wrong and how to fix it.

---

---

---

## Parallel Operation (Starting March 26 — System Runs Alongside Manual Efforts)

The automated system runs in the background while you continue manual outreach, networking, and walk-in visits. They complement each other:

| Channel | Who Does It | When |
|---------|------------|------|
| **Automated email outreach** (cold, 10/day) | daily_loop at 9am | Runs unattended every day |
| **Automated follow-ups** (3-touch sequences) | daily_loop at 9am | Runs unattended |
| **Response monitoring** (Twilio + Gmail) | check-responses every 15min | Already running since 7pm March 26 |
| **Manual networking** (walk-ins, calls, referrals) | William | During outreach blocks |
| **Discovery calls** | William | When HOT leads appear |

**They do NOT conflict**: The automated loop targets email outreach to new leads. Your manual efforts target in-person relationships and warm referrals. Different channels, same pipeline.db tracks both.

### Starting Tonight (March 26)

Run the supervised live test:
```bash
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop full --for-real
```

This sends real outreach emails to the top-scored leads. Watch it complete, check your sent mail. After this, the system runs automatically at 9am daily.

### What's Already Running
- **check-responses**: Polling Twilio every 15 min since 7pm March 26 (log shows 45 lines of activity)
- **morning-digest**: Will fire at 6:30am March 27
- **daily-loop**: Will fire at 9:00am March 27
- **digest**: Will fire at 5:30pm March 27

---

## Week 1: Land the First Client (March 27 — April 6)

### Success Metric
**At least one warm lead scheduled for a discovery call by April 6.**

### Day-by-Day Plan

**Day 1 (Thursday March 27)**:
- 6:30am: First real morning digest arrives on Telegram. Confirm it has pipeline numbers and email count.
- 9:00am: Daily loop fires automatically. No action needed.
- 5:30pm: Check pipeline digest. Note how many leads were outreached.
- Evening: Run one supervised live test:
  ```bash
  cd ~/dev-sandbox/projects/lead-generation && python3 -m src.daily_loop full --for-real
  ```
  Watch it send real outreach emails. Check your sent mail to confirm delivery.

**Day 2-3 (Friday-Saturday)**:
- Morning digests should show `Outreached (24h): [N]` where N > 0.
- Follow-up sequences should be advancing (`Auto follow-ups today: [N]`).
- If no responses yet, that's normal. 3-touch sequences take 7 days to complete.

**Day 4-7 (Sunday-Wednesday)**:
- By now first batch of Touch 1 recipients have had 3-5 days. Touch 2 goes out.
- Watch for HOT lead SMS alerts on your phone.
- Check the pipeline digest for response counts.

**When First HOT Lead Arrives**:
1. You'll get an SMS like: `🔥 HOT LEAD — Naples Med Spa — "This sounds interesting"`
2. Reply **1** to send Calendly link automatically.
3. Monitor your calendar for the booking (Calendly creates the event).
4. Morning digest will show the call under 📞 CALLS TODAY.
5. Do the call. This is the human step that closes the deal.

**If No HOT Leads by Day 5**:
- Check `python3 -m src.daily_loop status` — are leads being discovered and outreached?
- Check response rates: `tail -50 logs/daily-loop.log | grep "outreached\|replies"`
- Consider adjusting outreach volume: the daily cap is 10 emails/day. If you want faster results, increase it in `campaign_auto_launcher.py`.

### Protected Content
- Client website (flamesofpassionentertainment.com) restored to `client-sites/`
- damagedbydesign.com is hosted externally (not in this repo) — confirmed safe
- `PROTECTED_PATHS` list in standardization_enforcer.py prevents accidental deletion

---

---

## Saving Your Work

All major code changes should be committed and pushed to GitHub. Use the safe save command:

```bash
# Save with a message
./scripts/save.sh "Added new outreach templates"

# Save with default timestamp
./scripts/save.sh

# Preview what would be committed (no changes made)
./scripts/save.sh --dry-run

# Also include new files you created
./scripts/save.sh --include-new "Created new tower"
```

**Safety**: This script never stages `.env`, `token.json`, `credentials.json`, databases, or log files. It pulls before pushing. It only touches files already tracked by git (unless you use `--include-new`).

**When to save**: After any Claude Code session, after making manual changes, or any time you want a checkpoint.

---

**System designed for reliability over features.**
**When in doubt, check the morning digest — it tells you everything.**
