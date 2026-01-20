# Quick Start: Free API Setup

**Goal:** Get posting to Facebook TODAY, LinkedIn + TikTok in 2-4 weeks
**Cost:** $0 (all free APIs)
**Time:** 45 minutes total setup

---

## Step 1: Facebook API (DO THIS NOW - 15 min)

### A. Create Facebook Page

1. Go to: https://www.facebook.com/pages/create
2. Page name: **SW Florida Comfort**
3. Category: **Heating, Ventilation & Air Conditioning Service**
4. Add logo and cover photo
5. Fill in: Address (Naples, FL), Phone (239-766-6129), Website

### B. Create Developer App

1. Go to: https://developers.facebook.com/
2. Click: **My Apps** → **Create App** → **Business**
3. App name: **SW Florida Comfort Automation**
4. Contact email: wmarceau@marceausolutions.com

### C. Get Page Access Token

1. In your app: **Tools** → **Graph API Explorer**
2. Select your page from dropdown
3. Add permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
4. Click: **Generate Access Token**
5. Copy the token (starts with `EAA...`)

### D. Make Token Permanent

Open Terminal and run:

```bash
# Get your app credentials from developers.facebook.com
# App Dashboard → Settings → Basic

# Replace these values:
APP_ID="YOUR_APP_ID"
APP_SECRET="YOUR_APP_SECRET"
SHORT_TOKEN="TOKEN_FROM_STEP_C"

# Get long-lived user token
curl "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$APP_SECRET&fb_exchange_token=$SHORT_TOKEN"

# Copy the access_token from response
USER_TOKEN="PASTE_TOKEN_FROM_ABOVE"

# Get permanent page token
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=$USER_TOKEN"

# Copy the access_token from response (this is your permanent token)
```

### E. Add to .env File

```bash
# Open .env file
open /Users/williammarceaujr./dev-sandbox/.env

# Add these lines (replace with your values):
FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
FACEBOOK_PAGE_ID="123456789"
```

Save and close.

### F. Test Posting

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python -m src.facebook_api test
```

**Expected:** Test post appears on your Facebook page

---

## Step 2: LinkedIn API (START THIS NOW - 15 min)

### A. Create Developer App

1. Go to: https://www.linkedin.com/developers/
2. Click: **Create App**
3. Fill in:
   - App name: **Marceau Solutions Automation**
   - LinkedIn Page: (create company page first if needed)
   - Upload logo
4. Click: **Create App**

### B. Add Redirect URL

1. In your app: **Auth** tab
2. Redirect URLs: Add `http://localhost:8000/callback`
3. Save

### C. Apply for API Access

1. In your app: **Products** tab
2. Find: **Marketing Developer Platform**
3. Click: **Request Access**
4. Fill in:
   - Use case: Social media automation for B2B marketing
   - Description: Automated LinkedIn posting for AI automation services
   - Volume: 3-5 posts/week
5. Submit

**Wait 2-4 weeks for approval**

### D. Save Credentials

1. In your app: **Auth** tab
2. Copy **Client ID** and **Client Secret**

```bash
# Open .env file
open /Users/williammarceaujr./dev-sandbox/.env

# Add these lines:
LINKEDIN_CLIENT_ID="YOUR_CLIENT_ID"
LINKEDIN_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

### E. When Approved: Run OAuth Flow

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python -m src.linkedin_auth
```

This will:
1. Open browser for authorization
2. You approve the app
3. Script saves access token to .env

### F. Test Posting

```bash
python -m src.linkedin_api test
```

---

## Step 3: TikTok API (ALREADY IN PROGRESS)

**Status:** ⏳ Waiting for audit approval (2-4 weeks)

**What to do now:**

### Film & Stockpile Videos

```bash
# Create content directory
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/social-media-automation/content/tiktok/
```

