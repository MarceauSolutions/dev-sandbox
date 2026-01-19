# Workflow: Morning Digest Aggregator

**Created:** 2026-01-19
**Purpose:** Aggregate multiple data sources into unified morning digest with prioritized action items
**Output:** Structured digest combining emails, SMS replies, form submissions, calendar events, and campaign metrics

---

## Overview

This workflow combines data from Gmail, SMS campaigns, form submissions, Google Calendar, and campaign analytics into a single morning digest. It prioritizes action items (hot leads first) and provides a complete business overview in one glance.

---

## Use Cases

- Daily morning routine (8:00 AM digest)
- Quick business health check (5-minute scan)
- Identify urgent action items (hot leads, callbacks)
- Track campaign performance trends
- Plan day based on calendar + priorities
- Respond to inquiries within 24 hours

---

## Prerequisites

Before running digest aggregator:
- ✅ Google OAuth configured (credentials.json + token.json)
- ✅ Gmail API enabled
- ✅ Google Calendar API enabled
- ✅ Google Sheets API enabled (optional, for form submissions)
- ✅ SMS campaign data exists: `projects/lead-scraper/output/sms_campaigns.json`
- ✅ Environment variables in `.env`:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_PROJECT_ID`

---

## Data Sources Aggregated

| Source | Data Retrieved | Update Frequency |
|--------|----------------|------------------|
| **Gmail** | Categorized emails (sponsorship, business, customer, urgent) | Real-time |
| **SMS Campaigns** | Hot leads, callbacks, questions, opt-outs | Real-time |
| **Form Submissions** | New inquiries with source tracking | Real-time |
| **Google Calendar** | Today's events + upcoming week | Real-time |
| **Campaign Metrics** | Response rates, funnel stages | Aggregated |

---

## Input Parameters

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `--hours` | Integer | 24 | Hours to look back for data |
| `--credentials` | File path | "credentials.json" | Google OAuth credentials file |
| `--token` | File path | "token.json" | Google OAuth token file |
| `--output` | File path | None | Save digest to JSON file (optional) |
| `--no-auth` | Flag | False | Skip Google auth, use local data only |

---

## Steps

### Step 1: Authenticate with Google APIs

**Objective:** Connect to Gmail, Calendar, and Sheets

**Actions:**
1. First-time setup:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
   python -m src.digest_aggregator --hours 1
   ```

2. Browser opens for OAuth consent:
   - Sign in to Google account
   - Grant permissions:
     - Read Gmail messages
     - Read Calendar events
     - Read Google Sheets (optional)

3. Token saved to `token.json` (reused for future runs)

**Tools:**
- Google OAuth 2.0
- `google-auth-oauthlib` library

**Output:**
```
Authenticating with Google...
Please visit this URL to authorize: https://accounts.google.com/o/oauth2/auth?...
Authentication successful!
```

**Verification:**
- ✅ `token.json` created in project directory
- ✅ No auth errors (credential issues would show here)

**Troubleshooting:**
- If `credentials.json` missing → Generate from `.env` using SOP 24 instructions
- If token expired → Delete `token.json` and re-run (will re-authenticate)

---

### Step 2: Fetch Email Summary

**Objective:** Categorize inbox emails from last N hours

**Actions:**
1. Query Gmail for messages in last 24 hours (or `--hours` value)
2. Categorize each email using keyword matching:
   - **Sponsorship**: "sponsorship", "brand deal", "collaboration", "partnership"
   - **Business**: "invoice", "payment", "revenue", "affiliate", "commission"
   - **Customer**: "refund", "support", "help", "question", "issue", "course"
   - **Other**: Everything else

3. Identify urgent emails (sponsorship + business = high priority)
4. Track action required items

**Data Structure:**
```python
EmailSummary:
    total: 15
    urgent: 3
    sponsorship: 2
    business: 1
    customer: 4
    other: 8
    action_required: [
        {
            'subject': 'Sponsorship Opportunity - $5K/month',
            'from': 'brands@company.com',
            'category': 'sponsorship'
        }
    ]
```

**Tools:**
- Gmail API (messages.list + messages.get)
- Keyword-based categorization

**Output:**
```
  - Fetching email summary...
📧 EMAILS: 15
   Urgent: 3
   Sponsorship: 2
   Business: 1
   Customer: 4
```

**Verification:**
- ✅ Total count matches inbox reality
- ✅ Urgent items are actually high priority
- ✅ Categories make sense (spot check a few)

---

### Step 3: Fetch SMS Reply Summary

**Objective:** Identify hot leads and action items from SMS campaigns

