# Voice AI Cold Outreach SMS Templates

**For use with SOP 18 (SMS Campaign Execution)**

---

## Template Guidelines

**TCPA Compliance:**
- ✅ B2B exemption (business numbers only)
- ✅ Include sender name ("This is William")
- ✅ Include opt-out ("Reply STOP to opt out")
- ✅ Send during business hours only (8 AM - 9 PM local time)

**Best Practices:**
- Keep under 160 characters when possible
- Personalize with {business_name}
- Lead with value, not pitch
- Clear CTA (reply, call, book)
- Professional but conversational tone

---

## Initial Outreach Templates

### Template 1: Case Study Lead (RECOMMENDED)

```
Hi {owner_name}, this is William from Marceau Solutions.

I helped a Naples HVAC company capture $12K in new revenue their first month using Voice AI to answer calls 24/7.

Would a 5-min call to see if this could work for {business_name} be helpful?

Reply STOP to opt out.
```

**Character count:** 259 (over 160, will split into 2 SMS)
**Use for:** All industries
**Strength:** Social proof + specific results

---

### Template 2: Pain Point (Missed Calls)

```
{owner_name} - William from Marceau Solutions.

Quick question: How many customer calls does {business_name} miss during busy times or after hours?

Most Naples businesses lose 30-40%. We built AI that answers 24/7.

Interested in 5-min demo?

STOP to opt out
```

**Character count:** 252
**Use for:** Restaurants, HVAC, home services
**Strength:** Leads with pain point

---

### Template 3: Direct Value

```
{owner_name}, I'm William - I build AI phone systems for Naples businesses.

Your competitor uses voicemail. You could use AI that books appointments 24/7.

5-min demo?

Text YES or call (239) 398-5676

STOP to opt out
```

**Character count:** 222
**Use for:** Competitive industries (restaurants)
**Strength:** Competitive angle

---

### Template 4: After-Hours Focus

```
Hi {owner_name}, William from Marceau Solutions here.

How many emergency calls does {business_name} miss after 6 PM?

I built Voice AI for a Naples HVAC company - they're now capturing $3K+/month in after-hours jobs they used to lose.

Interested?

STOP to opt out
```

**Character count:** 257
**Use for:** HVAC, plumbing, emergency services
**Strength:** Quantified after-hours opportunity

---

## Follow-Up Sequence (SOP 19)

### Follow-Up #1 (Day 2): Still Looking

```
{owner_name}, following up on my message about Voice AI for {business_name}.

Still exploring options to handle more calls without hiring?

Here's a 2-min case study: [link]

Let me know if helpful.

- William
STOP to opt out
```

---

### Follow-Up #2 (Day 5): Social Proof

```
Quick update {owner_name} -

Just helped another Naples business set up Voice AI. They booked 15 appointments in the first week without touching the phone.

Would this help {business_name}?

Reply YES for demo.

- William
STOP to opt out
```

---

### Follow-Up #3 (Day 10): Direct Question

```
{owner_name}, honest question:

If Voice AI could book appointments 24/7 and never miss a call, would you invest $8K to set it up?

If yes, let's talk. If no, I'll stop bothering you.

- William
(239) 398-5676

STOP to opt out
```

---

### Follow-Up #4 (Day 15): Availability

```
{owner_name}, last follow-up:

I have 2 slots this month for new Voice AI setups.

If you want to stop missing calls at {business_name}, I can get you live by February.

Free demo: [calendly link]

- William
STOP to opt out
```

---

### Follow-Up #5 (Day 30): Breakup

```
{owner_name}, looks like timing isn't right for Voice AI at {business_name}.

No worries - if you ever want to see how it works, you know where to find me.

Best of luck!
- William

STOP to opt out
```

---

### Follow-Up #6 (Day 60): Re-engage

```
{owner_name}, been a couple months.

Still handling all your calls manually at {business_name}?

We've helped 3 more Naples businesses go live since we last talked. Results have been incredible.

Want to see it in action?

- William
STOP to opt out
```

---

## Response Handlers

### If they reply "YES" or "Interested"

```
Great! I'll call you in the next hour to schedule a quick demo.

Or you can book directly: https://calendly.com/wmarceau/voice-ai-demo

What's the best number to reach you?

- William
```

---

### If they reply "MORE INFO"

```
Perfect. Here's what Voice AI does:

✅ Answers 24/7 (never miss a call)
✅ Books appointments automatically
✅ Routes emergencies to your phone
✅ Captures every lead in your CRM

Case study: [link]

When can I call you for 5-min demo?

- William
```

---

### If they reply "HOW MUCH"

```
Great question. 3 packages:

Starter: $5K setup + $150/mo
Professional: $8K + $200/mo ⭐ Most popular
Enterprise: $10K+ + $300/mo

Most Naples businesses go with Professional.

Can I show you what you'd get? 5-min call?

- William
```

---

### If they reply "NOT INTERESTED"

```
No problem, {owner_name}. Thanks for letting me know.

If anything changes and you want to see Voice AI in action, feel free to reach out.

Best,
William
```

