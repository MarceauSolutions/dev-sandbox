# Pricing Model Optimization - SOP 9 Exploration

**Date:** 2026-01-17
**Purpose:** Optimize pricing model for Marceau Solutions automation business
**Method:** Multi-agent parallel exploration (SOP 9)

---

## Context

We're consolidating pricing across all projects (Fitness Influencer, HVAC, Lead Scraper, Claude Framework, future projects) into a unified model that:

1. Uses setup fee + monthly retainer structure
2. Treats all projects as "automation implementations"
3. Positions existing projects as proof-of-concepts for sales
4. Aligns with Nick Saraev's high-margin approach
5. Filters for serious buyers (no price shoppers)

---

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Profitability** | 25% | Margin per deal, LTV potential |
| **Simplicity** | 20% | Easy to explain, easy to buy |
| **Scalability** | 20% | Works for 1 client or 100 |
| **Filtering** | 15% | Attracts right clients, repels wrong ones |
| **Flexibility** | 10% | Handles different project sizes |
| **Market Fit** | 10% | Competitive but premium positioning |

---

## Four Approaches to Evaluate

### Agent 1: Pure Value-Based Pricing
- Price = 25-30% of client's annual value
- No fixed tiers, every project scoped individually
- Requires discovery call for every deal
- Nick Saraev's core principle

### Agent 2: Tiered SaaS Model
- Fixed tiers with clear feature gates
- Self-serve checkout possible
- Lower touch, higher volume
- Risk: Commoditizes the offering

### Agent 3: Hybrid Model (Current Direction)
- 2-3 setup tiers + 2 retainer tiers
- Community as entry point
- Balance of structure and flexibility
- Question: What's the optimal number of tiers?

### Agent 4: Nick Saraev Pure Model
- $9,400/month retainer as anchor
- High-ticket only ($5K+ minimum)
- No self-serve, all high-touch
- Maximum margin, minimum volume

---

## Research Questions Per Agent

### All Agents Should Answer:
1. What's the minimum viable price point that filters price-shoppers?
2. How many tiers optimizes for both simplicity and flexibility?
3. Should community be separate or bundled?
4. How does Claude Framework fit (lead magnet vs product)?
5. What's the realistic LTV for a client?
6. What's the break-even timeline for client?

---

## Deliverables

Each agent creates `FINDINGS.md` with:
1. Recommended pricing structure
2. Pros/Cons analysis
3. Example client journey
4. Revenue projections (conservative/moderate/optimistic)
5. Risk assessment
6. Score against evaluation criteria

Consolidated output: `consolidated/OPTIMAL-MODEL.md`

---

## Success Criteria

Final model should:
- [ ] Have 6 or fewer products in Stripe
- [ ] Minimum $5K setup or $500/mo retainer (filters price-shoppers)
- [ ] Clear upsell path from entry to partner
- [ ] 70%+ gross margin achievable
- [ ] Explainable in 30 seconds
