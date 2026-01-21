# SOP: Daily Routine Checklist

*Last Updated: 2026-01-15*
*Version: 1.0.0*

## Overview

Daily tasks to ensure no leads, opportunities, or urgent items are missed. Designed to take 30-45 minutes total.

## Morning (8:00 AM - 10:30 AM)

### Step 1: Review Morning Digest (8:00 AM - 15 min)

**Objective**: Get overview of all activity from last 24 hours

**Command**:
```bash
# If automated digest not received:
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.morning_digest --preview
```

**Review**:
- [ ] Urgent emails flagged
- [ ] Hot leads from SMS replies
- [ ] New form submissions
- [ ] Today's calendar events
- [ ] Action items list

**Action**: Prioritize items for the day

---

### Step 2: Check SMS Replies (10:00 AM - 15 min)

**Objective**: Respond to leads and maintain campaign momentum

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.twilio_webhook stats
```

**Review**:
- [ ] Hot leads (call within 1 hour)
- [ ] Callback requests (schedule call)
- [ ] Questions (reply with answer)
- [ ] Opt-outs (verify processed)

**Priorities**:
1. **Hot leads**: Call immediately
2. **Callbacks**: Schedule or call within 2 hours
3. **Questions**: Reply same day
4. **Opt-outs**: Verify compliance (must be <1 min processing)

---

### Step 3: Check Form Submissions (10:15 AM - 10 min)

**Objective**: Ensure no inquiry goes unnoticed

**Check**:
1. Google Sheets: `Lead Submissions` (ID: `1AgdGdTLi0E8eZBUZ3yHVCCdVSlXOuxFhOZ7BSXmNbZM`)
2. ClickUp: New tasks in Intake stage

**Review**:
- [ ] New submissions since yesterday
- [ ] Source of submissions (which landing page)
- [ ] Quality of leads (fit for services)

**Action**: Create ClickUp task for qualified leads

---

### Step 4: Webhook Health Check (10:25 AM - 5 min)

**Objective**: Ensure all webhooks are running

**Commands**:
```bash
# Check Twilio webhook
curl http://localhost:5001/health

# Check Form webhook
curl http://localhost:5000/webhook/health
```

**Expected**: `{"status": "healthy", "uptime": "..."}`

**If unhealthy**:
```bash
# Restart webhooks
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.twilio_webhook serve --port 5001 &
python -m src.form_webhook serve --port 5000 &
```

---

## Evening (Optional - 5:00 PM)

### Quick Status Check

**Objective**: Ensure nothing urgent was missed

**Review**:
- [ ] Any new SMS replies since morning
- [ ] Any new form submissions
- [ ] Tomorrow's calendar preview

**Command**:
```bash
python -m src.digest_aggregator --hours 8
```

---

## Quick Reference Commands

```bash
# Generate morning digest
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.morning_digest --preview

# Check SMS stats
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.twilio_webhook stats

# Webhook health
curl http://localhost:5001/health
curl http://localhost:5000/webhook/health

# Record SMS response
python -m src.campaign_analytics response --phone "+1XXX" --category hot_lead

# View today's calendar
python calendar_reminders.py list --days 1
```

---

## Success Criteria

- [ ] Morning digest reviewed before 9 AM
- [ ] Hot leads contacted within 1 hour
- [ ] All SMS questions answered same day
- [ ] Webhooks healthy (no downtime)
- [ ] New form inquiries processed into CRM

---

## Automation Status

| Task | Manual | Automated |
|------|--------|-----------|
| Morning Digest | `--preview` | Email at 8 AM |
| SMS Check | Manual stats | Calendar reminder |
| Form Check | Manual sheet | Auto ClickUp task |
| Webhook Health | curl | Uptime monitoring (future) |

---

## References

- [Webhook Monitoring SOP](../../lead-scraper/workflows/webhook-monitoring-sop.md)
- [Campaign Analytics (SOP 22)](../../../CLAUDE.md#sop-22-campaign-analytics--tracking)
