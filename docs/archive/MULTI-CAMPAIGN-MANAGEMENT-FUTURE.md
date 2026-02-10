# Multi-Campaign Management System (Future Plan)

**Created:** 2026-01-19
**Status:** DEFERRED - Run after HVAC proof of concept
**Trigger:** When HVAC campaign proves successful (2%+ reply rate, 2+ jobs booked)

---

## Current State (Single Campaign)

**What we're doing now:**
- HVAC customer acquisition only (500 homeowners via SMS)
- Single target audience (Naples homeowners)
- Single channel (SMS)
- Manual tracking (check replies, count jobs booked)

**Why we're starting simple:**
- Proof of concept first
- Learn what works before scaling
- Don't overcomplicate before we have data

---

## Future State (Multi-Campaign Management)

**Once HVAC proves successful, we'll run:**

| Campaign | Target Audience | Channel | Monthly Budget |
|----------|----------------|---------|----------------|
| **HVAC Customer Acquisition** | Naples homeowners | SMS + TikTok | $5-100 |
| **Marceau Solutions Lead Gen** | B2B businesses (gyms, restaurants, etc.) | LinkedIn + Apollo email | $0-50 |
| **Total** | 2 campaigns in parallel | 3 channels | $5-150 |

**Goal:** Prove we can manage 2 campaigns simultaneously before adding Shipping (or other clients)

---

## Multi-Campaign Tracking Dashboard (To Build)

### What We Need to Track:

**Per Campaign:**
- Contacts sent (SMS/email)
- Delivery rate (%)
- Reply rate (%)
- Opt-out rate (%)
- Interested leads (count)
- Callback requests (count)
- Jobs/clients booked (count)
- Revenue generated (if known)
- Cost per contact
- Cost per interested lead
- Cost per conversion
- ROI (revenue / cost)

**Cross-Campaign:**
- Total spend across all campaigns
- Budget utilization (% of $500 cap)
- Best performing campaign (by ROI)
- Worst performing campaign (to pause)
- Channel comparison (SMS vs Email vs LinkedIn)

---

## Tools to Build

### 1. Multi-Campaign Dashboard Script

**File:** `projects/lead-scraper/src/campaign_dashboard.py`

**Usage:**
```bash
# View all active campaigns
python -m src.campaign_dashboard

# Compare campaigns side-by-side
python -m src.campaign_dashboard --compare

# Show top performers
python -m src.campaign_dashboard --top 3

# Show underperformers (to pause)
python -m src.campaign_dashboard --bottom 3
```

**Output example:**
```
==================================================
MULTI-CAMPAIGN DASHBOARD
==================================================
Total Campaigns: 2 active, 0 paused
Total Spend: $105.00 / $500.00 budget (21%)
Total Contacts: 1,200 (600 HVAC, 600 Marceau)
Overall ROI: 1,900% ($2,000 revenue on $105 spend)

Campaign Performance:
----------------------------------------------------
1. HVAC Homeowners (SMS)
   Contacts: 600 | Replies: 45 (7.5%) | Opt-outs: 30 (5%)
   Interested: 12 | Booked: 4 | Revenue: $2,000 (side income)
   Cost: $6 | ROI: 33,333%
   Status: ✅ WINNING - Continue

2. Marceau Solutions (Apollo Email)
   Contacts: 600 | Opens: 180 (30%) | Replies: 18 (3%)
   Interested: 5 | Calls booked: 2 | Revenue: $0 (pipeline)
   Cost: $0 (free Apollo emails) | ROI: N/A (no revenue yet)
   Status: ⚠️ TESTING - Need more data

Recommendations:
- Scale HVAC SMS (increase from 600 → 1,000/month)
- Continue Marceau email sequence (wait for conversions)
- Budget allocation: HVAC 60% / Marceau 40%
```

---

### 2. Campaign Comparison Report

**File:** `projects/lead-scraper/src/campaign_comparison.py`

**Features:**
- Side-by-side metrics for all campaigns
- Identify winning channels (SMS vs Email vs LinkedIn)
- Recommend budget reallocation
- Detect underperforming campaigns (auto-suggest pause)

