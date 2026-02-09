# X Automation Plan - AI Automation Agency

**Created:** January 19, 2026 (End of Day)
**Status:** Plan approved, ready to implement tomorrow
**Goal:** Build X audience (500-1000 followers in 30 days) while POCs are running

---

## Quick Summary

**What we're building:**
- Automated X posting: 25 posts/day about AI automation agency services
- 50% posts get Grok-generated images (~$26/month cost)
- Focus: Voice AI, lead gen, automation (NOT Square Foot Shipping/HVAC)
- Account: Personal (@wmarceau) - "building in public" approach

**Why now:**
- Build audience WHILE running POCs (not after)
- Share real POC results = social proof
- Have engaged followers ready when POCs finish

---

## Implementation Tomorrow (3-Day Plan)

### Day 1: Content Creation
1. Create AI agency content bank in `templates/business_content.json`
   - 20+ pain points
   - 20+ solutions
   - 20+ benefits/stats
   - Case study templates (for POC updates)

2. Add `marceau-solutions` config in `config/businesses.json`
   - Services, hashtags, posting schedule (25/day)

### Day 2: Technical Integration
3. Add Grok image generation to `business_content_generator.py`
   - `_generate_grok_image()` method
   - `_build_image_prompt()` method
   - Update `generate_post()` to support images

4. Update `business_scheduler.py` for 25 posts/day
   - Read `posts_per_day` from config
   - 50% image generation logic

### Day 3: Deploy & Monitor
5. Update cron jobs (9 times/day: 6 AM - 10 PM)
6. Run dry-run test
7. Go live
8. Monitor first 24 hours

---

## Content Strategy

**5 Content Pillars:**
1. **Service Highlights (25%)** - Voice AI, lead gen, automation services
2. **Case Study Updates (25%)** - Real POC metrics from HVAC/Shipping
3. **Tech How-To (20%)** - Tutorials, tool shares, tech stack
4. **Industry Insights (15%)** - Stats, trends, ROI calculations
5. **Behind-the-Scenes (15%)** - Building in public, wins, challenges

**Example Posts:**
```
"Week 1 POC Results: Voice AI for HVAC

📞 47 calls answered
📅 12 appointments booked
💰 ~$8K recovered revenue
⏱️ 0 missed calls at night

All automated. Owner just shows up to jobs.

This is the future of local service businesses."
```

---

## Posting Schedule

**25 posts/day across optimal times:**

| Time | Posts | Why |
|------|-------|-----|
| 6 AM | 2 | Early birds |
| 8 AM | 3 | Commute |
| 10 AM | 2 | Mid-morning |
| 12 PM | 4 | Lunch (peak) |
| 2 PM | 2 | Afternoon |
| 4 PM | 3 | End of workday |
| 6 PM | 4 | Evening (peak) |
| 8 PM | 3 | Night scroll |
| 10 PM | 2 | Late night |

**Cron jobs:** Every 2 hours (9 times/day)

---

## Image Generation Strategy

**50% of posts get Grok images:**

✅ **Always get image:**
- Case study updates with metrics
- Service highlights
- Stat/insight posts
- Before/after comparisons

❌ **Text only:**
- Quick tips
- Questions
- Behind-the-scenes personal posts

**Cost:** ~$26/month (12.5 images/day × $0.07)

---

## Expected Results (30 Days)

**Audience Growth:**
- +500-1000 followers
- Engagement rate: 2-5% (with images)

**Content Output:**
- 750 posts total (25/day × 30)
- 375 with Grok images
- Mix: 25% case studies, 25% services, 50% thought leadership

**Business Value:**
- Engaged audience ready when POCs finish
- Social proof from real POC metrics
- Positioned as AI automation expert

---

## Files to Modify

| File | What to Add |
|------|-------------|
| `templates/business_content.json` | `marceau-solutions` content bank |
| `config/businesses.json` | `marceau-solutions` business config |
| `src/business_content_generator.py` | Grok image generation methods |
| `src/business_scheduler.py` | 25 posts/day logic |
| `scripts/setup_posting_schedule.sh` | Update cron to 9 times/day |

---

## Account Recommendation

**Use personal account (@wmarceau):**

**Why:**
- Trust: People buy from people, not logos
- Building in public: Share POC journey authentically
- Network effects: Connect with founders/builders
- Flexibility: Can pivot without rebranding

**Strategy:**
- Months 1-6: Personal account (thought leadership)
- Month 6+: Launch brand account (@MarceauSolutions) for sales/marketing
- Best of both worlds

---

## Next Session Checklist

Tomorrow morning, start with:

1. ✅ Review full plan: `/Users/williammarceaujr./.claude/plans/humble-cooking-journal.md`
2. Create content bank (pain points, solutions, stats for AI agency)
3. Add business config
4. Implement Grok integration
5. Test with 1-2 sample posts
6. Deploy if tests pass

**Estimated time:** 2-3 hours for full implementation

---

**This runs parallel to POC monitoring - we'll build audience AND validate services simultaneously.**
