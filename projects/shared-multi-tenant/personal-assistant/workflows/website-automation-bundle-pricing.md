# Workflow: Website + Automation Bundle Pricing

**Created:** 2026-01-19
**Purpose:** Determine correct pricing tier and calculate custom pricing for bundled website + automation offerings
**Output:** Pricing recommendation with tier selection rationale

---

## Overview

This workflow helps price Marceau Solutions bundled offerings by analyzing client needs and mapping them to the correct tier (Digital Storefront, Growth System, or Enterprise Package). Includes decision trees for edge cases and custom pricing calculations when standard tiers don't fit.

---

## Use Cases

- Discovery call complete, need to select pricing tier for proposal
- Client needs fall between two tiers (need custom pricing)
- Client requests specific features not in standard tiers
- Need to justify pricing recommendation to client
- Calculating ROI to demonstrate value proposition

---

## Prerequisites

Before pricing decision:
- ✅ Discovery call completed (pain points identified)
- ✅ Client business info collected (revenue, size, industry)
- ✅ Current solutions documented (what they use now + costs)
- ✅ Automation needs identified (which workflows they need)
- ✅ Budget range discussed (if possible)

---

## The Three Tiers (Quick Reference)

| Tier | Setup Fee | Retainer | Best For | Timeline |
|------|-----------|----------|----------|----------|
| **Digital Storefront** | $4,997 | $247/mo (opt) | Website + basic automation | 4 weeks |
| **Growth System** | $9,997 | $747/mo (opt) | Website + full automation suite | 6 weeks |
| **Enterprise Package** | Custom ($20K+) | Custom ($2K+) | Multi-location, complex workflows | 8-10 weeks |

**Reference:** `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`

---

## Steps

### Step 1: Gather Client Requirements Data

**Objective:** Collect all information needed for tier decision

**Actions:**
1. Review discovery call notes
2. Extract key data points:
   - Business revenue (annual)
   - Number of locations
   - Number of employees
   - Industry/niche
   - Current tech stack (what they use now)
   - Pain points (prioritized by severity)
   - Must-have features vs nice-to-have
   - Budget constraints (if disclosed)

**Tools:**
- Discovery call template notes
- Client intake form responses
- ClickUp task with client details

**Output:**
```json
{
  "business_name": "Tony's Pizza Naples",
  "annual_revenue": 800000,
  "locations": 1,
  "employees": 8,
  "industry": "Restaurant",
  "current_solutions": [
    {"tool": "None", "cost": 0}
  ],
  "pain_points": [
    {"pain": "Missing 30% of calls during rush", "severity": "high"},
    {"pain": "No online ordering", "severity": "high"},
    {"pain": "Manual order tracking", "severity": "medium"}
  ],
  "must_have_features": [
    "Phone answering automation",
    "Online ordering form",
    "Order tracking"
  ],
  "nice_to_have": [
    "SMS confirmations",
    "Email marketing"
  ],
  "budget_disclosed": false
}
```

---

### Step 2: Run Tier Decision Tree

**Objective:** Map client needs to the correct tier using decision logic

**Decision Tree:**

```
START: Does client need a website?
├── NO → Not a bundled offering (automation-only, different pricing)
└── YES → Continue to Q2

Q2: How many locations?
├── 1 location → Continue to Q3
├── 2-3 locations → Likely Growth System or Enterprise
└── 4+ locations → Enterprise Package

Q3: How many automation workflows needed?
├── 0-2 workflows → Digital Storefront
├── 3-5 workflows → Growth System
└── 6+ workflows → Enterprise Package

Q4: Does client need custom integrations?
├── NO → Use Q3 result
└── YES → Upgrade one tier OR Enterprise

Q5: What's their annual revenue?
├── <$250K → Digital Storefront (affordability)
├── $250K-$1M → Growth System
└── >$1M → Growth System or Enterprise

Q6: Do they have existing systems to integrate?
├── NO → Use Q3/Q5 result
└── YES (e.g., POS, CRM, inventory) → Upgrade to Enterprise
```

