# Lead Tracking & Follow-Up System

**Created:** 2026-01-19
**Purpose:** Ensure no leads fall through the cracks - monitor all inbound channels and follow up appropriately
**Problem:** Multiple websites + cold outreach campaigns = need centralized lead tracking

---

## The Problem: Leads in Multiple Places

You currently have **7 different places** where leads can come in:

| Source | Type | Where Data Lives | Check Frequency |
|--------|------|------------------|-----------------|
| **1. Marceau Solutions website** | Form submissions | Google Sheets (via form handler) | Daily |
| **2. SW Florida Comfort HVAC website** | Form submissions | Google Sheets | Daily |
| **3. Square Foot Shipping website** | Form submissions | Google Sheets | Daily |
| **4. SMS cold outreach replies** | Text responses | Twilio → `sms_replies.json` | Real-time |
| **5. Email cold outreach replies** | Email responses | Gmail inbox | Daily |
| **6. Phone calls (HVAC/Shipping)** | Voice calls | Twilio call logs | Daily |
| **7. ClickUp CRM** | Manual entries | ClickUp lists | Weekly |

**Without a system:** Leads sit in different places, no follow-up, lost revenue.

**With this system:** Centralized dashboard, automated reminders, nothing falls through cracks.

---

## Solution: Daily Lead Review Workflow

### Morning Routine (8:00-9:00 AM Daily)

**File:** `projects/personal-assistant/workflows/daily-lead-review.md`

**Checklist:**
```bash
# 1. Check all form submissions (Google Sheets)
open "https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_SPREADSHEET_ID}"

# 2. Check SMS replies (local file)
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
cat output/sms_replies.json | jq '.[] | select(.timestamp > "'$(date -u -v-1d +%Y-%m-%dT%H:%M:%S)'")'

# 3. Check email inbox (filter: from leads)
# Manual check in Gmail: Search "from:*@* subject:RE"

# 4. Check Twilio call logs (phone calls)
# Manual check in Twilio Console: https://console.twilio.com/us1/monitor/logs/calls

# 5. Check ClickUp for tasks needing follow-up
# Manual check: https://app.clickup.com
```

**Output:** List of leads needing response (hot, warm, cold)

---

## Form Submission Monitoring

### Current Setup (Already Implemented)

Your websites use the unified form handler that saves to Google Sheets:

**File:** `/assets/js/form-handler.js` (referenced in all 3 websites)

**Google Sheets Integration:**
- Sheet ID: `GOOGLE_SHEETS_SPREADSHEET_ID` (from `.env`)
- All form submissions go to same sheet with `source` tracking
- Columns: Name, Email, Phone, Interest, Message, Source, Timestamp, Email Opt-In, SMS Opt-In

**Sources:**
- `coming-soon-page` (Marceau Solutions main site)
- `hvac-contact` (SW Florida Comfort HVAC)
- `shipping-quote` (Square Foot Shipping)

### Daily Form Check Command

```bash
# View all form submissions from last 24 hours
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.form_submission_checker --hours 24

# View only unresponded submissions
python -m src.form_submission_checker --status unresponded

# Mark submission as responded
python -m src.form_submission_checker --mark-responded --submission-id {id}
```

**Create this script:**

**File:** `projects/personal-assistant/src/form_submission_checker.py`

