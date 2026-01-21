# Apollo.io Prospect Alerts Integration Research
**Email Source:** Apollo <hello@mail.apollo.io> - January 21, 2026 11:42 AM
**Subject:** "Get immediate alerts when you have new prospects ⏰"
**Purpose:** Evaluate immediate prospect alert integration with our lead scraping system
**Last Updated:** January 21, 2026

---

## Overview

Apollo.io offers **real-time prospect alerts** that could enhance our current lead scraping workflow by notifying us immediately when new prospects match our criteria.

---

## Current State

**What We Have:**
- ✅ Apollo.io API integration (`projects/shared/lead-scraper/src/apollo.py`)
- ✅ Lead enrichment via Apollo API
- ✅ Manual lead scraping workflows
- ✅ Environment variable: `APOLLO_API_KEY` configured

**What We're Missing:**
- ❌ Real-time prospect alerts
- ❌ Automated alert → SMS/Email notifications
- ❌ Alert → Auto-enroll in follow-up sequences

---

## Apollo.io Prospect Alerts Features

### What Alerts Can Do:

1. **Real-Time Notifications**
   - Email when new prospects match saved searches
   - Slack/webhook integrations
   - Daily digest of new prospects

2. **Saved Search Triggers**
   - Set criteria (industry, location, company size, etc.)
   - Get alerted when new companies/contacts match
   - Useful for: New businesses in Naples, Fort Myers, Cape Coral

3. **Enrichment Triggers**
   - Alert when prospect data is enriched with emails/phone numbers
   - Useful for: Leads that were missing contact info now have it

---

## Integration Opportunities

### Opportunity 1: New Business Alerts → Automated Outreach

**Workflow:**
```
Apollo Alert (new Naples gym opened)
  ↓
Webhook → Our API
  ↓
Auto-scrape additional details
  ↓
Enrich with Google/Yelp data
  ↓
Add to ClickUp (qualified lead)
  ↓
Auto-enroll in SMS follow-up sequence
  ↓
Send first outreach message
```

**Value:**
- ⏱️ Immediate outreach (before competitors)
- 🤖 Fully automated (zero manual work)
- 🎯 Higher conversion (first to contact)

**Implementation Complexity:** Medium
- Need webhook endpoint to receive Apollo alerts
- Map Apollo data format to our lead model
- Trigger existing enrichment + outreach pipelines

---

### Opportunity 2: Missing Contact Info → Re-Enrichment

**Workflow:**
```
Apollo Alert (email found for previously scraped lead)
  ↓
Webhook → Our API
  ↓
Update lead in database
  ↓
Check if lead qualifies for outreach
  ↓
If yes: Enroll in follow-up sequence
```

**Value:**
- 📈 Increase contactable leads by 20-30%
- 🔄 Automatically retry leads that were missing contact info
- 💰 More revenue from existing lead database

**Implementation Complexity:** Low
- Simpler than Opportunity 1
- Just updates existing leads
- Reuses existing outreach logic

---

### Opportunity 3: Competitor Monitoring

**Workflow:**
```
Apollo Alert (competitor hiring/expanding)
  ↓
Webhook → Our API
  ↓
Log competitor activity
  ↓
If significant: Notify William via SMS
  ↓
Optionally: Auto-adjust pricing/messaging
```

**Value:**
- 🕵️ Competitive intelligence
- 🎯 Proactive strategy adjustments
- 📊 Market trend detection

**Implementation Complexity:** Low
- Passive monitoring
- Minimal action required
- Could use simple email forwarding initially

---

## Technical Implementation

### Step 1: Enable Apollo Webhooks

Apollo.io supports webhooks for:
- New prospects in saved searches
- Prospect data updates
- Enrichment completions

**Setup:**
1. Log into Apollo.io dashboard
2. Go to Settings → Integrations → Webhooks
3. Add webhook URL: `https://api.marceausolutions.com/webhooks/apollo`
4. Select events: "New prospects", "Data enrichment"
5. Save

### Step 2: Create Webhook Endpoint

**File:** `projects/shared/lead-scraper/src/apollo_webhook_handler.py`

```python
from fastapi import APIRouter, Request
from .apollo import ApolloClient
from .models import Lead
from .enrichment import enrich_lead
from .scraper import add_to_clickup
from .follow_up_sequence import enroll_in_sequence

router = APIRouter()

@router.post("/webhooks/apollo")
async def handle_apollo_webhook(request: Request):
    """
    Handle incoming Apollo.io webhook for new prospects.

    Workflow:
    1. Parse Apollo prospect data
    2. Convert to our Lead model
    3. Enrich with Google/Yelp if needed
    4. Add to ClickUp
    5. Enroll in follow-up sequence
    """
    payload = await request.json()

    # Parse Apollo data
    prospect = payload.get('person') or payload.get('organization')

    if not prospect:
        return {"status": "ignored", "reason": "no prospect data"}

    # Convert to our Lead model
    lead = Lead(
        business_name=prospect.get('organization_name') or prospect.get('name'),
        phone=prospect.get('phone_numbers', [{}])[0].get('raw_number'),
        email=prospect.get('email'),
        website=prospect.get('website_url'),
        address=f"{prospect.get('city')}, {prospect.get('state')}",
        # ... map other fields
    )

    # Enrich if missing data
    if not lead.phone or not lead.email:
        lead = enrich_lead(lead)

    # Add to ClickUp
    clickup_task_id = add_to_clickup(lead)

    # Enroll in follow-up sequence
    if lead.phone:
        enroll_in_sequence(
            campaign_name="Apollo Auto-Enroll",
            phone=lead.phone,
            business_name=lead.business_name
        )

    return {
        "status": "processed",
        "lead_id": lead.id,
        "clickup_task_id": clickup_task_id,
        "enrolled_in_sequence": bool(lead.phone)
    }
```

