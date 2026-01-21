# Google Cloud $100 Charge - Action Plan

**Created:** 2026-01-21
**Status:** 🔴 URGENT - Requires immediate verification
**Estimated Time:** 1-2 hours

---

## ✅ Quick Checklist

### Immediate (Next 30 Minutes)

- [ ] **Verify charge type** - Login to Google Cloud Console
  - Go to: https://console.cloud.google.com/billing
  - Select project: `fitness-influencer-assistant`
  - Check if $100 is "Credit" (Trust & Safety hold) or "Charge" (usage)

- [ ] **Check email** - Search for Trust & Safety messages
  - Search: `from:google-cloud-billing-support@google.com`
  - Search: `from:trust-and-safety@google.com`
  - Look for: "Account verification" or "$100 payment request"

- [ ] **Review billing transactions**
  - Go to: Billing → Transactions
  - Identify exact charge description
  - Take screenshot for records

---

### Today (1 Hour)

- [ ] **Set up billing alerts**
  - Navigate to: https://console.cloud.google.com/billing/budgets?project=fitness-influencer-assistant
  - Create 3 alerts:
    - Alert 1: $10 (50% of expected) → Email
    - Alert 2: $25 (warning) → Email + SMS
    - Alert 3: $50 (critical) → Email + SMS + Slack (optional)

- [ ] **Configure API quotas**
  - Go to: https://console.cloud.google.com/apis/api/places-backend.googleapis.com/quotas?project=fitness-influencer-assistant
  - Set daily limits:
    - Requests per day: 1,000 (prevent runaway costs)
    - Requests per 100 seconds: 100 (rate limiting)

- [ ] **Enable cost reports**
  - Billing → Reports → Export to BigQuery (optional)
  - Or: Set up daily email cost summary

---

### This Week (3-5 Hours)

- [ ] **Implement API caching**
  - File: `/projects/shared-multi-tenant/lead-scraper/src/google_places.py`
  - Add: 30-day cache for Place Details
  - Test: Run on 10 sample leads
  - Expected: 80% cost reduction

- [ ] **Switch to Yelp primary**
  - Refactor: Lead scraper to use Yelp API first
  - Fallback: Google Places only when Yelp doesn't have data
  - Expected: 70-90% reduction in Google API calls

- [ ] **Optimize search parameters**
  - Reduce: `radius_meters` from 25000 → 10000
  - Remove: Atmosphere fields if not critical
  - Test: Naples gym scraping campaign
  - Expected: 30-50% fewer API calls

- [ ] **Set up daily monitoring**
  - Add to cron: `python -m src.check_google_api_costs`
  - Schedule: 9:00 AM daily
  - Alert threshold: $5/day

---

## 📊 Expected Results

### Before Optimization
- Current usage: 1,022 API calls = $10.90/month
- If scaled 5x: 5,000 calls = $97.80/month
- Risk: Exceeds free tier after March 1, 2025

### After Optimization
- Caching: 80% reduction → 204 calls
- Yelp primary: 90% reduction → 102 calls
- Optimized fields: 33% savings → $3.40/month
- **Final cost:** $2-5/month (even at 5x scale)

---

## 🔗 Quick Links

### Google Cloud Console
- [Billing Reports](https://console.cloud.google.com/billing)
- [Budget Alerts](https://console.cloud.google.com/billing/budgets?project=fitness-influencer-assistant)
- [API Quotas](https://console.cloud.google.com/apis/api/places-backend.googleapis.com/quotas?project=fitness-influencer-assistant)
- [IAM & Admin](https://console.cloud.google.com/iam-admin?project=fitness-influencer-assistant)

### Cost Tracking
- [Full Cost Analysis](GOOGLE-CLOUD-COST-ANALYSIS.md)
- [Cost Tracker](COST-TRACKING.md)
- [API Usage Checker](companies/marceau-solutions/API-USAGE-COST-CHECKER.md)

### Tools
- Cost checker: `python -m src.check_google_api_costs --detailed`
- Twilio balance: `python -m src.check_actual_costs`

---

## 💡 Key Insights

### Most Likely Scenario: Trust & Safety Hold
- **Evidence:** $100 is exact verification amount
- **Action:** Check email for verification request
- **Outcome:** $100 becomes account credit (not a loss)

### Alternative Scenario: Usage Overage
- **Evidence:** Only $10.90 in actual usage
- **Conclusion:** UNLIKELY - usage too low for $100 charge

### Critical Date: March 1, 2025
- Google Maps Platform changes pricing model
- $200 monthly credit → Free usage caps
- Caps likely lower than current $200
- **Action:** Optimize NOW before price change

---

## 📞 Support Contacts

### Google Cloud Billing Support
- Email: google-cloud-billing-support@google.com
- Phone: 1-877-355-5787 (US)
- Chat: https://cloud.google.com/support

### Escalation
- If charge is fraudulent: File dispute with credit card
- If API quota exhausted: Request quota increase
- If Trust & Safety: Respond to verification email

---

## 🚀 Next Steps Summary

**RIGHT NOW:**
1. Check Google Cloud Console billing
2. Search email for Trust & Safety messages
3. Determine if $100 is hold or charge

**TODAY:**
4. Set billing alerts ($10, $25, $50)
5. Configure API quotas (1,000/day limit)
6. Run cost checker: `python -m src.check_google_api_costs`

**THIS WEEK:**
7. Implement caching (80% savings)
8. Switch to Yelp primary (90% savings)
9. Optimize search radius (50% savings)
10. Set up daily monitoring

**OUTCOME:**
- ✅ Understand what caused $100 charge
- ✅ Prevent future surprises with alerts
- ✅ Reduce API costs by 90%+
- ✅ Stay under free tier limits

---

**Status Updates:**

- [ ] Charge verified as: _________________ (Trust & Safety / Usage / Other)
- [ ] Billing alerts: _________________ (Configured / Pending)
- [ ] Caching implemented: _________________ (Complete / In progress)
- [ ] Monitoring enabled: _________________ (Yes / No)

**Total Time Investment:** ~5 hours for permanent fix
**Cost Savings:** ~$15-95/month (depending on scale)
**ROI:** High - prevents future billing surprises

---

**Last Updated:** 2026-01-21
**Next Review:** After Google Cloud Console verification
