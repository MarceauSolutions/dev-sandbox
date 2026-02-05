# 36-Month Financial Projection: Peptide-Focused Personal Training Business

**Created:** 2026-02-05
**Location:** Naples, FL
**Business Model:** Personal Training + Peptide Education (Educator + Referral Partner Model)

---

## Executive Summary

| Metric | Year 1 | Year 2 | Year 3 | 36-Month Total |
|--------|--------|--------|--------|----------------|
| **Total Personal Expenses** | $55,800 | $57,492 | $59,217 | $172,509 |
| **Total Business Expenses** | $4,887 | $3,588 | $3,659 | $12,134 |
| **Combined Total** | $60,687 | $61,080 | $62,876 | $184,643 |
| **Monthly Burn Rate (Avg)** | $5,057 | $5,090 | $5,240 | - |

**Key Insight:** By leveraging existing tools we've built and free alternatives, business costs are kept to **$100-150/month** ongoing vs. industry average of **$400-800/month**.

---

## Part 1: Personal Expenses (Monthly)

### Fixed Expenses (User Provided + Estimated)

| Category | Monthly | Annual | Notes |
|----------|---------|--------|-------|
| **Rent** | $2,200 | $26,400 | User provided |
| **Food** | $1,000 | $12,000 | User provided |
| **Car Payment** | $400 | $4,800 | Est. avg for reliable vehicle |
| **Car Insurance** | $150 | $1,800 | FL average for good driver |
| **Gas** | $200 | $2,400 | Mobile trainer, ~15K miles/year |
| **Phone** | $80 | $960 | Business line important |
| **Internet** | $70 | $840 | Work-from-home essential |
| **Health Insurance** | $350 | $4,200 | Self-employed, marketplace plan |
| **Utilities** | $150 | $1,800 | Electric, water (FL is higher) |
| **Subscriptions (Personal)** | $50 | $600 | Streaming, gym membership |
| **Clothing/Personal Care** | $100 | $1,200 | Professional appearance |
| **Miscellaneous** | $200 | $2,400 | Buffer for unexpected |
| **TOTAL PERSONAL** | **$4,950** | **$59,400** | |

### Year-Over-Year Adjustment (3% Inflation)

| Year | Monthly | Annual |
|------|---------|--------|
| Year 1 | $4,650 (ramp-up) | $55,800 |
| Year 2 | $4,791 | $57,492 |
| Year 3 | $4,935 | $59,217 |

---

## Part 2: Business Startup Costs (One-Time)

### Required (Minimum Viable)

| Item | Cost | Notes |
|------|------|-------|
| **ISSA CPT Certification** | $948 | You have materials; exam fee included |
| **CPR/AED Certification** | $15 | Online course, 2-year validity |
| **Florida LLC Formation** | $125 | Articles of Organization |
| **Business Tax Receipt (Naples/Collier)** | $75 | Local business license |
| **Equipment (Mobile Training Kit)** | $500 | Bands, mat, adjustable DBs, TRX, bag |
| **Legal Disclaimer Templates** | $99 | Wellness coaching disclaimers |
| **Domain Name** | $15 | marceaufitness.com or similar |
| **Initial Marketing Materials** | $100 | Business cards, basic branding |
| **TOTAL STARTUP** | **$1,877** | |

### Optional (Recommended)

| Item | Cost | Notes |
|------|------|-------|
| **Peptide Education Course** | $500 | Knowledge building (not certification for non-MDs) |
| **Additional Equipment** | $400 | Kettlebells, foam roller, assessment tools |
| **Professional Photos** | $200 | For website/social (or DIY with good phone) |
| **Website Development** | $0 | Build ourselves or use Carrd free tier |
| **TOTAL OPTIONAL** | **$1,100** | |

---

## Part 3: Business Monthly Operating Costs

### Essential Monthly Costs

| Category | Monthly | Annual | Notes |
|----------|---------|--------|-------|
| **Insurance (GL + PL)** | $17 | $200 | NEXT Insurance combined policy |
| **Website Hosting** | $5 | $60 | Hostinger or similar |
| **Payment Processing** | ~$30 | ~$360 | Stripe fees on $1K revenue (2.9%) |
| **Google Workspace** | $6 | $72 | Professional email |
| **Twilio SMS** | $10 | $120 | Client reminders, already configured |
| **TOTAL ESSENTIAL** | **$68** | **$812** | |

### Tools We Already Have (ZERO Additional Cost)

