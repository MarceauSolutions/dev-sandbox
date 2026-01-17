# Feature Docket: Items to Revisit

*Last Updated: 2026-01-16 (Trigger conditions refined)*

## How to Use This Document

This docket tracks deferred features, enhancements, and ideas that require future action. Each item has:
- **Trigger Condition**: When to revisit this item
- **Target Date**: Optional date for check-in
- **Dependencies**: What's blocking implementation

The morning digest (when implemented) will check trigger conditions and surface ready items.

---

## Active Docket Items

### 1. Sora 2 Video Generation

**Added:** 2026-01-15
**Status:** DEFERRED
**Priority:** P2 - Nice to Have

**Description:**
Use OpenAI Sora 2 for AI-generated video content instead of text-only posts. Could dramatically increase engagement with short, AI-generated fitness videos.

**Target Revisit Condition:**
When text-only engagement proves ROI (>2% engagement rate)

**Trigger Condition (ALL must be met):**
- [ ] 30+ posts published on X
- [ ] Average engagement rate calculated AND exceeds 2%
- **Auto-check:** `posts >= 30 AND avg_engagement > 0.02`

**Promo Codes Available:**
| Code | Status |
|------|--------|
| MOXMOX | Available |
| MCUBAN | Available |
| SKF9PM | Available |
| PAHR6X | Available |
| YHWR87 | Available |
| E7REQW | Available |
| ZBM1X4 | Available |
| A85AN6 | Available |

**Resources:**
- Framework: snubroot/Veo-3-Meta-Framework
- OpenAI Sora 2 Docs: https://openai.com/sora

**Implementation Notes:**
- Start with educational style videos (workout form, nutrition tips)
- Test engagement vs. filmed content
- Compare cost per engagement
- Consider hybrid: AI + human content mix
- Use promo codes to minimize initial cost

**Metrics to Track:**
- Cost per video generated
- Engagement rate vs. text posts
- Time saved vs. manual filming
- Promo code redemption (track which codes used)

---

### 1b. Arcads AI Video Ads

**Added:** 2026-01-16
**Status:** DEFERRED
**Priority:** P2 - Nice to Have

**Description:**
Use Arcads AI to generate UGC-style video ads with AI avatars. Creates realistic "talking head" videos without filming - AI actors can hold products, demonstrate apps, and speak in 35+ languages.

**Pricing:**
| Plan | Cost | Videos/Month | Per Video |
|------|------|--------------|-----------|
| Starter | $110/mo | 10 | ~$11 |
| Creator | $220/mo | 20 | ~$11 |
| Pro | Custom | Higher volume | API access |

**Comparison vs Alternatives:**
- Human UGC creator: $80-200 per video
- Arcads: ~$11 per video
- Sora 2: Free (promo codes) but less UGC-focused
- You filming: Free but time-intensive

**Trigger Condition:**
- [ ] 50+ posts published on X
- [ ] Video posts proven to 3x text engagement
- [ ] Monthly content budget exceeds $100
- [ ] Need to scale without personal filming time

**When to Choose Arcads vs Sora 2:**
- **Arcads**: UGC-style talking head ads, product demos, testimonial style
- **Sora 2**: Cinematic B-roll, creative visuals, artistic content

**API Access:**
- Only available on Pro tier (custom pricing)
- Rate limit: 40 requests/second max
- Could integrate with fitness_influencer MCP

**Implementation Notes:**
- Start with Starter plan ($110/mo) to test
- Create fitness tip videos with AI avatar
- Compare engagement: AI avatar vs text vs filmed
- If ROI positive, consider Pro tier for API

**Resources:**
- Website: https://arcads.ai
- API docs: Contact for custom pricing

---

### 2. X Premium Upgrade

**Added:** 2026-01-15
**Status:** DEFERRED
**Priority:** P3 - Low

**Description:**
Upgrade @MarceauWil56312 to X Premium for higher posting limits and visibility boost.

