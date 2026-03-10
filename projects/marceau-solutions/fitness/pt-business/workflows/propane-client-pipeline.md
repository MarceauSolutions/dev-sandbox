# Client Acquisition Pipeline
## Modeled After Propane Fitness — Adapted for William Marceau

> **Status**: LIVE — All systems built and active
> **Created**: 2026-03-01
> **Updated**: 2026-03-01 (v3 — 5-tier offer structure, Day 7 upsell workflow, full page deployment)
> **Goal**: 0 → 10 paying clients (mix of $197-497/mo = $2,000-4,000 MRR)
> **Timeline**: 8 weeks
> **Existing infra used**: n8n automations, Twilio SMS, Stripe, Calendly, Google Sheets, coaching website

---

## How Propane Does It (The Model We're Adapting)

Propane Fitness built a $3.4M+ business using this core loop:

```
Paid Meta Ads → Free Lead Magnet (Macro Calculator) →
14-Day Email Nurture Sequence → Automated Offer (£147 entry) →
Monthly Continuity (£55/mo) → Long-term retention (avg client = years)
```

**Key principles we're stealing:**
1. **No-call funnel** — Automate the sale, don't rely on booking calls to close
2. **Mid-ticket + continuity** — $197/mo is the right price band (not $5K high-ticket)
3. **Lead magnet → nurture → offer** — Never pitch cold; warm them up over 7-14 days
4. **Paid ads > organic social** — Organic builds authority; paid ads drive volume
5. **Evidence-based positioning** — Be the anti-bro-science expert (your peptide knowledge is this x10)
6. **Community/group layer** — Free challenge group as bridge between quiz and paid offer (missing from v1)

---

## COMPLETE FUNNEL ARCHITECTURE (v3)

This is the full scalable, repeatable system. Every step is automated. 5-tier offer structure.

```
                     META ADS ($15-20/day)
                     Instagram Reels / YouTube Shorts
                     Local partnerships / Warm network
                            │
                            ▼
              ┌──────────────────────────┐
              │  QUIZ (7-Step Calculator) │  ← marceausolutions.com/quiz
              │  ───────────────────────  │
              │  Goal → Stats → Experience│
              │  → Frustration → Peptides │
              │  → Readiness → Contact    │
              │                           │
              │  FEATURES (research-backed):
              │  • Insight interstitials   │
              │  • Processing animation   │
              │  • Archetype assignment    │
              │  • Readiness score (0-98)  │
              │  • Predicted goal date     │
              │  • Tiered CTAs on results  │
              └────────────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
   ┌───────────────┐ ┌──────────┐ ┌──────────────┐
   │ FREE 7-DAY    │ │ DIGITAL  │ │ DIRECT BUY   │
   │ CHALLENGE     │ │ PRODUCTS │ │ $197 or $497 │
   │ (Community)   │ │ $37-97   │ │ Coaching     │
   │               │ │ one-time │ └──────┬───────┘
   │ /challenge    │ │ /programs│        │
   │               │ └──────────┘        ▼
   │ • Daily SMS   │                Stripe → Onboard
   │ • Group chat  │
   │ • Coach access│
   │ • Peptide edu │
   └───────┬───────┘
           │
    Day 7: Segmented
    Upsell (n8n auto)
           │
    ┌──────┼──────────────┐
    ▼      ▼              ▼
┌────────┐┌────────────┐┌──────────┐
│COACHING││ PREMIUM +  ││ STAY     │
│$197/mo ││ PEPTIDES   ││ FREE /   │
│        ││ $497/mo    ││ DIGITAL  │
│ Stripe ││ Calendly   ││ /programs│
└────────┘└────────────┘└──────────┘
                │
      (Peptide-interested leads
       get Premium offer first)
```

### 4 Archetype System (assigned by quiz)

| Archetype | Who | Trigger | Coaching Approach |
|-----------|-----|---------|-------------------|
| **The Igniter** | Ready + frustrated with consistency/info | all_in/soon + inconsistent/confused | Structured 4-week blocks, weekly accountability |
| **The Comeback** | Ready + plateaued | all_in + plateau/confused | Remove guesswork, precision protocols |
| **The Optimizer** | Advanced + plateau | advanced OR intermediate+plateau | Nutrient timing, periodization, peptides |
| **The Explorer** | Browsing options | exploring readiness | Free challenge first, test-drive approach |

