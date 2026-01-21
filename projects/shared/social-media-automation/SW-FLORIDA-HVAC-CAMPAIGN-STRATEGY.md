# SW Florida Comfort HVAC - Social Media Campaign Strategy
**Created:** January 20, 2026
**Status:** Planning Phase

---

## Executive Summary

Launch automated social media campaign for SW Florida Comfort HVAC to build local brand awareness, generate emergency service calls, and promote preventive maintenance plans.

**Target Platform:** X (Twitter)
**Goal:** 5-10 qualified leads/month from social
**Posting Frequency:** 3-5 posts/day (90-150 posts/month)
**Image Strategy:** 30-40% with Grok-generated images
**Budget:** ~$10-15/month (Grok images)

---

## Phase 0: Market Viability Assessment (SOP 17)

### Business Context
- **Existing Business:** ✅ SW Florida Comfort HVAC is operational
- **Proven Service:** ✅ Voice AI POC answering calls, website live at https://www.swfloridacomfort.com
- **Customer Base:** ✅ Serving Naples/Fort Myers/Cape Coral area
- **Revenue Model:** ✅ AC repair, maintenance plans, new installations

**SOP 17 Decision:** SKIP full market viability analysis
- **Reason:** This is marketing for an existing profitable business, not a new product validation
- **Alternative:** Proceed with campaign ROI analysis instead

### Campaign ROI Analysis

| Metric | Estimate | Source |
|--------|----------|--------|
| **Market Size (TAM)** | 400K+ homes in SWFL | Census data |
| **AC ownership rate** | 98% (Florida necessity) | Industry avg |
| **Annual service need** | 2x/year (spring tune-up + summer emergency) | HVAC standards |
| **Average ticket** | $300 (repair), $199 (maintenance), $6K (new install) | Industry avg |
| **Serviceable Market (SAM)** | 50K homes (10-mile radius Naples/FM) | Local targeting |

**Social Media Benchmarks (HVAC Industry)**:
- Engagement rate: 1-3% (good for local service)
- Conversion to call: 0.5-2% of engaged audience
- Cost per lead: $20-50 (organic social)
- Lead-to-customer: 10-20% close rate

**Projected Results (Month 1-3)**:
- 90-150 posts/month → 500-1,000 impressions/post (conservative)
- Total reach: 45K-150K impressions/month
- Engagement (2%): 900-3,000 interactions
- Leads (0.5%): 5-15 calls/month
- Closed deals (15%): 1-2 customers/month
- Revenue: $300-$6,000/month
- **ROI**: 20x-400x (spend $15, earn $300-$6K)

**Decision:** ✅ GO - High ROI, low risk, existing business

---

## Phase 1: Content Strategy (AI Automation Agency Model Applied to HVAC)

### Account Strategy

**Recommendation:** Brand Account (@SWFloridaComfort or similar)

**Why Brand vs Personal for HVAC:**
- ✅ **Local trust:** "SW Florida Comfort" = geographic + service clarity
- ✅ **Emergency credibility:** People call businesses for AC repair, not individuals
- ✅ **Scalable:** Can be run by office manager/team, not just William
- ✅ **24/7 consistency:** Matches 24/7 emergency service positioning
- ❌ **Personal connection:** Less "building in public" but not critical for HVAC

**Account Setup:**
- **Handle:** @SWFLComfortAC or @SWFloridaHVAC
- **Display Name:** SW Florida Comfort HVAC
- **Bio:** "24/7 AC Repair • Naples, Fort Myers, Cape Coral • Same-Day Service • No Overtime Charges • (239) 766-6129 🌴❄️"
- **Location:** Naples, FL
- **Link:** https://www.swfloridacomfort.com

### Content Pillars (5 Themes)

| Pillar | % of Posts | Purpose | Example |
|--------|-----------|---------|---------|
| **1. Emergency Readiness** | 30% | Position as 24/7 go-to | "AC out? Florida heat won't wait. 24/7 service: (239) 766-6129" |
| **2. Preventive Maintenance** | 25% | Sell tune-ups/plans | "90% of AC failures are preventable. $199 tune-up → avoid $3K repairs" |
| **3. Educational Tips** | 20% | Build authority | "Change your filter every 1-3 months. Dirty filter = 30% higher bills" |
| **4. Seasonal Reminders** | 15% | Timely urgency | "Summer's coming. Book your spring tune-up before the rush" |
| **5. Local Pride/Social Proof** | 10% | Build trust | "Proudly serving Naples families for 10+ years. Your neighbors trust us." |

