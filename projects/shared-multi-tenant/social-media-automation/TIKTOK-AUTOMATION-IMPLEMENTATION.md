# TikTok Automation Implementation Guide
**Date:** January 20, 2026
**Purpose:** Automate TikTok posting for SW Florida Comfort HVAC

---

## Executive Summary

**Goal:** Automate video posting to TikTok for HVAC content (2-3 videos/day)

**TikTok API Status:** ✅ Official Content Posting API exists
**Feasibility:** ⚠️ MEDIUM - Requires business account + API audit approval
**Timeline:** 3-4 weeks (including audit)
**Cost:** Free (TikTok Business API) + video creation time

**CRITICAL:** All content posted by unaudited clients will be PRIVATE until audit approval.

---

## Part 1: TikTok API Research Findings

### Official TikTok Content Posting API

**Primary API:** [TikTok Content Posting API](https://developers.tiktok.com/products/content-posting-api/)

**What TikTok API Can Do:**
- ✅ Upload videos (MP4, MOV, WebM)
- ✅ Upload photos (carousel posts)
- ✅ Post directly or save as draft
- ✅ Schedule posts (via API)
- ✅ Add captions, hashtags, mentions
- ✅ Set privacy settings
- ✅ Upload to multiple accounts

**What TikTok API CANNOT Do:**
- ❌ Generate video content (you must create videos first)
- ❌ Edit videos (must be edited before upload)
- ❌ Add TikTok effects/filters (must be pre-produced)

**Authentication:** OAuth 2.0

**Rate Limits:**
- Video uploads: Generous (specific limits not published)
- Generally sufficient for 2-3 videos/day

### Critical Requirements

**1. TikTok Business Account (REQUIRED)**

Standard personal accounts CANNOT use the API. Must convert to Business Account:

**How to Convert:**
1. Open TikTok app
2. Go to Profile → Menu (☰) → Settings and Privacy
3. Tap "Account" → "Switch to Business Account"
4. Select category: "Home & Garden" or "Professional Services"
5. Complete business profile

**2. API Audit (REQUIRED for Public Posts)**

⚠️ **CRITICAL LIMITATION:** All content posted by unaudited clients will be PRIVATE.

**To Post Publicly:**
- Must submit app for TikTok audit
- Verify compliance with Terms of Service
- Approval timeline: 2-4 weeks
- Without approval: Videos only visible to you (useless)

**Audit Process:**
1. Build API integration
2. Submit audit request via TikTok for Business portal
3. TikTok reviews compliance
4. Approval granted → Videos post publicly
5. Rejection → Fix issues, resubmit

### TikTok vs Other Platforms API Comparison

| Feature | TikTok API | X API | LinkedIn API |
|---------|------------|-------|--------------|
| **Video Upload** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Business Account Required** | ✅ Yes | ❌ No | ❌ No |
| **Audit Required** | ✅ Yes (for public) | ❌ No | ✅ Yes (partner) |
| **Approval Timeline** | 2-4 weeks | Instant | 2-4 weeks |
| **Content Restrictions** | Private until audit | Public immediately | Public after partner |
| **Rate Limits** | Generous | 50/day | 100/day |
| **Cost** | Free | Free | Free |

**Conclusion:** TikTok API is more restrictive than X, but still feasible.

---

## Part 2: Implementation Plan

### Phase 1: TikTok Business Account Setup (Week 1)

**Step 1: Create Business Account**

1. **Create new TikTok account for brand:**
   - Username: `@SWFloridaComfortAC` (or similar, check availability)
   - Display Name: "SW Florida Comfort HVAC"
   - Bio: "24/7 AC Repair | Naples, Fort Myers, Cape Coral | Same-Day Service | (239) 766-6129 ❄️🌴"
   - Profile Picture: Company logo
   - Website: https://www.swfloridacomfort.com

2. **Convert to Business Account:**
   - Settings → Switch to Business Account
   - Category: "Professional Services" or "Home & Garden"
   - Business Email: Contact info

3. **Optimize Profile:**
   - Add contact button (Call, Website, Email)
   - Link website
   - Pin top-performing video (once posted)

**Step 2: Create TikTok Developer Account**

1. Go to: https://developers.tiktok.com/
2. Register developer account
3. Create a new app:
   - **App Name:** SW Florida Comfort Automation
   - **App Description:** "Content scheduling tool for HVAC service videos"
   - **Category:** Social Media Management
   - **Products:** Content Posting API

4. Get credentials:
   - Client Key (App ID)
   - Client Secret
   - Redirect URI: http://localhost:8000/callback

### Phase 2: OAuth Authentication (Week 1-2)

**Step 1: Implement OAuth Flow**

```python
# src/tiktok_auth.py

import requests
from urllib.parse import urlencode

class TikTokAuth:
    def __init__(self, client_key, client_secret, redirect_uri):
        self.client_key = client_key
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self):
        """Generate OAuth authorization URL."""
        params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.upload",
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": "random_state_string"
        }
        return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token."""
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data
        )

        return response.json()
        # Returns: {"access_token": "...", "expires_in": 86400, "refresh_token": "..."}
```

**Step 2: Authorization Script**

```bash
# Run one-time authorization
python -m src.tiktok_auth authorize

# Opens browser → TikTok OAuth consent
# Approve → Access token saved to .env
```

### Phase 3: Video Upload API Implementation (Week 2)

**Create TikTok Video Upload Module**

```python
# src/tiktok_api.py

import requests
import os

class TikTokAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://open.tiktokapis.com/v2"

    def initialize_upload(self, video_path):
        """Step 1: Initialize video upload and get upload URL."""
        file_size = os.path.getsize(video_path)

        payload = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,  # Single chunk for simplicity
                "total_chunk_count": 1
            }
        }

        response = requests.post(
            f"{self.base_url}/post/publish/video/init/",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        result = response.json()
        return result["data"]["upload_url"], result["data"]["publish_id"]

    def upload_video_file(self, upload_url, video_path):
        """Step 2: Upload video file to TikTok."""
        with open(video_path, "rb") as video_file:
            response = requests.put(
                upload_url,
                headers={"Content-Type": "video/mp4"},
                data=video_file
            )

        return response.status_code == 200

    def publish_video(self, publish_id, caption, privacy_level="PUBLIC_TO_EVERYONE"):
        """Step 3: Publish uploaded video.

        Args:
            publish_id: ID from initialize_upload
            caption: Video caption (max 2,200 characters, includes hashtags)
            privacy_level: PUBLIC_TO_EVERYONE, SELF_ONLY, MUTUAL_FOLLOW_FRIENDS

        NOTE: If not audited, privacy_level will be forced to SELF_ONLY!
        """
        payload = {
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000  # Thumbnail at 1 second
            },
            "source_info": {
                "source": "FILE_UPLOAD"
            }
        }

        response = requests.post(
            f"{self.base_url}/post/publish/video/publish/",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        return response.json()

    def post_video(self, video_path, caption, privacy="PUBLIC_TO_EVERYONE"):
        """Complete flow: Upload and publish video.

        Returns:
            {"publish_id": "...", "url": "..."}
        """
        # Step 1: Initialize
        upload_url, publish_id = self.initialize_upload(video_path)

        # Step 2: Upload file
        success = self.upload_video_file(upload_url, video_path)
        if not success:
            raise Exception("Video upload failed")

        # Step 3: Publish
        result = self.publish_video(publish_id, caption, privacy)

        return {
            "publish_id": publish_id,
            "url": f"https://www.tiktok.com/@SWFloridaComfortAC/video/{publish_id}"
        }
```

### Phase 4: Content Scheduler Integration (Week 3)

**Create TikTok Scheduler**

```python
# src/tiktok_scheduler.py

from src.tiktok_api import TikTokAPI
import os
from pathlib import Path

class TikTokScheduler:
    def __init__(self):
        self.api = TikTokAPI(access_token=os.getenv("TIKTOK_ACCESS_TOKEN"))
        self.video_queue_dir = Path("output/tiktok_videos")

    def post_next_video(self):
        """Post next video from queue."""
        # Get next video from queue directory
        videos = sorted(self.video_queue_dir.glob("*.mp4"))

        if not videos:
            print("No videos in queue")
            return

        video_path = videos[0]

        # Read caption from accompanying .txt file
        caption_file = video_path.with_suffix(".txt")
        with open(caption_file, "r") as f:
            caption = f.read()

        # Post to TikTok
        result = self.api.post_video(
            video_path=str(video_path),
            caption=caption,
            privacy="PUBLIC_TO_EVERYONE"  # Will be SELF_ONLY until audited!
        )

        print(f"Posted: {result['url']}")

        # Archive posted video
        archive_dir = self.video_queue_dir / "posted"
        archive_dir.mkdir(exist_ok=True)
        video_path.rename(archive_dir / video_path.name)
        caption_file.rename(archive_dir / caption_file.name)

        return result

    def post_from_schedule(self, count=1):
        """Post N videos from queue."""
        for i in range(count):
            self.post_next_video()
```

### Phase 5: API Audit Submission (Week 3-4)

**Submit App for Audit**

1. **Prepare Audit Submission:**
   - Complete app development
   - Test with private videos first
   - Document use case and compliance

2. **Submit Audit Request:**
   - Go to TikTok for Business portal
   - Navigate to developer dashboard
   - Click "Submit for Audit"
   - Fill out questionnaire:
     - **Use Case:** "Automated posting for local HVAC business educational content"
     - **Compliance:** "All content follows TikTok Community Guidelines"
     - **Data Privacy:** "No user data collected beyond OAuth"

3. **Wait for Approval:** 2-4 weeks

4. **If Approved:**
   - Videos post publicly
   - Full API access unlocked

5. **If Rejected:**
   - Review feedback
   - Fix compliance issues
   - Resubmit

**During Audit Wait:**
- Videos post as SELF_ONLY (private)
- Can still test workflow
- Manual posting as fallback

---

## Part 3: Video Content Creation Workflow

### TikTok Video Requirements

**Technical Specs:**
- Format: MP4, MOV, WebM
- Resolution: 1080x1920 (9:16 vertical) or 1080x1080 (1:1 square)
- Length: 3 seconds - 10 minutes (optimal: 15-60 seconds)
- File Size: Max 287.6 MB
- Frame Rate: 23-60 FPS

**Content Best Practices:**
- ✅ Hook in first 3 seconds
- ✅ Vertical video (phone native)
- ✅ Captions/text overlay (80% watch without sound)
- ✅ Educational or entertaining (not salesy)
- ✅ 15-60 seconds (optimal engagement)

### Video Content Ideas for HVAC

**Educational (Highest Performing):**
1. "3 Signs Your AC is About to Die" (prevention tips)
2. "What I Found in This AC Unit" (gross-out curiosity)
3. "Here's Why Your Electric Bill is So High" (value-driven)
4. "Homeowner Tried to Fix AC Himself - Here's What Happened" (entertainment + expertise)
5. "Quick HVAC Tip: Do This Before Summer" (seasonal urgency)

**Behind-the-Scenes:**
6. "Same-Day AC Repair in Naples - Full Process"
7. "Installing New AC System Start to Finish"
8. "Emergency Call at 2 AM - Here's What We Found"

**Social Proof:**
9. "Customer Reaction: AC Fixed in 2 Hours"
10. "Before vs After: Old AC vs New High-Efficiency"

### Video Creation Options

**Option 1: DIY with Smartphone (FREE)**

**Tools:**
- iPhone/Android camera (vertical mode)
- CapCut (free editing app) - add text, transitions
- Canva (free templates for thumbnails)

**Workflow:**
1. Film raw footage on-site (AC repairs, installs, tips)
2. Edit in CapCut:
   - Add hook text in first 3 seconds
   - Add captions throughout
   - Add background music (CapCut library)
   - Export 1080x1920 MP4
3. Save to `output/tiktok_videos/`
4. Create caption .txt file with hashtags

**Time:** 30-60 min per video

**Option 2: Batch Film + AI Editing**

**Tools:**
- Film 5-7 clips in one day
- Use AI video editor (e.g., Descript, Pictory.ai)
- Auto-generate captions, b-roll, music

**Time:** 2 hours batch → 7 videos for week

**Option 3: Hire Video Editor (SCALABLE)**

**Outsource:**
- Fiverr/Upwork: $10-$30 per video
- Send raw footage → receive edited video
- Batch 10 videos = $100-$300

**Time:** 1 hour filming → outsource editing

### Video Queue Structure

**Directory Structure:**
```
output/tiktok_videos/
├── video_001.mp4              # Ready to post
├── video_001.txt              # Caption + hashtags
├── video_002.mp4
├── video_002.txt
├── video_003.mp4
├── video_003.txt
└── posted/                    # Archive after posting
    ├── video_001.mp4
    └── video_001.txt
```

**Caption Format (.txt file):**
```
3 signs your AC is about to die 🚨

1. Strange noises (grinding, squealing)
2. Warm air instead of cold
3. Higher electric bills

Don't wait for it to fail in Florida heat!

Call us: (239) 766-6129

#ACRepair #HVAC #Naples #FloridaHeat #HVACTips #SWFlorida #AirConditioning
```

---

## Part 4: Posting Schedule & Automation

### Recommended Posting Schedule

**Frequency:** 2-3 videos/day

**Best Times for HVAC Content:**
- 7 AM: Morning scroll (commute)
- 12 PM: Lunch break
- 7 PM: Evening scroll (peak engagement)

**Cron Jobs:**

```bash
# TikTok posting schedule (2-3 videos/day)

# Morning post (7 AM)
0 7 * * * cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation && python -m src.tiktok_scheduler post_from_schedule --count 1 >> logs/tiktok_morning.log 2>&1

# Midday post (12 PM)
0 12 * * * cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation && python -m src.tiktok_scheduler post_from_schedule --count 1 >> logs/tiktok_midday.log 2>&1

# Evening post (7 PM)
0 19 * * * cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation && python -m src.tiktok_scheduler post_from_schedule --count 1 >> logs/tiktok_evening.log 2>&1
```

**Manual Workflow (Until Automation Ready):**

```bash
# Queue 7 videos for the week
# Sunday: Film and edit 7 videos
# Save to output/tiktok_videos/

# Monday-Sunday: Post manually or via script
python -m src.tiktok_scheduler post_from_schedule --count 1
```

---

## Part 5: Alternative Approaches

### Option A: Third-Party Scheduling Tools

**Recommended:** [Ayrshare](https://www.ayrshare.com/docs/apis/post/social-networks/tiktok) or [Loomly](https://www.loomly.com)

**Why Third-Party:**
- ✅ Already audited by TikTok (instant public posting)
- ✅ Simple API (no OAuth flow to build)
- ✅ Multi-platform (TikTok + LinkedIn + X + Facebook + Instagram)
- ✅ Analytics dashboard included

**Pricing:**
- Ayrshare: $49/month (covers all platforms)
- Loomly: $42/month

**API Example (Ayrshare):**

```python
import requests

def post_to_tiktok(video_path, caption):
    """Post video to TikTok via Ayrshare."""

    # Upload video to CDN first (Ayrshare requires public URL)
    video_url = upload_to_cdn(video_path)  # S3, Cloudflare, etc.

    payload = {
        "post": caption,
        "platforms": ["tiktok"],
        "mediaUrls": [video_url]
    }

    response = requests.post(
        "https://app.ayrshare.com/api/post",
        headers={"Authorization": f"Bearer {AYRSHARE_API_KEY}"},
        json=payload
    )

    return response.json()
```

**Pros:**
- ✅ No audit wait (posts publicly immediately)
- ✅ Covers LinkedIn + X too (one service for all)
- ✅ Less development time

**Cons:**
- ❌ $49-$42/month cost
- ❌ Requires video hosted at public URL (not local file)

### Option B: Manual Posting (Temporary)

**While Waiting for API Audit:**

1. Create TikTok videos
2. Post manually via TikTok app
3. Use scheduling feature in TikTok Creator Tools (built-in)

**TikTok Native Scheduling:**
- Free feature for Business Accounts
- Upload video in TikTok app
- Select "Schedule" → Pick date/time
- Auto-posts at scheduled time

**Pros:**
- ✅ Free
- ✅ No API needed
- ✅ Posts publicly immediately

**Cons:**
- ❌ Manual upload (not fully automated)
- ❌ Must use phone/desktop app

---

## Part 6: Implementation Timeline

### Fast Track (Ayrshare) - 1 Week

**Week 1:**
- [ ] Convert TikTok account to Business
- [ ] Sign up for Ayrshare ($49/month)
- [ ] Create 7 videos for Week 1
- [ ] Upload videos to CDN (S3, Cloudflare)
- [ ] Configure Ayrshare API
- [ ] Start posting 2-3 videos/day

**Result:** Posting live within 7 days, public immediately

### Official API Track - 4-5 Weeks

**Week 1: Setup**
- [ ] Convert TikTok account to Business
- [ ] Create TikTok Developer account
- [ ] Create OAuth app
- [ ] Implement OAuth flow

**Week 2: Development**
- [ ] Build video upload API
- [ ] Create scheduler
- [ ] Test with private posts

**Week 3: Audit Submission**
- [ ] Submit app for TikTok audit
- [ ] Continue posting as SELF_ONLY (private)

**Week 4-5: Approval Wait**
- [ ] Wait for audit approval (2-4 weeks)
- [ ] Meanwhile: Post manually or use Ayrshare

**Week 6: Go Live**
- [ ] Audit approved → Switch to PUBLIC_TO_EVERYONE
- [ ] Enable automated posting
- [ ] Monitor analytics

**Result:** Free forever, but 4-5 week delay for public posts

---

## Part 7: Recommended Implementation Path

### Hybrid Approach (BEST)

**Phase 1 (Week 1-4): Use Ayrshare**
- Sign up for Ayrshare today
- Start posting immediately (public posts)
- Build audience while developing official API

**Phase 2 (Week 2-5): Build Official API in Parallel**
- Develop TikTok API integration
- Submit for audit
- Wait for approval

**Phase 3 (Week 6+): Migrate to Official API**
- Once audit approved, switch from Ayrshare to official API
- Cancel Ayrshare ($49/month savings)
- Now posting for free with official API

**Benefits:**
- ✅ Immediate results (Ayrshare)
- ✅ Long-term cost savings (official API)
- ✅ No waiting period delays growth

**Cost:**
- Months 1-2: $98 (Ayrshare while building)
- Months 3+: $0 (official API)
- **Total Investment:** $98 to get started immediately

---

## Part 8: Step-by-Step Quick Start

### Quick Start: Ayrshare (Recommended)

**1. Create TikTok Business Account**
```
- Download TikTok app
- Create @SWFloridaComfortAC
- Settings → Switch to Business Account
- Category: Professional Services
- Add bio, website, contact info
```

**2. Sign Up for Ayrshare**
```
- Go to: https://www.ayrshare.com
- Sign up for $49/month plan
- Get API key from dashboard
- Save to .env: AYRSHARE_API_KEY=...
```

**3. Create Videos**
```
- Film 7 videos (one week's content)
- Edit with CapCut (add captions, music)
- Export as 1080x1920 MP4
- Upload to CDN (S3, Cloudflare, or Ayrshare's hosting)
```

**4. Schedule Posts**
```python
# Schedule Week 1 posts
from src.ayrshare_api import AyrshareAPI

ayr = AyrshareAPI(api_key=os.getenv("AYRSHARE_API_KEY"))

videos = [
    {"url": "https://cdn.example.com/video1.mp4", "caption": "3 signs AC failing..."},
    {"url": "https://cdn.example.com/video2.mp4", "caption": "Quick HVAC tip..."},
    # ... 5 more
]

for video in videos:
    ayr.post_to_tiktok(video["url"], video["caption"])
```

**5. Monitor Performance**
```
- Check TikTok Analytics daily
- Track: Views, Likes, Comments, Shares
- Identify top-performing content
- Create more of what works
```

---

## Part 9: Success Metrics

### TikTok KPIs to Track

| Metric | Week 1 Goal | Month 1 Goal | Month 3 Goal |
|--------|-------------|--------------|--------------|
| **Videos Posted** | 14-21 | 60-90 | 180-270 |
| **Views/Video** | 100+ | 500+ | 2,000+ |
| **Engagement Rate** | 3% | 5% | 8% |
| **Followers** | 50+ | 500+ | 2,000+ |
| **Profile Visits** | 20+ | 200+ | 1,000+ |
| **Website Clicks** | 5+ | 50+ | 200+ |
| **Phone Calls** | 1-3 | 5-10 | 10-20 |

**Viral Potential:**
- 1 in 10 videos hits 10K+ views
- 1 in 50 videos hits 100K+ views
- Viral video = 50-100 calls in 48 hours

---

## Part 10: Next Steps

### Immediate Actions (This Week)

1. **Create @SWFloridaComfortAC TikTok Account**
   - Business account conversion
   - Optimize profile (bio, logo, contact)

2. **Choose Implementation Path:**
   - **Option A:** Ayrshare ($49/month, immediate) ← RECOMMENDED
   - **Option B:** Official API (free, 4-5 week wait)
   - **Option C:** Hybrid (both, migrate later)

3. **Create First 7 Videos**
   - Film this weekend
   - Edit with CapCut
   - Queue for Week 1 posting

4. **Set Up Posting Automation**
   - Configure Ayrshare OR build official API
   - Test with 1 video first
   - Schedule Week 1 posts

5. **Monitor & Iterate**
   - Track analytics daily
   - Identify winning content
   - Double down on what works

---

## Sources

- [TikTok Content Posting API](https://developers.tiktok.com/products/content-posting-api/)
- [TikTok Content Posting Guide](https://developers.tiktok.com/doc/content-posting-api-get-started)
- [TikTok Business API Portal](https://business-api.tiktok.com/portal)
- [Ayrshare TikTok Integration](https://www.ayrshare.com/docs/apis/post/social-networks/tiktok)
- [Ultimate Guide to TikTok Automation](https://www.spurnow.com/en/blogs/tiktok-automation)
- [Comprehensive Guide to TikTok API](https://scrapfly.io/blog/posts/guide-to-tiktok-api)

---

## Conclusion

**TikTok Automation is FEASIBLE** with official API, but has AUDIT requirement.

**Critical Decision: Ayrshare vs Official API**

| Factor | Ayrshare | Official API |
|--------|----------|--------------|
| **Time to Live** | 1 week | 4-5 weeks |
| **Public Posts** | Immediate | After audit approval |
| **Cost** | $49/month | Free |
| **Development** | Minimal (API calls) | Moderate (OAuth + upload) |
| **Long-Term** | Ongoing cost | Free forever |

**Recommended:** Hybrid approach
1. Start with Ayrshare (immediate results)
2. Build official API in parallel
3. Migrate after audit approval (save $588/year)

**Expected ROI:**
- Cost: $49/month (Ayrshare) or $0 (official API)
- Leads: 10-20/month
- Revenue: $3K-$20K/month
- ROI: 61x-408x (Ayrshare) or Infinite (official API)

Ready to create @SWFloridaComfortAC and start posting?
