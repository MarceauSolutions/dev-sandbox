# How to Get Your Creatomate API Key

## Step-by-Step Walkthrough

### 1. Sign Up for Creatomate

Go to: **https://creatomate.com/**

Click "Sign Up" or "Get Started"

### 2. Choose Your Plan

**Free Tier (Recommended to Start):**
- 25 videos/month free
- Perfect for testing
- No credit card required initially

**Paid Plans (If needed later):**
- Starter: $49/month (1,000 videos)
- Pro: $149/month (5,000 videos)
- Or pay-as-you-go: $0.05 per video

**Recommendation:** Start with free tier to test, upgrade only if you consistently hit 200+ videos/month

### 3. Verify Your Email

Check your email for verification link from Creatomate and click it.

### 4. Access Your Dashboard

After logging in, you'll see the Creatomate dashboard.

### 5. Get Your API Key

**Option A: From Dashboard**
1. Click on your profile/account icon (top right)
2. Select "API Keys" or "Settings"
3. Look for "API Key" section
4. Click "Generate API Key" or "Show API Key"
5. Copy the key (starts with something like `sk_...`)

**Option B: From Settings**
1. Go to Settings → API
2. Find "API Key" or "Authentication"
3. Copy your API key

### 6. Add to Your .env File

Once you have the key:

```bash
# Open your .env file
nano .env  # or use your text editor

# Add this line:
CREATOMATE_API_KEY=your_actual_key_here

# Save and close
```

### 7. Verify It Works (Later)

After setup is complete, test with:
```bash
python execution/intelligent_video_router.py \
  --images "https://picsum.photos/1080/1920,https://picsum.photos/1080/1920" \
  --headline "Test" \
  --cta "Works!" \
  --force creatomate
```

---

## Important Notes

### API Key Security
- ✅ Keep your API key in `.env` file (already in `.gitignore`)
- ✅ Never commit API keys to git
- ✅ Never share API keys publicly

### Free Tier Limits
- 25 videos/month free
- After that: $0.05 per video
- Monitor usage in Creatomate dashboard

### When Do You Need It?
- **Optional for testing** - System works with MoviePy only
- **Recommended for production** - Provides reliable fallback
- **Required for complex videos** - Long text, special characters, etc.

### If You Don't Get It Now
- System will work with MoviePy only (free)
- 100% of videos will try MoviePy
- Some complex videos may fail
- You can add it later at any time

---

## Troubleshooting

**Can't find API key section?**
- Look for "Settings" → "API" → "Authentication"
- Or "Account" → "API Keys"
- Or "Developer" → "API"

**API key not working?**
- Make sure you copied the entire key
- Check for extra spaces
- Verify it's in `.env` file with correct format: `CREATOMATE_API_KEY=sk_...`
- Restart any running scripts after adding key

**Want to test without it?**
- Skip this step for now
- System will use MoviePy only
- Add Creatomate key later when needed

---

## Next Steps After Getting Key

1. Add key to `.env` file
2. Let me know when done
3. I'll test the system with both methods
4. You'll see analytics showing MoviePy vs Creatomate usage

**Estimated time:** 5-10 minutes