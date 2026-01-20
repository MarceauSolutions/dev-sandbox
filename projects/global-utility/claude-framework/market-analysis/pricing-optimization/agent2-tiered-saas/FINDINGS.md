# Agent 2: Tiered SaaS Pricing Model Analysis

**Date:** 2026-01-17
**Model Evaluated:** Tiered SaaS Pricing for Marceau Solutions
**Approach:** Fixed tiers with clear feature/scope gates, self-serve checkout possible

---

## Executive Summary

Tiered SaaS pricing **can work for automation agencies**, but with significant caveats. The model excels at predictability and scalability but risks commoditizing custom work and attracting price-shoppers. For Marceau Solutions, a **pure tiered model is NOT recommended**, but a **hybrid tiered approach** (productized entry + custom expansion) scores 3.2/5 and deserves consideration.

**Key Finding:** The automation agency market is moving toward productized services, with agencies reporting **margin improvements from 30% to 60%** through productization. However, only 2% of agencies "always" sell productized services, indicating the model works best as a component of a broader strategy, not the entire business.

---

## Recommended Tier Structure

### Option A: Pure Productized Tiers (NOT Recommended for Custom Work)

| Tier | Monthly Price | Setup Fee | What's Included |
|------|---------------|-----------|-----------------|
| **Starter** | $99/mo | $0 | 1 pre-built automation template, self-serve setup, community support |
| **Pro** | $299/mo | $500 | 3 automations, 30-min onboarding call, email support, 2 revisions/mo |
| **Business** | $599/mo | $2,500 | 5 automations, custom branding, priority support, 5 revisions/mo |
| **Enterprise** | $999/mo | $5,000+ | Unlimited automations, dedicated account manager, custom integrations |

**Why This Doesn't Work for Custom AI:**
- Custom automation scope varies wildly (10 hours to 100+ hours)
- AI/LLM work has high complexity variance
- Clients expect "custom" when paying enterprise prices
- Forces you to either underprice complex work or overprice simple work

### Option B: Hybrid Tiered Model (RECOMMENDED)

| Component | Pricing | Purpose |
|-----------|---------|---------|
| **Claude Framework (Free Tier)** | $0 | Lead magnet, establishes expertise |
| **Productized Quickstarts** | $499-$1,499 one-time | Templatized automations, self-serve |
| **Monthly Retainer** | $500-$3,000/mo | Ongoing support, optimization |
| **Custom Builds** | Value-based | High-margin custom work |

**Productized Quickstart Examples:**

| Quickstart | Price | Scope | Time to Deliver |
|------------|-------|-------|-----------------|
| "HVAC Quote Automator" | $1,499 | RFQ submission + tracking | 2 days |
| "Fitness Content Calendar" | $499 | AI-powered content planning | 1 day |
| "Lead Nurture Sequence" | $999 | 7-touch SMS/email automation | 3 days |
| "Video Jump-Cut Pipeline" | $749 | FFmpeg automation + branding | 2 days |

These are **entry points** that lead to custom work, not the whole business model.

---

## Analysis: Can You Productize Custom Implementations?

### What CAN Be Productized (Tier-Friendly)

| Automation Type | Productizable? | Reason |
|-----------------|----------------|--------|
| Lead capture forms | Yes | Template-based, low variance |
| Email sequences | Yes | Content changes, logic stays same |
| Social media scheduling | Yes | API patterns well-established |
| Basic chatbots | Yes | FAQ-based, templated responses |
| Data entry automation | Yes | Predictable inputs/outputs |
| Report generation | Yes | Format varies, process consistent |

### What CANNOT Be Productized (Needs Value-Based)

| Automation Type | Productizable? | Reason |
|-----------------|----------------|--------|
| Custom AI agents | No | Unique business logic per client |
| Multi-system orchestration | No | Integration complexity varies 10x |
| Legacy system integration | No | Unpredictable documentation/APIs |
| Compliance-heavy workflows | No | Regulatory requirements vary |
| Real-time decision systems | No | Business rules unique per client |

### The 70/30 Rule for Automation Agencies

Based on research, successful productized agencies maintain approximately:
- **70% productized/templated work** - Predictable, high-margin, scalable
- **30% custom work** - High-touch, strategic, relationship-building

