# PT Business Operations Manual

**Complete System Guide — Architecture, Trade-Offs & Decision Validations**

*William Marceau | Marceau Solutions | March 5, 2026 — v2.1*

## 1. System Overview

Marceau Solutions operates a 1:1 fitness coaching business at $197/month, built on a fully automated infrastructure. Every component — from lead capture to payment processing to weekly check-ins — runs on systems you own and control.

### Architecture Summary

- **Website**: Static HTML at marceausolutions.com (GitHub Pages)
- **Automation**: n8n on EC2 (17 active workflows)
- **SMS**: Twilio +1 (855) 239-9364 (19 templates, TCPA compliant)
- **Payments**: Stripe subscriptions ($197/mo recurring)
- **CRM**: Google Sheets (Leads + Client Tracker)
- **Client Portal**: fitai.marceausolutions.com/client/ (gamification, workouts, progress)
- **Notifications**: Telegram bot (@w_marceaubot)
- **AI Agents**: Claude Code (interactive) + Clawdbot (Telegram 24/7) + Ralph (complex builds)

### Three-Agent Model

- **Claude Code** (Mac terminal): Interactive work, complex implementations, publishing
- **Clawdbot** (EC2/Telegram): Quick tasks, research, complexity 0-6
- **Ralph** (EC2/autonomous): Multi-story builds, complexity 7-10

All agents share memory via Mem0 API on EC2 port 5020.

---

## 2. Sales Funnel Architecture

### Lead Capture Paths

- **Quiz Funnel**: marceausolutions.com/quiz.html -> Webhook -> Lead-Magnet-Capture workflow -> Leads Sheet -> Day 0 SMS + Email -> Nurture-Sequence-7Day
- **Challenge Funnel**: marceausolutions.com/challenge.html -> Webhook -> Challenge-Signup-7Day workflow -> 7-day workout emails -> Challenge-Day7-Upsell
- **Premium Waitlist**: marceausolutions.com/programs.html -> Webhook -> Premium-Waitlist-Capture workflow -> Confirmation email
- **Contact Form**: marceausolutions.com/contact.html -> Webhook -> Website-Lead-Capture workflow

### Nurture Sequence (Post-Quiz)

- Day 0: Welcome SMS + email with quiz results
- Day 1: "Your Plan" email
- Day 3: Training tip SMS
- Day 5: Peptide education email
- Day 7: Strategy call CTA (Calendly link)
- If no conversion: Non-Converter-Followup (Day 10-60)

### Non-Converter Follow-Up (7 Touches, Day 10-60)

- Day 10: SMS — Soft check-in + Calendly link
- Day 14: SMS — Founding member rate ($197/mo) + Stripe link
- Day 21: Email — Value tip using quiz data (protein target)
- Day 30: Email — "Breakup" positioning ("No hard feelings")
- Day 45: SMS — Social proof ("A client just hit their milestone")
- Day 60: Email — Re-engagement with testimonial + Stripe link
- After Day 60: Lead marked as sequence_complete

### Conversion Path

- Lead clicks Stripe link ($197/mo) -> Stripe webhook fires -> Coaching-Payment-Welcome workflow -> Welcome SMS + email + client folder creation + portal account + starter workout assigned

---

## 3. n8n Workflow Registry (17 Active)

### Coaching Operations (5 workflows)

- **Coaching-Monday-Checkin** (aBxCj48nGQVLRRnq): Monday 9 AM ET — reads Client Tracker Sheet, sends personalized check-in SMS to all active clients
- **Coaching-Payment-Welcome** (1wS9VvXIt95BrR9V): Stripe payment via `/webhook/stripe-payment-welcome` — welcome SMS + email + Sheet update + portal account creation + billing log
- **Coaching-Cancellation-Exit** (uKjqRexDIheaDJJH): Stripe cancel via `/webhook/stripe-cancellation` — feedback SMS + re-engagement sequence (Day 7 + Day 30)
- **Fitness-SMS-Outreach** (89XxmBQMEej15nak): Prospect outreach via webhook trigger
- **Fitness-SMS-Followup-Sequence** (VKC5cifm595JNcwG): Multi-step SMS drip with configurable delays

### Funnel & Lead Acquisition (8 workflows)