### 5-Tier Revenue Structure (v3)

| Tier | Price | What | Funnel Position |
|------|-------|------|-----------------|
| Community + Challenge | FREE | Group, 7-day workouts, macros, coach access, peptide primer | Entry (quiz → group) |
| Digital Programs | $37-97 (one-time) | 8-Week Recomp ($67), Nutrition Blueprint ($37), Peptide Masterclass ($97) | Self-guided, funds ads |
| 1:1 Coaching | $197/mo | Custom program, weekly check-ins, AI tracking, community | Core recurring revenue |
| Premium + Peptides | $497/mo (WAITLIST) | Everything in coaching + peptide protocols — **waiting on physician partnerships** | High-touch premium (coming soon) |
| Free Strategy Call | FREE | 30-min Calendly call | For hesitant leads at any tier |

### Live n8n Workflows

| Workflow | ID | Status | Purpose |
|----------|----|--------|---------|
| Lead-Magnet-Capture | `hgInaJCLffLFBX1G` | ACTIVE | Quiz → Sheet → Day 0 SMS/Email |
| Nurture-Sequence-7Day | `szuYee7gtQkzRn3L` | ACTIVE | 7-day drip (SMS + Email) |
| Non-Converter-Followup | `Y2jfeIlTRDlbCHeS` | ACTIVE | Day 10/14/30 follow-ups |
| Challenge-Signup-7Day | `WTZDxLDQuSkIkcqf` | ACTIVE | Challenge → Sheet → Welcome → 7-day SMS workouts |
| Challenge-Day7-Upsell | `Xza1DB4f4PIHw2lZ` | ACTIVE | Day 7 segmented upsell (waitlist for peptide leads, $197 for others) |
| Premium-Waitlist-Capture | `j306crRxCmWW3dMo` | ACTIVE | Waitlist form → Sheet "Premium Waitlist" tab → confirmation email |
| Digital-Product-Delivery | `kk7ZjWtjmZgylVzi` | ACTIVE | Stripe checkout → identify product → delivery email + Sheet update |
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | ACTIVE | Stripe $197 payment → welcome SMS/email + Sheet + onboarding |

### Live Pages

| Page | URL | Purpose |
|------|-----|---------|
| Quiz | `marceausolutions.com/quiz` | Lead magnet calculator (7-step, archetype-based results) |
| Challenge | `marceausolutions.com/challenge` | Community funnel — free 7-day challenge signup |
| Programs | `marceausolutions.com/programs` | Full 5-tier shop (community → digital → coaching → premium) |
| Coaching | `marceausolutions.com/coaching` | Detailed coaching offer ($197 base, $497 premium) |

### Lead Tracking

| Asset | Details |
|-------|---------|
| Google Sheet | ID: `13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E` |
| Leads tab | Name, Email, Phone, Goal, Age, Gender, Weight, Height, Experience, Peptide Interest, Source, Date, Nurture Status |
| Metrics tab | Weekly: leads, sources, nurture progress, conversions, ad spend, CAC, MRR |

---

