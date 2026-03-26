# SOP: Cold Outreach Strategy Development & A/B Testing

*Last Updated: 2026-01-15*
*Version: 1.0.0*

## Overview

This SOP defines the process for developing, testing, and optimizing cold outreach strategies across campaigns. It ensures systematic improvement of response rates through hypothesis-driven A/B testing and data analysis.

## When to Use

- Starting a new outreach campaign
- Response rates below target (<10%)
- Testing new messaging approaches
- Expanding to new market segments
- Quarterly strategy reviews

## Key Principles

### The Hormozi Framework

| Principle | Application |
|-----------|-------------|
| **Rule of 100** | 100 outreaches per day until results |
| **Cocktail Party Rule** | Personalize with business name, show you know them |
| **Big Fast Value** | Lead with value, not ask (free mockup, audit, insight) |
| **Pattern Interrupt** | Open differently than competitors |
| **Social Proof** | Reference similar businesses, results |

### Multi-Touch Reality

**Key Insight**: 80% of sales require 5+ touches. Design for the sequence, not the single message.

| Touch | Purpose | Typical Template |
|-------|---------|------------------|
| 1 | Introduce, identify pain | `no_website_intro` |
| 2 | Reminder, still relevant? | `still_looking` |
| 3 | Social proof, credibility | `social_proof` |
| 4 | Direct question, qualify | `direct_question` |
| 5 | Scarcity, closing loop | `availability` |
| 6 | Breakup, last chance | `breakup` |
| 7 | Re-engagement | `re_engage` |

---

## Phase 1: Strategy Development

### Step 1.1: Define Target Segment

```markdown
## Target Segment Profile

**Segment Name**: [e.g., "Naples Gyms Without Websites"]
**Pain Point**: [e.g., "Missing 80% of customers who search online"]
**Decision Maker**: [e.g., "Owner, Manager"]
**Budget Range**: [$1,500 - $5,000]
**Urgency Level**: [1-10]

**Where They Are**:
- Google Maps / Yelp listings
- Facebook business pages
- Industry associations

**Current Alternatives**:
- DIY website builders
- Word of mouth
- Social media only
```

### Step 1.2: Craft Message Hypotheses

For each touch point, develop 2-3 message variants to test:

```markdown
## Message Hypothesis Template

**Touch Point**: [1-7]
**Hypothesis**: [What you believe will increase response]
**Control**: [Current/baseline message]
**Variant A**: [Alternative approach]
**Variant B**: [Another approach]
**Success Metric**: [Response rate, hot lead rate]
**Sample Size Needed**: [Minimum 30-50 per variant]
```

**Example Hypotheses**:

| Hypothesis | Test |
|------------|------|
| FOMO increases response | "Gym near you got 23 new members" vs. direct offer |
| Questions beat statements | "Do you have someone handling X?" vs. "I can help with X" |
| Short beats long | 80 chars vs 150 chars |
| Specific beats generic | "$2,500 website" vs "affordable website" |
| Pain focus beats gain focus | "You're losing customers" vs "Get more customers" |

### Step 1.3: Design A/B Test Plan

```markdown
## A/B Test Plan

**Test ID**: TEST_001
**Test Name**: Website Hook Variants
**Start Date**: 2026-01-15
**Target Sample Size**: 100 per variant

**Control (A)**:
- Template: no_website_intro
- Message: "Hi, this is William. I noticed {business_name} doesn't have a website. 80% of customers search online first. Want a free mockup? Reply STOP to opt out"

**Variant (B)**:
- Template: competitor_hook
- Message: "Hi, noticed a gym near {business_name} just added 23 members from their new website. Could do the same for you. Interested? -William. Reply STOP to opt out"

**Success Criteria**:
- Primary: Response rate (target: +5 percentage points)
- Secondary: Hot lead rate (target: +3 percentage points)
- Guardrail: Opt-out rate (<5%)

**Statistical Significance**: 85% confidence minimum
```

---

## Phase 2: Campaign Execution

### Step 2.1: Set Up Tracking

```bash
# Initialize analytics for new campaign
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.campaign_analytics update --campaign-id "test_001_website_hooks"
```

### Step 2.2: Split Test Groups

When running A/B tests, split leads evenly:

```bash
# Control group (first 50 leads)
python -m src.scraper sms --dry-run --pain-point no_website --limit 50 --template no_website_intro

# Variant group (next 50 leads)
python -m src.scraper sms --dry-run --pain-point no_website --limit 50 --offset 50 --template competitor_hook
```

### Step 2.3: Monitor Daily

```bash
# Daily check: View current metrics
python -m src.campaign_analytics report

# Template comparison
python -m src.campaign_analytics templates

# Funnel status
python -m src.campaign_analytics funnel
```

### Step 2.4: Record Responses

When replies come in (via Twilio webhook or manual):