**Actions:**
1. Load `sms_campaigns.json` from lead-scraper project
2. Filter replies by timestamp (last N hours)
3. Categorize replies:
   - **Hot Lead**: "yes", "interested", "call me", positive signals
   - **Warm Lead**: "maybe", "more info", lukewarm interest
   - **Question**: Asking for details, not clear yes/no
   - **Callback Requested**: Explicitly asked to be called
   - **Opt-Out**: "STOP", "unsubscribe"

4. Prioritize action items:
   - Hot leads → URGENT (top of list)
   - Callbacks → URGENT
   - Questions → Medium priority

**Data Structure:**
```python
SMSReplySummary:
    total: 8
    hot_leads: 2
    warm_leads: 3
    questions: 1
    opt_outs: 1
    callbacks_requested: 1
    action_required: [
        {
            'phone': '+1239555XXXX',
            'message': 'Yes, I need a website ASAP',
            'business': 'Naples Gym',
            'category': 'hot_lead'
        }
    ]
```

**Tools:**
- JSON file reading
- Timestamp filtering
- Keyword-based categorization

**Output:**
```
  - Fetching SMS reply summary...
📱 SMS REPLIES: 8
   Hot Leads: 2
   Questions: 1
   Callbacks: 1
   Opt-outs: 1
```

**Verification:**
- ✅ Hot leads are actually positive responses (not false positives)
- ✅ Opt-outs correctly identified (prevent re-contact)

---

### Step 4: Fetch Form Submission Summary

**Objective:** Track new inquiries from website forms

**Actions:**
1. Load `form_submissions.json` from lead-scraper project
2. Filter by timestamp (last N hours)
3. Group by source:
   - Website contact form
   - Landing page
   - Referral
   - Unknown

4. Extract inquiry details:
   - Name, email, message
   - Source tracking
   - Skip test submissions (@example.com, @test.com)

**Data Structure:**
```python
FormSubmissionSummary:
    total: 3
    sources: {
        'website_contact_form': 2,
        'landing_page': 1
    }
    new_inquiries: [
        {
            'name': 'Jane Fitness',
            'email': 'jane@naplesfit.com',
            'source': 'website_contact_form',
            'message': 'Need a website for my gym...'
        }
    ]
```

**Tools:**
- JSON file reading
- Source tracking
- Email validation (skip test addresses)

**Output:**
```
  - Fetching form submissions...
📝 FORM SUBMISSIONS: 3
   website_contact_form: 2
   landing_page: 1
```

**Verification:**
- ✅ No test submissions included
- ✅ All inquiries have contact info (name + email)

---

### Step 5: Fetch Calendar Summary

**Objective:** Show today's schedule + upcoming week

**Actions:**
1. Query Google Calendar for:
   - **Today's events**: 12:00 AM today → 11:59 PM today
   - **Upcoming week**: Tomorrow → 7 days from now

2. Extract event details:
   - Summary (title)
   - Start time
   - Location (if available)

**Data Structure:**
```python
CalendarSummary:
    today_events: [
        {
            'summary': 'Client Call - Naples Gym',
            'start': '2026-01-19T10:00:00-05:00',
            'location': 'Zoom'
        }
    ]
    upcoming_week: [
        {
            'summary': 'Discovery Call - Pizza Shop',
            'start': '2026-01-20T14:00:00-05:00'
        }
    ]
```

**Tools:**
- Google Calendar API (events.list)
- Timezone-aware date filtering

**Output:**
```
  - Fetching calendar events...
📅 TODAY'S CALENDAR: 2 events
   - 10:00 AM: Client Call - Naples Gym
   - 2:00 PM: Discovery Call - Pizza Shop
```

**Verification:**
- ✅ Events match what's in Google Calendar
- ✅ Times displayed in local timezone

---

### Step 6: Fetch Campaign Summary

**Objective:** Calculate campaign performance metrics

**Actions:**
1. Load `sms_campaigns.json`
2. Calculate:
   - Total contacted (all records)
   - Total responded (records with replies or status='replied')
   - Response rate (responded / contacted * 100)
   - Funnel stages:
     - Contacted → Responded → Qualified → Converted

3. Use estimates for funnel stages:
   - Qualified ≈ 50% of responded (until ClickUp integration)
   - Converted ≈ from ClickUp (manual for now)

**Data Structure:**
```python
CampaignSummary:
    total_contacted: 150
    total_responded: 12
    response_rate: 8.0
    funnel_stages: {
        'contacted': 150,
        'responded': 12,
        'qualified': 6,
        'converted': 0
    }
```

**Tools:**
- JSON aggregation
- Percentage calculation

**Output:**
```
  - Fetching campaign metrics...
📊 CAMPAIGN METRICS:
   Total Contacted: 150
   Total Responded: 12
   Response Rate: 8.0%
```