**Target Revisit Condition:**
When posting hits free tier limits consistently

**Current Limits (Free Tier):**
- 1,500 posts/month
- 50 posts/day
- 2-minute minimum gap

**Premium Benefits:**
- 3,000 posts/month
- 30% visibility boost
- Analytics access

**Trigger Condition (ANY triggers review):**
- [ ] Daily rate limit hit 3+ times in a single week
- [ ] Monthly limit at 80% (1,200+ posts used)
- **Auto-check:** `weekly_rate_limit_hits >= 3 OR monthly_posts >= 1200`

**Cost:** $100/month (for 3,000 posts)

**Decision Criteria:**
- Calculate ROI before upgrading
- Only upgrade if engagement proves model works
- Consider audience growth trajectory
- Compare: $100/month vs. value of additional 1,500 posts

**Resources:**
- X Premium: https://twitter.com/i/premium_sign_up

---

### 3. YouTube MCP Publishing

**Added:** 2026-01-15
**Updated:** 2026-01-15
**Built:** 2026-01-15
**Published:** 2026-01-15
**Status:** ✅ PUBLISHED
**Priority:** P1 - High

**Description:**
YouTube MCP for automated video uploads, Shorts publishing, and analytics.

**Target Revisit Condition:**
After building youtube_uploader.py with video pipeline working end-to-end

**Original Trigger Condition:**
- [x] youtube_uploader.py built and tested
- [x] Video pipeline working end-to-end
- [x] OAuth credentials configured

**Package Name:** `youtube-creator-mcp`
**Registry Name:** `io.github.wmarceau/youtube-creator`
**Location:** `projects/youtube-creator/`
**PyPI:** https://pypi.org/project/youtube-creator-mcp/1.0.0/