```bash
# Record a response
python -m src.campaign_analytics response \
    --phone "+1239XXXXXXX" \
    --text "Yes, interested in learning more" \
    --category hot_lead

# Categories: hot_lead, warm_lead, cold_lead, opt_out
```

---

## Phase 3: Analysis & Optimization

### Step 3.1: Weekly Analysis (Every Friday)

Run after minimum 7 days or 100+ messages per variant:

```bash
# Generate full report
python -m src.campaign_analytics report > reports/weekly_$(date +%Y%m%d).txt

# Template comparison for A/B test winner
python -m src.campaign_analytics templates
```

### Step 3.2: Statistical Significance Check

**Minimum requirements before declaring winner**:
- 50+ messages per variant
- 7+ days of data
- 85%+ confidence level

**Quick significance calculator**:
```
Control: 50 sent, 5 responses = 10%
Variant: 50 sent, 9 responses = 18%
Difference: +8 percentage points
Significance: ~80% (needs more data)
```

### Step 3.3: Decision Framework

| Scenario | Action |
|----------|--------|
| Variant wins with 85%+ confidence | Scale variant, retire control |
| No significant difference | Continue test or try different hypothesis |
| Control wins | Document learning, try new variant |
| Variant has higher opt-out | Stop variant immediately |

### Step 3.4: Document Learnings

Add to `CAMPAIGN_LEARNINGS.md`:

```markdown
## Learning: [Date] - [Test Name]

**Hypothesis**: [What we tested]
**Result**: [Winner and by how much]
**Why It Worked**: [Analysis]
**Action Taken**: [What we changed]
**Future Tests**: [What to try next]
```

---

## Phase 4: Strategy Iteration

### Step 4.1: Quarterly Strategy Review

Every quarter, review:

1. **Overall response rates** - Are we improving?
2. **Best performing templates** - What patterns emerge?
3. **Conversion funnel** - Where are we losing leads?
4. **New hypotheses** - What should we test next?

### Step 4.2: New Segment Expansion

When expanding to new segments:

1. Clone successful templates
2. Adapt pain points and value props
3. Start with 50-lead test batch
4. Measure before scaling

### Step 4.3: Template Library Maintenance

Keep templates organized and versioned:

```
templates/
├── active/
│   ├── no_website_intro_v2.txt    # Current winner
│   └── social_proof_v1.txt
├── testing/
│   └── fomo_hook_v1.txt           # Currently in A/B test
└── retired/
    └── no_website_intro_v1.txt    # Previous version
```

---

## Analytics Commands Reference

```bash
# Import campaign data to analytics
python -m src.campaign_analytics update --campaign-id "campaign_name"

# View comprehensive report
python -m src.campaign_analytics report

# Compare template performance
python -m src.campaign_analytics templates

# View conversion funnel
python -m src.campaign_analytics funnel

# Record a response
python -m src.campaign_analytics response --phone "+1XXXXXXXXXX" --text "Message" --category hot_lead

# Record a conversion
python -m src.campaign_analytics convert --lead-id "abc123" --value 2500

# Send follow-up to previous campaign
python -m src.send_followup --message "Your message" --for-real
```

---

## Tracking Checklist

### Per Campaign
- [ ] Campaign ID assigned
- [ ] Analytics initialized
- [ ] Templates documented
- [ ] A/B test plan (if applicable)

### Per Response
- [ ] Response recorded in analytics
- [ ] Category assigned (hot/warm/cold/optout)
- [ ] ClickUp task created (if qualified)
- [ ] Follow-up scheduled (if qualified)

### Weekly Review
- [ ] Analytics report generated
- [ ] Template comparison reviewed
- [ ] Funnel analyzed
- [ ] Learnings documented
- [ ] Next week's tests planned

### Quarterly Review
- [ ] Overall metrics vs. targets
- [ ] Best performers identified
- [ ] New hypotheses documented
- [ ] Template library cleaned
- [ ] Strategy updated

---

## Integration Points

| System | Integration |
|--------|-------------|
| **sms_campaigns.json** | Raw send records |
| **campaign_analytics.json** | Processed metrics |
| **lead_records.json** | Per-lead tracking |
| **ClickUp** | Qualified leads only (hot/warm) |
| **Google Sheets** | Backup logging |
| **CLAUDE.md** | SOP reference |

---

## Success Metrics

| Metric | Target | Red Flag |
|--------|--------|----------|
| Response rate | >10% | <5% |
| Hot lead rate | >3% | <1% |
| Opt-out rate | <3% | >5% |
| Conversion rate | >1% | 0% after 100+ contacts |
| Days to response | <5 | >14 |

---

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Very low response rate (<2%) | Wrong segment, weak message | Try different pain point or hook |
| High opt-out rate (>5%) | Too aggressive, wrong target | Soften message, verify list quality |
| Responses but no conversions | Qualification issue | Improve follow-up process |
| Good first touch, weak follow-up | Sequence not optimized | Test different follow-up templates |

---

*SOP Version 1.0.0 - 2026-01-15*
