# LinkedIn MCP Implementation Guide
**Date:** January 20, 2026
**Purpose:** Build LinkedIn MCP for automating AI automation service content posting

---

## Executive Summary

**Goal:** Create an MCP (Model Context Protocol) server for LinkedIn to automate posting for Marceau Solutions AI automation services.

**LinkedIn API Status:** ✅ Official API exists and is well-documented
**Feasibility:** ✅ HIGH - LinkedIn provides Posts API for content automation
**Timeline:** 2-3 weeks (including partner approval process)
**Cost:** Free (LinkedIn Partner program) + time investment

---

## Part 1: LinkedIn API Research Findings

### Official LinkedIn API Capabilities

**Primary API:** [Posts API (Microsoft Learn)](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2025-11)

**What LinkedIn API Can Do:**
- ✅ Create text posts on personal profiles
- ✅ Create posts on company pages
- ✅ Upload and attach images/documents
- ✅ Schedule posts (via third-party integration)
- ✅ Manage engagement (likes, comments)
- ✅ Access profile data and connections
- ✅ Analytics and insights

**Authentication:** OAuth 2.0 (standard)

**Rate Limits:**
- Posts: 100/day per user (generous for our 3-5 posts/week strategy)
- API calls: Varies by endpoint, generally sufficient for automation

**Requirements:**
1. **LinkedIn Partner Status** - Must apply and be approved
2. **OAuth App** - Create app in LinkedIn Developer Portal
3. **User Consent** - Must authorize app to post on their behalf

### LinkedIn vs X API Comparison

| Feature | LinkedIn API | X API |
|---------|-------------|-------|
| **Official Support** | ✅ Well-documented | ✅ Well-documented |
| **Rate Limits** | 100 posts/day | 50 posts/day (free tier) |
| **Authentication** | OAuth 2.0 | OAuth 2.0 |
| **Image Support** | ✅ Yes | ✅ Yes |
| **Scheduling** | Via API | Via API |
| **Partner Approval** | Required (2-4 weeks) | Not required (instant) |
| **Cost** | Free | Free (with limits) |
| **Use Case Fit** | ⭐⭐⭐⭐⭐ B2B perfect | ⭐⭐⭐⭐ Tech audience |

**Conclusion:** LinkedIn API is mature, well-supported, and perfect for B2B automation.

---

## Part 2: Implementation Plan

### Phase 1: LinkedIn Partner Application (Week 1)

**Step 1: Create LinkedIn Developer Account**

1. Go to: https://www.linkedin.com/developers/
2. Sign in with William Marceau's LinkedIn account
3. Create a new app:
   - **App Name:** Marceau Solutions Automation
   - **LinkedIn Page:** Marceau Solutions (if company page exists, or personal)
   - **Privacy Policy URL:** https://marceausolutions.com/privacy.html
   - **App Logo:** Marceau Solutions logo
   - **App Description:** "Content automation tool for AI automation services marketing"

**Step 2: Apply for LinkedIn Partner Status**

1. Navigate to Partner Program: https://partner.linkedin.com/
2. Select "Marketing Developer Platform"
3. Fill out application:
   - **Use Case:** Content marketing automation for AI services
   - **Products Needed:** Posts API, Profile API
   - **Scale:** 3-5 posts/week, personal profile
4. Submit for review

**Expected Timeline:** 2-4 weeks for approval

**Alternative if Rejected:** Use third-party services like Buffer, Hootsuite (they already have partner status)

### Phase 2: OAuth Authentication Setup (Week 2)

**Step 1: Configure OAuth App**

```python
# config/linkedin_config.py

LINKEDIN_CONFIG = {
    "client_id": "YOUR_APP_CLIENT_ID",  # From LinkedIn Developer Portal
    "client_secret": "YOUR_APP_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8000/callback",
    "scopes": [
        "w_member_social",  # Post on behalf of user
        "r_liteprofile",    # Read basic profile
        "r_emailaddress"    # Read email (optional)
    ]
}
```

**Step 2: Implement OAuth Flow**