| Tool | Purpose | Alternative Cost Avoided |
|------|---------|--------------------------|
| **Email System** | gmail_monitor.py, SMTP configured | $13/mo (Mailchimp) |
| **SMS System** | twilio_sms.py, inbox_monitor.py | $15/mo (SimpleTexting) |
| **CRM** | ClickUp API integration, lead_manager.py | $20/mo (HubSpot Starter) |
| **Video Generation** | shotstack_api.py, grok_video_gen.py | $20/mo (Canva Pro) |
| **Image Generation** | grok_image_gen.py | $10/mo (AI tools) |
| **PDF Generation** | markdown_to_pdf.py | $12/mo (tools) |
| **Analytics** | revenue_analytics.py | $15/mo (analytics tools) |
| **Calendar Integration** | calendar_reminders.py, calendly_monitor.py | $12/mo (Calendly paid) |
| **Video Editing Automation** | video_jumpcut.py | $23/mo (Premiere Pro) |
| **Scheduling** | Calendly Free tier | $0 |
| **CRM** | ClickUp Free tier (configured) | $0 |
| **SAVINGS FROM EXISTING TOOLS** | | **$140+/month avoided** |

### Tools to Build (Instead of Buy)

| Tool Needed | Build Cost | Alternative Paid Cost | Priority |
|-------------|------------|----------------------|----------|
| **Client Portal** | 3-5 days work | $60/mo (Trainerize) | Medium |
| **Workout PDF Generator** | 1-2 days work | $20/mo | High |
| **Video Batch Processor** | 1-2 days work | $23/mo (Premiere) | High |
| **Email Drip Sequences** | 2-3 days work | $13/mo | Medium |
| **Content Scheduler** | 2-3 days work | $25/mo (Later) | Low |

**Total Build Time:** ~2 weeks of focused development
**Monthly Savings After Build:** $141/month = $1,692/year

---

## Part 4: Free Tools Strategy

### Use These Free Tiers (Don't Build)

| Category | Tool | Why Free Tier Works |
|----------|------|---------------------|
| **Scheduling** | Calendly Free or Cal.com | 1 event type sufficient to start |
| **CRM** | HubSpot Free | 1M contacts, more than enough |
| **Email Marketing** | Kit (ConvertKit) Free | 10,000 subscribers FREE |
| **Social Scheduling** | Buffer Free | 3 channels, 10 posts each |
| **Video Editing** | DaVinci Resolve | Professional-grade, completely free |
| **Design** | Canva Free | Most features available |
| **Invoicing** | Stripe Dashboard | Built-in invoicing |

### Don't Buy These (Common Mistakes)

| Tool Category | Typical Cost | Our Alternative |
|---------------|--------------|-----------------|
| Trainerize/TrueCoach | $60-100/mo | Google Sheets + Custom Python |
| Adobe Creative Cloud | $55/mo | DaVinci Resolve + Canva Free |
| Social Media Suite | $50-100/mo | Buffer Free + Native scheduling |
| Email Platform (Paid) | $30-100/mo | Kit Free (10K subs) + Custom |
| CRM (Paid) | $50-200/mo | HubSpot Free + ClickUp |

**Total Monthly Savings:** $245-555/month vs. typical fitness business

---

## Part 5: Revenue Projections

### Service Pricing (Naples Market - Premium)

| Service | Price | Sessions/Month | Monthly Revenue |
|---------|-------|----------------|-----------------|
| **1-on-1 Training Session** | $100 | Variable | - |
| **4-Session Package** | $380 | - | - |
| **8-Session Package** | $720 | - | - |
| **Online Coaching (Monthly)** | $299 | - | - |
| **Peptide Education Consult** | $150/hr | - | - |
| **Group Training (4 people)** | $40/person | - | - |

### Revenue Ramp-Up Projection

| Month | Clients | Sessions | Gross Revenue | Net (After Fees) |
|-------|---------|----------|---------------|------------------|
| 1-3 | 3-5 | 20 | $2,000 | $1,940 |
| 4-6 | 8-10 | 40 | $4,000 | $3,880 |
| 7-9 | 12-15 | 60 | $6,000 | $5,820 |
| 10-12 | 15-20 | 80 | $8,000 | $7,760 |
| Year 2 Avg | 20-25 | 100 | $10,000 | $9,700 |
| Year 3 Avg | 25-30 | 120+ | $12,000+ | $11,640+ |

### Additional Revenue Streams

| Stream | Potential Monthly | Notes |
|--------|-------------------|-------|
| **Clinic Referral Commissions** | $200-500 | 15-20% on peptide clinic referrals |
| **Digital Products** | $100-300 | Workout guides, meal plans |
| **Affiliate Marketing** | $50-200 | Supplement, equipment recommendations |
| **Group Programs** | $500-1,000 | 6-week challenges, bootcamps |

