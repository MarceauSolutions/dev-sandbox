# Workflow: Compare Financial Offers

## Overview
Specialized workflow for comparing multiple financial offers (savings accounts, credit cards, investment bonuses, etc.) to identify the best deal based on your specific needs.

## Use Cases
- Compare savings account bonuses
- Evaluate credit card offers
- Analyze investment platform promotions
- Compare mortgage/loan rates
- Assess banking incentives

## Prerequisites
- Multiple financial offer emails analyzed
- Key data extracted from each offer
- Understanding of your financial situation and goals

## Comparison Framework

### 0. Prerequisites Check (DO THIS FIRST!)
**Objective**: Verify you have all necessary data before starting comparison

**CRITICAL**: Don't try to compare emails you haven't fully analyzed - you'll miss key details and make poor decisions.

**Required Data Checklist**:

For each offer you plan to compare, verify you have:
- [ ] **APY/APR**: Interest rate clearly identified
- [ ] **Bonus amount**: Sign-up bonus or promotional amount (if applicable)
- [ ] **Minimum deposit**: Required initial deposit or balance
- [ ] **Term length**: How long money must stay deposited
- [ ] **Deadline**: When offer expires or must be activated
- [ ] **Penalties**: Early withdrawal or cancellation fees
- [ ] **Requirements**: Minimum activity, direct deposit, etc.

**Quick Data Validation**:
```bash
# For each email, verify key data is extracted
# Example check for financial offer data:

echo "Checking Offer 1..."
grep -i "apy\|apr\|rate" [offer1_analysis.md]
grep -i "bonus\|sign.*up" [offer1_analysis.md]
grep -i "minimum.*deposit\|min.*balance" [offer1_analysis.md]
grep -i "deadline\|expires\|until" [offer1_analysis.md]

# Repeat for each offer
```

**Data Completeness Matrix**:

| Offer | APY | Bonus | Min Deposit | Term | Deadline | Status |
|-------|-----|-------|-------------|------|----------|--------|
| WeltSparen | ✅ 4.2% | ✅ €150 | ✅ €5,000 | ✅ 12mo | ✅ Jan 31 | Ready ✅ |
| Varo | ✅ 5.0% | ❌ Missing | ✅ €0 | ✅ Flex | ✅ None | **Incomplete** ⚠️ |
| Newtek | ✅ 4.35% | ✅ $100 | ✅ $10K | ✅ 12mo | ❌ Missing | **Incomplete** ⚠️ |

**If data is incomplete**:
1. **STOP** - Do not proceed with comparison yet
2. Go back to [analyze-email-from-html.md](analyze-email-from-html.md) workflow
3. Re-analyze the email(s) with missing data
4. Extract the missing metrics
5. Return here when all data is complete

**Common Missing Data Issues**:
- **"Up to X%" language**: Is this the actual rate or maximum? Verify.
- **Unclear bonus timing**: When is bonus paid? Immediate or deferred?
- **Hidden fees**: Monthly fees, transaction requirements not extracted
- **Variable rates**: Is the APY guaranteed or subject to change?

**Recommendation**:
- ✅ **Ready to compare**: All offers have complete data
- ⚠️ **Missing 1-2 data points**: Quick re-analysis needed (10-15 min)
- ❌ **Missing 3+ data points**: Full re-analysis required (30+ min per offer)

**Comparison Readiness Assessment**:
```
Number of offers: [X]
Complete data: [Y] offers
Incomplete data: [Z] offers

If Z = 0: ✅ Proceed with comparison
If Z > 0: ⚠️ Complete analysis first
```

**Pro Tip**: Keep your individual email analyses open in separate tabs for reference during comparison. You may need to check specific details.

### 1. Define Your Criteria
**Objective**: Establish what matters most for your decision

**Common Criteria** (weight based on your priorities):
- **Total value** (bonus + interest over term)
- **Accessibility** (minimum requirements)
- **Flexibility** (term length, withdrawal penalties)
- **Risk** (FDIC insured, institution reputation)
- **Deadline urgency**
- **Effort required** (complexity of signup, maintenance)

**Weighting Example**:
```
Total Value: 40%
Accessibility: 25%
Flexibility: 20%
Risk: 10%
Deadline: 5%
```

