# API Usage Cost Checker - January 2026

**Created:** 2026-01-19
**Purpose:** Track ALL API and service costs (not just Twilio)

---

## How to Check Each Service

### 1. Claude API (Anthropic) - USAGE-BASED

**Where to check:** https://console.anthropic.com/settings/billing

**Steps:**
1. Log in to Anthropic Console
2. Go to Settings → Billing
3. View "Current billing period" usage
4. Check for API calls made this month

**Expected cost:**
- Free tier: $5/month credit
- If using Claude Opus 4.5: ~$15-75/million tokens (input)
- If using Claude Sonnet 3.5: ~$3/million tokens (input)

**January 2026 usage:** $_______ (fill in after checking)

---

### 2. ngrok - AI WEBHOOK TUNNELING

**Where to check:** https://dashboard.ngrok.com/billing

**Steps:**
1. Log in to ngrok dashboard
2. Go to Billing section
3. Check current plan and usage

**Plans:**
- Free tier: 1 online ngrok process (enough for dev)
- Personal ($8/month): 3 online processes
- Pro ($20/month): 10 online processes

**Current plan:** _____________ (Free / Personal / Pro)
**January 2026 cost:** $_______ (fill in)

**Note:** If using free tier for AI webhook (`AI_CUSTOMER_SERVICE_BASE_URL=https://cuddly-bryn-fiduciarily.ngrok-free.dev`), cost is $0.

---

### 3. Apollo.io - LEAD ENRICHMENT

**Where to check:** https://app.apollo.io/#/settings/billing

**Steps:**
1. Log in to Apollo.io
2. Go to Settings → Billing
3. Check current plan and credit usage

**Plans:**
- Free tier: 50 credits/month (50 contact exports)
- Basic ($49/month): 1,200 credits/month
- Professional ($99/month): 12,000 credits/month

**API Key in .env:** `88ptiN7zpJrVc1hNP6rjVw`

**Current plan:** _____________ (Free / Basic / Professional)
**January 2026 cost:** $_______ (fill in)

---

### 4. Google Places API - LEAD SCRAPING

**Where to check:** https://console.cloud.google.com/billing

**Steps:**
1. Log in to Google Cloud Console
2. Select project: `fitness-influencer-assistant`
3. Go to Billing → Reports
4. Filter by: "Places API"

**Pricing:**
- Find Place: $0.017 per request
- Place Details: $0.017 per request
- First $200/month free (Google Cloud credit)

**API Key in .env:** `AIzaSyAViFkLMAp46vJo1CoXanVurYiFNXRp12w`

**January 2026 usage:** $_______ (fill in after checking)

---

### 5. Yelp Fusion API - BUSINESS DATA

**Where to check:** https://www.yelp.com/developers/v3/manage_app

**Cost:** FREE (5,000 calls/day limit)

**API Key in .env:** `mzsippSksP10-DHk5imVCbK-72_LJPKoOgG_AcCDP40LLvlbW4GfDgQHwFURij-TsajcqXR1lRAOoE3Wr2AZsw29Xo_ERGD_hp3u4nEPOQXxwPCN9ZLbVZd1EgZpaXYx`

**January 2026 cost:** $0.00 (free tier)

---

### 6. Shotstack - VIDEO GENERATION

**Where to check:** https://dashboard.shotstack.io/billing

**Steps:**
1. Log in to Shotstack
2. Go to Billing section
3. Check current usage and plan

**Plans:**
- Sandbox (free): 25 renders/month (watermarked)
- Starter ($29/month): 100 renders/month
- Creator ($99/month): 400 renders/month

**API Key in .env:** `mBwVD1lW1Us1MR2JAQRwh2lMEG4BAcTuZRK5uXtt`
**Environment:** `stage` (sandbox mode)

**Current plan:** _____________ (Sandbox / Starter / Creator)
**January 2026 cost:** $_______ (fill in)

---

### 7. xAI (Grok) - IMAGE GENERATION

**Where to check:** https://console.x.ai/billing

**Steps:**
1. Log in to xAI Console
2. Go to Billing section
3. Check API usage this month

**Pricing:**
- Grok Vision: ~$5 per 1M tokens
- Image generation: Usage-based

**API Key in .env:** `xai-jgczhiinOJQsu1PfjmRbKmCD6xYME0a9wQYe1RRhTuYK4axMdcANSqEsGyKeiNoKDt6or8nJtpIjfjUP`

**January 2026 usage:** $_______ (fill in after checking)

---

### 8. Creatomate - VIDEO GENERATION (CLOUD FALLBACK)

**Where to check:** https://creatomate.com/billing

**Steps:**
1. Log in to Creatomate
2. Go to Account → Billing
3. Check current plan and usage

**Plans:**
- Free tier: 25 renders/month (watermarked)
- Starter ($29/month): 100 renders/month
- Pro ($99/month): 500 renders/month

**API Key in .env:** `7b0f9c02f0f44111bc27221faa04bd008afba086f99576402587e886aceba4917ab0a393d5208b2aacfab18a091de08d`

