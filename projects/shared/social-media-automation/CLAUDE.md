# Social Media Automation

## What This Does
Multi-platform social media posting and content automation. Supports X (Twitter), YouTube, TikTok, Facebook, and LinkedIn. Follows Nick Saraev's content repurposing strategy: create long-form content once, then distribute optimized versions across all platforms. Manages multiple business accounts via `config/businesses.json`.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# Check platform API status
python -m src.multi_platform_manager status

# Post to X
python -m src.x_api post "Your tweet text here"
python -m src.x_scheduler schedule --content "Post text" --time "2026-02-10 09:00"

# Repurpose long-form video to all platforms
python -m src.multi_platform_manager repurpose --video path/to/video.mp4

# Generate weekly content calendar
python -m src.multi_platform_manager calendar --week

# Generate content
python -m src.content_generator generate --topic "peptide research" --platform x
python -m src.peptide_content_generator generate --topic "BPC-157"

# Business-specific content
python -m src.business_content_generator generate --business "sw-florida-comfort"
python -m src.business_scheduler schedule --business "sw-florida-comfort"

# Check post analytics
python -m src.post_analytics report
python -m src.engagement_tracker summary
```

## Architecture
- **`src/x_api.py`** - X/Twitter API wrapper with rate limiting (Premium tier: 25K posts/month)
- **`src/x_scheduler.py`** - X post scheduling with queue management
- **`src/youtube_uploader.py`** - YouTube video uploads
- **`src/tiktok_api.py`** + **`src/tiktok_auth.py`** - TikTok API integration
- **`src/multi_platform_manager.py`** - Central hub for cross-platform distribution
- **`src/content_generator.py`** - AI-powered content creation
- **`src/peptide_content_generator.py`** - Fitness/peptide niche content
- **`src/business_content_generator.py`** - Multi-business content (HVAC, fitness, etc.)
- **`src/script_generator.py`** - Video script generation
- **`src/post_analytics.py`** + **`src/engagement_tracker.py`** - Performance tracking
- **`src/link_manager.py`** - UTM tracking and link management
- **`src/time_context.py`** - Time-aware content scheduling
- **`config/businesses.json`** - Multi-business account configuration
- **`DOCKET.md`** - Deferred features with trigger conditions (Sora 2, etc.)

## Project-Specific Rules
- X API requires Premium tier ($8/month) for posting automation
- API keys needed: `X_API_KEY`, `X_ACCESS_TOKEN`, `X_BEARER_TOKEN`, `YOUTUBE_*`, `TIKTOK_*`
- Multi-business support: each business has its own config in `businesses.json`
- Content repurposing pipeline: Long-form -> YouTube -> Clips -> TikTok/IG/X
- Check `DOCKET.md` for deferred features and their trigger conditions
- Facebook requires permanent page access token (see `QUICK-START.md` for setup)
- LinkedIn company page requires separate setup (see `LINKEDIN-COMPANY-SETUP.md`)

## Relevant SOPs
- SOP 30: n8n Workflow Management (some posting automation moved to n8n)
- `workflows/x-campaign-sop.md` - X/Twitter campaign execution
- `workflows/multi-business-automation.md` - Multi-tenant posting workflows
- `workflows/post-performance-tracking.md` - Analytics and optimization
- `DOCKET.md` - Deferred features with trigger conditions
