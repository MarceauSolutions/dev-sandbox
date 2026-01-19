# Apollo.io Maximization Plan - $59/month Basic Plan

**Created:** 2026-01-19
**Current Status:** UNDERUTILIZED - paying $59/month, using ~10% of features
**Goal:** Extract full value from Basic plan features

---

## Current Spend: $135.99 to date ($218/month burn rate)

**Breakdown:**
- Twilio (SMS/Voice): $6.06
- Fixed APIs: $212/month
  - Claude API: $100/month
  - Apollo.io: $59/month ⚠️ **UNDERUTILIZED**
  - ngrok: $20/month
  - xAI/Grok: $25/month
  - Google Workspace: $6/month
  - Domains: $2/month

**Budget status:** $136 / $500 spent (27.2% used)

---

## Apollo.io Basic Plan ($59/month) - What You're Paying For

### ✅ Features Included (What you have access to):

| Feature | Credits/Limits | Currently Using? |
|---------|----------------|------------------|
| **Email credits** | 1,200/month | ❌ NO |
| **Mobile credits** | 120/month | ❌ NO |
| **Export credits** | 1,200/month | ⚠️ MINIMAL |
| **Email finder** | Unlimited | ❌ NO |
| **Data enrichment** | Unlimited | ❌ NO |
| **AI email sequences** | Yes | ❌ NO |
| **Workflows (automation)** | Yes | ❌ NO |
| **Website visitor tracking** | Yes | ❌ NO |
| **CRM integrations** | Yes | ❌ NO (not synced with ClickUp) |
| **Chrome extension** | Yes | ❌ NO |
| **Bulk actions** | Yes | ❌ NO |
| **Data validation** | Yes | ❌ NO |

### ⚠️ What You're Currently Doing (Wasteful):

You're using Apollo ONLY for:
- Exporting raw contact lists (CSV)
- Sending data to lead-scraper scripts
- Manually copying to SMS campaigns

**This is like buying a Tesla and only using it as a tent.**

---

## MAXIMIZE VALUE: 4 High-Impact Workflows

### 1. Website Visitor Tracking (FREE LEADS)

**What it does:** Identifies companies visiting your websites (Marceau Solutions, HVAC, Shipping) and auto-adds them to lists.

**Setup:**
1. Install Apollo pixel on all 3 websites
2. Create workflow: "Target Website Visitors"
   - Trigger: Company visits marceausolutions.com/pricing
   - Action: Add to "Hot Leads - Pricing Page Visitors" list
   - Action: Enroll in AI email sequence

**Value:** Capture intent signals automatically (people researching your pricing = hot leads)

**Script needed:** `projects/lead-scraper/src/apollo_pixel_installer.py`

---

### 2. AI Email Sequences (AUTOMATED OUTREACH)

**What it does:** Apollo AI drafts personalized email sequences based on your templates and sends automatically.

**Setup:**
1. Create sequence templates in Apollo (not SMS - email)
2. Sync with your existing cold outreach strategy
3. AI personalizes each email based on:
   - Company name
   - Industry
   - Pain points (from Apollo data)
   - Recent news/events

**Value:** 1,200 emails/month INCLUDED in your $59 plan (why pay Twilio $0.01/SMS when Apollo emails are free?)

**Templates to migrate:**
- HVAC homeowner outreach → Apollo email sequence
- Shipping e-commerce outreach → Apollo email sequence

---

### 3. Data Enrichment (BETTER TARGETING)

**What it does:** Enriches scraped leads with phone numbers, emails, LinkedIn profiles, company revenue, employee count.

**Current workflow (bad):**
```
Google Places API → scrape business name/address → send SMS → hope they respond
```

**Better workflow (using Apollo):**
```
Google Places API → scrape business name
    ↓
Apollo enrichment → add owner email, phone, LinkedIn, revenue
    ↓
Multi-channel outreach → SMS + Email + LinkedIn (3x touchpoints)
```

**Script needed:** `projects/lead-scraper/src/apollo_enrichment.py`

**API endpoint:** `POST /v1/people/match` (included in Basic plan)

---

### 4. CRM Integration (CLICKUP SYNC)

**What it does:** Auto-syncs Apollo leads to ClickUp CRM tasks.

**Current workflow (manual):**
```
Lead responds via SMS → You manually create ClickUp task → Track in CRM
```

**Better workflow (automated):**
```
Lead responds via SMS → Webhook triggers Apollo → Apollo creates ClickUp task → Auto-categorized
```

**Setup:**
1. Connect Apollo to ClickUp via Zapier or API
2. Workflow: "When lead status = 'Responded', create ClickUp task"

**Value:** Never miss a lead, automatic tracking

---

## Implementation Priority

### Week 1 (This Week):
1. ✅ **Install Apollo pixel** on marceausolutions.com, swflorida-comfort-hvac.com, squarefoot-shipping.com
2. ✅ **Create "Website Visitors" workflow** in Apollo
3. ✅ **Migrate 1 email template** from SMS to Apollo AI sequence

### Week 2:
4. **Build Apollo enrichment script** (`src/apollo_enrichment.py`)
5. **Test enrichment** on 100 HVAC leads (add emails + phones)
6. **Launch first Apollo email sequence** (HVAC homeowners)

### Week 3:
7. **Set up ClickUp integration** via Zapier
8. **Create automated lead routing** (hot leads → ClickUp, cold leads → nurture sequence)

