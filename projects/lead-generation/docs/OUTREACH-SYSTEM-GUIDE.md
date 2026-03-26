# Marceau Solutions Lead Scraper & Outreach System Guide

*Last Updated: 2026-01-22*
*Version: 2.0.0*

## Overview

This guide documents the complete lead generation and outreach system, including:
- Lead scraping (Google Places, Yelp, Apollo)
- Chain/franchise detection
- Pain point identification
- SMS outreach with A/B testing
- Response tracking and optimization
- Follow-up sequences

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LEAD GENERATION LAYER                                 │
├───────────────┬───────────────┬───────────────┬────────────────────────────┤
│ Google Places │     Yelp      │    Apollo     │     Manual Import          │
│   Scraper     │   Scraper     │   B2B API     │      (CSV/JSON)            │
└───────┬───────┴───────┬───────┴───────┬───────┴────────────┬───────────────┘
        │               │               │                    │
        ▼               ▼               ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VALIDATION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  website_validator.py  │  chain_detector.py  │  phone_validator.py          │
│  - Real vs aggregator  │  - 25+ chain patterns│  - Format validation         │
│  - Domain verification │  - Confidence scores │  - Carrier lookup            │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PAIN POINT IDENTIFICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Source     │  Pain Points Detected                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Google     │  no_website, aggregator_only, few_reviews, low_rating,         │
│  Places     │  franchise, no_hours, incomplete_profile                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Apollo     │  apollo_b2b, decision_maker, company_size                      │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPLATE SELECTION LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Priority Order:                                                             │
│  1. Apollo B2B → apollo_b2b_intro, apollo_decision_maker                    │
│  2. Franchise → franchise_intro (NO website claims!)                        │
│  3. Aggregator Only → aggregator_only_intro                                 │
│  4. No Website (verified) → no_website_intro                                │
│  5. Low Rating → low_rating_recovery                                        │
│  6. Few Reviews → few_reviews, few_reviews_v2                               │
│  7. Default → competitor_hook, social_proof                                 │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTREACH OPTIMIZER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase        │  Strategy                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Exploration  │  Equal distribution until 50 sends per template              │
│  Exploitation │  70% to winner, 30% to others for ongoing testing            │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SMS OUTREACH (Twilio)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phone: +1 855 239 9364                                                      │
│  Daily Limit: 140 SMS (soft limit)                                           │
│  Compliance: B2B exemption, STOP opt-out in every message                   │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE TRACKING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Categories: hot_lead, warm_lead, cold_lead, question, opt_out              │
│  Auto-ClickUp: Hot leads create ClickUp tasks automatically                 │
│  Metrics: Response rate, quality score per template                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start Commands

### Scraping Leads

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Google Places - Naples gyms
python -m src.scraper search \
    --category "gym" \
    --location "Naples, FL" \
    --radius 25000 \
    --output output/naples_gyms.json

# Apollo B2B - Decision makers
python -m src.apollo_scraper search \
    --titles "Owner,General Manager,Fitness Director" \
    --location "Naples, FL" \
    --industry "Health and Fitness" \
    --limit 100
```

### Chain Detection Report

```bash
# Check which leads are national chains
python -m src.chain_detector report --file output/naples_gyms.json

# Check a single business
python -m src.chain_detector check --name "Planet Fitness Naples"
```

### SMS Outreach

```bash
# ALWAYS dry run first
python -m src.sms_outreach send --dry-run --limit 10

# Preview messages for specific leads
python -m src.sms_outreach preview --limit 5

# Real send (after dry run approval)
python -m src.sms_outreach send --for-real --limit 20
```

### Optimization Status

```bash
# Check template performance
python -m src.outreach_optimizer status

# Get recommended allocation for next batch
python -m src.outreach_optimizer recommend --limit 50 --source google_places
```

### Response Tracking

```bash
# Record a response
python -m src.response_tracker record \
    --phone "+1XXXXXXXXXX" \
    --category hot_lead \
    --notes "Interested in booking system demo"

