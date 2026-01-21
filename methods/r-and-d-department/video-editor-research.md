# Video Editor API Research
**Purpose:** Document researched video editing APIs for future TikTok/social media automation
**Status:** Shotstack currently in use, alternatives documented for future optimization
**Last Updated:** January 21, 2026

---

## Decision Matrix

| Tool | Cost | Ease of Use | Features | Status |
|------|------|-------------|----------|--------|
| **Shotstack** | Pay-per-render | ⭐⭐⭐⭐ Good | Full featured | ✅ **Currently Using** |
| **Creatomate** | Subscription | ⭐⭐⭐⭐⭐ Excellent | Template-based | 🔍 Researched |
| **Remotion** | Free (self-host) | ⭐⭐ Complex (React) | Unlimited | 📋 For consideration |
| **Zapier/Make + Shotstack** | Combination | ⭐⭐⭐⭐⭐ No-code | Workflow automation | 💡 **NEW** (from email) |

---

## 1. Shotstack (Currently Using)

**Website:** https://shotstack.io
**Pricing:** Pay-per-render (~$0.10-0.50 per video depending on length/complexity)
**Status:** ✅ Active integration

### Pros:
- ✅ JSON-based API (easy to template)
- ✅ Cloud rendering (no local compute)
- ✅ Good documentation
- ✅ Already integrated in our system

### Cons:
- ❌ Pay-per-render (can get expensive at scale)
- ❌ Render queue delays during peak times

### Use Cases:
- TikTok video generation (fitness influencer)
- Before/After videos (HVAC)
- Automated social media content

### Integration Status:
- **Environment variable:** `SHOTSTACK_API_KEY` (in `.env`)
- **Usage:** `projects/marceau-solutions/fitness-influencer/` (if exists)
- **Documentation:** Likely in project README or workflows

---

## 2. Creatomate (Researched Alternative)

**Website:** https://creatomate.com
**Pricing:** Subscription-based ($49-199/month unlimited renders)
**Status:** 🔍 Researched, not implemented

### Pros:
- ✅ Unlimited renders (predictable cost)
- ✅ Template editor (visual, no code)
- ✅ Fast rendering
- ✅ Better for high-volume use cases

### Cons:
- ❌ Monthly subscription (vs pay-as-you-go)
- ❌ Would require migration from Shotstack

### When to Reconsider:
- If creating >100 videos/month (break-even point)
- If Shotstack costs exceed $49/month
- If need faster render times

### Migration Effort:
- Low-Medium: Both use JSON templates
- Would need to recreate templates in Creatomate format
- API integration similar complexity

---

## 3. Remotion (Open Source)

**Website:** https://remotion.dev
**Pricing:** Free (self-hosted) or $15/month (cloud rendering)
**Status:** 📋 For future consideration

### Pros:
- ✅ Free (self-hosted)
- ✅ React-based (programmatic control)
- ✅ Unlimited renders
- ✅ Full customization

### Cons:
- ❌ Requires React knowledge
- ❌ Self-hosting complexity (or pay for cloud)
- ❌ Steeper learning curve

### When to Reconsider:
- If need highly custom video logic
- If rendering >500 videos/month
- If have dev resources to maintain

---

## 4. Zapier/Make + Shotstack Integration (NEW - from email)

**Email Source:** Derk @ Shotstack (Jan 21, 2026 7:19 AM)
**Subject:** "Use Zapier or Make to create videos programmatically without touching any code"

### Concept:
Combine no-code automation (Zapier/Make) with Shotstack's video rendering API

### Potential Workflows:

#### Workflow 1: Automated TikTok from Form Submissions
```
Google Forms (HVAC service request)
  ↓
Zapier trigger
  ↓
Shotstack (generate before/after video template)
  ↓
TikTok API (auto-post video)
```

#### Workflow 2: Social Media from ClickUp Tasks
```
ClickUp (new lead marked "Won")
  ↓
Make.com trigger
  ↓
Shotstack (generate testimonial video)
  ↓
Multi-platform post (LinkedIn/Facebook/TikTok)
```

