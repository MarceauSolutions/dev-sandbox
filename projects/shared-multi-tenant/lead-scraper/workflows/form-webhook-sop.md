# SOP: Form Webhook & Lead Capture System

*Last Updated: 2026-01-15*
*Version: 1.1.0*

## Overview

This SOP documents the form webhook system that captures leads from cold outreach campaigns (SMS/email) and processes them through:
1. **Google Sheets** - Stores all form submissions for tracking/analysis
2. **ClickUp CRM** - Creates inquiry tasks for follow-up
3. **Notifications** - SMS/email alerts when new leads arrive

## Prerequisites

Before starting the webhook system, verify:

| Requirement | Check Command | Expected Result |
|-------------|---------------|-----------------|
| **ClickUp API token** | `grep CLICKUP_API_TOKEN .env` | Token value set |
| **ClickUp list ID** | `grep CLICKUP_LIST_ID .env` | List ID set |
| **Python environment** | `python --version` | Python 3.10+ |
| **Twilio (optional)** | `grep TWILIO .env` | All 3 vars set for SMS notifications |
| **Google Sheets (optional)** | `grep GOOGLE_SHEETS .env` | Spreadsheet ID set |

**Quick Verification:**
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.form_webhook clickup-lists
# Should show: List of available ClickUp lists
```

✅ **You should see**: Available ClickUp lists with IDs
❌ **If "401 Unauthorized"**: Regenerate ClickUp API token

---

## Architecture

```
                    ┌─────────────────────┐
                    │   Form Submission   │
                    │  (Landing Page/SMS) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Webhook Handler   │
                    │  (form_webhook.py)  │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │Google Sheets│    │   ClickUp   │    │Notifications│
    │   Storage   │    │  CRM Task   │    │  SMS/Email  │
    └─────────────┘    └─────────────┘    └─────────────┘
```

## Setup

### 1. Environment Variables

Add to `/Users/williammarceaujr./dev-sandbox/.env`:

```bash
# ClickUp (already configured)
CLICKUP_API_TOKEN=your-token
CLICKUP_LIST_ID=901709132478  # "Project 1" list

# Notifications
NOTIFICATION_PHONE=+1-XXX-XXX-XXXX  # Your phone for SMS alerts
NOTIFICATION_EMAIL=wmarceau@marceausolutions.com

# Google Sheets (optional)
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
```

### 2. ClickUp List Selection

List available ClickUp lists:
```bash
python -m src.form_webhook clickup-lists
```

Output:
```
=== Available ClickUp Lists ===
  - Project 1 (ID: 901709132478)  ← Using this for inquiries
  - Project 2 (ID: 901709132479)
  - Get Started with ClickUp (ID: 901709132484)
```

### 3. Google Sheets Setup (Optional)

1. Create a new Google Spreadsheet
2. Name the first sheet "Inquiries"
3. Add headers in row 1:
   - A: Submitted At
   - B: Name
   - C: Email
   - D: Phone
   - E: Company
   - F: Project Type
   - G: Message
   - H: Budget
   - I: Timeline
   - J: Source
   - K: UTM Source
   - L: UTM Medium
   - M: UTM Campaign
   - N: ClickUp Task ID
   - O: Processed

4. Get spreadsheet ID from URL: `docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
5. Add to .env: `GOOGLE_SHEETS_SPREADSHEET_ID=your-id`

## Usage

### Manual Form Processing (Testing)

```bash
# Process a test submission
python -m src.form_webhook process --data '{
  "name": "John Smith",
  "email": "john@fitnessgym.com",
  "phone": "239-555-1234",
  "company": "Naples Fitness",
  "project_type": "website",
  "message": "Interested in getting a website"
}' --source "cold_sms"
```

Expected output:
```json
{
  "success": true,
  "submission_id": "sub_20260115_0",
  "clickup_task_id": "86dz9bxbb",
  "sheets_added": false,
  "notifications_sent": ["email"],
  "errors": []
}
```

### Start Webhook Server

For receiving live form submissions:

```bash
# Start server on port 5000
python -m src.form_webhook serve --port 5000
```

Endpoints:
- `POST /webhook/form` - Receive form submissions
- `GET /webhook/health` - Health check
- `GET /webhook/stats` - Submission statistics

### View Statistics

```bash
python -m src.form_webhook stats
```

### Test Notifications

```bash
python -m src.form_webhook test-notify
```

## Integration with Cold Outreach

### SMS Campaign → Form → CRM Flow

1. **Send SMS** with lead-scraper:
   ```bash
   python -m src.scraper sms --for-real --limit 100 --pain-point no_website
   ```

2. **Recipient replies** or visits landing page

3. **Form submission** hits webhook:
   ```
   POST /webhook/form?source=cold_sms
   ```