**Usage:**
```bash
python -m src.campaign_comparison --metric roi
python -m src.campaign_comparison --metric reply_rate
python -m src.campaign_comparison --export comparison.pdf
```

---

### 3. Budget Allocator (Smart)

**File:** `projects/lead-scraper/src/budget_allocator.py`

**What it does:** Automatically recommends budget allocation based on campaign performance

**Logic:**
```
IF campaign ROI > 1,000%:
  Recommend: Increase budget 2x

IF campaign ROI 100-1,000%:
  Recommend: Maintain budget

IF campaign ROI < 100%:
  Recommend: Pause campaign, reallocate budget to winners

IF campaign spend > 25% of total budget AND ROI < 500%:
  Recommend: Cap budget, test alternative messaging
```

**Usage:**
```bash
python -m src.budget_allocator --total-budget 500

# Output:
# Recommended Allocation:
# - HVAC SMS: $300/month (60% of budget) - High ROI
# - Marceau Email: $100/month (20%) - Testing phase
# - Reserve: $100/month (20%) - New campaign experiments
```

---

### 4. Apollo.io + SMS Unified Tracker

**File:** `projects/lead-scraper/src/unified_tracker.py`

**What it does:** Tracks contacts across BOTH SMS (Twilio) and Email (Apollo) in one place