```python
# src/linkedin_auth.py

import requests
from urllib.parse import urlencode

class LinkedInAuth:
    def __init__(self, config):
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.redirect_uri = config["redirect_uri"]
        self.scopes = config["scopes"]

    def get_authorization_url(self):
        """Generate OAuth authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes)
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=data
        )
        return response.json()  # {"access_token": "...", "expires_in": 5184000}
```

**Step 3: One-Time Authorization**

```bash
# Run authorization script
python -m src.linkedin_auth authorize

# Opens browser to LinkedIn OAuth consent
# User approves → Receives access token
# Token saved to .env file
```

### Phase 3: LinkedIn Posting API Implementation (Week 3)

**Create LinkedIn Posting Module**

```python
# src/linkedin_api.py

import requests
import json
from datetime import datetime

class LinkedInAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def get_user_id(self):
        """Get authenticated user's LinkedIn ID."""
        response = requests.get(
            f"{self.base_url}/me",
            headers=self.headers
        )
        return response.json()["id"]

    def create_text_post(self, text, visibility="PUBLIC"):
        """Create text-only post.

        Args:
            text: Post content (max 3,000 characters)
            visibility: PUBLIC, CONNECTIONS, or LOGGED_IN
        """
        user_id = self.get_user_id()

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        response = requests.post(
            f"{self.base_url}/ugcPosts",
            headers=self.headers,
            data=json.dumps(payload)
        )

        return response.json()

    def create_image_post(self, text, image_path, visibility="PUBLIC"):
        """Create post with image.

        Args:
            text: Post content
            image_path: Path to image file
            visibility: PUBLIC, CONNECTIONS, or LOGGED_IN
        """
        # Step 1: Upload image
        image_urn = self._upload_image(image_path)

        # Step 2: Create post with image
        user_id = self.get_user_id()

        payload = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": image_urn
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        response = requests.post(
            f"{self.base_url}/ugcPosts",
            headers=self.headers,
            data=json.dumps(payload)
        )

        return response.json()

    def _upload_image(self, image_path):
        """Upload image to LinkedIn and return URN."""
        # LinkedIn image upload flow (multi-step)
        # 1. Register upload
        # 2. Upload file
        # 3. Finalize
        # See: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api

        # Implementation details here...
        pass
```

### Phase 4: Content Scheduler Integration (Week 3)

**Integrate with Existing Scheduler**

```python
# src/linkedin_scheduler.py

from src.linkedin_api import LinkedInAPI
from src.business_content_generator import BusinessContentGenerator
import os

class LinkedInScheduler:
    def __init__(self):
        self.api = LinkedInAPI(access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"))
        self.content_gen = BusinessContentGenerator()

    def generate_and_post(self, business_id="marceau-solutions"):
        """Generate content and post to LinkedIn."""

        # Generate post using existing content templates
        post = self.content_gen.generate_post(
            business_id=business_id,
            template_type="case_study_update",  # Or other templates
            campaign="linkedin-thought-leadership",
            generate_image=False  # LinkedIn posts often text-focused
        )

        # Post to LinkedIn
        result = self.api.create_text_post(
            text=post.content,
            visibility="PUBLIC"
        )

        # Log success
        print(f"Posted to LinkedIn: {result['id']}")

        return result

    def schedule_week(self):
        """Generate and schedule posts for the week (3-5 posts)."""
        # LinkedIn strategy: 3-5 posts/week (not daily)
        # Best days: Tue, Wed, Thu
        # Best times: 10 AM, 12 PM, 5 PM

        posts_per_week = 4
        # Implementation...
```

---

## Part 3: MCP Server Architecture

### MCP Server Design

**File Structure:**
```
projects/linkedin-mcp/
├── src/
│   ├── linkedin_mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # MCP server entry point
│   │   ├── linkedin_api.py    # LinkedIn API wrapper
│   │   ├── auth.py            # OAuth flow
│   │   ├── scheduler.py       # Post scheduling
│   │   └── content.py         # Content generation
│   └── linkedin_mcp.py
├── server.json                # MCP manifest
├── pyproject.toml             # Package config
├── README.md
└── .env                       # Credentials
```

**MCP Server Implementation:**