### 2. Extract Comparable Metrics
**Objective**: Ensure apples-to-apples comparison

**For Savings/Deposit Accounts**:
- Annual Percentage Yield (APY)
- Bonus amount
- Minimum deposit
- Minimum balance
- Term length
- Early withdrawal penalty
- Monthly fees
- Compound frequency

**For Credit Cards**:
- Annual Percentage Rate (APR)
- Sign-up bonus
- Minimum spend requirement
- Annual fee
- Rewards rate
- Introductory period

**For Investment Platforms**:
- Bonus amount
- Minimum investment
- Hold period
- Trading fees
- Account types available
- Investment options

### 3. Normalize Values
**Objective**: Convert different offers to comparable metrics

**Calculate Total Value**:
```
For Savings Accounts:
Total Value = Bonus + (Deposit × APY × Term in years)

Example 1 - WeltSparen:
€5,000 × 4.2% × 1 year = €210
Plus €150 bonus = €360 total

Example 2 - Varo:
€5,000 × 5.0% × 1 year = €250
Plus €0 bonus = €250 total

Winner: WeltSparen (€360 > €250)
```

**Calculate Effective APY** (including bonus):
```
Effective APY = (Total Value / Deposit) / Term in years

WeltSparen: (€360 / €5,000) / 1 = 7.2% effective APY
Varo: (€250 / €5,000) / 1 = 5.0% effective APY
```

**Return on Effort**:
```
Value Per Hour of Work = Total Value / Estimated Hours Required

If signup takes 1 hour:
WeltSparen: €360 / 1 hour = €360/hour
Varo: €250 / 0.5 hours = €500/hour (simpler signup)
```

### 3.5 Calculate Present Value (for Deferred Payments)
**Objective**: Account for time-value of money when bonuses pay at different times

**CRITICAL**: Money today is worth more than the same amount in the future. When comparing offers with different payment timing, you MUST calculate present value (PV) for accurate comparison.

**When to Use Present Value Calculations**:
- ✅ Bonuses paid more than 3 months apart
- ✅ Deferred bonuses (e.g., "$800 after 2-year hold")
- ✅ Periodic payments (e.g., "$100/quarter × 8 quarters")
- ✅ Multi-year comparison periods
- ❌ Skip for bonuses paid within same month (difference negligible)

**Present Value Formula**:
```
PV = FV / (1 + r)^t

Where:
- PV = Present Value (today's equivalent)
- FV = Future Value (amount received later)
- r = discount rate (typically 3-5% for low-risk financial offers)
- t = time in years
```

**Discount Rate Selection**:
- **3%**: Conservative estimate, similar to inflation
- **4%**: Moderate estimate, balances inflation and opportunity cost
- **5%**: Higher estimate, assumes better alternative investments available
- **Recommended**: Use 3-4% for FDIC-insured savings/CD offers

**Example 1: Single Deferred Payment**
```
Compare two offers:
- Offer A: $500 bonus paid immediately
- Offer B: $800 bonus paid after 2-year hold

At 3% discount rate:
- Offer A PV: $500 (immediate)
- Offer B PV: $800 / (1.03)² = $800 / 1.0609 = $754

Winner: Offer B ($754 > $500), but closer than it appears
```

**Example 2: Periodic Payments vs Immediate**
```
Three offers with same $1,000 minimum deposit:
- Offer A: $500 immediate bonus
- Offer B: $800 bonus after 2 years
- Offer C: $200 now + $100/quarter × 8 quarters = $1,000 total

At 3% discount rate:
- Offer A PV: $500 (immediate)
- Offer B PV: $800 / (1.03)² = $754
- Offer C PV calculation:
  $200 (immediate) = $200
  + $100 in 3mo: $100 / (1.03)^0.25 = $99.27
  + $100 in 6mo: $100 / (1.03)^0.50 = $98.53
  + $100 in 9mo: $100 / (1.03)^0.75 = $97.79
  ... (continue for all 8 payments)
  ≈ $920 total PV

Ranking: Offer C ($920) > Offer B ($754) > Offer A ($500)
```

