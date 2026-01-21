# Cold Outreach Optimization Playbook

**Quick Reference Guide for Campaign Performance Improvement**

**Status**: 🔴 CRITICAL - All responses are opt-outs (0% positive)
**Goal**: Achieve 12% positive response rate within 90 days

---

## Current Performance (Jan 15, 2026)

```
CAMPAIGN: wave_1_no_website_jan15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Volume Metrics
   ✅ Sent:        98 messages
   ✅ Delivered:   98 (100% delivery rate)

📈 Response Metrics
   ⚠️  Responses:   14 (14.3% response rate)
   ❌ Hot Leads:   0
   ❌ Warm Leads:  0
   ❌ Cold Leads:  0
   🔴 Opt-outs:   14 (100% of responses)

💰 Revenue Impact
   Current:  $0
   Lost:     ~$4,200 (14 potential customers @ $300 avg)
```

---

## Root Cause: Why 100% Opt-Outs?

### 🔴 Problem #1: Targeting Error (CRITICAL)
**Evidence**: "we have a website\nSTOP" - Velocity Naples
**Evidence**: "if you took two seasons to Google us..." - P-Fit North Naples

**Issue**: Telling businesses with websites they have no website
- Makes William look unprepared
- Damages brand reputation
- Immediate opt-out trigger

**Fix**: Validate website detection (see Section 1 below)

---

### 🟡 Problem #2: Message Tone (HIGH)
**Current Message**:
```
Hi, this is William. I noticed [Business] doesn't have a website.
80% of customers search online first. Want a free mockup?
Reply STOP to opt out.
```

**Issues**:
- Too transactional (immediate pitch)
- No credibility signals (who is William?)
- No social proof (why trust this?)
- Generic marketing spam tone

**Fix**: Test variants with social proof (see Section 2 below)

---

### 🟡 Problem #3: Wrong Segment (MEDIUM)
**Gyms/Fitness Studios**:
- Many are franchises (Planet Fitness, LA Fitness) with corporate websites
- Already website-saturated segment
- Not the low-hanging fruit

**Fix**: Cohort analysis to find better targets (see Section 3 below)

---

## 90-Day Optimization Plan

### Phase 1: STOP THE BLEEDING (Week 1) 🩹

**Objective**: Fix targeting errors before sending more messages

#### Action 1.1: Validate "No Website" Leads
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper

# Check if businesses actually have websites
python -m src.scraper validate-websites --sample 100 --pain-point no_website

# Expected output:
# Checked: 100 leads
# False Positives: 15 (have websites despite being marked "no website")
# True Positives: 85 (verified no website)
# Accuracy: 85%
```

**Success Criteria**: <10% false positives

**If >10% false positives**: Fix website detection logic in `src/google_places.py` and `src/yelp.py`

---

#### Action 1.2: Segment Analysis
```bash
# Which business categories respond best?
python -m src.campaign_analytics cohorts --group-by category > output/cohort_analysis.txt

# Review results
cat output/cohort_analysis.txt
```

**Look for**:
- Categories with <5% opt-out rate
- Categories with 0 sends (untapped segments)
- Geographic patterns (Naples vs Bonita vs Fort Myers)

**Decision**: Pause gym outreach if opt-out rate >10%

---

### Phase 2: MESSAGE OPTIMIZATION (Weeks 2-4) ✍️

**Objective**: Find template with >8% positive response rate

#### Action 2.1: Create Template Variants

**Variant A: Social Proof**
```
Hi, this is William. I just helped 3 Naples gyms get online
(Fitness X saw +40% calls). Noticed you're not on Google yet.
Quick question - interested in a free mockup? Text STOP to opt out.
```
- **Hypothesis**: Social proof builds credibility
- **Expected**: +5-10% positive responses

**Variant B: Question-First**
```
Hi {name}, William here. Do you get customers asking if you
have a website? I help Naples businesses get online.
Worth a quick chat? Reply STOP to opt out.
```
- **Hypothesis**: Softer approach, opens dialogue
- **Expected**: +3-8% positive responses

**Variant C: Value-First**
```
Hi, William with Marceau Solutions. I noticed {business} isn't
showing up when I search online. Happy to send a free mockup -
no obligation. Interested? Reply STOP to opt out.
```
- **Hypothesis**: "not showing up" = less accusatory
- **Expected**: +4-9% positive responses

---

#### Action 2.2: Launch A/B Tests

**Test 1: Current vs Social Proof**
```bash
python -m src.ab_testing create \
    --name "current_vs_social_proof" \
    --control no_website_intro \
    --variant social_proof_intro \
    --sample-size 200 \
    --business marceau-solutions