**Film 20-30 videos:**
- 3 signs your AC is failing
- How to change your AC filter
- Why is my AC frozen?
- Before/After AC cleaning
- 24/7 emergency service promo
- Customer testimonials
- Behind-the-scenes repairs
- Energy saving tips
- Common AC myths debunked
- Naples summer survival tips

**Format:** 1080x1920 (vertical), 15-60 seconds, MP4

**When approved:** Upload all videos at once

---

## Step 4: X (Twitter) - Already Working ✅

**Status:** ✅ Fully operational

**No action needed** - continue current automation (20-30 posts/day)

---

## Environment Variables Checklist

After all setups, your `.env` should have:

```bash
# X (Twitter) - EXISTING ✅
X_API_KEY="..."
X_API_SECRET="..."
X_ACCESS_TOKEN="..."
X_ACCESS_TOKEN_SECRET="..."

# Facebook - ADD TODAY ✅
FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
FACEBOOK_PAGE_ID="123456789"

# LinkedIn - ADD NOW (Client ID/Secret), ADD LATER (Access Token when approved)
LINKEDIN_CLIENT_ID="..."
LINKEDIN_CLIENT_SECRET="..."
# LINKEDIN_ACCESS_TOKEN="..." (after approval)

# TikTok - ADD WHEN APPROVED
# TIKTOK_ACCESS_TOKEN="..." (after approval)
```

---

## What You Can Post TODAY

### Facebook (Ready Now):
```bash
# Text post
python -m src.facebook_api test

# Or use multi-platform scheduler
python -m src.multi_platform_scheduler test
```

### X (Already Working):
Continue current automation

### LinkedIn (Ready in 2-4 weeks):
Wait for Marketing Developer Platform approval

### TikTok (Ready in 2-4 weeks):
Wait for audit approval

---

## Timeline

| Week | Task | Platform |
|------|------|----------|
| **Week 1 (NOW)** | Set up Facebook API | Facebook ✅ |
| **Week 1** | Apply for LinkedIn API | LinkedIn ⏳ |
| **Week 1** | Film 20-30 TikTok videos | TikTok 📹 |
| **Week 1** | Continue X automation | X ✅ |
| **Week 2-3** | Wait for approvals | LinkedIn, TikTok ⏳ |
| **Week 3-5** | LinkedIn approved | LinkedIn ✅ |
| **Week 3-5** | TikTok approved | TikTok ✅ |
| **Week 4+** | All platforms live! | All ✅ |

---

## Expected Results (After All Active)

**Month 1:**
- Facebook: 30-60 posts → 5-10 leads
- TikTok: 60-90 videos → 10-20 leads
- LinkedIn: 12-20 posts → 1-3 qualified leads
- X: 600-900 posts → 3-10 inquiries

**Combined:** 19-43 leads/month

**Revenue:** $29.5K-$110K/month (based on conversion rates)

**Cost:** $0/month (all free APIs)

---

## Troubleshooting

### Facebook: "Invalid OAuth Access Token"
**Fix:** Token expired - regenerate long-lived token (Step 1D)

### LinkedIn: "Insufficient permissions"
**Fix:** Wait for Marketing Developer Platform approval (2-4 weeks)

### TikTok: "Posts are private"
**Fix:** Wait for audit approval (posts will be public once approved)

---

## Next Steps

**RIGHT NOW (5 minutes):**
1. Open https://www.facebook.com/pages/create
2. Create SW Florida Comfort page
3. Start Step 1 above

**WITHIN 1 HOUR:**
4. Complete Facebook API setup
5. Test first post
6. Apply for LinkedIn API access

**THIS WEEK:**
7. Film 20-30 TikTok videos
8. Draft 30 LinkedIn posts
9. Plan Facebook content calendar

**WHEN APPROVED (2-4 weeks):**
10. Run LinkedIn OAuth flow
11. Upload TikTok videos
12. Full multi-platform automation live!

---

**Questions?** Check `API-SETUP-GUIDE.md` for detailed instructions.

**Ready?** Start with Facebook (Step 1) - takes 15 minutes!
