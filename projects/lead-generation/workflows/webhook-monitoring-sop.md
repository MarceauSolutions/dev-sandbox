# SOP: Webhook Monitoring & Reply Handling

*Last Updated: 2026-01-15*
*Version: 1.0.0*

**Extends**: [form-webhook-sop.md](form-webhook-sop.md)

## Overview

This SOP covers real-time monitoring of SMS/form webhooks, handling inbound replies, and managing the response pipeline from inquiry to follow-up action.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Twilio SMS     │────▶│  twilio_webhook │────▶│  ClickUp Task   │
│  (Inbound)      │     │  (Port 5001)    │     │  + Notification │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Auto Actions   │
                        │  - Opt-out      │
                        │  - Remove seq   │
                        │  - Log reply    │
                        └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Landing Page   │────▶│  form_webhook   │────▶│  ClickUp Task   │
│  (Email Form)   │     │  (Port 5000)    │     │  + Notification │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Starting the Webhook Servers

### Twilio SMS Webhook (Reply Handler)

```bash
# Terminal 1: Start webhook server
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.twilio_webhook serve --port 5001

# Terminal 2: Expose via ngrok
ngrok http 5001
```

**Configure Twilio:**
1. Go to console.twilio.com
2. Phone Numbers > +1 855 239 9364
3. Messaging > Webhook URL
4. Set to: `https://{ngrok-url}/sms/reply`

### Form Webhook (Landing Page Handler)

```bash
# Terminal 3: Start form webhook
python -m src.form_webhook serve --port 5000

# Terminal 4: Expose via ngrok (if needed)
ngrok http 5000
```

---

## Monitoring Dashboard

### Health Checks

```bash
# Check Twilio webhook
curl http://localhost:5001/health

# Check form webhook
curl http://localhost:5000/webhook/health
```

Expected: `{"status": "healthy", "uptime": "..."}`

### Real-Time Logs

```bash
# Watch Twilio webhook logs
tail -f /Users/williammarceaujr./dev-sandbox/projects/lead-scraper/output/twilio_webhook.log

# Watch form webhook logs
tail -f /Users/williammarceaujr./dev-sandbox/projects/lead-scraper/output/form_submissions.json
```

### Statistics

```bash
# Twilio webhook stats
python -m src.twilio_webhook stats

# Form webhook stats
python -m src.form_webhook stats
```

---

## Reply Classification

### Automatic Classification

The webhook automatically classifies inbound SMS:

| Category | Trigger Words | Action |
|----------|---------------|--------|
| **OPT_OUT** | STOP, UNSUBSCRIBE, CANCEL | Add to opt-out, stop sequence |
| **POSITIVE** | Yes, interested, call me | Create high-priority task |
| **NEGATIVE** | No, not interested, remove | Mark lead cold, stop sequence |
| **QUESTION** | ?, how, what, when, who | Create task for response |
| **CALLBACK** | Call, phone, reach | Create urgent callback task |

### Manual Override

```bash
# Reclassify a reply
python -m src.twilio_webhook reclassify \
    --message-id {sid} \
    --category positive
```

---

## Notification Pipeline

### Immediate Notifications

When a reply is received:

1. **SMS Notification** (if configured):
   ```
   "New reply from Naples Fitness: 'Yes I'm interested in the website...'"
   ```

2. **Email Notification**:
   - Subject: "SMS Reply from {Business Name}"
   - Body: Full message + lead context + suggested action

3. **ClickUp Task**:
   - Title: "Reply: {Business Name} - {Category}"
   - Priority: High for positive, Normal for questions
   - Tags: `sms_reply`, `{category}`

### Notification Configuration

```bash
# Set notification preferences
export NOTIFICATION_PHONE="+1XXXXXXXXXX"
export NOTIFICATION_EMAIL="wmarceau@marceausolutions.com"

# Test notifications
python -m src.twilio_webhook test-notify
python -m src.form_webhook test-notify
```

