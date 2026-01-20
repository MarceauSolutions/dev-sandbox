# Automated Outreach System

**Status**: Ready to deploy 🚀

Similar to the social media automation system, this automates cold email and SMS outreach for multiple businesses throughout the day.

---

## System Overview

### Businesses Configured

| Business | Emails/Day | SMS/Day | Target Categories | Pain Points |
|----------|------------|---------|-------------------|-------------|
| **Marceau Solutions** (AI Automation) | 20 | 10 | gym, restaurant, medical | no_website, low_reviews, no_google_listing |
| **SW Florida Comfort HVAC** | 15 | 10 | restaurant, gym, retail | no_website, low_reviews |

### Optimal Send Times (EST)

**Email batches**: 8 AM, 9 AM, 10 AM, 11 AM, 1 PM, 2 PM, 3 PM, 4 PM

**SMS batches**: 9 AM, 3 PM (avoid early morning/late evening)

### Daily Workflow

```
6:00 AM: Schedule today's outreach for both businesses
8:00 AM: Send first email batch
9:00 AM: Send email + SMS batches
...continues throughout business hours...
4:00 PM: Final email batch for the day
```

---

## Setup (One-Time)

### 1. Test the Scheduler

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Check status
python -m src.outreach_scheduler status

# Schedule one day (dry run)
python -m src.outreach_scheduler daily-run --business marceau-solutions

# View what was scheduled
python -m src.outreach_scheduler status
```

### 2. Enrich Restaurant Leads

Before deploying, enrich restaurants that have websites to get owner emails:

```bash
# Enrich 50 restaurants with websites
python -m src.scraper enrich --limit 50

# This uses Apollo to find owner emails from business websites
```

### 3. Deploy Cron Jobs

```bash
bash scripts/setup_outreach_schedule.sh
```

This creates 10 cron jobs:
- 2 for daily scheduling (one per business)
- 8 for processing queue at optimal times

### 4. Verify Deployment

```bash
# Check cron jobs
crontab -l | grep outreach_scheduler

# Should show 10 entries
```

---

## Daily Operations

### Morning Check (Optional)

```bash
# View today's scheduled batches
python -m src.outreach_scheduler status
```

Output:
```
=== Outreach Scheduler Status ===
Total queued: 24
Pending: 16
Sent today: 8

Next batch:
  Business: marceau-solutions
  Type: email
  Count: 5
  Scheduled: 2026-01-20T14:00:00
```

### Monitor Logs

```bash
# View recent outreach activity
tail -50 output/outreach.log