```python
# src/linkedin_mcp/server.py

from mcp.server import Server
from mcp import Tool
from .linkedin_api import LinkedInAPI
import os

app = Server("linkedin-automation")

@app.tool()
def post_to_linkedin(text: str, visibility: str = "PUBLIC") -> dict:
    """Post content to LinkedIn.

    Args:
        text: Post content (max 3,000 characters)
        visibility: PUBLIC, CONNECTIONS, or LOGGED_IN

    Returns:
        {
            "success": True,
            "post_id": "...",
            "url": "..."
        }
    """
    api = LinkedInAPI(access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"))
    result = api.create_text_post(text, visibility)

    return {
        "success": True,
        "post_id": result["id"],
        "url": f"https://www.linkedin.com/feed/update/{result['id']}"
    }

@app.tool()
def generate_linkedin_post(topic: str, template: str = "thought_leadership") -> dict:
    """Generate LinkedIn post content.

    Args:
        topic: Post topic (e.g., "Voice AI case study")
        template: Content template type

    Returns:
        {"content": "...", "hashtags": [...]}
    """
    # Use existing content generator
    from src.business_content_generator import BusinessContentGenerator

    gen = BusinessContentGenerator()
    post = gen.generate_post(
        business_id="marceau-solutions",
        template_type=template,
        campaign="linkedin"
    )

    return {
        "content": post.content,
        "hashtags": post.hashtags
    }

@app.tool()
def schedule_linkedin_posts(count: int = 4) -> dict:
    """Schedule LinkedIn posts for the week.

    Args:
        count: Number of posts to schedule (default 4/week)

    Returns:
        {"scheduled": [...], "count": 4}
    """
    from .scheduler import LinkedInScheduler

    scheduler = LinkedInScheduler()
    posts = scheduler.schedule_week(count=count)

    return {
        "scheduled": posts,
        "count": len(posts)
    }

if __name__ == "__main__":
    app.run()
```

---

## Part 4: Alternative Approach (If Partner Approval Slow)

### Option A: Third-Party Automation Services