#### Workflow 3: Automated Fitness Content
```
Scheduled trigger (daily 6 AM)
  ↓
Zapier webhook
  ↓
Shotstack (generate workout tip video from template)
  ↓
Instagram Reels + TikTok + YouTube Shorts
```

### Pros:
- ✅ No Python code needed for video workflows
- ✅ Non-technical team members can create videos
- ✅ Visual workflow builder
- ✅ Combines with existing Shotstack investment

### Cons:
- ❌ Zapier/Make monthly cost ($20-50/month)
- ❌ Less flexible than code
- ❌ Additional platform dependency

### When to Implement:
- **Phase 1 (Now):** Stick with Python + Shotstack API (more control)
- **Phase 2 (After scaling):** Add Zapier/Make for non-dev team to create videos
- **Phase 3 (Team growth):** Train others to use no-code video creation

### Integration Path:
1. Keep current Python Shotstack integration
2. Add Zapier/Make later for:
   - Client self-service video creation
   - Marketing team to create content without dev
   - Automated workflows triggered by external events

---

## Cost Comparison (at scale)

### Scenario: 100 videos/month

| Solution | Monthly Cost | Notes |
|----------|-------------|-------|
| **Shotstack only** | $10-50 | Depends on video length/complexity |
| **Creatomate** | $49 | Unlimited renders |
| **Remotion (cloud)** | $15 + compute | $15 base + AWS costs |
| **Shotstack + Zapier** | $30-70 | Shotstack + Zapier Pro ($20/month) |

### Scenario: 500 videos/month

| Solution | Monthly Cost | Notes |
|----------|-------------|-------|
| **Shotstack only** | $50-250 | Gets expensive |
| **Creatomate** | $99-199 | Still unlimited |
| **Remotion (cloud)** | $15 + $50-100 compute | More cost-effective |
| **Shotstack + Zapier** | $70-270 | Not ideal at this scale |

---

## Decision Framework

### Use Shotstack When:
- Creating <100 videos/month
- Need simple template-based videos
- Want to pay only for what you use
- Already have integration working

### Switch to Creatomate When:
- Creating >100 videos/month consistently
- Shotstack costs exceed $49/month
- Need faster render times
- Want predictable pricing

### Switch to Remotion When:
- Creating >500 videos/month
- Need highly custom video logic
- Have dev resources to maintain
- Want full control over rendering

### Add Zapier/Make When:
- Non-technical team needs to create videos
- Want to automate video creation from external triggers
- Have budget for additional tool ($20-50/month)

---

## Current Recommendation

**Stick with Shotstack** until:
1. Creating >100 videos/month (then evaluate Creatomate)
2. Costs exceed $49/month (then switch to Creatomate)
3. Team grows and needs self-service video creation (then add Zapier/Make)

**Next Review:** After 3 months of TikTok automation (April 2026)
- Evaluate actual video volume
- Calculate actual Shotstack costs
- Determine if migration makes sense

---

## References

- **Shotstack docs:** https://shotstack.io/docs/
- **Creatomate docs:** https://creatomate.com/docs
- **Remotion docs:** https://remotion.dev/docs
- **Zapier Shotstack integration:** https://zapier.com/apps/shotstack/integrations
- **Email (saved):** Derk @ Shotstack Jan 21, 2026

---

## Integration Locations

| Tool | Code Location | Status |
|------|---------------|--------|
| Shotstack API | `execution/shotstack_api.py` (if exists) | Check existence |
| Shotstack in Fitness | `projects/marceau-solutions/fitness-influencer/` | Check usage |
| Video templates | `templates/videos/` (if exists) | Check storage location |

---

**Action Items:**
- [ ] Verify Shotstack integration location
- [ ] Document current Shotstack usage/cost
- [ ] Set reminder to review in April 2026 (3 months)
- [ ] File Zapier/Make integration idea for Phase 2 (team scaling)
