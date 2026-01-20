# GO/NO-GO Decision: DecideForHer

## Overall Score: 2.53/5

## Decision: PIVOT

The "DecideForHer" concept as originally proposed is NOT recommended for development. However, the research uncovered a viable pivot opportunity that addresses the core issues.

---

## Why Not "DecideForHer"

### Fatal Flaws Identified

1. **Market Doesn't Exist as Monetizable Category**
   - SAM: $4-8M (tiny)
   - SOM Year 1: $3,000-9,000 (not worth the effort)
   - No successful precedent for paid "food decision" apps

2. **Customer Pain Is Insufficient**
   - Pain level: 5/10 (annoyance, not crisis)
   - Willingness to pay: <5%
   - Free behavioral solutions work well enough

3. **Unit Economics Are Brutal**
   - CAC: $305 per paid subscriber (paid channels)
   - LTV: $42-107
   - LTV/CAC ratio: 0.4x-1.7x (non-viable without 80%+ organic)

4. **Brand Is a PR Liability**
   - "DecideForHer" implies boyfriend controls girlfriend's food
   - Cycle tracking perceived as invasive/creepy
   - 40% probability of triggering public backlash

### What the Research Got Right

- **Competition**: True blue ocean (4/5 stars)
- **Mobile Platform**: Strong fit (35/40)
- **Viral Potential**: High cultural recognition
- **Partnership Opportunity**: Period tracking apps could be valuable partners

---

## Recommended Pivot: "CraveSmart"

### The New Concept

**What it is**: A personal craving prediction app that helps users understand their own food patterns based on time of day, day of week, weather, and optionally menstrual cycle phase.

**Who it's for**: Women (primarily) who want to understand why they crave certain foods at certain times, with an optional partner-sharing feature.

**Problem it solves**: Self-awareness around food cravings and patterns, helping users make better food choices aligned with their body's signals.

**Key Repositioning**:
| DecideForHer (OLD) | CraveSmart (NEW) |
|--------------------|------------------|
| Boyfriend decides for girlfriend | User understands herself |
| Cycle tracking feels invasive | Cycle tracking feels empowering |
| Partner feature is creepy | Partner feature is optional sharing |
| B2C men (hard to monetize) | B2C women (wellness spending) |
| Gimmick/novelty | Health/wellness tool |

### Why This Pivot Works

1. **Women spend on wellness apps**
   - Calm, Headspace: $70-100/year
   - Period trackers: Flo Premium $9.99/month
   - Nutrition apps: MyFitnessPal Premium $19.99/month

2. **Period app partnerships become natural**
   - CraveSmart helps Flo/Clue users understand cravings
   - Mutual benefit: both apps get more engaged users
   - Privacy-friendly: user controls data flow

3. **Brand is empowering, not problematic**
   - "Understand your cravings" vs "Let him decide"
   - Science-backed wellness angle
   - Positive PR potential ("women's health tech")

4. **Partner feature becomes optional upsell**
   - Core value: self-understanding
   - Premium feature: share preferences with partner
   - Removes dual-adoption requirement

---

## Partnership Strategy: Period Tracking Apps

### Tier 1 Targets (Highest Priority)

| App | Users | Integration Path | Pitch |
|-----|-------|------------------|-------|
| **Clue** | 12M+ | Terra API (existing) | "Complete the wellness picture - food + cycle" |
| **Flo** | 50M+ | Apple Health export | "Help your users understand cravings scientifically" |

### Integration Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flo / Clue    │────▶│   Apple Health  │────▶│   CraveSmart    │
│  (Period Data)  │     │  (Data Bridge)  │     │  (Predictions)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Partner Share  │
                                               │   (Optional)    │
                                               └─────────────────┘