```python
#!/usr/bin/env python3
"""
Check Google Sheets for new form submissions and track follow-up status.

Usage:
  python -m src.form_submission_checker --hours 24
  python -m src.form_submission_checker --status unresponded
  python -m src.form_submission_checker --mark-responded --submission-id abc123
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
SHEET_NAME = 'Form Submissions'

def get_form_submissions(hours=24):
    """Fetch form submissions from last N hours."""
    # Connect to Google Sheets API
    service = build('sheets', 'v4', credentials=get_credentials())

    # Read all submissions
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A2:K'  # All rows except header
    ).execute()

    rows = result.get('values', [])

    # Filter by timestamp (last N hours)
    cutoff = datetime.now() - timedelta(hours=hours)
    recent_submissions = []

    for row in rows:
        if len(row) >= 7:  # Ensure row has timestamp
            timestamp = datetime.fromisoformat(row[6])
            if timestamp > cutoff:
                submission = {
                    'name': row[0],
                    'email': row[1],
                    'phone': row[2] if len(row) > 2 else '',
                    'interest': row[3] if len(row) > 3 else '',
                    'message': row[4] if len(row) > 4 else '',
                    'source': row[5] if len(row) > 5 else '',
                    'timestamp': row[6],
                    'email_optin': row[7] if len(row) > 7 else '',
                    'sms_optin': row[8] if len(row) > 8 else '',
                    'responded': row[9] if len(row) > 9 else 'No',
                    'responded_at': row[10] if len(row) > 10 else ''
                }
                recent_submissions.append(submission)

    return recent_submissions

def get_unresponded_submissions():
    """Fetch all submissions that haven't been responded to."""
    all_submissions = get_form_submissions(hours=24*30)  # Last 30 days
    return [s for s in all_submissions if s['responded'] == 'No']

def mark_as_responded(submission_id):
    """Mark a submission as responded to."""
    # Find row by ID, update 'Responded' column
    # (Implementation details)
    pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--status', choices=['all', 'unresponded'])
    parser.add_argument('--mark-responded', action='store_true')
    parser.add_argument('--submission-id')

    args = parser.parse_args()

    if args.mark_responded:
        mark_as_responded(args.submission_id)
        print(f"Marked submission {args.submission_id} as responded")
    elif args.status == 'unresponded':
        submissions = get_unresponded_submissions()
        print(json.dumps(submissions, indent=2))
    else:
        submissions = get_form_submissions(hours=args.hours)
        print(json.dumps(submissions, indent=2))
```

---

## SMS Reply Monitoring

### Current Setup (Already Implemented)

SMS replies are captured by Twilio webhook and saved to:

**File:** `projects/lead-scraper/output/sms_replies.json`

**Structure:**
```json
{
  "phone": "+1XXXXXXXXXX",
  "message": "YES interested",
  "timestamp": "2026-01-19T14:30:00",
  "campaign": "hvac-homeowners-jan19",
  "responded": false,
  "response_sent_at": null
}
```

### Daily SMS Reply Check Command

```bash
# View all SMS replies from last 24 hours
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.sms_reply_checker --hours 24

# View only unresponded replies
python -m src.sms_reply_checker --status unresponded

# Mark reply as responded
python -m src.sms_reply_checker --mark-responded --phone "+1XXXXXXXXXX"
```

**Create this script:**

**File:** `projects/lead-scraper/src/sms_reply_checker.py`

```python
#!/usr/bin/env python3
"""
Check SMS replies from cold outreach campaigns and track follow-up.

Usage:
  python -m src.sms_reply_checker --hours 24
  python -m src.sms_reply_checker --status unresponded
"""

import json
from datetime import datetime, timedelta

REPLIES_FILE = 'output/sms_replies.json'

def load_replies():
    """Load all SMS replies from JSON file."""
    try:
        with open(REPLIES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_recent_replies(hours=24):
    """Get replies from last N hours."""
    replies = load_replies()
    cutoff = datetime.now() - timedelta(hours=hours)

    recent = []
    for reply in replies:
        timestamp = datetime.fromisoformat(reply['timestamp'])
        if timestamp > cutoff:
            recent.append(reply)

    return recent

def get_unresponded_replies():
    """Get all unresponded replies."""
    replies = load_replies()
    return [r for r in replies if not r.get('responded', False)]

def categorize_reply(message):
    """Categorize reply as hot, warm, or cold."""
    message_lower = message.lower()

    if any(word in message_lower for word in ['yes', 'interested', 'tell me more', 'send', 'info']):
        return 'hot'
    elif any(word in message_lower for word in ['maybe', 'later', 'call me', 'email']):
        return 'warm'
    elif any(word in message_lower for word in ['no', 'stop', 'not interested', 'remove']):
        return 'cold'
    else:
        return 'warm'  # Default to warm if unclear

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--status', choices=['all', 'unresponded'])

    args = parser.parse_args()

    if args.status == 'unresponded':
        replies = get_unresponded_replies()
    else:
        replies = get_recent_replies(hours=args.hours)

    # Categorize and print
    for reply in replies:
        reply['category'] = categorize_reply(reply['message'])

    print(json.dumps(replies, indent=2))

    # Summary
    hot = [r for r in replies if r['category'] == 'hot']
    warm = [r for r in replies if r['category'] == 'warm']
    cold = [r for r in replies if r['category'] == 'cold']

    print(f"\n\nSUMMARY:")
    print(f"Hot leads: {len(hot)} (respond immediately)")
    print(f"Warm leads: {len(warm)} (respond within 24 hours)")
    print(f"Cold leads: {len(cold)} (mark as not interested)")
```