# View all campaigns sent today
cat output/outreach_history.json | jq '.campaigns[] | select(.sent_at | startswith("2026-01-20"))'
```

---

## How It Works

### Email Outreach Flow

1. **6 AM**: Scheduler creates email batches for the day
   - Marceau Solutions: 20 emails across 4 time slots = 5 emails per batch
   - HVAC: 15 emails across 4 time slots = 3-4 emails per batch

2. **8 AM - 4 PM**: Each hour, `process` command runs:
   - Loads leads from database
   - Filters by category + pain point
   - **Auto-enriches** leads with websites (finds owner emails via Apollo)
   - Sends personalized emails using Hormozi templates
   - Logs results to `outreach_history.json`

3. **Skips already contacted** - Won't send duplicate emails

### SMS Outreach Flow

1. **6 AM**: Scheduler creates SMS batches
   - 2 batches per day (9 AM, 3 PM)
   - Each batch = 5 messages

2. **9 AM & 3 PM**: SMS batches sent
   - Only targets leads with `no_website` pain point
   - Uses approved Twilio templates
   - Respects TCPA compliance (8 AM - 9 PM)

---

## Customization

### Change Daily Limits

Edit `src/outreach_scheduler.py`:

```python
BUSINESS_CONFIGS = {
    "marceau-solutions": OutreachConfig(
        emails_per_day=30,  # Change from 20 to 30
        sms_per_day=15,     # Change from 10 to 15
        ...
    )
}
```

### Change Send Times

Edit `src/outreach_scheduler.py`:

```python
"marceau-solutions": OutreachConfig(
    optimal_times=[8, 10, 12, 14, 16],  # Add more slots
    ...
)
```

### Add New Business

```python
"my-new-business": OutreachConfig(
    business_id="my-new-business",
    business_name="My Business Name",
    emails_per_day=10,
    sms_per_day=5,
    optimal_times=[9, 13, 16],
    target_categories=["restaurant"],
    pain_points=["no_website"],
    enrich_first=True
)
```

Then add to cron:
```bash
(crontab -l; echo "10 6 * * * cd $PROJECT_PATH && $PYTHON_PATH -m src.outreach_scheduler daily-run --business my-new-business") | crontab -
```

---

## Expected Results (30 Days)

### Marceau Solutions

- **Emails sent**: ~600 (20/day × 30 days)
- **SMS sent**: ~300 (10/day × 30 days)
- **Cost**: ~$70/month ($24 SMS + $50 Apollo enrichment)
- **Response rate**: 2-5% expected (12-30 replies)

### SW Florida Comfort HVAC

- **Emails sent**: ~450 (15/day × 30 days)
- **SMS sent**: ~300 (10/day × 30 days)
- **Cost**: ~$70/month
- **Response rate**: 3-7% for HVAC (higher urgency)

---

## Safety Features

### Rate Limiting

- Daily limits enforced per business
- Won't exceed configured `emails_per_day` or `sms_per_day`

### Duplicate Prevention

- Checks `outreach_history.json` before sending
- Skips leads already contacted
- Tracks opt-outs from `optout_list.json`

### TCPA Compliance (SMS)

- Only sends 8 AM - 9 PM local time
- Includes "Reply STOP to opt out" in every message
- Requires explicit business phone consent (B2B exemption)

---

## Pause/Resume

### Pause All Outreach

```bash
# Disable cron jobs (but keep them)
crontab -l | sed 's/^/#/' | grep outreach_scheduler | crontab -
```

### Resume Outreach

```bash
# Re-enable cron jobs
crontab -l | sed 's/^#//' | grep outreach_scheduler | crontab -
```

### Stop Completely

```bash
# Remove all outreach cron jobs
crontab -l | grep -v outreach_scheduler | crontab -
```

---

## Integration with Follow-Up Sequences

When leads reply, they automatically enter the 7-touch follow-up sequence (SOP 19):

```
Day 0: Initial outreach (via scheduler)
Day 2: Follow-up #1 (automated)
Day 5: Follow-up #2
Day 10: Follow-up #3
...
Day 60: Final re-engagement
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No emails sending | Check Apollo API key in `.env` |
| SMS failing | Verify Twilio balance and phone number |
| "No leads" warnings | Run `python -m src.scraper enrich --limit 50` to get more emails |
| Duplicate sends | Check `outreach_history.json` - may need to clear old entries |

---

## Files Created

```
projects/lead-scraper/
├── src/
│   └── outreach_scheduler.py          # NEW - Automated scheduler
├── scripts/
│   └── setup_outreach_schedule.sh     # NEW - Cron setup
├── output/
│   ├── outreach_queue.json            # Scheduled batches
│   ├── outreach_history.json          # Sent campaigns
│   └── outreach.log                   # Activity log
└── AUTOMATED-OUTREACH-GUIDE.md        # This file
```

---

## Next Steps

1. **Enrich leads**: `python -m src.scraper enrich --limit 100`
2. **Test scheduler**: `python -m src.outreach_scheduler daily-run --business marceau-solutions`
3. **Review queue**: `python -m src.outreach_scheduler status`
4. **Deploy**: `bash scripts/setup_outreach_schedule.sh`
5. **Monitor**: `tail -f output/outreach.log`

---

**Ready to go live? ✅**

Just run the enrich command, then the cron setup script, and you're automated!
