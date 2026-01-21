# Campaign Monitoring Cheat Sheet

**Quick reference for daily outreach monitoring**

---

## 🏃 Quick Commands (Copy-Paste)

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper

# Morning dashboard (daily at 9 AM)
python -m src.campaign_monitor dashboard

# Process overdue follow-ups (DO THIS FIRST!)
python -m src.follow_up_sequence process --for-real

# Check what's overdue
python -m src.campaign_monitor overdue

# View analytics
python -m src.campaign_analytics report

# Send daily email summary
python -m src.campaign_monitor email-summary
```

---

## 📊 Dashboard Interpretation

### Critical Alerts (Red)
- **>3 days overdue** = CRITICAL (lost revenue)
- **1-3 days overdue** = HIGH (send today)
- **<1 day overdue** = NORMAL (send now)

### Response Metrics
- **5-10%** = GOOD response rate
- **<10%** = Safe opt-out rate
- **>15%** = DANGER - pause immediately

### Touch Progress
- **T1** = Initial outreach sent
- **T2** = Follow-up #1 sent (Day 2)
- **T3** = Follow-up #2 (Day 5) ← **MOST IMPORTANT**
- **T4** = Follow-up #3 (Day 10)
- **T5** = Breakup message (Day 15)

---

## 🚨 Emergency Actions

### High Opt-Out Rate (>15%)
```bash
# STOP everything
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
print('✅ Campaign paused')
"
```

### Resume After Fix
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
print('✅ Campaign resumed')
"
```

---

## 💬 Reply Handling

### Hot Lead (Interested)
```bash
# Create ClickUp task
python -m src.crm_sync create-task \
    --phone "+1XXXXXXXXXX" \
    --business-name "Business Name" \
    --priority high

# Stop their sequence
python -m src.follow_up_sequence mark-response \
    --phone "+1XXXXXXXXXX" \
    --outcome hot_lead
```

### Opt-Out (STOP)
- Automatically handled by webhook
- No action needed

### Not Interested
```bash
# Stop their sequence
python -m src.follow_up_sequence mark-response \
    --phone "+1XXXXXXXXXX" \
    --outcome not_interested
```

---

## 📅 Automation Setup

### Daily Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines:

# Process overdue follow-ups daily at 9 AM
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper && python -m src.follow_up_sequence process --for-real >> logs/followup-cron.log 2>&1

# Email summary daily at 8 AM
0 8 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper && python -m src.campaign_monitor email-summary >> logs/monitor-cron.log 2>&1
```

---

## 🎯 Daily Checklist (5 minutes)

- [ ] Run dashboard: `python -m src.campaign_monitor dashboard`
- [ ] Check overdue count (target: 0)
- [ ] Process overdue if any: `python -m src.follow_up_sequence process --for-real`
- [ ] Check for unprocessed replies (respond within 24h)
- [ ] Verify response rate 5-10%, opt-out <10%

---

## 📈 Weekly Review

```bash
# View detailed analytics
python -m src.campaign_analytics report

# Compare template performance
python -m src.campaign_analytics templates

# View conversion funnel
python -m src.campaign_analytics funnel

# Export weekly report
python -m src.campaign_monitor export --output output/weekly-$(date +%Y%m%d).json
```

---

## 🔍 Current State (as of 2026-01-21)

| Metric | Value | Status |
|--------|-------|--------|
| Total Leads | 138 | ✅ |
| Active Sequences | 111 | ✅ |
| Response Rate | 10.1% | ✅ GOOD |
| Opt-Out Rate | 10.1% | ⚠️ BORDERLINE |
| Overdue Follow-Ups | 97 | 🚨 URGENT |
| Touch 3 Pending | 85 | 🚨 CRITICAL |

**IMMEDIATE ACTION**: Run `python -m src.follow_up_sequence process --for-real`

---

## 📚 Documentation

- **Quick Start**: `workflows/monitoring-quick-start.md` (5 min setup)
- **Full SOP**: `workflows/outreach-monitoring-sop.md` (detailed procedures)
- **Strategy Guide**: `workflows/cold-outreach-strategy-sop.md` (optimize messaging)
- **Current Status**: `output/CAMPAIGN-STATUS-SUMMARY-2026-01-21.md` (full analysis)

---

## 🆘 Troubleshooting

### Dashboard Shows 0 Leads
```bash
# Check files exist
ls -la output/sms_campaigns.json
ls -la output/follow_up_sequences.json
```

### Overdue Not Decreasing
```bash
# Check for errors
python -m src.follow_up_sequence process --dry-run

# Check logs
tail -50 logs/followup-cron.log
```

### Replies Not Showing
```bash
# Check webhook running
curl http://localhost:5001/health

# Check raw replies
cat output/sms_replies.json | jq '.replies[]'
```

---

**Last Updated**: 2026-01-21
**Owner**: William Marceau
**Project**: `/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper`
