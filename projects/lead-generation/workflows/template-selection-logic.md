# Template Selection Logic

*Last Updated: 2026-01-22*

## Overview

This document describes how SMS templates are selected for each lead based on their pain points. The selection logic prioritizes avoiding false claims (like telling Planet Fitness they don't have a website).

## Selection Priority Order

```
┌─────────────────────────────────────────────────────────────────┐
│                     LEAD ARRIVES                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Is Apollo B2B?  │
                    │ (source=apollo) │
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ apollo_b2b_intro    │
                    │ apollo_decision_maker│
                    │ apollo_automation_offer│
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Is Franchise?   │
                    │ (Planet Fitness,│
                    │ LA Fitness, etc)│
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ franchise_intro     │  ← NO website claims!
                    │ franchise_member_retention│
                    │ franchise_operations│
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Aggregator Only?│
                    │ (has Yelp but   │
                    │ no real website)│
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ aggregator_only_intro│
                    │ aggregator_google_ranking│
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Verified No     │
                    │ Website?        │
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ no_website_intro    │  ← Only for VERIFIED no-website
                    │ direct_question     │
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Low Rating?     │
                    │ (under 3.5 stars)│
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ low_rating_recovery │
                    │ low_rating_reputation│
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Few/No Reviews? │
                    │ (under 10)      │
                    └────────┬────────┘
                             │ YES
                             ▼
                    ┌─────────────────────┐
                    │ few_reviews         │
                    │ few_reviews_v2      │
                    │ few_reviews_system  │
                    └─────────────────────┘
                             │ NO
                             ▼
                    ┌─────────────────────┐
                    │ competitor_hook     │  ← Safe default
                    │ social_proof        │
                    └─────────────────────┘
```

## Pain Point to Template Mapping

| Pain Point | Templates | Key Characteristic |
|------------|-----------|-------------------|
| `apollo_b2b` | `apollo_b2b_*` | B2B decision-maker outreach, uses $first_name |
| `franchise` | `franchise_*` | NO website claims, focus on automation |
| `aggregator_only` | `aggregator_*` | Acknowledges they have Yelp/Google presence |
| `no_website` | `no_website_*` | ONLY for verified no real website |
| `low_rating` | `low_rating_*` | Focus on reputation recovery |
| `few_reviews` | `few_reviews_*` | Focus on review generation |
| (default) | `competitor_hook`, `social_proof` | Generic value hooks |

## Critical Rules

### 1. Franchise Detection ALWAYS Runs First
```python
# In select_template_for_lead():
if "franchise" in pain_points:
    return "franchise_intro"  # BEFORE checking no_website!
```

### 2. Never Claim "No Website" For:
- Any franchise (Planet Fitness, LA Fitness, CrossFit, etc.)
- Any business with an aggregator page (Yelp, Facebook)
- Any business where website_validator couldn't verify

### 3. Chain Detector Flags Franchises During Scraping
```python
# In google_places.py _identify_pain_points():
chain_result = _chain_detector.is_chain(business_name)
if chain_result.is_chain and chain_result.confidence >= 0.7:
    pain_points.append("franchise")
```

## Example Scenarios

### Scenario 1: Planet Fitness Naples
```
Lead: Planet Fitness Naples
Pain Points: ["franchise"] (chain detector fired)
Template Selected: franchise_intro
Message: "Hi, this is William. I help local fitness owners like Planet Fitness Naples automate no-show follow-ups..."
```

### Scenario 2: Joe's Local Gym (no website)
```
Lead: Joe's Local Gym
Pain Points: ["no_website"] (verified no site)
Template Selected: no_website_intro
Message: "Hi, this is William. I noticed Joe's Local Gym doesn't have a website..."
```

### Scenario 3: Naples Yoga Studio (has Yelp only)
```
Lead: Naples Yoga Studio
Pain Points: ["aggregator_only"]
Template Selected: aggregator_only_intro
Message: "Hi, saw Naples Yoga Studio on Yelp but couldn't find your own website..."
```

## Testing Template Selection

```bash
# Test with sample leads
python3 -c "
from src.sms_outreach import SMSOutreachManager
from src.models import Lead

manager = SMSOutreachManager()

# Test franchise
lead1 = Lead(business_name='Planet Fitness', phone='555-1234', pain_points=['franchise'])
print(f'Planet Fitness: {manager.select_template_for_lead(lead1, use_optimizer=False)}')

# Test no_website
lead2 = Lead(business_name='Joes Gym', phone='555-1234', pain_points=['no_website'])
print(f'Joes Gym: {manager.select_template_for_lead(lead2, use_optimizer=False)}')
"
```

## Related Files

- `src/chain_detector.py` - Franchise detection
- `src/website_validator.py` - Website validation
- `src/sms_outreach.py` - Template definitions and selection
- `src/outreach_optimizer.py` - A/B testing allocation
- `src/google_places.py` - Pain point identification during scraping

## Version History

| Date | Change |
|------|--------|
| 2026-01-22 | Initial documentation |
| 2026-01-21 | Added franchise detection, new templates |