- **Lead-Magnet-Capture** (hgInaJCLffLFBX1G): Quiz form webhook -> Leads Sheet + Day 0 SMS + email
- **Nurture-Sequence-7Day** (szuYee7gtQkzRn3L): 7-day automated nurture (SMS + email)
- **Non-Converter-Followup** (Y2jfeIlTRDlbCHeS): Day 10-60 multi-touch sequence with lead removal logic
- **Challenge-Signup-7Day** (WTZDxLDQuSkIkcqf): Challenge form -> 7-day workout delivery
- **Challenge-Day7-Upsell** (Xza1DB4f4PIHw2lZ): Day 7 coaching upsell after challenge
- **Premium-Waitlist-Capture** (j306crRxCmWW3dMo): Premium tier waitlist form processing
- **Digital-Product-Delivery** (kk7ZjWtjmZgylVzi): Stripe payment via `/webhook/stripe-digital-delivery` -> digital product delivery
- **SMS-Response-Handler-v2** (G14Mb6lpeFZVYGwa): Twilio webhook -> STOP detection + auto-unsubscribe + response logging + Telegram notification

### Utility & Monitoring (4 workflows)

- **n8n-Health-Check** (QhDtNagsZFUrKFsG): Daily 6 AM ET — checks health endpoint + verifies all 13 critical workflows are active. Alerts via SMS + Telegram.
- **Weekly-Campaign-Analytics** (M62QBpROE48mEgDC): Monday 7 AM ET — pulls Twilio logs, calculates delivery/reply/opt-out rates, writes to Campaign Analytics Sheet tab, sends SMS + Telegram summary.
- **Monthly-Workflow-Backup** (2QaQbhIUlL7ctfq4): 1st of month 3 AM ET — exports all workflows to JSON, git commits + pushes.
- **GitHub Push Notifications** (BsoplLFe1brLCBof): Every git push -> Telegram notification.

---

## 4. SMS System & TCPA Compliance

### 19 Templates (All Compliant — Audited March 4, 2026)

**Compliance Rules:**
- First message in each sequence MUST have identification + "Reply STOP to opt out"
- All messages have sender identification ("This is William" or "— William")
- Sending window: 8 AM - 9 PM recipient's local time only
- TCPA quiet hours enforcement built into twilio_sms.py

**Template Categories:**
- Prospect Outreach (7 templates): Day 0, 2, 5, 10, 15, 30, 60
- Client Onboarding (3): Welcome, kickoff reminder, pre-call
- Weekly Check-Ins (3): Monday check-in, midweek tip, no-response follow-up
- Offboarding (3): Cancel feedback, Day 7, Day 30
- Billing (2): Payment failed, payment failed follow-up
- Testimonials (3): 30-day, 90-day, referral reward
- General (1): Appointment reminder

### Inbound SMS Handling

All inbound SMS are processed by SMS-Response-Handler-v2:
- STOP/UNSUBSCRIBE/CANCEL/QUIT -> Lead marked opted_out + confirmation sent + Telegram alert
- Regular replies -> Logged to Responses tab in Leads Sheet + Telegram notification to William
- Twilio webhook: https://n8n.marceausolutions.com/webhook/sms-response

---

## 5. Client Lifecycle

### Onboarding (Automated — SLA: 60 seconds to first value)

1. Stripe payment received
2. n8n Coaching-Payment-Welcome fires:
   - Welcome SMS sent
   - Onboarding email with Calendly kickoff link + intake form
   - Client added to Client Tracker Sheet
   - Google Drive folder created
   - Client portal account created with magic link
   - Starter workout assigned in portal
3. Manual follow-up: Book kickoff call within 48h, review intake form

### Weekly Cadence

- Sunday PM: Upload program PDF to client Drive (manual)
- Monday 9 AM: Check-in SMS to all clients (automated)
- Tuesday: Follow up non-responders (manual)
- Wednesday: Mid-week tip SMS (manual, uses midweek-tips.json — 30 tips)
- Friday: Review check-ins, update Sheet (manual)
- Month end: 15-min progress review via Calendly (manual)

### Offboarding (Automated + Manual)

1. Stripe cancellation detected
2. n8n Coaching-Cancellation-Exit fires:
   - Feedback SMS: "No hard feelings. What could I do better?"
   - Day 7: Encouragement SMS
   - Day 30: Returning client discount offer
