# Session Summary: Voice AI Strategy & Multi-Business Infrastructure

**Date:** 2026-01-18
**Focus:** Strategic planning, business configuration, marketing strategy

---

## ✅ Completed

### 1. Business Configuration Updates

**Updated** [/execution/form_handler/business_config.py](execution/form_handler/business_config.py):
- ✅ Changed HVAC owner email: `wjgeorge26@gmail.com` → `wmarceau@marceausolutions.com`
- ✅ Added `is_client_business` field to distinguish your business from client businesses
- ✅ Marked Marceau Solutions as `is_client_business=False` (YOUR business)
- ✅ Marked HVAC and Square Foot as `is_client_business=True` (CLIENT businesses)

**Current Business Setup:**

| Business | Type | Owner Email | ClickUp List | Status |
|----------|------|-------------|--------------|--------|
| **Marceau Solutions** | YOUR BUSINESS | wmarceau@marceausolutions.com | 901709132478 | ✅ Active |
| **SW Florida Comfort HVAC** | CLIENT | wmarceau@marceausolutions.com | 901709854724 | ✅ Active |
| **Square Foot Shipping** | CLIENT | wgeorge@squarefootshipping.com | 901709854725 | ✅ Active |

### 2. Marketing Strategy Document Created

**Created** [/docs/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md](docs/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md)

**Key Strategic Decisions:**

1. **Primary Focus: Voice AI**
   - Leverage existing HVAC case study
   - Target local Naples/Fort Myers businesses
   - High-value, high-touch service

2. **Business Model: Done-For-You Services**
   - Project pricing: $5K-10K setup
   - Recurring: $150-300/mo maintenance
   - Premium positioning (compete on results, not price)

3. **Revenue Goal: 8-10 Clients = $100K in 2026**
   - Mixed scenario: 3 × $10K + 5 × $5K = $55K projects
   - Recurring: 8 clients × $175/mo × 12 = $16.8K/year
   - **Total Year 1: ~$72K** (conservative)
   - Plus upsells: $10K-20K additional

4. **Time Allocation: Project-Dependent**
   - Client work when projects are active
   - Product development between projects
   - Flexible based on workload

### 3. Voice AI Action Plan (Q1 2026)

**Immediate Priorities (Next 2 Weeks):**
1. Polish HVAC case study (metrics, testimonial)
2. Create Voice AI landing page
3. Define Ideal Customer Profile
4. Build lead list (100 Naples businesses)

**Short-term (Next 30 Days):**
5. Launch cold outreach campaign (SOP 18)
6. Productize offering (3 packages: Starter, Professional, Enterprise)
7. Set up sales process (discovery script, demo, proposal, contract)

**Timeline to $100K:**
- **Month 1-2:** Case study, landing page, outreach → Close 1-2 clients ($10K-20K)
- **Month 3-4:** Deliver, refine, scale → Close 2-3 clients ($15K-25K)
- **Month 5-8:** Scale outreach (500+ prospects) → Close 3-4 clients ($25K-40K)
- **Month 9-12:** Upsells, referrals → Hit 8-10 clients, $100K+

### 4. API Server Restarted

**Status:** ✅ Running on port 8000
- Health check: `http://localhost:8000/api/form/health`
- 3 businesses configured
- All integrations active (ClickUp, email, SMS, Google Sheets)
- Public endpoint: `https://api.marceausolutions.com`

---

## 📋 Productized Voice AI Packages

| Package | Setup Fee | Monthly | Features |
|---------|-----------|---------|----------|
| **Starter** | $5,000 | $150 | Basic answering, FAQ, call forwarding |
| **Professional** | $8,000 | $200 | Full ordering, booking, CRM integration |
| **Enterprise** | $10,000+ | $300 | Multi-location, custom voices, analytics |

---

## 🎯 Marketing Positioning

**Positioning Statement:**
> "Marceau Solutions builds custom AI tools that automate your business operations - from voice AI to video editing to inventory management. If it's repetitive, we can automate it."

**Voice AI Value Prop:**
> "Never miss a customer call again. Our AI answers 24/7, takes orders, books appointments, and sends you qualified leads. From $5K."