**Current plan:** _____________ (Free / Starter / Pro)
**January 2026 cost:** $_______ (fill in)

---

### 9. X (Twitter) API - SOCIAL MEDIA

**Where to check:** https://developer.twitter.com/en/portal/dashboard

**Steps:**
1. Log in to Twitter Developer Portal
2. Go to Dashboard → Projects & Apps
3. Check current usage and plan

**Plans:**
- Free tier: Read-only, limited writes
- Basic ($100/month): 10,000 tweets/month
- Pro ($5,000/month): 1M tweets/month

**API Key in .env:** `Bs3zN32gG909jtjbx3sJBifR3`

**Current plan:** _____________ (Free / Basic / Pro)
**January 2026 cost:** $_______ (fill in)

---

### 10. YouTube API - VIDEO UPLOADS

**Where to check:** https://console.cloud.google.com/billing

**Cost:** FREE (quota-based, 10,000 units/day)

**Project:** `fitness-influencer-assistant`

**January 2026 cost:** $0.00 (free tier)

---

### 11. TikTok Content Posting API

**Where to check:** https://developers.tiktok.com/apps

**Cost:** FREE (sandbox mode)

**Client Key in .env:** `awztj4k9iysxawwy`

**January 2026 cost:** $0.00 (sandbox/free tier)

---

### 12. Amazon SP-API - SELLER OPERATIONS

**Where to check:** https://sellercentral.amazon.com/gp/homepage.html → Reports → Payments

**Cost:** FREE (no API fees, only Amazon selling fees)

**Marketplace:** US (ATVPDKIKX0DER)

**January 2026 cost:** $0.00 (no API fees)

---

## COMPREHENSIVE COST SUMMARY

Fill this in after checking all services above:

| Service | Plan/Tier | January Cost | Notes |
|---------|-----------|--------------|-------|
| **Twilio (SMS/Voice)** | Pay-as-you-go | $6.06 | ✅ Already tracked |
| **Domains (2)** | Annual | $2.00/month | ✅ Already tracked |
| **Google Workspace** | Business Starter | $6.00/month | ✅ Already tracked |
| **Claude API** | Usage-based | $_______ | ⬜ Check console.anthropic.com |
| **ngrok** | Free/Personal/Pro | $_______ | ⬜ Check dashboard.ngrok.com |
| **Apollo.io** | Free/Basic/Pro | $_______ | ⬜ Check app.apollo.io |
| **Google Places API** | Usage-based | $_______ | ⬜ Check console.cloud.google.com |
| **Yelp Fusion API** | Free | $0.00 | ✅ Free tier |
| **Shotstack** | Sandbox/Starter | $_______ | ⬜ Check dashboard.shotstack.io |
| **xAI/Grok** | Usage-based | $_______ | ⬜ Check console.x.ai |
| **Creatomate** | Free/Starter/Pro | $_______ | ⬜ Check creatomate.com |
| **X (Twitter) API** | Free/Basic/Pro | $_______ | ⬜ Check developer.twitter.com |
| **YouTube API** | Free | $0.00 | ✅ Free tier |
| **TikTok API** | Sandbox | $0.00 | ✅ Free tier |
| **Amazon SP-API** | Free | $0.00 | ✅ No API fees |
| **GitHub Pages** | Free | $0.00 | ✅ Free tier |
| **ClickUp CRM** | Free | $0.00 | ✅ Free tier |
| | | | |
| **KNOWN COSTS** | | **$14.06** | Already tracked |
| **UNKNOWN COSTS** | | **$??.??** | ⬜ Fill in above |
| | | | |
| **TOTAL JANUARY 2026** | | **$??.??** | Add up when complete |

---

## Action Items

1. ⬜ Check Claude API usage at console.anthropic.com
2. ⬜ Check ngrok plan at dashboard.ngrok.com
3. ⬜ Check Apollo.io credits at app.apollo.io
4. ⬜ Check Google Places API at console.cloud.google.com
5. ⬜ Check Shotstack renders at dashboard.shotstack.io
6. ⬜ Check xAI/Grok usage at console.x.ai
7. ⬜ Check Creatomate renders at creatomate.com
8. ⬜ Check X API usage at developer.twitter.com
9. ⬜ Fill in COMPREHENSIVE COST SUMMARY table above
10. ⬜ Update COST-BUDGET-TRACKING-JAN-19-2026.md with actual totals

---

## Quick Links

- Twilio: https://console.twilio.com/us1/monitor/logs/sms
- Claude API: https://console.anthropic.com/settings/billing
- ngrok: https://dashboard.ngrok.com/billing
- Apollo.io: https://app.apollo.io/#/settings/billing
- Google Cloud: https://console.cloud.google.com/billing
- Shotstack: https://dashboard.shotstack.io/billing
- xAI: https://console.x.ai/billing
- Creatomate: https://creatomate.com/billing
- X Developer: https://developer.twitter.com/en/portal/dashboard

---

**Next Step:** Check each service above and fill in actual costs, then run the updated cost tracker:

```bash
python -m src.check_actual_costs --detailed
```
