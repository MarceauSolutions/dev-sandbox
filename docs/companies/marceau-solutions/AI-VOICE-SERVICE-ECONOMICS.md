# AI Voice Service Economics & Pricing Analysis

Last Updated: 2026-01-18

## Per-Client Cost Breakdown

### Fixed Costs (Monthly)

| Item | Cost | Notes |
|------|------|-------|
| Twilio Phone Number | $1.15/mo | Each client gets dedicated number |
| GitHub Pages Hosting | $0 | Free static website hosting |
| Domain (optional) | ~$1/mo | $12-15/year if client wants custom domain |
| **Subtotal Fixed** | **$1.15-2.15/mo** | |

### Variable Costs (Usage-Based)

| Item | Rate | Typical Usage | Est. Monthly |
|------|------|--------------|--------------|
| **Inbound Voice** | $0.0085/min | 200 min (40 calls × 5 min) | $1.70 |
| **Anthropic API** | ~$0.015/1k tokens | ~50k tokens (40 conversations) | $0.75 |
| **SMS** | $0.0079/msg | 20 msgs (confirmations) | $0.16 |
| **Subtotal Variable** | | | **~$2.61** |

### Total Cost Per Client

| Volume Level | Fixed | Variable | Total Cost/Mo |
|--------------|-------|----------|---------------|
| **Low** (20 calls/mo) | $1.15 | ~$1.30 | **~$2.45** |
| **Medium** (50 calls/mo) | $1.15 | ~$3.25 | **~$4.40** |
| **High** (100 calls/mo) | $1.15 | ~$6.50 | **~$7.65** |
| **Very High** (200 calls/mo) | $1.15 | ~$13.00 | **~$14.15** |

---

## Pricing Tiers (Proposed)

### Tier 1: Basic - $99/month
- **Includes**: AI phone answering, 100 minutes
- **Overage**: $0.15/minute
- **Your cost**: ~$4.40
- **Gross margin**: **$94.60 (95.5%)**

### Tier 2: Professional - $249/month
- **Includes**: AI phone + scheduling, 300 minutes, SMS confirmations
- **Overage**: $0.12/minute
- **Your cost**: ~$8.50
- **Gross margin**: **$240.50 (96.6%)**

### Tier 3: Enterprise - $499/month
- **Includes**: Everything + custom voice, priority support, 600 minutes
- **Overage**: $0.10/minute
- **Your cost**: ~$15.00
- **Gross margin**: **$484.00 (97.0%)**

---

## Setup Costs

### Equipment/Setup (One-Time per Client)

| Item | Time | Your Cost | Suggested Charge |
|------|------|-----------|------------------|
| **Phone Number Purchase** | 5 min | $1.15 | Included in setup |
| **Website Creation** | 2-4 hrs | $0 (your time) | $500-1,500 |
| **Voice AI Configuration** | 1-2 hrs | ~$1 (API testing) | Included |
| **Twilio Webhook Setup** | 30 min | $0 | Included |
| **Testing & QA** | 1 hr | ~$2 (test calls) | Included |
| **Training Call w/ Client** | 30 min | $0 | Included |
| **Total One-Time** | ~5-7 hrs | **~$4** | **$500-1,500** |

### Recommended Setup Fee Structure

| Service Level | Website | Voice AI | Setup Fee |
|---------------|---------|----------|-----------|
| **Basic** | Template site | Standard config | $299 |
| **Professional** | Custom site | Custom personality | $799 |
| **Enterprise** | Full custom | Custom + integrations | $1,999 |

---

## Take-Home Analysis

### Example: HVAC Client (SW Florida Comfort)

**If they pay $249/month:**

| Category | Amount |
|----------|--------|
| Monthly Revenue | $249.00 |
| Twilio Phone | -$1.15 |
| Twilio Voice (est. 150 min) | -$1.28 |
| Anthropic API (est. 30 calls) | -$0.45 |
| SMS (est. 10) | -$0.08 |
| **Total Costs** | **-$2.96** |
| **Net Take-Home** | **$246.04** |
| **Margin** | **98.8%** |

### Example: Shipping Client (Square Foot)

**If they pay $99/month:**

