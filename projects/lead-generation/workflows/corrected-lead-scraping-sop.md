# SOP: Corrected Lead Scraping & Outreach (v2.0)

*Last Updated: 2026-01-21*
*Version: 2.0.0*

## Overview

This SOP documents the corrected lead scraping process that prevents the January 2026 disaster where we sent "you don't have a website" messages to Planet Fitness, LA Fitness, and other major chains.

## The Problem We Fixed

**Root Cause**: The original scraper incorrectly flagged leads as `no_website` when:
1. The website field contained aggregator URLs (Yelp, Google Maps)
2. The business was a national chain with an obvious website
3. No validation was performed before sending outreach

**Impact**: 13 opt-outs from 137 sends (9.5% opt-out rate) - mostly angry franchise owners.

## The Solution

### 1. Website Validation (`website_validator.py`)

Checks if a URL is a real business website vs an aggregator:

```python
from src.website_validator import is_real_business_website

# Returns (is_real, reason)
is_real_business_website("https://yelp.com/biz/planet-fitness")
# -> (False, "Aggregator: yelp.com")

is_real_business_website("https://planetfitness.com")
# -> (True, "Custom domain")
```

**Aggregator domains detected**: Yelp, Google Maps, Facebook, Instagram, Mindbody, Vagaro, etc.

### 2. Chain Detection (`chain_detector.py`)

Identifies national fitness chains for appropriate messaging:

```python
from src.chain_detector import ChainDetector

detector = ChainDetector()
result = detector.is_chain("Planet Fitness Naples")
# -> ChainMatch(is_chain=True, chain_name="Planet Fitness", confidence=1.0)
```

**Chains detected**: Planet Fitness, LA Fitness, Gold's Gym, Anytime Fitness, Crunch Fitness, Orangetheory, CrossFit, YMCA, Pure Barre, Club Pilates, etc.

### 3. Pain Point Mapping

| Pain Point | Template Category | Example Templates |
|------------|-------------------|-------------------|
| `franchise` | Franchise templates | `franchise_intro`, `franchise_member_retention` |
| `no_website` | No website templates | `no_website_intro` (VERIFIED only) |
| `aggregator_only` | Aggregator templates | `aggregator_only_intro` |
| `low_rating` | Rating recovery | `low_rating_recovery` |
| `few_reviews` | Review templates | `few_reviews`, `few_reviews_v2` |
| `apollo_b2b` | B2B decision maker | `apollo_b2b_intro` |

## Correct Workflow

### Step 1: Scrape Leads with Validation

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Scrape with built-in validation
python -m src.scraper search \
    --category "gym" \
    --location "Naples, FL" \
    --radius 25000 \
    --output output/naples_gyms_validated.json
```

The scraper now automatically:
- Validates websites using `website_validator.py`
- Detects chains using `chain_detector.py`
- Assigns correct pain points

### Step 2: Review Chain Detection Report

```bash
python -m src.chain_detector report --file output/naples_gyms_validated.json
```

Output shows:
- Total leads
- Independent businesses (local outreach)
- Franchise locations (franchise templates)

### Step 3: Verify Template Assignment

```bash
python -m src.sms_outreach preview --limit 10 --dry-run
```

Check that:
- Franchises get `franchise_*` templates
- No-website leads get `no_website_*` templates
- All leads have appropriate messaging

### Step 4: Send Outreach

```bash
# Dry run first
python -m src.sms_outreach send --dry-run --limit 20

# Real send
python -m src.sms_outreach send --for-real --limit 20
```

## Template Selection Logic

```
Lead arrives
    ↓
Is Apollo B2B? → apollo_b2b_intro
    ↓
Is Franchise? → franchise_intro (NO WEBSITE CLAIMS)
    ↓
Has aggregator only? → aggregator_only_intro
    ↓
Verified no website? → no_website_intro
    ↓
Low rating? → low_rating_recovery
    ↓
Few reviews? → few_reviews
    ↓
Default → competitor_hook
```

## Never Do This Again

1. **Never claim "you don't have a website"** unless verified by `website_validator.py`
2. **Never send website templates to franchises** - they have corporate sites
3. **Always run chain detection** before outreach
4. **Always dry-run first** and review template assignments

## Files Changed

| File | Change |
|------|--------|
| `src/chain_detector.py` | NEW - Detects national chains |
| `src/google_places.py` | Added chain detection, updated pain points |
| `src/sms_outreach.py` | Added franchise, low_rating, aggregator templates |
| `src/outreach_optimizer.py` | Added template categories by pain point |

## Monitoring

Check opt-out rates by template:

```bash
python -m src.response_tracker report
```

Target metrics:
- Opt-out rate: <3%
- Response rate: >5%
- Hot lead rate: >1%

If opt-out rate spikes, immediately:
1. Pause outreach
2. Check which template is causing issues
3. Review leads receiving that template
4. Fix data or template

## References

- `src/website_validator.py` - Website validation logic
- `src/chain_detector.py` - Franchise detection
- `src/sms_outreach.py` - Template definitions
- `workflows/hormozi-optimization-protocol.md` - Response tracking
