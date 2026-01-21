# Facebook API Setup - Existing Page

**Your Status:** ✅ Facebook page already exists for SW Florida Comfort
**Next Step:** Connect it to the API (10 minutes)

---

## Quick Setup for Existing Facebook Page

### Step 1: Create Facebook Developer App (5 minutes)

1. **Go to:** https://developers.facebook.com/
2. **Login** with your Facebook account (same one that manages SW Florida Comfort page)
3. **Click:** "My Apps" (top right)
4. **Click:** "Create App"
5. **Select:** "Business" as app type
6. **Fill in:**
   - **App Display Name:** SW Florida Comfort Automation
   - **App Contact Email:** wmarceau@marceausolutions.com
   - **Business Account:** (create new if you don't have one)
7. **Click:** "Create App"

---

### Step 2: Get Page Access Token (5 minutes)

#### A. Add Your Page to the App

1. In your new app dashboard, go to: **Settings** → **Basic**
2. Copy your **App ID** and **App Secret** (you'll need these)

#### B. Use Graph API Explorer

1. In your app, go to: **Tools** → **Graph API Explorer**
2. **Top dropdown:** Select your new app ("SW Florida Comfort Automation")
3. **User or Page dropdown:** Select "SW Florida Comfort" page
4. **Permissions:** Click "Add a Permission" and add:
   - `pages_manage_posts` (required for posting)
   - `pages_read_engagement` (for analytics)
   - `pages_show_list` (to list your pages)
5. **Click:** "Generate Access Token"
6. **Authorize:** Grant the permissions
7. **Copy the token:** It starts with `EAA...` (this is temporary, we'll make it permanent)

---

### Step 3: Make Token Permanent (Never Expires)

Open Terminal and run these commands:

```bash
# Set your values (replace with actual values from Step 2)
APP_ID="YOUR_APP_ID"              # From Settings → Basic
APP_SECRET="YOUR_APP_SECRET"      # From Settings → Basic
SHORT_TOKEN="YOUR_TOKEN_FROM_B"   # From Graph API Explorer

# Step 3A: Get long-lived user token (60 days)
curl "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$APP_SECRET&fb_exchange_token=$SHORT_TOKEN"
```

**Output:** You'll get a JSON response like:
```json
{
  "access_token": "EAAxxxxx...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

**Copy the `access_token` value**, then run:

```bash
# Step 3B: Get permanent page token (never expires)
USER_TOKEN="PASTE_TOKEN_FROM_ABOVE"

curl "https://graph.facebook.com/v18.0/me/accounts?access_token=$USER_TOKEN"
```

**Output:** You'll get a JSON response with all your pages:
```json
{
  "data": [
    {
      "access_token": "EAAyyyyyy...",
      "category": "Heating, Ventilating & Air Conditioning Service",
      "name": "SW Florida Comfort",
      "id": "123456789",
      "tasks": ["ANALYZE", "ADVERTISE", "MODERATE", "CREATE_CONTENT", "MANAGE"]
    }
  ]
}
```

**Copy:**
- `access_token` - This is your **permanent page token** (never expires!)
- `id` - This is your **page ID**

---

### Step 4: Add to .env File

```bash
# Open your .env file
open /Users/williammarceaujr./dev-sandbox/.env

# Add these lines (replace with your actual values):
FACEBOOK_PAGE_ACCESS_TOKEN="EAAyyyyyy..."
FACEBOOK_PAGE_ID="123456789"
```

Save and close the file.

---

### Step 5: Test Posting

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python -m src.facebook_api test
```

**Expected Output:**
```
✅ Posted to Facebook: 123456789_987654321
✅ Test successful!
Post ID: 123456789_987654321
View at: https://www.facebook.com/123456789_987654321
```

**Check your SW Florida Comfort Facebook page** - you should see a test post!

---

## What You Can Do Now

### Post Text:
```bash
python -c "
from src.facebook_api import FacebookAPI
api = FacebookAPI()
api.create_text_post(
    message='❄️ Need AC repair in Naples? Call (239) 766-6129 for same-day service!',
    link='https://www.swfloridacomfort.com'
)
"
```

### Post Photo:
```bash
python -c "
from src.facebook_api import FacebookAPI
api = FacebookAPI()
api.create_photo_post(
    image_path='/path/to/your/image.jpg',
    caption='Before/After AC unit transformation! 🌟'
)
"
```

### Post Video:
```bash
python -c "
from src.facebook_api import FacebookAPI
api = FacebookAPI()
api.create_video_post(
    video_path='/path/to/your/video.mp4',
    description='Watch how we replaced this AC unit in 2 hours!'
)
"
```

---

## Troubleshooting

### "Invalid OAuth Access Token"
**Cause:** Token expired or incorrect
**Fix:**
1. Make sure you completed Step 3B (permanent page token)
2. Verify you copied the `access_token` from the **me/accounts** response, not the first token

### "Permissions Error"
**Cause:** Missing permissions
**Fix:**
1. Go back to Graph API Explorer
2. Add permissions: `pages_manage_posts`, `pages_read_engagement`
3. Generate new token
4. Repeat Step 3

### "Page Not Found"
**Cause:** Wrong page ID
**Fix:**
1. Check the `id` field from Step 3B
2. Make sure it matches your SW Florida Comfort page

---

## Security Notes

**Important:**
- ✅ Page Access Token is permanent (never expires)
- ✅ Token is in `.env` which is gitignored (not committed)
- ✅ Only has access to SW Florida Comfort page (not your personal profile)
- ✅ Only has posting permissions (can't access messages or private data)

**Keep the token secure:**
- Never commit `.env` to git
- Never share the token publicly
- If compromised, regenerate from Graph API Explorer

---

## Next Steps After Testing

Once your test post works:

1. **Set up LinkedIn API** (follow [QUICK-START.md](QUICK-START.md) Step 2)
2. **Film TikTok videos** (20-30 videos to stockpile)
3. **Draft Facebook content calendar** (30 posts for Month 1)

---

## Summary

**What you just did:**
1. ✅ Created Facebook Developer App
2. ✅ Connected your existing SW Florida Comfort page
3. ✅ Got permanent API access token
4. ✅ Tested posting via API

**What you can do now:**
- Post to Facebook page via Python scripts
- Schedule posts programmatically
- Automate content publishing
- Track analytics via API

**Cost:** $0 (free Facebook API)

**Ready for:** Full automation when you create content calendar!

---

**Next:** Follow [QUICK-START.md](QUICK-START.md) Step 2 to set up LinkedIn API!