---

## Automated Morning Digest (Combines All Sources)

**Goal:** Single email every morning at 8 AM with all leads needing follow-up.

**File:** `projects/personal-assistant/src/morning_lead_digest.py`

**What it does:**
1. Checks all form submissions (last 24 hours)
2. Checks all SMS replies (last 24 hours)
3. Checks email inbox for replies
4. Checks Twilio call logs
5. Sends you ONE email with summary:

```
MORNING LEAD DIGEST - January 19, 2026

HOT LEADS (Respond Today):
- John Smith (HVAC) - Form submission: "AC not working, need help ASAP" [Source: Website]
- Jane Doe (Shipping) - SMS reply: "YES interested in quote" [Source: SMS Campaign]
- Bob Johnson (HVAC) - Missed call: (239) XXX-XXXX at 6:30 PM yesterday [Source: Phone]

WARM LEADS (Respond This Week):
- Sarah Williams (Marceau Solutions) - Form submission: "Tell me more about Growth System" [Source: Website]

COLD LEADS (Mark as Not Interested):
- Mike Brown - SMS reply: "Not interested, remove me" [Source: SMS Campaign]

FOLLOW-UPS DUE TODAY:
- Tony's Pizza Naples - Quote sent 3 days ago, no response yet [Reminder: Follow up]

ACTION ITEMS:
1. Call John Smith (AC emergency - high priority)
2. Text Jane Doe (send quote for shipping services)
3. Call Bob Johnson back (missed call yesterday)
4. Email Sarah Williams (send Growth System info)
5. Mark Mike Brown as opt-out (not interested)
6. Follow up with Tony's Pizza (quote reminder)
```

**Run this automatically via cron:**

```bash
# Add to crontab (runs every day at 8 AM)
0 8 * * * cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant && python -m src.morning_lead_digest
```

**Manual run:**

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/personal-assistant
python -m src.morning_lead_digest
```

---

## Lead Follow-Up Workflow

### When You Get a Lead (Daily Process)

**1. Hot Lead (Interested - "YES", "Tell me more")**

**Response Time:** Within 4 hours (same day)

**HVAC Hot Lead Response (Homeowner):**
```
Hi {name}, this is William from SW Florida Comfort HVAC.

Thanks for your interest! I'd love to help with your AC needs.

When works best for a free inspection?
- Tomorrow morning (9-11 AM)
- Tomorrow afternoon (2-4 PM)
- Wednesday morning (9-11 AM)

Or call me anytime: (239) 766-6129

Looking forward to helping you stay cool!
- William
```

**Shipping Hot Lead Response (E-commerce Seller):**
```
Hi {name}, this is William from Square Foot Shipping.

Thanks for your interest in our fulfillment services!

I'd like to learn more about your business and send you a custom quote.

Quick questions:
- How many orders/month do you ship?
- What's your average package size/weight?
- Where are most of your customers located?

Call me: (239) 880-3365
Or reply here and I'll send a quote today.

- William
```

**After sending response:**
```bash
# Mark as responded in system
python -m src.sms_reply_checker --mark-responded --phone "+1XXXXXXXXXX"

# Add to ClickUp CRM as "Hot Lead - Discovery Call Needed"
# (Manual or automated via ClickUp API)
```

---

**2. Warm Lead (Maybe interested - "Call me", "Email me")**

**Response Time:** Within 24 hours

**Response Template:**
```
Hi {name}, happy to call you!

When's a good time?
- Tomorrow between 9 AM - 5 PM?
- Wednesday morning?

Or if you prefer email, what questions can I answer?

- William
(239) XXX-XXXX
```

**After sending response:**
```bash
# Mark as responded, set follow-up reminder for 3 days
python -m src.follow_up_reminders --add --phone "+1XXXXXXXXXX" --days 3
```

---

**3. Cold Lead (Not interested - "STOP", "Not interested")**

**Response Time:** Immediate (automated)

**Auto-response (already implemented in SMS system):**
```
Understood, you've been removed from our list. Have a great day!
```

**After auto-response:**
```bash
# Add to opt-out list (already done by SMS system)
# No further action needed
```

---

## ClickUp CRM Integration (Centralize All Leads)

**Goal:** All leads (form, SMS, phone, email) go into ClickUp for unified tracking.

**ClickUp List Structure:**

```
Marceau Solutions Workspace
└── Leads List
    ├── HOT LEADS (Red)
    │   ├── John Smith - HVAC Emergency [Form Submission - Jan 19]
    │   ├── Jane Doe - Shipping Quote [SMS Reply - Jan 19]
    │   └── Bob Johnson - Missed Call [Phone - Jan 18]
    ├── WARM LEADS (Yellow)
    │   └── Sarah Williams - Growth System Inquiry [Form - Jan 19]
    ├── COLD LEADS (Gray)
    │   └── Mike Brown - Not Interested [SMS - Jan 19]
    └── FOLLOW-UPS DUE
        └── Tony's Pizza - Quote Sent 3 Days Ago [Reminder Due Today]
