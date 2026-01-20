# Cost Budget Tracking - HVAC & Shipping Customer Acquisition

**Created:** 2026-01-19
**Purpose:** Ensure we don't overspend on ads/outreach for practice projects (HVAC + Shipping)
**Problem:** These are testimonial clients (not paying full price), need to cap costs

---

## Budget Philosophy: Don't Lose Money on Free Work

**Key Principle:** These are **practice projects** to get testimonials, NOT profit centers yet.

**Budget Rule:**
- **Total spend on HVAC + Shipping ads/outreach:** Max $500/month TOTAL
- **Why $500/month:** Your side income ($1K-4K/month) should MORE than cover costs
- **Break-even goal:** Side income > Ad spend + time investment

---

## Current Monthly Costs (Breakdown)

### Fixed Costs (Already Paying)

| Service | Purpose | Monthly Cost | Annual Cost |
|---------|---------|--------------|-------------|
| **Twilio (SMS + Voice)** | SMS campaigns + Voice AI | $50-150 | $600-1,800 |
| **Hosting (GitHub Pages)** | HVAC + Shipping websites | $0 (free) | $0 |
| **Domain (2 domains)** | swflorida-comfort-hvac.com + squarefoot-shipping.com | $2 | $24 |
| **ClickUp CRM** | Lead tracking | $0 (free tier) | $0 |
| **Google Workspace** | Email, Sheets, Forms | $6 | $72 |
| **TOTAL FIXED** | | **$58-158/month** | **$696-1,896/year** |

**Note:** These are sunk costs - you're paying them anyway for dev-sandbox infrastructure.

---

### Variable Costs (Campaign-Specific - WATCH THESE)

| Campaign | Cost Type | Cost Per Unit | Budget Limit | Total Budget |
|----------|-----------|---------------|--------------|--------------|
| **HVAC SMS (Homeowners)** | SMS outreach | $0.01/message | 500 contacts | **$5** |
| **Shipping SMS (E-commerce)** | SMS outreach | $0.01/message | 100 contacts | **$1** |
| **HVAC Google Ads (Optional)** | PPC ads | $5-15/click | 20 clicks/month | **$100-300** |
| **HVAC Google LSA (Optional)** | Pay-per-lead | $25-50/lead | 10 leads/month | **$250-500** |
| **TOTAL VARIABLE** | | | | **$6-806/month** |

---

## RECOMMENDED Budget (Conservative)

### Month 1 (January 2026) - Testing Phase

**Goal:** Test campaigns at LOW cost, measure results before scaling.

| Campaign | Budget | Why |
|----------|--------|-----|
| **HVAC SMS (Homeowners)** | $5 (500 contacts @ $0.01 each) | Test messaging, measure reply rate |
| **Shipping SMS (E-commerce)** | $0 (PAUSED - no outreach) | Not targeting e-commerce sellers |
| **Google Ads (HVAC)** | $0 (SKIP Month 1) | Wait for SMS results first |
| **Google LSA (HVAC)** | $0 (SKIP Month 1) | Wait for SMS results first |
| **TOTAL Month 1** | **$5** | Ultra-low cost testing (HVAC only) |

**Expected ROI (Month 1):**
- Spend: $5 (HVAC only - Shipping paused)
- HVAC jobs booked: 2-4 (from SMS campaign)
- Your side income: $500-2,000 (helping on jobs)
- **ROI: 10,000% - 40,000%** (you make $500-2K on $5 spend)

**Decision Point After Month 1:**
- If SMS works (2%+ reply rate) → Continue SMS, stay at $6/month
- If SMS doesn't work (<1% reply rate) → Pause SMS, try Google Ads instead

---

### Month 2-3 (February-March) - Scale What Works

**IF SMS campaigns worked:**
- Continue SMS at $6/month (same budget)
- NO need to increase spend if getting results

**IF SMS didn't work:**
- **Option A:** Try Google Ads (HVAC only) - $100/month budget
  - 20 clicks @ $5/click = 2-3 leads = 1-2 jobs booked
  - Your side income: $500-2K (still profitable)

- **Option B:** Try Google LSA (HVAC only) - $250/month budget
  - 10 leads @ $25/lead = 5-7 jobs booked
  - Your side income: $1K-3K (very profitable)

**Maximum Spend (Month 2-3):** $250/month (if switching to Google LSA)

---

## Cost Tracking System

### Daily Cost Monitoring

**Command:**
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Check Twilio balance and usage
python -m src.cost_tracker --service twilio --period month

# Check total campaign costs
python -m src.cost_tracker --campaign hvac-homeowners-jan19

# Alert if over budget
python -m src.cost_tracker --alert-threshold 500
```

**File:** `projects/lead-scraper/src/cost_tracker.py`

```python
#!/usr/bin/env python3
"""
Track campaign costs and alert if over budget.

Usage:
  python -m src.cost_tracker --service twilio --period month
  python -m src.cost_tracker --campaign hvac-homeowners-jan19
  python -m src.cost_tracker --alert-threshold 500
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

def get_twilio_usage(period='month'):
    """Get Twilio usage for current period."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # Get SMS usage
    sms_usage = client.usage.records.list(
        category='sms',
        start_date='2026-01-01',
        end_date='2026-01-31'
    )

    total_sms = sum([record.count for record in sms_usage])
    total_cost = sum([float(record.price) for record in sms_usage])

    return {
        'sms_count': total_sms,
        'sms_cost': total_cost,
        'voice_cost': 0,  # Add if using Voice AI
        'total_cost': total_cost
    }