3. Manual: Update tracker, archive Drive folder, document cancel reason

---

## 6. Analytics & Monitoring

### Automated (n8n)

- **Daily 6 AM**: Health check — all 13 critical workflows verified active
- **Monday 7 AM**: Weekly SMS report — delivery rate, reply rate, opt-out rate, cost
- **Monthly 1st**: Workflow backup to GitHub

### Manual (Scripts)

- `python execution/coaching_analytics.py --report weekly` — SMS performance report
- `python execution/coaching_analytics.py --report funnel` — Lead funnel conversion report
- `python execution/coaching_analytics.py --health-check` — Infrastructure health check

### Key Metrics Targets

- SMS delivery rate: >95%
- Reply rate: 2-5%
- Opt-out rate: <2%
- Quiz-to-call conversion: >10%
- Call-to-client conversion: >30%

### Google Sheets Tabs

- **Leads** tab: All lead data (name, email, phone, quiz results, nurture status)
- **Responses** tab: All inbound SMS replies (date, from, message, category, responded)
- **Campaign Analytics** tab: Weekly SMS metrics (sent, delivered, rates, cost)
- **Weekly Metrics** tab: Manual performance tracking

---

## 7. Decision Validation Matrix

Every major architectural choice has been validated against alternatives.

### Why $197/month?

- **Rationale**: Sweet spot between accessibility and perceived value. Below $200 removes "I need to think about it." Above $150 signals serious coaching.
- **Alternatives considered**: Per-session ($100-150/session), tiered ($97/$197/$297), annual ($1,970/year)
- **Trade-off**: Lower than premium coaches ($300-500/mo) but appropriate for zero-client launch. Price can increase with testimonials.
- **Review trigger**: Raise to $247 after 10 active clients with retention >3 months

### Why Peptide Focus?

- **Rationale**: Blue ocean differentiation in Naples market. Zero local competitors combining evidence-based training with peptide education.
- **Alternatives considered**: General fitness coaching, bodybuilding specialization, weight loss only
- **Trade-off**: Smaller addressable market but zero competition. Requires careful legal positioning (education only, not prescribing).
- **Review trigger**: If peptide regulations tighten, pivot to "evidence-based optimization" umbrella

### Why Naples + Online?

- **Rationale**: Local trust bootstraps testimonials. Naples affluent demographics ($80k+ median income) match premium coaching. Online scales beyond hours-in-the-day.
- **Alternatives considered**: Online only, single-gym partnership, multi-city
- **Trade-off**: Two marketing tracks (local SEO + online content) vs. focusing on one.
- **Review trigger**: If local pipeline sufficient (5+ clients), reduce online marketing spend

### Why Stripe Over Square/PayPal?

- **Rationale**: Native subscription management. Webhook automation with n8n. Already integrated (19 templates + 3 workflows). Payment links work in SMS.
- **Alternatives considered**: Square (simpler POS), PayPal (wider reach), Gumroad (digital products)
- **Trade-off**: 2.9% + $0.30 per transaction vs. Square's 2.6%. Worth it for subscription + webhook capabilities.
- **Review trigger**: If transaction volume >$10k/mo, negotiate custom Stripe rate

### Why n8n Over Zapier?

- **Rationale**: Free self-hosted. Unlimited executions. Full data ownership. 17+ workflows already running on EC2. No monthly fee.
- **Alternatives considered**: Zapier ($49-149/mo), Make.com ($9-29/mo), custom Python scripts
- **Trade-off**: Requires EC2 maintenance (~$15/mo) and self-management. No support team.
- **Review trigger**: If workflow count >50 or uptime <99%, consider managed n8n cloud

### Why Twilio Over Alternatives?

- **Rationale**: Already integrated (19 templates). Usage-based pricing (~$12/mo at current volume). API flexibility. Local Naples number (+1 239 area code) for better deliverability and trust.
- **Alternatives considered**: MessageBird, Plivo, native carrier SMS
- **Trade-off**: Local number has better deliverability than toll-free. $0.0079/SMS adds up at scale.
- **Review trigger**: If monthly SMS cost >$100, evaluate 10DLC registration for higher throughput

### Why Static HTML Over WordPress/Webflow?

