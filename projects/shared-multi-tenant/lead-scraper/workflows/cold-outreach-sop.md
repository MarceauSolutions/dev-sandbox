# SOP: Cold Outreach Campaign System

*Last Updated: 2026-01-15*
*Version: 1.1.0*

## Overview

This SOP defines how to run cold outreach campaigns for any project in the dev-sandbox. The system uses the **lead-scraper** project as the core engine, with project-specific configurations for different products/services.

## Prerequisites

Before starting a cold outreach campaign, verify the following:

| Requirement | Check Command | Expected Result |
|-------------|---------------|-----------------|
| **Twilio configured** | `grep TWILIO .env` | All 3 TWILIO vars set |
| **Apollo API key** | `grep APOLLO .env` | APOLLO_API_KEY has value |
| **ClickUp webhook** | `grep CLICKUP .env` | CLICKUP_API_TOKEN set |
| **Python environment** | `python --version` | Python 3.10+ |
| **Lead database exists** | `ls output/leads.json` | File exists |

**Quick Verification:**
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.scraper stats
# Should show: Total leads, enriched count, etc.
```

✅ **You should see**: Lead statistics without errors
❌ **If you see errors**: Check `.env` file and dependencies

---

## Hormozi Framework (Core Principles)

1. **Rule of 100**: 100 outreach attempts daily
2. **Cocktail Party Effect**: Personalize with 1-3 facts a friend would know
3. **Big Fast Value (BFV)**: Give away crazy value in 30 seconds
4. **Multi-touch**: 5-7 follow-ups before giving up
5. **Still Looking**: 9-word reactivation for dormant leads

## Project-Specific Configurations

### Configuration File: `projects/{project}/outreach_config.json`

```json
{
  "project_name": "fitness-influencer",
  "service_offered": "AI-powered content creation for fitness creators",

  "target_audience": {
    "business_types": ["gym", "personal trainer", "fitness studio", "yoga studio"],
    "decision_maker_titles": ["owner", "founder", "head coach", "general manager"],
    "pain_points": ["no_website", "few_reviews", "low_engagement", "manual_content"],
    "ideal_customer": "10K-100K follower fitness creators struggling with content consistency"
  },

  "search_parameters": {
    "categories": ["gym", "fitness center", "personal trainer", "yoga studio"],
    "locations": ["Naples, FL", "Fort Myers, FL", "Miami, FL"],
    "radius_meters": 25000,
    "employee_range": "1,50"
  },

  "templates": {
    "primary": "content_struggle",
    "follow_up_1": "social_proof",
    "follow_up_2": "still_looking"
  },

  "value_offer": {
    "lead_magnet": "Free 7-day content calendar with AI-generated post ideas",
    "discovery_call": "15-minute content strategy session",
    "demo": "Live demo creating a week of content in 10 minutes"
  }
}
```

## Step 1: Configure Project for Outreach

### 1.1 Create Project Outreach Config

```bash
# Create config file for your project
cat > projects/{project}/outreach_config.json << 'EOF'
{
  "project_name": "{project}",
  "service_offered": "{description of what you're selling}",
  ...
}
EOF
```

### 1.2 Define Target Audience

Answer these questions:
- Who buys this? (business type, size, role)
- What pain does it solve? (map to scraper pain_points)
- Where are they located? (geographic focus)
- What makes them a good fit? (qualification criteria)

### 1.3 Create Project-Specific Templates

Templates go in: `projects/lead-scraper/src/templates/{project}/`

```python
# projects/lead-scraper/src/templates/{project}.py

TEMPLATES = {
    "initial_reach": {
        "subject": "...",
        "body": "...",
        "pain_points": ["..."],
    },
    "follow_up_1": {...},
    "follow_up_2": {...},
    "still_looking": {...}
}
```

## Step 2: Scrape Leads for Project

```bash
# Navigate to lead-scraper
cd projects/lead-scraper

# Scrape based on project config
python -m src.scraper scrape \
    --category "{category from config}" \
    --area "{location}" \
    --all-areas

# Check results
python -m src.scraper stats
```

## Step 3: Enrich with Apollo

```bash
# Enrich leads that have websites (to find owner emails)
python -m src.scraper enrich --limit 100

