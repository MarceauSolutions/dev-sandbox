# Company on a Laptop — Live Operation Guide

**Last Updated:** March 27, 2026

## Overview

Your multi-tower company runs autonomously during 7am–3pm work hours. The system discovers leads, sends outreach, monitors responses, follows up automatically, and alerts you only when a prospect is ready to talk. Your job is the human-touch work that closes deals: reading the morning briefing, visiting qualified leads, taking discovery calls, and recording what happened so the system gets smarter.

---

## Daily Automated Schedule

| Time | What Happens | Your Input |
|------|-------------|------------|
| **6:30am** | Morning digest → Telegram (health, schedule, pipeline, email, calendar) | Read it (1 min) |
| **9:00am** | Daily loop: discover → score → outreach → follow-up → cross-tower handoffs | None |
| **Every 15 min** | Response monitoring: Twilio + Gmail → classify → HOT lead SMS if detected | Only if HOT lead arrives |
| **5:30pm** | Pipeline digest → Telegram (daily stats, hot leads, tomorrow's follow-ups) | Read it (1 min) |

---

## Your Role Each Day

### Morning (6:30am)

Read the Telegram digest. It shows your ROI-prioritized plan for the day:

```
📋 TODAY'S PLAN
  ❗ 09:00–11:00: 🎯 Walk-in visits: A&Y Auto Service, Dolphin Cooling
  ▪️ 13:00–15:00: 📞 Calls: Antimidators, Inc.
  💰 Expected ROI: MEDIUM — 5 visit targets + 1 proposals to close
```

If the proposed schedule looks good, reply **yes schedule** to add the blocks to your Google Calendar.

### When You Get a HOT Lead SMS

You'll receive an SMS like this:

```
🔥 HOT LEAD

Naples Med Spa — Dr. Sarah Johnson
"This sounds interesting, can we talk this week?"

Reply:
1 = Send Calendly link
2 = I'll call them now
3 = Pass
```

| Reply | What Happens |
|-------|-------------|
| **1** | System emails them your Calendly link. They book a time. You get a calendar event. |
| **2** | System texts you their phone number. You call when ready. |
| **3** | Deal marked as passed. No further contact. |

### After Visits or Calls

Record the outcome so tomorrow's digest shows what happened:

```bash
cd ~/dev-sandbox/projects/lead-generation

# They want a proposal
python3 -m src.daily_loop record --deal 42 --outcome meeting_booked --notes "Wants proposal for missed-call text-back"

# Good conversation, call back later
python3 -m src.daily_loop record --deal 42 --outcome callback --notes "Call back Thursday"

# Not interested
python3 -m src.daily_loop record --deal 42 --outcome not_interested
```

Outcomes: `conversation`, `meeting_booked`, `proposal_sent`, `client_won`, `callback`, `no_show`, `not_interested`

---

## Evening Routine (Recommended)

After your last task of the day, run these two commands:

```bash
# Check pipeline status
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop status

# Save everything to GitHub
cd ~/dev-sandbox
./scripts/save.sh "end of day — [brief note]"
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 6:30am digest doesn't arrive by 6:45am | `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check` |
| Want to re-send the digest manually | `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.unified_morning_digest` |
| Daily loop seems broken | `cd ~/dev-sandbox/projects/lead-generation && python3 -m src.daily_loop full --dry-run` |
| Launchd jobs stopped | `bash ~/dev-sandbox/projects/lead-generation/launchd/install.sh && bash ~/dev-sandbox/projects/personal-assistant/launchd/install.sh` |
| Need to save work right now | `cd ~/dev-sandbox && ./scripts/save.sh "checkpoint"` |
| Check overall system health | `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check` |

---

Save this guide to your phone. The system is live — let it run and focus on closing clients.
