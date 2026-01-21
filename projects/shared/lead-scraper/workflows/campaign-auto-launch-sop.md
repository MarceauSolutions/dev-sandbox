# SOP: Automated Campaign Launch

**Version**: 1.0.0
**Created**: 2026-01-21
**Last Updated**: 2026-01-21

## Overview

Automated SMS campaign launch system for Southwest Florida Comfort (HVAC) and Marceau Solutions (AI Automation) that runs like X posting automation - scheduled, monitored, and fully autonomous.

## Use Cases

- Daily automated lead discovery + outreach
- Multi-business campaign management
- Follow-up sequence enrollment
- Response tracking and analytics
- Cost/quota enforcement

## Prerequisites

| Requirement | Check | Expected |
|-------------|-------|----------|
| Twilio account | `echo $TWILIO_ACCOUNT_SID` | Set |
| Twilio balance | Check Twilio Console | >$10 |
| Campaign configs | `ls output/campaigns/*.json` | 2 files |
| Lead database | `ls output/leads.json` | Exists |
| Templates | `ls templates/sms/optimized/*.json` | 12+ files |

## Campaign Schedules

### Southwest Florida Comfort (HVAC Voice AI)
- **Monday 8 AM** - 50 leads
- **Wednesday 8 AM** - 50 leads
- **Friday 8 AM** - 50 leads
- **Total**: 150 leads/week, 600/month
- **Cost**: ~$11.85/week, ~$47.40/month

### Marceau Solutions (AI Automation)
- **Tuesday 8 AM** - 100 leads
- **Thursday 8 AM** - 100 leads
- **Saturday 10 AM** - 50 leads
- **Total**: 250 leads/week, 1,000/month
- **Cost**: ~$19.75/week, ~$79/month

## Installation

### Step 1: Test Dry Run

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Test single business dry run
python -m src.campaign_auto_launcher --business swflorida-hvac --dry-run --limit 5

# Test both businesses dry run
python -m src.campaign_auto_launcher --dry-run --limit 5

# Check integrations
python -m src.campaign_auto_launcher --check-integrations
```

**Expected Output**:
- ✅ Pre-flight checks pass
- ✅ Leads discovered/loaded
- ✅ Messages generated (not sent)
- ✅ Sequences previewed (not created)

### Step 2: Small Batch Test (REAL sends)

```bash
# Test with 3 real sends
python -m src.campaign_auto_launcher --business swflorida-hvac --for-real --limit 3

# Monitor results
tail -f output/logs/campaign-launcher.log
```

**Verify**:
- SMS delivered (check Twilio console)
- Leads enrolled in sequences
- No errors in logs

### Step 3: Install Launchd (macOS)

```bash
# Create log directory
mkdir -p output/logs

# Copy plist to LaunchAgents
cp launchd/com.marceausolutions.campaign-launcher.plist ~/Library/LaunchAgents/

# Load the agent
launchctl load ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist

# Verify loaded
launchctl list | grep campaign-launcher
```

### Step 4: Test Manual Trigger

```bash
# Trigger manually (tests scheduler without waiting)
launchctl start com.marceausolutions.campaign-launcher

# Watch logs
tail -f output/logs/campaign-launcher.log
```

## Usage

### Manual Campaign Launches

```bash
# Dry run (preview)
python -m src.campaign_auto_launcher --dry-run

# Launch Southwest Florida Comfort only
python -m src.campaign_auto_launcher --business swflorida-hvac --for-real

# Launch Marceau Solutions only
python -m src.campaign_auto_launcher --business marceau-solutions --for-real

# Launch both businesses
python -m src.campaign_auto_launcher --for-real

# Limited batch (testing)
python -m src.campaign_auto_launcher --business swflorida-hvac --limit 10 --for-real
```

### Scheduler Management

```bash
# Check if scheduler loaded
launchctl list | grep campaign-launcher

# Unload scheduler (pause automation)
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist

# Reload scheduler (resume automation)
launchctl load ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist

# Trigger manual run
launchctl start com.marceausolutions.campaign-launcher
```

### Log Monitoring

```bash
# Watch live campaign launches
tail -f output/logs/campaign-launcher.log

# View errors only
tail -f output/logs/campaign-launcher-error.log

# Check recent launches
tail -50 output/logs/campaign-launcher.log | grep "CAMPAIGN COMPLETE"
```

### Follow-Up Sequence Management

```bash
# Check what's due today
python -m src.follow_up_sequence queue --days 0

# Process due follow-ups (dry run)
python -m src.follow_up_sequence process --dry-run

# Process due follow-ups (send)
python -m src.follow_up_sequence process --for-real