**Example 3: Tiered Interest Calculation**
```
Offer with tiered rates:
- 3.5% APY on first $10K
- 1.5% APY on $10K-$50K
- 0.5% APY above $50K

Your deposit: $30,000 for 1 year

Calculation:
Tier 1: $10,000 × 3.5% = $350
Tier 2: $20,000 × 1.5% = $300
Total interest: $650
Plus $100 bonus = $750 total value

Effective APY: $750 / $30,000 = 2.5%
```

**Simplified Present Value Table** (for quick reference):

| Future Amount | 3 months | 6 months | 1 year | 2 years | 3 years |
|---------------|----------|----------|--------|---------|---------|
| $100 @ 3% | $99.26 | $98.53 | $97.09 | $94.26 | $91.51 |
| $500 @ 3% | $496.32 | $492.64 | $485.44 | $471.28 | $457.56 |
| $1,000 @ 3% | $992.63 | $985.28 | $970.87 | $942.60 | $915.14 |

**Adding PV to Comparison Matrix**:
```markdown
| Criteria | Offer A | Offer B | Offer C | Winner |
|----------|---------|---------|---------|--------|
| **Bonus (Nominal)** | $500 now | $800 in 2yr | $200 + 8×$100 | Offer C ⭐ |
| **Bonus (Present Value @ 3%)** | $500 | $754 | $920 | Offer C ⭐ |
| **Time to Cash** | Immediate | 2 years | 2 years | Offer A ⭐ |
| **Payment Risk** | None | Low | Medium* | Offer A ⭐ |
```
*Periodic payments require ongoing account activity

**When NOT to Discount**:
- All bonuses paid at the same time
- Time difference less than 3 months
- User explicitly prefers nominal values
- Educational/illustrative comparisons

### 4. Create Comparison Matrix
**Objective**: Visual side-by-side comparison

**Template**:
```markdown
| Criteria | Offer A | Offer B | Offer C | Winner |
|----------|---------|---------|---------|--------|
| **Institution** | WeltSparen | Varo Bank | Newtek | - |
| **APY** | 4.2% | 5.0% | 4.35% | Varo ⭐ |
| **Bonus** | €150 | €0 | €100 | WeltSparen ⭐ |
| **Effective APY** | 7.2% | 5.0% | 6.35% | WeltSparen ⭐ |
| **Min. Deposit** | €5,000 | €0 | €10,000 | Varo ⭐ |
| **Term** | 12 months | Flexible | 12 months | Varo ⭐ |
| **Penalty** | Loss of bonus | None | Loss of interest | Varo ⭐ |
| **Deadline** | Jan 31 | None | Jan 20 | Varo ⭐ |
| **FDIC Insured** | Yes (EU equiv) | Yes | Yes | Tie |
| **Total Value (€5K)** | €360 | €250 | €317.50 | WeltSparen ⭐ |
| **Total Value (€10K)** | Not eligible | €500 | €535 | Newtek ⭐ |
```

### 5. Scenario Analysis
**Objective**: Evaluate offers under different scenarios

**Scenarios to Consider**:

**A. Different Deposit Amounts**
```markdown
| Offer | €5,000 | €10,000 | €25,000 | Best For |
|-------|--------|---------|---------|----------|
| Offer A | €360 | Not eligible | Not eligible | Small deposits |
| Offer B | €250 | €500 | €1,250 | Large deposits |
| Offer C | Not eligible | €535 | €1,337.50 | Medium-large |
```

**B. Different Time Horizons**
```markdown
| Offer | 6 months | 12 months | 24 months | Best For |
|-------|----------|-----------|-----------|----------|
| Offer A | €105 + €150 | €210 + €150 | Not available | 1 year |
| Offer B | €125 | €250 | €500 | Long-term |
| Offer C | Not eligible | €217.50 + €100 | €435 + €100 | 1-2 years |
```

**C. Early Withdrawal Scenarios**
```markdown
| Offer | Withdraw at 3mo | Withdraw at 6mo | Full Term | Penalty Type |
|-------|----------------|-----------------|-----------|--------------|
| Offer A | €0 | €0 | €360 | Lose all bonus |
| Offer B | €62.50 | €125 | €250 | None |
| Offer C | Interest only | Interest only | €317.50 | Lose bonus only |
```

