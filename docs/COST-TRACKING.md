# Cost Tracking - All Projects

Last Updated: 2026-01-21

## 🚨 ALERT: $100 Google Cloud Charge Identified

**Status:** Under investigation
**Date:** January 2026
**Likely Cause:** Google Trust & Safety verification hold (not actual usage)
**Actual API Usage:** Only $10.90 in Google Places API calls

**Full Analysis:** See [GOOGLE-CLOUD-COST-ANALYSIS.md](GOOGLE-CLOUD-COST-ANALYSIS.md)

**Action Taken:**
- ✅ Cost analysis report created
- ✅ Billing alerts configured ($10, $25, $50 thresholds)
- ✅ API usage tracker deployed (`check_google_api_costs.py`)
- ⏳ Awaiting Google Cloud Console verification

---

## Twilio Account

**Account Balance**: $38.16 USD

### Phone Numbers (Monthly)

| Number | Business | Cost/Month | Purchased |
|--------|----------|------------|-----------|
| +1 (855) 239-9364 | Personal/Main | $1.15 | Pre-existing |
| +1 (239) 880-3365 | Square Foot Shipping & Storage | $1.15 | 2026-01-18 |
| +1 (239) 766-6129 | SW Florida Comfort HVAC | $1.15 | 2026-01-18 |
| **Total** | | **$3.45/mo** | |

### Usage Costs (Pay-per-use)

| Service | Rate | Notes |
|---------|------|-------|
| Inbound Voice | $0.0085/min | When someone calls |
| Outbound Voice | $0.014/min | When AI calls out |
| Inbound SMS | $0.0079/msg | Text received |
| Outbound SMS | $0.0079/msg | Text sent |

---

## GitHub (Free Tier)

| Service | Cost | Status |
|---------|------|--------|
| GitHub Pages - SquareFoot Shipping | $0 | Live: wmarceau.github.io/squarefoot-shipping-website |
| GitHub Pages - SW Florida HVAC | $0 | Live: wmarceau.github.io/swflorida-comfort-hvac |
| GitHub Pages - Personal | $0 | Existing |

---

## Expo/EAS (Free Tier)

| Service | Cost | Notes |
|---------|------|-------|
| Expo Go Development | $0 | Free for development builds |
| EAS Update (30/month) | $0 | Free tier includes 30 updates |
| EAS Build (30/month) | $0 | Free tier includes 30 builds |

---

## Apple Developer Program

| Service | Cost | Status |
|---------|------|--------|
| Apple Developer (Organization) | $99/year | Pending verification - Enrollment ID: 5949X3CZ65 |

---

## Pending/Future Costs

| Item | Estimated Cost | Status |
|------|---------------|--------|
| Domain: squarefootshipping.com | ~$12-15/year | Not purchased |
| Domain: swfloridacomfort.com | ~$12-15/year | Not purchased |
| Domain: cravesmart.app | ~$15-20/year | Not purchased |
| Email hosting (per business) | $0-6/user/month | Options: Zoho Free, Google Workspace |

---

## Monthly Summary

**Current Monthly Costs:**
- Twilio Phone Numbers: $3.45
- Hosting: $0 (GitHub Pages free)
- Development: $0 (Expo free tier)

**Total Fixed Monthly: ~$3.45**

**Annual:**
- Twilio: $41.40
- Apple Developer: $99.00
- Domains (estimated 3): ~$45.00
- **Total Annual: ~$185.40**

---

## Google Cloud Platform (New)

**Project:** `fitness-influencer-assistant`

### Active APIs

| API | Current Usage | Free Tier | Status |
|-----|---------------|-----------|--------|
| Google Places API | $10.90/month | $200/month credit | ✅ Under limit |
| YouTube Data API | 0 units | 10,000 units/day | ✅ Free |
| Gmail API | Free (OAuth) | Unlimited | ✅ Free |
| Google Sheets API | Free (OAuth) | Unlimited | ✅ Free |
| Google Calendar API | Free (OAuth) | Unlimited | ✅ Free |

### API Usage Details

**Google Places API (Lead Scraper):**
- Leads scraped: 409 businesses
- Estimated API calls: 1,022 requests
- Breakdown:
  - Nearby Search: 21 calls × $32/1K = $0.67
  - Place Details: 409 calls × $25/1K = $10.22
- **Total cost:** $10.90/month (5.4% of free tier)

**Cost-Saving Measures:**
- Implement caching (80% reduction) → Target: $2-3/month
- Use Yelp API as primary (free, 5K calls/day)
- Reduce search radius 25km → 10km (50% reduction)

**Monitoring:**
- Daily cost checks: `python -m src.check_google_api_costs`
- Billing alerts: $10, $25, $50 thresholds
- API quotas: 1,000 requests/day limit

---

## Cost-Saving Notes

1. **GitHub Pages**: Free hosting for static sites (unlimited)
2. **Expo Free Tier**: 30 builds + 30 updates/month sufficient for development
3. **Zoho Mail**: Free for up to 5 users per domain
4. **Twilio**: Pay-as-you-go, only charged for actual usage
5. **Voice AI**: Uses Anthropic API from existing subscription (already paid)
6. **Google Places API**: $200/month free tier until March 1, 2025
7. **Yelp API**: Free (5,000 calls/day) - use as primary source
