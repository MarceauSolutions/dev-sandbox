# AI Phone Agent — Go-To-Market Plan
**Marceau Solutions | Created: May 10, 2026**
**Execution window: Evenings & weekends starting May 12, 2026**

---

## EXECUTIVE SUMMARY

Production-deployed AI receptionist. Zero build time remaining. Market charges $255–$1,275/month for human virtual receptionists. At $297–$497/month, William operates at 80–85% gross margin. Path to $3,000/month recurring = 8–10 clients in 60–90 days. Constraint is sales and onboarding time — this plan minimizes both.

---

## 1. PRICING STRUCTURE

### TIER 1 — STARTER | $297/month + $299 setup
- 24/7 inbound call handling (unlimited calls)
- Caller qualification (up to 3 qualifying questions)
- Voicemail-to-Telegram alerts, same-day
- Standard AI voice (ElevenLabs neural)
- Up to 2 phone numbers routed
- Monthly call summary report (n8n auto-generated)
- **Target:** Solo HVAC tech, solo plumber, 1-chair med spa

### TIER 2 — PRO | $497/month + $499 setup
Everything in Starter, plus:
- Custom voice persona (name + personality tailored to brand)
- Warm transfer to up to 3 numbers
- Missed-call SMS follow-up to caller (n8n automation)
- Business hours logic (day vs. night behavior)
- Bi-weekly 15-min check-in with William
- Priority support (4-hour response, 7 days/week)
- **Target:** 3–8 truck HVAC company, plumbing outfit with dispatcher

### TIER 3 — BUNDLE "Always-On Lead Machine" | $697/month + $799 setup
Everything in Pro, plus:
- Full n8n follow-up automation (5-step: SMS + email after missed call, review request)
- Weekly reporting PDF (branded PDF engine)
- Custom on-hold messaging
- Dedicated Twilio number managed by William
- Monthly 30-min strategy call
- **Target:** Multi-location contractor, growing med spa with staff

### Margin Table
| Tier | Price | COGS | Gross Margin |
|------|-------|------|-------------|
| Starter | $297 | $65 | $232 (78%) |
| Pro | $497 | $80 | $417 (84%) |
| Bundle | $697 | $107 | $590 (85%) |

**10-client revenue (5 Starter + 3 Pro + 2 Bundle): ~$4,570 MRR at 82% blended margin**

---

## 2. TARGET CUSTOMER PROFILE (ICP)

**Primary ICP: The Overwhelmed Owner-Operator**

- Business type: HVAC, plumbing, electrical contracting, med spa
- Geography: Collier County, Lee County, Charlotte County (Naples, Bonita Springs, Cape Coral, Fort Myers)
- Revenue: $500K–$3M/year
- Employees: 2–12 (owner + 1–3 techs, maybe an office person)
- Phone volume: 15–50 inbound calls/day
- Current solution: Owner's cell phone, spouse answering, or nothing after hours
- Pain: Losing leads to competitors who answer faster; frustrated by 9pm "emergency" calls

**Disqualify if:**
- Already has a full-time receptionist
- Wants live calendar scheduling via API (scope creep)
- Franchise requiring corporate vendor approval
- Revenue under $250K/year