# Status report
python -m src.follow_up_sequence status
```

## Safeguards

### Built-in Protections

1. **Daily Quota Enforcement**
   - HVAC: Max 50 SMS/day
   - Marceau: Max 100 SMS/day
   - Tracked in `output/daily_campaign_limits.json`

2. **Pre-flight Health Checks**
   - Twilio API status
   - Twilio balance >$10
   - Apollo MCP availability
   - Webhook server status

3. **Rate Limiting**
   - 2 seconds between SMS sends
   - 30 API calls/minute max

4. **Error Handling**
   - Auto-pause after 5 consecutive errors
   - Auto-pause if error rate >20%

5. **Cost Limits**
   - Max $1/day per business
   - Max $5/day total across all

### Manual Safeguards

**Pause automation**:
```bash
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist
```

**Emergency stop**:
```bash
# Kill any running campaign processes
pkill -f campaign_auto_launcher
```

## Monitoring

### Daily Health Check

```bash
# Check campaign status
python -m src.launch_multi_business_campaigns --status

# Check follow-up sequences
python -m src.follow_up_sequence status

# Check quota usage
cat output/daily_campaign_limits.json
```

**Expected Daily Output**:
```json
{
  "2026-01-21": {
    "swflorida-hvac": 48,
    "marceau-solutions": 97
  }
}
```

### Weekly Review

```bash
# Count total SMS sent this week
grep "CAMPAIGN COMPLETE" output/logs/campaign-launcher.log | grep "2026-01-" | wc -l

# Check error rate
grep "ERROR" output/logs/campaign-launcher-error.log | wc -l

# Review response rates (when Agent 2 analytics available)
python -m src.campaign_analytics report --period week
```

## Troubleshooting

### Campaign Didn't Launch

**Check scheduler status**:
```bash
launchctl list | grep campaign-launcher
```

**If not loaded**:
```bash
launchctl load ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist
```

**Check logs**:
```bash
tail -20 output/logs/campaign-launcher-error.log
```

### Daily Quota Reached Early

**Check quota file**:
```bash
cat output/daily_campaign_limits.json
```

**Reset quota** (use with caution):
```bash
# Edit file, change today's count to 0
nano output/daily_campaign_limits.json
```

### SMS Not Delivering

**Check Twilio balance**:
```bash
# Go to: https://console.twilio.com/us1/billing/manage-billing/billing-overview
```

**Check Twilio logs**:
```bash
# Go to: https://console.twilio.com/us1/monitor/logs/sms
```

**Check phone number health**:
```bash
# Verify phone number not flagged for spam
# Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active
```

### Pre-flight Check Failures

**Twilio balance low**:
```bash
# Add funds: https://console.twilio.com/us1/billing/manage-billing/billing-overview
```

**Apollo MCP unavailable**:
```bash
# Check if Apollo MCP server running
# For now, uses existing leads (fallback)
```

**Webhook not running**:
```bash
# Start webhook server (when Agent 4 complete)
python -m src.webhook_server --port 5001
```

## Integration with Other Agents

### Agent 1: Health Checks

**When available**, replace placeholders in `campaign_auto_launcher.py`:
```python
from .health_checks import check_system_health

def check_health_agent1():
    return check_system_health()
```

### Agent 2: Analytics Tracking

**When available**, replace placeholders:
```python
from .campaign_analytics import track_campaign_launch, update_metrics

def track_campaign_launch_agent2(campaign_id, business_id, leads_targeted, template):
    track_campaign_launch(campaign_id, business_id, leads_targeted, template)
```

### Agent 3: Apollo MCP

**When available**, replace placeholders:
```python
# Use Apollo MCP via run_full_outreach_pipeline tool
# or direct Apollo API integration
```

### Agent 4: Webhook

**When available**, replace placeholders:
```python
from .webhook_processor import fetch_responses, check_webhook_health

def fetch_responses_agent4(campaign_id, since):
    return fetch_responses(campaign_id, since)
```

## Success Criteria

### Campaign Execution
- ✅ Daily launches succeed 90%+ of time
- ✅ Delivery rate >95%
- ✅ Error rate <5%
- ✅ Daily quotas met consistently

### Business Results
- ✅ Response rate >5% (target: 8%)
- ✅ Opt-out rate <2%
- ✅ 5+ booked demos/month per business
- ✅ Conversion rate >20% (demo → customer)

### System Reliability
- ✅ Uptime >99% (scheduled launches execute)
- ✅ No runaway spending (stays within budget)
- ✅ Logs clean (minimal errors)

## Next Steps

1. **Week 1**: Dry-run testing with all integrations
2. **Week 2**: Small batch testing (3-5 sends/day)
3. **Week 3**: Medium batch testing (10-20 sends/day)
4. **Week 4**: Full automation activation (scheduler enabled)

## Related Documentation

- Campaign configurations: `output/campaigns/*.json`
- SMS templates: `templates/sms/optimized/*.json`
- Follow-up sequences: `src/follow_up_sequence.py`
- Multi-business launcher: `src/launch_multi_business_campaigns.py`
- Agent 5 full plan: `AGENT-5-CAMPAIGN-AUTOMATION-PLAN.md`

---

**Last Updated**: 2026-01-21
**Maintained By**: Agent 5 (Campaign Automation Architect)
