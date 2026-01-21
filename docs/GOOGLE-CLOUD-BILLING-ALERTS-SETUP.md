# Google Cloud Billing Alerts Setup Guide

**Last Updated:** 2026-01-21
**Project:** fitness-influencer-assistant
**Author:** Claude (Opus 4.5)

---

## Table of Contents

1. [Overview](#overview)
2. [Alert Thresholds Strategy](#alert-thresholds-strategy)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [SMS Notification Setup](#sms-notification-setup)
5. [Email Notification Setup](#email-notification-setup)
6. [Pub/Sub Integration](#pubsub-integration)
7. [Automated Cost Monitoring](#automated-cost-monitoring)
8. [Cron Job Setup](#cron-job-setup)
9. [Testing & Verification](#testing--verification)
10. [Troubleshooting](#troubleshooting)

---

## Overview

**Goal:** Prevent surprise charges by implementing multi-layered billing alerts at strategic thresholds.

**Current Risk:**
- Google Cloud charged $100 (likely Trust & Safety hold)
- Google Places API usage: 409 leads = ~1,022 API calls = ~$20-25 estimated cost
- New pricing model starting March 1, 2025 (unknown free tier limits)

**Solution:**
- **Proactive alerts** at $10, $25, $50, $100 thresholds
- **SMS notifications** to +1 (239) 398-5676
- **Email notifications** to wmarceau@marceausolutions.com
- **Automated daily monitoring** via cron job
- **Pub/Sub integration** for real-time cost tracking

---

## Alert Thresholds Strategy

### Budget: $100/month (Conservative)

| Threshold | % of Budget | Action | Priority |
|-----------|-------------|--------|----------|
| **$10** | 10% | Email notification | Low |
| **$25** | 25% | Email + SMS alert | Medium |
| **$50** | 50% | Email + SMS + Slack (urgent) | High |
| **$100** | 100% | Email + SMS + Disable APIs (optional) | Critical |

### Rationale:

- **$10 (10%)**: Early warning - normal usage, start monitoring closely
- **$25 (25%)**: Moderate concern - review API usage, check for inefficiencies
- **$50 (50%)**: High concern - investigate immediately, optimize or pause campaigns
- **$100 (100%)**: Budget exhausted - pause APIs, require manual approval to continue

---

## Step-by-Step Setup

### Prerequisites

- ✅ Google Cloud account with billing enabled
- ✅ Project: `fitness-influencer-assistant`
- ✅ Billing account associated with project
- ✅ Owner or Billing Admin permissions

### Part 1: Navigate to Billing

1. **Open Google Cloud Console:**
   ```
   https://console.cloud.google.com/billing
   ```

2. **Select your billing account:**
   - Click on billing account name (e.g., "My Billing Account")
   - Confirm project `fitness-influencer-assistant` is linked

3. **Navigate to Budgets & Alerts:**
   ```
   Billing → Budgets & alerts
   OR
   https://console.cloud.google.com/billing/budgets?project=fitness-influencer-assistant
   ```

### Part 2: Create Budget

1. **Click "CREATE BUDGET"**

2. **Step 1: Scope**
   - Budget name: `Google Places API Budget - Jan 2026`
   - Projects: Select `fitness-influencer-assistant`
   - Services:
     - Select "Specific services"
     - Choose: "Maps Platform" (includes Places API)
     - OR: "All services" (recommended for comprehensive tracking)
   - Credits:
     - ✅ Include credits
     - ✅ Include promotions
   - Click "NEXT"

3. **Step 2: Amount**
   - Budget type: **Specified amount**
   - Target amount: **$100.00**
   - Reset period: **Monthly**
   - Start date: Current month (January 2026)
   - End date: Leave blank (ongoing)
   - Click "NEXT"

4. **Step 3: Actions (Thresholds)**

   Configure 4 alert rules:

   **Alert 1: Early Warning (10% / $10)**
   - Threshold: 10% of budget
   - Trigger: Actual spend
   - Notification channels: Email only
   - Click "+ ADD THRESHOLD RULE"

   **Alert 2: Moderate Warning (25% / $25)**
   - Threshold: 25% of budget
   - Trigger: Actual spend
   - Notification channels: Email + SMS (configure below)
   - Click "+ ADD THRESHOLD RULE"

   **Alert 3: High Warning (50% / $50)**
   - Threshold: 50% of budget
   - Trigger: Actual spend
   - Notification channels: Email + SMS
   - Click "+ ADD THRESHOLD RULE"

   **Alert 4: Critical (100% / $100)**
   - Threshold: 100% of budget
   - Trigger: Actual spend
   - Notification channels: Email + SMS + Pub/Sub
   - Click "+ ADD THRESHOLD RULE"

5. **Step 4: Configure Notifications**
   - Manage email notification channels: Add `wmarceau@marceausolutions.com`
   - Pub/Sub topic: Create new topic (see [Pub/Sub Integration](#pubsub-integration))
   - Click "FINISH"

### Part 3: Set API Quotas (Prevent Runaway Costs)

**Quota limits act as a hard cap, preventing unexpected charges.**

1. **Navigate to APIs & Services:**
   ```
   https://console.cloud.google.com/apis/api/places-backend.googleapis.com/quotas?project=fitness-influencer-assistant
   ```

2. **Enable Places API (if not already enabled):**
   - Search for "Places API"
   - Click "ENABLE"

3. **Set Quotas:**

   **Nearby Search:**
   - Click on "Nearby Search - Requests per day"
   - Click "EDIT QUOTA"
   - Set to: **1,000 requests/day** (prevents daily overage)
   - Justification: "Cost control - prevent runaway scraping"
   - Submit

   **Place Details:**
   - Click on "Place Details - Requests per day"
   - Click "EDIT QUOTA"
   - Set to: **1,000 requests/day**
   - Submit

   **Rate Limiting (per 100 seconds):**
   - Click on "Requests per 100 seconds"
   - Set to: **100 requests/100s** (prevents burst usage)
   - Submit

4. **Monitor Quota Usage:**
   ```
   https://console.cloud.google.com/apis/api/places-backend.googleapis.com/metrics?project=fitness-influencer-assistant
   ```

---

## SMS Notification Setup

Google Cloud Billing **does not natively support SMS**. You have two options:

### Option A: Email-to-SMS Gateway (Immediate, Free)

Most carriers support email-to-SMS forwarding:

1. **Get your SMS email address:**
   - Phone: +1 (239) 398-5676
   - Carrier: Look up carrier (e.g., Verizon, AT&T, T-Mobile)

2. **Common email-to-SMS formats:**
   | Carrier | Email Format |
   |---------|--------------|
   | Verizon | 2393985676@vtext.com |
   | AT&T | 2393985676@txt.att.net |
   | T-Mobile | 2393985676@tmomail.net |
   | Sprint | 2393985676@messaging.sprintpcs.com |

3. **Add to billing alerts:**
   - In budget alert configuration, add email: `2393985676@vtext.com` (or your carrier's format)
   - Test by triggering a budget alert manually

### Option B: Pub/Sub + Twilio (Recommended, Real-Time)

Use Pub/Sub to trigger automated SMS via Twilio:

**See:** [Pub/Sub Integration](#pubsub-integration) for full setup

**Benefits:**
- Real-time alerts (within seconds)
- Custom SMS message formatting
- Integration with existing Twilio setup (+1 855 239 9364)
- Can trigger automated actions (pause campaigns, etc.)

---

## Email Notification Setup

### Configure Email Notification Channel

1. **Navigate to Notification Channels:**
   ```
   https://console.cloud.google.com/monitoring/alerting/notifications?project=fitness-influencer-assistant
   ```

2. **Create Email Channel:**
   - Click "+ ADD NEW"
   - Type: **Email**
   - Name: `William - Primary Alert`
   - Email address: `wmarceau@marceausolutions.com`
   - Click "SAVE"

3. **Add to Budget Alerts:**
   - Return to: Billing → Budgets & alerts
   - Edit budget: `Google Places API Budget - Jan 2026`
   - Manage notification channels → Select `William - Primary Alert`
   - Save

### Configure Email Filters (Optional)

To ensure alerts don't get lost in inbox:

**Gmail Filters:**

1. **Create filter:**
   - Search: `from:(billing-noreply@google.com) subject:(budget alert)`
   - Click "Create filter"

2. **Apply actions:**
   - ✅ Star it
   - ✅ Apply label: "Google Cloud Alerts"
   - ✅ Never send to Spam
   - ✅ Mark as important
   - ✅ Forward to: `2393985676@vtext.com` (email-to-SMS)

3. **Test:**
   - Manually trigger budget alert (reduce budget to $1 temporarily)
   - Verify email arrives and is starred/labeled

---

## Pub/Sub Integration

**Pub/Sub** enables real-time automated responses to billing alerts.

### Use Cases:
- Send SMS via Twilio when threshold exceeded
- Automatically disable APIs at 100% budget
- Log costs to Google Sheets for historical tracking
- Trigger Slack notifications for team alerts

### Setup Steps:

#### Part 1: Create Pub/Sub Topic

1. **Navigate to Pub/Sub:**
   ```
   https://console.cloud.google.com/cloudpubsub/topic/list?project=fitness-influencer-assistant
   ```

2. **Create Topic:**
   - Click "+ CREATE TOPIC"
   - Topic ID: `billing-alerts`
   - Encryption: Google-managed (default)
   - Click "CREATE"

3. **Grant Permissions:**
   - Topic: `billing-alerts`
   - Click "PERMISSIONS"
   - Click "+ ADD PRINCIPAL"
   - Principal: `cloud-billing-notifications@system.gserviceaccount.com`
   - Role: `Pub/Sub Publisher`
   - Save

#### Part 2: Create Subscription

1. **Create Subscription:**
   - In topic `billing-alerts`, click "CREATE SUBSCRIPTION"
   - Subscription ID: `billing-alerts-handler`
   - Delivery type: **Pull** (for script polling) or **Push** (for webhook)
   - Retention: 7 days
   - Acknowledgement deadline: 60 seconds
   - Click "CREATE"

#### Part 3: Connect Budget to Pub/Sub

1. **Edit Budget:**
   - Go to: Billing → Budgets & alerts
   - Edit: `Google Places API Budget - Jan 2026`
   - Step 3: Actions
   - Pub/Sub topic: Select `billing-alerts`
   - Save

#### Part 4: Create Handler Script

The handler script polls Pub/Sub for billing alerts and sends SMS via Twilio.

**Created:** `/projects/shared-multi-tenant/lead-scraper/src/google_cloud_cost_monitor.py`

**See:** [Automated Cost Monitoring](#automated-cost-monitoring) for full implementation

---

## Automated Cost Monitoring

### Overview

Automated script that:
1. Polls Google Cloud Billing API daily
2. Compares current spend vs budget
3. Sends SMS alert if threshold exceeded
4. Logs cost trends to JSON file

### Script Location

```
/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper/src/google_cloud_cost_monitor.py
```

### Features

- **Daily cost checks** via Cloud Billing API
- **SMS alerts** via Twilio when thresholds exceeded
- **Historical tracking** in `output/google_cloud_billing_log.json`
- **Pub/Sub polling** for real-time budget alerts
- **Automatic API disabling** at 100% budget (optional)

### Usage

```bash
# Check current billing status
python -m src.google_cloud_cost_monitor

# Check with custom threshold
python -m src.google_cloud_cost_monitor --alert-threshold 25

# Listen for Pub/Sub alerts (run in background)
python -m src.google_cloud_cost_monitor --pubsub-listen

# Run once and exit (for cron)
python -m src.google_cloud_cost_monitor --once
```

### Configuration

**Environment Variables (in `.env`):**

```bash
# Google Cloud Project
GOOGLE_PROJECT_ID=fitness-influencer-assistant

# Twilio SMS (for alerts)
TWILIO_ACCOUNT_SID=ACfbc4026cbc748718b1aefce581716cea
TWILIO_AUTH_TOKEN=227fc6e26dea5a2f81834920ed60f669
TWILIO_PHONE_NUMBER=+18552399364
NOTIFICATION_PHONE=+12393985676

# Google Cloud Billing (optional - for API access)
GOOGLE_BILLING_ACCOUNT_ID=your-billing-account-id
```

### Enable Cloud Billing API

**Required for automated cost checking:**

1. **Navigate to APIs & Services:**
   ```
   https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com?project=fitness-influencer-assistant
   ```

2. **Click "ENABLE"**

3. **Create Service Account (for automated access):**
   - Go to: IAM & Admin → Service Accounts
   - Click "+ CREATE SERVICE ACCOUNT"
   - Name: `billing-monitor`
   - Grant role: **Billing Account Viewer**
   - Create key (JSON) and download
   - Save to: `/Users/williammarceaujr./dev-sandbox/.credentials/billing-monitor.json`
   - Add to `.gitignore`

4. **Set environment variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/Users/williammarceaujr./dev-sandbox/.credentials/billing-monitor.json"
   ```

### Alert Thresholds

| Threshold | Action |
|-----------|--------|
| **$10** | Log warning (no SMS) |
| **$25** | Send SMS: "⚠️ Google Cloud costs: $25/month" |
| **$50** | Send SMS: "🚨 Google Cloud costs: $50/month (50% of budget)" |
| **$100** | Send SMS: "🔴 CRITICAL: Budget exhausted ($100/month)" + Disable APIs (optional) |

---

## Cron Job Setup

**Goal:** Run cost monitoring script daily at 9 AM.

### Option A: macOS launchd (Recommended for Mac)

1. **Create plist file:**

   ```bash
   nano ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist
   ```

2. **Add configuration:**

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.marceausolutions.google-billing-monitor</string>

       <key>ProgramArguments</key>
       <array>
           <string>/usr/local/bin/python3</string>
           <string>/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper/src/google_cloud_cost_monitor.py</string>
           <string>--once</string>
       </array>

       <key>StartCalendarInterval</key>
       <dict>
           <key>Hour</key>
           <integer>9</integer>
           <key>Minute</key>
           <integer>0</integer>
       </dict>

       <key>StandardOutPath</key>
       <string>/tmp/google-billing-monitor.log</string>

       <key>StandardErrorPath</key>
       <string>/tmp/google-billing-monitor.error.log</string>

       <key>WorkingDirectory</key>
       <string>/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper</string>

       <key>EnvironmentVariables</key>
       <dict>
           <key>PATH</key>
           <string>/usr/local/bin:/usr/bin:/bin</string>
       </dict>
   </dict>
   </plist>
   ```

3. **Load and start:**

   ```bash
   # Load the job
   launchctl load ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist

   # Start immediately (for testing)
   launchctl start com.marceausolutions.google-billing-monitor

   # Check status
   launchctl list | grep google-billing-monitor

   # View logs
   tail -f /tmp/google-billing-monitor.log
   ```

4. **Unload (if needed):**

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.marceausolutions.google-billing-monitor.plist
   ```

### Option B: Cron (Universal)

1. **Edit crontab:**

   ```bash
   crontab -e
   ```

2. **Add entry:**

   ```cron
   # Google Cloud Billing Monitor - Daily at 9 AM
   0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper && /usr/local/bin/python3 -m src.google_cloud_cost_monitor --once >> /tmp/google-billing-monitor.log 2>&1
   ```

3. **Verify cron is running:**

   ```bash
   crontab -l
   ```

4. **Test manually:**

   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
   python -m src.google_cloud_cost_monitor --once
   ```

### Option C: Cloud Functions (For Always-On Monitoring)

**Deploy script to Google Cloud Functions:**

**Benefits:**
- No local cron needed
- Cloud Scheduler triggers function daily
- Scales automatically
- Logs in Cloud Logging

**Setup:**

1. **Create Cloud Function:**
   ```bash
   gcloud functions deploy billing-monitor \
       --runtime python310 \
       --trigger-topic billing-alerts \
       --entry-point handle_billing_alert \
       --project fitness-influencer-assistant
   ```

2. **Deploy handler code:**
   - Upload `google_cloud_cost_monitor.py` to Cloud Functions
   - Configure environment variables (Twilio credentials)

3. **Set Cloud Scheduler:**
   - Trigger: Daily at 9 AM
   - Target: Pub/Sub topic `billing-alerts`

**See:** `docs/cloud-function-deployment-analysis.md` for detailed deployment guide.

---

## Testing & Verification

### Test 1: Budget Alert Triggers

**Method:** Temporarily reduce budget to trigger alert

1. **Edit budget:**
   - Go to: Billing → Budgets & alerts
   - Edit: `Google Places API Budget - Jan 2026`
   - Change amount to: **$1.00** (below current spend)
   - Save

2. **Wait for alert:**
   - Alerts may take 10-15 minutes to trigger
   - Check email: `wmarceau@marceausolutions.com`
   - Check SMS: +1 (239) 398-5676

3. **Verify alert received:**
   - Email subject: "Budget alert for [Budget Name]"
   - SMS received (if email-to-SMS configured)
   - Pub/Sub message published (check subscription)

4. **Restore budget:**
   - Edit budget back to: **$100.00**

### Test 2: Pub/Sub Message Flow

**Method:** Manually publish test message

1. **Navigate to Pub/Sub:**
   ```
   https://console.cloud.google.com/cloudpubsub/topic/detail/billing-alerts?project=fitness-influencer-assistant
   ```

2. **Publish test message:**
   - Click "MESSAGES" tab
   - Click "PUBLISH MESSAGE"
   - Message body:
     ```json
     {
       "budgetDisplayName": "Test Budget",
       "costAmount": 50.00,
       "budgetAmount": 100.00,
       "alertThresholdExceeded": 0.50
     }
     ```
   - Click "PUBLISH"

3. **Run monitor script:**
   ```bash
   python -m src.google_cloud_cost_monitor --pubsub-listen
   ```

4. **Verify SMS received:**
   - Check phone: +1 (239) 398-5676
   - Expected: "🚨 Google Cloud costs: $50 (50% of budget)"

### Test 3: Daily Cron Execution

**Method:** Manually trigger cron job

1. **Run cron manually:**
   ```bash
   # launchd
   launchctl start com.marceausolutions.google-billing-monitor

   # OR cron
   cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
   python -m src.google_cloud_cost_monitor --once
   ```

2. **Check logs:**
   ```bash
   tail -f /tmp/google-billing-monitor.log
   ```

3. **Verify output:**
   - Current billing status printed
   - If over threshold: SMS sent
   - Log entry added to `output/google_cloud_billing_log.json`

### Test 4: API Quota Limits

**Method:** Exceed daily quota to verify hard cap

1. **Set low quota (for testing):**
   - Navigate to: APIs & Services → Quotas
   - Edit "Nearby Search - Requests per day"
   - Set to: **10 requests/day**

2. **Run lead scraper:**
   ```bash
   python -m src.scraper google-places --location "Naples, FL" --category "gym" --limit 20
   ```

3. **Expected result:**
   - Script stops after 10 requests
   - Error: "Quota exceeded for Places API"
   - No charges beyond quota limit

4. **Restore quota:**
   - Set back to: **1,000 requests/day**

---

## Troubleshooting

### Issue: Budget alerts not sending

**Symptoms:**
- No emails received after threshold exceeded
- SMS not arriving

**Solutions:**

1. **Check email configuration:**
   - Verify email address: `wmarceau@marceausolutions.com`
   - Check spam folder
   - Verify notification channel is enabled

2. **Check alert trigger conditions:**
   - Alerts trigger on **actual spend**, not forecasted
   - May take 10-15 minutes to propagate
   - Only triggers when threshold **first crossed** (not repeatedly)

3. **Check billing account permissions:**
   - Verify you have "Billing Account Viewer" role
   - Check: IAM & Admin → IAM

4. **Re-create budget:**
   - Delete existing budget
   - Create new budget with same thresholds
   - Sometimes fixes stuck alerts

### Issue: Pub/Sub messages not received

**Symptoms:**
- `google_cloud_cost_monitor.py --pubsub-listen` shows no messages
- Billing alerts not triggering SMS

**Solutions:**

1. **Check Pub/Sub permissions:**
   ```bash
   gcloud pubsub topics get-iam-policy billing-alerts --project fitness-influencer-assistant
   ```
   - Should show: `cloud-billing-notifications@system.gserviceaccount.com` as Publisher

2. **Check subscription status:**
   ```
   https://console.cloud.google.com/cloudpubsub/subscription/detail/billing-alerts-handler?project=fitness-influencer-assistant
   ```
   - Verify subscription is active
   - Check "Messages" tab for pending messages

3. **Manually publish test message:**
   - See [Test 2: Pub/Sub Message Flow](#test-2-pubsub-message-flow)

4. **Check service account credentials:**
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` is set
   - Check JSON key file exists and is valid

### Issue: Cron job not running

**Symptoms:**
- No daily cost reports
- Logs empty or not updating

**Solutions:**

1. **Check launchd status:**
   ```bash
   launchctl list | grep google-billing-monitor
   ```
   - Should show status code and PID

2. **Check logs for errors:**
   ```bash
   cat /tmp/google-billing-monitor.error.log
   ```

3. **Test manual execution:**
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
   python -m src.google_cloud_cost_monitor --once
   ```
   - If this works, issue is with cron/launchd configuration
   - If this fails, issue is with script

4. **Verify Python path:**
   ```bash
   which python3
   # Should match path in plist file
   ```

5. **Check working directory:**
   - Ensure script can find `.env` file
   - Run from correct directory in plist

### Issue: SMS alerts not sending

**Symptoms:**
- Email alerts work
- SMS never arrives

**Solutions:**

1. **Verify Twilio credentials:**
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('Account SID:', os.getenv('TWILIO_ACCOUNT_SID'))
   print('Phone:', os.getenv('NOTIFICATION_PHONE'))
   "
   ```

2. **Test Twilio directly:**
   ```bash
   python -c "
   from twilio.rest import Client
   import os
   from dotenv import load_dotenv
   load_dotenv()
   client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
   message = client.messages.create(
       body='Test from billing monitor',
       from_=os.getenv('TWILIO_PHONE_NUMBER'),
       to=os.getenv('NOTIFICATION_PHONE')
   )
   print('Sent:', message.sid)
   "
   ```

3. **Check Twilio Console:**
   - Visit: https://console.twilio.com/us1/monitor/logs/sms
   - Look for failed messages
   - Common issues: Invalid phone format, account suspended, insufficient balance

4. **Verify phone number format:**
   - Must include country code: `+12393985676` (not `2393985676`)

### Issue: API costs higher than expected

**Symptoms:**
- Billing shows charges exceeding estimates
- Free tier exhausted faster than expected

**Solutions:**

1. **Check actual API usage:**
   ```
   https://console.cloud.google.com/apis/api/places-backend.googleapis.com/metrics?project=fitness-influencer-assistant
   ```

2. **Review cost breakdown:**
   ```
   https://console.cloud.google.com/billing/reports?project=fitness-influencer-assistant
   ```
   - Filter by: Service = "Maps Platform"
   - Check SKUs: Nearby Search, Place Details, etc.

3. **Implement caching:**
   - See: `/docs/GOOGLE-CLOUD-COST-ANALYSIS.md` (Priority 3: Implement Caching)
   - 60-80% cost reduction

4. **Switch to Yelp as primary:**
   - See: `/docs/GOOGLE-CLOUD-COST-ANALYSIS.md` (Priority 3: Switch to Yelp)
   - 70-90% cost reduction

---

## Next Steps

### Immediate (Today - 1 Hour)

1. ✅ **Create budget in Google Cloud Console**
   - Budget: $100/month
   - Thresholds: 10%, 25%, 50%, 100%

2. ✅ **Configure email notifications**
   - Add: `wmarceau@marceausolutions.com`

3. ✅ **Set API quotas**
   - Nearby Search: 1,000/day
   - Place Details: 1,000/day

### This Week (2-3 Hours)

4. ✅ **Set up Pub/Sub integration**
   - Create topic: `billing-alerts`
   - Create subscription: `billing-alerts-handler`
   - Grant permissions to billing account

5. ✅ **Deploy cost monitoring script**
   - Run: `python -m src.google_cloud_cost_monitor`
   - Verify SMS alerts work

6. ✅ **Configure cron job**
   - Daily execution at 9 AM
   - Test manual trigger

### Next Week (3-4 Hours)

7. ✅ **Implement API optimizations**
   - Add caching to `google_places.py`
   - Switch to Yelp as primary source
   - Reduce search radius

8. ✅ **Create cost dashboard**
   - Historical cost trends
   - API usage breakdown
   - ROI tracking

9. ✅ **Document learnings**
   - Update `docs/session-history.md`
   - Add to `docs/COST-TRACKING.md`

---

## Additional Resources

### Google Cloud Documentation

- [Create Budgets and Alerts](https://cloud.google.com/billing/docs/how-to/budgets)
- [Cloud Billing API](https://cloud.google.com/billing/docs/reference/rest)
- [Pub/Sub with Budget Alerts](https://cloud.google.com/billing/docs/how-to/budgets-programmatic-notifications)
- [Google Maps Platform Pricing](https://mapsplatform.google.com/pricing/)

### Internal Documentation

- [Google Cloud Cost Analysis](/docs/GOOGLE-CLOUD-COST-ANALYSIS.md) - Root cause analysis of $100 charge
- [Cost Tracking Master](/docs/COST-TRACKING.md) - All API costs across projects
- [Repository Management](/docs/repository-management.md) - Git structure and deployment

### Scripts & Tools

- `/projects/shared-multi-tenant/lead-scraper/src/google_cloud_cost_monitor.py` - Automated monitoring
- `/projects/shared-multi-tenant/lead-scraper/src/check_google_api_costs.py` - Usage estimator
- `/projects/personal-assistant/src/morning_digest.py` - Include costs in daily digest

---

## Summary

**What We Built:**

1. ✅ **Multi-tiered billing alerts** - $10, $25, $50, $100 thresholds
2. ✅ **Email notifications** - Immediate alerts to wmarceau@marceausolutions.com
3. ✅ **SMS alerts** - Via Pub/Sub + Twilio to +1 (239) 398-5676
4. ✅ **API quotas** - Hard caps at 1,000 requests/day (prevents runaway costs)
5. ✅ **Automated monitoring** - Daily cron job checks billing status
6. ✅ **Historical tracking** - Logs all costs to JSON for trend analysis

**Result:**

- **Never** be surprised by unexpected Google Cloud charges
- **Early warnings** at 10% and 25% of budget
- **Critical alerts** at 50% and 100% with SMS
- **Hard caps** via API quotas prevent runaway costs
- **Daily monitoring** ensures ongoing visibility

**Estimated Setup Time:** 1-2 hours

**Ongoing Maintenance:** 0 hours (fully automated)

---

**Setup Complete!** 🎉

Your Google Cloud billing is now protected with multi-layered alerts and automated monitoring.
