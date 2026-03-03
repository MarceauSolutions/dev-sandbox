# Client Acquisition System
## A Complete Operations Manual for William Marceau Fitness Coaching

**Version**: 1.0
**Date**: March 2, 2026
**Author**: William Marceau & Claude Code (AI Engineering Partner)
**Website**: marceausolutions.com
**Business**: William Marceau — Fitness Coach & Peptide Expert

---

# Table of Contents

1. Executive Summary
2. System Philosophy & Design Decisions
3. The Funnel Architecture
4. Website Pages — What They Do & How to Use Them
5. The Quiz (Lead Magnet) — Deep Dive
6. The 7-Day Challenge — Deep Dive
7. n8n Workflow Automation — Complete Reference
8. Stripe Payment Infrastructure
9. Google Sheets Data Architecture
10. The Operator's Playbook — How You Interact With the System
11. The End User's Journey — What Your Clients Experience
12. Troubleshooting & Maintenance
13. Growth Roadmap

---

# Chapter 1: Executive Summary

This document is a comprehensive reference for your entire client acquisition system — the automated funnel that takes a stranger from "never heard of you" to "paying coaching client" with minimal manual intervention.

### What You Built

You built a fully automated fitness coaching sales funnel modeled after Propane Fitness's proven $3.4M+ playbook, adapted for your unique positioning: evidence-based training combined with peptide expertise. The system includes:

- **6 website pages** that form a complete marketing funnel
- **8 n8n automation workflows** that handle lead capture, nurture sequences, challenge delivery, upsells, payment processing, and digital product fulfillment
- **4 Stripe payment products** covering digital programs ($37–$97) and monthly coaching ($197/mo)
- **A 5-tier revenue structure** from free community to premium peptide coaching
- **Automated SMS and email sequences** that nurture leads over 7–30 days

### What It Costs to Run

| Item | Monthly Cost |
|------|-------------|
| n8n + EC2 hosting | ~$0 (already running) |
| Twilio SMS (~200 msgs) | ~$12 |
| Skool Community (Hobby) | $9 |
| Domain/hosting | $0 (GitHub Pages) |
| Stripe processing | 2.9% + $0.30 per transaction |
| **Total fixed** | **~$21/month** |

### The Revenue Model

| Tier | Price | Type |
|------|-------|------|
| Community + Challenge | FREE | Lead magnet |
| Nutrition Blueprint | $37 one-time | Digital product |
| 8-Week Recomp Program | $67 one-time | Digital product |
| Peptide Masterclass | $97 one-time | Digital product |
| 1:1 Coaching | $197/month | Recurring subscription |
| Premium + Peptides | $497/month | Waitlist (physician partnerships pending) |

**Break-even**: 4 coaching clients at $197 = $788/month covers all costs plus ad spend.

---

# Chapter 2: System Philosophy & Design Decisions

### Why This Architecture?

Every design decision in this system traces back to a few core principles borrowed from Propane Fitness and adapted for your specific situation.

### Decision 1: No-Call Funnel

**What**: The system is designed so that leads can purchase coaching without ever getting on a phone call. The Stripe payment link is sent directly in SMS and email at Day 7.

**Why**: Propane Fitness proved that mid-ticket offers ($150–$300/month) convert better through automated sequences than through sales calls. Sales calls work for high-ticket ($3K+) but create a bottleneck at your scale. You're one person — you can't do 10 discovery calls a day. A no-call funnel lets you acquire clients while you sleep.

**The call option still exists**: Calendly is embedded on the coaching page and linked in every offer message. Some leads need the human touch. But it's optional, not required.

### Decision 2: Mid-Ticket Pricing ($197/month)

**What**: Your core offer is $197/month with no contract.

**Why**: This price point is the sweet spot for online fitness coaching. It's high enough to attract serious clients (not tire-kickers), low enough that the purchase doesn't require a sales call, and generates meaningful recurring revenue. At 10 clients, you're at $1,970 MRR. At 30 clients (Propane's average student result), you're at $5,910 MRR.

**No contracts**: The "cancel anytime" promise removes the biggest objection. Clients who stay because they want to — not because they're locked in — refer more people and churn less.

### Decision 3: Archetype-Based Quiz (Not Just a Calculator)

**What**: The quiz assigns one of four archetypes (The Igniter, The Comeback, The Optimizer, The Explorer) based on answers, and tailors the results page accordingly.

**Why**: A basic macro calculator is commodity — every fitness site has one. The archetype system creates an emotional connection. When someone reads "You're The Comeback — you've been putting in work but not seeing results. Here's why..." they feel *understood*. This is the same psychology that makes BuzzFeed quizzes go viral. It also lets you segment your messaging: different archetypes get different coaching approaches.

| Archetype | Who They Are | What Triggers It |
|-----------|-------------|-----------------|
| The Igniter | Ready and frustrated with consistency/info | High readiness + inconsistency or confusion frustration |
| The Comeback | Ready and plateaued | High readiness + plateau frustration |
| The Optimizer | Advanced and wanting more | Advanced experience OR intermediate with plateau |
| The Explorer | Still browsing options | Low readiness (exploring) |

### Decision 4: Two Entry Paths (Quiz + Challenge)

**What**: There are two ways into the funnel — the quiz (immediate results) and the 7-day challenge (sustained engagement).

**Why**: Different people buy differently. Some want information immediately (quiz → results → buy). Others need to experience your coaching before committing (challenge → 7 days of workouts → buy). Having both paths captures more leads at different stages of readiness. The quiz is your top-of-funnel magnet. The challenge is your trust-builder.