**Verification:**
- ✅ Response rate is realistic (5-10% typical for cold outreach)
- ✅ Funnel stages decrease monotonically (contacted > responded > qualified > converted)

---

### Step 7: Generate Prioritized Action Items

**Objective:** Create ranked to-do list from all data sources

**Priority Rules:**
1. **URGENT (top)**: Hot leads from form submissions (waiting >24h is fatal)
2. **URGENT**: SMS hot leads and callback requests
3. **HIGH**: Urgent emails (sponsorship, business)
4. **MEDIUM**: SMS questions
5. **LOW**: Other emails

**Actions:**
1. Scan form submissions for hot lead signals:
   - Keywords: "website", "interested", "need", "want", "help", "quote", "asap", "urgent", "gym", "fitness"
   - If found → Insert at top with 🚨 [URGENT HOT LEAD] tag

2. Add SMS hot leads/callbacks to top

3. Add urgent emails (top 3)

4. Add SMS questions

**Data Structure:**
```python
action_items: [
    "🚨 [URGENT HOT LEAD] Follow up with Jane Fitness NOW - website_contact_form",
    "🚨 [URGENT] Call back Naples Gym - hot lead",
    "1. Respond to: Sponsorship Opportunity - $5K/month",
    "2. Answer SMS question from +1239555XXXX"
]
```

**Why URGENT Tags?**
- Form submissions waiting >24 hours = lost leads (Jane Fitness example: waited 26 hours, probably went elsewhere)
- Hot leads have 24-48 hour window before they move on

**Tools:**
- Keyword matching for urgency detection
- Priority queue logic

**Output:**
```
  - Generating action items...

============================================================
ACTION ITEMS:
============================================================
  🚨 [URGENT HOT LEAD] Follow up with Jane Fitness NOW - website_contact_form
  🚨 [URGENT] Call back Naples Gym - hot lead
  1. Respond to: Sponsorship Opportunity - $5K/month
  2. Answer SMS question from +1239555XXXX
```

**Verification:**
- ✅ Hot leads appear first (not buried in list)
- ✅ Action items are specific (names, business, context)
- ✅ No test data in action items

---

### Step 8: Output Digest

**Objective:** Display or save complete digest

**Option A: Console Output (default)**
```bash
python -m src.digest_aggregator --hours 24
```

**Output:**
```
============================================================
DIGEST SUMMARY - Last 24 Hours
============================================================

📧 EMAILS: 15
   Urgent: 3
   Sponsorship: 2
   Business: 1
   Customer: 4

📱 SMS REPLIES: 8
   Hot Leads: 2
   Questions: 1
   Callbacks: 1
   Opt-outs: 1

📝 FORM SUBMISSIONS: 3
   website_contact_form: 2
   landing_page: 1

📅 TODAY'S CALENDAR: 2 events
   - 10:00 AM: Client Call - Naples Gym
   - 2:00 PM: Discovery Call - Pizza Shop

📊 CAMPAIGN METRICS:
   Total Contacted: 150
   Total Responded: 12
   Response Rate: 8.0%

============================================================
ACTION ITEMS:
============================================================
  🚨 [URGENT HOT LEAD] Follow up with Jane Fitness NOW - website_contact_form
  🚨 [URGENT] Call back Naples Gym - hot lead
  1. Respond to: Sponsorship Opportunity - $5K/month
  2. Answer SMS question from +1239555XXXX
```

**Option B: JSON File Output**
```bash
python -m src.digest_aggregator --hours 24 --output output/digests/digest-2026-01-19.json
```

**JSON Structure:**
```json
{
  "generated_at": "2026-01-19T08:00:00",
  "hours_covered": 24,
  "email": {
    "total": 15,
    "urgent": 3,
    "sponsorship": 2,
    "business": 1,
    "customer": 4,
    "other": 8,
    "action_required": [...]
  },
  "sms": {
    "total": 8,
    "hot_leads": 2,
    "warm_leads": 3,
    "questions": 1,
    "opt_outs": 1,
    "callbacks_requested": 1,
    "action_required": [...]
  },
  "forms": {
    "total": 3,
    "sources": {...},
    "new_inquiries": [...]
  },
  "calendar": {
    "today_events": [...],
    "upcoming_week": [...]
  },
  "campaign": {
    "total_contacted": 150,
    "total_responded": 12,
    "response_rate": 8.0,
    "funnel_stages": {...}
  },
  "action_items": [...]
}
```

**Tools:**
- Console formatting (colors, emojis)
- JSON serialization

---

### Step 9: Integration with Morning Digest Email (Optional)

