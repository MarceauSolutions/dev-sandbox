# William's Personal Training Business

> Peptide-focused online coaching, $197/month. Naples FL, local + remote.
> This directory is the BUSINESS hub. The PRODUCT (SaaS platform) lives at `projects/marceau-solutions/fitness-influencer/`.

## Quick Reference

| Resource | Link / ID |
|----------|-----------|
| Landing Page | https://marceausolutions.com/coaching |
| Stripe Dashboard | https://dashboard.stripe.com |
| Stripe Payment Link | https://buy.stripe.com/14A14n29hdqU48wf5wg3601 |
| Calendly Kickoff (paid) | https://calendly.com/wmarceau/kickoff-call |
| Calendly Strategy (free) | https://calendly.com/wmarceau/30min |
| Google Form (Intake) | https://docs.google.com/forms/d/e/1FAIpQLSfscvTEGRc7YxRiJdMslS6fj33ca3MOij1erZN6zy82JPNS4Q/viewform |
| Client Tracker Sheet | https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA/edit |
| Drive: Coaching Clients | Folder ID `1v9iYh6Cb-1WC9ZRQXAl44LxgJS25mczJ` |
| n8n Dashboard | https://n8n.marceausolutions.com |
| Twilio Phone (clients) | +1 855 239 9364 |
| Admin Phone (notifications) | +1 239 398 5676 |

## Status

- **Paying clients**: 0 (just getting started)
- **Social media**: Not yet active
- **All infrastructure**: Built and operational (see below)

---

## File Map: Everything That Exists

### In This Directory

| What | Path | Description |
|------|------|-------------|
| Master Runbook | `ops/coaching-ops-runbook.md` | Single source of truth for operations |
| Cancellation Policy | `legal/cancellation-policy.md` + `.pdf` | $197/mo, cancel anytime, 30-day pause |
| Liability Waiver | `legal/liability-waiver.md` + `.pdf` | Client-facing legal protection |
| Working Together | `legal/working-together.md` + `.pdf` | Client expectations and communication |
| Intake Questions | `intake/intake-form-questions.md` | 35 questions across 9 sections for Google Forms |
| Content Strategy | `content/WEEKLY-CONTENT-STRATEGY.md` | Weekly content framework |
| Multi-Platform Strategy | `content/MULTI-PLATFORM-CONTENT-STRATEGY.md` | X/YouTube/IG/TikTok plan (TikTok bans peptides) |
| Peptide Video Script | `content/PEPTIDE-VIDEO-SCRIPT.md` | Full narrative + talking points |
| Peptide Video Production | `content/PEPTIDE-VIDEO-PRODUCTION.md` | Production plan + specs |
| Current Week Calendar | `content/current-week/` | Rolling weekly content plan |
| Peptide Video Assets | `content/peptide-video/` | B-roll MP4s, graphics PNGs, talking head MOVs, Premiere projects |
| Financial Projections | `business-planning/FINANCIAL-PROJECTION-36-MONTH.md` | 36-month P&L ($4,650/mo Y1 personal expenses) |
| Viability Testing | `business-planning/BUSINESS-VIABILITY-TESTING-PLAN.md` | 8-week testing roadmap |
| Funding Prep | `business-planning/7-FIGURE-FUNDING-MEETING-PREP.md` | Due diligence FAQ |
| Strategic Analysis | `business-planning/WILLIAM-STRATEGIC-ANALYSIS.md` | Business strategy doc |
| Peptide Research | `research/peptide-business/` | 4-agent viability study (telemedicine, clinics, legal, certs) |
| Midweek Tips | `data/midweek-tips.json` | 30 coaching tips for SMS |
| Collaborators | `data/collaborators.json` | Julia + William asset tracking |

### Shared Code (DO NOT MOVE -- used by multiple projects)