**Lead sources (priority order):**
1. Collier County contractor network (William's warmest channel — use first)
2. Google Maps — local HVAC/plumbing with 50+ reviews, no "after hours" mention
3. Apollo.io cold outreach (already configured)
4. Facebook Groups — "SWFL Business Owners," "Naples/Marco Island Business Network"

---

## 3. OUTREACH SEQUENCE

### SMS (existing Twilio/EC2 setup)

**SMS 1 — Day 0**
> Hey {first_name}, William here in Naples — quick Q: how do you handle calls when you're on a job? Most {trade_type} owners I know are losing 3–5 leads/day from missed calls. I built a 24/7 AI receptionist — want to see how it works? Takes 5 min.

**SMS 2 — Day 3**
> {first_name} — 74% of contractor calls go unanswered. Average missed call costs ~$450. My AI answers every call, qualifies the lead, and texts you immediately. Live demo is 5 minutes — want me to call you this week?

**SMS 3 — Day 7**
> Last one, {first_name} — bringing on 2 more Naples contractors this month, wanted to give {business_name} first look. Call (239) 398-5676 or reply "YES" for a quick demo. No pressure either way.

### Email (n8n Gmail — existing infrastructure)

**Email 1 — Day 1** | Subject: Your phones after 5pm — {business_name}
- Personal intro as local Naples builder
- 4-bullet breakdown of what the AI does
- "Call (855) 239-9364 right now to hear it" — makes the demo immediate
- ROI math: missing 3 calls/day = $40K–$60K/year at typical job values
- CTA: 15-minute call, can meet in person

**Email 2 — Day 5** | Subject: What happened when [local contractor] stopped missing calls
- Social proof (use own experience until first client testimonial)
- Step-by-step walkthrough of exactly what happens on a call
- "I have capacity for 2 more Naples clients this month"
- CTA: 10-minute demo call

**Email 3 — Day 10** | Subject: Closing your file — {business_name}
- Final touch, no pressure
- Waive $299 setup fee for the first client this month (urgency + risk reversal)
- 30-day money-back guarantee
- Leave door open: "reach me when it becomes a priority"

---

## 4. DEMO SCRIPT

### Pre-call setup (5 min before)
- Second phone ready to call (855) 239-9364
- Prospect's business name and trade type pulled up
- Pricing PDF open
- Calendly ready for close

### The Live Demo (the centerpiece — do this on EVERY call)
> "Can you do me a favor and call this number right now from your phone — (855) 239-9364. That's my actual business line. I'll stay on with you. Just listen to how it handles the call."

Let them go through the full flow. After they hang up:
> "So that's the actual system. Same one I'd set up for {business_name}. What did you notice?"

### Qualification questions
- "What does your phone situation look like right now?"
- "What's your average job value — roughly?"
- "If we captured 2 extra jobs a month you'd have missed, that's {2x job value}. This runs $297/month. Does that math make sense?"

### The Close
> "Here's how it works. I send a one-page agreement, you pay the setup fee, I do all the work. 45 minutes of your time total. In about a week you're live. Want me to send that over today?"

---

## 5. OBJECTION HANDLING

| Objection | Response |
|-----------|----------|
| "Customers won't like a robot" | "Call (855) 239-9364 right now. Most people can't tell. And voicemail is already worse than this." |
| "How is it different from a phone tree?" | "Phone trees say press 1. This has a conversation — understands natural language, routes differently based on what they say." |
| "I already have someone answering calls" | "During hours, great. What about evenings, weekends, lunch? AI works alongside your person — covers the gaps, never calls in sick." |
| "What if it says something wrong?" | "It only says what I program it to say. Anything outside that: 'let me have someone call you right back.' I monitor it — if it breaks, I know first." |
| "$297 seems like a lot" | "Let's do the math. {job value} × 2 missed jobs/month = {amount}. Service costs $297. You need 0.6 jobs to break even. The question is whether missing calls is costing more — and we both know it is." |

---

## 6. ONBOARDING CHECKLIST

**Total: 1 weekend William's time + 45 min client's time**

### Client fills out intake form (15 min)
Google Form covering: business name, transfer numbers, business hours, trade type, top 3 qualifying questions, AI persona name, billing info.

### William's setup (4–6 hours, one weekend)
- [ ] Hour 1: Twilio — new number or configure forward, create subaccount, set webhook
- [ ] Hour 2: Flask app — add client config (business name, persona, questions, transfer numbers, hours)
- [ ] Hour 3: ElevenLabs — select/configure voice, run 3–5 test calls, get client approval
- [ ] Hour 4: n8n follow-up automation (Pro/Bundle only) — clone template, update triggers, test SMS fires within 60 sec
- [ ] Hour 5: QA (10 test calls, different scenarios) + Loom walkthrough for client
- [ ] Hour 6: Stripe payment link + service agreement + Google Drive client folder + monthly check-in calendar

### Go-live (Day 7–10)
- [ ] Client forwards their number to Twilio number (William provides instructions)
- [ ] Monitor first 24 hours, review 3–5 calls
- [ ] Send "You're live" text with their AI number and William's direct cell

**Ongoing: ~30 min/month per client**

---

## 7. 30-60-90 DAY REVENUE TARGETS

### Month 1 (May 12 – June 12)
- Week 1: Build intake form, Stripe billing, client config system, service agreement
- Week 2: Launch Apollo sequence, 50–100 HVAC + plumbing contacts (Collier + Lee)
- Week 3–4: Work county network referrals, run 5–8 demos
- **Target: 2 clients signed → $794 MRR + $798 setup = $1,592 cash**

### Month 2 (June 12 – July 12)
- Sequence continues (200+ additional contacts)
- First testimonial — update Email 2 with real social proof
- Referral program activated (1 month free for successful referral)
- **Target: 5 total clients → $1,788 MRR**

### Month 3 (July 12 – August 12)
- HVAC summer rush — peak Florida season, best close timing of the year
- Referral loop active
- Volume increased to 300 contacts/month
- **Target: 8–10 total clients → $2,673–$4,570 MRR**

**Conservative 90-day total cash: $4,500+ (8 clients, mixed tiers)**
**Stretch target: $3,400+ MRR by Day 90 if warm referrals activate**

---

## 8. LEGAL & COMPLIANCE NOTES

### Service Agreement (must-haves)
- Scope: AI does NOT schedule, quote, or give medical/technical advice
- No-guarantee clause: best-effort performance, not guaranteed conversion
- Call recording disclosure in AI greeting (Florida two-party consent — F.S. 934.03)
- Liability cap: 1 month of service fees
- 30-day written notice to cancel, setup fees non-refundable after go-live

### Twilio A2P 10DLC (MANDATORY before outreach)
Verify registration in Twilio Console → Messaging → Regulatory Compliance. Without it, outbound SMS is filtered/blocked by carriers.

### Med Spas — HIPAA Caution
Limit AI qualifying questions to: appointment type, new vs. existing client, general inquiry. Nothing clinical. Have med spa clients sign acknowledgment that AI does not handle PHI. Do NOT offer HIPAA-covered scheduling until a BAA is in place (requires attorney). **Start with HVAC/plumbing first — cleaner regulatory environment.**

### ElevenLabs
Commercial use permitted. Do not clone specific real person's voice without explicit consent. Use standard library voices for clients in Starter/Pro tiers unless client formally consents to voice cloning.

---

## 9. IMMEDIATE ACTION LIST — Week 1 (~7 hours total)

| Task | Est. Time |
|------|-----------|
| Build client intake form (Google Form) | 1 hr |
| Set up Stripe recurring billing | 1 hr |
| Draft service agreement (template for attorney review) | 1 hr |
| Verify Twilio 10DLC registration | 30 min |
| Call 3 Collier County contractor contacts (warmest leads) | 1 hr |
| Load Apollo sequence — 50 HVAC + plumbing contacts, Collier + Lee County | 1 hr |
| Generate one-page sales PDF via branded_pdf_engine.py | 1 hr |
| **TOTAL** | **~7 hours** |

---

## RED FLAGS

1. **EC2 single point of failure** — all clients on one server. Set up CloudWatch → Telegram alert + Twilio fallback (forward directly to owner's cell if webhook fails).
2. **HVAC summer rush is NOW** — Florida peak season June–August. If outreach doesn't start by May 15, the best close window is missed.
3. **Med spa HIPAA exposure** — defer to Month 2–3 after HVAC/plumbing base established.
4. **Time cap at 3+ clients/month** — without the intake + config tooling built in Week 1, onboarding bottlenecks at client 3. Build the tooling first.

---

*Saved by Panacea, May 10 2026. Market research verified against Smith.ai, Ruby, My AI Front Desk, Trillet, Dialzara, NextPhone, Cleverly, ElevenLabs ToS.*
