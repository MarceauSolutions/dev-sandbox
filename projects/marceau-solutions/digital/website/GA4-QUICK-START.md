# GA4 Quick Start

**3 Steps to Activate Google Analytics on Marceau Solutions Website**

---

## Step 1: Get Your Measurement ID

1. Go to: **https://analytics.google.com**
2. Sign in: **wmarceau@marceausolutions.com**
3. Create account: **"Marceau Solutions"**
4. Create property: **"Marceau Solutions Website"**
   - URL: `https://marceausolutions.com`
   - Time Zone: Eastern Time
5. Copy the **Measurement ID** (format: `G-XXXXXXXXXX`)

**Don't have an account yet?** See detailed setup: [GA4-ACTIVATION-GUIDE.md](GA4-ACTIVATION-GUIDE.md#1-create-google-analytics-account--property)

---

## Step 2: Activate GA4 on Website

```bash
cd /Users/williammarceaujr./marceausolutions.com
./activate-ga4.sh G-XXXXXXXXXX
```

**What this does:**
- ✅ Validates Measurement ID format
- ✅ Creates backup of all HTML files
- ✅ Uncomments GA4 code in all 5 HTML files
- ✅ Replaces placeholder with your real ID

---

## Step 3: Deploy & Verify

```bash
# Review changes
git diff

# Commit and push
git add -A
git commit -m "feat: Activate GA4 tracking (G-XXXXXXXXXX)"
git push
```

**Verify (30-60 seconds after deployment):**
1. Go to: https://analytics.google.com
2. Click: **Reports** → **Real-time**
3. Visit: https://marceausolutions.com
4. Watch your visit appear in Real-time report ✅

---

## What Gets Tracked

**Automatic:**
- Page views
- Sessions
- Traffic sources
- Geographic data
- Device type

**Custom Events:**
- Form submissions (`form_submission`)
- Email opt-ins (`opt_in_email`)
- SMS opt-ins (`opt_in_sms`)

**See full event list:** [GA4-EVENTS-TRACKING.md](GA4-EVENTS-TRACKING.md)

---

## Need Help?

- **Detailed Guide:** [GA4-ACTIVATION-GUIDE.md](GA4-ACTIVATION-GUIDE.md) (8 sections, troubleshooting, advanced config)
- **Event Reference:** [GA4-EVENTS-TRACKING.md](GA4-EVENTS-TRACKING.md) (all tracked events + parameters)
- **GA4 Support:** https://support.google.com/analytics

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `activate-ga4.sh` | One-command activation script |
| `GA4-QUICK-START.md` | This file (3-step guide) |
| `GA4-ACTIVATION-GUIDE.md` | Comprehensive setup guide |
| `GA4-EVENTS-TRACKING.md` | Event tracking reference |

---

**Ready?** Run: `./activate-ga4.sh G-XXXXXXXXXX` 🚀