**Features:**
- Deduplication (don't SMS someone you already emailed)
- Cross-channel attribution (did they respond via SMS or email?)
- Unified opt-out list (if they STOP SMS, don't email them)

**Usage:**
```bash
# Check if contact already reached
python -m src.unified_tracker check --phone +12395551234

# Record multi-channel outreach
python -m src.unified_tracker record \
  --phone +12395551234 \
  --email john@example.com \
  --channel sms \
  --campaign hvac-homeowners-jan19

# Get contact history (all touchpoints)
python -m src.unified_tracker history --phone +12395551234
```

---

## Campaign Workflow (Future Multi-Campaign)

### Step 1: Launch New Campaign

```bash
# Create campaign in tracker
python -m src.campaign_dashboard create \
  --name "Marceau Solutions - Naples Gyms" \
  --target-audience "Naples gym owners" \
  --channel apollo_email \
  --budget 50 \
  --goal "5 discovery calls booked"

# Scrape leads
python -m src.scraper scrape \
  --type business \
  --industry gym \
  --location "Naples, FL" \
  --limit 600

# Enrich leads (Apollo)
python -m src.apollo_enrichment \
  --input leads.json \
  --output enriched_leads.json

# Launch Apollo email sequence
python -m src.apollo_workflows enroll \
  --list "Naples Gyms" \
  --sequence "Marceau Intro - Gym Automation"
```

### Step 2: Monitor Daily

```bash
# Check all campaigns (morning routine)
python -m src.campaign_dashboard

# Check responses that need human follow-up
python -m src.unified_tracker pending
```

### Step 3: Weekly Review

```bash
# Generate comparison report
python -m src.campaign_comparison --export weekly_report.pdf

# Get budget recommendations
python -m src.budget_allocator --total-budget 500

# Decide: Scale winners, pause losers
```

### Step 4: Adjust Budget

```bash
# Increase budget for winning campaign
python -m src.campaign_dashboard update \
  --campaign "HVAC Homeowners" \
  --budget 200 \
  --reason "ROI 33,333% - scale up"

# Pause underperforming campaign
python -m src.campaign_dashboard pause \
  --campaign "Marceau Solutions - Naples Gyms" \
  --reason "ROI < 100% after 30 days"
```

---

## Parallel Campaign Examples

### Example 1: HVAC + Marceau Solutions (B2B)

| Campaign | Audience | Channel | Budget | Expected Outcome |
|----------|----------|---------|--------|------------------|
| HVAC Homeowners | 1,000 Naples homeowners | SMS | $10/month | 4-8 jobs booked, $1K-4K side income |
| Marceau Gyms | 600 Naples gym owners | Apollo email | $0 (free emails) | 2-5 discovery calls, 1 paid client |
| **Total** | 1,600 contacts | 2 channels | **$10/month** | $1K-4K income + 1 client ($5K+) |

**Why this works:**
- Different audiences (homeowners vs gym owners)
- Different channels (SMS vs email)
- Different goals (side income vs paid clients)
- Low cost ($10/month total)

---

### Example 2: HVAC + Marceau Solutions (Multiple B2B Verticals)

| Campaign | Audience | Channel | Budget | Expected Outcome |
|----------|----------|---------|--------|------------------|
| HVAC Homeowners | 1,000 Naples homeowners | SMS | $10/month | 4-8 jobs, $1K-4K |
| Marceau Gyms | 600 Naples gyms | Apollo email | $0 | 2-5 calls, 1 client |
| Marceau Restaurants | 600 Naples restaurants | Apollo email | $0 | 2-5 calls, 1 client |
| Marceau Salons | 600 Naples salons | Apollo email | $0 | 2-5 calls, 1 client |
| **Total** | 2,800 contacts | 2 channels | **$10/month** | $1K-4K + 3 clients ($15K+) |

**How to manage:**
- All B2B campaigns use Apollo (same tool, different sequences)
- HVAC uses SMS (different tool, different audience)
- Unified tracker ensures no duplicate outreach
- Dashboard shows all 4 campaigns side-by-side

---

## When to Implement Multi-Campaign System

### Trigger Conditions:

✅ **HVAC campaign proves successful:**
- Reply rate ≥ 2%
- Opt-out rate ≤ 10%
- At least 2 jobs booked
- Positive ROI (side income > ad spend)

✅ **Ready to add Marceau Solutions outreach:**
- Have bandwidth to manage 2 campaigns
- Apollo.io pixel installed (website visitors tracked)
- AI email sequences tested (1-2 templates ready)

✅ **Budget allows:**
- HVAC + Marceau total < $150/month
- Still under $500/month cap
- Buffer room for experiments

### Timeline:

- **Week 1-4 (Jan 19 - Feb 15):** HVAC proof of concept (single campaign)
- **Week 5-6 (Feb 16 - Mar 1):** Build multi-campaign tools (dashboard, tracker, allocator)
- **Week 7+ (Mar 2+):** Launch Marceau Solutions campaign in parallel with HVAC

---

## Files to Create (When Ready)

1. `projects/lead-scraper/src/campaign_dashboard.py` - Main dashboard
2. `projects/lead-scraper/src/campaign_comparison.py` - Side-by-side comparison
3. `projects/lead-scraper/src/budget_allocator.py` - Smart budget recommendations
4. `projects/lead-scraper/src/unified_tracker.py` - Cross-channel contact tracking
5. `projects/lead-scraper/workflows/multi-campaign-management.md` - SOP for managing multiple campaigns

---

## Success Criteria

**We'll know multi-campaign management is working when:**

1. ✅ Can launch new campaign in < 1 hour (scrape → enrich → send)
2. ✅ Daily check-in takes < 15 minutes (all campaigns reviewed)
3. ✅ No missed responses (unified tracker catches everything)
4. ✅ No duplicate outreach (same person contacted via multiple channels)
5. ✅ Budget stays under $500/month (auto-alerts if approaching cap)
6. ✅ Can compare campaigns objectively (data-driven decisions)
7. ✅ Winners scale automatically (more budget → more results)
8. ✅ Losers pause automatically (avoid wasting money)

---

## Current Priorities (Before Multi-Campaign)

**Don't build this yet. Focus on:**

1. ✅ HVAC SMS campaign ($5, 500 homeowners) - Proof of concept
2. ✅ Measure results (reply rate, jobs booked, side income)
3. ✅ Apollo.io setup (website visitor tracking, email sequences)
4. ✅ TikTok organic content (HVAC brand awareness)

**Build multi-campaign system only when:**
- HVAC proves successful (≥2 jobs booked)
- Ready to add Marceau Solutions outreach
- Have bandwidth to manage 2+ campaigns

---

**Summary:** Multi-campaign management is the future, but we're starting with single-campaign proof of concept (HVAC) first. Once that works, we'll build the tools to manage HVAC + Marceau Solutions in parallel, then potentially add more campaigns (Shipping, other B2B verticals) without losing our minds.

**Deferred to:** After HVAC campaign results (Feb 15+)