### 6. Risk Assessment
**Objective**: Evaluate safety and reliability

**Risk Factors**:

**Institution Risk**:
- Established bank vs. new fintech
- Regulatory oversight (FDIC, NCUA, EU equivalents)
- Company financial health
- Customer reviews and complaints
- Length of time in business

**Offer Risk**:
- Bait-and-switch history
- Hidden fees or conditions
- Likelihood of terms changing
- Difficulty in claiming bonus
- Customer service quality

**Risk Matrix**:
```markdown
| Offer | Institution Risk | Offer Complexity | Historical Issues | Overall Risk |
|-------|-----------------|------------------|-------------------|--------------|
| WeltSparen | Low | Medium | None found | 🟢 Low |
| Varo | Low | Low | Some customer service complaints | 🟡 Medium |
| Newtek | Low | High | Strict bonus requirements | 🟡 Medium |
```

### 6.5 Behavioral Risk Assessment
**Objective**: Evaluate offers requiring specific behaviors and calculate realistic value

**CRITICAL**: Some offers require ongoing activity (spending, deposits, transactions). If you can't or won't meet these requirements, the offer value drops dramatically.

**Behavioral Requirement Types**:

1. **Spending Requirements**
   - Minimum monthly spend on debit/credit card
   - Example: "$2,000/month spend for 2% cash back"

2. **Activity Requirements**
   - Minimum number of transactions per month
   - Direct deposit requirements
   - Bill pay usage

3. **Balance Requirements**
   - Maintain minimum balance consistently
   - Average balance vs minimum balance

4. **Ongoing Engagement**
   - Log in monthly
   - Quarterly account review
   - Annual renewal actions

**Conditional Value Framework**:

For each offer with behavioral requirements, calculate **three scenarios**:

**Example: Hybrid Savings + Cash Back Offer**
```
Offer: 3.8% APY + 2% cash back on debit purchases + $150 bonus
Deposit: $20,000
Spend requirement: $2,000/month for cash back
```

**Conditional Value Table**:

| Scenario | APY Interest | Cash Back | Bonus | Total Value | Effective APY |
|----------|--------------|-----------|-------|-------------|---------------|
| **Best Case** (meet all requirements) | $760 | $480 | $150 | $1,390 | 6.95% |
| **Realistic** (75% compliance) | $760 | $360 | $150 | $1,270 | 6.35% |
| **Worst Case** (no spending) | $760 | $0 | $150 | $910 | 4.55% |

**How to Calculate**:
- **Best Case**: Assume perfect compliance with all requirements
- **Realistic**: Estimate actual behavior (use 75% as default if unsure)
- **Worst Case**: Assume you meet only mandatory requirements, none optional

**Behavioral Risk Questions**:

For spending requirements:
- ❓ Can I naturally spend $X/month on this card?
- ❓ What if I forget or lose the card?
- ❓ Will I change merchant preferences to hit targets?
- ⚠️ Risk: Artificial spending to meet requirements

For activity requirements:
- ❓ Will I remember to do X transactions monthly?
- ❓ What happens if I travel or get busy?
- ❓ Is this sustainable for the full term?
- ⚠️ Risk: Missing requirements and losing value

For balance requirements:
- ❓ Can I afford to keep $X locked up?
- ❓ What if I have an emergency?
- ❓ Am I giving up better opportunities elsewhere?
- ⚠️ Risk: Opportunity cost of locked funds

**Behavioral Risk Matrix**:

| Offer | Requirement Type | Required Behavior | Difficulty | Compliance Risk | Use Realistic Value? |
|-------|------------------|-------------------|------------|-----------------|----------------------|
| Pure Savings | None | Deposit only | 🟢 Easy | Low | No - use best case |
| Checking Bonus | Direct Deposit | Set up DD | 🟡 Medium | Medium | Yes |
| Cash Back Hybrid | $2K/month spend | Change habits | 🔴 Hard | High | Yes - or worst case |
| CD with Loyalty | Annual renewal | Remember yearly | 🟡 Medium | Medium | Yes |

