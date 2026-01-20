# SMS Scheduler Setup Guide

## Overview

The SMS Scheduler automates cold outreach at optimal times for maximum response rates while maintaining TCPA compliance.

## Key Features

- **TCPA Compliant**: Sends only during 8 AM - 8 PM (Florida Mini-TCPA)
- **Optimal Timing**: Tuesday-Friday, 9-11 AM peak window
- **Rate Limited**: 25 messages/day by default
- **Opt-out Aware**: Never sends to opted-out contacts

## Time Windows

| Window | Time (EST) | Priority | Best For |
|--------|------------|----------|----------|
| `morning_peak` | 9:00-11:00 AM | ⭐⭐⭐⭐⭐ | Decision-makers, highest conversions |
| `late_morning` | 11:00 AM-12:00 PM | ⭐⭐⭐⭐ | Pre-lunch engagement |
| `afternoon` | 2:00-4:00 PM | ⭐⭐⭐ | Follow-up, re-engagement |
| `evening` | 5:00-7:00 PM | ⭐⭐ | End-of-day catch-up |

## Quick Commands

```bash
# Preview what would be sent
python -m src.sms_scheduler preview

# Run sends manually
python -m src.sms_scheduler run --window morning_peak

# Dry run (preview without sending)
python -m src.sms_scheduler run --dry-run

# Check statistics
python -m src.sms_scheduler stats

# List time windows
python -m src.sms_scheduler windows
```

## Automated Setup (macOS)

### Option 1: launchd (Recommended for macOS)

1. **Copy plist to LaunchAgents:**
```bash
cp config/com.marceausolutions.sms-scheduler.plist ~/Library/LaunchAgents/
```

2. **Load the scheduler:**
```bash
launchctl load ~/Library/LaunchAgents/com.marceausolutions.sms-scheduler.plist
```

3. **Verify it's loaded:**
```bash
launchctl list | grep sms-scheduler
```

4. **To unload (disable):**
```bash
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.sms-scheduler.plist
```

### Option 2: Cron

1. **Generate crontab entries:**
```bash
python -m src.sms_scheduler cron --path /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
```

2. **Add to crontab:**
```bash
crontab -e
# Paste the generated entries
```

## Schedule Configuration

Default schedule (configured in plist):
- **Tuesday-Friday at 9:00 AM EST**
- Sends up to 25 messages per day
- Uses `morning_peak` window (highest priority)

### Customizing the Schedule

Edit `config/com.marceausolutions.sms-scheduler.plist`:

```xml
<!-- Change to 10 AM instead of 9 AM -->
<key>Hour</key>
<integer>10</integer>

<!-- Change daily limit by adding to ProgramArguments -->
<string>--limit</string>
<string>50</string>
```

After editing, reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.sms-scheduler.plist
launchctl load ~/Library/LaunchAgents/com.marceausolutions.sms-scheduler.plist
```

## Monitoring

### Check Logs

```bash
# View latest log
tail -f logs/sms_scheduler.log

# View errors
cat logs/sms_scheduler_error.log
```

### Check Campaign Stats

```bash
python -m src.sms_scheduler stats
```

### Manual Test Run

```bash
# Dry run to see what would be sent
python -m src.sms_scheduler run --dry-run --window morning_peak

# Force run on a non-optimal day (e.g., Monday)
python -m src.sms_scheduler run --force --window morning_peak
```

## Compliance Notes

### Florida Mini-TCPA Requirements

- **Sending Window**: 8:00 AM - 8:00 PM local time
- **Opt-out Handling**: STOP replies automatically processed
- **Rate Limiting**: 1 message per phone number per day

### Best Practices

1. **Never send on weekends** - B2B decision-makers unavailable
2. **Avoid Mondays** - People are overwhelmed catching up
3. **Thursday/Friday = Best** - Decision-making days
4. **9-11 AM = Peak** - Fresh minds, high engagement

## Troubleshooting

### Scheduler Not Running

```bash
# Check if loaded
launchctl list | grep sms-scheduler

# Check logs
cat logs/sms_scheduler_error.log

# Manual test
python -m src.sms_scheduler preview
```

### No Messages Sent

1. Check eligible leads: `python -m src.sms_scheduler preview`
2. Verify Twilio credentials in `.env`
3. Check opt-out list: `cat output/opt_out_list.json`

### All Leads Skipped

- Leads may already be contacted - check `output/sms_campaigns.json`
- Run `python -m src.sms_scheduler stats` to see campaign stats

## Daily Workflow

1. **Morning (9 AM)**: Scheduler automatically sends 25 messages
2. **During Day**: Monitor Twilio for responses
3. **Evening**: Run `python -m src.sms_scheduler stats` to review
4. **Weekly**: Review opt-outs, adjust strategy as needed

## Files

| File | Purpose |
|------|---------|
| `src/sms_scheduler.py` | Main scheduler code |
| `config/com.marceausolutions.sms-scheduler.plist` | macOS launchd config |
| `logs/sms_scheduler.log` | Execution logs |
| `output/sms_schedule.json` | Schedule state |
| `output/sms_campaigns.json` | Campaign records |