---

## Part 6: 36-Month Cash Flow Projection

### Year 1 (Months 1-12)

| Category | M1-3 (Startup) | M4-6 | M7-9 | M10-12 | Y1 Total |
|----------|----------------|------|------|--------|----------|
| **Personal Expenses** | $13,950 | $13,950 | $13,950 | $13,950 | $55,800 |
| **Business Startup** | $1,877 | - | - | - | $1,877 |
| **Business Operating** | $204 | $204 | $204 | $204 | $816 |
| **Business Development** | $600 | $400 | $400 | $400 | $1,800 |
| **Marketing** | $150 | $100 | $100 | $44 | $394 |
| **TOTAL EXPENSES** | $16,781 | $14,654 | $14,654 | $14,598 | $60,687 |
| **Revenue** | $6,000 | $12,000 | $18,000 | $24,000 | $60,000 |
| **Net Cash Flow** | -$10,781 | -$2,654 | $3,346 | $9,402 | -$687 |
| **Cumulative** | -$10,781 | -$13,435 | -$10,089 | -$687 | -$687 |

### Year 2 (Months 13-24)

| Quarter | Expenses | Revenue | Net | Cumulative |
|---------|----------|---------|-----|------------|
| Q1 (M13-15) | $14,793 | $27,000 | $12,207 | $11,520 |
| Q2 (M16-18) | $14,793 | $30,000 | $15,207 | $26,727 |
| Q3 (M19-21) | $14,793 | $30,000 | $15,207 | $41,934 |
| Q4 (M22-24) | $15,327 | $33,000 | $17,673 | $59,607 |
| **Y2 Total** | $59,706 | $120,000 | $60,294 | - |

### Year 3 (Months 25-36)

| Quarter | Expenses | Revenue | Net | Cumulative |
|---------|----------|---------|-----|------------|
| Q1 (M25-27) | $15,500 | $36,000 | $20,500 | $80,107 |
| Q2 (M28-30) | $15,500 | $36,000 | $20,500 | $100,607 |
| Q3 (M31-33) | $15,500 | $39,000 | $23,500 | $124,107 |
| Q4 (M34-36) | $15,876 | $42,000 | $26,124 | $150,231 |
| **Y3 Total** | $62,376 | $153,000 | $90,624 | - |

### 36-Month Summary

| Metric | Amount |
|--------|--------|
| **Total Expenses (36 months)** | $182,769 |
| **Total Revenue (36 months)** | $333,000 |
| **Total Net Profit** | $150,231 |
| **Break-Even Month** | Month 9-10 |
| **Average Monthly Profit (Y2-3)** | $6,288 |

---

## Part 7: Startup Capital Required

### Conservative Estimate

| Category | Amount | Notes |
|----------|--------|-------|
| **Business Startup Costs** | $1,877 | One-time setup |
| **6-Month Personal Runway** | $29,700 | Until business profitable |
| **Emergency Fund** | $5,000 | Unexpected expenses |
| **Marketing Reserve** | $1,000 | Initial client acquisition |
| **TOTAL REQUIRED** | **$37,577** | |

### Aggressive (Minimum Viable)

| Category | Amount | Notes |
|----------|--------|-------|
| **Business Startup** | $1,500 | Absolute minimum |
| **3-Month Personal Runway** | $14,850 | Faster revenue ramp needed |
| **Small Buffer** | $2,000 | Tight margins |
| **TOTAL MINIMUM** | **$18,350** | High risk |

### Recommended Approach

**$40,000 in savings** before starting allows:
- 6 months without income pressure
- Professional setup (better equipment, branding)
- Marketing investment for faster client acquisition
- Breathing room for unexpected costs

---

## Part 8: Existing Infrastructure Inventory

### APIs & Integrations Already Configured

| Service | Purpose | Monthly Cost | Already Paid |
|---------|---------|--------------|--------------|
| **Twilio** | SMS campaigns, client reminders | Usage-based | Yes |
| **Google APIs** | Gmail, Calendar, Sheets, OAuth | Free | Yes |
| **ClickUp** | CRM, task management | Free tier | Yes |
| **Stripe** | Payment processing | 2.9% per transaction | Yes |
| **Shotstack** | Video generation | Usage-based | Yes |
| **Creatomate** | Video generation (backup) | Usage-based | Yes |
| **XAI/Grok** | Image generation | Usage-based | Yes |
| **Apollo** | Lead enrichment | Usage-based | Yes |

### Execution Scripts Ready to Use