```

**Test 2: Social Proof vs Question-First** (after Test 1 winner declared)
```bash
python -m src.ab_testing create \
    --name "social_vs_question" \
    --control social_proof_intro \
    --variant question_first_intro \
    --sample-size 200 \
    --business marceau-solutions
```

---

#### Action 2.3: Daily Monitoring (7 days)

**Morning Routine**:
```bash
# Check A/B test results
python -m src.ab_testing results --name "current_vs_social_proof"

# Dashboard
python -m src.campaign_analytics dashboard --days 7

# New responses
python -m src.campaign_analytics report | grep -A 10 "RESPONSE"
```

**Success Metrics**:
- Response rate: >10%
- Positive responses (hot+warm): >5%
- Opt-out rate: <5%

**After 7 days**:
```bash
# Statistical analysis
python -m src.ab_testing results --name "current_vs_social_proof"

# If winner declared with 85%+ confidence:
# 1. Archive losing template
# 2. Use winner as new control
# 3. Test new variant against winner
```

---

### Phase 3: MULTI-TOUCH SEQUENCES (Weeks 5-8) 🔄

**Objective**: Capture the 50-70% of responses that come from touches 2-5

#### Current: 1-Touch Strategy
```
Touch 1: Intro message
❌ If no response → Give up
```

**New: 7-Touch Strategy** (Hormozi Framework)
```
Touch 1 (Day 0):  Intro message (winning template from Phase 2)
Touch 2 (Day 3):  Value-add follow-up
Touch 3 (Day 7):  Case study share
Touch 4 (Day 15): Direct question
Touch 5 (Day 30): Scarcity ("last message")
Touch 6 (Day 45): Re-engage
Touch 7 (Day 60): Breakup message
```

**Touch 2 Template**:
```
Hi {name}, William again. I know you're busy. Wanted to share -
customers find 73% of local businesses on Google. Quick 10-min call
to show you what a website could do for {business}?
```

**Touch 3 Template**:
```
{name}, last message! Just finished a site for [Similar Business].
They got 12 calls in first week. Want me to send you their before/after?
No cost to look.
```

---

#### Action 3.1: Enable Multi-Touch Sequences
```bash
# Create sequence
python -m src.follow_up_sequence create \
    --name "Naples Gyms No Website - 7 Touch" \
    --pain-point no_website \
    --limit 100

# Daily processing (automate via cron)
python -m src.follow_up_sequence process-due
```

---

#### Action 3.2: Attribution Analysis
```bash
# After 4 weeks, analyze which touches drive responses
python -m src.campaign_analytics attribution

# Expected output:
# Touch 1: 25% of responses
# Touch 2: 30% of responses
# Touch 3: 25% of responses
# Touch 4+: 20% of responses
```

**Decision**: If Touch 1 <20%, improve intro template further

---

### Phase 4: COHORT OPTIMIZATION (Weeks 9-12) 🎯

**Objective**: +15% response rate from better targeting

#### Action 4.1: Find Best-Performing Cohorts
```bash
# Category analysis
python -m src.campaign_analytics cohorts --group-by category

# Location analysis
python -m src.campaign_analytics cohorts --group-by location