**Scoring System** (if decision tree unclear):

| Factor | Weight | Digital Storefront | Growth System | Enterprise |
|--------|--------|-------------------|---------------|------------|
| Revenue | 20% | <$250K | $250K-$1M | >$1M |
| Locations | 25% | 1 | 1-2 | 3+ |
| Workflows Needed | 30% | 1-2 | 3-5 | 6+ |
| Custom Integrations | 15% | None | 1-2 simple | 3+ or complex |
| Team Size | 10% | <5 | 5-20 | 20+ |

**Actions:**
1. Walk through decision tree questions
2. If unclear, use scoring system (calculate weighted score for each tier)
3. Choose tier with highest score
4. Document rationale

**Tools:**
- This decision tree
- Calculator for scoring system
- Reference: `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`

**Output:**
- Recommended tier with justification

---

### Step 3: Verify Tier Match Against Documented Scope

**Objective:** Ensure selected tier includes everything client needs

**Actions:**
1. Open tier documentation: `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`
2. Compare client must-have features to tier "What's Included"
3. Check for gaps:
   - Are all must-haves included? → Good match
   - Missing 1-2 must-haves? → Consider upgrade or custom pricing
   - Missing 3+ must-haves? → Wrong tier, re-evaluate

4. Check for overkill:
   - Does tier include features client doesn't need?
   - Is client paying for unused capabilities?
   - If yes, can we remove features? (Usually NO - standard tiers)

**Verification Checklist:**
- [ ] Website design/hosting included? (all tiers)
- [ ] All requested automation workflows included?
- [ ] Integration requirements covered?
- [ ] Support level matches client expectations?
- [ ] Timeline acceptable to client?

**Tools:**
- `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md`

**Output:**
- Confirmed tier OR flag for custom pricing

---

### Step 4: Calculate Custom Pricing (If Needed)

**Objective:** Price edge cases that don't fit standard tiers

**When to Use Custom Pricing:**
- Client needs fall between two tiers
- Client needs tier + 1-2 add-ons
- Multi-location but not full Enterprise
- Unique industry requirements

**Custom Pricing Formula:**

```
Base Setup Fee = Closest Standard Tier Setup Fee

Add-On Pricing:
- Additional automation workflow: +$1,500 each
- Additional location/website: +$2,500 each
- Custom integration (API): +$2,000-$5,000 each
- Complex workflow (multi-step): +$3,000 each
- Rush delivery (<4 weeks): +25% fee

Example Calculation:
Growth System base: $9,997
+ 2 additional workflows: +$3,000
+ 1 custom POS integration: +$3,500
= Custom Setup Fee: $16,497

Retainer Calculation:
Base Retainer = Closest Standard Tier Retainer
+ $100/month per additional automation
+ $200/month per custom integration (maintenance)

Example:
Growth System retainer: $747/mo
+ 2 additional workflows: +$200/mo
+ 1 custom integration: +$200/mo
= Custom Retainer: $1,147/mo
```

**Actions:**
1. Start with closest standard tier
2. List all additions/customizations needed
3. Apply add-on pricing from formula
4. Calculate total setup fee
5. Calculate ongoing retainer
6. Round to nearest $97 (pricing psychology)

**Tools:**
- Calculator
- Add-on pricing reference (above)

**Output:**
```json
{
  "tier": "Custom (Growth System + Add-ons)",
  "base_tier": "Growth System",
  "customizations": [
    {"item": "Additional workflow: Email marketing", "cost": 1500},
    {"item": "Custom integration: Square POS", "cost": 3500}
  ],
  "setup_fee": 14997,
  "monthly_retainer": 947,
  "rationale": "Client needs Growth System core + POS integration for order syncing"
}
```

---

### Step 5: Calculate Client ROI/Value Proposition

**Objective:** Justify pricing with concrete ROI numbers