Marceau Solutions' current project mix:
- Fitness Influencer MCP: 80% productizable (video editing, content plans)
- HVAC Quotes: 60% productizable (RFQ flow is standard, distributor integration varies)
- Lead Scraper: 70% productizable (templates vary, core scraping is consistent)
- Custom Claude Framework: 20% productizable (highly custom per client)

**Verdict:** Overall ~55% productizable, suggesting a hybrid model is optimal.

---

## Risk Assessment: Price-Shoppers

### The Price-Shopper Problem

**Definition:** Clients who optimize for lowest cost over best fit, leading to:
- Higher support burden (expectations misaligned)
- More refund requests
- Negative reviews when "it's not exactly what I needed"
- Time wasted on unqualified leads

### Price-Shopper Risk by Tier

| Tier | Price | Risk Level | Why |
|------|-------|------------|-----|
| $99/mo | High | Below filtering threshold, attracts hobbyists |
| $299/mo | Medium-High | Still accessible to price-shoppers |
| $599/mo | Medium | Starting to filter, but "agency pricing" stigma |
| $999+/mo | Low | Signals serious business investment |

### Mitigation Strategies

1. **Minimum viable price point: $299/mo or $1,500 setup**
   - Research shows $99/mo attracts tire-kickers
   - $299/mo is where "business tool" mental model kicks in
   - [Digital Agency Network](https://digitalagencynetwork.com/ai-agency-pricing/) confirms $500+ retainers filter effectively

2. **Qualification gates:**
   - Require business email (no gmail/yahoo)
   - Annual revenue minimum on intake form
   - Credit card on file before any setup
   - Mandatory strategy call before custom work

3. **Self-service friction for tire-kickers:**
   - Make pricing visible (filters budget-constrained)
   - Detailed FAQ that answers "is this for me?"
   - Clear scope limitations per tier

4. **Positioning language:**
   - "For businesses doing $X+ in revenue"
   - "Replaces $Y/year in manual work"
   - "Not for hobbyists or side projects"

### Research Finding on Price Shoppers

> "As a bonus, shoppers who aren't a good fit for a provider of productized services will discover the mismatch quickly and move on, saving the vendor from wasting his time on sales pitches that have little chance of bearing fruit."

This suggests visible tiered pricing can actually **reduce** price-shopper conversations by making the mismatch obvious before they contact you.

---

## Handling Projects That Don't Fit Tiers

### Three Approaches

**1. Clear "Custom Quote" Tier**
- Add explicit tier: "Enterprise / Custom - Contact for pricing"
- Signals availability of custom work without pricing it publicly
- Keeps tier structure clean while acknowledging complexity

**2. Add-On Model**
- Base tier + add-ons for complex features
- Example: "Pro tier ($299/mo) + Custom API Integration (+$1,500 setup)"
- Allows flexibility within structure
- Risk: Complexity creep, pricing becomes confusing

**3. Hybrid Funnel**
- Tiers for entry/productized work
- Sales call for anything that doesn't fit
- "Not sure which tier? Book a 15-min call"
- Best of both worlds but requires more sales time

### Recommended Approach for Marceau Solutions

**Hybrid Funnel with Clear Upgrade Path:**

```
Free Tier (Claude Framework)
         ↓
Productized Quickstarts ($499-$1,499)
         ↓
Monthly Retainer ($500-$1,500/mo)
         ↓
Custom Builds (Value-based, $2,500-$15,000+)
```

Each tier explicitly states: "For projects beyond this scope, book a strategy call."

---

## Revenue Projections at 50 Customers

### Scenario A: Pure Tiered Model

**Assumptions:**
- 50 customers across tiers
- Distribution: 20 Starter, 15 Pro, 10 Business, 5 Enterprise
- 80% monthly retention

| Tier | Customers | MRR | Annual |
|------|-----------|-----|--------|
| Starter ($99) | 20 | $1,980 | $23,760 |
| Pro ($299) | 15 | $4,485 | $53,820 |
| Business ($599) | 10 | $5,990 | $71,880 |
| Enterprise ($999) | 5 | $4,995 | $59,940 |
| **Total MRR** | 50 | **$17,450** | **$209,400** |

**Plus setup fees (Year 1 only):**
- 15 Pro @ $500 = $7,500
- 10 Business @ $2,500 = $25,000
- 5 Enterprise @ $5,000 = $25,000
- **Total Year 1 Setup: $57,500**

**Year 1 Total Revenue: $266,900**

**Problems:**
- High customer count needed (50 customers is a lot to support)
- Low ARPU ($3,490/year excluding setup)
- Churn risk: 20% annual churn = 10 customers/year replaced
- Support burden: 50 customers = 50 potential support tickets

### Scenario B: Hybrid Model (Recommended)

**Assumptions:**
- 25 customers (half the volume)
- Mix: 10 Quickstart-only, 10 Retainer, 5 Custom builds
- Higher ARPU, lower volume

| Segment | Customers | Revenue | Annual |
|---------|-----------|---------|--------|
| Quickstart-only ($999 avg) | 10 | $9,990 | One-time |
| Retainer ($1,500/mo avg) | 10 | $15,000/mo | $180,000 |
| Custom builds ($7,500 avg) | 5 | $37,500 | One-time |
| **Total Year 1** | 25 | | **$227,490** |

**Benefits:**
- Half the customers, nearly same revenue
- Higher ARPU ($9,100/customer)
- Lower support burden
- Better client relationships (fewer, deeper)
- Path to upsell (Quickstart → Retainer → Custom)

### Scenario C: Conservative vs Optimistic

| Scenario | Customers | Avg ARPU | Annual Revenue | Margin |
|----------|-----------|----------|----------------|--------|
| Conservative | 25 | $4,000 | $100,000 | 60% |
| Moderate | 35 | $6,500 | $227,500 | 65% |
| Optimistic | 50 | $8,000 | $400,000 | 70% |

---

## Example Client Journey: Tiered SaaS Model

### The "Fitness Influencer Emily" Journey

**Day 1: Discovery**
- Emily finds Claude Framework (free tier) on Claude MCP Registry
- Downloads, plays with it, sees value
- Visits Marceau Solutions website, sees tier pricing

**Week 1: Entry**
- Chooses "Fitness Content Quickstart" - $749
- Receives: Content calendar automation, video jump-cut pipeline
- Self-serve setup, video walkthrough, email support
- **Total investment: $749**

**Month 1: Expansion**
- Emily loves the time savings
- Wants custom revenue dashboard integrated with her sponsors
- Sales call booked (doesn't fit any tier)
- Custom quote: $3,500 setup + $1,000/mo retainer
- **Total investment: $749 + $3,500 + $1,000 = $5,249**

**Month 6: Partnership**
- Emily refers two other fitness creators
- Gets referral discount on retainer
- Asks for AI comment responder (custom)
- Additional $5,000 custom build
- **LTV at 6 months: ~$12,000**

**Analysis:**
- Tiers provided entry point (low friction)
- Self-serve allowed initial sale without sales call
- Custom work captured high-margin expansion
- Referral loop created via relationship

---

## Evaluation Criteria Scoring

### Scoring Matrix

| Criterion | Weight | Pure Tiers | Hybrid Tiers | Rationale |
|-----------|--------|------------|--------------|-----------|
| **Profitability** | 25% | 2/5 | 4/5 | Pure tiers compress margins; hybrid captures value |
| **Simplicity** | 20% | 4/5 | 3/5 | Pure tiers very clear; hybrid has two paths |
| **Scalability** | 20% | 5/5 | 4/5 | Pure tiers highly scalable; hybrid needs some custom |
| **Filtering** | 15% | 2/5 | 3/5 | Low tiers attract price-shoppers; hybrid $499 min helps |
| **Flexibility** | 10% | 1/5 | 4/5 | Pure tiers are rigid; hybrid handles variance |
| **Market Fit** | 10% | 3/5 | 4/5 | Market expects custom; productized is competitive |

### Weighted Scores

**Pure Tiered Model:**
- (2 x 0.25) + (4 x 0.20) + (5 x 0.20) + (2 x 0.15) + (1 x 0.10) + (3 x 0.10)
- = 0.50 + 0.80 + 1.00 + 0.30 + 0.10 + 0.30
- = **3.0/5**

**Hybrid Tiered Model:**
- (4 x 0.25) + (3 x 0.20) + (4 x 0.20) + (3 x 0.15) + (4 x 0.10) + (4 x 0.10)
- = 1.00 + 0.60 + 0.80 + 0.45 + 0.40 + 0.40
- = **3.65/5**

---

## Pros and Cons Summary

### Pros of Tiered SaaS

| Pro | Impact | Evidence |
|-----|--------|----------|
| **Predictable revenue** | High | MRR is forecastable, easier to plan |
| **Self-serve possible** | Medium | Reduces sales time for small deals |
| **Clear positioning** | Medium | Prospects self-select into tiers |
| **Scalability** | High | Same work, more customers |
| **Lower sales friction** | Medium | No price negotiation needed |

### Cons of Tiered SaaS

| Con | Impact | Mitigation |
|-----|--------|------------|
| **Commoditization risk** | High | Position as "entry point," not complete solution |
| **Price-shopper attraction** | Medium | $299+ minimum, qualification gates |
| **Custom work doesn't fit** | High | Explicit "Custom Quote" tier, hybrid model |
| **Margin compression** | Medium | Ensure tiers priced above breakeven |
| **Scope creep** | Medium | Clear boundaries, add-on pricing |
| **Client expectations** | Medium | Under-promise, over-deliver |

---

## Final Recommendation

### Verdict: Hybrid Tiered Model (3.65/5)

**Use Tiered Pricing For:**
- Entry-level productized quickstarts ($499-$1,499)
- Ongoing retainer support tiers ($500, $1,000, $2,000/mo)
- Claude Framework distribution (free tier)

**Use Value-Based Pricing For:**
- Custom AI agents and complex automation
- Multi-system integrations
- Anything requiring >20 hours of work

### Recommended Price Points

| Product | Price | Gate/Qualifier |
|---------|-------|----------------|
| Claude Framework | Free | Email capture |
| Quickstart Automation | $499-$1,499 | Self-serve checkout |
| Basic Retainer | $500/mo | 3-month minimum |
| Pro Retainer | $1,500/mo | 6-month commitment |
| Partner Retainer | $3,000/mo | Annual agreement |
| Custom Build | Value-based | Strategy call required |

### Key Implementation Notes

1. **Never offer a tier below $299/mo** - attracts wrong clients
2. **Make custom work explicitly available** - "Not sure which tier? Let's talk."
3. **Track tier-to-custom conversion rate** - Should be 20-30%
4. **Monitor support burden per tier** - Low tiers often cost more to support
5. **Revisit tier pricing quarterly** - Adjust based on actual delivery costs

---

## Comparison to Other Models

| Factor | Pure Tiers | Hybrid Tiers | Value-Based | Nick Saraev Pure |
|--------|------------|--------------|-------------|------------------|
| Weighted Score | 3.0/5 | 3.65/5 | TBD | TBD |
| Min price point | $99 | $499 | $2,500 | $5,000 |
| Sales touch | Low | Medium | High | High |
| Scalability | Highest | High | Medium | Low |
| Margin potential | Low-Medium | Medium-High | High | Highest |
| Client quality | Mixed | Good | Better | Best |

---

## Sources

- [The Complete Guide to Productized Services (2025)](https://assembly.com/blog/productized-services)
- [AI Agency Pricing Guide 2025 - Digital Agency Network](https://digitalagencynetwork.com/ai-agency-pricing/)
- [17 Top AI Automation Agencies in 2025 - Latenode](https://latenode.com/blog/industry-use-cases-solutions/enterprise-automation/17-top-ai-automation-agencies-in-2025-complete-service-comparison-pricing-guide)
- [Productized Service Pricing Models - Memberstack](https://www.memberstack.com/blog/productized-service-pricing-models-how-to-price-your-productized-service)
- [8 Challenges When Productizing Services - SPP](https://spp.co/blog/challenges-productizing-service/)
- [The 2026 Guide to SaaS and Agentic Pricing - Monetizely](https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models)
- [Productization for Agencies - Pros & Cons - RSW](https://www.rswus.com/productization-for-ad-agencies-pros-cons/)
- [Advanced SaaS Pricing Psychology 2026](https://ghl-services-playbooks-automation-crm-marketing.ghost.io/advanced-saas-pricing-psychology-beyond-basic-tiered-models/)
- [AI Automation Agency Business Model - Zaytrics](https://zaytrics.com/ai-automation-agency-business-model-services-pricing-and-value-proposition/)

---

*Agent 2 Analysis Complete - 2026-01-17*