4. **System automatically**:
   - Creates ClickUp task with all lead details
   - Sends you SMS/email notification
   - Logs to Google Sheets

5. **Follow up** via ClickUp task

### Landing Page Integration

Add webhook URL to your landing page form:

```html
<form action="https://your-server.com/webhook/form?source=landing_page" method="POST">
  <input type="text" name="name" required>
  <input type="email" name="email" required>
  <input type="tel" name="phone">
  <input type="text" name="company">
  <select name="project_type">
    <option value="website">Website</option>
    <option value="ai_assistant">AI Assistant</option>
    <option value="consulting">Consulting</option>
  </select>
  <textarea name="message"></textarea>
  <button type="submit">Submit</button>
</form>
```

## ClickUp Task Format

Created tasks include:

**Title**: `Inquiry: {Name} - {Project Type}`

**Description**:
```markdown
**New Inquiry from {Source}**

**Contact Information:**
- Name: John Smith
- Email: john@fitnessgym.com
- Phone: 239-555-1234
- Company: Naples Fitness

**Project Details:**
- Type: website
- Budget:
- Timeline:

**Message:**
Interested in getting a website

**Tracking:**
- Source: cold_sms
- Campaign:
- Submitted: 2026-01-15T12:00:00
```

**Tags**: `inquiry`, `{source}`

## Troubleshooting

### ClickUp Task Not Created

Check:
1. `CLICKUP_API_TOKEN` is set
2. `CLICKUP_LIST_ID` is set to a valid list
3. Run `python -m src.form_webhook clickup-lists` to verify

### No SMS Notifications

Check:
1. `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` are set
2. `NOTIFICATION_PHONE` has your phone number (with country code)
3. Twilio account has credits

### Google Sheets Not Working

Check:
1. `GOOGLE_SHEETS_SPREADSHEET_ID` is set
2. OAuth token exists at `output/google_token.json`
3. Token is not expired (may need to re-authorize)

## Files

| File | Purpose |
|------|---------|
| `src/form_webhook.py` | Main webhook handler module |
| `output/form_submissions.json` | Local backup of all submissions |
| `output/google_token.json` | Google OAuth token (generated on auth) |
| `.env` | Configuration (API keys, IDs) |

## Commands Reference

```bash
# Show available ClickUp lists
python -m src.form_webhook clickup-lists

# Process manual submission
python -m src.form_webhook process --data '{"name":"...", "email":"..."}' --source "test"

# Start webhook server
python -m src.form_webhook serve --port 5000

# View statistics
python -m src.form_webhook stats

# Test notifications
python -m src.form_webhook test-notify
```

## Metrics

Track these metrics weekly:
- Total form submissions
- Submissions by source (cold_sms, landing_page, referral)
- ClickUp tasks created
- Response rate (replies / submissions)
- Conversion rate (meetings / submissions)

---

## Rollback Procedures

### Stop Webhook Server

```bash
# If running in foreground: Ctrl+C
# If running in background:
pkill -f "form_webhook serve"
```

### Remove Duplicate/Test Submissions

```bash
# View recent submissions
cat output/form_submissions.json | python -m json.tool | tail -50

# Submissions are appended - to remove a test entry:
# 1. Open output/form_submissions.json
# 2. Remove the test entry object
# 3. Delete corresponding ClickUp task manually if created
```

### Handle Incorrect ClickUp Tasks

1. **Archive task**: Don't delete - archive for audit trail
2. **Update source tracking**: Edit task to mark as "test/duplicate"
3. **Prevent future**: Add email/phone to test blocklist

### Reset Google Sheets Token

If OAuth token expires:
```bash
# Delete existing token
rm output/google_token.json

# Re-run any command - will trigger OAuth flow
python -m src.form_webhook clickup-lists
# Follow browser prompts to re-authenticate
```

---

## Success Criteria

### Per-Step Verification

| Step | Success Indicator | Verification Command |
|------|------------------|---------------------|
| **Environment** | All required vars set | `grep -E "(CLICKUP|TWILIO)" .env` |
| **ClickUp Connection** | Lists retrieved | `python -m src.form_webhook clickup-lists` |
| **Test Submission** | Task created | Check ClickUp for new task |
| **Server Running** | Endpoints respond | `curl http://localhost:5000/webhook/health` |
| **Notifications** | Email/SMS received | `python -m src.form_webhook test-notify` |

### End-to-End Validation

- [ ] `.env` configured with required variables
- [ ] ClickUp API connection verified
- [ ] Test submission creates ClickUp task
- [ ] Webhook server starts without errors
- [ ] Health endpoint responds with 200
- [ ] Form submissions processed and logged
- [ ] Notifications delivered (if configured)
- [ ] Google Sheets row added (if configured)
