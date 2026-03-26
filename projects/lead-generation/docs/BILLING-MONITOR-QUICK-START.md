# Google Cloud Billing Monitor - Quick Start Guide

**Last Updated:** 2026-01-21

---

## TL;DR - Get Started in 5 Minutes

```bash
# 1. Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# 2. Test the monitor (manual check)
python -m src.google_cloud_cost_monitor

# 3. Set up automated daily monitoring
bash setup_billing_monitor_cron.sh

# 4. Verify setup
tail -f /tmp/google-billing-monitor.log
```

**Done!** You'll now receive SMS alerts when billing thresholds are exceeded.

---

## What This Does

**Automated billing alerts to prevent surprise charges:**

| Threshold | Alert | Action |
|-----------|-------|--------|
| **$10** | Email only | Monitor closely |
| **$25** | Email + SMS | Review usage |
| **$50** | Email + SMS (urgent) | Optimize immediately |
| **$100** | Email + SMS + Critical alert | Consider disabling APIs |

**How it works:**
1. Script runs daily at 9:00 AM (via cron/launchd)
2. Checks current Google Cloud spend
3. Compares against budget thresholds
4. Sends SMS alert if threshold exceeded
5. Logs trends to `output/google_cloud_billing_log.json`

---

## Commands Reference

### Manual Checks

```bash
# Standard check with SMS alerts
python -m src.google_cloud_cost_monitor

# Check without sending SMS (just print report)
python -m src.google_cloud_cost_monitor --no-sms

# Test SMS alert (without checking billing)
python -m src.google_cloud_cost_monitor --test-sms

# Custom budget
python -m src.google_cloud_cost_monitor --budget 50
```

### Cron Management (macOS)

```bash
# Check if cron is running
launchctl list | grep google-billing-monitor

# Start job manually (for testing)
launchctl start com.marceausolutions.google-billing-monitor

# View logs
tail -f /tmp/google-billing-monitor.log
tail -f /tmp/google-billing-monitor.error.log

# Disable monitoring
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist

# Re-enable monitoring
launchctl load ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist
```

### Cron Management (Linux)

```bash
# View cron jobs
crontab -l

# Edit cron jobs
crontab -e

# View logs
tail -f /tmp/google-billing-monitor.log
```

---

## Alert Levels Explained

### NONE (< $10)
- ✅ Normal usage
- No alerts sent
- Report logged daily

### LOW ($10 - $24.99)
- ℹ️ Early warning
- Email notification only
- Continue monitoring

### MEDIUM ($25 - $49.99)
- ⚠️ 25% of budget used
- Email + SMS alert
- Review API usage, check for inefficiencies

### HIGH ($50 - $99.99)
- 🚨 50% of budget used
- Urgent SMS alert
- Investigate immediately, optimize or pause campaigns

### CRITICAL ($100+)
- 🔴 Budget exhausted
- Critical alert + SMS
- Consider disabling APIs to prevent overage

---

## Troubleshooting

### "No SMS received"

**Check Twilio credentials:**
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Account SID:', os.getenv('TWILIO_ACCOUNT_SID'))
print('From:', os.getenv('TWILIO_PHONE_NUMBER'))
print('To:', os.getenv('NOTIFICATION_PHONE'))
"
```

**Test Twilio directly:**
```bash
python -m src.google_cloud_cost_monitor --test-sms
```

**Check Twilio Console:**
- https://console.twilio.com/us1/monitor/logs/sms
- Look for failed messages

### "Cron not running"

**macOS (launchd):**
```bash
# Check status
launchctl list | grep google-billing-monitor

# If not listed, reload
launchctl load ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist

# Check logs for errors
cat /tmp/google-billing-monitor.error.log
```

**Linux (cron):**
```bash
# Check cron is running
sudo systemctl status cron

# View crontab
crontab -l
```

### "Script errors"

**Check dependencies installed:**
```bash
pip install twilio google-cloud-billing google-cloud-pubsub python-dotenv
```

**Run script manually to see errors:**
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.google_cloud_cost_monitor --once
```

---

## Integration with Google Cloud Console

**For full setup including Google Cloud Console configuration:**

See: `/docs/GOOGLE-CLOUD-BILLING-ALERTS-SETUP.md`

**Key steps:**
1. Create budget in Google Cloud Console
2. Set alert thresholds (10%, 25%, 50%, 100%)
3. Configure Pub/Sub topic for real-time alerts
4. Set API quotas to prevent runaway costs
5. Enable Cloud Billing API (for advanced monitoring)

---

## Files Created

| File | Purpose |
|------|---------|
| `/docs/GOOGLE-CLOUD-BILLING-ALERTS-SETUP.md` | Complete setup guide with screenshots |
| `src/google_cloud_cost_monitor.py` | Automated cost monitoring script |
| `setup_billing_monitor_cron.sh` | One-click cron/launchd setup |
| `output/google_cloud_billing_log.json` | Historical cost tracking |
| `BILLING-MONITOR-QUICK-START.md` | This file (quick reference) |

---

## What's Next?

### Immediate (Today)
1. ✅ Run manual test: `python -m src.google_cloud_cost_monitor`
2. ✅ Verify SMS alerts work: `python -m src.google_cloud_cost_monitor --test-sms`
3. ✅ Set up cron: `bash setup_billing_monitor_cron.sh`

### This Week
4. ✅ Create budget in Google Cloud Console (see full guide)
5. ✅ Set API quotas (1,000 requests/day)
6. ✅ Configure Pub/Sub for real-time alerts (optional)

### Ongoing
7. ✅ Review daily logs: `tail -f /tmp/google-billing-monitor.log`
8. ✅ Optimize API usage if alerts triggered (see cost analysis guide)
9. ✅ Monitor trends: `output/google_cloud_billing_log.json`

---

## Cost Optimization Resources

**If you receive HIGH or CRITICAL alerts:**

See: `/docs/GOOGLE-CLOUD-COST-ANALYSIS.md`

**Quick wins (90% cost reduction):**
1. Implement caching (80% reduction)
2. Use Yelp API as primary source (70% reduction)
3. Reduce search radius from 25km to 10km (30% reduction)
4. Remove atmosphere fields from API requests (33% reduction)

---

## Support

**Questions or issues?**

1. Check logs: `/tmp/google-billing-monitor.log` and `/tmp/google-billing-monitor.error.log`
2. Review full guide: `/docs/GOOGLE-CLOUD-BILLING-ALERTS-SETUP.md`
3. Check cost analysis: `/docs/GOOGLE-CLOUD-COST-ANALYSIS.md`

---

**You're all set!** 🎉

Your billing is now monitored 24/7 with automated SMS alerts.
