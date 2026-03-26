# Outreach Monitoring SOP - Daily Operations

**Purpose**: Ensure no leads are missed and all follow-ups happen on schedule using the Hormozi 5-touch strategy.

**Frequency**: Daily (morning routine) + Real-time alerts

---

## Quick Reference Commands

```bash
# Morning dashboard check (daily at 9 AM)
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.campaign_monitor dashboard

# Check overdue follow-ups
python -m src.campaign_monitor overdue

# Daily summary email (automated via cron)
python -m src.campaign_monitor email-summary

# Export status report
python -m src.campaign_monitor export --output output/daily-report-$(date +%Y%m%d).json

# Continuous monitoring (runs every 5 minutes)
python -m src.campaign_monitor watch --interval 300
```

---

## Daily Routine (15 minutes)

### Step 1: Morning Dashboard Check (9:00 AM)

```bash
python -m src.campaign_monitor dashboard
```

**What to Look For**:
- ⚠️ **Critical alerts** at the top (red)
  - Overdue follow-ups (>3 days = critical, 1-3 days = high)
  - Unprocessed replies
- 📊 **Business-by-business status**
  - Response rates (target: >5%)
  - Opt-out rates (alert if >10%)
  - Hot/warm leads
- 📅 **Upcoming follow-ups** (next 24 hours)

---

### Step 2: Process Overdue Follow-Ups (Priority #1)

If dashboard shows overdue follow-ups:

```bash
# View all overdue
python -m src.campaign_monitor overdue

# Process overdue (sends pending Touch 2, 3, 4, 5)
python -m src.follow_up_sequence process --dry-run  # Preview first
python -m src.follow_up_sequence process --for-real # Send if looks good
```

**CRITICAL**:
- Touch 3 is due 5 days after initial outreach
- Hormozi research shows most replies come after Touch 3-5
- Overdue = lost opportunities

**Expected Output**:
```
Processing 85 overdue follow-ups...
  Touch 3: 85 leads (free_mockup template)
  Touch 4: 0 leads
  Touch 5: 0 leads

Dry run complete. Run with --for-real to send.
```

---

### Step 3: Respond to Unprocessed Replies

If dashboard shows unprocessed replies:

```bash
# View all replies
cat output/sms_replies.json | jq '.replies[] | select(.processed == false)'

# Categorize and respond to each
# (Manual process - requires human judgment)
```

**Reply Categories**:
- 🔥 **Hot Lead** - "Yes, interested" / "Tell me more" / "What's the cost?"
  - Action: Create ClickUp task, schedule call
  - Command: `python -m src.crm_sync create-task --phone "+1XXXXXXXXXX" --priority high`

- 🌡️ **Warm Lead** - "Maybe later" / "Send info" / "Call next week"
  - Action: Create ClickUp task with callback date
  - Command: `python -m src.crm_sync create-task --phone "+1XXXXXXXXXX" --callback-date "2026-01-25"`

- ❄️ **Cold Lead** - "Not interested" / "We're good"
  - Action: Mark sequence as completed, no further touches
  - Command: `python -m src.follow_up_sequence mark-response --phone "+1XXXXXXXXXX" --outcome not_interested`

- 🛑 **Opt-Out** - "STOP" / "Remove me" / "Don't contact again"
  - Action: Auto-processed by webhook, verify in Twilio console
  - No action needed (already marked opted_out)

**Mark Response** (stops follow-up sequence):
```bash
python -m src.follow_up_sequence mark-response \
    --phone "+1XXXXXXXXXX" \
    --outcome [hot_lead|warm_lead|not_interested|opted_out]
```

---

### Step 4: Check Response Rates & Opt-Out Rates

**Target Metrics**:
- Response Rate: **5-10%** (good)
- Opt-Out Rate: **<10%** (acceptable), **<5%** (excellent)
- Hot Lead Rate: **1-3%** of total contacted

**If Opt-Out Rate >10%**:
1. PAUSE all outreach immediately
2. Review templates for compliance
3. Check if targeting is too broad (wrong audience)
4. See: `workflows/cold-outreach-strategy-sop.md` for A/B testing

```bash
# View detailed metrics
python -m src.campaign_analytics report
python -m src.campaign_analytics templates  # Compare template performance
```

---

### Step 5: Queue Upcoming Touches (Optional)

Preview what's scheduled for the next 7 days:

```bash
python -m src.follow_up_sequence queue --days 7
```

**Expected Output**:
```
Upcoming Follow-Ups (Next 7 Days):

2026-01-21: 15 touches scheduled
  Touch 3: 12 leads (free_mockup)
  Touch 4: 3 leads (seo_audit)

2026-01-22: 8 touches scheduled
  Touch 3: 8 leads (free_mockup)

...
```

---

## Emergency Procedures

### Emergency: Campaign Stopped Sending

**Symptoms**:
- No messages sent in last 24 hours
- `last_message_sent` timestamp is old

**Diagnosis**:
```bash
# Check Twilio balance
python -c "
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
balance = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch().balance
print(f'Twilio Balance: {balance}')
"

# Check for errors in last campaign
tail -50 output/sms_campaigns.json | jq '.records[] | select(.status == "failed")'
```