### Decision 5: Premium Tier as Waitlist

**What**: The $497/month Premium + Peptides tier is visible on all pages but cannot be purchased. Instead, it shows "Coming Soon" and captures waitlist signups.

**Why**: You haven't established physician partnerships yet, so you cannot deliver peptide prescribing services. Selling something you can't deliver creates legal liability and destroys trust. But keeping Premium visible serves two purposes: (1) it anchors the $197 tier as the "affordable" option (price anchoring), and (2) it builds a pre-qualified list of people who want the premium service when it launches.

### Decision 6: SMS-First Nurture

**What**: The 7-day nurture sequence alternates between SMS and email, with SMS carrying the most important messages (Day 0, Day 2 personal story, Day 4 social proof, Day 6 preview, Day 7 offer).

**Why**: SMS open rates are 98% vs. 20% for email. Your Twilio integration was already built and working. For a local Naples audience, text messages feel personal — like a friend checking in, not a marketing blast. Email carries the longer-form educational content (Day 1 training myths, Day 3 peptides, Day 5 signs).

### Decision 7: Digital Products Fund Ads

**What**: Three one-time digital products ($37, $67, $97) exist alongside the recurring coaching offer.

**Why**: Digital products serve three purposes: (1) they provide an entry point for people not ready for monthly coaching, (2) they fund your ad spend so coaching revenue is pure profit, and (3) they let people "test" your expertise before committing to coaching. A $37 Nutrition Blueprint buyer who gets value becomes a $197 coaching client later.

### Decision 8: Google Sheets as CRM (Not a $200/month SaaS)

**What**: All lead data lives in Google Sheets, not a dedicated CRM like HubSpot or GoHighLevel.

**Why**: At your current scale (0–30 clients), Google Sheets is free, infinitely customizable, and integrates natively with n8n. You don't need lead scoring algorithms or automated pipeline stages when you have 15 leads. When you hit 100+ leads per month, upgrade to a real CRM. Until then, Sheets works perfectly and costs nothing.

---

# Chapter 3: The Funnel Architecture

### Visual Overview

```
                     TRAFFIC SOURCES
                     ──────────────
                     Meta Ads ($15-20/day)
                     Instagram Reels / YouTube
                     Local partnerships (Naples)
                     Warm network outreach
                            │
                            ▼
              ┌──────────────────────────┐
              │     WEBSITE PAGES         │
              │                           │
              │  index.html (Homepage)    │
              │  coaching.html (Detail)   │
              │  peptides.html (Education)│
              │  programs.html (All Tiers)│
              └────────────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  QUIZ PAGE        │    │  CHALLENGE PAGE   │
    │  /quiz.html       │    │  /challenge.html  │
    │                   │    │                   │
    │  7-step quiz      │    │  7-day free       │
    │  → Archetype      │    │  challenge signup  │
    │  → Custom macros  │    │                   │
    │  → Results + CTAs │    │  → Daily SMS      │
    └────────┬──────────┘    │    workouts       │
             │               └────────┬──────────┘
             │                        │
    ┌────────┴────────┐    ┌──────────┴──────────┐
    │  n8n: Lead       │    │  n8n: Challenge     │
    │  Magnet Capture  │    │  Signup 7Day        │
    │  → Sheet         │    │  → Sheet            │
    │  → Day 0 SMS     │    │  → Welcome SMS      │
    │  → Day 0 Email   │    │  → 7 daily workouts │
    └────────┬─────────┘    └──────────┬──────────┘
             │                         │
    ┌────────┴────────┐    ┌───────────┴──────────┐
    │  n8n: Nurture    │    │  n8n: Challenge      │
    │  Sequence 7Day   │    │  Day7 Upsell         │
    │  → 7 days of     │    │  → Peptide branch    │
    │    SMS + Email    │    │  → Standard branch   │
    │  → Day 7: OFFER  │    └──────────────────────┘
    └────────┬─────────┘
             │
    ┌────────┴────────┐
    │  n8n: Non-       │
    │  Converter       │
    │  Followup        │
    │  → Day 10, 14, 30│
    └─────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │           CONVERSION EVENTS              │
    │                                          │
    │  Stripe $197/mo → Coaching Welcome       │
    │  Stripe $37-97  → Digital Product Delivery│
    │  Waitlist form  → Premium Waitlist Capture│
    └─────────────────────────────────────────┘
```

### The Two Funnels

**Funnel A: Quiz → Nurture → Offer** (7 days, automated)
1. Visitor takes quiz on /quiz.html
2. Gets custom macros + archetype assignment instantly
3. Lead-Magnet-Capture workflow fires → saves to Sheet, sends Day 0 SMS + email
4. Nurture-Sequence-7Day fires → 7 days of alternating SMS/email
5. Day 7: Direct coaching offer with Stripe link
6. If no purchase: Non-Converter-Followup → Day 10, 14, 30 follow-ups

**Funnel B: Challenge → Workouts → Upsell** (7 days, automated)
1. Visitor signs up for 7-day challenge on /challenge.html
2. Challenge-Signup-7Day fires → saves to Sheet, sends welcome, then 7 daily workout SMS
3. Challenge-Day7-Upsell runs at 8am daily → checks for Day 7 leads
4. Sends segmented upsell: Premium waitlist for peptide-interested, $197 coaching for others

Both funnels converge at the same Stripe payment links and the same Google Sheets lead database.

---

# Chapter 4: Website Pages — What They Do & How to Use Them

All pages are static HTML hosted on GitHub Pages at marceausolutions.com. They share a dark theme design system (navy/black backgrounds, green primary, amber accents, Montserrat headings, Inter body text).

