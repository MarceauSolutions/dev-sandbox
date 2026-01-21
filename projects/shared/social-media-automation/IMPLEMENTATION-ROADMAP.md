# Social Media Automation - Complete Implementation Roadmap
**Date:** January 20, 2026
**Status:** Ready for Approval & Execution

---

## ✅ COMPLETED: Strategic Planning & Research

All platform analysis, API research, and implementation guides are complete. Awaiting approval to proceed with execution.

---

## Executive Summary

### Platform Strategy (Based on Audience Analysis)

**Marceau Solutions (AI Automation Services):**
- **PRIMARY:** LinkedIn (B2B decision-makers, thought leadership)
- **SECONDARY:** X/Twitter (tech community, building in public)
- **SKIP:** TikTok (wrong audience for B2B)

**SW Florida Comfort HVAC:**
- **PRIMARY:** TikTok (homeowners 35-65, educational videos)
- **SECONDARY:** Facebook (local groups, community trust)
- **SKIP:** X/Twitter (wrong audience for local services)

### Implementation Approach

**Recommended:** Hybrid Strategy
1. **Immediate (Week 1):** Sign up for Ayrshare ($49/month, all platforms)
2. **Parallel (Weeks 2-5):** Apply for LinkedIn Partner + TikTok audit
3. **Long-term (Month 3+):** Migrate to official APIs (free forever)

---

## Phase 1: Immediate Actions (Week 1)

### Setup Tasks

- [ ] **Sign up for Ayrshare** ($49/month)
  - Website: https://www.ayrshare.com
  - Plan: All platforms (LinkedIn, X, TikTok, Facebook, Instagram)
  - Get API key
  - Add to `.env`: `AYRSHARE_API_KEY=...`

- [ ] **Connect Accounts to Ayrshare:**
  - William Marceau LinkedIn (AI content)
  - @wmarceau X account (AI content)
  - @SWFloridaComfortAC TikTok (create first, then connect)
  - SW Florida Comfort Facebook page (create first, then connect)

- [ ] **Create @SWFloridaComfortAC TikTok Account:**
  - Download TikTok app
  - Create brand account
  - Bio: "24/7 AC Repair | Naples, Fort Myers, Cape Coral | (239) 766-6129 ❄️🌴"
  - Convert to Business Account
  - Category: Professional Services

- [ ] **Create SW Florida Comfort Facebook Page:**
  - Business page (not personal)
  - Add contact info, website, hours
  - Upload logo, cover photo
  - Join local groups (Naples Homeowners, Fort Myers Community, etc.)

### Content Creation Tasks

- [ ] **AI Content (LinkedIn + X):**
  - Optimize William Marceau LinkedIn profile
    - Professional headshot
    - Headline: "Building AI Automation for Local Businesses | Voice AI | Lead Gen"
    - About: Case studies, expertise, contact
  - Draft 15 LinkedIn posts (Month 1 content)
    - 5 case studies (POC results)
    - 5 tech insights (building in public)
    - 3 industry trends (AI adoption)
    - 2 engagement hooks (questions)
  - Adapt to X threads (4-8 tweets each)

- [ ] **HVAC Content (TikTok + Facebook):**
  - Film 7 TikTok videos (Week 1 content)
    - 3 educational tips ("3 signs AC failing")
    - 2 behind-the-scenes (repairs)
    - 2 before/after (transformations)
  - Edit videos with CapCut
    - Add text overlays (hook in first 3 seconds)
    - Add captions (sound-off viewing)
    - Add background music
    - Export 1080x1920 MP4
  - Write captions (TikTok short + Facebook long)
  - Upload to CDN (S3, Cloudflare, or Ayrshare hosting)

### Development Tasks

- [ ] **Install Ayrshare SDK:**
  ```bash
  pip install ayrshare
  ```

- [ ] **Create Ayrshare Integration:**
  - `src/ayrshare_api.py` - API wrapper
  - `src/cross_platform_poster.py` - Platform-specific formatting
  - `src/unified_scheduler.py` - Automated posting