# Check enrichment rate
python -m src.scraper stats
```

## Step 4: Run Dry-Run Campaign

```bash
# Preview emails without sending
python -m src.scraper outreach \
    --dry-run \
    --limit 10 \
    --template {template_name}
```

## Step 5: Send Real Campaign

```bash
# ONLY after reviewing dry-run output
python -m src.scraper outreach \
    --for-real \
    --limit 100 \
    --template {template_name}
```

## Step 6: Track & Follow Up

```bash
# Check campaign stats
python -m src.scraper outreach stats

# Generate follow-up list (leads who didn't reply after 3 days)
python -m src.scraper outreach follow-ups --days 3
```

---

## Project-Specific Outreach Profiles

### Profile: Fitness Influencer AI

| Parameter | Value |
|-----------|-------|
| **Target** | Fitness creators with 10K-100K followers |
| **Pain Points** | Content creation time, consistency, engagement |
| **Categories** | gym, personal trainer, fitness studio |
| **Lead Magnet** | Free 7-day content calendar |
| **Primary Template** | `content_struggle` |

**Subject**: "Creating fitness content is taking forever - I built a fix"

**Key Hook**: "I noticed you're posting 3x/week on Instagram. What if I could show you how to create a month of content in 2 hours?"

### Profile: MCP Aggregator / Rideshare Comparison

| Parameter | Value |
|-----------|-------|
| **Target** | Fleet managers, airport shuttles, corporate travel |
| **Pain Points** | Price comparison, booking complexity |
| **Categories** | transportation, fleet management, travel agency |
| **Lead Magnet** | Free ride price comparison report |
| **Primary Template** | `cost_savings` |

**Subject**: "Your Uber/Lyft spending - quick question"

**Key Hook**: "Most companies overpay for rideshare by 15-30%. I built a tool that compares prices across all providers in real-time."

### Profile: Amazon Seller Operations

| Parameter | Value |
|-----------|-------|
| **Target** | Amazon FBA sellers, ecommerce brands |
| **Pain Points** | Fee calculations, inventory tracking, profitability |
| **Categories** | ecommerce, retail, wholesale |
| **Lead Magnet** | Free FBA fee audit for 5 ASINs |
| **Primary Template** | `profit_leak` |

**Subject**: "Found $X hidden in your Amazon fees"

**Key Hook**: "Amazon sellers lose 5-10% profit to fee errors they don't know about. I audited similar sellers and found an average of $X/month in recoverable fees."

### Profile: Interview Prep AI

| Parameter | Value |
|-----------|-------|
| **Target** | Career coaches, recruiters, HR professionals |
| **Pain Points** | Interview preparation, candidate quality |
| **Categories** | staffing agency, career counseling, HR consulting |
| **Lead Magnet** | Free company research report |
| **Primary Template** | `candidate_prep` |

**Subject**: "Your candidates could interview 40% better"

**Key Hook**: "I built an AI that generates company-specific interview prep in 5 minutes - the same research that takes candidates 3 hours."

---

## Template Library

### Universal Templates (Work for Any Project)

1. **competitor_callback** - Ultra short, creates open loop
2. **still_looking** - 9-word reactivation
3. **free_audit** - Highest conversion, requires personalization
4. **social_proof** - Reference another customer's success

### Pain Point Templates

| Pain Point | Template | Key Message |
|------------|----------|-------------|
| `no_website` | `website_builder` | "80% of customers search online first" |
| `few_reviews` | `review_booster` | "12 to 67 reviews in 60 days" |
| `no_online_booking` | `booking_system` | "34% more bookings from online scheduling" |
| `low_engagement` | `content_strategy` | "Triple your engagement with AI content" |
| `manual_processes` | `automation_pitch` | "Save 10 hours/week with automation" |

---

## Metrics & Tracking

### Key Metrics to Track

| Metric | Target | Formula |
|--------|--------|---------|
| Open Rate | >40% | Opens / Sent |
| Reply Rate | >5% | Replies / Sent |
| Meeting Rate | >2% | Meetings / Sent |
| Enrichment Rate | >30% | Enriched / Attempted |

### Daily Tracking

```bash
# Generate daily report
python -m src.scraper outreach stats --format daily
```

### A/B Testing Templates

```bash
# Test two templates on same audience
python -m src.scraper outreach --template A --limit 50
python -m src.scraper outreach --template B --limit 50

