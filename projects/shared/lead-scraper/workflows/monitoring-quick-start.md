# Campaign Monitoring Quick Start

**Purpose**: Get started with the campaign monitoring dashboard in 5 minutes.

---

## 🚀 Quick Start (Copy-Paste Ready)

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper

# View real-time dashboard
python -m src.campaign_monitor dashboard

# Process overdue follow-ups (DO THIS FIRST!)
python -m src.follow_up_sequence process --dry-run  # Preview
python -m src.follow_up_sequence process --for-real # Send
```

---

## 📊 What the Dashboard Shows

### Critical Alerts (Red Section)
- **Overdue Follow-Ups**: Messages that should have been sent already
  - >3 days overdue = CRITICAL (lost opportunity)
  - 1-3 days overdue = HIGH (send today)
  - <1 day overdue = NORMAL (send now)

- **Unprocessed Replies**: Leads that responded but you haven't acted on yet
  - Hot leads get cold fast - respond within 24h

### Campaign Status (Blue Section)
- **Total Leads**: How many businesses you've contacted
- **Active Sequences**: How many are still in the follow-up pipeline
- **Touch Progress**:
  - T1 = Initial outreach sent
  - T2 = Follow-up #1 sent (Day 2)
  - T3 = Follow-up #2 pending (Day 5) ← **MOST IMPORTANT**

- **Response Rate**: What % of leads replied (target: 5-10%)
- **Opt-Out Rate**: What % said "STOP" (alert if >10%)

### Upcoming (Cyan Section)
- Follow-ups scheduled for next 24 hours

---

## ⚡ Daily Actions (3 Minutes)

### 1. Check for Overdue (Priority #1)
```bash
python -m src.campaign_monitor overdue
```

If any shown, send them immediately:
```bash
python -m src.follow_up_sequence process --for-real
```

**Why This Matters**:
- Hormozi research: 60% of responses come AFTER touch 3-5
- Overdue = lost revenue

---

### 2. Check for Replies
Look in "CRITICAL ALERTS" section for unprocessed replies.

**If Hot Lead** (interested):
```bash
# Create ClickUp task
python -m src.crm_sync create-task \
    --phone "+1XXXXXXXXXX" \
    --business-name "Business Name" \
    --priority high

# Stop their sequence (don't keep texting them)
python -m src.follow_up_sequence mark-response \
    --phone "+1XXXXXXXXXX" \
    --outcome hot_lead
```

**If Opt-Out** (STOP):
- Already handled automatically by webhook
- No action needed

---

### 3. Check Metrics
Look at Response Rate and Opt-Out Rate in dashboard.

**If Opt-Out Rate >10%**:
```bash
# View detailed analytics
python -m src.campaign_analytics report

# PAUSE campaign if >15%
# See: workflows/outreach-monitoring-sop.md Emergency section
```

---

## 📅 Automated Daily Check

Set up a cron job to run every morning at 9 AM:

```bash
crontab -e
```

Add this line:
```
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper && python -m src.follow_up_sequence process --for-real >> logs/followup-cron.log 2>&1
```

This automatically processes overdue follow-ups daily.

---

## 🎯 Success Metrics

**Daily Targets**:
- ✅ Overdue count: 0
- ✅ Unprocessed replies: 0 within 24h
- ✅ Response rate: 5-10%
- ✅ Opt-out rate: <10%

**Weekly Check**:
```bash
python -m src.campaign_analytics report
python -m src.campaign_analytics templates  # Which templates work best
python -m src.campaign_analytics funnel     # Conversion rates
```

---

## 🆘 Emergency Shortcuts

### Stop Everything (High Opt-Out Rate)
```bash
# Pause all pending touches
python -c "
import json
with open('output/follow_up_sequences.json', 'r') as f:
    data = json.load(f)
for seq in data['sequences']:
    for tp in seq['touchpoints']:
        if tp['status'] == 'pending':
            tp['status'] = 'skipped'
with open('output/follow_up_sequences.json', 'w') as f:
    json.dump(data, f, indent=2)
print('✅ All pending touches paused')
"
```

### Resume After Pause
```bash
# Change 'skipped' back to 'pending'
python -c "
import json
with open('output/follow_up_sequences.json', 'r') as f:
    data = json.load(f)
for seq in data['sequences']:
    for tp in seq['touchpoints']:
        if tp['status'] == 'skipped':
            tp['status'] = 'pending'
with open('output/follow_up_sequences.json', 'w') as f:
    json.dump(data, f, indent=2)
print('✅ Sequences resumed')
"
```

---

## 📧 Email Summary

Get daily summary emailed to you:

```bash
# One-time send
python -m src.campaign_monitor email-summary

# Automated daily (add to crontab)
0 8 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper && python -m src.campaign_monitor email-summary >> logs/monitor-cron.log 2>&1
```

Email includes:
- Total leads and sequences
- Overdue alerts
- Unprocessed replies
- Business breakdown

---

## 🔍 Understanding Your Current State

**Based on 2026-01-21 dashboard**:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Leads | 138 | - | ✅ |
| Active Sequences | 111 | - | ✅ |
| Response Rate | 10.1% | 5-10% | ✅ GOOD |
| Opt-Out Rate | 10.1% | <10% | ⚠️ BORDERLINE |
| Overdue Follow-Ups | 97 | 0 | 🚨 ACTION NEEDED |
| Touch 3 Pending | 111 | - | 🚨 CRITICAL (most important touch!) |

**IMMEDIATE ACTION REQUIRED**:
1. Send 97 overdue follow-ups TODAY
2. Monitor opt-out rate closely (don't let it go >15%)
3. Touch 3 is the "free_mockup" template - this drives most conversions

```bash
# Send overdue now
python -m src.follow_up_sequence process --for-real
```

---

## 📚 Full Documentation

- **Full SOP**: `workflows/outreach-monitoring-sop.md` (detailed procedures)
- **Script Reference**: `src/campaign_monitor.py` (all commands)
- **Strategy Guide**: `workflows/cold-outreach-strategy-sop.md` (optimize messaging)

---

**Last Updated**: 2026-01-21
**Next Review**: Daily at 9 AM