### Page Map

| Page | URL | Role in Funnel |
|------|-----|---------------|
| Homepage | / | Awareness — introduces you, shows credibility |
| Coaching | /coaching.html | Consideration — detailed $197/mo offer page |
| Peptides | /peptides.html | Authority — peptide education, builds trust |
| Programs | /programs.html | Decision — all 5 tiers, pricing, buy buttons |
| Quiz | /quiz.html | Capture — lead magnet, collects contact info |
| Challenge | /challenge.html | Capture — free challenge signup |

### Homepage (index.html)

**Purpose**: First impression. Establishes who you are, what you do, and why you're different. Drives traffic to deeper pages.

**Key sections**:
- Hero with background video and coach photo
- Three value propositions (evidence-based, peptide expertise, real results)
- Training videos section (3 workout clips)
- Peptide overview with "Coming Soon" physician partnership framing
- Coaching program tiers (Starter/Performance/Elite — legacy naming)
- Backend services section (for influencers)

**How you use it**: This is your link-in-bio destination. When someone asks "what do you do?", send them here. All social media profiles should link to this page.

**How end users experience it**: They land here, get a quick sense of your brand, and click through to either the quiz, coaching page, or peptides page depending on their interest.

### Coaching Page (coaching.html)

**Purpose**: The detailed sales page for $197/month coaching. This is where interested leads go to understand exactly what they get.

**Key sections**:
- Hero with price display ($197/mo, $497 coming soon)
- "What You Get" 6-card grid (custom program, nutrition, peptide guidance, weekly check-ins, messaging access, AI tracking)
- "Not Your Typical Coach" comparison section
- 4-step "How It Works" timeline
- Embedded Calendly booking widget
- 6-question FAQ accordion
- Final CTA section with 4 options

**Key feature — Embedded Calendly**: The coaching page has a live Calendly widget at the #book anchor. Visitors can book a free 30-minute strategy call directly without leaving the page.

**How you use it**: Share this link when someone asks about coaching details. The page does the selling for you. The Calendly widget means they can book without you sending a separate link.

**How end users experience it**: They read the benefits, scroll through the FAQ to handle objections, then either click the Stripe link to buy immediately or book a call first.

### Peptides Page (peptides.html)

**Purpose**: Establish authority on peptides through education. This is NOT a sales page — it's a trust-building page.

**Key sections**:
- Evidence spectrum visualization (FDA-approved → research phase → anecdotal)
- Specific compound profiles (Tesamorelin, GH Secretagogues, BPC-157)
- "My Approach" 3-card grid (evidence first, physician partnership coming soon, track everything)
- "Is This Right for You?" decision framework
- Medical disclaimer (prominent, required)

**Critical compliance note**: All physician partnership language is framed as "coming soon." The page explicitly states: "I'm building partnerships with licensed physicians" (future tense). This protects you legally since you cannot currently offer prescribing services.

**How you use it**: Share when someone asks about peptides. Post it in response to peptide questions on social media. It positions you as the expert bridge between research and practical application.

**How end users experience it**: They learn what peptides are, see that you take an evidence-based approach, understand the "coming soon" physician partnership, and either join the waitlist or explore coaching.

### Programs Page (programs.html)

**Purpose**: The "menu" — shows all 5 tiers so leads can choose what fits them.

**Key sections**:
- Funnel path visualization (Free → Community → Digital → Coaching → Premium)
- Tier 0: Free Community + Challenge (with Skool link)
- Tier 1: Three digital products with Stripe buy buttons ($37, $67, $97)
- Tier 2: 1:1 Coaching at $197/mo with Stripe buy button
- Tier 3: Premium + Peptides at $497/mo with waitlist form
- "Not sure?" section with quiz and Calendly links
- Guarantee section

**The waitlist form**: The Premium tier card contains an inline form (name + email) that submits to the n8n Premium-Waitlist-Capture webhook. On success, it shows a confirmation message.

**How you use it**: Link people here when they ask "what do you offer?" or "what's the price?" It gives them every option from free to premium.

**How end users experience it**: They see all tiers, compare features, and either buy a digital product, start coaching, join the waitlist, or take the quiz/challenge.

### Quiz Page (quiz.html)

**Purpose**: The primary lead magnet. A 7-step interactive calculator that captures contact information in exchange for personalized fitness recommendations.

**Detailed in Chapter 5.**

### Challenge Page (challenge.html)

**Purpose**: The secondary lead magnet. A free 7-day challenge that demonstrates your coaching value through daily workouts delivered via SMS.

**Detailed in Chapter 6.**

---

# Chapter 5: The Quiz (Lead Magnet) — Deep Dive

### What It Is

A 7-step interactive "Body Recomp Calculator" that asks about goals, stats, experience, frustrations, peptide interest, readiness, and contact info. It then shows a personalized results page with calculated macros, a training recommendation, an archetype assignment, a readiness score, and a predicted goal date.

### The 7 Steps

| Step | Question | Input Type | Options |
|------|----------|-----------|---------|
| 1 | Primary goal | Single select | Lose Fat, Build Muscle, Body Recomp, Athletic Performance |
| 2 | Current stats | Number inputs | Age, Gender, Weight (lbs), Height |
| 3 | Training experience | Single select | Beginner, Intermediate, Advanced |
| 4 | Biggest frustration | Single select | Consistency, Plateau, Conflicting info, No accountability |
| 5 | Peptide interest | Single select | Yes interested, Curious, Not now |
| 6 | Readiness to commit | Single select | All in, Within 2 weeks, Exploring |
| 7 | Contact info | Text inputs | First name, Email, Phone |