# View response summary
python -m src.response_tracker report
```

---

## File Structure

```
projects/shared/lead-scraper/
├── src/
│   ├── scraper.py              # Main scraper CLI
│   ├── google_places.py        # Google Places API integration
│   ├── yelp_scraper.py         # Yelp API integration
│   ├── apollo_scraper.py       # Apollo.io B2B leads
│   ├── chain_detector.py       # Franchise/chain detection
│   ├── website_validator.py    # Real website vs aggregator
│   ├── sms_outreach.py         # SMS templates & sending
│   ├── outreach_optimizer.py   # A/B testing & optimization
│   ├── response_tracker.py     # Response categorization
│   ├── follow_up_sequence.py   # Multi-touch follow-ups
│   ├── clickup_sync.py         # ClickUp CRM integration
│   └── models.py               # Data models
├── workflows/
│   ├── corrected-lead-scraping-sop.md
│   ├── template-selection-logic.md
│   ├── hormozi-optimization-protocol.md
│   ├── sms-campaign-sop.md
│   └── cold-outreach-sop.md
├── output/
│   ├── leads.json              # Scraped leads
│   ├── apollo_sequences.json   # Apollo B2B sequences
│   ├── sms_campaigns.json      # Campaign records
│   ├── outreach_optimizer_state.json
│   └── response_tracker.json
└── templates/
    └── sms/                    # SMS message templates
