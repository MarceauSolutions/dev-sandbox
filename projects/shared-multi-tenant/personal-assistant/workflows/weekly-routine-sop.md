# SOP: Weekly Routine Checklist

*Last Updated: 2026-01-15*
*Version: 1.0.0*

## Overview

Weekly, bi-weekly, and monthly tasks for campaign performance review, pipeline management, and strategic planning. Best performed Monday mornings (weekly) and 1st of each month (monthly).

## Weekly Tasks (Every Monday, 9:00 AM - 10:30 AM)

### Step 1: Campaign Performance Review (9:00 AM - 30 min)

**Objective**: Analyze SMS campaign effectiveness and optimize

**Commands**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Full campaign report
python -m src.campaign_analytics report

# Template comparison (A/B testing)
python -m src.campaign_analytics templates

# Conversion funnel analysis
python -m src.campaign_analytics funnel
```

**Review**:
- [ ] Response rate vs industry benchmark (2-5%)
- [ ] Hot lead conversion rate
- [ ] Template performance comparison
- [ ] Opt-out rate (should be <3%)
- [ ] Best performing time slots

**Actions**:
- Pause underperforming templates
- Scale winning templates
- Adjust send times based on response data

---

### Step 2: ClickUp Pipeline Review (9:30 AM - 20 min)

**Objective**: Ensure no leads are stuck in pipeline

**Check**:
1. ClickUp: Lead Pipeline board
2. Filter by stage: Intake, Qualified, Proposal, Negotiation, Won/Lost

**Review**:
- [ ] Leads in Intake >3 days (need qualification)
- [ ] Leads in Qualified >7 days (need proposal)
- [ ] Leads in Proposal >14 days (need follow-up)
- [ ] Stale leads (no activity >21 days)

**Actions**:
- Move qualified leads forward
- Send follow-ups on stale proposals
- Archive lost leads with reason

---

### Step 3: Calendar Week Preview (9:50 AM - 10 min)

**Objective**: Prepare for upcoming week

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
python calendar_reminders.py list --days 7
```

**Review**:
- [ ] Client calls scheduled
- [ ] Content creation blocks
- [ ] Review/analysis sessions
- [ ] Personal appointments

**Actions**:
- Block prep time before important calls
- Reschedule conflicts

---

### Step 4: Product Opportunity Review (10:00 AM - 15 min)

**Objective**: Review and prioritize new product ideas

**Check**:
- File: `/Users/williammarceaujr./dev-sandbox/OPPORTUNITY-LOG.md`

**Review**:
- [ ] New opportunities logged this week
- [ ] Viability scores assigned
- [ ] Priority rankings updated

**Actions**:
- Score new opportunities
- Move high-priority items to project backlog
- Archive low-viability ideas

---

## Bi-Weekly Tasks (Every Other Monday, 10:30 AM - 11:30 AM)

### Step 5: Revenue Analytics Review (10:30 AM - 20 min)

**Objective**: Track profit margins and cost efficiency

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
python -m src.revenue_analytics monthly
```

**Review**:
- [ ] Monthly profit vs target
- [ ] COGS margin (target: 60%+)
- [ ] Revenue trend (MoM)
- [ ] Top revenue sources

**Actions**:
- Investigate declining revenue streams
- Double down on profitable services

---

### Step 6: API Cost Review (10:50 AM - 15 min)

**Objective**: Monitor AI/API costs and maintain margins

**Check**:
- Anthropic dashboard: API usage
- OpenAI dashboard: API usage
- Twilio console: SMS costs

**Review**:
- [ ] Total API spend this period
- [ ] Cost per lead/conversion
- [ ] Any unexpected spikes

**Actions**:
- Optimize prompts if costs high
- Switch to cheaper models where quality allows

---

### Step 7: Amazon Inventory Check (11:05 AM - 15 min)

**Objective**: Prevent stockouts and aged inventory fees

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/amazon-seller
python -m src.amazon_sp_api inventory --low-stock-alert 14
```

**Review**:
- [ ] Items <14 days of stock
- [ ] Items with aged inventory (>180 days)
- [ ] Reorder quantities needed

**Actions**:
- Create restock orders for low items
- Run promotions on aged inventory

---

### Step 8: A/B Test Results (11:20 AM - 10 min)

**Objective**: Check statistical significance of running tests

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.campaign_analytics ab_test --check-significance
```

**Review**:
- [ ] Any tests reached significance
- [ ] Winner identified
- [ ] Tests needing more data

**Actions**:
- Implement winning variants
- Close inconclusive tests after 30 days

---

## Monthly Tasks (1st of Month, 9:00 AM - 11:00 AM)

### Step 9: Monthly Revenue Report (9:00 AM - 30 min)

**Objective**: Comprehensive month-over-month analysis

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
python -m src.revenue_analytics monthly --compare-previous
```