**Branding:**
- **Colors:** Navy blue (#003366) + Bright orange (#FF6B35)
- **Fonts:** Montserrat (headings), Inter (body)
- **Tone:** Professional but approachable, results-focused, transparent

---

## 📊 Client Acquisition Math

**To hit $100K with Voice AI:**

**Realistic Mixed Scenario:**
- 3 Professional clients ($10K setup + $200/mo) = $30K + $7.2K/year
- 5 Starter clients ($5K setup + $150/mo) = $25K + $9K/year
- **Year 1 Total:** $71.2K
- **Year 2 Recurring:** $16.2K (if no churn)
- **Upsells:** Move Starter → Professional = $3K upgrade + $50/mo more

**With 20% upsell rate:**
- 1-2 upsells × $3K = $3K-6K additional
- **Year 1 Total: $74K-77K**

---

## 🔄 CRM Workflow (Already Implemented)

### For YOUR Business (Marceau Solutions):
1. Lead comes in via marceausolutions.com form
2. Goes to Main Leads List (901709132478)
3. Qualify → Move to "Active Deals"
4. Convert → Move to "Clients"
5. Manage project in ClickUp

### For CLIENT Businesses (HVAC, Square Foot):
1. Their customer submits form on their site
2. Goes to THEIR ClickUp list (you get notification)
3. You manage it for them (update status, add notes)
4. Send weekly report (leads summary + follow-ups)
5. They close the deal → Mark as won

**Future Opportunity:** "Lead Management as a Service"
- Offer $500-1K/month to manage their lead pipeline
- They get view-only ClickUp access
- You handle all automation + follow-up

---

## 🚀 Next Steps

### This Week:
- [ ] Create HVAC case study document (metrics + testimonial)
- [ ] Build Voice AI landing page (marceausolutions.com/voice-ai)
- [ ] Set up Google Analytics on marceausolutions.com
- [ ] Define 3 Voice AI packages (pricing, features, deliverables)

### Next Week:
- [ ] Build lead list (100 Naples restaurants/HVAC/home services)
- [ ] Create cold outreach SMS template
- [ ] Set up discovery call script
- [ ] Create demo workflow (show HVAC system live)

### Month 1 Goal:
- [ ] Launch outreach to 100 prospects
- [ ] Book 5-10 demo calls
- [ ] Send 3-5 proposals
- [ ] Close 1-2 clients ($10K-20K)

---

## 📁 Key Files Modified/Created

**Modified:**
- `/execution/form_handler/business_config.py` - Added `is_client_business` field

**Created:**
- `/docs/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md` - Full marketing strategy + action plan
- `/docs/SESSION-SUMMARY-2026-01-18.md` - This file

**Infrastructure:**
- API server running: `https://api.marceausolutions.com`
- 3 business configs active
- Form handlers ready for all websites

---

## 💡 Key Insights

1. **Focus beats breadth:** Voice AI + done-for-you is clearer than "we do everything"

2. **Case study is critical:** HVAC success story is your best sales tool

3. **Productize to scale:** 3 packages make pricing/scoping easier

4. **Local-first strategy:** Naples market is underserved, less competition

5. **Recurring revenue compounds:** $200/mo × 8 clients = $19.2K/year passive income by end of 2026

6. **CRM already built:** Multi-business infrastructure is production-ready

---

## 🎯 Success Metrics to Track

**Weekly:**
- SMS sent / responses / opt-outs
- Demo calls booked / attended
- Proposals sent / won / lost

**Monthly:**
- New clients signed
- Project revenue
- Recurring MRR (Monthly Recurring Revenue)
- Client satisfaction (NPS)

**Quarterly:**
- Total revenue vs goal ($25K/quarter to hit $100K)
- Client retention rate
- Avg deal size
- Sales cycle length (days from first contact → signed contract)

---

## 🔐 Security Note

**Anthropic Auth Code:** The token you shared was an authentication code from Anthropic (not a sensitive API key). These codes are one-time use and expire quickly, so no security risk.

For future reference:
- **API keys/tokens:** Add to `.env` file
- **Auth codes:** Safe to share (short-lived)
- **Passwords:** Never share in chat

---

## 📚 Reference Documents

- **Full Marketing Strategy:** [docs/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md](docs/MARCEAU-SOLUTIONS-MARKETING-STRATEGY.md)
- **Multi-Business Form System:** [docs/MULTI-BUSINESS-FORM-SYSTEM.md](docs/MULTI-BUSINESS-FORM-SYSTEM.md)
- **Business Config:** [execution/form_handler/business_config.py](execution/form_handler/business_config.py)
- **SOP 18:** SMS Campaign Execution
- **SOP 19:** Multi-Touch Follow-Up Sequence

---

**Status:** All systems operational. Ready to launch Voice AI client acquisition.