```

**Automation:**

Create tasks automatically when leads come in:

**File:** `projects/personal-assistant/src/clickup_lead_sync.py`

```python
#!/usr/bin/env python3
"""
Sync leads from all sources (forms, SMS, phone) to ClickUp CRM.

Usage:
  python -m src.clickup_lead_sync --source forms --hours 24
  python -m src.clickup_lead_sync --source sms --hours 24
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
CLICKUP_LIST_ID = os.getenv('CLICKUP_LIST_ID')

def create_clickup_task(lead_data):
    """Create a task in ClickUp for a new lead."""
    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"

    headers = {
        'Authorization': CLICKUP_API_TOKEN,
        'Content-Type': 'application/json'
    }

    # Determine priority based on lead temperature
    priority_map = {
        'hot': 1,    # Urgent (red)
        'warm': 2,   # High (yellow)
        'cold': 4    # Low (gray)
    }

    task_data = {
        'name': f"{lead_data['name']} - {lead_data['source']}",
        'description': f"""
**Contact Info:**
- Email: {lead_data.get('email', 'N/A')}
- Phone: {lead_data.get('phone', 'N/A')}

**Source:** {lead_data['source']}
**Timestamp:** {lead_data['timestamp']}

**Message/Interest:**
{lead_data.get('message', 'N/A')}

