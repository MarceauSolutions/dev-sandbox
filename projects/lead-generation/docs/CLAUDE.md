# Lead Scraper & SMS Campaign System

## What This Does
Local business lead generation tool for SW Florida (Naples, Fort Myers) with multi-source scraping (Google Places, Yelp, Apollo), pain point detection, SMS cold outreach via Twilio, multi-touch follow-up sequences, campaign analytics, and ClickUp CRM integration.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Scrape leads
python -m src.scraper scrape --category "gym" --area "Naples, FL"
python -m src.scraper scrape --all-categories --all-areas

# Filter leads by pain point
python -m src.scraper filter --pain-point no_website
python -m src.scraper filter --category gym --city Naples --has-phone

# SMS campaign (always dry-run first)
python -m src.scraper sms --dry-run --limit 5 --template no_website_intro
python -m src.scraper sms --for-real --limit 10 --pain-point no_website

# Campaign analytics
python -m src.campaign_analytics report
python -m src.campaign_analytics templates
python -m src.campaign_analytics funnel

# Follow-up sequences
python -m src.follow_up_sequence create --name "Naples Gyms" --pain-point no_website --limit 100
python -m src.follow_up_sequence process-due

# Export leads
python -m src.scraper export --format csv
python -m src.scraper stats
```

## Architecture
- **`src/scraper.py`** - Main CLI entry point for scraping and SMS
- **`src/google_places.py`** + **`src/yelp.py`** - Lead source scrapers
- **`src/apollo.py`** + **`src/apollo_pipeline.py`** - Apollo.io integration for enrichment
- **`src/sms_outreach.py`** + **`src/sms_scheduler.py`** - Twilio SMS sending with rate limiting
- **`src/twilio_webhook.py`** - Inbound SMS reply handler (webhook server)
- **`src/follow_up_sequence.py`** - 7-touch, 60-day Hormozi "Still Looking" follow-up engine
- **`src/campaign_analytics.py`** - Response tracking, A/B testing, funnel analysis
- **`src/lead_scoring.py`** - Lead qualification scoring
- **`src/apollo_to_clickup.py`** + **`src/crm_sync.py`** - CRM sync (hot leads only)
- **`src/opt_out_manager.py`** - TCPA compliance, STOP handling
- **`templates/`** - SMS message templates (must be approved before sending)
- **`output/`** - Scraped leads (JSON/CSV), campaign data
- **`workflows/`** - 19 workflow SOPs covering scraping, SMS, follow-ups, monitoring

## Project-Specific Rules

### ⛔ TCPA HARD RULE — NO COLD SMS (NON-NEGOTIABLE)
**Never send a first-contact SMS to any prospect who has not explicitly opted in.**
- Opt-out handling (STOP) is NOT sufficient — prior express consent is required before the first text.
- TCPA fines: $500 (unintentional) to $1,500 (willful) **per message**. 100 cold texts = up to $150,000 liability.
- `sms_outreach.py` now hard-blocks any lead without `sms_consent: true`. This cannot be bypassed.
- **How a lead earns SMS consent:** They reply to an email, fill out a contact form, or verbally agree during a call — then set `sms_consent: true` manually on their record.
- Cold outreach to prospects = **email + phone calls only**. SMS is for opted-in contacts only.
- This same rule is what we sell to clients. We cannot violate it ourselves.

### Other Rules
- TCPA compliance required: "This is William" in every SMS, "Reply STOP" required, no messages before 8am/after 9pm
- Always dry-run SMS campaigns before real sends
- Twilio phone: +1 855 239 9364 (configured via `TWILIO_*` env vars in root `.env`)
- Only push hot/warm leads to ClickUp (not every contact)
- Apollo API has credit limits -- use `src/check_actual_costs.py` to monitor
- Campaign data stored in `output/sms_campaigns.json`
- Follow-up sequence: Day 0 (intro) -> Day 2, 5, 10, 15, 30, 60 (escalating touches)

## Relevant SOPs
- SOP 18: SMS Campaign Execution (template approval, dry run, send)
- SOP 19: Multi-Touch Follow-Up Sequence (7-touch, 60-day Hormozi framework)
- SOP 22: Campaign Analytics & Tracking (response rates, funnel, A/B tests)
- SOP 23: Cold Outreach Strategy Development (hypotheses, A/B testing)
- `workflows/sms-campaign-sop.md` - Step-by-step SMS campaign guide
- `workflows/cold-outreach-sop.md` - Full cold outreach procedure
