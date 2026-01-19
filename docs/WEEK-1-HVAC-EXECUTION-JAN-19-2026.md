# Week 1 Execution Plan - HVAC Agency Launch

**Week:** Jan 19-25, 2026
**Phase:** 1 (Agency Services)
**Goal:** Install Voice AI on Sr.'s business + prepare first outreach campaign

---

## Day 1-2: Monday-Tuesday (Jan 19-20)
**Focus:** Set up Voice AI infrastructure for case study

### Actions:

**1. Configure Voice AI for Sr.'s Business**
- [ ] Access Twilio account (phone: +1 855 239 9364)
- [ ] Set up call forwarding from Sr.'s business line to Voice AI
- [ ] Configure AI voice prompts for HVAC scenarios:
  - Emergency calls (AC out, heater broken)
  - Routine maintenance requests
  - New customer inquiries
  - Existing customer questions
- [ ] Test call flow (call from your phone, verify AI answers correctly)

**2. Set Up Call Tracking**
- [ ] Enable call recording in Twilio
- [ ] Create tracking spreadsheet:
  - Date/time of call
  - Call type (emergency, routine, inquiry)
  - AI handled successfully? (Yes/No)
  - Appointment booked? (Yes/No)
  - Estimated job value
- [ ] Set up daily summary email (calls received, appointments booked)

**3. Brief Sr. on Case Study**
- [ ] Explain: "We're tracking results for 2 weeks"
- [ ] Ask: "Tell me immediately if AI mishandles a call"
- [ ] Request: Access to his calendar to verify appointments booked

### Success Criteria:
- ✅ Voice AI answers calls on Sr.'s business line
- ✅ Call tracking operational
- ✅ Sr. briefed and onboard

---

## Day 3-4: Wednesday-Thursday (Jan 21-22)
**Focus:** Build target list for first outreach campaign

### Actions:

**1. Scrape 100 Naples HVAC Companies**

Run lead scraper:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

python -m src.scraper scrape \
  --type business \
  --industry hvac \
  --location "Naples, FL" \
  --radius 15 \
  --limit 100 \
  --output output/hvac_naples_jan19.json
```

**2. Filter and Qualify Leads**

Criteria:
- [ ] Business size: 5-20 employees (check Google reviews count, photos, etc.)
- [ ] Established: 10+ years in business (avoid brand new companies)
- [ ] Website quality: Basic/no website OR terrible website (opportunity to help)
- [ ] Location: Service areas overlapping with Naples/Bonita/Fort Myers

Create filtered list:
```bash
python -m src.scraper filter \
  --input output/hvac_naples_jan19.json \
  --min-reviews 10 \
  --max-reviews 500 \
  --output output/hvac_qualified_leads.json
```

**3. Enrich Lead Data**

- [ ] Add phone numbers (if missing)
- [ ] Add owner names (if available)
- [ ] Check if they have website
- [ ] Note any public pain points (Google reviews mentioning "can't reach them", "never answer phone")

**4. Draft SMS Template**

Create template (will customize with Sr.'s results next week):

```
Hi {owner_name}, this is William from Marceau Solutions.