**Content Mix**:
- 70% service-focused (emergency, maintenance, installs)
- 20% educational (tips, stats, how-to)
- 10% trust-building (local pride, testimonials)

### Seasonal Strategy (Critical for HVAC)

**Q1 (Jan-Mar): Pre-Summer Prep**
- Theme: "Get ready before the heat"
- Focus: Spring tune-ups, maintenance plans
- Urgency: Medium (prevent future breakdowns)
- Post frequency: 3-4/day
- Example: "Summer temps hit 95°+ in Naples by May. Is your AC ready? Book your spring tune-up now."

**Q2 (Apr-Jun): Peak Emergency Season**
- Theme: "We're here when you need us"
- Focus: 24/7 emergency, same-day repair
- Urgency: HIGH (AC failures spike)
- Post frequency: 5-6/day (peak season)
- Example: "AC out? In Florida, that's an emergency. We're available 24/7, no overtime: (239) 766-6129"

**Q3 (Jul-Sep): Efficiency & Upgrades**
- Theme: "Beat the heat AND the bill"
- Focus: Energy savings, system upgrades
- Urgency: Medium (people see high bills)
- Post frequency: 4-5/day
- Example: "Energy bill jumped $200 this month? Your 10-year-old AC is working 40% harder. Time to upgrade."

**Q4 (Oct-Dec): Planning & Deals**
- Theme: "Smart off-season planning"
- Focus: New installs, financing, year-end specials
- Urgency: Low (off-season)
- Post frequency: 3/day
- Example: "New AC installation takes 1 day. Start next summer cool. Financing available. (239) 766-6129"

**Current Season (January):** Q1 Pre-Summer Prep - PERFECT timing for maintenance push

---

## Phase 2: Technical Implementation

### Existing Infrastructure

**Already Built** (per templates/business_content.json):
- ✅ Content bank: 7 pain points, 6 solutions, 6 benefits, 5 stats, 5 tips
- ✅ Post templates: 6 formats (emergency, promo, educational, seasonal, social proof, stat hooks)
- ✅ Campaigns: 4 pre-defined (emergency, maintenance, new-install, local-trust)
- ✅ Seasonal content: 4 quarters with messaging
- ✅ Scheduler infrastructure: business_scheduler.py supports swflorida-hvac

**Status:** 8 posts already scheduled (ready to post)

### Configuration Required

**1. Business Configuration** (config/businesses.json or equivalent)

Need to verify/create:
```json
{
  "swflorida-hvac": {
    "name": "SW Florida Comfort HVAC",
    "tagline": "24/7 AC Repair & Maintenance",
    "website": "https://www.swfloridacomfort.com",
    "phone": "(239) 766-6129",
    "location": "Naples, Fort Myers, Cape Coral, FL",
    "services": [
      "24/7 Emergency AC Repair",
      "AC Maintenance & Tune-Ups",
      "New AC Installation",
      "Air Quality Solutions"
    ],
    "hashtags": {
      "primary": ["ACRepair", "HVAC", "SWFL"],
      "secondary": ["Naples", "FortMyers", "FloridaLiving", "EmergencyHVAC"],
      "local": ["Naples", "CapeCoral", "FortMyers", "FloridaHeat"]
    },
    "posting_schedule": {
      "posts_per_day": 4,  // Start conservative
      "optimal_times": [7, 10, 14, 18, 21],  // Morning, mid-day, afternoon, evening, night (emergencies happen 24/7)
      "seasonal_multiplier": {
        "q1": 1.0,   // 4 posts/day
        "q2": 1.5,   // 6 posts/day (peak)
        "q3": 1.25,  // 5 posts/day
        "q4": 0.75   // 3 posts/day (slow season)
      }
    },
    "campaigns": {
      "default": "emergency-awareness",  // Always emphasize 24/7 availability
      "seasonal": {
        "q1": "maintenance-push",
        "q2": "emergency-awareness",
        "q3": "energy-efficiency",
        "q4": "new-install"
      }
    }
  }
}
```

**2. Image Generation Strategy**

**Which posts get Grok images:**
- ✅ Seasonal reminders (visual impact)
- ✅ Stat hooks (infographic-style)
- ✅ Service promos (professional illustration)
- ❌ Emergency posts (text urgency > image)
- ❌ Quick tips (simple text works)
- ❌ Local pride (optional)

**Target:** 30-40% of posts = ~1.2-1.6 images/day = ~40-50 images/month

**Cost Projection:**
- 40-50 images/month × $0.07 = **$2.80-$3.50/month** (very affordable)