**Review**:
- [ ] Total revenue vs previous month
- [ ] Revenue by source breakdown
- [ ] Profit margin trend
- [ ] YTD progress vs goals

**Actions**:
- Document insights in monthly report
- Adjust strategies for underperforming areas

---

### Step 10: Campaign ROI Analysis (9:30 AM - 30 min)

**Objective**: Calculate true cost per acquisition

**Metrics to Calculate**:
```
CPA = (SMS Costs + Time Investment) / Conversions
LTV = Average Deal Size * Retention Rate
ROI = (Revenue - Costs) / Costs * 100
```

**Review**:
- [ ] CPA by campaign
- [ ] LTV by customer segment
- [ ] Overall ROI

**Actions**:
- Kill campaigns with CPA > LTV
- Scale campaigns with positive ROI

---

### Step 11: Churn Analysis (10:00 AM - 20 min)

**Objective**: Understand customer retention

**Check**:
- Stripe dashboard: Subscription metrics
- ClickUp: Lost deals from past month

**Review**:
- [ ] Churn rate (target: <5%)
- [ ] Common churn reasons
- [ ] At-risk customers (payment failures)

**Actions**:
- Reach out to at-risk customers
- Implement retention strategies for common churn reasons

---

### Step 12: Storage Fee Review (10:20 AM - 20 min)

**Objective**: Minimize Amazon FBA aged inventory fees

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/amazon-seller
python -m src.amazon_sp_api storage_fees --aged-inventory
```

**Review**:
- [ ] Items approaching 180-day threshold
- [ ] Items approaching 365-day threshold (long-term storage)
- [ ] Current storage fee totals

**Actions**:
- Create removal orders for slow movers
- Run liquidation promotions

---

### Step 13: Quarterly Planning Preview (10:40 AM - 20 min)

**Objective**: Prepare for upcoming quarter (on last month of quarter)

**Only on**: March, June, September, December

**Review**:
- [ ] Q goals achievement
- [ ] Lessons learned
- [ ] Next Q priorities

**Actions**:
- Draft Q+1 goals
- Schedule planning session

---

## Quick Reference Commands

```bash
# Weekly campaign report
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.campaign_analytics report

# Template comparison
python -m src.campaign_analytics templates

# Conversion funnel
python -m src.campaign_analytics funnel

# Calendar preview
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
python calendar_reminders.py list --days 7

# Revenue analytics
python -m src.revenue_analytics monthly

# Amazon inventory
cd /Users/williammarceaujr./dev-sandbox/projects/amazon-seller
python -m src.amazon_sp_api inventory --low-stock-alert 14

# A/B test check
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.campaign_analytics ab_test --check-significance
```

---

## Task Frequency Summary

| Task | Frequency | Duration | Priority |
|------|-----------|----------|----------|
| Campaign Performance | Weekly (Mon) | 30 min | High |
| ClickUp Pipeline | Weekly (Mon) | 20 min | High |
| Calendar Preview | Weekly (Mon) | 10 min | Medium |
| Product Opportunities | Weekly (Fri) | 15 min | Medium |
| Revenue Analytics | Bi-weekly | 20 min | High |
| API Cost Review | Bi-weekly | 15 min | Medium |
| Amazon Inventory | Bi-weekly | 15 min | High |
| A/B Test Results | Bi-weekly | 10 min | Medium |
| Monthly Revenue | Monthly | 30 min | Critical |
| Campaign ROI | Monthly | 30 min | High |
| Churn Analysis | Monthly | 20 min | High |
| Storage Fees | Monthly | 20 min | Medium |
| Quarterly Planning | Quarterly | 20 min | High |

---

## Success Criteria

### Weekly
- [ ] Campaign metrics reviewed before EOD Monday
- [ ] Pipeline stages updated and current
- [ ] Week's calendar reviewed and prepared
- [ ] Opportunity log reviewed

### Bi-Weekly
- [ ] Revenue on track for monthly target
- [ ] API costs within budget
- [ ] No inventory stockouts
- [ ] A/B tests progressing

### Monthly
- [ ] Monthly report completed by 5th
- [ ] ROI positive on all active campaigns
- [ ] Churn rate <5%
- [ ] No aged inventory fees

---

## Automation Status

| Task | Current | Future |
|------|---------|--------|
| Campaign Report | Manual command | Auto-email Monday 8 AM |
| Pipeline Review | Manual ClickUp | Auto-digest with stale alerts |
| Calendar Preview | Manual command | Included in morning digest |
| Revenue Analytics | Manual command | Auto-email 1st of month |
| Inventory Check | Manual command | Auto-alert on low stock |

---

## References

- [Daily Routine SOP](./daily-routine-sop.md)
- [Campaign Analytics (SOP 22)](../../../CLAUDE.md#sop-22-campaign-analytics--tracking)
- [Cold Outreach Strategy (SOP 23)](../../../CLAUDE.md#sop-23-cold-outreach--sms-campaign-strategy)