I just helped {Sr.'s business name} recover [X] missed emergency calls in the past week using Voice AI.

Their customers now get answered 24/7, even when technicians are on job sites.

Would you be open to a free "missed calls audit" to see how much revenue you might be losing?

Reply YES for more info.

Reply STOP to opt out.
```

**Note:** Don't send yet - wait for Week 1 results from Sr.'s business to fill in real numbers.

### Success Criteria:
- ✅ 100 HVAC companies scraped
- ✅ 30-50 qualified leads (filtered list)
- ✅ SMS template drafted (ready to customize)

---

## Day 5-7: Friday-Sunday (Jan 23-25)
**Focus:** Review Week 1 data + prepare Week 2

### Actions:

**1. Review Call Data from Sr.'s Business**

Pull from tracking spreadsheet:
- Total calls received
- Calls answered by AI vs missed
- Appointments booked
- Estimated revenue from booked jobs
- Any AI failures (escalations, confused customers)

**Example metrics to look for:**
- "15 calls this week, AI answered 14 (93% answer rate)"
- "3 emergency appointments booked = estimated $2,500-$4,000 revenue"
- "2 routine maintenance calls = $500-$800"

**2. Document Early Wins**

Create case study outline (even with partial data):

```markdown
# Case Study: SW Florida Comfort HVAC - Week 1

## The Problem
- Missing 30-40% of calls when technicians on job sites
- Lost revenue estimated at $50K-$100K annually
- No after-hours coverage (customers call competitors)

## The Solution
- Voice AI installed on main business line
- 24/7 call answering and appointment booking
- Emergency vs routine call routing

## Week 1 Results (Jan 19-25, 2026)
- Calls received: 15
- Calls answered: 14 (93%)
- Appointments booked: 3 emergency + 2 routine
- Estimated revenue recovered: $3,000-$4,800
- Extrapolated annual impact: $156K-$250K

## Customer Feedback
- [Quote from Sr. if available]
- [Quote from customer who used AI if available]
```

**3. Refine SMS Template with Real Data**

Update template with actual numbers:

```
Hi {owner_name}, this is William from Marceau Solutions.

I just helped SW Florida Comfort HVAC recover 14 missed calls in one week using Voice AI - that's $3,000-$4,800 in jobs that would've gone to competitors.

Their customers now get answered 24/7, even when technicians are on job sites.

Would you be open to a free "missed calls audit" for your business?

Reply YES for details.

Reply STOP to opt out.
```

**4. Plan Week 2 Outreach**

- [ ] Review budget ($5 for 500 SMS = $0.01 each)
- [ ] Target: Send to 30-50 qualified leads (cost: $0.30-$0.50)
- [ ] Schedule: Tuesday-Wednesday of Week 2
- [ ] Expected: 5-10 replies, 2-3 discovery calls, 0-1 signed client

### Success Criteria:
- ✅ Week 1 call data reviewed
- ✅ Case study outline created (even partial data)
- ✅ SMS template updated with real numbers
- ✅ Week 2 outreach plan ready

---

## Budget Tracking

**Week 1 Costs:**
- Voice AI (Twilio): ~$5-10 (call minutes + recording)
- Lead scraping (Google Places API): $0 (free tier)
- SMS (not sent yet): $0
- **Total Week 1:** ~$5-10

**Month 1 Budget:** $50-100
**Remaining:** $40-90

---

## Risk Mitigation

**Risk 1: Sr.'s business doesn't get many calls in Week 1**
- **Mitigation:** Extend to Week 2 before sending outreach
- **Backup:** Use hypothetical numbers based on industry average ("HVAC companies typically receive 20-30 calls/week")

**Risk 2: AI fails on emergency call**
- **Mitigation:** Have Sr. monitor closely, escalate to human if needed
- **Backup:** Document failure, fix prompt, retest

**Risk 3: Not enough qualified leads in Naples**
- **Mitigation:** Expand to Bonita Springs, Fort Myers (10 miles radius)
- **Backup:** 500+ HVAC companies in SW Florida metro

---

## Daily Check-In Questions

**Each day, review:**
1. How many calls did Sr.'s business receive today?
2. Did AI handle them correctly?
3. Were any appointments booked?
4. Any issues to fix?

**End of week review:**
1. Do we have enough data for a compelling case study?
2. Is the SMS template ready with real numbers?
3. Are we ready for Week 2 outreach?

---

## Week 2 Preview (Jan 26 - Feb 1)

**If Week 1 goes well:**
- Send SMS to 30-50 HVAC companies
- Book 2-3 discovery calls
- Offer free "missed calls audit"
- Target: 1 signed contract by end of Week 2

**If Week 1 needs more data:**
- Extend case study to Week 2
- Refine AI prompts based on failures
- Send outreach in Week 3 instead

---

## Tools Needed

**Already have:**
- ✅ Twilio account (SMS + Voice)
- ✅ Lead scraper
- ✅ Google Places API access

**Need to set up:**
- [ ] Call tracking spreadsheet
- [ ] Daily summary automation (optional)
- [ ] Case study template

---

## Success Metrics (Week 1)

**Primary Metrics:**
- Calls received on Sr.'s business line: Target 10-20
- AI answer rate: Target >90%
- Appointments booked: Target 2-5
- Estimated revenue: Target $1,000-$5,000

**Secondary Metrics:**
- HVAC companies scraped: Target 100
- Qualified leads: Target 30-50
- SMS template completed: Yes/No

**Ultimate Goal:**
- ✅ Compelling case study ready for Week 2 outreach

---

## Next Steps After Week 1

**If successful (2+ appointments booked via AI):**
- Week 2: Send SMS outreach (30-50 companies)
- Week 3: Discovery calls + proposals
- Week 4: Close first paying client

**If needs improvement (<2 appointments):**
- Week 2: Refine AI prompts, extend case study
- Week 3: Send outreach with 2-week data
- Week 4: Discovery calls + proposals

---

## Bottom Line

**This week:** Set up infrastructure + gather proof
**Next week:** Use proof to acquire first client
**This month:** $15K setup fee + $3K/month retainer

Focus: Make Sr.'s Voice AI so successful that selling to other HVAC companies becomes easy.

Let's execute. 🚀