| Category | Amount |
|----------|--------|
| Monthly Revenue | $99.00 |
| Twilio Phone | -$1.15 |
| Twilio Voice (est. 50 min) | -$0.43 |
| Anthropic API (est. 15 calls) | -$0.23 |
| **Total Costs** | **-$1.81** |
| **Net Take-Home** | **$97.19** |
| **Margin** | **98.2%** |

---

## Scaling Economics

| Clients | Monthly Revenue | Total Costs | Net Take-Home |
|---------|-----------------|-------------|---------------|
| 1 | $249 | ~$3 | $246 |
| 5 | $1,245 | ~$15 | $1,230 |
| 10 | $2,490 | ~$30 | $2,460 |
| 25 | $6,225 | ~$75 | $6,150 |
| 50 | $12,450 | ~$150 | $12,300 |
| 100 | $24,900 | ~$300 | $24,600 |

**At 100 clients: ~98.8% margin, $24,600/month take-home**

---

## Hidden Costs to Consider

### Your Time (Opportunity Cost)

| Activity | Frequency | Time | Monetize? |
|----------|-----------|------|-----------|
| Client Onboarding | Per client | 2-4 hrs | Setup fee |
| Support/Troubleshooting | Ongoing | 1-2 hrs/mo/client | Include in pricing |
| System Updates | Monthly | 2-4 hrs | Amortize |
| Sales/Marketing | Ongoing | 10+ hrs/mo | CAC |

### Infrastructure (Currently Free)

| Item | Current | If You Scale |
|------|---------|--------------|
| Hosting | GitHub Pages (free) | Vercel Pro $20/mo at scale |
| Database | None (in-memory) | Supabase ~$25/mo |
| Monitoring | None | DataDog/Sentry ~$50/mo |
| Backup/DR | None | ~$10/mo |

---

## Should Equipment Setup Be Separate?

**Recommendation: YES, keep setup separate**

**Reasons:**
1. **Cleaner pricing** - clients understand one-time vs recurring
2. **Cash flow** - upfront payment covers your time
3. **Flexibility** - can offer setup discounts to close deals
4. **Value perception** - custom setup feels premium

**Pricing Suggestion:**
- **Setup fee**: $299-$1,999 (one-time)
- **Monthly service**: $99-$499 (recurring)

**Example Package:**
```
SW Florida Comfort HVAC Package:
- Setup Fee: $799 (website + voice AI configuration)
- Monthly Service: $249/month (Professional tier)
- Year 1 Total: $799 + ($249 × 12) = $3,787
- Your Cost Year 1: ~$4 + ($3 × 12) = ~$40
- Year 1 Take-Home: ~$3,747 (99% margin)
```

---

## Current Projects Cost Summary

### Active Demo/Test Accounts

| Business | Phone Cost | Status | Billing |
|----------|------------|--------|---------|
| Square Foot Shipping | $1.15/mo | Demo | Free (your project) |
| SW Florida Comfort HVAC | $1.15/mo | Demo | Free (your project) |
| Main Line (855) | $1.15/mo | Your personal | N/A |
| **Total** | **$3.45/mo** | | |

These are currently unpaid demos/tests. Once you convert them to paying clients, they become profit centers.

---

## Pricing Recommendation

**For William George (Square Foot):**
- Setup: $0 (friend/demo)
- Monthly: $99/month (Basic tier) OR $0 (continue as demo)

**For William Marceau Sr. (HVAC):**
- Setup: $0 (family)
- Monthly: $0 (keep as demo) OR $149/month (if he wants to pay)

**For Future Paying Clients:**
| Tier | Setup | Monthly | Annual Value |
|------|-------|---------|--------------|
| Basic | $299 | $99 | $1,487 |
| Professional | $799 | $249 | $3,787 |
| Enterprise | $1,999 | $499 | $7,987 |

---

## Summary

**Key Numbers:**
- **Cost per client**: $2-15/month (depending on usage)
- **Suggested pricing**: $99-499/month
- **Gross margin**: 95-99%
- **Setup costs**: ~$4 (materials) + your time
- **Setup fee**: $299-1,999

**Equipment is essentially free** - the only real costs are:
1. Twilio phone number ($1.15/mo)
2. Twilio usage (voice minutes, SMS)
3. Anthropic API (for AI responses)
4. Your time (price accordingly)