def check_budget_alert(threshold=500):
    """Alert if total spend exceeds threshold."""
    usage = get_twilio_usage()

    if usage['total_cost'] > threshold:
        print(f"⚠️  BUDGET ALERT: ${usage['total_cost']:.2f} spent (threshold: ${threshold})")
        print(f"   SMS: {usage['sms_count']} messages (${usage['sms_cost']:.2f})")
        print(f"   ACTION: Pause campaigns or increase budget")
    else:
        print(f"✅ Budget OK: ${usage['total_cost']:.2f} / ${threshold} spent")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--service', choices=['twilio', 'google_ads'])
    parser.add_argument('--period', choices=['day', 'week', 'month'], default='month')
    parser.add_argument('--campaign')
    parser.add_argument('--alert-threshold', type=float, default=500)

    args = parser.parse_args()

    if args.service == 'twilio':
        usage = get_twilio_usage(period=args.period)
        print(f"Twilio Usage ({args.period}):")
        print(f"  SMS: {usage['sms_count']} messages (${usage['sms_cost']:.2f})")
        print(f"  Total: ${usage['total_cost']:.2f}")

    check_budget_alert(threshold=args.alert_threshold)
```

---

## Campaign ROI Calculator

**Track:** For every dollar spent, how much revenue did you generate?

**File:** `projects/lead-scraper/src/campaign_roi.py`

```python
#!/usr/bin/env python3
"""
Calculate ROI for customer acquisition campaigns.

Usage:
  python -m src.campaign_roi --campaign hvac-homeowners-jan19
"""

import json