| Script | Function | Replaces |
|--------|----------|----------|
| `twilio_sms.py` | SMS automation | $15/mo SMS platform |
| `gmail_monitor.py` | Email automation | $13/mo Mailchimp |
| `lead_manager.py` | Lead tracking | $20/mo CRM |
| `calendar_reminders.py` | Scheduling reminders | $12/mo tool |
| `revenue_analytics.py` | Financial tracking | $15/mo analytics |
| `video_jumpcut.py` | Video editing automation | Manual editing time |
| `markdown_to_pdf.py` | Document generation | $12/mo PDF tools |
| `stripe_payments.py` | Payment automation | Custom dev |

### Total Monthly Savings from Built Tools: **$87-140+/month**
### Annual Savings: **$1,044-1,680/year**

---

## Part 9: Build vs Buy Decision Matrix

### HIGH PRIORITY BUILDS (Do These First)

| Tool | Build Time | Monthly Savings | ROI |
|------|------------|-----------------|-----|
| **Workout PDF Generator** | 1-2 days | $20 | 10x in 30 days |
| **Video Batch Processor (FFmpeg)** | 1-2 days | $23 | 11x in 30 days |
| **Client Check-in Automation** | 1 day | Time savings | Immediate |
| **Email Drip Sequences** | 2-3 days | $13 | 4x in 30 days |

### MEDIUM PRIORITY (After Revenue Flowing)

| Tool | Build Time | Notes |
|------|------------|-------|
| **Client Portal (Streamlit)** | 3-5 days | Differentiation, professional image |
| **Custom Booking System** | 2-3 days | Only if Calendly limits become issue |
| **Content Calendar Automation** | 2-3 days | After content strategy solidified |

### LOW PRIORITY (Use Free Tools Instead)

| Category | Free Solution | Don't Build |
|----------|---------------|-------------|
| **CRM** | HubSpot Free | Database from scratch |
| **Scheduling** | Cal.com / Calendly | Booking system |
| **Payment** | Stripe | Payment gateway |

---

## Part 10: Risk Factors & Mitigations

### Financial Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Slower client acquisition | Cash flow pressure | 6-month runway, aggressive networking |
| Equipment damage/theft | Replacement costs | Insurance coverage, backup equipment |
| Seasonal fluctuation | Revenue drops (summer) | Online coaching, snowbird marketing |
| Competition | Price pressure | Niche differentiation (peptide education) |

### Legal Risks (Peptide Coaching)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope of practice violation | Lawsuits, license issues | Heavy disclaimers, education-only model |
| Client injury | Liability claims | Proper insurance, referral to clinics |
| Insurance coverage gap | Policy void | Confirm coverage with provider |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tool dependency | Business disruption | Own your data, backup systems |
| API changes | Broken automation | Modular architecture, easy swaps |
| Time management | Burnout | Automation, boundaries |

---

## Part 11: Key Metrics to Track

### Monthly Review

| Metric | Target Y1 | Target Y2 | Target Y3 |
|--------|-----------|-----------|-----------|
| **Active Clients** | 15 | 25 | 35 |
| **Sessions/Month** | 60 | 100 | 140 |
| **Revenue** | $6,000 | $10,000 | $14,000 |
| **Client Acquisition Cost** | <$50 | <$40 | <$30 |
| **Client Retention (Monthly)** | >85% | >90% | >90% |
| **Referral Rate** | 20% | 30% | 40% |

### Quarterly Review

- Revenue vs projection
- Expense variance
- Tool usage (are we using what we built?)
- Client feedback/NPS
- Referral source analysis

---

## Conclusion

### Total 36-Month Financial Requirement

| Category | Amount |
|----------|--------|
| **Startup Capital Needed** | $40,000 |
| **Total Expenses (36 mo)** | $182,769 |
| **Projected Revenue (36 mo)** | $333,000 |
| **Net Position (36 mo)** | +$150,231 |

### Key Success Factors

1. **Leverage existing tools** - $1,680/year savings from what we've already built
2. **Use free tiers strategically** - $2,000+/year savings from smart tool selection
3. **Build only high-ROI tools** - Focus development time on real savings
4. **Naples premium market** - Higher rates justify quality service
5. **Peptide niche differentiation** - Education model creates unique positioning

### Next Steps

1. [ ] Finalize startup capital ($37-40K target)
2. [ ] Complete ISSA certification exam
3. [ ] Form Florida LLC
4. [ ] Get insurance quotes
5. [ ] Build high-priority automation tools (1-2 weeks)
6. [ ] Launch with 3-5 beta clients
7. [ ] Iterate based on feedback

---

*Document created: 2026-02-05*
*Review frequency: Monthly*
*Next review: 2026-03-05*
