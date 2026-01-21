# SOP: SMS Campaign Execution

*Last Updated: 2026-01-15*
*Version: 1.0.0*

**Extends**: [cold-outreach-sop.md](cold-outreach-sop.md)

## Overview

This SOP covers SMS-specific campaign execution, including template approval workflows, compliance requirements, and Twilio integration details. Use this SOP in conjunction with the main cold outreach SOP.

## Prerequisites

All prerequisites from `cold-outreach-sop.md` PLUS:

| Requirement | Check Command | Expected Result |
|-------------|---------------|-----------------|
| **Twilio account** | Login to console.twilio.com | Account active |
| **Twilio balance** | Check console > Billing | >$10 balance |
| **Phone number** | `grep TWILIO_PHONE_NUMBER .env` | +1 number set |
| **Templates approved** | Check approved_templates.json | William's approval |

---

## Template Approval Workflow

### Step 1: Draft Templates

Templates are stored in `src/templates/sms_templates.py`:

```python
TEMPLATES = {
    "no_website_intro": {
        "message": "Hi, this is William. I noticed {business_name} doesn't have a website...",
        "chars": 158,
        "compliance": ["opt_out_included", "sender_identified"]
    }
}
```

### Step 2: Request Approval

Before any campaign, present templates to William for review:

| Template | Message | Chars | Status |
|----------|---------|-------|--------|
| `template_name` | "Full message text..." | XXX | ⏳ Pending |

**Approval criteria:**
- [ ] Under 160 chars (single SMS segment)
- [ ] STOP opt-out included
- [ ] No spam trigger words
- [ ] Personalization variables correct
- [ ] Compliant with TCPA/carrier rules

### Step 3: Document Approval

Once approved, record in `output/approved_templates.json`:

```json
{
  "approved": [
    {
      "template": "no_website_intro",
      "approved_by": "William",
      "approved_date": "2026-01-15",
      "notes": "Approved as-is"
    }
  ]
}
```

---

## SMS Compliance Requirements

### TCPA Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Consent** | B2B exemption for business numbers |
| **Identification** | "This is William" in every message |
| **Opt-out** | "Reply STOP to opt out" required |
| **Time restrictions** | No messages before 8am or after 9pm local |

### Carrier Compliance

**Do NOT include:**
- ALL CAPS words (spam signal)
- Multiple exclamation marks!!!
- URL shorteners (bit.ly, etc.)
- "Free" or "Winner" language
- Excessive urgency ("ACT NOW")

**DO include:**
- Business name personalization
- Clear sender identification
- Legitimate opt-out mechanism

---

## Campaign Execution

### Step 1: Verify Template Approved

```bash
cat output/approved_templates.json | grep "template_name"
# Must show approval entry
```

### Step 2: Dry Run (Required)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.scraper sms --dry-run --limit 5 --template no_website_intro
```

**Review output for:**
- [ ] Message renders correctly
- [ ] Personalization variables populated
- [ ] Character count within limit
- [ ] No formatting errors

### Step 3: Small Batch Test

```bash
# Send to 10 leads first
python -m src.scraper sms --for-real --limit 10 --pain-point no_website
```

**Wait 24 hours and check:**
- [ ] Messages delivered (Twilio logs)
- [ ] No carrier violations
- [ ] Any STOP responses handled

### Step 4: Full Campaign

```bash
# Only after small batch succeeds
python -m src.scraper sms --for-real --limit 100 --pain-point no_website
```

---

## Monitoring During Campaign

### Real-Time Twilio Console

Monitor at: https://console.twilio.com/us1/monitor/logs/sms

Watch for:
- **Delivery failures**: Bad numbers, carrier blocks
- **STOP responses**: Auto-added to opt-out list
- **Error codes**: 30003 (unreachable), 30005 (unknown)

### Webhook for Replies

Ensure Twilio webhook is running:

```bash
# Terminal 1: Start webhook
python -m src.twilio_webhook serve --port 5001

# Terminal 2: Expose via ngrok
ngrok http 5001
```

Configure Twilio: Phone Numbers > Your Number > Messaging > Webhook URL

---

## Cost Tracking

### Per-Message Costs

| Segment | Cost |
|---------|------|
| Outbound SMS (US) | ~$0.0079 |
| Inbound SMS (reply) | ~$0.0079 |
| Phone number/month | ~$1.15 |

### Campaign Cost Estimation

```
100 messages × $0.0079 = $0.79
Expected 5% reply rate = 5 replies × $0.0079 = $0.04
Total campaign cost ≈ $0.83
```

### Budget Alerts

Set up in Twilio Console > Billing > Usage Triggers:
- Alert at $10 spent
- Alert at $25 spent
- Hard stop at $50

---

## Troubleshooting

### Message Not Delivered

| Error Code | Meaning | Solution |
|------------|---------|----------|
| 30003 | Unreachable | Phone disconnected/invalid |
| 30005 | Unknown destination | Number doesn't exist |
| 30006 | Landline | Remove from mobile list |
| 30007 | Carrier violation | Review message content |
| 21211 | Invalid number | Fix E.164 formatting |

### Carrier Filtering

If messages blocked:
1. Review message for spam triggers
2. Reduce sending rate (max 1/second)
3. Consider A2P 10DLC registration for high volume

### Opt-Out Not Working

```bash
# Manually process opt-out
python -m src.twilio_webhook process-optout --phone "+1XXXXXXXXXX"

# Verify in opt-out list
cat output/optout_list.json | grep "XXXXXXXXXX"
```

---

## Success Criteria

| Metric | Target | Red Flag |
|--------|--------|----------|
| Delivery rate | >95% | <90% (number quality issue) |
| Reply rate | 2-5% | <1% (template issue) |
| Opt-out rate | <2% | >5% (compliance concern) |
| Callback rate | 1-2% | 0% after 100 sends |

### End-to-End Validation

- [ ] Template approved by William
- [ ] Dry run successful
- [ ] Small batch (10) delivered without issues
- [ ] Webhook receiving replies
- [ ] Opt-outs automatically processed
- [ ] Cost within budget

---

## Quick Reference Commands

```bash
# Dry run
python -m src.scraper sms --dry-run --limit 10 --template no_website_intro

# Send to pain point segment
python -m src.scraper sms --for-real --limit 100 --pain-point no_website

# Check campaign stats
python -m src.scraper sms stats

# Process opt-out manually
python -m src.twilio_webhook process-optout --phone "+1XXXXXXXXXX"

# Start reply webhook
python -m src.twilio_webhook serve --port 5001
```