def calculate_roi(campaign_name):
    """
    Calculate ROI for a campaign.

    Inputs:
    - Campaign cost (SMS, ads, etc.)
    - Jobs booked via campaign
    - Revenue from jobs (if known)
    - Your side income from helping

    Output:
    - ROI percentage
    - Break-even analysis
    """

    # Example:
    campaign_data = {
        'name': 'hvac-homeowners-jan19',
        'cost': 5.00,  # $5 for 500 SMS
        'contacts': 500,
        'replies': 15,  # 3% reply rate
        'inspections_booked': 7,
        'jobs_completed': 4,
        'revenue_for_dad': 8000,  # $2K average per job
        'your_side_income': 1000  # You helped on 4 jobs @ $250 each
    }

    roi = (campaign_data['your_side_income'] / campaign_data['cost']) * 100 - 100

    print(f"\nCampaign: {campaign_data['name']}")
    print(f"Cost: ${campaign_data['cost']:.2f}")
    print(f"Your side income: ${campaign_data['your_side_income']:.2f}")
    print(f"ROI: {roi:.0f}%")
    print(f"\nFor every $1 spent, you earned ${campaign_data['your_side_income'] / campaign_data['cost']:.2f}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', required=True)
    args = parser.parse_args()

    calculate_roi(args.campaign)
```

---

## STOP LOSS Rules (Prevent Overspending)

### Automatic Campaign Pause Triggers

**Rule 1: Daily Spend Limit**
- **If daily SMS spend > $10:** Pause campaigns automatically
- **Why:** $10/day = $300/month (already over budget)
- **Action:** Review campaign performance, adjust messaging or pause

**Rule 2: Weekly Budget Check**
- **Every Monday 9 AM:** Check total spend for week
- **If weekly spend > $50:** Alert + require manual approval to continue
- **Why:** $50/week = $200/month (approaching budget limit)

**Rule 3: Monthly Budget Cap**
- **Hard cap:** $500/month TOTAL (all campaigns combined)
- **At $400 spent:** Alert + pause all campaigns
- **Why:** Buffer room for unexpected costs

**Implementation:**

```bash
# Add to crontab (runs daily at 9 AM)
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper && python -m src.cost_tracker --alert-threshold 500

# Add to crontab (runs weekly Monday 9 AM)
0 9 * * 1 cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper && python -m src.cost_tracker --period week --alert-threshold 50
```

---

## Cost Optimization Strategies

### FREE Customer Acquisition Channels (Use These First)

| Channel | Cost | Time Investment | Expected Results |
|---------|------|-----------------|------------------|
| **TikTok (HVAC)** | $0 | 2-3 hours/week | 1-2 leads/month (if viral) |
| **LinkedIn (Shipping)** | $0 | 1-2 hours/week | 1-2 leads/month |
| **Google My Business (HVAC)** | $0 | 1 hour setup | 2-5 leads/month (organic search) |
| **Referrals (Word of mouth)** | $0 | Ongoing | 1-3 leads/month |
| **TOTAL FREE** | **$0** | **4-6 hours/week** | **5-12 leads/month** |

**Recommendation:** Prioritize FREE channels before spending on ads.

---

### LOW-Cost Channels (If Free Doesn't Work)

| Channel | Cost | Expected ROI | Use When |
|---------|------|--------------|----------|
| **SMS (500 contacts)** | $5 | 2-4 jobs booked | Free channels not working |
| **Google Ads (HVAC)** | $100/month | 1-2 jobs booked | Need faster results |
| **Google LSA (HVAC)** | $250/month | 5-7 jobs booked | SMS + Ads not working |

**Decision Tree:**
```
Start with FREE channels (TikTok, LinkedIn, GMB)
  ↓
After 30 days:
  - If getting 5+ leads/month → Keep using FREE channels, don't spend on ads
  - If getting <5 leads/month → Try SMS ($5)
  ↓
After SMS (30 days):
  - If 2%+ reply rate → Keep using SMS ($5/month)
  - If <2% reply rate → Try Google Ads ($100/month)
  ↓
After Google Ads (30 days):
  - If getting 1-2 jobs/month → Keep using Ads ($100/month)
  - If not working → Try Google LSA ($250/month) OR pivot strategy
```

---

## Monthly Budget Report Template

**Run this on the 1st of every month:**

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.cost_tracker --report monthly
```

**Output:**

```
MONTHLY COST REPORT - January 2026

TOTAL SPEND: $156.00
- Twilio (SMS): $5.00 (500 messages)
- Twilio (Voice): $0.00 (no calls yet)
- Google Ads: $0.00 (not running)
- Fixed costs: $151.00 (hosting, domain, tools)

CAMPAIGN PERFORMANCE:
HVAC SMS Campaign (hvac-homeowners-jan19):
  - Spend: $5.00
  - Contacts: 500
  - Replies: 15 (3% reply rate)
  - Inspections booked: 7
  - Jobs completed: 4
  - Revenue for Dad: $8,000
  - Your side income: $1,000
  - ROI: 20,000% ($1K earned on $5 spent)

Shipping SMS Campaign (shipping-ecommerce-jan19):
  - Spend: $1.00
  - Contacts: 100
  - Replies: 6 (6% reply rate)
  - Quotes requested: 3
  - Clients signed: 1
  - Revenue for William George: $12,000/year
  - Your side income: $500 (setup help)
  - ROI: 50,000% ($500 earned on $1 spent)

TOTAL SIDE INCOME: $1,500
TOTAL VARIABLE SPEND: $6
NET PROFIT: $1,494

✅ BUDGET STATUS: WELL UNDER LIMIT ($6 / $500 spent)
✅ ACTION: Continue current campaigns, NO changes needed
```

---

## Revised Budget Recommendations

### Month 1 (January) - ULTRA-LOW COST TEST

**Total Budget:** $6
- HVAC SMS: $5 (500 contacts)
- Shipping SMS: $1 (100 contacts)
- Google Ads: $0 (skip)
- TikTok/LinkedIn: $0 (organic)

**Expected Side Income:** $1,000-4,000
**Expected ROI:** 16,667% - 66,667%

---

### Month 2-3 (February-March) - SCALE ONLY IF NEEDED

**IF SMS is working (2%+ reply rate):**
- Total Budget: $6/month (don't increase)
- Why: Already getting results at low cost

**IF SMS is NOT working (<1% reply rate):**
- Total Budget: $100/month (try Google Ads for HVAC)
- Still WELL under $500 limit

---

### Month 4+ (April onwards) - PAID CLIENTS

**AT THIS POINT:**
- You have 3-6 months of testimonial data from HVAC + Shipping
- Start selling to PAID clients at full price ($4,997-$19,997)
- Revenue from paid clients > Covers all ad spend for practice projects

**Budget can increase to $500/month** because:
- Paid client revenue justifies higher ad spend
- Practice projects (HVAC + Shipping) continue generating side income

---

## Summary: Don't Overspend on Practice Projects

**Key Rules:**
1. ✅ Month 1: Spend ONLY $6 (SMS testing)
2. ✅ Use FREE channels first (TikTok, LinkedIn, GMB)
3. ✅ Only increase spend if FREE + SMS don't work
4. ✅ Cap at $500/month TOTAL (all campaigns combined)
5. ✅ Your side income ($1K-4K/month) should ALWAYS > ad spend
6. ✅ After 3-6 months, pivot to paid clients (higher revenue)

**Cost Tracking:**
- Daily: Check Twilio balance
- Weekly: Check total spend (Monday 9 AM)
- Monthly: Generate cost report (1st of month)

**Automation:**
```bash
# Add to crontab
0 9 * * * cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper && python -m src.cost_tracker --alert-threshold 500
```

---

**Files to Create:**
1. `projects/lead-scraper/src/cost_tracker.py`
2. `projects/lead-scraper/src/campaign_roi.py`

**Next Steps:**
1. Implement cost tracking scripts
2. Set up daily/weekly budget alerts
3. Run Month 1 at $6 total spend
4. Measure ROI after 30 days
5. Decide: Continue low-cost OR try ads