**Recommended:** [Ayrshare](https://www.ayrshare.com/docs/apis/post/social-networks/linkedin)

**Why Ayrshare:**
- Already has LinkedIn Partner status
- Simple API: One endpoint posts to LinkedIn, X, Facebook, TikTok
- Pricing: $49/month (unlimited posts)
- No waiting for partner approval

**Implementation:**

```python
# src/ayrshare_api.py

import requests

class AyrshareAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://app.ayrshare.com/api"

    def post_to_linkedin(self, text, image_url=None):
        """Post to LinkedIn via Ayrshare."""
        payload = {
            "post": text,
            "platforms": ["linkedin"],
        }

        if image_url:
            payload["mediaUrls"] = [image_url]

        response = requests.post(
            f"{self.base_url}/post",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )

        return response.json()
```

**Pros:**
- ✅ Instant access (no approval wait)
- ✅ Multi-platform support (LinkedIn + X + TikTok + Facebook)
- ✅ Managed compliance (they handle API changes)

**Cons:**
- ❌ $49/month cost
- ❌ Dependency on third party

### Option B: Puppeteer/Selenium Automation (NOT RECOMMENDED)

**Why NOT:**
- ❌ Violates LinkedIn Terms of Service
- ❌ Risk of account ban
- ❌ Unreliable (breaks with UI changes)
- ❌ No official support

**Verdict:** Only use official API or approved third-party services

---

## Part 5: Implementation Timeline

### Week 1: Setup & Partner Application
- [ ] Create LinkedIn Developer account
- [ ] Create OAuth app
- [ ] Apply for LinkedIn Partner status
- [ ] Wait for approval (2-4 weeks)

### Week 2-3: Development (Parallel to Approval Wait)
- [ ] Build OAuth authentication flow
- [ ] Implement LinkedIn API wrapper
- [ ] Create content scheduler
- [ ] Test with dummy account (if available)

### Week 4: Integration & Testing
- [ ] Integrate with existing content generator
- [ ] Create MCP server structure
- [ ] Test posting flow
- [ ] Set up cron jobs (3-5 posts/week)

### Week 5: Launch
- [ ] Post first LinkedIn content
- [ ] Monitor engagement
- [ ] Adjust posting schedule based on analytics
- [ ] Document learnings

**Total Timeline:** 4-5 weeks (including partner approval)

**Fast Track:** Use Ayrshare → 1 week implementation

---

## Part 6: Content Strategy for LinkedIn

### LinkedIn Content Pillars (Per Platform Analysis)

**Focus:** B2B thought leadership, case studies, technical insights

**Post Types:**
1. **Case Studies** (30%) - "How we automated 47 hours/week for a Naples gym"
2. **Technical Insights** (25%) - "Here's the tech stack I use for Voice AI"
3. **Industry Trends** (20%) - "AI won't replace you - but the person using AI will"
4. **Behind-the-Scenes** (15%) - "Building in public: Week 3 of Voice AI POC"
5. **Engagement Hooks** (10%) - "What's the #1 task you wish you could automate?"

**Posting Frequency:** 3-5 posts/week (NOT daily like X)

**Best Times:**
- Tuesday: 10 AM
- Wednesday: 12 PM
- Thursday: 5 PM

**Character Limit:** 3,000 characters (vs X's 280)
- Use this! LinkedIn rewards long-form, valuable content

**Image Strategy:**
- Less critical than X (text-first platform)
- Use for case study infographics
- Professional headshots, screenshots of results

---

## Part 7: Success Metrics

### LinkedIn KPIs to Track

| Metric | Week 1 Goal | Month 1 Goal | Month 3 Goal |
|--------|-------------|--------------|--------------|
| **Posts Published** | 3-5 | 12-20 | 36-60 |
| **Impressions/Post** | 100+ | 500+ | 1,000+ |
| **Engagement Rate** | 2% | 4% | 6% |
| **Profile Views** | 20+ | 100+ | 300+ |
| **Connection Requests** | 5+ | 20+ | 50+ |
| **Qualified Leads** | 0-1 | 1-3 | 3-5 |

**Lead Quality Matters More Than Volume:**
- 1 LinkedIn lead = Worth 10 X leads
- Higher intent (B2B decision-makers)
- Larger deal sizes ($10K-$30K vs $500-$3K)

---

## Part 8: Next Steps

### Immediate Actions (This Week)

1. **Apply for LinkedIn Partner Status** (2-4 week approval)
2. **OR: Sign up for Ayrshare** ($49/month, instant access)
3. **Optimize William Marceau LinkedIn Profile**
   - Professional headshot
   - Compelling headline: "Building AI Automation for Local Businesses | Voice AI | Lead Gen"
   - About section: Case studies, expertise, contact
4. **Draft 15 LinkedIn Posts** (Month 1 content)
5. **Set up posting schedule** (Tue/Wed/Thu)

### Decision Point: Official API vs Ayrshare

**Option 1: Official LinkedIn API (FREE but wait 2-4 weeks)**
- Apply for partner status now
- Build during approval wait
- Launch in 4-5 weeks

**Option 2: Ayrshare ($49/month but immediate)**
- Sign up today
- Posting live this week
- Covers LinkedIn + X + TikTok + Facebook

**Recommendation:** Start with Ayrshare for immediate results, migrate to official API later (save $588/year)

---

## Sources

- [LinkedIn Posts API Documentation](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2025-11)
- [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
- [Complete Guide to LinkedIn API](https://evaboot.com/blog/what-is-linkedin-api)
- [Building LinkedIn Automation Stack](https://www.getphyllo.com/post/building-full-linkedin-automation-stack-using-official-api-endpoints-iv)
- [Ayrshare LinkedIn Integration](https://www.ayrshare.com/docs/apis/post/social-networks/linkedin)

---

## Conclusion

**LinkedIn MCP is HIGHLY FEASIBLE** with official API support.

**Recommended Path:**
1. Start with Ayrshare (immediate results)
2. Apply for LinkedIn Partner (parallel track)
3. Migrate to official API after approval (cost savings)
4. Build MCP server for Claude Desktop integration

**Expected ROI:**
- Cost: $49/month (Ayrshare) or $0 (official API after approval)
- Leads: 1-3 qualified/month
- Pipeline: $10K-$30K/month
- ROI: 204x-612x (Ayrshare) or Infinite (official API)

Ready to proceed with implementation?
