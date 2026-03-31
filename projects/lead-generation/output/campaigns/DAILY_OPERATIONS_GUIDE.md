# Daily Campaign Operations Guide

Quick reference for managing multi-business outreach campaigns.

---

## Morning Routine (8:00 AM - 9:00 AM)

### 1. Check Dashboard
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.campaign_dashboard
```

**Look for**:
- Opt-out rate >2% (red flag - pause campaign)
- Delivery rate <95% (investigate carrier issues)
- Response trends by touch

### 2. Process Due Follow-Ups
```bash
# Preview what's scheduled today
python -m src.follow_up_sequence queue --days 1

# Process follow-ups (live)
python -m src.follow_up_sequence process --for-real --limit 100
```

### 3. Mark Responses
Check SMS inbox for replies, then:
```bash
# Interested response
python -m src.follow_up_sequence response "+12393985676" --type responded --notes "Interested in demo"

# Booked meeting
python -m src.follow_up_sequence response "+12393985676" --type converted --notes "Demo scheduled for Jan 25"

# Not interested
python -m src.follow_up_sequence response "+12393985676" --type responded --notes "Not interested right now"

# Opt-out (auto-handled, but can manually mark)
python -m src.follow_up_sequence response "+12393985676" --type opted_out
```

---

## Launch New Batch (As Needed)

### Southwest Florida Comfort (HVAC)
```bash
# Small batch (10 leads) - test first
python -m src.launch_multi_business_campaigns --business swflorida-hvac --for-real --limit 10

# Full batch (50 leads)
python -m src.launch_multi_business_campaigns --business swflorida-hvac --for-real --limit 50
```

### Marceau Solutions (Automation)
```bash
# Small batch (20 leads)
python -m src.launch_multi_business_campaigns --business marceau-solutions --for-real --limit 20

# Full batch (100 leads)
python -m src.launch_multi_business_campaigns --business marceau-solutions --for-real --limit 100
```

---

## Check Campaign Status

### Quick Status
```bash
python -m src.launch_multi_business_campaigns --status
```

**Output**:
```json
{
  "swflorida-hvac": {
    "business_name": "Southwest Florida Comfort",
    "status": "active",
    "launched_at": "2026-01-21T12:00:00",
    "stats": {
      "sent": 50,
      "enrolled_in_sequence": 50
    }
  },
  "follow_up_sequences": {
    "total_sequences": 150,
    "response_rate": 5.3,
    "conversion_rate": 1.2
  }
}
```

### Full Dashboard
```bash
# All campaigns
python -m src.campaign_dashboard

# Specific business
python -m src.campaign_dashboard --business swflorida-hvac
python -m src.campaign_dashboard --business marceau-solutions