### What Happens on Submit

1. The browser shows an animated "processing" screen (6 seconds) with dynamic status messages and educational facts
2. A POST request is sent to `https://n8n.marceausolutions.com/webhook/lead-magnet-capture` with all quiz data plus calculated results
3. The results page appears with personalized content

### The Calculations (Client-Side JavaScript)

**TDEE (Total Daily Energy Expenditure)** — Mifflin-St Jeor equation:
- Male: (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
- Female: (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
- Multiplied by activity factor based on experience level

**Macro Split** — Varies by goal:
- Fat loss: -500 calories, 40% protein / 30% carbs / 30% fat
- Muscle gain: +300 calories, 35% protein / 40% carbs / 25% fat
- Recomp: maintenance calories, 40% protein / 35% carbs / 25% fat
- Performance: +200 calories, 30% protein / 45% carbs / 25% fat

**Archetype Assignment** — Based on frustration + readiness + experience:
- The Igniter: Ready (all_in/soon) + frustrated (inconsistent/confused)
- The Comeback: Ready (all_in) + frustrated (plateau/confused)
- The Optimizer: Advanced experience OR intermediate with plateau
- The Explorer: Exploring readiness (default)

**Readiness Score** — 0 to 100 based on:
- Readiness level (+40 all_in, +25 soon, +10 exploring)
- Experience (+20 advanced, +15 intermediate, +10 beginner)
- Frustration type (+15 plateau, +10 inconsistent, +12 confused, +8 accountability)
- Peptide interest (+10 yes, +5 curious)

**Predicted Goal Date** — Weeks from today:
- Base: 12 weeks for fat loss, 16 for muscle, 14 for recomp, 10 for performance
- Modified by experience (-2 advanced, +0 intermediate, +2 beginner)
- Modified by readiness (-2 all_in, +0 soon, +4 exploring)

### Results Page CTAs (Tiered)

The results page shows different CTAs based on quiz answers:

1. **7-Day Challenge** (always shown, green badge "FREE") → /challenge.html
2. **1:1 Coaching** ($197/mo) → Stripe payment link
3. **Premium + Peptides** ($497/mo, "Coming Soon") → /programs.html#premium — **only shown if peptide interest is "yes" or "curious"**
4. **Digital Products / Strategy Call** → /programs.html or Calendly

### How You Use It

- This is your primary link for ads. Meta ad → quiz.html
- Share it in DMs when someone asks about training
- Post "Take the quiz" CTAs on Instagram Stories
- The quiz captures their phone number, which feeds your SMS nurture — your strongest channel

### How End Users Experience It

They click through 7 quick steps (most are single-click selections), see an animated processing screen that builds anticipation, then get a personalized results page that feels custom-made. The archetype gives them an identity ("I'm The Comeback"). The macros give them immediate actionable value. The CTAs give them a clear next step.

---

# Chapter 6: The 7-Day Challenge — Deep Dive

### What It Is

A free 7-day fitness challenge that delivers daily workouts via SMS. No cost, no credit card. The purpose is to let skeptical leads *experience* your coaching before paying.

### Signup Flow

1. Visitor fills out the form on /challenge.html (name, email, phone)
2. Form POSTs to `https://n8n.marceausolutions.com/webhook/challenge-signup`
3. Confirmation message appears: "You're In! Check your phone."
4. n8n fires: welcome SMS, welcome email, saves to Sheet

### The 7 Days (SMS Content)

| Day | Theme | Content |
|-----|-------|---------|
| 1 | Foundation | Baseline workout: Goblet Squats, Push-ups, DB Rows, Plank + 20-min walk |
| 2 | Nutrition Lock-In | Workout: RDLs, OH Press, Lunges, Face Pulls + protein timing tip |
| 3 | Progressive Overload | Repeat Day 1 exercises, add 5 lbs or 2 reps |
| 4 | Nutrition Check | Protein target reminder + hydration focus |
| 5 | Active Recovery | 30-min walk + stretching/yoga |
| 6 | Final Push | Full-body workout (hardest session) |
| 7 | Celebration | Results check + "what's next" teaser |

### Day 7 Upsell (Automated)

The Challenge-Day7-Upsell workflow runs every morning at 8 AM. It checks which leads signed up exactly 7 days ago, then sends a segmented SMS:

- **Peptide-interested leads**: Get Premium waitlist pitch + Peptide Masterclass ($97) + coaching ($197/mo)
- **Standard leads**: Get coaching pitch ($197/mo) + digital programs link

### How You Use It

- Share the challenge link when someone isn't ready to commit financially
- Post "Join my free challenge" on social media
- The challenge builds trust through doing, not just reading
- After 7 days of getting your workouts, they're warm leads

### How End Users Experience It

They sign up, immediately get a welcome text, then receive a workout every morning for 7 days. It feels like having a personal trainer in their pocket. On Day 7, they get a congratulations message with a natural upsell to continue with paid coaching.

---

# Chapter 7: n8n Workflow Automation — Complete Reference

All workflows run on your EC2 instance at n8n.marceausolutions.com. They are managed through the n8n visual editor. Here is every workflow, what triggers it, what it does, and how it connects to other workflows.

### Workflow 1: Lead-Magnet-Capture

| Field | Detail |
|-------|--------|
| **ID** | hgInaJCLffLFBX1G |
| **Trigger** | Webhook POST /webhook/lead-magnet-capture |
| **Status** | Active |

**What it does**:
1. Receives quiz submission data from the website
2. Returns success response to the browser (so the results page can show)
3. Saves the lead to Google Sheets "Leads" tab (20 columns: name, email, phone, goal, age, gender, weight, height, experience, peptide interest, macros, UTM params, date, status)
4. Sends Day 0 SMS: "Your custom plan is ready! Check your email."
5. Sends Day 0 Email: Personalized macro breakdown (calories, protein, carbs, fat)
6. Triggers Workflow 2 (Nurture-Sequence-7Day) via HTTP POST

**Chains to**: Workflow 2

### Workflow 2: Nurture-Sequence-7Day

| Field | Detail |
|-------|--------|
| **ID** | szuYee7gtQkzRn3L |
| **Trigger** | Webhook POST /webhook/nurture-sequence-start (called by Workflow 1) |
| **Status** | Active |

**What it does** (over 7 days):

| Day | Channel | Content | Purpose |
|-----|---------|---------|---------|
| 1 | Email | "#1 mistake I see in every gym" | Education — training myths |
| 2 | SMS | TBI recovery story (personal) | Vulnerability — builds connection |
| 3 | Email | "Why your coach doesn't know peptides" | Authority — peptide expertise |
| 4 | SMS | Client transformation (22 lbs in 12 weeks) | Social proof |
| 5 | Email | "3 signs your training isn't working" | Education — pre-frames offer |
| 6 | SMS | What coaching week looks like | Preview — reduces uncertainty |
| 7 | SMS + Email | THE OFFER: $197/mo, Stripe link, Calendly | Conversion — the ask |

After Day 7: Updates lead status in Sheet to "day7_offer_sent" and triggers Workflow 3.

**Chains to**: Workflow 3

### Workflow 3: Non-Converter-Followup

| Field | Detail |
|-------|--------|
| **ID** | Y2jfeIlTRDlbCHeS |
| **Trigger** | Webhook POST /webhook/non-converter-followup (called by Workflow 2) |
| **Status** | Active |

**What it does**:
- Day 10 SMS: Soft check-in, offer to answer questions, Calendly link
- Day 14 SMS: Urgency — "founding member rate won't last," Stripe link
- Day 30 Email: Pure value — protein tracking tip using their calculated target

**Chains to**: Nothing (terminal)

### Workflow 4: Challenge-Signup-7Day

| Field | Detail |
|-------|--------|
| **ID** | WTZDxLDQuSkIkcqf |
| **Trigger** | Webhook POST /webhook/challenge-signup |
| **Status** | Active |

**What it does**:
1. Receives challenge signup from website
2. Saves to Google Sheets with status "challenge_signup"
3. Sends welcome SMS explaining what to expect
4. Sends welcome email with week overview
5. Delivers 7 daily workout SMS (one per day, with 24-hour waits between)

**Chains to**: Workflow 5 reads the Sheet data this workflow writes

### Workflow 5: Challenge-Day7-Upsell

| Field | Detail |
|-------|--------|
| **ID** | Xza1DB4f4PIHw2lZ |
| **Trigger** | Daily schedule at 8:00 AM |
| **Status** | Active |

**What it does**:
1. Reads all leads from Google Sheet
2. Filters for "challenge_signup" status where signup was 7 days ago
3. Checks peptide interest:
   - **Peptide-interested**: SMS with Premium waitlist + Masterclass $97 + coaching $197
   - **Standard**: SMS with coaching $197 + digital programs link
4. Updates Sheet status to "day7_waitlist_sent" or "day7_standard_sent"

**Chains to**: Nothing (terminal)

### Workflow 6: Coaching-Payment-Welcome

| Field | Detail |
|-------|--------|
| **ID** | 1wS9VvXIt95BrR9V |
| **Trigger** | Stripe event: checkout.session.completed |
| **Status** | Active |

**What it does** (when someone pays $197/mo):
1. Extracts client name, email, phone from Stripe session
2. Adds to "Client Roster" sheet (separate spreadsheet from Leads)
3. Sends welcome SMS with Calendly kickoff call link
4. Sends welcome email with two actions: (a) Book kickoff call, (b) Complete intake form (Google Form)
5. Logs payment to "Billing" sheet
6. Sends admin notification SMS to your phone (+1 239-398-5676) with client name and amount

**Chains to**: Nothing (terminal)

### Workflow 7: Premium-Waitlist-Capture

| Field | Detail |
|-------|--------|
| **ID** | j306crRxCmWW3dMo |
| **Trigger** | Webhook POST /webhook/premium-waitlist |
| **Status** | Active |

**What it does**:
1. Receives waitlist form submission from programs.html
2. Returns success response to browser
3. Saves to "Premium Waitlist" tab in Leads spreadsheet
4. Sends confirmation email with what's being built + cross-sells Peptide Masterclass ($97)

**Chains to**: Nothing (terminal)

### Workflow 8: Digital-Product-Delivery

| Field | Detail |
|-------|--------|
| **ID** | kk7ZjWtjmZgylVzi |
| **Trigger** | Stripe event: checkout.session.completed |
| **Status** | Active |

**What it does** (when someone buys a digital product):
1. Receives Stripe payment event
2. Identifies product by amount: $67 = Recomp Program, $37 = Nutrition Blueprint, $97 = Masterclass
3. If recognized: sends delivery email with Skool access link
4. Updates lead's row in Leads sheet with purchase info

**Chains to**: Nothing (terminal)

### Workflow Chain Map

```
Quiz Submit
    └──> [1] Lead-Magnet-Capture
              └──> [2] Nurture-Sequence-7Day (via webhook)
                        └──> [3] Non-Converter-Followup (via webhook)

Challenge Signup
    └──> [4] Challenge-Signup-7Day
              └──> [5] Challenge-Day7-Upsell (via shared Sheet, daily poll)

Stripe $197 Payment
    └──> [6] Coaching-Payment-Welcome

Waitlist Form
    └──> [7] Premium-Waitlist-Capture

Stripe $37-97 Payment
    └──> [8] Digital-Product-Delivery
```

---

# Chapter 8: Stripe Payment Infrastructure

### Products & Payment Links

| Product | Stripe Product ID | Price | Payment Link |
|---------|------------------|-------|-------------|
| 8-Week Recomp Program | prod_U4jezcD1vz00DB | $67 one-time | buy.stripe.com/eVq28r6pxbiM8oMg9Ag3605 |
| Nutrition Blueprint | prod_U4jeBo7zPtDken | $37 one-time | buy.stripe.com/eVqaEX9BJ1Ic0Wk7D4g3606 |
| Peptide Masterclass | prod_U4jfzm92znLSap | $97 one-time | buy.stripe.com/3cI00jg070E86gE9Lcg3607 |
| 1:1 Coaching | (existing) | $197/month recurring | buy.stripe.com/14A14n29hdqU48wf5wg3601 |
| Premium + Peptides | prod_U4jf4vyZUW3Evs | $497/month recurring | buy.stripe.com/dRmbJ1aFNgD60Wkg9Ag3608 (NOT linked on site — waitlist only) |

### How Payments Flow

1. **Customer clicks Stripe link** on website or in SMS/email
2. **Stripe Checkout** handles the payment (hosted by Stripe — you don't touch card data)
3. **Stripe fires webhook** to n8n on successful checkout
4. **n8n processes**: Either Coaching-Payment-Welcome (for $197) or Digital-Product-Delivery (for $37-97)
5. **Customer receives**: Welcome SMS, welcome email, and/or product access link

### Important Notes

- Stripe takes 2.9% + $0.30 per transaction
- Recurring subscriptions auto-bill monthly — no action needed from you
- The Premium payment link exists but is NOT linked on any website page. It's reserved for when physician partnerships are established.
- Failed payments are handled by Stripe's built-in retry logic (3 attempts over ~1 week)
- Cancellations: Customers can cancel via Stripe's customer portal, or you can cancel manually in the Stripe dashboard

---

# Chapter 9: Google Sheets Data Architecture

### Two Spreadsheets

**Spreadsheet 1: Leads Database** (ID: 13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E)

Used by: Workflows 1, 2, 4, 5, 7, 8

| Tab | Purpose | Key Columns |
|-----|---------|-------------|
| Leads | Master lead database | Name, Email, Phone, Goal, Age, Gender, Weight, Height, Experience, Peptide Interest, Calories, Protein, Carbs, Fat, Source, Date, Nurture Status, Converted, Digital Purchase |
| Premium Waitlist | Premium tier interest | Name, Email, Date, Source |
| Metrics | Weekly tracking | Leads, Sources, Conversions, Ad Spend, CAC, MRR |

**Spreadsheet 2: Client Operations** (ID: 1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA)

Used by: Workflow 6

| Tab | Purpose | Key Columns |
|-----|---------|-------------|
| Client Roster | Active paying clients | Full Name, Email, Phone, Start Date, Status, Stripe Customer ID |
| Billing | Payment records | Date, Client Name, Amount, Status, Stripe Payment ID |

### Nurture Status Values

The "Nurture Status" column in the Leads tab tracks where each lead is in the funnel:

| Status Value | Meaning | Set By |
|-------------|---------|--------|
| Day 0 | Just submitted quiz, Day 0 messages sent | Workflow 1 |
| challenge_signup | Joined free challenge | Workflow 4 |
| day7_offer_sent | Received Day 7 coaching offer (quiz path) | Workflow 2 |
| day7_waitlist_sent | Received Day 7 waitlist pitch (challenge, peptide-interested) | Workflow 5 |
| day7_standard_sent | Received Day 7 coaching pitch (challenge, standard) | Workflow 5 |

---

# Chapter 10: The Operator's Playbook — How You Interact With the System

This is the section you'll reference most often. It covers your daily, weekly, and monthly responsibilities as the operator of this system.

### Daily (5 minutes)

**Check your phone for admin notifications**. Workflow 6 sends you an SMS every time someone pays. If you see "New client: [Name] — $197.00", that means the system worked end-to-end.

**Check the Leads sheet** (optional but recommended in the first few weeks). Look at new entries — are quiz submissions coming in? Are challenge signups happening? Is the nurture status updating (Day 0 → day7_offer_sent)?

### Weekly (15 minutes)

**Review the Metrics tab**. Update it with this week's numbers:
- How many new leads?
- What source (quiz vs. challenge, organic vs. ad)?
- How many reached Day 7?
- How many converted?
- What was your ad spend?
- What's your cost per lead and cost per client?

**Check Skool community**. Are challenge participants engaging? Post a welcome message for new members. Share a quick tip. The community is your retention tool.

**Respond to waitlist signups** (Premium Waitlist tab). If someone joins the waitlist, consider sending them a personal DM. These are your highest-intent leads.

### Monthly (30 minutes)

**Review conversion rates**. If less than 10% of Day 7 leads are converting, the offer message may need tweaking. If less than 40% of quiz visitors complete the quiz, a step may be confusing.

**Check Stripe dashboard**. Look at MRR, churn, and failed payments. Reach out to clients with failed payments before Stripe's retry expires.

**Update ad creative** (when running ads). Meta recommends refreshing creatives every 2-4 weeks to avoid ad fatigue.

### When You Get a New Client

The system handles 90% of onboarding automatically:
1. ✅ Welcome SMS (auto — Workflow 6)
2. ✅ Welcome email with kickoff call booking + intake form (auto — Workflow 6)
3. ✅ Added to Client Roster sheet (auto — Workflow 6)
4. ✅ Payment logged (auto — Workflow 6)
5. ✅ Admin notification to your phone (auto — Workflow 6)

**What you do manually**:
6. Review their intake form responses (Google Form submission)
7. Do the kickoff call (Calendly, they book it)
8. Build their custom program within 48 hours
9. Send the program via whatever method you prefer (PDF, app, Skool post)
10. Start weekly check-ins

### When Someone Joins the Waitlist

The system handles the capture:
1. ✅ Saved to Premium Waitlist sheet (auto — Workflow 7)
2. ✅ Confirmation email sent with Masterclass cross-sell (auto — Workflow 7)

**What you do manually**:
3. Consider sending a personal text or email
4. When physician partnerships are finalized, email the waitlist to announce the launch

### Deploying Website Changes

All website files are in `projects/marceau-solutions/website/`. After editing, deploy with:

```bash
./scripts/deploy_website.sh marceau-solutions
```

This pushes changes to GitHub Pages. Changes go live within 1-2 minutes.

### Editing n8n Workflows

Access the n8n editor at http://34.193.98.97:5678. Or use n8n.marceausolutions.com if DNS is configured.

**Important**: Always test changes before activating. Use the "Execute Workflow" button in the editor with test data. Check that SMS and emails send correctly before going live.

---

# Chapter 11: The End User's Journey — What Your Clients Experience

This chapter walks through the complete experience from the client's perspective.

### Journey 1: The Quiz Path

**Minute 0 — Discovery**
Sarah sees your Instagram Reel about progressive overload. She clicks the link in your bio.

**Minute 1 — Homepage**
She lands on marceausolutions.com. The hero video catches her eye. She reads "Evidence-Based Training" and "Peptide Expertise." She clicks "Get Your Free Custom Plan."

**Minute 2 — Quiz**
She goes through 7 steps: selects "Lose Fat," enters her stats (age 34, 155 lbs, 5'6"), selects "Intermediate" experience, says her biggest frustration is hitting a plateau, marks "Curious" about peptides, says she's ready "Within 2 weeks," and enters her name, email, and phone.

**Minute 3 — Processing + Results**
An animated processing screen shows her plan being built. Educational facts appear ("Your TDEE is calculated using the Mifflin-St Jeor equation..."). Then her results: She's "The Comeback" archetype. Readiness score: 72. Predicted goal date: 14 weeks out. Custom macros: 1,800 calories, 155g protein, 158g carbs, 60g fat.

**Minute 3 — Day 0 Messages**
Her phone buzzes: "Hey Sarah, your custom plan is ready! Check your email for your macro targets." Her inbox has a formatted email with her macro breakdown and training recommendation.

**Days 1-6 — Nurture Sequence**
Over the next week, she gets alternating messages:
- Day 1 email about training mistakes
- Day 2 text about your TBI story
- Day 3 email about peptides (she clicked "curious" so this feels relevant)
- Day 4 text with a client transformation
- Day 5 email about signs her program isn't working (hits close to home — she's plateaued)
- Day 6 text showing what coaching looks like

**Day 7 — The Offer**
She gets a text: "I've got 3 spots open for March coaching. $197/mo — custom training, nutrition, weekly check-ins..." and a Stripe link. She also gets a detailed email with the full offer breakdown.

**Day 7 — She Clicks the Link**
She pays $197 through Stripe Checkout. Within seconds, she gets a welcome text with a kickoff call link and a welcome email with the intake form.

**Day 8 — Onboarding**
She books a kickoff call for Thursday, fills out the intake form. You review it, build her program, and she starts coaching.

### Journey 2: The Challenge Path

**Day 0 — Sign Up**
Mike finds your challenge page through a Facebook ad. "7-Day Body Recomp Challenge — FREE." He enters his info.

**Day 0 — Welcome**
His phone buzzes: "Welcome to the 7-Day Recomp Challenge! Here's what to expect..." He gets an email with the week overview.

**Days 1-7 — Workouts**
Every morning, he gets a workout via text:
- Day 1: Foundation workout (goblet squats, push-ups, DB rows, plank)
- Day 2: Nutrition-focused workout + protein timing tip
- Day 3: Progressive overload — same exercises as Day 1, heavier
- Day 4: Protein check-in
- Day 5: Active recovery
- Day 6: Full-body final push
- Day 7: Celebration + results

**Day 7 — Upsell**
Mike marked "Yes" for peptide interest in his quiz. His Day 7 text includes: "Want to keep the momentum? Join the Premium waitlist for peptide-optimized coaching, or start 1:1 coaching at $197/mo..." with links to the waitlist, Stripe, and Calendly.

### Journey 3: The Digital Product Buyer

**The Purchase**
Rachel browses /programs.html and clicks "Get the Nutrition Blueprint" ($37). She pays through Stripe Checkout.

**The Delivery**
Within seconds, she gets an email: "Your Nutrition Blueprint is ready!" with a link to access it on Skool. Her purchase is logged in the Leads sheet.

**The Upsell**
Rachel is now in the Skool community. She sees other members doing the challenge, talking about coaching. Eventually she upgrades to $197/mo coaching.

---

# Chapter 12: Troubleshooting & Maintenance

### Common Issues

**"A lead took the quiz but didn't appear in the Sheet"**
1. Check the n8n workflow execution log for Lead-Magnet-Capture
2. Look for errors in the Google Sheets node (permissions, column mismatch)
3. Verify the webhook URL in quiz.html matches the n8n webhook path

**"Someone paid but didn't get a welcome message"**
1. Check the Stripe webhook events in your Stripe dashboard
2. Check Coaching-Payment-Welcome execution log in n8n
3. Verify Twilio and Gmail credentials haven't expired

**"The challenge SMS stopped after Day 2"**
1. Open Challenge-Signup-7Day in n8n
2. Check the execution — look for which Wait node it's paused at
3. n8n Wait nodes require the workflow to stay active. If the workflow was deactivated and reactivated, in-flight executions are lost.

**"Premium waitlist form isn't submitting"**
1. Check browser console for CORS errors
2. Verify the webhook URL in programs.html matches the n8n webhook path
3. Test the webhook directly with curl:
```bash
curl -X POST https://n8n.marceausolutions.com/webhook/premium-waitlist \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","source":"test"}'
```

### Credentials to Monitor

| Service | Credential | Expires? | How to Renew |
|---------|-----------|----------|-------------|
| Google Sheets | OAuth2 token | Yes (refreshes auto) | Re-authenticate in n8n if refresh fails |
| Twilio | API key | No | N/A |
| Stripe | Webhook secret | No | N/A |
| Gmail SMTP | App password | No (unless you change Google password) | Generate new app password in Google settings |

### Backup & Recovery

- **Website files**: Git-tracked in dev-sandbox, deployed to GitHub Pages
- **n8n workflows**: Can be exported to JSON via n8n API or editor
- **Google Sheets**: Google's version history provides automatic backups
- **Stripe data**: Lives in Stripe's dashboard — no backup needed

---

# Chapter 13: Growth Roadmap

### Phase 1: First 10 Clients (Weeks 1-8)

You're here now. Focus on:
- Warm outreach (text 20 people you know)
- 3 gym conversations per week
- Set up Instagram (bio + first 9 posts)
- Start posting 3-5 Reels per week
- Launch Meta ads at $15/day targeting Naples, FL

**Target**: 10 paying clients = $1,970+ MRR

### Phase 2: Scale to 30 Clients (Months 2-4)

- Scale winning ads to $25-30/day
- Add retargeting (Facebook Pixel on all pages)
- Collect and publish client testimonials
- Launch referral program ("Refer a friend, get 1 month free")
- Start YouTube (monthly long-form content)
- Contact 5 local businesses for referral partnerships

**Target**: 30 clients = $5,910+ MRR

### Phase 3: Activate Premium Tier (Month 4+)

- Finalize physician partnerships
- Convert Premium from waitlist to live purchase
- Email waitlist list to announce launch
- Update all 6 website pages (remove "Coming Soon")
- Activate the $497/mo Stripe link on programs.html

**Target**: Mix of $197 and $497 clients = $8,000-12,000 MRR

### Phase 4: Systematize & Scale (Month 6+)

- Hire a VA for community management
- Build more digital products
- Consider group coaching tier
- Explore coach-the-coach program (Propane's highest-margin product)
- Evaluate upgrading from Google Sheets to a real CRM

**Target**: $15,000+ MRR, working ON the business not just IN it

---

# Appendix A: All URLs & Links

| Asset | URL |
|-------|-----|
| Homepage | marceausolutions.com |
| Coaching Page | marceausolutions.com/coaching.html |
| Peptides Page | marceausolutions.com/peptides.html |
| Programs Page | marceausolutions.com/programs.html |
| Quiz Page | marceausolutions.com/quiz.html |
| Challenge Page | marceausolutions.com/challenge.html |
| Skool Community | skool.com/unbreakable-9502 |
| Calendly (Strategy Call) | calendly.com/wmarceau/30min |
| Calendly (Kickoff Call) | calendly.com/wmarceau/kickoff-call |
| n8n Editor | n8n.marceausolutions.com (or 34.193.98.97:5678) |
| Stripe Dashboard | dashboard.stripe.com |
| Leads Sheet | docs.google.com/spreadsheets/d/13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E |
| Client Ops Sheet | docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA |

# Appendix B: All n8n Webhook URLs

| Webhook | URL | Triggered By |
|---------|-----|-------------|
| Lead Magnet Capture | n8n.marceausolutions.com/webhook/lead-magnet-capture | Quiz submission |
| Nurture Sequence Start | n8n.marceausolutions.com/webhook/nurture-sequence-start | Workflow 1 |
| Non-Converter Followup | n8n.marceausolutions.com/webhook/non-converter-followup | Workflow 2 |
| Challenge Signup | n8n.marceausolutions.com/webhook/challenge-signup | Challenge form |
| Premium Waitlist | n8n.marceausolutions.com/webhook/premium-waitlist | Waitlist form |

# Appendix C: All Stripe Payment Links

| Product | Price | Link |
|---------|-------|------|
| 1:1 Coaching | $197/mo | buy.stripe.com/14A14n29hdqU48wf5wg3601 |
| 8-Week Recomp | $67 | buy.stripe.com/eVq28r6pxbiM8oMg9Ag3605 |
| Nutrition Blueprint | $37 | buy.stripe.com/eVqaEX9BJ1Ic0Wk7D4g3606 |
| Peptide Masterclass | $97 | buy.stripe.com/3cI00jg070E86gE9Lcg3607 |
| Premium + Peptides | $497/mo | buy.stripe.com/dRmbJ1aFNgD60Wkg9Ag3608 (WAITLIST ONLY) |

---

*This document was generated on March 2, 2026. System built by William Marceau with Claude Code (Opus 4.6) as engineering partner.*