- [ ] **Test Posting:**
  - Post 1 test to LinkedIn
  - Post 1 test to X
  - Post 1 test video to TikTok
  - Post 1 test to Facebook
  - Verify all work correctly

### Scheduling Tasks

- [ ] **Set Up Cron Jobs:**
  ```bash
  # AI content (LinkedIn + X)
  0 10 * * 2,3,4 - LinkedIn post
  0 12 * * 2,3,4 - X thread
  0 19 * * * - X posts (20-30/day continues as before)

  # HVAC content (TikTok + Facebook)
  0 7 * * * - TikTok video #1
  0 12 * * * - TikTok video #2
  0 19 * * * - TikTok video #3
  0 10 * * * - Facebook post
  ```

---

## Phase 2: Parallel Development (Weeks 2-5)

While using Ayrshare, work on official APIs in parallel:

### LinkedIn Official API

- [ ] **Apply for LinkedIn Partner Status:**
  - Create developer account: https://www.linkedin.com/developers/
  - Create OAuth app
  - Apply for Marketing Developer Platform
  - Wait 2-4 weeks for approval

- [ ] **Develop LinkedIn Integration:**
  - `src/linkedin_auth.py` - OAuth flow
  - `src/linkedin_api.py` - Posts API wrapper
  - `src/linkedin_scheduler.py` - Content scheduler
  - Test with dummy account (if available)

### TikTok Official API

- [ ] **Create TikTok Developer Account:**
  - Register: https://developers.tiktok.com/
  - Create app
  - Get Client Key and Secret

- [ ] **Submit for Audit:**
  - Build API integration
  - Submit audit request
  - Wait 2-4 weeks for approval
  - Meanwhile: Videos post as SELF_ONLY (private)

- [ ] **Develop TikTok Integration:**
  - `src/tiktok_auth.py` - OAuth flow
  - `src/tiktok_api.py` - Video upload API
  - `src/tiktok_scheduler.py` - Video queue manager

### X API (Already Have Access)

- [x] **X automation already working** (per humble-cooking-journal.md)
- [ ] **Continue current strategy:** 20-30 posts/day

### Facebook API

- [ ] **Create Facebook Developer Account:**
  - Register: https://developers.facebook.com/
  - Create app
  - Get Page Access Token

- [ ] **Develop Facebook Integration:**
  - `src/facebook_api.py` - Graph API wrapper
  - `src/facebook_scheduler.py` - Post scheduler

---

## Phase 3: Migration (Month 3+)

After official API approvals:

- [ ] **Switch from Ayrshare to Official APIs:**
  - Test official APIs in parallel with Ayrshare
  - Verify identical posting behavior
  - Cut over to official APIs
  - Cancel Ayrshare subscription

- [ ] **Cost Savings:**
  - Months 1-2: $98 (Ayrshare)
  - Months 3+: $0 (official APIs)
  - Annual Savings: $490

---

## Success Metrics & KPIs

### Month 1 Goals

**LinkedIn:**
- Posts: 12-20
- Impressions/post: 500+
- Engagement: 2-4%
- Profile visits: 100+
- Qualified leads: 1-3

**X:**
- Posts: 600-900
- Impressions/post: 500+
- Engagement: 1-3%
- Followers growth: +100
- Inquiries: 3-10

**TikTok:**
- Videos: 60-90
- Views/video: 500+
- Engagement: 3-5%
- Followers: 500+
- Leads: 10-20

**Facebook:**
- Posts: 30-60
- Reach: 200+/post
- Engagement: 2-4%
- Group members: Join 5 local groups
- Leads: 5-10

### Month 3 Goals

**Combined Results:**
- Total Reach: 115K-1.07M impressions
- Total Leads: 19-43/month
- Revenue: $29.5K-$110K/month
- ROI: 602x-2,245x

---

## Cost Breakdown

### Option A: Ayrshare Only (Ongoing)

**Monthly Cost:** $49

