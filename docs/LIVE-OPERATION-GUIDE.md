# Company on a Laptop — Live Operation Guide

**Last Updated:** March 27, 2026

---

## Overview

Your multi-tower company runs autonomously during 7am–3pm work hours. The system discovers leads, sends outreach emails, monitors for responses, follows up automatically, and alerts you only when a prospect is ready to talk. Your job is the work that closes deals: reading the morning plan, visiting qualified leads, taking discovery calls, and recording what happened.

---

## Daily Automated Schedule

| Time | What Happens | Your Input |
|------|-------------|------------|
| **6:30am** | Morning digest → Telegram (health, ROI schedule, pipeline, email, calendar) | Read it (~1 min) |
| **9:00am** | Daily loop: discover → score → outreach → follow-up → cross-tower handoffs | None |
| **Every 15 min** | Response monitoring: Twilio + Gmail → HOT lead SMS if someone replies interested | Only if SMS arrives |
| **5:30pm** | Pipeline digest → Telegram (daily stats, hot leads, tomorrow's follow-ups) | Read it (~1 min) |

---

## Your Daily Actions

### Morning (6:30am)

Read the Telegram digest. It includes your ROI-prioritized plan:

```
📋 TODAY'S PLAN
  ❗ 09:00–11:00: 🎯 Walk-in visits: A&Y Auto Service, Dolphin Cooling
  ▪️ 13:00–15:00: 📞 Calls: Antimidators, Inc.
  💰 Expected ROI: MEDIUM — 5 visit targets + 1 proposals to close
  Reply 'yes schedule' to add these blocks to your calendar
```

If the plan looks good, reply **yes schedule** — the blocks appear on your Google Calendar.

### When You Receive a HOT Lead SMS

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
| **1** | Prospect receives your Calendly link via email. They book. You get a calendar event. |
| **2** | You receive their phone number via SMS. Call when ready. |
| **3** | Deal marked as passed. No further contact. |

### After Visits or Calls

Record what happened so tomorrow's digest shows your results:

```bash
cd ~/dev-sandbox/projects/lead-generation

# Good conversation
python3 -m src.daily_loop record --deal 42 --outcome conversation --notes "Interested in automation, wants proposal"

# Meeting booked
python3 -m src.daily_loop record --deal 42 --outcome meeting_booked --notes "Discovery call Thursday 2pm"

# Client won
python3 -m src.daily_loop record --deal 42 --outcome client_won --notes "Signed $2000 setup + $350/mo"

# Not interested
python3 -m src.daily_loop record --deal 42 --outcome not_interested

# Call back later
python3 -m src.daily_loop record --deal 42 --outcome callback --notes "Call back next Tuesday"
```

Valid outcomes: `conversation` · `meeting_booked` · `proposal_sent` · `client_won` · `callback` · `no_show` · `not_interested`

---

## Evening Routine (Recommended)

Run these two commands before wrapping up:

```bash
# Check pipeline status
cd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop status

# Save everything to GitHub
cd ~/dev-sandbox
./scripts/save.sh "end of day"
```

---

## Troubleshooting

| Problem | Command |
|---------|---------|
| Digest didn't arrive by 6:45am | `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check` |
| Re-send the digest manually | `cd ~/dev-sandbox/projects/personal-assistant && python3 -m src.unified_morning_digest` |
| Daily loop seems broken | `cd ~/dev-sandbox/projects/lead-generation && python3 -m src.daily_loop full --dry-run` |
| Launchd jobs need reload | `bash ~/dev-sandbox/projects/lead-generation/launchd/install.sh && bash ~/dev-sandbox/projects/personal-assistant/launchd/install.sh` |
| Check launchd status | `launchctl list \| grep marceau` |
| Save work right now | `cd ~/dev-sandbox && ./scripts/save.sh "checkpoint"` |

---

## Document Generation

Convert any Markdown file to a branded Marceau Solutions PDF:

```bash
# Quick way
./make-pdf.sh docs/LIVE-OPERATION-GUIDE.md

# With custom title
./make-pdf.sh drafts/proposal.md "Naples Med Spa — AI Automation Proposal"
```

Auto-detects the right template from keywords in the filename: proposal, workout, nutrition, onboarding, progress, agreement. Everything else uses the standard branded template.

Output: `projects/fitness-influencer/outputs/branded-pdfs/`

---

Keep this guide on your phone. The system is live — focus on closing clients.