# Compare after 3 days
python -m src.scraper outreach compare --template-a A --template-b B
```

---

## Quick Start Checklist

When starting cold outreach for a new project:

- [ ] Create `projects/{project}/outreach_config.json`
- [ ] Define target audience and pain points
- [ ] Create project-specific templates
- [ ] Scrape initial leads (aim for 500+)
- [ ] Enrich with Apollo (find owner emails)
- [ ] Dry-run 10 emails, review quality
- [ ] Send first batch of 100
- [ ] Schedule follow-ups (Day 3, Day 7)
- [ ] Track metrics weekly

## Commands Reference

```bash
# Scrape leads
python -m src.scraper scrape --category gym --all-areas

# Check stats
python -m src.scraper stats

# Enrich leads
python -m src.scraper enrich --limit 100

# List templates
python -m src.scraper templates

# Dry run outreach
python -m src.scraper outreach --dry-run --limit 10

# Send for real
python -m src.scraper outreach --for-real --limit 100

# Filter by pain point
python -m src.scraper outreach --pain-point no_website --limit 50
```

---

## Troubleshooting

### SMS Not Sending

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Twilio not configured" error | Missing env vars | Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to .env |
| "Invalid phone number" | Bad phone format | Ensure E.164 format (+1XXXXXXXXXX) |
| Messages sent but not received | Twilio balance depleted | Check balance at console.twilio.com |
| "Carrier violation" | Message flagged as spam | Review message content, reduce urgency language |

### Low Enrichment Rate

| Symptom | Cause | Solution |
|---------|-------|----------|
| Enrichment <10% | Leads without websites | Apollo needs website to find contacts |
| "API limit exceeded" | Apollo quota used | Check credits at app.apollo.io |
| No emails found | Business too small | Try scraping larger businesses |

### No Callbacks/Responses

| Symptom | Cause | Solution |
|---------|-------|----------|
| 0% reply rate after 100 sends | Template issue | Review template compliance, try different hook |
| Replies going to spam | Sender reputation | Warm up number with legitimate conversations first |
| Wrong audience | Pain point mismatch | Verify pain_point filter matches actual need |

### ClickUp Tasks Not Created

| Symptom | Cause | Solution |
|---------|-------|----------|
| "401 Unauthorized" | Token expired | Generate new API token |
| "List not found" | Wrong list ID | Run `python -m src.form_webhook clickup-lists` |
| Tasks missing data | Field mapping issue | Check form_webhook.py task creation |

---

## Rollback Procedures

### Stop a Campaign Mid-Run

```bash
# Ctrl+C to interrupt current batch
# View what was sent
python -m src.scraper outreach stats

# Leads already contacted are logged in:
# output/sms_campaigns.json or output/outreach_campaigns.json
```

### Remove Leads from Future Campaigns

```bash
# Add phone numbers to opt-out list
echo '"+1XXXXXXXXXX"' >> output/optout_list.json

# Verify lead won't be contacted
python -m src.scraper check-optout +1XXXXXXXXXX
```

### Handle Compliance Issues (STOP requests)

1. **Immediate**: Add to opt-out list (automatic if webhook running)
2. **Verify**: Check lead removed from future batches
3. **Document**: Log compliance action in campaign notes

```bash
# Process STOP request manually
python -m src.twilio_webhook process-optout --phone "+1XXXXXXXXXX"
```

### Undo Sent Messages (Not Possible)

⚠️ **SMS/Email cannot be unsent.** Prevention strategies:
- Always run `--dry-run` first
- Start with `--limit 10` to verify
- Review output before sending full batch

---

## Success Criteria

### Per-Step Verification

| Step | Success Indicator |
|------|------------------|
| **Configure** | `outreach_config.json` exists, valid JSON |
| **Scrape** | `stats` shows 100+ leads for target category |
| **Enrich** | >20% enrichment rate |
| **Dry-run** | 10 messages rendered without errors |
| **Send** | Messages delivered (check Twilio logs) |
| **Track** | ClickUp tasks created for responses |

### End-to-End Validation

- [ ] Leads scraped for target audience
- [ ] Enrichment complete (emails/phones found)
- [ ] Templates reviewed and approved
- [ ] Dry-run successful (no errors)
- [ ] First batch sent (10-25 messages)
- [ ] Webhook receiving replies
- [ ] ClickUp tasks being created
- [ ] Follow-up sequence scheduled