## Your Adapted Pipeline (4 Phases)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: ATTRACT (Top of Funnel)             │
│                                                                 │
│   LOCAL                          ONLINE                         │
│   ─────                          ──────                         │
│   Gym conversations              Instagram Reels (3-5/week)     │
│   Naples med spa referrals       YouTube Shorts                 │
│   Chiropractor partnerships      Facebook/Meta Ads ($15-20/day) │
│   Country club networking        TBI recovery story content     │
│   Warm network outreach          Peptide education posts        │
│                                                                 │
│              ALL TRAFFIC → Lead Magnet Landing Page              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 2: CAPTURE (Lead Magnet)                │
│                                                                 │
│   FREE "Peptide-Informed Body Recomp Calculator"                │
│   ─────────────────────────────────────────────────             │
│   → Enter: age, weight, goal, training experience               │
│   → Get: Custom macro targets + peptide protocol recommendation │
│   → Captures: name, email, phone                                │
│                                                                 │
│   WHY THIS WORKS (Propane's exact playbook):                    │
│   - Interactive = high completion rate                           │
│   - Personalized output = perceived value                       │
│   - Peptide angle = unique differentiator no competitor has      │
│   - Phone capture = enables SMS nurture (your strongest channel) │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                PHASE 3: NURTURE (7-Day Sequence)                │
│                                                                 │
│   Day 0: Calculator results + "Here's your plan" (SMS + Email)  │
│   Day 1: "The #1 mistake killing your fat loss" (Email)         │
│   Day 2: Your TBI recovery story — why this is personal (SMS)   │
│   Day 3: "Why peptides matter (and why most coaches ignore      │
│            them)" (Email + link to peptides page)               │
│   Day 4: Client transformation case study (SMS with photo)      │
│   Day 5: "3 signs your training program isn't working" (Email)  │
│   Day 6: Social proof — what working with you looks like (SMS)  │
│   Day 7: THE OFFER — "Ready to stop guessing?" (SMS + Email)   │
│                                                                 │
│   DELIVERY: n8n workflow with scheduled delays                  │
│   SMS: Twilio (+1 239 880 3365)                                 │
│   Email: Gmail SMTP (already configured)                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 4: CONVERT (Tiered Paths)                 │
│                                                                 │
│   PATH A: FREE CHALLENGE (Community Funnel)                     │
│   ──────────────────────────────────────────                    │
│   Quiz → /challenge signup → 7-day SMS workouts                 │
│   → Day 7 segmented upsell (n8n auto)                           │
│   → Peptide-interested → Premium $497/mo offer                  │
│   → Standard → Coaching $197/mo offer                           │
│   → All → Digital products /programs fallback                   │
│                                                                 │
│   PATH B: DIRECT PURCHASE (No-Call, Propane Style)              │
│   ──────────────────────────────────────────────                │
│   Day 7 message includes Stripe link                            │
│   → $197/mo subscription starts immediately                     │
│   → Auto-triggers: Welcome SMS + Onboarding Email + Intake Form │
│                                                                 │
│   PATH C: FREE STRATEGY CALL (For Hesitant Leads)              │
│   ──────────────────────────────────────────────                │
│   Calendly link available at every tier                          │
│   → 30-min call (you close in person/video)                     │
│   → If yes → send Stripe link on call                           │
│                                                                 │
│   NON-CONVERTERS:                                               │
│   Day 10: "Still thinking about it?" (SMS)                      │
│   Day 14: "Last chance — founding member rate" (SMS)            │
│   Day 30: Move to long-term nurture list (monthly value email)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Execution Plan (Week by Week)

### Week 1-2: Foundation & Warm Launch

| Task | Details | Tool/Platform |
|------|---------|---------------|
| Build lead magnet page | Peptide-informed calculator on `marceausolutions.com/quiz` | Website HTML/JS |
| Write 7-day nurture sequence | 4 emails + 4 SMS messages (content outlined above) | Markdown → n8n |
| Build n8n nurture workflow | Webhook trigger → 7-day drip with delays | n8n (EC2) |
| Warm outreach (20 people) | Personal network — friends, family, gym contacts | Phone + SMS |
| Gym floor conversations | 2-3 conversations/day at your Naples gym | In person |
| Set up Instagram | Bio, profile pic, first 9 posts (grid aesthetic) | Instagram |
| Record 3 short videos | TBI story, peptide myth-busting, "what coaching looks like" | iPhone → edit |

**Target**: 5-10 leads captured, 1-2 paying clients from warm network

### Week 3-4: Content Engine + Local Partnerships

| Task | Details | Tool/Platform |
|------|---------|---------------|
| Publish 3-5 Reels/week | Peptide tips, form checks, client results, personal story | Instagram + TikTok |
| Contact 5 local businesses | Med spas, chiropractors, country clubs in Naples | Email + in-person |
| Propose referral deal | "Send me clients, I send you clients" or rev share | Agreement template |
| Launch Meta Ads ($15/day) | Target: Naples FL, 30-55, fitness interest, top 25% income | Facebook Ads Manager |
| Ad creative: 3 variations | (1) TBI story, (2) peptide education, (3) transformation | Canva + iPhone |
| Ad destination | Lead magnet calculator page | `marceausolutions.com/quiz` |
| Analyze Week 1-2 nurture data | Open rates, reply rates, conversion | Google Sheets |