**Objective:** Send digest via email instead of console

**Actions:**
1. Use `morning_digest.py` to send email:
   ```bash
   python -m src.morning_digest
   ```

2. Email includes:
   - All digest sections (emails, SMS, forms, calendar, campaigns)
   - Action items at top (prioritized)
   - Links to ClickUp, Gmail, Calendar
   - AI news summary (if available)

**Tools:**
- `morning_digest.py` (wraps digest_aggregator + email sender)
- SMTP email delivery

**See:** `workflows/daily-routine-sop.md` for complete morning digest workflow

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Credentials file not found` | Missing credentials.json | Generate from .env using SOP 24 (create from GOOGLE_CLIENT_ID vars) |
| `Token expired` | OAuth token > 7 days old | Delete token.json, re-run to re-authenticate |
| `Gmail API error: 403` | API not enabled in Google Cloud Console | Enable Gmail API at console.cloud.google.com |
| `sms_campaigns.json not found` | No SMS data exists yet | Create empty file: `{"records": []}` or run first SMS campaign |
| `No action items` | No new data in timeframe | Expand `--hours` to 48 or 72 to see older data |
| Form submissions duplicated | Same inquiry submitted twice | Deduplicate by email address or timestamp |
| Hot leads missed | Keyword detection incomplete | Add custom keywords to `EMAIL_CATEGORIES` in digest_aggregator.py |

---

## Success Criteria

**Digest is complete when:**
- ✅ All 5 data sources queried (email, SMS, forms, calendar, campaigns)
- ✅ Hot leads appear in action items with 🚨 URGENT tag
- ✅ No test data included (no @example.com emails)
- ✅ Action items are specific and actionable
- ✅ Calendar shows today + upcoming week
- ✅ Campaign metrics calculated correctly (response rate realistic)
- ✅ Digest generated in < 30 seconds

---

## Performance Metrics

**Typical Digest Composition (Naples Gym Example):**
- Emails: 10-20/day (3-5 urgent)
- SMS Replies: 5-10/day (1-2 hot leads)
- Form Submissions: 2-5/day (1-2 hot leads)
- Calendar Events: 2-4/day
- Campaign Metrics: 100-200 contacted total, 5-10% response rate

**Time to Generate:**
- With Google APIs: 10-20 seconds (network calls)
- Without Google (--no-auth): 2-5 seconds (local data only)

**Data Freshness:**
- Email: Real-time (< 1 minute delay)
- SMS: Real-time (updated immediately on reply)
- Forms: Real-time (Google Sheets sync < 5 minutes)
- Calendar: Real-time
- Campaign Metrics: Aggregated (updates when sms_campaigns.json changes)

---

## Example Use Cases

### Use Case 1: Daily Morning Routine
```bash
# 8:00 AM: Run digest as part of morning routine
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.digest_aggregator --hours 24

# Review action items
# Respond to hot leads FIRST (within 1 hour)
# Then handle other emails/SMS
```

---

### Use Case 2: After-Hours Check
```bash
# 6:00 PM: Check if any urgent items came in after work hours
python -m src.digest_aggregator --hours 4

# If hot leads → respond immediately (competitive advantage)
```

---

### Use Case 3: Weekly Review
```bash
# Monday 9:00 AM: Review last week's activity
python -m src.digest_aggregator --hours 168 --output output/digests/weekly-2026-01-19.json

# Analyze trends:
# - Response rate improving or declining?
# - Which form sources drive most inquiries?
# - Calendar utilization (too many/few meetings?)
```

---

### Use Case 4: Local Data Only (No Google)
```bash
# Use when offline or Google APIs down
python -m src.digest_aggregator --hours 24 --no-auth

# Only shows: SMS, forms (local JSON), campaign metrics
# Skips: Gmail, Calendar
```

---

## Related Workflows

- `daily-routine-sop.md` - Complete morning routine (includes digest + actions)
- `weekly-routine-sop.md` - Weekly review and planning
- `ai-news-digest-generation.md` - AI news summary (can be added to digest)
- `client-proposal-generation.md` - Follow up on form submissions with proposals

---

## Future Enhancements

**Planned Integrations:**
- ClickUp CRM sync (actual conversion data instead of estimates)
- Twilio webhook (real-time SMS replies, not polling JSON)
- Slack notifications (send digest to Slack channel)
- Historical trending (compare this week vs last week metrics)
- Weather integration (show today's weather in digest)

**Automation:**
- Cron job: Run daily at 8:00 AM
- Email delivery: Send digest automatically (via morning_digest.py)
- Calendar reminders: Auto-create for action items

---

## Version History

- **v1.0 (2026-01-19):** Initial workflow created for personal assistant project
