# Social Media API Setup Guide
**Date:** January 20, 2026
**Status:** Step-by-step setup for all free APIs

---

## Overview

Setting up 4 platform APIs for automated posting:
1. ✅ **X (Twitter)** - Already working
2. 🔧 **Facebook** - Setup TODAY (instant, free)
3. ⏳ **TikTok** - Waiting for audit approval (2-4 weeks)
4. ⏳ **LinkedIn** - Need to apply for Partner (2-4 weeks)

**Cost:** $0 (all free APIs)
**Timeline:** Fully operational in 4-6 weeks

---

## 1. Facebook API Setup (DO THIS NOW - 15 minutes)

### Prerequisites
- Facebook personal account
- Business email address

### Step-by-Step

#### A. Create Facebook Business Page

1. **Go to:** https://www.facebook.com/pages/create
2. **Click:** "Get Started"
3. **Page Type:** Business or Brand
4. **Fill in details:**
   - **Page name:** SW Florida Comfort
   - **Category:** Heating, Ventilation & Air Conditioning Service
   - **Description:**
     ```
     24/7 AC Repair & Installation | Naples, Fort Myers, Cape Coral
     Licensed & Insured | Same-Day Service Available
     Call: (239) 766-6129
     ```

5. **Add profile picture:** Upload HVAC company logo
6. **Add cover photo:** Upload branded cover image
7. **Complete setup:**
   - Address: Naples, FL
   - Phone: (239) 766-6129
   - Website: https://www.swfloridacomfort.com
   - Hours: 24/7 Emergency Service

#### B. Create Facebook Developer App

1. **Go to:** https://developers.facebook.com/
2. **Click:** "My Apps" → "Create App"
3. **App Type:** "Business"
4. **Fill in:**
   - **App Display Name:** SW Florida Comfort Automation
   - **App Contact Email:** wmarceau@marceausolutions.com
   - **Business Account:** (create if needed)
5. **Click:** "Create App"

#### C. Get Page Access Token

1. **In your new app**, go to: **Tools** → **Graph API Explorer**
2. **User or Page:** Select "SW Florida Comfort" page
3. **Permissions:** Add these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
4. **Generate Token:** Click "Generate Access Token"
5. **Authorize:** Grant permissions
6. **Copy token:** Starts with `EAA...` (this is temporary)

#### D. Get Long-Lived Token (Never Expires)

Run this command in terminal:

```bash
# Replace with your values
APP_ID="YOUR_APP_ID"
APP_SECRET="YOUR_APP_SECRET"
SHORT_TOKEN="YOUR_SHORT_TOKEN"

# Get long-lived user token (60 days)
curl "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$APP_SECRET&fb_exchange_token=$SHORT_TOKEN"

# Response will have access_token - copy it
```

Then get permanent page token:

```bash
# Use the long-lived token from above
USER_TOKEN="LONG_LIVED_TOKEN_FROM_ABOVE"

# Get page access token (never expires)
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=$USER_TOKEN"

# Response will have access_token for your page - copy it
```

#### E. Add to `.env` File

```bash
# Add to /Users/williammarceaujr./dev-sandbox/.env
FACEBOOK_PAGE_ACCESS_TOKEN="YOUR_PERMANENT_PAGE_TOKEN"
FACEBOOK_PAGE_ID="YOUR_PAGE_ID"  # From the /me/accounts response
```

#### F. Test Posting

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# Test post
python -m src.facebook_api test
```

**Expected:** Post appears on SW Florida Comfort Facebook page

---

## 2. TikTok API Setup (ALREADY IN PROGRESS)

### Current Status
⏳ **Waiting for audit approval** (2-4 weeks)

### What You've Done
- ✅ Created TikTok Developer account
- ✅ Created app
- ✅ Submitted for audit

### What Happens Next
1. **Wait 2-4 weeks** for TikTok to review app
2. **Approval email** arrives
3. **Posts become PUBLIC** automatically

### Meanwhile: Film & Stockpile Content

```bash
# Create content directory
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/social-media-automation/content/tiktok/

# Film videos NOW:
# - 3 signs your AC is failing
# - How to change your AC filter
# - Why is my AC frozen?
# - Before/After AC cleaning
# - 24/7 emergency service promo
# ... (target 20-30 videos)
```

**When approved, you'll upload all at once**

---

## 3. LinkedIn API Setup (START THIS NOW - 30 minutes)

### Step-by-Step

#### A. Create LinkedIn Developer App

1. **Go to:** https://www.linkedin.com/developers/
2. **Click:** "Create App"
3. **Fill in:**
   - **App name:** Marceau Solutions Automation
   - **LinkedIn Page:** (create Marceau Solutions company page first if needed)
   - **App logo:** Upload Marceau Solutions logo
   - **Legal agreement:** Check box
4. **Click:** "Create App"

#### B. Configure OAuth Settings

1. **In your app**, go to: **Auth** tab
2. **Redirect URLs:** Add:
   ```
   http://localhost:8000/callback
   ```
3. **Save**

#### C. Request API Access (Marketing Developer Platform)

1. **In your app**, go to: **Products** tab
2. **Find:** "Marketing Developer Platform"
3. **Click:** "Request Access"
4. **Fill in application:**
   - **Use case:** Social media automation for B2B marketing
   - **Describe app:** Automated LinkedIn posting for AI automation services company
   - **Company size:** 1-10 employees
   - **Volume:** 3-5 posts/week
5. **Submit**

**Timeline:** 2-4 weeks for approval

#### D. While Waiting: Get Credentials

1. **In your app**, go to: **Auth** tab
2. **Copy:**
   - **Client ID**
   - **Client Secret**
3. **Add to `.env`:**

```bash
# Add to /Users/williammarceaujr./dev-sandbox/.env
LINKEDIN_CLIENT_ID="YOUR_CLIENT_ID"
LINKEDIN_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