**Pros:**
- All platforms (LinkedIn, X, TikTok, Facebook, Instagram, YouTube)
- No development time
- Public posts immediately
- Analytics dashboard

**Cons:**
- Ongoing cost ($588/year)

**ROI:** 602x-2,245x ($49 → $29.5K-$110K)

### Option B: Hybrid (Recommended)

**Months 1-2:** $98 (Ayrshare)
**Months 3+:** $0 (official APIs)

**Total Year 1:** $98 + development time
**Total Year 2+:** $0

**Annual Savings:** $490/year (vs Ayrshare ongoing)

---

## Decision Points

### Decision 1: Ayrshare or Official APIs?

**Recommendation:** Hybrid
- Start with Ayrshare (immediate results)
- Build official APIs in parallel
- Migrate after approvals

**Justification:**
- Don't wait 8-10 weeks for all API approvals
- Build audience while developing
- Migrate when ready (save $588/year long-term)

### Decision 2: Post Frequency

**LinkedIn:** 3-5 posts/week (quality > quantity)
**X:** 20-30 posts/day (volume + engagement)
**TikTok:** 2-3 videos/day (consistency)
**Facebook:** 1-2 posts/day (community engagement)

**Total:** ~200-250 posts/week across all platforms

### Decision 3: Image/Video Generation

**Grok Images for X:** 50% of posts (~$26/month)
**TikTok Videos:** DIY with smartphone (free) or outsource ($10-30/video)
**LinkedIn Images:** Optional (text-first platform)

---

## Repository Transfer (Separate Task)

- [ ] **Transfer swflorida-comfort-hvac to MarceauSolutions org:**
  - Follow `REPO-TRANSFER-GUIDE.md`
  - Update local git remote
  - Verify website still accessible

---

## MCP Optimization Tasks (Per User Request)

Ralph will optimize these MCPs:

- [ ] **Apollo.io MCP** - Lead scraping and enrichment
- [ ] **LinkedIn MCP** - Social posting automation
- [ ] **ClickUp MCP** - CRM and task management
- [ ] **TikTok Automation** - Video posting workflow

---

## Next Steps Summary

**IMMEDIATE (This Week):**
1. Review and approve this roadmap
2. Sign up for Ayrshare
3. Create TikTok and Facebook accounts
4. Film 7 HVAC videos
5. Draft 15 LinkedIn posts
6. Set up Ayrshare integration
7. Start posting

**SHORT-TERM (Next 4 Weeks):**
8. Apply for LinkedIn Partner
9. Submit TikTok for audit
10. Monitor performance
11. Iterate based on analytics
12. Build official APIs in parallel

**LONG-TERM (Month 3+):**
13. Migrate to official APIs
14. Cancel Ayrshare (save $588/year)
15. Scale successful content
16. Hire video editor if needed

---

## Files Reference

| Document | Purpose |
|----------|---------|
| `PLATFORM-ANALYSIS-2026.md` | Platform comparison, audience analysis, account strategy |
| `LINKEDIN-MCP-IMPLEMENTATION.md` | LinkedIn API, MCP design, partner process |
| `TIKTOK-AUTOMATION-IMPLEMENTATION.md` | TikTok API, video workflow, audit process |
| `CROSS-PLATFORM-WORKFLOW.md` | Ayrshare integration, content repurposing |
| `SW-FLORIDA-HVAC-CAMPAIGN-STRATEGY.md` | HVAC content strategy (OUTDATED - use TikTok instead of X) |
| `REPO-TRANSFER-GUIDE.md` | GitHub repo transfer process |
| `IMPLEMENTATION-ROADMAP.md` | This file - master plan |

---

## Status: ✅ READY FOR APPROVAL

All strategic planning complete. Awaiting your approval to:
1. Sign up for Ayrshare
2. Create social media accounts
3. Start posting

**Expected Timeline:** Live posting in 7 days

**Expected ROI:** 602x-2,245x return on investment

Ready to proceed?
