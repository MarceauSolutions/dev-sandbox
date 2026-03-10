# Coaching Operations Runbook

**Last updated**: 2026-03-05
**Purpose**: Track operational notes, nuances, and things to remember for the fitness coaching business. This is the single source of truth for "things William needs to know."

---

## Quick Reference

| Resource | Link / ID |
|----------|-----------|
| Landing Page | https://marceausolutions.com/coaching |
| Stripe Payment Link ($197/mo) | https://buy.stripe.com/14A14n29hdqU48wf5wg3601 |
| Stripe Dashboard | https://dashboard.stripe.com |
| Client Portal | https://fitai.marceausolutions.com/client/ |
| Calendly Kickoff | https://calendly.com/wmarceau/kickoff-call |
| Calendly Strategy (free) | https://calendly.com/wmarceau/free-fitness-strategy-call |
| Google Form (Intake) | https://docs.google.com/forms/d/e/1FAIpQLSfscvTEGRc7YxRiJdMslS6fj33ca3MOij1erZN6zy82JPNS4Q/viewform |
| Client Tracker Sheet | https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA/edit |
| Leads Database Sheet | https://docs.google.com/spreadsheets/d/13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E/edit |
| Drive: Coaching Clients | Folder ID: `1v9iYh6Cb-1WC9ZRQXAl44LxgJS25mczJ` |
| Skool Community | https://www.skool.com/unbreakable-9502 |
| n8n Dashboard | https://n8n.marceausolutions.com (or http://34.193.98.97:5678) |
| Twilio Phone | +1 (855) 239-9364 |
| Admin Phone (notifications) | +1 239 398 5676 |

---

## n8n Workflow Status

### Coaching Operations Workflows

| Workflow | ID | Status | Notes |
|----------|-----|--------|-------|
| Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | ACTIVE | Fires Mon 9am ET, reads active clients from Sheet, sends SMS |
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | ACTIVE | Stripe checkout.session.completed → portal account + starter workout + welcome SMS/email + Sheet + billing log + admin notify |
| Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | ACTIVE | Stripe subscription.deleted → feedback SMS + admin notify + Day 7/30 re-engage |
| Fitness-SMS-Outreach | `89XxmBQMEej15nak` | ACTIVE | Prospect outreach (pre-existing) |
| Fitness-SMS-Followup-Sequence | `VKC5cifm595JNcwG` | ACTIVE | Follow-up drip (pre-existing) |

### Funnel / Lead Acquisition Workflows

| Workflow | ID | Status | Notes |
|----------|-----|--------|-------|
| Lead-Magnet-Capture | `hgInaJCLffLFBX1G` | ACTIVE | Quiz submission → Sheet + Day 0 SMS/email → triggers Nurture |
| Nurture-Sequence-7Day | `szuYee7gtQkzRn3L` | ACTIVE | 7-day SMS/email drip → Day 7 coaching offer |
| Non-Converter-Followup | `Y2jfeIlTRDlbCHeS` | ACTIVE | Day 10/14/30 follow-ups for non-converters |
| Challenge-Signup-7Day | `WTZDxLDQuSkIkcqf` | ACTIVE | Challenge signup → 7 daily workout SMS |
| Challenge-Day7-Upsell | `Xza1DB4f4PIHw2lZ` | ACTIVE | Daily 8am: segmented upsell for Day 7 challenge completers |
| Premium-Waitlist-Capture | `j306crRxCmWW3dMo` | ACTIVE | Waitlist form → Sheet + confirmation email + Masterclass cross-sell |
| Digital-Product-Delivery | `kk7ZjWtjmZgylVzi` | ACTIVE | Stripe $37-97 → product delivery email + Sheet update |

### Utility / Monitoring Workflows

