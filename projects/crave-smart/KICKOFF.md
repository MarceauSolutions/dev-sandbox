# CraveSmart - Project Kickoff

## Project Summary

**Product**: CraveSmart - Personal craving prediction app that helps users understand their food patterns based on time, weather, and menstrual cycle phase.

**Tagline**: "Finally understand why you crave what you crave"

**Pivot From**: DecideForHer (problematic branding, market viability issues)

---

## SOP 0: Kickoff Questionnaire

### Part 1: Business/Purpose

**Q1: What problem does this solve?**
Women experience predictable food cravings tied to their menstrual cycle (91.78% report this), but lack tools to understand and anticipate these patterns. Current period trackers focus on symptoms, not actionable food insights.

**Q2: Who is the target user?**
- Primary: Women ages 22-40 interested in wellness and self-understanding
- Secondary: Partners who want to understand their significant other's food patterns
- Tertiary: Couples looking to reduce "where to eat" friction

**Q3: What's the unique value proposition?**
The only app that combines cycle phase data with food craving predictions, backed by [peer-reviewed research](https://pmc.ncbi.nlm.nih.gov/articles/PMC10316899/) on hormone-driven food preferences.

**Q4: How will this make money?**
- Freemium model with $5.99/month premium
- Restaurant affiliate commissions (secondary)
- Meal kit partnerships (future)

**Q5: What's the success metric?**
- Year 1: 500 paid subscribers ($35K ARR)
- Validation: 500+ landing page signups before full development

---

### Part 2: Technical Requirements

**Q6: What platform(s)?**
Mobile (iOS first, Android second) via React Native + Expo

**Q7: What data sources are needed?**
- Apple Health (cycle data from Flo, Clue, etc.)
- User-logged food preferences
- Location (for restaurant recommendations)
- Weather API (cravings correlate with weather)

**Q8: What integrations are required?**
- Apple HealthKit (cycle data)
- Terra API (Clue integration) - future
- Google Places API (restaurant discovery)
- Weather API (OpenWeather or similar)

**Q9: What's the technical complexity?**
Medium-High
- HealthKit integration (iOS-specific)
- ML prediction model (can start simple, iterate)
- Cross-platform mobile development

**Q10: What are the technical risks?**
- Apple HealthKit approval process
- Prediction accuracy expectations
- Privacy/security for health data

---

### Part 3: App Type Decision

**Q11: Primary platform?**
Mobile App (iOS/Android)

**Q12: Mobile App Viability Score?**
35/40 (Strong candidate)

| Factor | Score | Rationale |
|--------|-------|-----------|
| Location Dependency | 4/5 | Often deciding food while out |
| Frequency | 5/5 | Daily meal decisions |
| Session Length | 5/5 | Quick check (<2 min) |
| Offline Need | 2/5 | Nice to have, not critical |
| Push Notifications | 4/5 | "You might crave X today" |
| Device Features | 3/5 | HealthKit, location |
| Competition | 5/5 | No direct competitors |
| Revenue Model | 4/5 | Wellness subscriptions proven |

**Q13: Why not MCP/CLI/Web?**
- Users are on-the-go when deciding food
- Need Apple HealthKit for cycle data
- Push notifications add significant value
- Mobile-first wellness market

---

### Part 4: Resource Assessment

**Q14: Development time estimate?**
- MVP: 4-6 weeks (React Native + Expo)
- Landing page: 1 day
- Full v1.0: 8-10 weeks

**Q15: Ongoing costs?**
| Cost | Monthly | Annual |
|------|---------|--------|
| Apple Developer | - | $99 |
| Expo (free tier) | $0 | $0 |
| Backend hosting | $20 | $240 |
| Weather API | $0 | $0 (free tier) |
| **Total** | ~$20 | ~$340 |

**Q16: Revenue projection?**
| Year | Paid Users | ARR |
|------|------------|-----|
| Year 1 | 500 | $35,940 |
| Year 2 | 1,500 | $107,820 |
| Year 3 | 4,500 | $323,460 |

---

### Part 5: Template Decision

**Q17: Use existing template?**
Clean slate - no existing mobile app template in dev-sandbox

**Q18: Innovation level?**
Medium - Novel prediction concept, standard mobile development

**Q19: Template vs clean slate rationale?**
Clean slate because:
- First React Native project in portfolio
- Unique data model (cycle + food)
- Learning opportunity for mobile development

---

## App Type Decision

**Selected**: Mobile App (React Native + Expo)

**Rationale**:
- Mobile viability score 35/40 (strong)
- Apple HealthKit required for core feature
- Users decide food while mobile
- Wellness apps thrive on mobile

**Framework**: React Native + Expo
- Fastest path to both iOS and Android
- Expo handles 90% of native complexity
- OTA updates for quick iteration

---

## Cost-Benefit Analysis

### Costs (Year 1)
| Category | Amount |
|----------|--------|
| Development time | 160-240 hours |
| Apple Developer | $99 |
| Hosting | $240 |
| Marketing | $500 |
| Provisional patent | $2,000 |
| **Total** | ~$2,840 + time |

### Benefits (Year 1)
| Benefit | Value |
|---------|-------|
| Subscription revenue | $35,940 |
| Learning (mobile dev) | Priceless |
| Portfolio piece | High value |
| Partnership potential | TBD |

### Break-even
~Month 1 of paid subscriptions (if hitting targets)

---

## MVP Feature Set

### Phase 1: Core (Weeks 1-3)
- [ ] User onboarding (cycle tracking setup)
- [ ] Apple Health integration (read cycle data)
- [ ] Basic craving logging (what did you eat?)
- [ ] Pattern visualization (calendar view)
- [ ] Simple predictions ("Based on your cycle, you might want...")

### Phase 2: Intelligence (Weeks 4-5)
- [ ] Time-of-day patterns
- [ ] Day-of-week patterns
- [ ] Weather correlation
- [ ] Improved prediction algorithm

### Phase 3: Social (Week 6)
- [ ] Partner sharing (premium feature)
- [ ] "Share my cravings" link
- [ ] Partner view (what she might want today)

### Phase 4: Monetization (Week 7-8)
- [ ] Premium subscription (RevenueCat)
- [ ] Restaurant recommendations (affiliate)
- [ ] Analytics dashboard

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | React Native + Expo |
| Navigation | Expo Router |
| State | Zustand |
| Backend | Supabase (auth + DB) |
| Health Data | Apple HealthKit |
| Payments | RevenueCat |
| Analytics | Mixpanel |
| Push Notifications | Expo Notifications |

---

## Pre-Development Validation

Before building, validate with landing page:

**Target**: 500 email signups

**Landing page content**:
- Headline: "Finally understand why you crave what you crave"
- Subhead: "CraveSmart predicts your food cravings based on your cycle"
- Email capture: "Get early access"
- Social proof: "Backed by research from UCLA and PMC"

**Distribution**:
- Reddit: r/xxfitness, r/1200isplenty, r/PeriodDramas
- TikTok: Craving-related content
- Instagram: Wellness influencer outreach

---

## IP Protection Checklist

Before partnership outreach:
- [ ] File provisional patent ($2K)
- [ ] Create public timestamp (blog post)
- [ ] Ensure all code in git with dates
- [ ] Prepare NDA template

---

## Next Steps

1. **Today**: Create landing page for validation
2. **This week**: Initialize Expo project, set up dev environment
3. **Week 1**: Apple HealthKit integration
4. **Week 2**: Craving logging and pattern detection
5. **Week 3**: Prediction algorithm v1
6. **Week 4+**: Iterate based on feedback

---

## Decision

**GO** - Proceed with CraveSmart development

**Conditions**:
- [x] Market research complete (SOP 17)
- [x] Pivot from problematic branding
- [x] IP protection strategy defined
- [ ] Landing page validates 500+ signups (in progress)

---

*Kickoff Date: January 18, 2026*
*Project Lead: William*