**Tools Implemented (11):**
- `upload_video` - Upload video with metadata and thumbnail
- `upload_short` - Upload YouTube Short (auto-adds #Shorts)
- `update_video_metadata` - Update title/description/tags
- `get_video_analytics` - Get views, likes, watch time, subscriber gain
- `get_channel_stats` - Subscriber count, total views, video count
- `schedule_video` - Schedule for future publication
- `add_to_playlist` - Add video to playlist
- `list_playlists` - List channel playlists
- `create_playlist` - Create new playlist
- `get_comments` - Retrieve video comments
- `reply_to_comment` - Post reply to comment

**Completion:**
- [x] v1.0.0 code complete
- [x] Published to PyPI: https://pypi.org/project/youtube-creator-mcp/1.0.0/
- [x] Published to MCP Registry: io.github.wmarceau/youtube-creator v1.0.0

**Resources:**
- YouTube Data API: https://developers.google.com/youtube/v3
- PyPI Package: https://pypi.org/project/youtube-creator-mcp/

---

### 4. Instagram Integration

**Added:** 2026-01-15
**Built:** 2026-01-15
**Status:** ✅ CODE COMPLETE - Awaiting Platform Validation
**Priority:** P2 - Medium

**Description:**
Instagram MCP for posting images, Reels, carousels, Stories, and analytics.

**Target Revisit Condition:**
After X proves engagement model works

**Trigger Condition (ALL must be met):**
- [ ] X engagement stable and consistently >2%
- [ ] YouTube Shorts performing (if applicable)
- [ ] Meta account access restored (currently blocked)
- **Auto-check:** `x_avg_engagement > 0.02 AND x_posts >= 50`

**Package Name:** `instagram-creator-mcp`
**Registry Name:** `io.github.wmarceau/instagram-creator`
**Location:** `projects/instagram-creator/`

**Tools Implemented (9):**
- `post_image` - Post single image to feed
- `post_carousel` - Post multi-image carousel (2-10 images)
- `post_reel` - Post video Reel
- `post_story` - Post to Stories
- `get_post_insights` - Impressions, reach, engagement
- `get_account_stats` - Followers, following, post count
- `get_recent_posts` - List recent posts
- `get_comments` - Get post comments
- `reply_to_comment` - Reply to comment

**To Publish - Just Need:**
1. Facebook Business account + Instagram Professional account
2. Meta Developer App with Instagram Graph API
3. Run: `cd projects/instagram-creator && python -m build && twine upload dist/*`
4. Run: `mcp-publisher publish --server server.json`

**Resources:**
- Meta Developer Portal: https://developers.facebook.com
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api

---

### 5. TikTok Integration

**Added:** 2026-01-15
**Built:** 2026-01-15
**Status:** ✅ CODE COMPLETE - Awaiting Platform Validation
**Priority:** P2 - Medium

**Description:**
TikTok MCP for posting videos, analytics, and comment management.

**Target Revisit Condition:**
After X proves engagement model (same triggers as Instagram)

**Trigger Condition (ALL must be met):**
- [ ] X engagement stable and consistently >2%
- [ ] YouTube Shorts performing (if applicable)
- [ ] TikTok OAuth flow working (currently has PKCE issues)
- **Auto-check:** `x_avg_engagement > 0.02 AND x_posts >= 50`

**Package Name:** `tiktok-creator-mcp`
**Registry Name:** `io.github.wmarceau/tiktok-creator`
**Location:** `projects/tiktok-creator/`

**Tools Implemented (7):**
- `post_video` - Upload video from local file
- `post_video_from_url` - Upload video from public URL
- `get_video_stats` - Views, likes, comments, shares
- `get_account_stats` - Followers, likes, video count
- `get_video_list` - List your TikTok videos
- `get_comments` - Get video comments
- `reply_to_comment` - Reply to comment

**To Publish - Just Need:**
1. TikTok Developer Account: https://developers.tiktok.com
2. App with Content Posting API access
3. Run: `cd projects/tiktok-creator && python -m build && twine upload dist/*`
4. Run: `mcp-publisher publish --server server.json`

**Resources:**
- TikTok Developer Portal: https://developers.tiktok.com
- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started

---

### 6. Fitness Influencer v1.3.0 PyPI Push

**Added:** 2026-01-15
**Completed:** 2026-01-15
**Status:** ✅ COMPLETED
**Priority:** P0 - Critical

**Description:**
Push fitness-influencer MCP v1.3.0 to PyPI and MCP Registry. Currently at v1.2.0 on PyPI but v1.3.0 in dev.

**New Features in v1.3.0:**
- Video Blueprint Generator
- COGS Tracker
- Updated imports for MoviePy 2.x compatibility

**Completion:**
- [x] v1.3.0 code complete
- [x] Education scenarios tested
- [x] Published to PyPI: https://pypi.org/project/fitness-influencer-mcp/1.3.0/
- [x] Published to MCP Registry: io.github.wmarceau/fitness-influencer v1.3.0

---

### 7. OpenRouter Directory Registration

**Added:** 2026-01-15
**Updated:** 2026-01-15
**Status:** ⏳ READY TO SUBMIT
**Priority:** P2 - Medium

**Description:**
Register all published MCPs on OpenRouter directories to expand reach.

**MCPs Ready for Registration (all on PyPI + MCP Registry):**
| MCP | PyPI | Registry |
|-----|------|----------|
| md-to-pdf | ✅ 1.0.1 | ✅ io.github.wmarceau/md-to-pdf |
| amazon-seller | ✅ 1.0.0 | ✅ io.github.wmarceau/amazon-seller |
| fitness-influencer | ✅ 1.3.0 | ✅ io.github.wmarceau/fitness-influencer |
| rideshare-comparison | ✅ 1.0.0 | ✅ io.github.wmarceau/rideshare-comparison |
| hvac-quotes | ✅ 1.0.0 | ✅ io.github.wmarceau/hvac-quotes |

**Directories (require manual web form submission):**
1. **PulseMCP** (https://pulsemcp.com/submit) - Auto-ingests from MCP Registry weekly
2. **Glama** (https://glama.ai/mcp/servers) - Click "Add Server" button
3. **MCP Market** (https://mcpmarket.com) - Check for submission form

**Submission Workflow:** `workflows/openrouter-registration.md`

**Next Action:** Submit GitHub URLs via web forms (see workflow for URLs)

---

### 8. Lead Scraper API Keys

**Added:** 2026-01-15
**Updated:** 2026-01-15
**Status:** ✅ OPERATIONAL
**Priority:** P2 - Medium

**Description:**
Lead scraper is fully built and operational using Google Places API.

**Current Status:**
- [x] Google Places API: WORKING (primary source)
- [x] Lead scraper functional: 98 leads generated as of 2026-01-15
- [ ] Yelp API: OPTIONAL (not needed, Google Places sufficient)
- [ ] Apollo.io: OPTIONAL (for enrichment, not scraping)

**Lead Scraper Location:** `projects/lead-scraper/`
**Output:** `projects/lead-scraper/output/lead_records.json` (98 leads)

---

### 9. MCP Aggregator Platform Testing

**Added:** 2026-01-15
**Status:** PENDING
**Priority:** P2 - Medium

**Description:**
Complete integration testing for the refactored MCP aggregator platform.

**Tasks:**
- [ ] Integrate refactored platform core
- [ ] Test HVAC service registration
- [ ] Deploy aggregator_mcp.py
- [ ] Run integration tests (all connectivity types)

**Trigger Condition:**
- [ ] Lead scraper API keys obtained
- [ ] Core refactoring complete

---

### 10. Project Scoping Calculator

**Added:** 2026-01-15
**Status:** PENDING REVIEW
**Priority:** P3 - Low

**Description:**
Tool for calculating project scope and effort estimates.

**Decision Date:** 2026-01-17

**Trigger Condition:**
- [ ] Market viability analysis complete (SOP 17)
- [ ] Decision made on whether to build

---

### 15. Claude Development Framework - Paid Tier Packaging

**Added:** 2026-01-16
**Status:** BLOCKED - AWAITING VALIDATION
**Priority:** P1 - High

**Description:**
Package the Claude.md system with all 17 SOPs as a sellable product. Market analysis complete (3.875/5 CONDITIONAL GO). Free tier packaged. Need validation before investing in paid tiers.

**Market Analysis Results:**
- Market Size: 3.5/5 (TAM $5.2B, SOM Y1 $25K-$150K)
- Competition: 4.0/5 (No direct competitor, Nick Saraev created awareness)
- Customer Pain: 4.0/5 (Solo devs, 7/10 pain level)
- Monetization: 4.0/5 (LTV:CAC 6.6:1, break-even 97 customers)

**Planned Tiers:**
| Tier | Price | Status |
|------|-------|--------|
| Free | $0 | ✅ PACKAGED |
| Starter | $47 | ⏳ Blocked |
| Pro | $97 | ⏳ Blocked |
| Course | $297 | ⏳ Blocked |

**Trigger Condition (ALL must be met):**
- [ ] Email list reaches 500+ subscribers
- [ ] 5-10 beta testers recruited and using framework
- [ ] 3-5 testimonials collected
- [ ] Demo video created showing ROI
- **Auto-check:** `email_subscribers >= 500 AND beta_testers >= 5 AND testimonials >= 3`

**Validation Actions Required:**
1. Create landing page with email capture
2. Release free tier (GitHub/Gumroad)
3. Promote: X, Reddit (r/ClaudeAI), Indie Hackers
4. Track metrics: signups, downloads, engagement

**Location:** `projects/claude-framework/`

**Files Created:**
- `market-analysis/consolidated/VIABILITY-SCORECARD.md`
- `market-analysis/consolidated/GO-NO-GO-DECISION.md`
- `tiers/free/CLAUDE.md` (template)
- `tiers/free/SOP-01-PROJECT-INIT.md`
- `tiers/free/SOP-03-DEPLOYMENT.md`
- `tiers/free/SOP-05-SESSION-DOCS.md`
- `tiers/free/CLAUDE-QUICKSTART.md`
- `tiers/free/QUICK-REFERENCE.md`

**Resources:**
- Full analysis: `projects/claude-framework/market-analysis/`
- Nick Saraev (concept originator): YouTube @nicksaraev

---

### 11. Video Creation with Talking Head

**Added:** 2026-01-15
**Status:** DEFERRED
**Priority:** P2 - Medium

**Description:**
Create professional videos with AI-generated educational infographics and a talking head overlay in the corner. Useful for YouTube content, demos, and social media videos.

**Current Capability:**
- AI image generation via Grok: WORKING ($0.07/image)
- Video creation via Shotstack: PARTIAL (transition bug needs fix)
- Talking head overlay: NOT IMPLEMENTED

**Implementation Approach:**
1. **Option A: Shotstack + Overlay** - Use Shotstack's compositor to overlay talking head video on infographic slideshow
2. **Option B: MoviePy** - Use local MoviePy processing to composite videos
3. **Option C: Creatomate** - Use Creatomate templates with talking head slot

**Shotstack Issue to Fix:**
- Error: `transition.in` and `transition.out` cannot be `None` (Python null)
- Fix: Omit transition key entirely OR use string "none" instead of Python `None`

**Trigger Condition:**
- [ ] YouTube upload workflow tested and working
- [ ] At least 5 posts published that would benefit from video format
- [ ] Talking head footage recorded (requires filming setup)

**Resources:**
- Shotstack API docs: https://shotstack.io/docs/api/
- Generated test images (2026-01-15):
  - Workout splits infographic
  - Calorie deficit concept
  - Protein intake guide
  - Progressive overload tips

**Cost Estimate:**
- AI images: ~$0.07/image (Grok)
- Video render: ~$0.27/video (Shotstack)
- Total per video: ~$0.50-1.00

---

### 12. TikTok OAuth Setup

**Added:** 2026-01-15
**Status:** BLOCKED
**Priority:** P3 - Low

**Description:**
Complete TikTok OAuth flow to get access tokens for the TikTok Creator MCP.

**Blocker:**
OAuth flow had issues with PKCE code challenge. Sandbox mode requires further testing.

**Credentials (in .env):**
- Client Key: awztj4k9iysxawwy
- Client Secret: (in .env)

**Trigger Condition:**
- [ ] X automation stable and posting consistently
- [ ] YouTube automation working
- [ ] Desire to expand to TikTok platform

**Script Location:** `projects/tiktok-creator/get_credentials.py`

---

### 13. Instagram/Meta Setup

**Added:** 2026-01-15
**Status:** BLOCKED
**Priority:** P3 - Low

**Description:**
Complete Meta/Instagram setup for Instagram Creator MCP.

**Blocker:**
Meta device verification blocked access. Need to resolve account security issue.

**Trigger Condition:**
- [ ] Meta account access restored
- [ ] X and YouTube automation stable

---

### 14. Submit HVAC-Quotes MCP to MCP.so

**Added:** 2026-01-16
**Status:** PENDING
**Priority:** P3 - Low

**Description:**
Submit hvac-quotes-mcp to MCP.so directory. Rate limited during batch submission.

**Target Date:** 2026-01-17

**Submission Details:**
```
Title: Add hvac-quotes-mcp

GitHub: https://github.com/wmarceau/hvac-quotes-mcp
PyPI: hvac-quotes-mcp
Description: HVAC equipment RFQ management - submit quotes, track responses, compare pricing.
```

**URL:** https://github.com/chatmcp/mcpso/issues/new

**Trigger Condition:**
- [ ] 24 hours passed since rate limit (2026-01-16)

**Note:** Other MCPs (amazon-seller, fitness-influencer, rideshare-comparison) already in MCP.so queue via auto-ingestion.

---

## Completed Items

(Move items here when done)

---

## Docket Check Logic

```python
def check_docket():
    """Check deferred features for trigger conditions."""
    alerts = []

    # Get current metrics
    posts = get_post_count()
    engagement = get_avg_engagement()
    monthly_posts = get_monthly_post_count()
    weekly_rate_limit_hits = get_weekly_rate_limit_hits()

    # 1. Check Sora 2 trigger (30+ posts AND >2% engagement)
    if posts >= 30 and engagement >= 0.02:
        alerts.append("🟢 Sora 2: READY FOR IMPLEMENTATION")
        alerts.append(f"   Posts: {posts}, Engagement: {engagement:.1%}")
        alerts.append("   Promo codes available: MOXMOX, MCUBAN, SKF9PM, PAHR6X, YHWR87, E7REQW, ZBM1X4, A85AN6")

    # 2. Check X Premium trigger (rate limits OR 80% monthly)
    if weekly_rate_limit_hits >= 3:
        alerts.append("🟢 X Premium: Rate limit hit 3+ times this week")
        alerts.append("   Cost: $100/month for 3,000 posts")
    elif monthly_posts >= 1200:
        alerts.append("🟢 X Premium: At 80% monthly limit")
        alerts.append(f"   Posts: {monthly_posts}/1,500 - Consider upgrade")

    # 3. Check Instagram/TikTok triggers (X proves engagement model)
    if posts >= 50 and engagement >= 0.02:
        alerts.append("🟢 Instagram: X engagement validated - ready to expand")
        alerts.append("🟢 TikTok: X engagement validated - ready to expand")
        alerts.append(f"   X Posts: {posts}, Engagement: {engagement:.1%}")

    # 4. Check PyPI version mismatches
    dev_version = get_dev_version('fitness-influencer')
    pypi_version = get_pypi_version('fitness-influencer-mcp')
    if dev_version != pypi_version:
        alerts.append(f"🟢 fitness-influencer: Push {dev_version} to PyPI (current: {pypi_version})")

    return alerts


def get_trigger_summary():
    """Return summary of all trigger conditions and current status."""
    return {
        "sora_2": {
            "condition": "posts >= 30 AND engagement > 2%",
            "current": f"posts={get_post_count()}, engagement={get_avg_engagement():.1%}",
            "met": get_post_count() >= 30 and get_avg_engagement() >= 0.02
        },
        "x_premium": {
            "condition": "rate_limit_hits >= 3/week OR monthly_posts >= 1200",
            "current": f"hits={get_weekly_rate_limit_hits()}, posts={get_monthly_post_count()}",
            "met": get_weekly_rate_limit_hits() >= 3 or get_monthly_post_count() >= 1200
        },
        "instagram": {
            "condition": "x_posts >= 50 AND x_engagement > 2%",
            "current": f"posts={get_post_count()}, engagement={get_avg_engagement():.1%}",
            "met": get_post_count() >= 50 and get_avg_engagement() >= 0.02
        },
        "tiktok": {
            "condition": "x_posts >= 50 AND x_engagement > 2%",
            "current": f"posts={get_post_count()}, engagement={get_avg_engagement():.1%}",
            "met": get_post_count() >= 50 and get_avg_engagement() >= 0.02
        }
    }
```

---

## Adding New Items

When adding a new item to the docket:

1. **Set clear trigger condition** - What metrics/events signal readiness?
2. **Add dependencies** - What must exist before implementing?
3. **Set priority** - P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
4. **Add target date** if time-bound
5. **Include implementation notes** for future reference

---

## References

- [X Campaign SOP](workflows/x-campaign-sop.md)
- [MCP Publishing SOPs](../CLAUDE.md#sop-11-mcp-package-structure)
- [Content Strategy Plan](templates/content_strategy.json)