**Solutions**:
1. **Low Twilio Balance**: Add funds at https://console.twilio.com/billing
2. **Carrier Block**: Check Twilio console for carrier violations
3. **Rate Limit**: Wait 1 hour, messages queued automatically
4. **Script Error**: Check logs, restart follow_up_sequence processor

---

### Emergency: High Opt-Out Rate (>15%)

**IMMEDIATE ACTION**: STOP all outreach

```bash
# Mark all pending touches as skipped
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

**Root Cause Analysis**:
1. Wrong audience (gyms vs restaurants need different messaging)
2. Template too aggressive
3. Sent outside business hours (8 AM - 9 PM local)
4. Message doesn't match pain point

**Recovery**:
1. Review and fix templates
2. A/B test new messaging (see `cold-outreach-strategy-sop.md`)
3. Segment leads more carefully
4. Resume with small batch (10-20 leads) to test

---

### Emergency: Missed Follow-Ups (>100 overdue)

**Why This Matters**:
- Hormozi data: 60% of responses come after Touch 3-5
- Overdue touches = lost revenue

**Batch Recovery**:
```bash
# Send all overdue in batches (avoid rate limits)
python -m src.follow_up_sequence process --for-real --batch-size 50 --delay 60

# This sends 50 messages, waits 60 seconds, sends next 50, etc.
```

**Prevention**:
Set up daily cron job:
```bash
# Add to crontab (run daily at 9 AM)
crontab -e

# Add this line:
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && python -m src.follow_up_sequence process --for-real >> logs/followup-cron.log 2>&1
```

---

## Automated Monitoring Setup

### Option 1: Daily Email Summary (Recommended)

Add to crontab:
```bash
# Daily summary at 8 AM
0 8 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper && python -m src.campaign_monitor email-summary >> logs/monitor-cron.log 2>&1
```

Email includes:
- Total leads, active sequences
- Overdue follow-ups
- Unprocessed replies
- Business breakdown

---

### Option 2: Continuous Monitoring (Advanced)

Run monitoring dashboard continuously (updates every 5 minutes):

```bash
# Start in background
nohup python -m src.campaign_monitor watch --interval 300 > logs/monitor-watch.log 2>&1 &

# View live log
tail -f logs/monitor-watch.log

# Stop monitoring
pkill -f "campaign_monitor watch"
```

---

## Interpreting the Dashboard

### Sample Dashboard Output

```
================================================================================
CAMPAIGN MONITORING DASHBOARD
Last Updated: 2026-01-21 09:00:00
================================================================================

⚠️  CRITICAL ALERTS
--------------------------------------------------------------------------------

Overdue Follow-Ups: 85
  • Smash Fitness (Touch 3) - 1 days overdue
    Phone: +1 239-331-3581 | Template: free_mockup
  • Athletica Health & Fitness (Touch 3) - 1 days overdue
    Phone: +1 239-276-7160 | Template: free_mockup
  ...

Unprocessed Replies: 2
  • Velocity Naples Indoor Cycling (opt_out) - 15.5h ago
    "we have a website STOP"
  • CrossFit Naples (opt_out) - 16.2h ago
    "This is an automated message from CrossFit Naples..."

--------------------------------------------------------------------------------

CAMPAIGN STATUS BY BUSINESS
--------------------------------------------------------------------------------

All Campaigns (Legacy) (all)
  Total Leads: 138 | Active Sequences: 111
  Touch Progress: T1=17 | T2=94 | T3=85 pending
  Replies: 14 (10.1%) | Opt-outs: 14 (10.1%)
  Last Sent: 2026-01-20 08:33:31
  Last Reply: 2026-01-15 21:39:01

📅 UPCOMING (Next 24 Hours): 0

================================================================================
```

### What Each Section Means

**Critical Alerts**:
- RED = Action required NOW
- Overdue >3 days = lost opportunity (Hormozi: most replies after Touch 3)

**Touch Progress**:
- T1 sent = Initial outreach complete
- T2 sent = Follow-up #1 complete (Day 2)
- T3 pending = Follow-up #2 due (Day 5) - **THIS IS KEY TOUCH**

**Response Rate**:
- 10.1% = GOOD (target: 5-10%)
- 14 replies from 138 contacted

**Opt-Out Rate**:
- 10.1% = BORDERLINE (acceptable but watch closely)
- If exceeds 15%, PAUSE campaign

---

## Response Handling Workflow

### Hot Lead Response Flow

```
Reply Received
    ↓
Categorize as Hot Lead
    ↓
Create ClickUp Task (High Priority)
    ↓
Schedule Discovery Call (within 24h)
    ↓
Mark sequence as "converted"
    ↓
Send confirmation SMS
```

**Commands**:
```bash
# Create ClickUp task
python -m src.crm_sync create-task \
    --phone "+1XXXXXXXXXX" \
    --business-name "Smash Fitness" \
    --priority high \
    --notes "Replied: 'Yes, I'm interested in the free mockup'"

# Mark sequence completed
python -m src.follow_up_sequence mark-response \
    --phone "+1XXXXXXXXXX" \
    --outcome hot_lead

