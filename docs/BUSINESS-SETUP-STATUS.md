# Business Setup Status - January 18, 2026

## Quick Summary

| Business | Website | Phone | Voice AI | Social | Logo |
|----------|---------|-------|----------|--------|------|
| Square Foot Shipping | ✅ Live | ✅ Active | ✅ Ready | ⏳ Needs Account | ✅ Created |
| SW Florida Comfort HVAC | ✅ Live | ✅ Active | ✅ Ready | ⏳ Needs Account | ✅ Created |

---

## Phone Numbers - READY TO TEST

Both phone numbers are configured and the voice AI server is running.

### Test the Phone Numbers Now:

**Square Foot Shipping & Storage**
```
📞 (239) 880-3365
```
- AI will greet: "Thank you for calling Square Foot Shipping and Storage!"
- Transfers to William George at (239) 692-1101 when requested

**SW Florida Comfort HVAC**
```
📞 (239) 766-6129
```
- AI will greet: "Thank you for calling SW Florida Comfort HVAC!"
- Treats AC emergencies with urgency
- Transfers to Bill (William Marceau Sr.) at (239) 398-7544 when requested

### Voice Server Status
- **Local Server**: Running on port 8000 ✅
- **Public URL**: https://cuddly-bryn-fiduciarily.ngrok-free.dev ✅
- **Twilio Webhooks**: Configured ✅

### Keep Voice AI Running
The ngrok tunnel needs to stay running for calls to work. If the server stops:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &
ngrok http 8000 --pooling-enabled
```

---

## Websites - LIVE

| Business | URL |
|----------|-----|
| Square Foot Shipping | https://wmarceau.github.io/squarefoot-shipping-website/ |
| SW Florida Comfort HVAC | https://wmarceau.github.io/swflorida-comfort-hvac/ |

---

## Logos - CREATED

Professional logos generated with Grok AI:

| Business | Logo File |
|----------|-----------|
| Square Foot | `/Users/williammarceaujr./squarefoot-shipping-website/assets/logo-grok.png` |
| SW Florida HVAC | `/Users/williammarceaujr./swflorida-comfort-hvac/assets/logo-grok.png` |

---

## 🔴 REQUIRES YOUR ACTION: X Account Setup

### Step 1: Create X Accounts (5 min each)

**Square Foot Shipping:**
1. Go to https://twitter.com/i/flow/signup
2. Use email: `wmarceau+squarefoot@marceausolutions.com` (or any email)
3. Set name: `Square Foot Shipping`
4. Try username: `@SquareFootShip`
5. Complete phone verification

**SW Florida Comfort HVAC:**
1. Go to https://twitter.com/i/flow/signup (incognito browser)
2. Use email: `wmarceau+hvac@marceausolutions.com`
3. Set name: `SW Florida Comfort HVAC`
4. Try username: `@SWFLComfortHVAC`
5. Complete phone verification (wait 24h if same phone)

### Step 2: Upload Logos
1. Go to Settings > Profile on each account
2. Upload the logo-grok.png files as profile pictures

### Step 3: Complete Profile Bios

**Square Foot Shipping:**
```
Professional logistics, warehouse storage & fulfillment in SW Florida. Climate-controlled storage, same-day delivery, 99% on-time rate. 📦
📞 (239) 880-3365
🌐 wmarceau.github.io/squarefoot-shipping-website
```

**SW Florida Comfort HVAC:**
```
AC repair, installation & maintenance in Naples, Fort Myers, Cape Coral. 24/7 emergency service, no overtime. Your Comfort, Our Mission. ❄️
📞 (239) 766-6129
🌐 wmarceau.github.io/swflorida-comfort-hvac
```

### Step 4: Get API Access (Optional - for automation)
1. Go to https://developer.twitter.com/
2. Create developer account for each business
3. Create an App and get API credentials
4. Add to .env file for automated posting

---

## Social Media Automation - READY

The automation system is built and ready:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# Generate content preview
python -m src.business_content_generator generate --business swflorida-hvac --count 5

# Run daily automation
python -m src.business_scheduler daily-run
```

Currently posts to your main X account. Once business accounts are created with API access, update the config to post to individual accounts.

---

## Costs Summary

| Item | Monthly Cost |
|------|--------------|
| Twilio - Square Foot | $1.15 |
| Twilio - HVAC | $1.15 |
| Twilio - Main Line | $1.15 |
| Voice AI (Claude API) | ~$5-15/mo per business |
| X Accounts | Free |
| GitHub Pages | Free |
| **Total** | ~$15-35/mo |

Account Balance: $36.92 USD

---

## Next Steps

1. **Test phone calls** - Call both numbers to verify AI works
2. **Create X accounts** - Follow guide above
3. **Set up cron job** for daily social media automation
4. **Monitor** - Track engagement and leads

---

## Files Reference

| Purpose | Location |
|---------|----------|
| Voice AI Config | `projects/ai-customer-service/src/business_voice_engine.py` |
| Social Media Config | `projects/social-media-automation/config/businesses.json` |
| Content Templates | `projects/social-media-automation/templates/business_content.json` |
| X Setup Guide | `docs/X-ACCOUNT-SETUP-GUIDE.md` |
| HVAC Logo | `swflorida-comfort-hvac/assets/logo-grok.png` |
| Shipping Logo | `squarefoot-shipping-website/assets/logo-grok.png` |

---

*Last Updated: January 18, 2026*