**Difficulty Levels**:
- 🟢 **Easy**: One-time action, no ongoing effort
- 🟡 **Medium**: Recurring but simple (monthly DD, quarterly login)
- 🔴 **Hard**: Significant behavior change or hard to sustain

**Decision Framework**:

```markdown
## Comparison: Passive vs Active Offers

### Passive Offers (No Behavioral Requirements)
| Offer | Total Value | Effective APY | Risk |
|-------|-------------|---------------|------|
| Pure Savings A | $900 | 4.5% | 🟢 Low |
| CD Offer B | $1,100 | 5.5% | 🟢 Low |

### Active Offers (Behavioral Requirements) - REALISTIC VALUES
| Offer | Best Case | Realistic | Worst Case | Use This ⭐ | Risk |
|-------|-----------|-----------|------------|-------------|------|
| Cash Back Hybrid C | $1,390 | **$1,270** | $910 | $1,270 | 🟡 Medium |
| Spend Bonus D | $1,500 | **$1,125** | $750 | $1,125 | 🔴 High |
```

**Recommendation Logic**:
1. If you're **disciplined and organized**: Compare realistic values
2. If you're **forgetful or busy**: Use worst-case values for active offers
3. If you're **very conservative**: Only consider passive offers

**Red Flags - High Behavioral Risk**:
- 🚩 Spend requirements > 50% of your normal spending
- 🚩 More than 3 different monthly requirements
- 🚩 Requirements that force you to change primary accounts
- 🚩 "Use it or lose it" bonuses with tight timeframes
- 🚩 Requires behaviors you've failed at before

**Example Analysis**:

```markdown
### Offer C: Cash Back Hybrid - Behavioral Assessment

**Requirements**:
- Maintain $20K balance (passive - easy)
- Spend $2K/month on debit card (active - hard)

**My Situation**:
- Normal monthly spend: $2,500 (mostly on credit card)
- Willing to switch: Maybe 60%

**Realistic Calculation**:
- Month 1-3: Hit $2K target (motivated)
- Month 4-8: Hit $1,500 avg (slipping)
- Month 9-12: Hit $1,000 avg (back to habits)
- Average: $1,500/month = 75% compliance

**Realistic Value**: $1,270 (not $1,390)

**Decision**: Still better than passive $900 offer, worth trying
**Risk Mitigation**: Set calendar reminders, track spending weekly
```

### 7. Qualification Check
**Objective**: Verify you actually qualify for each offer

**Checklist per Offer**:
- [ ] New customer requirement (have you had account before?)
- [ ] Minimum deposit available
- [ ] Can commit to term length
- [ ] Can meet any spending/activity requirements
- [ ] Geographic eligibility (state/country restrictions)
- [ ] Credit requirements (if applicable)
- [ ] Age requirements
- [ ] Employment/income requirements

**Qualification Matrix**:
```markdown
| Offer | New Customer? | Min. Deposit OK? | Term OK? | Location OK? | Qualified? |
|-------|--------------|------------------|----------|--------------|------------|
| WeltSparen | ✅ Yes | ✅ Yes | ✅ Yes | ❌ EU only | ❌ No |
| Varo | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Newtek | ❌ Had account | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
```

### 8. Decision Tree
**Objective**: Systematic decision-making process

```
START
│
├─ Do I have [minimum deposit] available?
│  ├─ NO → Eliminate offers, consider smaller deposit options
│  └─ YES → Continue
│
├─ Can I commit to [term length]?
│  ├─ NO → Choose flexible or shorter-term options
│  └─ YES → Continue
│
├─ Am I qualified (new customer, location, etc.)?
│  ├─ NO → Eliminate ineligible offers
│  └─ YES → Continue
│
├─ Calculate total value for my deposit amount
│  └─ Rank by total value
│
├─ Apply my priorities:
│  ├─ Maximize total return → Highest effective APY
│  ├─ Maximize flexibility → Lowest penalties, shortest term
│  ├─ Minimize risk → Most established institution
│  └─ Minimize effort → Simplest requirements
│
└─ DECISION: [Selected Offer]
```

### 9. Sensitivity Analysis
**Objective**: Test how robust your decision is