**Actions:**
1. Identify quantifiable pain points:
   - Missed calls → Lost revenue
   - Manual processes → Labor cost
   - No online presence → Missed customers

2. Calculate current cost of pain:
   ```
   Example (Restaurant missing calls):
   - 30% of calls missed during rush (client disclosed)
   - Average order value: $35
   - Estimated missed calls/day: 10
   - Lost revenue/month: 10 calls × $35 × 30 days = $10,500/month
   ```

3. Calculate solution value:
   ```
   Voice AI captures 90% of missed calls
   Recovered revenue: $10,500 × 0.9 = $9,450/month
   ```

4. Calculate payback period:
   ```
   Setup Fee: $9,997
   Retainer: $747/mo
   Total Year 1 Cost: $9,997 + ($747 × 12) = $18,961

   Annual Value: $9,450 × 12 = $113,400
   ROI: ($113,400 - $18,961) / $18,961 = 498% ROI
   Payback: $9,997 / $9,450 = 1.06 months (break-even in 1 month)
   ```

**ROI Calculation Templates by Industry:**

| Industry | Common Pain → Value Metric |
|----------|---------------------------|
| Restaurant | Missed calls → Captured orders |
| Gym/Fitness | Manual booking → Time saved (convert to billable hours) |
| Home Services | Missed leads → Booked jobs |
| Retail | No online sales → E-commerce revenue |
| Professional Services | Manual admin → Billable hours reclaimed |

**Tools:**
- Calculator
- Client's disclosed metrics (call volume, revenue, labor costs)

**Output:**
```markdown
## ROI Summary for Tony's Pizza

**Current State:**
- Missing 30% of calls during dinner rush
- Losing ~$10,500/month in potential orders

**Proposed Solution:**
- Voice AI captures 90% of missed calls
- Recovered revenue: $9,450/month

**Investment:**
- Setup: $9,997 (one-time)
- Retainer: $747/month (optional, for ongoing support)

**Payback:**
- Break-even in 1.06 months
- Year 1 net value: $94,439
- ROI: 498%
```

---

### Step 6: Prepare Pricing Recommendation

**Objective:** Document tier selection and rationale for proposal

**Actions:**
1. Create pricing recommendation document:
   - Recommended tier (or custom)
   - Setup fee
   - Monthly retainer (if applicable)
   - Rationale (why this tier fits)
   - ROI summary
   - What's included
   - What's NOT included