**Target**: 20-30 leads, 3-5 total paying clients, first local partnership signed

### Week 5-6: Optimize & Scale What Works

| Task | Details | Tool/Platform |
|------|---------|---------------|
| Kill underperforming ads | Keep top 1-2 ads, cut losers | Facebook Ads Manager |
| Scale winning ad to $25-30/day | If CAC < $100, increase spend | Facebook Ads Manager |
| Add retargeting campaign | Show testimonials to page visitors who didn't opt in | Facebook Pixel |
| Collect first testimonials | Ask Week 1-2 clients for video/text testimonials | SMS request |
| Publish transformation content | Before/after (with permission), client quotes | Instagram + website |
| Refine nurture sequence | A/B test Day 7 offer message (direct buy vs. call CTA) | n8n workflow |
| YouTube: first long-form video | "Everything I Know About Peptides for Fat Loss" (10-15 min) | YouTube |

**Target**: 40-50 total leads, 6-8 paying clients, CAC under $100

### Week 7-8: Systematize & Hit 10 Clients

| Task | Details | Tool/Platform |
|------|---------|---------------|
| Document what's working | Which channel, which message, which ad creative wins | Runbook update |
| Automate testimonial requests | n8n workflow: auto-request at Day 30 and Day 90 | n8n (templates exist) |
| Launch referral program | "Refer a friend, get 1 month free" | Stripe coupon + SMS |
| Second YouTube video | "My TBI Recovery: How Fitness Saved My Life" | YouTube |
| Expand local partnerships | 3 more businesses (different verticals) | In person |
| Create "founding member" scarcity | "Only accepting 15 clients at $197 — 5 spots left" | Website + ads |
| Evaluate go/no-go | 10 clients = GO. Scale to $5K MRR next. | Decision point |

**Target**: 10 paying clients = $1,970-4,000 MRR (mix of $197 + $497)

---

## Lead Magnet: Peptide-Informed Body Recomp Calculator

This is your equivalent of Propane's macro calculator — the thing that captures leads.

### What the user inputs:
1. Age
2. Current weight
3. Goal (fat loss / muscle gain / body recomp / performance)
4. Training experience (beginner / intermediate / advanced)
5. Interest in peptide protocols (yes / curious / no)
6. Name, email, phone

### What they get back (immediately):
- **Custom daily calorie target** (TDEE calculation)
- **Macro split** (protein/carb/fat grams)
- **Training frequency recommendation** (days/week + split type)
- **Peptide protocol suggestion** (if interested): brief mention of relevant peptides for their goal (e.g., "Based on your fat loss goal, Tesamorelin is worth discussing with your doctor")
- **CTA**: "Want the full custom plan? Book a free strategy call or start coaching today."

### Why this wins:
- **Interactive** — people complete calculators at 40%+ rate vs. 5-10% for PDF downloads
- **Personalized** — output feels custom, not generic
- **Peptide angle** — NO other fitness coach offers this; instant differentiation
- **Phone capture** — feeds directly into your Twilio SMS nurture (your strongest automation)

---

## 7-Day Nurture Sequence (Full Copy Outlines)

### Day 0 — Immediate (SMS + Email)
**SMS**: "Hey {name}, your custom plan is ready! Check your email for your macro targets and training recommendations. — William, Marceau Fitness"

**Email Subject**: "Your Custom Body Recomp Plan"
**Email Body**: Calculator results + macro breakdown + "Over the next week, I'll share my best tips for making this work. Talk soon."

### Day 1 — Email Only
**Subject**: "The #1 mistake I see in every gym in Naples"
**Body**: Address the biggest training/nutrition myth relevant to their goal. Evidence-based correction. End with: "Tomorrow I'll share something personal about why I coach."