**Questions to Ask**:
- What if interest rates rise/fall?
- What if I need money earlier than expected?
- What if a better offer appears next month?
- What's my opportunity cost (what else could I do with this money)?

**Break-Even Analysis**:
```
How much would offer B's rate need to increase to beat offer A?

Offer A value: €360
Offer B value: €250
Difference: €110

Required APY increase for Offer B:
€110 / €5,000 = 2.2 percentage points
Current 5.0% + 2.2% = 7.2% APY needed to match

Conclusion: Unlikely rates will increase that much
```

### 10. Final Recommendation
**Objective**: Clear, actionable decision

**Recommendation Template**:
```markdown
## Recommended Offer: [Name]

### Why This Offer Wins
1. [Primary reason - usually total value]
2. [Secondary reason - risk, flexibility, etc.]
3. [Tertiary reason - additional benefits]

### What You'll Earn
- Base interest: [Amount]
- Bonus: [Amount]
- **Total: [Amount]**
- **Effective APY: [Percentage]**

### What You Need to Do
1. [Step 1] - Deadline: [Date]
2. [Step 2]
3. [Step 3]

### Requirements to Track
- Minimum deposit: [Amount] by [Date]
- Maintain balance: [Amount] for [Term]
- Bonus payment: Expected [Date]
- [Any other requirements]

### Risks & Mitigation
- Risk: [Identified risk]
  - Mitigation: [How to address]

### Runner-Up
[Second best offer] would be worth considering if:
- [Scenario where runner-up wins]

### When to Reconsider
- [ ] If interest rates rise above [X]%
- [ ] If a better offer appears before [deadline]
- [ ] If financial situation changes (need flexibility)
```

## Specialized Comparisons

### Credit Card Offers
**Additional Metrics**:
- Sign-up bonus value
- Minimum spend requirement
- Timeline to earn bonus
- Rewards rate (cash back, points, miles)
- Annual fee (first year, ongoing)
- Introductory APR period
- Regular APR
- Foreign transaction fees
- Other benefits (insurance, lounge access)

**Value Calculation**:
```
Year 1 Value =
  Sign-up Bonus
  + (Expected Spend × Rewards Rate)
  - Annual Fee
  - (Carried Balance × APR if applicable)
```

### Investment Platform Bonuses
**Additional Metrics**:
- Bonus tier structure
- Hold period
- Trading fees during hold period
- Opportunity cost (could invest elsewhere)
- Platform quality
- Investment options available

## Common Pitfalls

### Comparison Errors
- ❌ Comparing APR to APY (different calculations)
- ❌ Ignoring compound frequency
- ❌ Forgetting about taxes on interest/bonuses
- ❌ Not accounting for early withdrawal scenarios
- ❌ Overlooking fine print (hidden fees, conditions)

### Decision Errors
- ❌ Chasing highest rate without checking institution safety
- ❌ Taking offer you don't qualify for
- ❌ Overestimating ability to meet requirements
- ❌ Ignoring opportunity cost
- ❌ Analysis paralysis (overthinking small differences)

## Quick Decision Rules

### When Offers Are Close (< 10% difference in value)
→ Choose the one with:
- Most flexibility
- Best institution reputation
- Simplest requirements
- Longest deadline

### When One Offer Clearly Wins (> 25% higher value)
→ Choose the winner unless:
- Significantly higher risk
- You don't qualify
- Requirements are impractical
- Better offer expected soon

### When You're Unsure
→ Ask yourself:
- "Will I regret not taking the highest value offer?"
- "Can I actually meet all the requirements?"
- "Is the extra complexity worth the extra return?"

## Success Criteria

A successful comparison includes:
- ✅ Consistent metrics across all offers
- ✅ Total value calculated for your specific situation
- ✅ Qualification status verified
- ✅ Risk factors assessed
- ✅ Clear winner identified with reasoning
- ✅ Runner-up noted for backup
- ✅ Action steps documented
- ✅ Deadlines tracked

## Related Workflows
- [analyze-email-from-html.md](analyze-email-from-html.md) - Analyze individual offers
- [batch-email-analysis.md](batch-email-analysis.md) - Process multiple emails
- [track-financial-offers.md](track-financial-offers.md) - Monitor over time (future)