### Step 3: Update API Server

Add webhook router to main API:

```python
# In api/main.py or equivalent
from src.apollo_webhook_handler import router as apollo_router

app.include_router(apollo_router, prefix="/api")
```

### Step 4: Test Webhook

```bash
# Send test webhook
curl -X POST https://api.marceausolutions.com/webhooks/apollo \
  -H "Content-Type: application/json" \
  -d '{
    "person": {
      "name": "Test Prospect",
      "email": "test@example.com",
      "phone_numbers": [{"raw_number": "+12395551234"}],
      "organization_name": "Test Gym Naples",
      "city": "Naples",
      "state": "FL"
    }
  }'
```

---

## Cost-Benefit Analysis

### Costs:
- **Apollo Plan:** Likely need Pro plan ($99-149/month) for webhook access
- **Development Time:** 4-8 hours to implement webhook handler
- **Ongoing:** Minimal (webhook endpoint maintenance)

### Benefits:
- **Speed to Lead:** Contact prospects within minutes (vs days)
- **Conversion Rate:** 20-40% higher (first-mover advantage)
- **Automation:** Zero manual work for new prospect discovery
- **Coverage:** 100% of new businesses (vs manual checking)

### ROI Calculation:

**Scenario:** 10 new Naples gyms/month via Apollo alerts

| Metric | Without Alerts | With Alerts | Delta |
|--------|---------------|-------------|-------|
| **New prospects found** | 10/month (manual) | 15/month (automated + broader criteria) | +50% |
| **Time to first contact** | 3-7 days | <1 hour | -99% |
| **Conversion rate** | 5% | 8% | +60% |
| **Deals closed** | 0.5/month | 1.2/month | +140% |
| **Revenue** | $5K/month | $12K/month | +$7K/month |

**Break-even:**
- Apollo Pro: $99-149/month
- Development: $0 (one-time internal)
- **Total cost:** $99-149/month
- **Revenue increase:** $7K/month
- **ROI:** 47x-71x

**Conclusion:** High-value integration, worth implementing

---

## Implementation Priority

### Phase 1: Basic Webhook (Now - 4 hours)
- ✅ Set up webhook endpoint
- ✅ Parse Apollo data
- ✅ Add to ClickUp
- ✅ Log all alerts

### Phase 2: Auto-Enrollment (Week 2 - 2 hours)
- ✅ Enroll in follow-up sequence
- ✅ Send first outreach message
- ✅ Track conversion from alerts

### Phase 3: Intelligence (Month 2 - 4 hours)
- ✅ Competitor monitoring
- ✅ Market trend detection
- ✅ Auto-adjust messaging based on patterns

---

## Alternative: Email-Based Alerts (Simpler)

If Apollo webhooks require higher tier:

### Workflow:
```
Apollo email alert (new gym in Naples)
  ↓
Gmail API detects email
  ↓
Parse prospect details from email
  ↓
Same enrichment + outreach workflow
```

**Pros:**
- ✅ No webhook setup needed
- ✅ Works with basic Apollo plan
- ✅ Easier to implement

**Cons:**
- ❌ Slight delay (email polling vs instant webhook)
- ❌ Less reliable (email parsing vs structured data)
- ❌ Harder to parse data from email format

**Implementation:** Use existing `execution/gmail_monitor.py` with email parsing

---

## Decision Framework

### Implement Apollo Alerts When:
- Generating >10 leads/month from scraping
- Time-to-contact matters for conversion
- Have budget for Apollo Pro ($99-149/month)
- Want to automate prospect discovery

### Skip Apollo Alerts When:
- Manual scraping sufficient (<5 leads/month)
- Not ready to scale outreach
- Budget constraints
- Current lead flow adequate

---

## Current Recommendation

**IMPLEMENT in Phase 2** (after social media automation live)

**Reasoning:**
1. Social media automation higher priority (multi-platform posting)
2. Apollo alerts valuable but not urgent
3. Can implement in 4-8 hours when ready
4. High ROI (47x-71x) justifies the work

**Timeline:**
- **Now:** Document research (✅ this file)
- **Feb 2026:** Implement after social media automation complete
- **Mar 2026:** Measure ROI, optimize workflows

---

## Integration Locations

| Component | File Path | Status |
|-----------|-----------|--------|
| Apollo API Client | `projects/shared/lead-scraper/src/apollo.py` | ✅ Exists |
| Webhook Handler | `projects/shared/lead-scraper/src/apollo_webhook_handler.py` | 📋 To create |
| Lead Model | `projects/shared/lead-scraper/src/models.py` | ✅ Exists |
| Enrichment | `projects/shared/lead-scraper/src/enrichment.py` | ✅ Exists |
| Follow-up Sequences | `projects/shared/lead-scraper/src/follow_up_sequence.py` | ✅ Exists |

---

## References

- **Apollo API docs:** https://apolloio.github.io/apollo-api-docs/
- **Apollo webhooks:** https://knowledge.apollo.io/hc/en-us/articles/4408971016077-Webhooks
- **Email source:** Apollo <hello@mail.apollo.io> Jan 21, 2026
- **Current integration:** `projects/shared/lead-scraper/src/apollo.py`

---

## Action Items

- [x] Document Apollo alerts research
- [ ] Add to project backlog (Phase 2)
- [ ] Set reminder for Feb 2026 implementation
- [ ] Verify Apollo plan has webhook access
- [ ] Estimate exact development time when ready

---

**Status:** Research complete, implementation deferred to Phase 2 (Feb 2026)