#### E. After Approval: Get Access Token

Run OAuth flow once to get refresh token:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python -m src.linkedin_auth
```

This will:
1. Open browser for authorization
2. You approve the app
3. Script saves refresh token to `.env`

---

## 4. X (Twitter) API - Already Working ✅

### Current Status
✅ **Fully operational** - posting 20-30x/day

### Configuration
Already in `.env`:
```bash
X_API_KEY="..."
X_API_SECRET="..."
X_ACCESS_TOKEN="..."
X_ACCESS_TOKEN_SECRET="..."
```

**No action needed** - continue current automation

---

## Environment Variables Summary

After all setups complete, your `.env` should have:

```bash
# X (Twitter) - EXISTING
X_API_KEY="..."
X_API_SECRET="..."
X_ACCESS_TOKEN="..."
X_ACCESS_TOKEN_SECRET="..."

# Facebook - ADD TODAY
FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
FACEBOOK_PAGE_ID="123456789"

# TikTok - ADD WHEN APPROVED
TIKTOK_CLIENT_KEY="..."
TIKTOK_CLIENT_SECRET="..."
TIKTOK_ACCESS_TOKEN="..."

# LinkedIn - ADD WHEN APPROVED
LINKEDIN_CLIENT_ID="..."
LINKEDIN_CLIENT_SECRET="..."
LINKEDIN_ACCESS_TOKEN="..."
LINKEDIN_REFRESH_TOKEN="..."
```

---

## Implementation Checklist

### TODAY (15-30 minutes):
- [ ] Create SW Florida Comfort Facebook Page
- [ ] Create Facebook Developer App
- [ ] Get Page Access Token (permanent)
- [ ] Add to `.env` file
- [ ] Test Facebook posting

### THIS WEEK (30 minutes):
- [ ] Create LinkedIn Developer App
- [ ] Apply for Marketing Developer Platform access
- [ ] Add LinkedIn credentials to `.env`
- [ ] Optimize William Marceau LinkedIn profile

### WHILE WAITING (ongoing):
- [ ] Film 20-30 TikTok videos
- [ ] Draft 30 LinkedIn posts (Month 1 content)
- [ ] Create Facebook content calendar
- [ ] Continue X automation (20-30 posts/day)

### WHEN TIKTOK APPROVED (Week 3-5):
- [ ] Get TikTok access token
- [ ] Upload stockpiled videos
- [ ] Start 2-3 videos/day schedule

### WHEN LINKEDIN APPROVED (Week 3-5):
- [ ] Complete OAuth flow
- [ ] Test LinkedIn posting
- [ ] Start 3-5 posts/week schedule

---

## Testing Commands

After each API is set up, test posting:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# Test Facebook
python -m src.facebook_api test --text "Test post from automation"

# Test TikTok (when approved)
python -m src.tiktok_api test --video content/tiktok/test.mp4 --caption "Test video"

# Test LinkedIn (when approved)
python -m src.linkedin_api test --text "Test post from automation"

# Test X (already working)
python -m src.x_scheduler add "Test tweet" --priority urgent
```

---

## Troubleshooting

### Facebook: "Invalid OAuth Access Token"
**Cause:** Token expired or incorrect
**Fix:** Regenerate long-lived token (Step 1D)

### TikTok: "Posts are private"
**Cause:** App not yet approved by TikTok audit
**Fix:** Wait for approval email (2-4 weeks)

### LinkedIn: "Insufficient permissions"
**Cause:** Marketing Developer Platform not approved
**Fix:** Check application status, wait for approval

### X: Rate limit exceeded
**Cause:** Posting too frequently
**Fix:** Reduce to <50 posts/day (free tier limit)

---

## Success Criteria

- ✅ Facebook page live with first post
- ✅ TikTok videos stockpiled (20-30 videos ready)
- ✅ LinkedIn application submitted
- ✅ All credentials in `.env`
- ✅ All test posts successful

---

## Next Steps After All APIs Active

1. **Build unified scheduler:**
   - `src/multi_platform_scheduler.py`
   - Post to all platforms from single command

2. **Set up cron jobs:**
   - Facebook: 1-2 posts/day
   - TikTok: 2-3 videos/day
   - LinkedIn: 3-5 posts/week
   - X: 20-30 posts/day (continue current)

3. **Monitor analytics:**
   - Track engagement per platform
   - Optimize posting times
   - A/B test content formats

---

**Ready to start?** Let's set up Facebook API first (15 minutes, instant results).