```

### Partnership Value Proposition

**For Flo/Clue:**
- New feature: "See what foods you might crave this week"
- User engagement: More reasons to open the app
- Revenue share: 20% of CraveSmart premium subscriptions from referred users
- Data insights: Anonymized craving patterns (research value)

**For CraveSmart:**
- Instant credibility: "Powered by Clue's cycle data"
- User acquisition: Promoted in partner app
- Data quality: Accurate cycle tracking without building it

### Partnership Outreach Plan

1. **Week 1**: Research Clue's partnership program, identify contacts
2. **Week 2**: Build MVP with Apple Health integration (proves capability)
3. **Week 3**: Create partnership deck with value proposition
4. **Week 4**: Cold outreach via LinkedIn to Clue business development
5. **Week 5+**: Follow up, iterate on proposal

---

## If Proceeding With Pivot

### Next Steps (SOP 0: Project Kickoff)

1. **Rebrand project**: `decide-for-her/` → `crave-smart/`

2. **Complete kickoff questionnaire** with new positioning:
   - Target: Women 22-40 interested in wellness
   - Platform: Mobile (iOS first, Android later)
   - Monetization: Freemium ($5.99/month premium)
   - Differentiation: Cycle-aware craving predictions

3. **Build MVP features** (Phase 1):
   - Apple Health integration (cycle data)
   - Basic craving logging
   - Pattern visualization ("You crave chocolate 2 days before period")
   - Simple recommendations

4. **Partnership outreach** (parallel to MVP):
   - Clue via Terra API
   - Flo via Apple Health bridge
   - Present MVP as proof of concept

5. **Validate with users** before full build:
   - Landing page with email capture
   - Target: 500 signups before investing in development
   - Test messaging: "Finally understand why you crave what you crave"

---

## Financial Projections (CraveSmart Pivot)

### Year 1 Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Downloads | 25,000 | Organic + partner referrals |
| Free users | 20,000 | 80% free tier |
| Paid subscribers | 500 | 2% conversion |
| ARPU (paid) | $5.99/month | Below Flo Premium |
| MRR | $2,995 | 500 × $5.99 |
| ARR | $35,940 | MRR × 12 |

### Year 1 Costs

| Category | Annual |
|----------|--------|
| Development | $20,000 |
| Hosting/APIs | $3,600 |
| Marketing | $5,000 |
| App Store fees | $5,394 (15% of revenue) |
| **Total** | **$34,000** |

### Year 1 P&L: **+$1,940** (break-even)

### Year 3 Projections (if successful)

| Metric | Target |
|--------|--------|
| Downloads | 500,000 |
| Paid subscribers | 15,000 |
| MRR | $89,850 |
| ARR | $1,078,200 |
| Net margin | 40% |
| **Annual profit** | **$431,280** |

---

## Alternative: No Development (Archive)

If the pivot doesn't feel right, the recommendation is to **archive** this idea:

1. Save research in `projects/decide-for-her/archive/`
2. Document learnings in session-history.md
3. Revisit if:
   - Period tracking APIs become more accessible
   - Cultural moment makes the concept less problematic
   - Partnership opportunity emerges organically

---

## Decision Summary

| Option | Recommendation | Confidence |
|--------|---------------|------------|
| **DecideForHer (original)** | NO-GO | HIGH |
| **CraveSmart (pivot)** | CONDITIONAL GO | MEDIUM |
| **Archive entirely** | ACCEPTABLE | LOW |

### Conditions for CraveSmart GO:
- [ ] Rebrand complete (no "DecideForHer" terminology)
- [ ] Landing page validates 500+ email signups
- [ ] At least one period app shows partnership interest
- [ ] Apple Health integration proves technically feasible
- [ ] William confirms interest in women's wellness market

---

## Appendix: Agent Findings Summary

| Agent | Focus | Score | Key Finding |
|-------|-------|-------|-------------|
| Agent 1 | Market Size | 2.0/5 | Market doesn't exist as monetizable category |
| Agent 2 | Competition | 4.0/5 | True blue ocean, zero direct competitors |
| Agent 3 | Customer | 2.0/5 | Problem real but not painful enough to pay |
| Agent 4 | Monetization | 2.5/5 | Brutal unit economics, requires viral growth |

---

*Decision Date: January 18, 2026*
*DecideForHer Market Viability Analysis*
*SOP 17 Complete*