**Image Prompts Examples:**
```
Emergency: "Professional HVAC technician arriving at Naples home, modern service truck, Florida palm trees, blue sky, clean illustration style"

Maintenance: "Clean modern AC unit being serviced by professional, checklist clipboard, Florida residential home, professional photography style"

Seasonal: "Split image: Struggling old AC unit vs efficient new unit, energy bill comparison, modern infographic design"
```

**3. Posting Schedule (Cron Jobs)**

**Phase 1 (Month 1-2): Conservative Start**
- 4 posts/day
- Times: 7 AM, 12 PM, 5 PM, 9 PM
- Total: ~120 posts/month
- Purpose: Test engagement, refine messaging

**Phase 2 (Month 3+): Scale Based on Data**
- If engagement good: Scale to 5-6 posts/day
- If conversion happening: Increase seasonal posts
- If slow: A/B test different templates

**Cron Configuration:**
```bash
# HVAC posting schedule (4x daily)
0 7 * * *   cd /path && python -m src.business_scheduler post --business swflorida-hvac --count 1
0 12 * * *  cd /path && python -m src.business_scheduler post --business swflorida-hvac --count 1
0 17 * * *  cd /path && python -m src.business_scheduler post --business swflorida-hvac --count 1
0 21 * * *  cd /path && python -m src.business_scheduler post --business swflorida-hvac --count 1

# Weekly batch generation (Sundays)
0 6 * * 0   cd /path && python -m src.business_scheduler schedule-week --business swflorida-hvac
```

---

## Phase 3: Campaign Execution Plan

### Week 1: Launch (Test & Learn)

**Goals:**
- Verify automation working
- Test post templates
- Gauge initial engagement

**Actions:**
1. ✅ Verify 8 posts already scheduled
2. Generate 20 more posts for Week 1 (4/day × 5 days + buffer)
3. Include 6-8 Grok images (30% of posts)
4. Monitor: Impressions, likes, retweets, profile visits
5. Track: Any phone calls mentioning "saw on Twitter/X"

**Success Metrics (Week 1):**
- ✅ All posts publish on schedule
- ✅ 100+ impressions per post
- ✅ 1-3% engagement rate
- ✅ 0-1 phone inquiries (early days)

### Month 1: Establish Rhythm

**Goals:**
- Build content library
- Establish posting consistency
- Start A/B testing

**Actions:**
1. Generate 120 posts (30 days × 4/day)
2. Rotate through all 6 post templates
3. Test campaigns: emergency-awareness vs maintenance-push
4. Create 40 Grok images
5. Monitor call tracking: "How did you hear about us?"

**Success Metrics (Month 1):**
- ✅ 120 posts published
- ✅ 500-1,000 avg impressions/post
- ✅ 100+ profile visits
- ✅ 2-5 phone inquiries from social

### Month 2-3: Optimize & Scale

**Goals:**
- Identify winning templates
- Scale successful campaigns
- Generate measurable ROI

**Actions:**
1. Analyze top 10% performing posts
2. Double down on high-engagement templates
3. Scale to 5 posts/day if engagement strong
4. A/B test: Emergency urgency vs Educational value
5. Add call tracking: "Mention this post for $20 off"

**Success Metrics (Month 2-3):**
- ✅ 5-10 qualified leads/month
- ✅ 1-2 booked jobs from social
- ✅ 1,000+ impressions/post (top posts)
- ✅ Identifiable ROI (>10x)

---

## Phase 4: Success Criteria & KPIs

### Leading Indicators (Track Weekly)

| Metric | Week 1 Goal | Month 1 Goal | Month 3 Goal |
|--------|-------------|--------------|--------------|
| Posts Published | 28 | 120 | 360 |
| Avg Impressions/Post | 100+ | 500+ | 1,000+ |
| Engagement Rate | 1% | 2% | 3% |
| Profile Visits | 20+ | 100+ | 300+ |
| Website Clicks | 5+ | 20+ | 50+ |

### Lagging Indicators (Track Monthly)

| Metric | Month 1 | Month 3 | Month 6 |
|--------|---------|---------|---------|
| Phone Inquiries (social) | 2-5 | 5-10 | 10-20 |
| Booked Jobs | 0-1 | 1-2 | 3-5 |
| Revenue (social attribution) | $0-$300 | $300-$1,200 | $1,000-$5,000 |
| Followers | 50+ | 150+ | 500+ |
| ROI | 0-20x | 20-80x | 67-333x |