- **Rationale**: Zero hosting cost (GitHub Pages). No dependencies to update. Sub-second load times. Full control over every element. Claude Code can edit directly.
- **Alternatives considered**: WordPress ($20-50/mo hosting), Webflow ($14-39/mo), Squarespace ($16-49/mo)
- **Trade-off**: No CMS for non-technical editing. No built-in blog comments or forms (use webhooks instead).
- **Review trigger**: If William hires a marketing person who can't code, migrate blog to WordPress

### Why Google Sheets as CRM?

- **Rationale**: Free. n8n native integration. Scale-appropriate for 0-30 clients. Easy to export. Everyone knows how to use it.
- **Alternatives considered**: HubSpot Free ($0, limited), Notion ($8-10/mo), Airtable ($20/mo), custom database
- **Trade-off**: No automated follow-up triggers within Sheets (n8n handles this). Manual data entry for some fields.
- **Review trigger**: If leads >100/month or clients >30, evaluate HubSpot Free CRM migration

### Why Subscription Over Per-Session?

- **Rationale**: Predictable MRR for financial planning. Scalable online delivery model. Automation-friendly (Stripe recurring handles everything). Enables no-call conversion via payment link.
- **Alternatives considered**: Per-session ($100-150), session packages (4-pack, 8-pack), hybrid
- **Trade-off**: Client may feel locked in. Requires delivering ongoing value to prevent churn. No "try one session" option.
- **Review trigger**: If churn >20% in first 3 months, add $47 "trial month" tier

---

## 8. Quick Reference

### Key Links

- Website: marceausolutions.com
- Stripe Dashboard: dashboard.stripe.com
- Payment Link: buy.stripe.com/14A14n29hdqU48wf5wg3601
- Calendly (free call): calendly.com/wmarceau/30min
- Calendly (kickoff): calendly.com/wmarceau/kickoff-call
- n8n Dashboard: n8n.marceausolutions.com
- Client Portal: fitai.marceausolutions.com/client/
- Client Tracker Sheet: docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA
- Leads Sheet: docs.google.com/spreadsheets/d/13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E

### Phone Numbers

- Business (Twilio): +1 (855) 239-9364
- Admin (William): +1 239 398 5676

### Common Commands

- Send SMS: `python execution/twilio_sms.py --template <name> --to <phone> --name <name>`
- Weekly report: `python execution/coaching_analytics.py --report weekly`
- Funnel report: `python execution/coaching_analytics.py --report funnel`
- Health check: `python execution/coaching_analytics.py --health-check`
- Backup workflows: `./scripts/backup-n8n-workflows.sh`
- Create client tracker: `python scripts/create-coaching-tracker-sheet.py`
- Create client Drive folder: `python scripts/create-coaching-drive-folders.py`

### Pricing Tiers

- Free: Quiz results + macro calculator (LIVE)
- $37: Nutrition Blueprint (LIVE)
- $67: 30-Day Recomp Program (LIVE)
- $97: Peptide Masterclass (LIVE)
- $197/mo: 1:1 Coaching (LIVE — primary offer)
- $497/mo: Premium VIP (WAITLIST)

---

## 9. File Locations

### Business Hub

- Master Runbook: projects/marceau-solutions/pt-business/ops/coaching-ops-runbook.md
- Legal Docs: projects/marceau-solutions/pt-business/legal/
- Content Strategy: projects/marceau-solutions/pt-business/content/
- Business Planning: projects/marceau-solutions/pt-business/business-planning/
- Workflows: projects/marceau-solutions/pt-business/workflows/
- Decision Matrix: projects/marceau-solutions/pt-business/business-planning/DECISION-VALIDATION-MATRIX.md

### Shared Scripts

- SMS: execution/twilio_sms.py (19 templates)
- Analytics: execution/coaching_analytics.py
- Onboarding Email: execution/send_onboarding_email.py
- Stripe: execution/stripe_payments.py + stripe_webhook_server.py
- Workouts: execution/workout_plan_generator.py
- Nutrition: execution/nutrition_guide_generator.py
- PDF Engine: execution/branded_pdf_engine.py (7 templates)

### Website

- All pages: projects/marceau-solutions/website/
- Deploy: scripts/deploy_website.sh

---

*Updated March 5, 2026 by Claude Code. All systems verified operational. Using toll-free +1 (855) 239-9364. Stripe webhooks rebuilt.*
*Marceau Solutions — Embrace the Pain & Defy the Odds*