# Send confirmation (manual for now)
# "Great! I'll call you at [TIME] tomorrow to discuss..."
```

---

### Opt-Out Response Flow

```
"STOP" Received
    ↓
Twilio Auto-Processes (webhook)
    ↓
Verify in sms_replies.json (category: opt_out)
    ↓
Check sequence marked "opted_out"
    ↓
No further touches sent (automatic)
```

**Verification**:
```bash
# Check opt-out was processed
cat output/sms_replies.json | jq '.replies[] | select(.phone == "+1XXXXXXXXXX")'

# Verify sequence stopped
cat output/follow_up_sequences.json | jq '.sequences[] | select(.phone == "+1XXXXXXXXXX") | .status'
# Should show: "opted_out"
```

---

## Metrics to Track

### Daily Metrics
- [ ] Overdue count (target: 0)
- [ ] Unprocessed replies (target: 0 within 24h)
- [ ] Response rate (target: 5-10%)
- [ ] Opt-out rate (alert if >10%)

### Weekly Metrics
- [ ] Touch distribution (how many at each stage)
- [ ] Template performance (which get best responses)
- [ ] Business performance (which businesses convert best)
- [ ] Conversion rate (replied → scheduled call)

### Monthly Metrics
- [ ] Total leads contacted
- [ ] Total conversations started
- [ ] Total deals closed
- [ ] Revenue per lead
- [ ] Cost per acquisition

**View Metrics**:
```bash
# Weekly summary
python -m src.campaign_analytics report

# Template comparison
python -m src.campaign_analytics templates

# Funnel analysis
python -m src.campaign_analytics funnel
```

---

## Integration with Other Systems

### ClickUp CRM Sync

When hot/warm lead identified:
```bash
python -m src.crm_sync create-task \
    --phone "+1XXXXXXXXXX" \
    --business-name "Business Name" \
    --priority [high|medium] \
    --callback-date "YYYY-MM-DD"
```

### Google Calendar

Schedule discovery calls:
```bash
python -m src.calendar_manager create-event \
    --title "Discovery Call - Business Name" \
    --start "2026-01-22 10:00:00" \
    --duration 30 \
    --attendee "email@business.com"
```

### Twilio Console

Check message delivery status:
- https://console.twilio.com/us1/monitor/logs/sms
- Filter by date, status (failed, delivered)
- Check for carrier violations

---

## Troubleshooting

### Issue: Dashboard Shows 0 Leads

**Cause**: No data files or wrong directory

**Solution**:
```bash
# Check files exist
ls -la output/sms_campaigns.json
ls -la output/follow_up_sequences.json
ls -la output/sms_replies.json

# Verify data in files
head -20 output/sms_campaigns.json
```

---

### Issue: Overdue Count Not Decreasing

**Cause**: `process` command not running or failing

**Solution**:
```bash
# Check for errors
python -m src.follow_up_sequence process --dry-run

# Check logs
cat logs/followup-cron.log

# Manually process
python -m src.follow_up_sequence process --for-real
```

---

### Issue: Replies Not Showing in Dashboard

**Cause**: Webhook not receiving replies or categorization failing

**Solution**:
```bash
# Check webhook server running
curl http://localhost:5001/health

# Check Twilio webhook configured
# https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
# Should point to: https://your-ngrok-url.ngrok.io/sms/reply

# Check raw replies
cat output/sms_replies.json | jq '.replies[]'
```

---

## Best Practices

1. **Check Dashboard DAILY** (9 AM routine)
   - 15 minutes max
   - Process overdue first
   - Respond to hot leads within 24h

2. **Never Let Follow-Ups Go >3 Days Overdue**
   - Hormozi: 60% of conversions happen after Touch 3-5
   - Overdue = lost revenue

3. **Respond to ALL Replies Within 24 Hours**
   - Hot leads get cold fast
   - Even opt-outs deserve acknowledgment (auto-handled)

4. **Monitor Opt-Out Rate Weekly**
   - >10% = investigate
   - >15% = PAUSE and fix

5. **A/B Test Templates Monthly**
   - Use `campaign_optimizer.py` to identify winners
   - Replace low-performers

6. **Back Up Data Weekly**
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz output/*.json
   ```

---

## Success Criteria

✅ **Daily**:
- Overdue count: 0
- Unprocessed replies: 0
- Hot leads responded to within 24h

✅ **Weekly**:
- Response rate: 5-10%
- Opt-out rate: <10%
- All sequences progressing through touches

✅ **Monthly**:
- 3+ hot leads generated
- 1+ deal closed
- ROI positive (revenue > outreach costs)

---

## Related Documentation

- `cold-outreach-sop.md` - How to send initial campaigns
- `multi-touch-followup-sop.md` - How follow-up sequences work
- `cold-outreach-strategy-sop.md` - How to optimize messaging
- `opt-out-management-sop.md` - Compliance and opt-out handling
- `campaign_monitor.py` - Dashboard script reference

---

**Last Updated**: 2026-01-21
**Owner**: William Marceau
**Frequency**: Daily (9 AM check) + Weekly (metrics review)