### Conversion Funnel

```
POSTS (120/mo)
  ↓ (2% engagement)
ENGAGED USERS (2,400)
  ↓ (1% click to website)
WEBSITE VISITORS (24)
  ↓ (20% call)
PHONE CALLS (5)
  ↓ (20% book)
BOOKED JOBS (1)
  ↓ (avg $300-$6K)
REVENUE ($300-$6,000)

Cost: $15/mo (Grok images)
ROI: 20x-400x
```

---

## Phase 5: Risk Mitigation

### Potential Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Low engagement** | Medium | Medium | A/B test templates, adjust posting times |
| **No conversions** | Low | High | Add call tracking codes, test different CTAs |
| **Automation breaks** | Low | Low | Monitor daily, have manual backup |
| **Negative comments** | Low | Medium | Respond quickly, have crisis plan |
| **Platform changes** | Low | Medium | Diversify (add Facebook, Instagram later) |
| **Seasonal slowdown** | High | Low | Expected in Q4, scale back posting |

### Contingency Plans

**If engagement is low (<1%):**
- Test posting at different times
- Add more images (increase to 50%)
- Try video content (short clips)
- Engage with local community (reply, retweet)

**If no leads after 60 days:**
- Review call tracking (are people calling without mentioning social?)
- Test aggressive CTAs ("Call now for $50 off")
- Add special social-only offers
- Consider paid promotion for best posts

---

## Phase 6: Next Steps (Action Plan)

### Immediate (This Week)

1. ✅ Review existing 8 scheduled posts
2. Generate 20 additional posts for Week 1
3. Create Grok images for 6-8 posts
4. Set up call tracking question: "How did you hear about us?"
5. Configure cron jobs for automated posting

### Short-Term (Next 30 Days)

6. Generate full Month 1 content (120 posts)
7. Monitor daily performance
8. Document winning templates
9. Set up analytics dashboard
10. Train Voice AI to ask about social media referrals

### Long-Term (90 Days)

11. Scale to 5 posts/day if successful
12. Add seasonal campaign rotation
13. Create special social-only offers
14. Consider expanding to Facebook/Instagram
15. Generate case study: "How Social Media Generated $X in HVAC Revenue"

---

## Appendix: Template Examples

### Example Post Schedule (Typical Week)

**Monday:**
- 7 AM: Emergency readiness + image
- 12 PM: Educational tip
- 5 PM: Stat hook
- 9 PM: Seasonal reminder

**Tuesday:**
- 7 AM: Service promo + image
- 12 PM: Local pride
- 5 PM: Emergency readiness
- 9 PM: Educational tip

**Wednesday:**
- 7 AM: Seasonal reminder + image
- 12 PM: Stat hook
- 5 PM: Social proof
- 9 PM: Emergency readiness

*[Continue pattern...]*

### Sample Posts (Ready to Use)

**Emergency Readiness:**
```
AC out? In Florida, that's an emergency.

24/7 service
No overtime charges
Same-day repair

Call now: (239) 766-6129

#ACRepair #SWFL
```

**Preventive Maintenance:**
```
90% of AC failures are preventable.

A $199 tune-up can save you $3,000+ in emergency repairs.

Don't wait until it fails.

Book now: (239) 766-6129

#HVAC #PreventiveMaintenance
```

**Educational Tip:**
```
Quick HVAC tip:

Set your thermostat to 78°F for best efficiency.

Every degree lower = 6-8% higher energy bill.

Need a tune-up? (239) 766-6129

#HVACTips #FloridaLiving
```

**Seasonal (Q1):**
```
Summer temps hit 95°+ in Naples by May.

Is your AC ready?

Book your spring tune-up now, before the rush.

(239) 766-6129

#HVAC #Naples
```

**Stat Hook:**
```
Florida AC units work 3x harder than the national average.

That's why annual maintenance isn't optional here.

Protect your investment.

(239) 766-6129

#HVAC #FloridaHeat
```

---

## Recommendation

**✅ PROCEED with SW Florida Comfort HVAC social media campaign**

**Why:**
- Low risk ($15/month)
- High potential ROI (20x-400x)
- Infrastructure already built
- Seasonal timing perfect (Q1 maintenance push)
- Complements existing Voice AI and website

**Start:** This week (January 20-27, 2026)
**First Milestone:** 30 days / 120 posts
**First Review:** February 20, 2026

**Expected Outcome:** 1-2 booked jobs/month from social by Month 3 = $3K-$12K annual revenue from $180 investment (20x-67x ROI)
