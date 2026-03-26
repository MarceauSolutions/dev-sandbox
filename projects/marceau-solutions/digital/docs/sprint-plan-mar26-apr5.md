# AI Client Sprint — Battle Plan
## March 26 – April 5 | 11 Days to Close

---

## Where You Stand Right Now (Honest Assessment)

**Pipeline:** 205 leads, 27 called, 3 showed interest, 1 qualified (A&Y Auto)
**Conversion rate from calls:** 11% interest rate (3/27) — that's actually good for cold outreach
**Problem:** Volume is too low. 27 calls in 3 days won't get you to a close in 11 days.
**What needs to happen:** You need 1-2 discovery calls booked THIS WEEK. Discovery calls close at 20-30%. So you need 5-7 discovery calls total to statistically land 1 client.

---

## The Math (Hormozi Rule of 100)

- Cold calls to interest: ~10% (you're at 11%)
- Interest to discovery call booked: ~30%
- Discovery call to close: ~25% (first-time seller, good product)
- **You need: 100+ cold calls → 10 interested → 3 discovery calls → 1 close**
- You've made 27 calls. You need 73 more minimum.
- At 15 calls/day = 5 more days of calling = done by March 31
- At 25 calls/day = 3 more days = done by March 28

**Target: 25 calls per day for the next 3 days. Non-negotiable.**

---

## Daily Schedule (March 26 – April 5)

### Phase 1: Volume Blitz (March 26-28) — 3 Days
**Goal: 75 calls, 7-8 interested, 2-3 discovery calls booked**

| Time | Activity |
|------|----------|
| 6:15am | Dog walk + morning routine |
| 7:00am | Dashboard review — check overnight email replies, Apollo sequence stats |
| 7:30am | Hand therapy + coffee + review call list |
| 8:00-9:30am | **PHONE BLITZ #1** — 12-15 calls (best window, owners in office before dispatch) |
| 9:30-10:00am | Log outcomes, send personalized emails to anyone who gave email |
| 10:00-11:30am | **PHONE BLITZ #2** — 10-12 calls |
| 11:30am-12:00pm | Quick follow-ups on morning warm responses |
| 12:00-1:00pm | Lunch (DO NOT CALL — nobody answers) |
| 1:00-3:00pm | **PHONE BLITZ #3** — 10-12 calls (afternoon window) |
| 3:00-3:30pm | Log all outcomes, send follow-up emails |
| 3:30-4:00pm | Spanish study |
| 4:00-5:00pm | Research tomorrow's call list, prep personalized angles |
| 6:00-8:00pm | Training |

### Phase 2: Convert (March 29 – April 1) — 4 Days
**Goal: Run 3-5 discovery calls, send 1-2 proposals**

- Morning: Follow up on all warm leads from Phase 1
- Midday: Discovery calls (15-30 min each via Calendly)
- Afternoon: Build custom proposals for interested prospects
- Continue calling new leads between meetings (never stop the pipeline)

### Phase 3: Close (April 2-5) — 4 Days
**Goal: Close 1 deal, sign agreement, begin onboarding**

- Follow up on proposals sent
- Handle objections
- Get signature on agreement
- Begin building their system (shows commitment, builds trust)

---

## What to Call (Priority Order)

### 1. Follow-ups FIRST (highest conversion)
These people already engaged. They convert at 3-5x the rate of cold calls.
- A&Y Auto — QUALIFIED. Call back, discuss pricing.
- Golden Plumbing — Wait for owner callback. If no call by March 27, email Dawn directly.
- One Way Air (Diana) — Personalized email sent. Follow up call March 28.
- Conditioned Air Naples (Yolanda) — Email sent. Follow up call March 28.
- Homepatible (Amanda) — Call back March 28, ask if she passed it along.
- Family AC — Owner may call back. If not, re-call March 28.

### 2. Fresh HVAC calls (81 uncalled with phones)
HVAC is your strongest vertical:
- Owners answer their own phones (small shops)
- Emergency call angle is immediately understandable
- Season is ramping up (summer in Naples = AC breaks)
- Average job value is high ($400-800)

### 3. Non-HVAC with phones
After HVAC is exhausted, move to plumbing, medical, dental, auto.

---

## The Pitch (Updated — AI Operations, Not Phone Bot)

**You are NOT selling a phone answering service.**
**You are selling the full AI operations layer for their business.**

Opening: "Hi, this is William from Marceau Solutions. I build AI operations systems for service businesses here in Naples. Got 60 seconds?"

Key differentiator: "I don't sell phone bots — anyone can buy one of those for $30 a month. I build the system that connects every customer touchpoint your business has — phone, website, Google, Instagram — and makes sure nothing falls through the cracks. The phone agent is just the front door."

Demo line: "Call (855) 239-9364 right now — that's our AI receptionist. It's exactly what I'd build for your business."

Close: "Do you have 15 minutes this week? I'll pull up your business specifically and show you where leads are leaking."

---

## Discovery Call Structure (When They Book)

1. **Open (2 min):** Thank them, confirm time, set agenda — "I want to learn about your business, then show you what I'd build. Sound good?"
2. **Pain discovery (10 min):**
   - "Walk me through what happens when a lead calls after hours."
   - "How many calls do you think you miss per week?"
   - "What happens to website form submissions — who follows up and how fast?"
   - "If I told you that you're losing $X/month in missed leads, would that surprise you?"
3. **Demo (5 min):**
   - "Call this number right now: (855) 239-9364"
   - Show how it qualifies, routes, books
   - "That's the front door. Behind it is automated follow-up, review requests, the full lifecycle."
4. **Proposal (3 min):**
   - "Based on what you told me, here's what I'd build for you."
   - Setup: $500-2,000 (depends on complexity)
   - Monthly: $297-997/mo (ongoing management + AI costs)
   - "I do a free 2-week onboarding — I build it, you test it, if it doesn't work you owe me nothing."

---

## Pricing Strategy (Hormozi Framework)

**The free trial is your weapon.** You're unknown, you have no case studies yet. The trial eliminates risk for them.

- "Free 2-week onboarding — I build the system, you test it"
- "If it works, $297/mo. If it doesn't, you owe me nothing."
- $297/mo is the entry point. It's low enough that it's a no-brainer for a business doing $500K+/year
- Once they're in and seeing results, upsell to full AI operations ($500-997/mo)

**For A&Y Auto (tight budget):**
- Start at $150/mo with basic missed call capture
- Prove ROI in 30 days
- Upgrade when they see the value

---

## Systems Checklist (What's Automated)

| System | Status | What It Does |
|--------|--------|-------------|
| Pipeline DB | WORKING | Tracks every lead, every touch, every stage |
| call_logger.py | WORKING | Panacea logs calls to pipeline.db via Telegram |
| log_call_complete.py | WORKING | Logs call + sends email + updates stage in one action |
| send_followup_email.py | WORKING | Personalized SMTP emails |
| followup_reminder.py | WORKING | Surfaces due follow-ups |
| generate_lead_lists.py | WORKING | Prioritized call lists excluding already-called |
| Cold Email Follow-Up Sequence | WORKING (fixed today) | Auto follow-up on Day 3/7 |
| Gmail Reply Watcher | WORKING | Catches inbound replies |
| ElevenLabs Call Poller | WORKING | Captures AI phone agent calls |
| Morning Accountability (5am) | WORKING (fixed today) | Daily check-in |
| EOD Accountability (7pm) | WORKING | End-of-day stats |
| SMTP | WORKING | Email from wmarceau@marceausolutions.com |
| Twilio SMS | WORKING | SMS from (855) 239-9364 |
| AI Phone Agent | WORKING | (855) 239-9364 live demo |
| Apollo Sequences | PARTIAL | General + HVAC active. Med Spa/Plumbing/Roofing need manual setup in Apollo UI |
| Calendar Gateway | WORKING | Prevents agent calendar conflicts |
| Google Sheet Call Tracker | WORKING | Fill in outcomes, I pull and log in batch |

---

## What YOU Do vs What THE SYSTEM Does

**You:**
- Make the calls
- Have the conversations
- Run discovery calls
- Close the deal

**The system:**
- Gives you who to call next (prioritized)
- Sends follow-up emails automatically after positive calls
- Reminds you of Day 3/Day 7 follow-ups
- Tracks everything in one database
- Catches inbound replies
- Provides the AI phone demo at (855) 239-9364

---

## Non-Negotiable Rules for the Next 11 Days

1. **25 calls per day minimum** — use the Google Sheet tracker, I log in batch
2. **Follow up on warm leads FIRST every morning** — they convert 3-5x higher
3. **Every email obtained = personalized follow-up sent same day** — I handle the research and sending
4. **No in-person visits unless someone ASKS you to come** — cold walk-ins wasted a full day. Phone first, always.
5. **Discovery calls are the #1 priority** — if someone wants to talk, everything else stops
6. **Log everything via Telegram to Panacea** — one source of truth
7. **Don't sell the phone bot. Sell the full AI operations system.** — differentiate from ElevenLabs/Bland/Vapi

---

## Milestones

| Date | Milestone |
|------|-----------|
| March 28 | 100 total calls made, 3+ discovery calls booked |
| March 31 | First discovery call completed, first proposal sent |
| April 2 | Follow up on proposal, handle objections |
| April 4 | Close deal, sign agreement |
| April 5 | Begin building client system (shows commitment before job starts) |
| April 6 | Start Collier County job with supplemental income secured |