2. Review with checklist:
   - [ ] Pricing matches tier documentation
   - [ ] All client must-haves covered
   - [ ] ROI calculated and documented
   - [ ] Rationale clear and client-specific
   - [ ] Timeline realistic
   - [ ] No scope creep (what's NOT included is clear)

**Tools:**
- Text editor or Google Doc
- Template: `templates/pricing-recommendation-template.md`

**Output:**
```markdown
# Pricing Recommendation: Tony's Pizza Naples

**Recommended Tier:** Growth System
**Setup Fee:** $9,997
**Monthly Retainer:** $747 (optional, recommended)
**Timeline:** 6 weeks to launch

## Rationale

Tony's Pizza needs:
1. Professional website with online ordering
2. Voice AI to capture missed calls during rush
3. Order tracking system
4. SMS confirmations

This maps to **Growth System** because:
- 4 automation workflows needed (Voice AI, Forms, SMS, CRM)
- Annual revenue ~$800K (fits Growth System target)
- 1 location (doesn't need Enterprise multi-location)
- No complex integrations (basic form → CRM flow)

Digital Storefront (cheaper) won't work because:
- Only includes 2 workflows (client needs 4)
- No Voice AI included

Enterprise (more expensive) is overkill because:
- Single location (Enterprise is for 3+ locations)
- No complex integrations needed

## ROI Summary

**Current Pain:** Missing 30% of calls = ~$10,500/month lost revenue

**Solution Value:** Capture 90% of missed calls = $9,450/month recovered

**Payback:** 1.06 months (break-even in first month)

**Year 1 ROI:** 498%

## What's Included
[Copy from Growth System tier documentation]

## What's NOT Included
- Multi-location support (single location only)
- Custom POS integration
- Mobile app development
- Advanced analytics/reporting
```

---

### Step 7: Handle Common Pricing Objections

**Objective:** Prepare responses to expected objections

**Common Objections:**

| Objection | Response Strategy |
|-----------|------------------|
| "That's too expensive" | Show ROI (payback in 1-2 months), compare to cost of current pain, offer payment plan |
| "Can't we just do the website first?" | Explain bundle value (15% discount vs a la carte), automation is where ROI comes from |
| "I found someone cheaper on Fiverr" | Compare scope (their $500 website ≠ our system), emphasize ongoing support, show examples |
| "Can you break this into phases?" | Offer phased payment (50% deposit, 50% at launch), but don't break deliverables (scope creep risk) |
| "Do I really need the retainer?" | Explain retainer = ongoing support, updates, fixes; optional but recommended; show examples of issues covered |

**Pricing Flexibility Options:**
1. **Payment Plan:** 50% deposit, 25% at milestone, 25% at launch (no discount)
2. **Prepay Discount:** Pay year 1 retainer upfront = 1 month free ($747 × 12 = $8,964, offer $8,217)
3. **Referral Credit:** $500 credit per qualified referral that closes
4. **Package Downgrade:** If truly can't afford, offer Digital Storefront instead (but document limitations)

**What NOT to Do:**
- ❌ Don't discount >10% (devalues service)
- ❌ Don't remove features to hit price point (scope creep later)
- ❌ Don't commit to undefined "future phases" (never get paid for them)
- ❌ Don't price-match Fiverr (different quality tier)

**Actions:**
1. Anticipate objections based on client's budget concerns
2. Prepare ROI-focused responses
3. Have flexibility options ready (payment plan, referral credit)
4. Know your walk-away point (Digital Storefront is minimum viable tier)

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Client needs fall exactly between two tiers | Standard tiers don't fit perfectly | Use custom pricing (Step 4) or recommend higher tier with "you'll grow into it" |
| Client budget is 50% below recommended tier | Budget/value mismatch | Show ROI to justify cost OR offer Digital Storefront with clear limitations documented |
| Client wants Enterprise features at Growth System price | Unrealistic expectations | Educate on complexity/cost of Enterprise features, show value justification |
| Can't calculate ROI (soft benefits only) | Pain points not quantifiable | Use time-savings ROI (hours saved × hourly rate) or qualitative value (customer experience, brand perception) |
| Client wants to "try it for a month first" | Risk aversion | Offer 30-day money-back guarantee OR start with Digital Storefront (lower commitment) |

---

## Success Criteria

**Pricing decision is complete when:**
- ✅ Tier selected (or custom pricing calculated)
- ✅ Rationale documented (why this tier fits)
- ✅ All must-have features verified as included
- ✅ ROI calculated (payback period, Year 1 value)
- ✅ Exclusions clear (what's NOT included)
- ✅ Objection responses prepared
- ✅ Pricing matches tier documentation exactly
- ✅ Ready to generate proposal (next workflow)

---

## Reference Documentation

**Pricing & Scope:**
- `docs/STRIPE-PRODUCTS-V2-BUNDLED-OFFERINGS.md` - Tier definitions, pricing, what's included
- `docs/MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md` - Detailed service descriptions

**Templates:**
- `templates/pricing-recommendation-template.md` - Pricing recommendation output format
- `templates/proposals/` - Proposal templates (next step after pricing decision)

---

## Related Workflows

- `discovery-call-intake.md` - How to conduct discovery call (before pricing)
- `client-proposal-generation.md` - Generate proposal after pricing decision (next step)
- `roi-calculator.md` - Detailed ROI calculation methodology

---

## Version History

- **v1.0 (2026-01-19):** Initial workflow created for bundled pricing strategy