| Workflow | ID | Status | Notes |
|----------|-----|--------|-------|
| SMS-Response-Handler-v2 | `G14Mb6lpeFZVYGwa` | ACTIVE | Webhook `/webhook/sms-response` — categorizes inbound SMS |
| n8n-Health-Check | `QhDtNagsZFUrKFsG` | ACTIVE | Scheduled health check of n8n + services |
| Weekly-Campaign-Analytics | `M62QBpROE48mEgDC` | ACTIVE | Weekly SMS campaign metrics aggregation |
| Monthly-Workflow-Backup | `2QaQbhIUlL7ctfq4` | ACTIVE | Monthly export of all workflows to backup |

See `docs/client-acquisition-system-guide.md` for complete funnel documentation (14 chapters).

---

## n8n Credentials

| Name | ID | Type |
|------|-----|------|
| Twilio Fitness SMS | `hduvneOOzFzKMfOa` | twilioApi |
| Stripe Coaching | `IRNFASlnSdGSicwk` | stripeApi |
| Google Sheets | `RIFdaHtNYdTpFnlu` | googleSheetsOAuth2Api |
| Gmail SMTP Coaching | `xJL5bzXyMeTkr1WQ` | smtp |

---

## Infrastructure

### HTTPS / SSL (RESOLVED 2026-02-11)
- **Domain**: `https://n8n.marceausolutions.com` (SSL via Let's Encrypt, auto-renews)
- **nginx**: Reverse proxy on EC2, config at `/etc/nginx/conf.d/n8n.conf`
- **n8n env**: `WEBHOOK_URL=https://n8n.marceausolutions.com/` in `/etc/n8n.env`
- **Cert expires**: 2026-05-12 (certbot auto-renewal configured)
- All Stripe webhook workflows now fully operational.

---

## Weekly Cadence

| Day | Time | What | Automated? |
|-----|------|------|-----------|
| Sunday PM | 7pm | Upload next week's program PDF to client's Drive folder | Manual |
| Sunday PM | 7pm | Send email with program update notification | Manual |
| Monday | 9am ET | Check-in SMS sent to all active clients | YES (n8n) |
| Tuesday | - | Follow up with non-responders | Manual (check Sheet) |
| Wednesday | Optional | Mid-week tip SMS (pick from `data/midweek-tips.json`) | Manual for now |
| Friday | EOD | Review all check-in responses, update Sheet | Manual |
| Month end | Calendly | 15-min Google Meet progress review | Manual (Calendly) |

---

## Client Onboarding

**Now automated via n8n (Coaching-Payment-Welcome).** HTTPS resolved 2026-02-11.

n8n handles automatically: portal account, starter workout, welcome SMS/email, Sheet entry, billing log, admin notification.

**Your manual steps:** See full workflow → `workflows/client-onboarding.md`

Quick checklist:
1. [ ] Verify n8n fired (check executions within 1 hour)
2. [ ] Check if they booked kickoff call (within 24h)
3. [ ] Review intake form after they submit
4. [ ] Do kickoff call
5. [ ] Customize their program (within 48h of kickoff)
6. [ ] Create Drive folder + upload legal docs

---

## Client Offboarding

**Automated via n8n (Coaching-Cancellation-Exit).**

n8n handles: feedback SMS, Day 7 + Day 30 re-engagement.

**Your manual steps:** See full workflow → `workflows/client-offboarding.md`

Quick checklist:
1. [ ] Update Client Roster status to "Cancelled" + cancel reason
2. [ ] Read their feedback SMS reply
3. [ ] Send exit email (thank you + progress summary)
4. [ ] Keep Drive access (permanent)

---

## Failed Payment Sequence

1. Day 0: Stripe auto-emails failed payment notice
2. Day 1: Send `coaching_payment_failed` SMS with billing portal link
3. Day 5: Send `coaching_payment_failed_followup` SMS ("want to pause?")
4. Day 10: **Phone call** — this is a relationship, not a SaaS
5. Day 14: If unresolved, cancel subscription → offboarding flow

---

## Collaborator Assets

| Person | Phone | Status | Files |
|--------|-------|--------|-------|
| Sister | +12393985197 | Assets received 2026-02-11 | `assets/collaborators/sister/` — headshot.jpg, voice-clip.wav, voice-clip.mp3 |

---

## Pricing & Billing

### Core Coaching
- **Monthly**: $197/month via Stripe (recurring subscription)
- **Stripe fees**: $6.01/payment ($5.71 processing + $0.30 fixed)
- **Net per client**: $190.99/month
- **Cancel anytime**: No contracts, no cancellation fees
- **Pause**: Up to 30 days free pause on request
- **Failed payment grace**: 14 days before auto-cancel

### Digital Products (One-Time)
| Product | Price | Stripe Link |
|---------|-------|-------------|
| Nutrition Blueprint | $37 | buy.stripe.com/eVqaEX9BJ1Ic0Wk7D4g3606 |
| 8-Week Recomp Program | $67 | buy.stripe.com/eVq28r6pxbiM8oMg9Ag3605 |
| Peptide Masterclass | $97 | buy.stripe.com/3cI00jg070E86gE9Lcg3607 |

### Premium + Peptides (Waitlist Only)
- **Price**: $497/month — NOT live yet (physician partnerships pending)
- **Stripe link exists** but is not linked on any website page

---

## SMS Templates Quick Reference

See `execution/twilio_sms.py` TEMPLATES dict for full text. Key templates:

| Template Key | When to Use |
|-------------|-------------|
| `coaching_welcome` | Immediately after payment |
| `coaching_kickoff_reminder` | 24h after payment if no call booked |
| `coaching_pre_call` | 1h before kickoff call |
| `coaching_monday_checkin` | Monday 9am (automated) |
| `coaching_midweek_tip` | Wed/Thu (manual, use `data/midweek-tips.json`) |
| `coaching_no_response` | If no Monday check-in response by Tuesday |
| `coaching_cancel_feedback` | Immediately on cancellation |
| `coaching_cancel_day7` | 7 days post-cancel |
| `coaching_cancel_day30` | 30 days post-cancel |
| `coaching_payment_failed` | Day 1 of failed payment |
| `coaching_payment_failed_followup` | Day 5 of failed payment |
| `coaching_testimonial_30day` | 30 days into coaching |
| `coaching_testimonial_90day` | 90 days into coaching |

---

## File Locations

| What | Path |
|------|------|
| **PT Business Hub** | `projects/marceau-solutions/pt-business/` |
| This runbook | `projects/marceau-solutions/pt-business/ops/coaching-ops-runbook.md` |
| Intake form questions | `projects/marceau-solutions/pt-business/intake/intake-form-questions.md` |
| Working Together doc | `projects/marceau-solutions/pt-business/legal/working-together.md` + .pdf |
| Liability Waiver | `projects/marceau-solutions/pt-business/legal/liability-waiver.md` + .pdf |
| Cancellation Policy | `projects/marceau-solutions/pt-business/legal/cancellation-policy.md` + .pdf |
| Mid-week tips | `projects/marceau-solutions/pt-business/data/midweek-tips.json` |
| Content strategy | `projects/marceau-solutions/pt-business/content/` |
| Business planning | `projects/marceau-solutions/pt-business/business-planning/` |
| SMS templates (shared) | `execution/twilio_sms.py` |
| Onboarding email | `execution/send_onboarding_email.py` |
| Stripe payments | `execution/stripe_payments.py` |
| Stripe webhook server | `execution/stripe_webhook_server.py` |
| Drive folder creator | `scripts/create-coaching-drive-folders.py` |
| Sheet creator | `scripts/create-coaching-tracker-sheet.py` |
| Collaborator assets | `projects/marceau-solutions/fitness-influencer/assets/collaborators/` |
| n8n workflow exports | `/tmp/coaching-*.json` (backup locally if needed) |
| Client acquisition guide | `docs/client-acquisition-system-guide.md` |
| **Workflows** | |
| Client onboarding | `workflows/client-onboarding.md` |
| Client offboarding | `workflows/client-offboarding.md` |
| Cold outreach strategy | `workflows/cold-outreach-strategy.md` |
| SMS compliance | `workflows/sms-compliance-checklist.md` |
| Funnel testing guide | `workflows/SALES-FUNNEL-TESTING-GUIDE.md` |
| Propane client pipeline | `workflows/propane-client-pipeline.md` |
| n8n workflow improvements | `workflows/n8n-workflow-improvements.md` |

---

## Environment Variables (.env)

| Key | Purpose |
|-----|---------|
| `INTAKE_FORM_URL` | Google Form intake link |
| `CALENDLY_KICKOFF_URL` | Kickoff call booking link |
| `COACHING_TRACKER_SPREADSHEET_ID` | Google Sheets tracker ID |
| `STRIPE_SECRET_KEY` | Stripe live API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature verification |
| `TWILIO_ACCOUNT_SID` / `AUTH_TOKEN` / `PHONE_NUMBER` | Twilio SMS |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Gmail sending |
| `SENDER_EMAIL` | From address for emails |

---

## Client Portal

**URL**: https://fitai.marceausolutions.com/client/

The client portal provides instant onboarding after payment. When Coaching-Payment-Welcome fires, it automatically:
1. Creates a portal account via the fitai API
2. Generates a magic link (no password needed)
3. Assigns the Beginner Full Body starter workout template (`tpl_530e4037df`)
4. Includes the magic link in the welcome SMS and email

**Portal features for clients:**
- Dashboard with XP bar, streak counter, today's workout
- My Workouts: weekly schedule with exercise details
- Form Check: upload video for AI exercise analysis
- Ask Coach: AI chat with client context injected
- My Progress: achievements, streaks, level system, coin rewards
- My Profile: contact info, goals, coach contact

**If a client loses their magic link**: Generate a new one via the fitai admin API or the admin dashboard at `fitai.marceausolutions.com`.

---

## SMS Compliance

All SMS campaigns must follow TCPA rules. See full checklist → `workflows/sms-compliance-checklist.md`

**Quick rules:**
- Every first message includes "Reply STOP to opt out"
- Identify yourself: "This is William" or "— William"
- Send only between 8 AM - 9 PM recipient's local time
- Honor STOP requests immediately

---

## Change Log

| Date | Change |
|------|--------|
| 2026-03-05 | Fixed Stripe Trigger nodes (replaced with standard Webhook nodes). Fixed n8n health check API key. New Stripe webhook paths: `/webhook/stripe-payment-welcome`, `/webhook/stripe-digital-delivery`, `/webhook/stripe-cancellation`. Reverted to toll-free +1 (855) 239-9364 (239 local number not working reliably). |
| 2026-03-04 | Operations audit: Added 7 funnel n8n workflows, Stripe payment link, client portal section, Leads Sheet, Skool community, digital product tiers, n8n-workflow-improvements ref, client-acquisition-system-guide ref. Fixed n8n URL to HTTPS. |
| 2026-03-04 | SOP audit: created 5 workflow docs, updated onboarding/offboarding to reference n8n automation, added SMS compliance section, added funnel testing guide |
| 2026-02-11 | Set up nginx + SSL for `n8n.marceausolutions.com`. Activated all 3 Stripe/coaching workflows. HTTPS blocker resolved. |
| 2026-02-11 | Created runbook. Deployed 3 n8n workflows (1 active, 2 pending HTTPS). Created Client Tracker Sheet. Set up Drive folders. Received collaborator assets from sister. |
| 2026-02-10 | Rewrote SMS templates (19 fitness-specific). Created legal docs (waiver, cancellation, working-together). Created intake form (35 questions). |
| 2026-02-10 | Rewrote onboarding email for fitness coaching. Updated Calendly links. |
| 2026-02-10 | Approved client communication plan (4-phase: Outreach → Onboarding → Ongoing → Offboarding). |