### Week 4:
9. **Measure ROI** - compare Apollo email response rate vs SMS
10. **Optimize** - adjust sequences based on data

---

## Scripts to Create

### 1. Apollo Pixel Installer
**File:** `projects/lead-scraper/src/apollo_pixel_installer.py`

```python
#!/usr/bin/env python3
"""
Install Apollo pixel tracking code on all websites.

Usage:
  python -m src.apollo_pixel_installer --website marceausolutions
  python -m src.apollo_pixel_installer --all
"""

def install_apollo_pixel(website_path, apollo_account_id):
    """Add Apollo tracking pixel to website HTML."""
    pixel_code = f"""
    <!-- Apollo.io Website Tracking -->
    <script>
    (function(a,p,o,l,i,s){a[i]=a[i]||function(){{(a[i].q=a[i].q||[]).push(arguments)}};
    s=p.createElement(o);s.async=1;s.src=l;
    p.getElementsByTagName(o)[0].parentNode.insertBefore(s,p.getElementsByTagName(o)[0]);
    }})(window,document,'script','https://assets.apollo.io/sitetracker/apollo-tracker.js','apollo');
    apollo('init', '{apollo_account_id}');
    </script>
    """

    # Inject into <head> section of each HTML file
    # ...
```

### 2. Apollo Enrichment Script
**File:** `projects/lead-scraper/src/apollo_enrichment.py`

```python
#!/usr/bin/env python3
"""
Enrich scraped leads with Apollo.io data.

Usage:
  python -m src.apollo_enrichment --input leads.json --output enriched_leads.json
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')

def enrich_lead(business_name, location):
    """
    Enrich a lead with Apollo data.

    Returns:
    - Owner name
    - Owner email
    - Owner phone
    - LinkedIn URL
    - Company revenue
    - Employee count
    """

    response = requests.post(
        'https://api.apollo.io/v1/organizations/enrich',
        headers={'X-Api-Key': APOLLO_API_KEY},
        json={
            'name': business_name,
            'domain': None,  # We don't have domain yet
            'location': location
        }
    )

    if response.status_code == 200:
        data = response.json()
        return {
            'enriched': True,
            'owner_email': data.get('primary_email'),
            'owner_phone': data.get('primary_phone'),
            'revenue': data.get('estimated_annual_revenue'),
            'employees': data.get('employee_count'),
            'linkedin': data.get('linkedin_url')
        }
    else:
        return {'enriched': False}
```

### 3. Apollo Workflow Manager
**File:** `projects/lead-scraper/src/apollo_workflows.py`

```python
#!/usr/bin/env python3
"""
Manage Apollo.io workflows via API.

Usage:
  python -m src.apollo_workflows create --name "Website Visitors" --trigger page_view
  python -m src.apollo_workflows list
  python -m src.apollo_workflows enroll --list "Hot Leads" --sequence "HVAC Intro"
"""

# Automate workflow creation and lead enrollment
```

---

## Expected ROI

### Current State (Wasting $59/month):
- Using only basic export (could use free tier for this)
- 1,200 email credits unused = $0 value extracted
- 120 mobile credits unused = $0 value extracted
- Workflows unused = $0 value extracted
- **Effective cost:** $59 for data scraping (overpriced)

### Future State (Maximizing $59/month):
- 1,200 emails/month = replaces SMS campaigns (saves $12/month in Twilio)
- Website visitor tracking = 20-50 free inbound leads/month
- Data enrichment = 3x outreach channels (email + SMS + LinkedIn)
- AI sequences = saves 5-10 hours/month manual outreach
- **Effective value:** $200-300/month worth of tools for $59

**Break-even:** If Apollo generates just 1 paid client ($4,997+), it pays for itself for 7 years.

---

## Decision Point: Keep or Cancel?

| Keep Apollo if: | Cancel Apollo if: |
|-----------------|-------------------|
| ✅ Implement website tracking (captures inbound leads) | ❌ Only using for basic data export |
| ✅ Use AI email sequences (1,200 free emails/month) | ❌ Not willing to set up integrations |
| ✅ Enrich leads with multi-channel data | ❌ SMS-only outreach strategy |
| ✅ Integrate with ClickUp CRM | ❌ No time to build scripts this month |

**Recommendation:** Keep Apollo for 30 days, implement Week 1-2 features. If not seeing value by Feb 19, downgrade to free tier.

---

## Next Steps

1. ⬜ Install Apollo pixel on all 3 websites (today)
2. ⬜ Create "Website Visitors" workflow in Apollo dashboard
3. ⬜ Build `apollo_enrichment.py` script
4. ⬜ Migrate 1 SMS template to Apollo email sequence
5. ⬜ Test enriched lead outreach (100 contacts)
6. ⬜ Measure: Email response rate vs SMS response rate
7. ⬜ Decision: Keep Apollo or downgrade to free tier (by Feb 19)

---

**Files to create:**
- `projects/lead-scraper/src/apollo_pixel_installer.py`
- `projects/lead-scraper/src/apollo_enrichment.py`
- `projects/lead-scraper/src/apollo_workflows.py`

**Apollo dashboard:** https://app.apollo.io
**Workflows:** https://app.apollo.io/#/workflows
**Billing:** https://app.apollo.io/#/settings/billing