```

---

## SMS Templates Reference

### Template Categories by Pain Point

| Pain Point | Templates | Key Characteristic |
|------------|-----------|-------------------|
| `apollo_b2b` | `apollo_b2b_intro`, `apollo_decision_maker`, `apollo_automation_offer` | B2B decision-maker outreach |
| `franchise` | `franchise_intro`, `franchise_member_retention`, `franchise_operations` | NO website claims |
| `aggregator_only` | `aggregator_only_intro`, `aggregator_google_ranking` | Acknowledges Yelp/Google presence |
| `no_website` | `no_website_intro`, `direct_question` | ONLY for verified no-website |
| `low_rating` | `low_rating_recovery`, `low_rating_reputation` | Focus on reputation recovery |
| `few_reviews` | `few_reviews`, `few_reviews_v2`, `few_reviews_system` | Focus on review generation |
| (default) | `competitor_hook`, `social_proof` | Generic value hooks |

### Template Selection Priority

```
1. Is Apollo B2B?     → apollo_b2b_intro
2. Is Franchise?      → franchise_intro (NEVER no_website!)
3. Aggregator only?   → aggregator_only_intro
4. No website?        → no_website_intro (verified only)
5. Low rating?        → low_rating_recovery
6. Few reviews?       → few_reviews
7. Default            → competitor_hook
```

### Compliance Requirements

Every SMS template MUST include:
- ✅ "This is William" identification
- ✅ Business name personalization (`$business_name`)
- ✅ "Reply STOP to opt out" (or similar)
- ✅ Under 160 characters (for single segment)
- ✅ Clear CTA (question or link)

---

## Chain Detection

### Detected Chains (25+)

**Major Gym Chains:**
- Planet Fitness, LA Fitness, Gold's Gym, Anytime Fitness
- Crunch Fitness, 24 Hour Fitness, Equinox, Lifetime Fitness

**Boutique Fitness:**
- CrossFit, Orangetheory, Pure Barre, Club Pilates
- SoulCycle, Barry's Bootcamp, F45 Training, Burn Boot Camp

**Yoga/Wellness:**
- CorePower Yoga, YogaWorks, Bikram/Hot Yoga

**MMA/Boxing:**
- UFC Gym, Title Boxing Club, 9Round

**Organizations:**
- YMCA, RecPlex, Recreation Centers

### Adding New Chains

Edit `src/chain_detector.py`:

```python
NATIONAL_FITNESS_CHAINS = {
    "New Chain Name": [
        "new chain", "newchain", "new chain fitness"
    ],
    # ... existing chains
}
```

---

## A/B Testing Strategy

### Exploration Phase (First 50 sends per template)
- Equal distribution across all templates
- Goal: Gather baseline performance data
- Don't declare winners yet

### Exploitation Phase (After 50+ sends each)
- 70% volume to best performer
- 30% distributed to others
- Continuous testing never stops

### Quality Score Calculation

```
Quality Score = (hot_leads × 3 + warm_leads × 2 + responses × 1 - opt_outs × 2) / total_sent
```

### Minimum Sample Sizes
- 50 sends per template before evaluation
- 100 sends for statistical confidence
- 7 days minimum test duration

---

## Response Categories

| Category | Definition | Action |
|----------|------------|--------|
| `hot_lead` | Ready to book/buy | Create ClickUp task, priority follow-up |
| `warm_lead` | Interested, needs info | Schedule follow-up, add to nurture |
| `cold_lead` | Polite but not interested | Archive, maybe re-engage in 90 days |
| `question` | Has questions | Answer promptly, track in thread |
| `callback_requested` | Wants a call | Schedule immediately |
| `not_interested` | Clear no | Remove from sequence |
| `opt_out` | STOP received | Do not contact again (legally required) |
| `wrong_number` | Not the business | Remove, mark data quality issue |

---

## Follow-Up Sequence (Hormozi "Still Looking" Framework)

```
Day 0:  Initial outreach (intro message)
Day 2:  "Still looking for [solution]?"
Day 5:  Social proof: "Just helped [similar business]..."
Day 10: Direct question: "Quick yes or no..."
Day 15: Availability check: "Open to a 5-min call this week?"
Day 30: Breakup: "Closing your file unless..."
Day 60: Re-engage: "Checking back in on [problem]..."
```

### Exit Conditions
- Lead replies (any response)
- Lead opts out (STOP)
- Delivery fails 2x consecutive
- Callback scheduled
- Day 60 completed

---

## Daily Operations Checklist

### Morning (8-9 AM)
- [ ] Check Twilio console for overnight replies
- [ ] Categorize responses in response_tracker
- [ ] Process hot leads → ClickUp
- [ ] Run `python -m src.outreach_optimizer status`

### Midday (12-1 PM)
- [ ] Send daily outreach batch (if ready)
- [ ] Process follow-ups due: `python -m src.follow_up_sequence process-due`

### Evening (5-6 PM)
- [ ] Review day's metrics
- [ ] Update campaign notes
- [ ] Plan tomorrow's batch

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No website" sent to chain | Chain not in detector | Add to `NATIONAL_FITNESS_CHAINS` |
| High opt-out rate | Wrong template for segment | Review template selection logic |
| Low delivery rate | Carrier filtering | Slow down sending rate |
| Empty pain_points | Scraper didn't validate | Re-scrape with validation enabled |

### Verifying Template Selection

```bash
python3 -c "
from src.sms_outreach import SMSOutreachManager
from src.models import Lead

manager = SMSOutreachManager()

# Test franchise
lead1 = Lead(business_name='Planet Fitness Naples', phone='555-1234', pain_points=['franchise'])
print(f'Planet Fitness: {manager.select_template_for_lead(lead1, use_optimizer=False)}')

# Test no_website
lead2 = Lead(business_name='Joes Gym', phone='555-1234', pain_points=['no_website'])
print(f'Joes Gym: {manager.select_template_for_lead(lead2, use_optimizer=False)}')
"
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `workflows/corrected-lead-scraping-sop.md` | Post-January-disaster SOP |
| `workflows/template-selection-logic.md` | Visual flowchart of selection |
| `workflows/hormozi-optimization-protocol.md` | Follow-up sequence details |
| `workflows/sms-campaign-sop.md` | Campaign execution steps |
| `CLAUDE.md` (root) | SOP 18-23 for outreach operations |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-22 | Added chain detection, new templates, optimizer |
| 1.0.0 | 2026-01-15 | Initial system with basic scraper and SMS |

---

## Contact

**System Owner:** William Marceau Jr.
**Support:** Via Claude Code assistant
**Phone (Twilio):** +1 855 239 9364