*[Mark in CRM: Not interested - Don't contact again]*

---

### If they reply "STOP" or "UNSUBSCRIBE"

**DO NOT REPLY**

*[System automatically adds to opt-out list per TCPA compliance]*

---

## Campaign Setup (Using SOP 18)

### Step 1: Prepare Lead List

```bash
# Use lead scraper to find 100 Naples businesses
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

python -m src.scraper google \
    --query "HVAC Naples FL" \
    --limit 50 \
    --output hvac_leads.json

python -m src.scraper google \
    --query "restaurants Naples FL" \
    --limit 50 \
    --output restaurant_leads.json
```

---

### Step 2: Create Campaign

```bash
# Create follow-up sequence campaign
python -m src.follow_up_sequence create \
    --name "Voice AI HVAC Jan 2026" \
    --pain-point missed_calls \
    --limit 50
```

---

### Step 3: Dry Run Test

```bash
# ALWAYS test first
python -m src.scraper sms \
    --dry-run \
    --limit 5 \
    --template voice_ai_case_study
```

---

### Step 4: Small Batch Launch

```bash
# Send to 10 leads first
python -m src.scraper sms \
    --for-real \
    --limit 10 \
    --pain-point missed_calls
```

Wait 24-48 hours. Check:
- Delivery rate (should be >95%)
- Reply rate (expect 2-5%)
- Opt-out rate (should be <2%)

---

### Step 5: Full Campaign

```bash
# If small batch successful, scale up
python -m src.scraper sms \
    --for-real \
    --limit 100 \
    --pain-point missed_calls
```

---

## A/B Testing Strategy (SOP 23)

### Test #1: Case Study vs Pain Point

**Control (50 leads):** Template 1 (Case Study)
**Variant (50 leads):** Template 2 (Pain Point)

**Hypothesis:** Case study with specific $ results will get higher reply rate

**Run for:** 7 days
**Track:** Reply rate, demo bookings

---

### Test #2: Short vs Long

**Control (50 leads):** Template 3 (Direct, 222 chars)
**Variant (50 leads):** Template 1 (Case Study, 259 chars)

**Hypothesis:** Shorter messages get higher reply rate

**Run for:** 7 days
**Track:** Reply rate, quality of responses

---

### Test #3: Industry-Specific

**HVAC leads:** Template 4 (After-hours focus)
**Restaurant leads:** Template 3 (Competitor angle)

**Hypothesis:** Industry-specific messaging converts better than generic

**Run for:** 7 days
**Track:** Reply rate, demo bookings, close rate

---

## Campaign Analytics (SOP 22)

### Track Weekly:

```bash
# View campaign report
python -m src.campaign_analytics report \
    --campaign "Voice AI HVAC Jan 2026"

# Compare templates
python -m src.campaign_analytics templates

# View conversion funnel
python -m src.campaign_analytics funnel
```

### Success Metrics:

| Metric | Target | Good | Great |
|--------|--------|------|-------|
| **Delivery Rate** | >95% | 97% | 99% |
| **Reply Rate** | 3-5% | 5-7% | >10% |
| **Opt-out Rate** | <3% | <2% | <1% |
| **Demo Booking Rate** | 1-2% | 2-3% | >3% |
| **Demo Show Rate** | 60% | 70% | 80% |
| **Close Rate** | 20% | 30% | 40% |

### ROI Calculation:

**Example Campaign:**
- 100 SMS sent × $0.01 = $1
- 5 replies (5% reply rate)
- 2 demos booked (2% booking rate)
- 1 demo shows (50% show rate)
- 1 closes (100% close rate from show, 50% from booking)
- 1 client × $8,000 = $8,000 revenue

**ROI: $8,000 / $1 = 800,000%**

Even with 10% close rate: $800 revenue / $1 = 80,000% ROI

---

## Legal & Compliance

### ✅ Safe to Send:

- Business phone numbers (HVAC, restaurants, professional services)
- B2B communication (business-to-business)
- Messages sent 8 AM - 9 PM local time
- Clear opt-out instructions
- Sender identified

### ❌ DO NOT Send:

- Consumer cell phones (residential numbers)
- Before 8 AM or after 9 PM
- After recipient says STOP
- Without clear sender identification
- False or misleading claims

### TCPA Compliance Checklist:

- [ ] Only B2B (business numbers)
- [ ] Sender identified ("This is William")
- [ ] Opt-out included ("STOP to opt out")
- [ ] Sent during business hours
- [ ] No false claims
- [ ] Opt-out list maintained
- [ ] Records kept for 4 years

---

## Winning Template Rotation

As you run campaigns, rotate your top performers:

**Week 1:** Template 1 (Case Study) - Baseline
**Week 2:** Template 2 (Pain Point) - A/B Test
**Week 3:** Winning template from Week 1-2
**Week 4:** Template 4 (After-hours) - New test

**Keep testing, keep improving.**

Goal: Increase reply rate from 3% → 5% → 10% over 3 months through continuous optimization.

---

**Remember:** Quality over quantity. 100 targeted messages to the right businesses will outperform 1,000 spray-and-pray messages.