### Day 2 — SMS Only
**SMS**: "{name}, quick story — 3 years ago I had a traumatic brain injury that changed everything. I rebuilt my body from scratch using the exact methods I now teach. Full story: [link to about page]. — William"

### Day 3 — Email Only
**Subject**: "Why your coach probably doesn't know about peptides"
**Body**: Brief, accessible intro to peptides. NOT a sales pitch — pure education. Tesamorelin for fat loss, GH secretagogues for recovery. Link to your peptides page. Position yourself as the expert bridge between research and practical application.

### Day 4 — SMS Only
**SMS**: "{name}, meet [client name] — lost 22 lbs in 12 weeks while working 60-hour weeks. No crash diets. No 2-hour gym sessions. Just smart programming. [link to transformation or photo]"

### Day 5 — Email Only
**Subject**: "3 signs your current training isn't working"
**Body**: Tactical value — plateaus, soreness vs. progress, program hopping. Position your coaching as the fix. End with: "I help my clients fix all three. More on that in 2 days."

### Day 6 — SMS Only
**SMS**: "{name}, here's what a typical week looks like for my coaching clients: Mon check-in, custom program updates, direct access to me, peptide guidance if you want it. No cookie-cutter BS. Details tomorrow."

### Day 7 — SMS + Email (THE OFFER)
**SMS**: "{name}, I've got 3 spots open for March coaching. $197/mo — custom training, nutrition, weekly check-ins, and peptide-informed protocols. No lock-in, cancel anytime. Ready? {stripe_link} — or book a free call: {calendly_link}"

**Email Subject**: "Your spot is open — here's the offer"
**Email Body**: Full offer breakdown — what's included, pricing, testimonials, FAQ, both CTAs (direct buy + call). Scarcity element: limited spots.

### Day 10 — SMS (Non-converters only)
**SMS**: "{name}, still thinking about coaching? Happy to answer any questions. Just reply here or book a quick call: {calendly_link} — William"

### Day 14 — SMS (Final push)
**SMS**: "{name}, last note from me — founding member rate of $197/mo won't last forever. If the timing isn't right, no worries. But if you're ready to stop guessing, I'm here: {stripe_link}"

### Day 30+ — Monthly email (Long-term nurture)
One value email per month: training tip, peptide research update, client story. Keeps you top-of-mind without being annoying.

---

## n8n Workflow Architecture

### Active Workflows

| Workflow Name | ID | Trigger | Actions |
|---|---|---|---|
| `Lead-Magnet-Capture` | `hgInaJCLffLFBX1G` | Webhook (quiz submit) | Save to Google Sheet → Send Day 0 SMS + Email → Start nurture timer |
| `Nurture-Sequence-7Day` | `szuYee7gtQkzRn3L` | Scheduled (per-lead timing) | Days 1-7 messages via Twilio + Gmail → Track opens/clicks → Branch at Day 7 |
| `Non-Converter-Followup` | `Y2jfeIlTRDlbCHeS` | Day 7 no-purchase check | Day 10 SMS → Day 14 SMS → Day 30 move to monthly list |
| `Challenge-Signup-7Day` | `WTZDxLDQuSkIkcqf` | Webhook (challenge signup) | Save to Sheet → Welcome SMS + Email → 7-day daily workout SMS |
| `Challenge-Day7-Upsell` | `Xza1DB4f4PIHw2lZ` | Cron (daily 8am) | Read Sheet → Filter Day 7 leads → Peptide interest? → Premium $497 SMS : Standard $197 SMS → Update sheet |

### Existing Workflows (Already Working)

| Workflow | Reuse For |
|---|---|
| `Coaching-Payment-Welcome` | Auto-fires when nurture → Stripe conversion happens |
| `Coaching-Monday-Checkin` | Keeps converted clients engaged (retention) |
| `Coaching-Cancellation-Exit` | Re-engagement for churned clients |

---

## Metrics Dashboard (Google Sheets)

### Track weekly:

| Metric | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Week 6 | Week 7 | Week 8 |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Leads captured | | | | | | | | |
| Lead source (local/online/ad) | | | | | | | | |
| Nurture sequence started | | | | | | | | |
| Day 7 offer sent | | | | | | | | |
| Strategy calls booked | | | | | | | | |
| Direct purchases | | | | | | | | |
| Total new clients | | | | | | | | |
| Ad spend ($) | | | | | | | | |
| Cost per lead | | | | | | | | |
| Cost per client (CAC) | | | | | | | | |
| MRR | | | | | | | | |

### Go/No-Go Thresholds (from Propane's playbook):

| Metric | GO | PAUSE | NO-GO |
|--------|-----|-------|-------|
| Clients at Week 8 | 10+ | 5-9 | <5 |
| CAC | <$100 | $100-200 | >$200 |
| Nurture→Client rate | >10% | 5-10% | <5% |
| Day 7 offer response rate | >20% | 10-20% | <10% |

---

## Budget

| Item | Weekly Cost | 8-Week Total |
|------|-----------|-------------|
| Meta Ads (start Week 3) | $105-210 | $630-1,260 |
| Twilio SMS (~200 msgs/week) | ~$3 | ~$24 |
| Skool Community ($9/mo) | ~$2.25 | ~$18 |
| Domain/hosting | $0 (already paid) | $0 |
| n8n/EC2 | $0 (already running) | $0 |
| Stripe fees | 2.9% + $0.30/txn | ~$6/client/mo |
| **Total investment** | | **$680-1,310** |
| **Break-even** | | **4 clients at $197 = $788/mo** |

---

## What Propane Does That We Skip (For Now)

| Propane Element | Our Decision | Why |
|---|---|---|
| ClickFunnels ($297/mo) | Skip — build on our website | We already have a live site + can code landing pages |
| ConvertKit ($29-79/mo) | Skip — use Gmail SMTP + n8n | Already configured and working |
| Two separate websites | Skip — one site, two audiences later | Focus on clients first |
| Podcast | Skip for now | Requires consistent content; YouTube/Reels first |
| eBooks as entry product | Skip — calculator is better | Interactive > static PDF |
| Coach-the-coach program | Phase 2 (after 50+ clients) | Need proven results first |
| Hyros ($500+/mo) | Skip — UTM params + Google Sheets | Manual tracking is fine at this scale |

---

## Immediate Next Actions

1. ~~Build the calculator/quiz page~~ ✅ LIVE at `marceausolutions.com/quiz`
2. ~~Write the 7 nurture messages~~ ✅ Built into n8n workflows
3. ~~Build the n8n Lead-Magnet-Capture workflow~~ ✅ ACTIVE
4. ~~Build the n8n Nurture-Sequence-7Day workflow~~ ✅ ACTIVE
5. ~~Build challenge page + signup workflow~~ ✅ LIVE + ACTIVE
6. ~~Build 5-tier programs page~~ ✅ LIVE at `marceausolutions.com/programs`
7. ~~Build Day 7 segmented upsell workflow~~ ✅ ACTIVE
8. **Set up Skool community** ($9/mo Hobby plan) — community platform for challenge group
9. **Create Stripe products** — digital programs ($37, $67, $97) + Premium tier ($497/mo)
10. **Set up Instagram** (bio + first 9 posts)
11. **Start warm outreach** (text 20 people in your network this week)
12. **Have 3 gym conversations** this week

---

## The Math (5-Tier Model)

```
100 leads → funnel breakdown:
├── 40% take free challenge (40 people)
│   ├── 15% convert to coaching (6 × $197 = $1,182/mo)
│   ├── 5% convert to premium (2 × $497 = $994/mo)
│   └── 80% stay free or buy digital
├── 20% buy digital products (20 × $57 avg = $1,140 one-time)
├── 5% buy coaching direct (5 × $197 = $985/mo)
└── 35% nurture / drop off

Conservative Month 1: $2,176/mo recurring + $1,140 digital = $3,316
Month 3 (compounding): $4,000-6,000 MRR (recurring stacks)

At Propane's 25% conversion rate (aspirational):
100 leads × 25% = 25 clients
Mix of $197 + $497 = ~$6,000+ MRR = $72,000+ ARR
```

Digital products fund ad spend. Coaching provides MRR. Premium is the profit multiplier.

Your infrastructure is built. The pipeline is mapped. Execute.