# Export to JSON for reporting
python -m src.campaign_dashboard --export dashboard_$(date +%Y%m%d).json
```

---

## Troubleshooting

### High Opt-Out Rate (>2%)

**Check**:
```bash
python -m src.campaign_dashboard --business <business_id>
```

**If opt-out rate >2%**:
1. Pause new sends (don't launch new batches)
2. Review recent message templates
3. Check if messages are too salesy or aggressive
4. Refine targeting (maybe wrong audience)

**Resume**:
After fixing templates, start with small test batch (10 leads).

### Low Response Rate (<3%)

**Possible causes**:
- Wrong target audience (no pain point fit)
- Message not compelling
- Offer not valuable enough
- Sent during wrong time

**Test**:
```bash
# A/B test new message variant
# Edit templates in campaign config, then launch small batch
python -m src.launch_multi_business_campaigns --business <id> --for-real --limit 10
```

### Messages Not Sending

**Check Twilio**:
1. Visit: https://console.twilio.com/us1/monitor/logs/sms
2. Look for errors: carrier blocks, invalid numbers, low balance

**Check balance**:
```bash
# Check .env for Twilio credentials
grep TWILIO /Users/williammarceaujr./dev-sandbox/.env
```

**Verify phone number active**:
- Twilio Phone: +1 855 239 9364
- Should be "Active" status in console

---

## Weekly Review (Mondays, 9:00 AM)

### 1. Export Dashboard Data
```bash
python -m src.campaign_dashboard --export weekly_report_$(date +%Y%m%d).json
```

### 2. Analyze Metrics

**Key Questions**:
- Which business has better response rate?
- Which touch (1, 2, or 3) drives most responses?
- Cost per conversion acceptable?
- Should we adjust budget up/down?

### 3. Optimize Templates

**If Touch 2 has low response**:
- Test new question hook
- Try different angle (social proof vs scarcity)

**If Touch 3 has high response**:
- Maybe send breakup message earlier (Day 5 instead of Day 7)

### 4. Plan Next Batch

**Criteria to launch more**:
- ✅ Response rate ≥5%
- ✅ Opt-out rate <2%
- ✅ Budget remaining
- ✅ No carrier violations

---

## Monthly Tasks (1st of Month)

### 1. Calculate ROI
```bash
# Export full month data
python -m src.campaign_dashboard --export monthly_$(date +%Y%m).json
```

**Metrics**:
- Total spent (messages × $0.0079)
- Total conversions (demos/audits booked)
- Revenue from conversions
- ROI = (Revenue - Cost) / Cost

### 2. Refresh Lead List

**If using existing leads**:
- Check for new scraped leads
- Re-score leads based on updated criteria

**If using Apollo**:
- Run new search for industries/geography
- Filter out previous contacted leads
- Enrich top 20%

### 3. Budget Adjustment

**Scale up if**:
- ROI >3x
- Response rate consistent
- Opt-out rate low
- Demand for demos/audits high

**Scale down if**:
- ROI <2x
- Response rate declining
- Lead quality poor

---

## Response Handling Workflow

### When Lead Responds "YES"

1. **Mark in system**:
```bash
python -m src.follow_up_sequence response "<phone>" --type responded --notes "Interested - wants demo"
```

2. **Schedule meeting**:
- Send calendar invite
- Add to CRM (if integrated)

3. **Send confirmation**:
Manual reply (or automated webhook):
```
Thanks! I'll send you a calendar invite for our demo. Looking forward to showing you how we can help.
- William
```

### When Lead Responds "STOP"

**Auto-handled by opt_out_manager.py**, but verify:
```bash
# Check opt-out list
python -m src.opt_out_manager list
```

### When Lead Asks Questions

**Common questions & responses**:

**Q: "How much does this cost?"**
```
Great question! Let's hop on a quick 15-min call so I can understand your
needs and give you accurate pricing. What's your availability this week?
```

**Q: "Can you send me more info?"**
```
Absolutely! I'll text you a link to our case study. But honestly, a 10-min
demo shows it better than any doc. Want to schedule?
```

**Q: "Not interested right now"**
```
No worries! If anything changes, feel free to reach out. I'll remove you
from follow-ups. Thanks for your time!
```
Then mark:
```bash
python -m src.follow_up_sequence response "<phone>" --type responded --notes "Not interested"
```

---

## Emergency Procedures

### High Complaint Rate

**If multiple STOP messages or carrier warnings**:

1. **Immediate pause**:
```bash
# Don't launch new batches
# Let existing sequences complete
```

2. **Review templates**:
- Too aggressive?
- Wrong audience?
- Messaging unclear?

3. **Contact Twilio support**:
- Check for carrier blocks
- Review compliance

### Twilio Account Suspended

**Causes**:
- TCPA violations
- High spam complaint rate
- Carrier blocks

**Actions**:
1. Contact Twilio support immediately
2. Provide campaign details (B2B, opt-out included)
3. Pause all campaigns until resolved

---

## Quick Command Reference

```bash
# PROJECT ROOT
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# DASHBOARD
python -m src.campaign_dashboard
python -m src.campaign_dashboard --business swflorida-hvac
python -m src.campaign_dashboard --export report.json

# LAUNCH CAMPAIGNS
python -m src.launch_multi_business_campaigns --status
python -m src.launch_multi_business_campaigns --dry-run --limit 5
python -m src.launch_multi_business_campaigns --business swflorida-hvac --for-real --limit 50
python -m src.launch_multi_business_campaigns --business marceau-solutions --for-real --limit 100

# FOLLOW-UPS
python -m src.follow_up_sequence queue --days 7
python -m src.follow_up_sequence process --dry-run
python -m src.follow_up_sequence process --for-real
python -m src.follow_up_sequence response "+12393985676" --type responded
python -m src.follow_up_sequence status

# OPT-OUTS
python -m src.opt_out_manager list
python -m src.opt_out_manager check "+12393985676"
```

---

**Last Updated**: January 21, 2026
**Owner**: William Marceau
**Support**: See `/projects/shared/lead-scraper/workflows/` for detailed SOPs