| What | Path | Description |
|------|------|-------------|
| SMS templates (19) | `execution/twilio_sms.py` | coaching_welcome, monday_checkin, cancel_feedback, etc. |
| Onboarding email | `execution/send_onboarding_email.py` | Post-payment email with Calendly + intake links |
| Stripe payments | `execution/stripe_payments.py` | Customer creation, payment links, invoices |
| Stripe webhooks | `execution/stripe_webhook_server.py` | Webhook handler for payment events |
| Twilio inbox | `execution/twilio_inbox_monitor.py` | Inbound SMS monitoring |
| Workout generator | `execution/workout_plan_generator.py` | Custom program generation |
| Nutrition generator | `execution/nutrition_guide_generator.py` | Nutrition guide generation |
| Coaching tracker sheet | `scripts/create-coaching-tracker-sheet.py` | Creates Google Sheets tracker per client |
| Drive folder creator | `scripts/create-coaching-drive-folders.py` | Creates Drive folders per client |

### Website (Deployment Source -- DO NOT MOVE)

| What | Path |
|------|------|
| Coaching page | `projects/marceau-solutions/website/coaching.html` |
| Peptides page | `projects/marceau-solutions/website/peptides.html` |
| Programs page | `projects/marceau-solutions/website/programs.html` |
| Full website | `projects/marceau-solutions/website/` |
| Restructure plan | `projects/marceau-solutions/website/WEBSITE-RESTRUCTURE-PLAN.md` |

### Social Media

| What | Path |
|------|------|
| Fitness coach handoff | `projects/shared/social-media-automation/CLAUDE-CODE-HANDOFF-FITNESS-COACHING.md` |
| LinkedIn/GitHub strategy | `projects/shared/resume/workflows/linkedin-github-presence.md` |

### n8n Workflows (EC2 -- reference only)

| Workflow | ID | Status | What It Does |
|----------|-----|--------|------|
| Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | ACTIVE | Mon 9am ET: reads Sheet, sends SMS check-in |
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | ACTIVE | Stripe payment → welcome SMS + email + Sheet + billing log |
| Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | ACTIVE | Stripe cancel → feedback SMS + re-engage Day 7/30 |
| Fitness-SMS-Outreach | `89XxmBQMEej15nak` | ACTIVE | Prospect outreach via webhook |
| Fitness-SMS-Followup-Sequence | `VKC5cifm595JNcwG` | ACTIVE | Multi-step drip with delays |

**n8n Credentials (on EC2):**
- Twilio: `hduvneOOzFzKMfOa` | Stripe: `IRNFASlnSdGSicwk` | Google Sheets: `RIFdaHtNYdTpFnlu` | Gmail SMTP: `xJL5bzXyMeTkr1WQ`

### The Product (SaaS -- separate project)

| What | Path |
|------|------|
| Fitness Influencer AI platform | `projects/marceau-solutions/fitness-influencer/` |
| Julia demo (BOABFIT) | `projects/marceau-solutions/fitness-influencer/demos/boabfit-julia/` |

---

## Weekly Cadence

| Day | Time | What | Automated? |
|-----|------|------|-----------|
| Sunday PM | 7pm | Upload program PDF to client Drive | Manual |
| Monday | 9am | Check-in SMS to all active clients | YES (n8n) |
| Tuesday | - | Follow up non-responders | Manual |
| Wednesday | - | Mid-week tip SMS (uses midweek-tips.json) | Manual |
| Friday | EOD | Review check-ins, update Sheet | Manual |
| Month end | - | 15-min progress review via Calendly | Manual |

## Pricing

- **Monthly**: $197 via Stripe
- **Net per client**: $190.99 (after $6.01 Stripe fees)
- **Cancel anytime**, 30-day pause available, 14-day grace on failed payments

## Common Operations

| Task | How |
|------|-----|
| New client onboarding | See `ops/coaching-ops-runbook.md` > Onboarding Checklist |
| Client cancellation | See `ops/coaching-ops-runbook.md` > Offboarding Checklist |
| Send mid-week tip | `python execution/twilio_sms.py --template coaching_midweek_tip --to <phone>` |
| Create tracker sheet | `python scripts/create-coaching-tracker-sheet.py` |
| Create Drive folders | `python scripts/create-coaching-drive-folders.py` |
| Check SMS inbox | `python execution/twilio_inbox_monitor.py` |
| Send onboarding email | `python execution/send_onboarding_email.py --email <email> --name <name>` |