---

## Response Workflows

### Positive Reply Workflow

When lead shows interest:

1. **Auto-actions**:
   - Remove from follow-up sequence
   - Create high-priority ClickUp task
   - Send notification

2. **Manual follow-up** (William):
   - Call within 24 hours
   - Update ClickUp task with outcome
   - Schedule meeting if appropriate

```bash
# View positive replies needing follow-up
python -m src.twilio_webhook pending-followups --category positive
```

### Opt-Out Workflow

When lead sends STOP:

1. **Auto-actions** (immediate):
   - Add to global opt-out list
   - Remove from ALL active sequences
   - Log compliance action
   - Confirm opt-out via SMS

2. **Verification**:
```bash
# Verify opt-out processed
cat output/optout_list.json | grep "{phone}"
```

### Callback Request Workflow

When lead wants a call:

1. **Auto-actions**:
   - Create urgent ClickUp task
   - Send immediate notification
   - Note best time if mentioned

2. **Manual follow-up**:
   - Call within 1 hour during business hours
   - Document outcome in task

---

## Error Handling

### Webhook Not Receiving Messages

| Symptom | Check | Solution |
|---------|-------|----------|
| No messages arriving | ngrok status | Restart ngrok, update Twilio URL |
| 401 errors in Twilio logs | Auth config | Verify webhook URL is public |
| Messages delayed | Server running? | Check `python -m src.twilio_webhook serve` |

### Duplicate Notifications

```bash
# Check for duplicate processing
cat output/processed_messages.json | grep "{message_sid}"

# If duplicate, message_sid will appear multiple times
```

### Notification Failures

```bash
# Test notification systems
python -m src.twilio_webhook test-notify --channel sms
python -m src.twilio_webhook test-notify --channel email

# Check notification logs
cat output/notification_log.json | tail -20
```

---

## Rollback Procedures

### Stop All Webhooks

```bash
# Kill all webhook processes
pkill -f "twilio_webhook serve"
pkill -f "form_webhook serve"
```

### Reprocess Failed Messages

```bash
# View failed messages
python -m src.twilio_webhook list-failed

# Reprocess specific message
python -m src.twilio_webhook reprocess --message-id {sid}

# Reprocess all failed
python -m src.twilio_webhook reprocess-all
```

### Remove Incorrect Task

If ClickUp task created incorrectly:
1. Archive task (don't delete - audit trail)
2. Update task notes with "Created in error"
3. Check if notification was sent (can't unsend)

---

## Monitoring Checklist

### Daily Checks

- [ ] Both webhook servers running
- [ ] ngrok tunnels active
- [ ] No error logs in past 24h
- [ ] All positive replies have follow-up tasks
- [ ] Opt-outs processed and confirmed

### Weekly Review

- [ ] Reply rate by campaign
- [ ] Category distribution (positive/negative/questions)
- [ ] Average response time to replies
- [ ] Missed or delayed notifications

---

## Success Criteria

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Webhook uptime | >99.9% | <99% |
| Reply processing time | <5 seconds | >30 seconds |
| Notification delivery | 100% | Any failure |
| Opt-out processing | <1 minute | >5 minutes |
| ClickUp task creation | 100% success | Any failure |

---

## Quick Reference

```bash
# Start webhooks
python -m src.twilio_webhook serve --port 5001
python -m src.form_webhook serve --port 5000

# Expose via ngrok
ngrok http 5001  # SMS replies
ngrok http 5000  # Form submissions

# Health checks
curl http://localhost:5001/health
curl http://localhost:5000/webhook/health

# View stats
python -m src.twilio_webhook stats
python -m src.form_webhook stats

# Test notifications
python -m src.twilio_webhook test-notify
python -m src.form_webhook test-notify

# Process opt-out manually
python -m src.twilio_webhook process-optout --phone "+1XXXXXXXXXX"

# View pending follow-ups
python -m src.twilio_webhook pending-followups --category positive
```