**Next Action:** {lead_data.get('next_action', 'Contact within 24 hours')}
        """,
        'priority': priority_map.get(lead_data.get('category', 'warm'), 2),
        'status': 'to do',
        'tags': [lead_data['source'], lead_data.get('category', 'warm')]
    }

    response = requests.post(url, json=task_data, headers=headers)
    return response.json()

if __name__ == '__main__':
    # Sync recent form submissions
    # Sync recent SMS replies
    # Sync recent phone calls
    pass
```

---

## Social Media Platform Evaluation: X vs TikTok vs LinkedIn

### For Marceau Solutions (Main Automation Business)

**You asked:** "Should we use X (Twitter) for Marceau Solutions?"

**Answer:** **LinkedIn is better than X for your automation business.** Here's why:

| Platform | Pros | Cons | Verdict |
|----------|------|------|---------|
| **X (Twitter)** | ✅ Real-time engagement<br>✅ Can share tech tips<br>✅ Good for thought leadership | ❌ Noisy, hard to reach decision-makers<br>❌ B2C audience (not B2B)<br>❌ Low conversion for $5K-20K services | ❌ **Skip** |
| **LinkedIn** | ✅ B2B decision-makers<br>✅ Business owners actively seeking solutions<br>✅ Professional content performs well<br>✅ Can target by industry | ❌ Slower growth than TikTok<br>❌ Less viral potential | ✅ **BEST CHOICE** |
| **TikTok** | ✅ Viral potential<br>✅ Visual before/after content<br>✅ Educational content works | ❌ B2C audience (consumers, not businesses)<br>❌ Wrong demographic for $5K-20K services | ❌ **Wrong audience** |

**Recommendation for Each Brand:**

| Brand | Platform | Why |
|-------|----------|-----|
| **Marceau Solutions** (Automation business selling to businesses) | **LinkedIn** | B2B audience, decision-makers, can showcase case studies |
| **SW Florida Comfort HVAC** (AC repair selling to homeowners) | **TikTok** | B2C audience, visual content works, homeowners use TikTok for home tips |
| **Square Foot Shipping** (3PL selling to e-commerce sellers) | **LinkedIn** | B2B audience, e-commerce sellers are on LinkedIn |

**Content Strategy by Platform:**

**LinkedIn (Marceau Solutions + Square Foot):**
- Post 2-3x per week
- Content: Case studies, ROI examples, automation tips
- Example: "How we helped an HVAC company book 40% more jobs with Voice AI"

**TikTok (SW Florida Comfort HVAC):**
- Post 3-5x per week
- Content: Emergency repair stories, before/after installs, AC tips
- Example: "AC died at 2 AM in 95° heat - here's what we did"

---

## Your Complete Action Todo List

### Priority 1: IMMEDIATE (This Week)

- [ ] **Stripe Integration** (2-3 hours)
  - Follow: `docs/STRIPE-UPDATE-GUIDE-JAN-19-2026.md`
  - Archive 3 old products
  - Create 6 new products
  - Create payment links
  - Update `pricing.html` with Stripe links

- [ ] **Check Current Form Submissions** (30 minutes)
  - Open Google Sheets: Form Submissions
  - Check last 7 days for any unresponded inquiries
  - Respond to any hot leads immediately

- [ ] **Check Current SMS Replies** (15 minutes)
  - Open: `projects/lead-scraper/output/sms_replies.json`
  - Look for any replies from previous campaigns
  - Respond to any hot leads

- [ ] **Check Email Inbox** (15 minutes)
  - Search: "RE:" or "Reply" in Gmail
  - Check for any cold outreach responses
  - Respond to hot leads

### Priority 2: SOCIAL MEDIA SETUP (This Week)

- [ ] **Create LinkedIn Company Page: Marceau Solutions** (30 minutes)
  - Go to: https://www.linkedin.com/company/setup/new/
  - Company name: Marceau Solutions
  - Tagline: "AI Automation for Local Service Businesses"
  - Description: Copy from website
  - Link: https://marceausolutions.com

- [ ] **Create LinkedIn Company Page: Square Foot Shipping** (30 minutes)
  - Company name: Square Foot Shipping & Storage
  - Tagline: "3PL Fulfillment & Warehouse Storage in Southwest Florida"
  - Link: https://squarefoot-shipping.com

- [ ] **Create TikTok Account: SW Florida Comfort HVAC** (30 minutes)
  - Go to: https://www.tiktok.com/signup
  - Username: @SWFloridaComfortHVAC
  - Bio: "24/7 AC Repair Naples/SWFL | Same-Day Service | (239) 766-6129"
  - Link: https://swflorida-comfort-hvac.com

### Priority 3: LEAD TRACKING AUTOMATION (Next Week)

- [ ] **Set Up Morning Lead Digest** (1 hour)
  - File: `projects/personal-assistant/src/morning_lead_digest.py`
  - Test run manually
  - Set up cron job (8 AM daily)

- [ ] **Create Form Submission Checker** (1 hour)
  - File: `projects/personal-assistant/src/form_submission_checker.py`
  - Test with existing submissions
  - Add to morning routine

- [ ] **Create SMS Reply Checker** (1 hour)
  - File: `projects/lead-scraper/src/sms_reply_checker.py`
  - Test with existing replies
  - Add to morning routine

### Priority 4: CUSTOMER CAMPAIGNS (After Setup Complete)

- [ ] **Scrape HVAC Homeowner Leads** (2 hours)
  - Source: Collier County Property Appraiser
  - Filter: Homes built 2000-2010 (old AC units)
  - Target: 500 homeowners in Naples

- [ ] **Scrape E-Commerce Seller Leads** (2 hours)
  - Source: Shopify store directories
  - Target: 100 Florida-based e-commerce sellers

- [ ] **Launch HVAC Customer Campaign** (Follow strategy doc)
  - Dry run → Small batch → Full campaign

- [ ] **Launch Shipping Customer Campaign** (Follow strategy doc)
  - Dry run → Small batch → Full campaign

---

## Success Criteria

**You'll know the system is working when:**

1. ✅ Morning digest arrives at 8 AM daily with all leads
2. ✅ No form submission sits unresponded for >24 hours
3. ✅ All SMS replies categorized (hot/warm/cold) and responded to
4. ✅ ClickUp shows all active leads in one place
5. ✅ Follow-up reminders trigger automatically
6. ✅ You respond to hot leads within 4 hours

---

**Files to Create:**
1. `projects/personal-assistant/src/morning_lead_digest.py`
2. `projects/personal-assistant/src/form_submission_checker.py`
3. `projects/lead-scraper/src/sms_reply_checker.py`
4. `projects/personal-assistant/src/clickup_lead_sync.py`
5. `projects/personal-assistant/workflows/daily-lead-review.md`

**Next Session:** Review lead tracking automation implementation