# Export for review
python -m src.campaign_analytics cohorts --group-by category > output/best_cohorts.txt
```

**Expected Insights**:
```
Best Cohorts (Response Rate):
1. Salon/Spa:        18.5% response, 12.3% hot+warm
2. Independent Gyms: 14.2% response, 9.1% hot+warm
3. Restaurants:      11.8% response, 7.5% hot+warm

Worst Cohorts:
4. Franchises:        3.2% response, 0.8% hot+warm
5. Retail:            5.1% response, 1.2% hot+warm
```

---

#### Action 4.2: Shift Budget to Winners
```bash
# Update campaign allocation
# Manual decision based on cohort data

# Example:
# - 60% of sends → Top cohort (Salon/Spa)
# - 25% of sends → Second best (Independent Gyms)
# - 15% of sends → Third best (Restaurants)
# - 0% of sends → Bottom performers
```

**Expected Impact**: +15-20% overall response rate from concentration

---

## Daily Operations Checklist

### Morning (15 minutes)
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper

# 1. Dashboard review
python -m src.campaign_analytics dashboard --days 1

# 2. Check new responses
python -c "
import json
from datetime import datetime, timedelta
with open('output/sms_replies.json') as f:
    data = json.load(f)
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent = [r for r in data['replies'] if r['date_sent'] > cutoff]
    print(f'Last 24h: {len(recent)} responses')
    for r in recent:
        print(f\"  {r['business_name']}: {r['category']} - {r['body'][:50]}\")
"

# 3. Process hot/warm leads
# Review ClickUp board for new tasks
# Respond within 24 hours
```

### Weekly (30 minutes)
```bash
# 1. Template leaderboard
python -m src.campaign_analytics template-scores > output/weekly_template_report.txt

# 2. Cohort analysis
python -m src.campaign_analytics cohorts --group-by category > output/weekly_cohort_report.txt

# 3. A/B test progress
python -m src.ab_testing list

# 4. Optimization recommendations
python -m src.campaign_optimizer recommend > output/weekly_recommendations.txt

# Review all 4 reports and adjust strategy
```

### Monthly (1 hour)
```bash
# 1. Comprehensive dashboard
python -m src.campaign_analytics dashboard --days 30 > output/monthly_dashboard.txt

# 2. Attribution analysis
python -m src.campaign_analytics attribution > output/monthly_attribution.txt

# 3. Revenue tracking
python -c "
import json
with open('output/campaign_analytics.json') as f:
    data = json.load(f)
    revenue = data['summary']['total_revenue']
    conversions = data['summary']['total_conversions']
    print(f'Monthly Revenue: \${revenue:,.2f}')
    print(f'Conversions: {conversions}')
    print(f'Avg Deal Size: \${revenue/conversions:,.2f}' if conversions > 0 else 'N/A')
"

# 4. Strategic review
# - What worked this month?
# - What didn't work?
# - What to test next month?
```

---

## Key Metrics to Track

### Leading Indicators (Predict Future Success)
| Metric | Current | Target (30d) | Target (90d) |
|--------|---------|--------------|--------------|
| **Delivery Rate** | 100% | >95% | >95% |
| **Overall Response Rate** | 14.3% | 10-15% | 15-20% |
| **Positive Response Rate** | 0% | 5-8% | 10-15% |
| **Opt-out Rate** | 100% | <5% | <3% |

### Lagging Indicators (Measure Revenue Impact)
| Metric | Current | Target (30d) | Target (90d) |
|--------|---------|--------------|--------------|
| **Hot+Warm Leads** | 0 | 5-8 | 12-20 |
| **Qualified Leads** | 0 | 3-5 | 8-15 |
| **Conversions** | 0 | 1-2 | 3-6 |
| **Revenue** | $0 | $300-$600 | $900-$1,800 |

---

## Red Flags 🚨

**STOP and reassess if you see**:

1. **Opt-out rate >10%** for 3+ consecutive days
   - **Action**: Pause campaigns immediately
   - **Root cause**: Targeting or message problem
   - **Fix**: Review responses, identify pattern, adjust

2. **Response rate <5%** after 100+ sends
   - **Action**: Message isn't resonating
   - **Root cause**: Wrong segment or poor offer
   - **Fix**: Test new template variants

3. **Zero hot/warm leads after 200+ sends**
   - **Action**: Fundamental strategy problem
   - **Root cause**: Offer not compelling or wrong audience
   - **Fix**: Revisit value proposition, test different pain points

4. **Delivery rate <90%**
   - **Action**: Carrier filtering your messages
   - **Root cause**: Flagged as spam
   - **Fix**: Reduce send volume, vary message content

---

## Success Milestones 🎯

### Month 1: Foundation
- ✅ Fix targeting (false positive rate <10%)
- ✅ Find winning template (>8% positive response)
- ✅ Opt-out rate <5%
- ✅ First hot lead responded to within 24h

### Month 2: Optimization
- ✅ Multi-touch sequences live
- ✅ Attribution showing 50%+ responses from touch 2+
- ✅ Top 3 cohorts identified and prioritized
- ✅ 3-5 qualified leads in pipeline

### Month 3: Scaling
- ✅ 12%+ positive response rate
- ✅ 3+ conversions (paying customers)
- ✅ $900+ revenue
- ✅ Automated workflow (minimal daily time)

---

## Tools Quick Reference

### Analytics Commands
```bash
# Dashboard (last N days)
python -m src.campaign_analytics dashboard --days 30

# Template comparison
python -m src.campaign_analytics templates

# Template leaderboard (scored 0-100)
python -m src.campaign_analytics template-scores

# Conversion funnel
python -m src.campaign_analytics funnel

# Multi-touch attribution
python -m src.campaign_analytics attribution

# Cohort analysis
python -m src.campaign_analytics cohorts --group-by category
python -m src.campaign_analytics cohorts --group-by location

# Get AI recommendations
python -m src.campaign_optimizer recommend
```

### A/B Testing Commands
```bash
# Create test
python -m src.ab_testing create \
    --name "test_name" \
    --control template1 \
    --variant template2 \
    --sample-size 200

# View results
python -m src.ab_testing results --name "test_name"

# List all tests
python -m src.ab_testing list
```

### Campaign Execution Commands
```bash
# Send batch (dry run first!)
python -m src.scraper sms --dry-run --limit 10 --template no_website_intro

# Send for real
python -m src.scraper sms --for-real --limit 100 --template no_website_intro

# Process follow-ups
python -m src.follow_up_sequence process-due

# Check campaign status
python -m src.follow_up_sequence status --campaign {campaign_id}
```

---

## Emergency Contacts

### If Something Goes Wrong

**High Opt-out Rate (>10%)**:
1. Pause all campaigns: `# Don't run process-due`
2. Review last 20 responses: `cat output/sms_replies.json`
3. Identify pattern (targeting error? message tone?)
4. Fix issue before resuming

**Twilio Account Issues**:
1. Check balance: https://console.twilio.com
2. Review compliance alerts
3. Check for flagged messages

**ClickUp Integration Broken**:
1. Verify API token: `echo $CLICKUP_API_TOKEN`
2. Check list ID: `echo $CLICKUP_LIST_ID`
3. Test API: `curl -H "Authorization: $CLICKUP_API_TOKEN" https://api.clickup.com/api/v2/team`

---

## Document Version

- **Version**: 1.0
- **Created**: 2026-01-21
- **Last Updated**: 2026-01-21
- **Next Review**: 2026-02-21 (monthly update)

---

**Remember**: The analytics system is world-class. The problem isn't tracking—it's **targeting and messaging**. Focus on fixing those first.

**Start here**: Phase 1, Action 1.1 (Validate "No Website" Leads)
