# Cross-Platform Social Media Workflow
**Date:** January 20, 2026
**Purpose:** Unified posting workflow across LinkedIn, X, TikTok, and Facebook

---

## Executive Summary

**Goal:** Create once, post everywhere with platform-specific optimization

**Platforms:**
- **Marceau Solutions (AI):** LinkedIn (primary) + X (secondary)
- **SW Florida Comfort (HVAC):** TikTok (primary) + Facebook (secondary)

**Recommended Tool:** [Ayrshare](https://www.ayrshare.com) - $49/month for ALL platforms

---

## Part 1: Ayrshare - Unified Multi-Platform Solution

### Why Ayrshare Wins

**One API for All Platforms:**
- ✅ LinkedIn (no partner approval wait)
- ✅ X/Twitter (instant access)
- ✅ TikTok (no audit wait, public posts immediately)
- ✅ Facebook (instant access)
- ✅ Instagram (bonus)
- ✅ YouTube (bonus)

**Cost:** $49/month vs building 4 separate integrations

**Time Savings:**
- Official APIs: 4-5 weeks (LinkedIn partner + TikTok audit)
- Ayrshare: 1 day

### Ayrshare Implementation

**Setup:**

```python
# config/ayrshare_config.py

AYRSHARE_CONFIG = {
    "api_key": os.getenv("AYRSHARE_API_KEY"),
    "base_url": "https://app.ayrshare.com/api"
}

# Business-to-platform mapping
BUSINESS_PLATFORMS = {
    "marceau-solutions": ["linkedin", "twitter"],  # AI automation
    "swflorida-hvac": ["tiktok", "facebook"]      # HVAC
}
```

**Unified Posting API:**

```python
# src/ayrshare_api.py

import requests

class AyrshareAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://app.ayrshare.com/api"

    def post_to_platforms(self, text, platforms, media_urls=None, schedule_time=None):
        """Post to multiple platforms at once.

        Args:
            text: Post content
            platforms: List of ["linkedin", "twitter", "tiktok", "facebook"]
            media_urls: List of public URLs to images/videos
            schedule_time: ISO timestamp for scheduled post
        """
        payload = {
            "post": text,
            "platforms": platforms
        }

        if media_urls:
            payload["mediaUrls"] = media_urls

        if schedule_time:
            payload["scheduleDate"] = schedule_time

        response = requests.post(
            f"{self.base_url}/post",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )

        return response.json()
```

**Example Usage:**

```python
# Post to LinkedIn + X simultaneously
ayr = AyrshareAPI(api_key=os.getenv("AYRSHARE_API_KEY"))

ayr.post_to_platforms(
    text="Just automated 47 hours/week for a Naples gym using Voice AI. Here's the tech stack we used...",
    platforms=["linkedin", "twitter"],
    media_urls=["https://cdn.example.com/case-study-infographic.png"]
)

# Result: Posted to both platforms at once
```

---

## Part 2: Content Strategy by Platform

### Content Repurposing Matrix

| Original Content | LinkedIn Version | X Version | TikTok Version | Facebook Version |
|-----------------|------------------|-----------|----------------|------------------|
| **HVAC Case Study** | N/A | N/A | 60s video walkthrough | Before/after photos + text |
| **HVAC Tip** | N/A | N/A | 15s quick tip video | Carousel post with images |
| **AI Case Study** | Long-form (1,000 chars) | Thread (8 tweets) | N/A | N/A |
| **AI Tech Insight** | 500-word article | 280-char summary | N/A | N/A |
| **Behind-the-Scenes** | Professional update | Casual share | Short video clip | Photo + story |

### Platform-Specific Optimization

**LinkedIn:**
- Long-form (500-3,000 characters)
- Professional tone
- Data/metrics heavy
- Hashtags: 3-5 max (#AI #Automation #SmallBusiness)

**X (Twitter):**
- Short (280 characters)
- Casual/conversational
- Thread for longer content
- Hashtags: 2-3 max (#VoiceAI #TechTwitter)

**TikTok:**
- Video only (15-60 seconds)
- Entertainment first, education second
- Captions required (80% watch without sound)
- Hashtags: 5-8 (#ACRepair #HVAC #Naples #FloridaHeat)

**Facebook:**
- Mixed (text, images, videos)
- Community-focused
- Local targeting (zip codes)
- Hashtags: Optional (less important than other platforms)

---

## Part 3: Cross-Platform Posting Workflow

### Workflow 1: AI Content (LinkedIn + X)

**Original Content (LinkedIn):**

```
Just completed our 3rd Voice AI POC - this time for a Naples fitness center.

Results (Week 1):
• 127 calls answered automatically
• 34 class bookings (vs 12 previous week)
• 0 missed calls
• Owner saved 15 hours

The tech stack:
- Anthropic Claude for conversation
- Twilio for phone integration
- Custom training on gym schedule/pricing
- Real-time calendar sync

B2B automation isn't coming - it's here.

If you're manually handling repetitive customer calls, let's talk.

#AI #Automation #SmallBusiness #VoiceAI #B2B
```

**Adapted for X (Thread):**

```
1/ Just completed our 3rd Voice AI POC

This time: Naples fitness center

Results in Week 1 were wild 👇

2/ 📞 127 calls answered automatically
📅 34 class bookings (vs 12 prev week)
✅ 0 missed calls
⏰ Owner saved 15 hours

That's a 2.8x booking increase. Same owner, same gym. Just better phone answering.

3/ Tech stack:

- @AnthropicAI Claude (conversation)
- @twilio (phone)
- Custom training (gym-specific)
- Real-time calendar sync

All running 24/7, no humans needed.

4/ B2B automation isn't coming.

It's already here.

If you're manually handling repetitive customer calls, you're leaving money on the table.

DM me if you want to see how this works 👋

#VoiceAI #Automation
```

**Code Implementation:**

```python
# src/cross_platform_poster.py

class CrossPlatformPoster:
    def __init__(self):
        self.ayr = AyrshareAPI(api_key=os.getenv("AYRSHARE_API_KEY"))

    def post_ai_case_study(self, case_study_data):
        """Post AI case study to LinkedIn + X."""

        # LinkedIn version (long-form)
        linkedin_post = self._format_linkedin_case_study(case_study_data)

        # X version (thread)
        x_thread = self._format_x_thread(case_study_data)

        # Post to LinkedIn
        self.ayr.post_to_platforms(
            text=linkedin_post,
            platforms=["linkedin"],
            media_urls=[case_study_data.get("image_url")]
        )

        # Post thread to X (Ayrshare handles threading automatically)
        self.ayr.post_to_platforms(
            text=x_thread,
            platforms=["twitter"]
        )

    def _format_linkedin_case_study(self, data):
        """Format as long-form LinkedIn post."""
        return f"""Just completed our {data['number']} Voice AI POC - this time for a {data['business_type']}.

Results (Week 1):
• {data['calls_answered']} calls answered automatically
• {data['bookings']} class bookings (vs {data['prev_bookings']} previous week)
• 0 missed calls
• Owner saved {data['hours_saved']} hours

The tech stack:
{data['tech_stack']}

B2B automation isn't coming - it's here.

If you're manually handling repetitive customer calls, let's talk.

#AI #Automation #SmallBusiness #VoiceAI #B2B
"""

    def _format_x_thread(self, data):
        """Format as X thread."""
        return f"""1/ Just completed our {data['number']} Voice AI POC

This time: {data['business_type']}

Results in Week 1 were wild 👇

2/ 📞 {data['calls_answered']} calls answered automatically
📅 {data['bookings']} bookings (vs {data['prev_bookings']} prev week)
✅ 0 missed calls
⏰ Owner saved {data['hours_saved']} hours

That's a {data['increase_multiplier']}x increase.

3/ Tech stack:

{data['tech_stack_short']}

All running 24/7, no humans needed.

4/ B2B automation isn't coming.

It's already here.

If you're manually handling repetitive customer calls, you're leaving money on the table.

DM me if you want to see how this works 👋

#VoiceAI #Automation
"""
```

### Workflow 2: HVAC Content (TikTok + Facebook)

**Original Content (TikTok Video):**

**Video:** 45-second clip of technician finding issue in AC unit

**Caption:**
```
Here's what I found in this AC unit 😱

Customer said "AC not cooling" - this is why 👇

Dirty filter was blocking 80% of airflow = system working overtime = high electric bills

Quick fix: $89 filter replacement
Prevented: $2,500 compressor failure

Don't skip your AC maintenance!

Call us for tune-up: (239) 766-6129

#ACRepair #HVAC #Naples #FloridaHeat #HVACTips #SWFlorida
```

**Adapted for Facebook:**

**Format:** Video (same as TikTok) + Photo carousel + longer text

```
Found the problem! 🔧

One of our Naples customers called saying their AC wasn't cooling. Here's what we found:

The air filter was so clogged it was blocking 80% of airflow. The system was working overtime trying to cool the house, driving up electric bills and putting massive strain on the compressor.

Quick fix:
• $89 filter replacement
• 15 minutes of work
• System running perfectly again

What we prevented:
• $2,500 compressor failure
• Emergency breakdown during heat wave
• Days without AC

Pro tip: Change your filter every 1-3 months in Florida. Our humid climate clogs filters faster than anywhere else in the country.

Need an AC tune-up before summer? We're booking appointments now: (239) 766-6129

Serving Naples, Fort Myers, and Cape Coral with same-day service.

#NaplesFL #HVAC #ACRepair #LocalBusiness
```

**Code Implementation:**

```python
def post_hvac_content(self, video_path, caption_short, caption_long):
    """Post HVAC content to TikTok + Facebook."""

    # Upload video to CDN (Ayrshare requires public URL)
    video_url = self._upload_to_cdn(video_path)

    # Post to TikTok (short caption)
    self.ayr.post_to_platforms(
        text=caption_short,
        platforms=["tiktok"],
        media_urls=[video_url]
    )

    # Post to Facebook (long caption)
    self.ayr.post_to_platforms(
        text=caption_long,
        platforms=["facebook"],
        media_urls=[video_url]
    )
```

---

## Part 4: Automated Cross-Platform Scheduler

### Unified Scheduler Architecture

```python
# src/unified_scheduler.py

from src.cross_platform_poster import CrossPlatformPoster
from src.business_content_generator import BusinessContentGenerator

class UnifiedScheduler:
    def __init__(self):
        self.poster = CrossPlatformPoster()
        self.content_gen = BusinessContentGenerator()

    def schedule_ai_content_week(self):
        """Schedule week of AI content for LinkedIn + X."""

        # Generate 4 posts for the week (LinkedIn strategy: 3-5/week)
        for i in range(4):
            # Generate content
            post = self.content_gen.generate_post(
                business_id="marceau-solutions",
                template_type="case_study_update",
                campaign="linkedin-thought-leadership"
            )

            # Post to LinkedIn + X
            self.poster.post_ai_case_study({
                "number": "3rd",
                "business_type": "Naples fitness center",
                "calls_answered": 127,
                # ... more data
            })

    def schedule_hvac_content_week(self):
        """Schedule week of HVAC content for TikTok + Facebook."""

        # Get next 14 videos from queue (2/day × 7 days)
        videos = self._get_video_queue(count=14)

        for video in videos:
            # Post to TikTok + Facebook
            self.poster.post_hvac_content(
                video_path=video["path"],
                caption_short=video["caption_tiktok"],
                caption_long=video["caption_facebook"]
            )
```

### Posting Schedule (Combined)

**Daily Schedule:**

| Time | Marceau Solutions (AI) | SW Florida Comfort (HVAC) |
|------|------------------------|---------------------------|
| 7 AM | - | TikTok video #1 |
| 10 AM | LinkedIn post (Tue/Wed/Thu only) | Facebook post |
| 12 PM | X thread | TikTok video #2 |
| 5 PM | - | - |
| 7 PM | X post | TikTok video #3 |
| 9 PM | X post | Facebook tip |

**Weekly Totals:**
- LinkedIn: 3-4 posts/week (Tue/Wed/Thu)
- X: 20-30 posts/day (140-210/week)
- TikTok: 14-21 videos/week (2-3/day)
- Facebook: 7-14 posts/week (1-2/day)

---

## Part 5: Content Creation Workflow

### AI Content Creation (LinkedIn + X)

**Process:**

1. **Source Material:**
   - POC results (Voice AI metrics)
   - Tech insights (development learnings)
   - Industry trends (AI adoption news)

2. **Create LinkedIn Post:**
   - Write long-form (500-1,000 words)
   - Include data/metrics
   - Professional tone
   - Add infographic (optional)

3. **Adapt to X Thread:**
   - Break into 4-8 tweets
   - Add hooks ("👇", "Here's why")
   - Casual tone
   - Tag relevant accounts (@AnthropicAI, @twilio)

4. **Schedule:**
   - LinkedIn: Tuesday 10 AM
   - X: Same day, 12 PM (thread)

**Time:** 30 minutes per post set

### HVAC Content Creation (TikTok + Facebook)

**Process:**

1. **Film Raw Footage:**
   - On-site AC repairs, installs, tips
   - 1-2 minutes raw footage
   - Vertical (9:16) for TikTok

2. **Edit Video:**
   - Cut to 45-60 seconds
   - Add text overlays (hook in first 3 seconds)
   - Add captions (for sound-off viewing)
   - Add background music (CapCut library)

3. **Create Captions:**
   - TikTok: Short (150 characters), 5-8 hashtags
   - Facebook: Long (300-500 characters), local hashtags

4. **Upload to CDN:**
   - S3, Cloudflare, or Ayrshare hosting
   - Get public URL

5. **Schedule:**
   - TikTok: 7 AM, 12 PM, 7 PM
   - Facebook: 10 AM, 9 PM

**Time:** 1 hour per video (or batch 7 videos in 3 hours)

---

## Part 6: Implementation Steps

### Step-by-Step Setup

**1. Sign Up for Ayrshare**

```bash
# Visit: https://www.ayrshare.com
# Choose plan: $49/month (all platforms)
# Get API key from dashboard
# Add to .env:
echo "AYRSHARE_API_KEY=your_key_here" >> .env
```

**2. Connect Accounts**

In Ayrshare dashboard:
- Connect William Marceau LinkedIn (for AI content)
- Connect @wmarceau X account (for AI content)
- Connect @SWFloridaComfortAC TikTok (for HVAC content)
- Connect SW Florida Comfort Facebook page (for HVAC content)

**3. Install Ayrshare Python SDK**

```bash
pip install ayrshare
```

**4. Test Posting**

```python
# Test LinkedIn post
from src.ayrshare_api import AyrshareAPI

ayr = AyrshareAPI(api_key=os.getenv("AYRSHARE_API_KEY"))

result = ayr.post_to_platforms(
    text="Test post from Marceau Solutions automation system",
    platforms=["linkedin"]
)

print(result)  # Should return success
```

**5. Set Up Automated Posting**

```bash
# Add to crontab

# AI content (LinkedIn + X)
0 10 * * 2,3,4 cd /path && python -m src.unified_scheduler schedule_ai_content >> logs/ai_posts.log 2>&1

# HVAC content (TikTok + Facebook)
0 7,12,19 * * * cd /path && python -m src.unified_scheduler schedule_hvac_content >> logs/hvac_posts.log 2>&1
```

---

## Part 7: Cost Analysis

### Option A: Ayrshare (All-in-One)

**Cost:** $49/month

**Covers:**
- LinkedIn (no partner wait)
- X (instant)
- TikTok (no audit wait, public posts)
- Facebook (instant)
- Instagram (bonus)
- YouTube (bonus)

**Pros:**
- ✅ One integration for all platforms
- ✅ No approval delays
- ✅ Public posts immediately
- ✅ Analytics dashboard included
- ✅ Less development time

**Cons:**
- ❌ Ongoing cost ($588/year)

### Option B: Official APIs (Build Each)

**Cost:** $0/month (after approvals)

**Development Time:**
- LinkedIn: 2-4 weeks (partner approval)
- X: 1 week (instant access)
- TikTok: 4-5 weeks (audit approval)
- Facebook: 1 week (instant access)
- **Total:** 8-10 weeks

**Pros:**
- ✅ Free forever
- ✅ Full control
- ✅ No third-party dependency

**Cons:**
- ❌ 8-10 weeks to fully operational
- ❌ Separate codebase for each platform
- ❌ More maintenance

### Recommendation: Hybrid

**Month 1-2: Ayrshare**
- Start posting immediately
- Build audience while developing official APIs
- Cost: $98

**Month 3+: Official APIs**
- Migrate to official APIs after approvals
- Cancel Ayrshare
- Cost: $0

**Total Investment:** $98 to get 2 months head start

---

## Summary

**Cross-Platform Posting Made Simple:**

1. ✅ **Use Ayrshare** ($49/month for all platforms)
2. ✅ **Create content once**, post everywhere
3. ✅ **Platform-specific optimization** (long LinkedIn, short X, video TikTok)
4. ✅ **Automated scheduling** (cron jobs)
5. ✅ **Track analytics** (Ayrshare dashboard)

**Expected Results:**

| Platform | Frequency | Monthly Reach | Monthly Leads | Revenue/Month |
|----------|-----------|---------------|---------------|---------------|
| LinkedIn | 12-20 posts | 10K-50K | 1-3 | $10K-$30K |
| X | 600-900 posts | 50K-500K | 3-10 | $15K-$50K |
| TikTok | 60-90 videos | 50K-500K | 10-20 | $3K-$20K |
| Facebook | 30-60 posts | 5K-20K | 5-10 | $1.5K-$10K |
| **TOTAL** | - | 115K-1.07M | 19-43 | $29.5K-$110K |

**ROI:** 602x-2,245x ($49 spend → $29.5K-$110K revenue)

Ready to set up Ayrshare and start cross-platform posting?
