# William's Personal Training Business

> Peptide-focused online coaching, $197/month. Naples FL, local + remote.
> This directory is the BUSINESS hub. The PRODUCT (SaaS platform) lives at `projects/marceau-solutions/fitness-influencer/`.
> Unified ops architecture (shared tools across PT + Web Dev): `docs/UNIFIED-BUSINESS-OPS.md`
> Cross-business integration: `docs/BUSINESS-INTEGRATION-PROTOCOL.md`

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
| Twilio Phone (clients) | +1 (855) 239-9364 |
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
| Expense Strategy | `business-planning/EXPENSE-MANAGEMENT-STRATEGY.md` | Two-card strategy, categories, tracking cadence |
| Viability Testing | `business-planning/BUSINESS-VIABILITY-TESTING-PLAN.md` | 8-week testing roadmap |
| Funding Prep | `business-planning/7-FIGURE-FUNDING-MEETING-PREP.md` | Due diligence FAQ |
| Strategic Analysis | `business-planning/WILLIAM-STRATEGIC-ANALYSIS.md` | Business strategy doc |
| Peptide Research | `research/peptide-business/` | 4-agent viability study (telemedicine, clinics, legal, certs) |
| Midweek Tips | `data/midweek-tips.json` | 30 coaching tips for SMS |
| Collaborators | `data/collaborators.json` | Julia + William asset tracking |
| **Workflows** | | |
| Client Onboarding | `workflows/client-onboarding.md` | Automated + manual steps, SLA, troubleshooting |
| Client Offboarding | `workflows/client-offboarding.md` | Cancel flow, re-engagement, reason tracking |
| Cold Outreach Strategy | `workflows/cold-outreach-strategy.md` | Target segment, A/B testing, follow-up sequence |
| SMS Compliance | `workflows/sms-compliance-checklist.md` | TCPA rules, template audit, opt-out handling |
| Funnel Testing Guide | `workflows/SALES-FUNNEL-TESTING-GUIDE.md` | End-to-end test all 5 pages + webhooks + Stripe |
| Client Acquisition Guide | `docs/client-acquisition-system-guide.md` | 14-chapter comprehensive funnel documentation |
| Propane Pipeline | `workflows/propane-client-pipeline.md` | Business coaching SOPs |

### Shared Code (DO NOT MOVE -- used by multiple projects)

| What | Path | Description |
|------|------|-------------|
| SMS templates (19 coaching + 7 webdev) | `execution/twilio_sms.py` | PT uses `coaching_*` prefix. Web dev uses `webdev_*` prefix. |
| Coaching analytics | `execution/coaching_analytics.py` | SMS metrics, funnel, template performance, health check |
| Onboarding email | `execution/send_onboarding_email.py` | Post-payment email with Calendly + intake links |
| Stripe payments | `execution/stripe_payments.py` | Customer creation, payment links, invoices |
| Stripe webhooks | `execution/stripe_webhook_server.py` | Webhook handler for payment events |
| Twilio inbox | `execution/twilio_inbox_monitor.py` | Inbound SMS monitoring |
| Workout generator | `execution/workout_plan_generator.py` | Custom program generation |
| Nutrition generator | `execution/nutrition_guide_generator.py` | Nutrition guide generation |
| Coaching tracker sheet | `scripts/create-coaching-tracker-sheet.py` | Creates Google Sheets tracker per client |
| Drive folder creator | `scripts/create-coaching-drive-folders.py` | Creates Drive folders per client |
| n8n backup | `scripts/backup-n8n-workflows.sh` | Exports all n8n workflows to local backup |

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
| SMS-Response-Handler-v2 | `G14Mb6lpeFZVYGwa` | ACTIVE | Webhook `/webhook/sms-response` -- categorizes inbound SMS |
| n8n-Health-Check | `QhDtNagsZFUrKFsG` | ACTIVE | Scheduled health check of n8n + services |
| Weekly-Campaign-Analytics | `M62QBpROE48mEgDC` | ACTIVE | Weekly SMS campaign metrics aggregation |
| Monthly-Workflow-Backup | `2QaQbhIUlL7ctfq4` | ACTIVE | Monthly export of all workflows to backup |

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
| Monday | 9am | Check-in SMS to all active clients | YES (n8n: Coaching-Monday-Checkin) |
| Tuesday | - | Follow up non-responders (coaching_no_response template) | Manual |
| Wednesday | - | Mid-week tip SMS (uses midweek-tips.json) | Manual (candidate for n8n) |
| Friday | EOD | Review check-ins, update Sheet | Manual |
| Weekly | - | SMS campaign analytics aggregation | YES (n8n: Weekly-Campaign-Analytics) |
| Monthly | 1st | Workflow backup export | YES (n8n: Monthly-Workflow-Backup) |
| Month end | - | 15-min progress review via Calendly | Manual |

## Pricing

- **Monthly**: $197 via Stripe
- **Net per client**: $190.99 (after $6.01 Stripe fees)
- **Cancel anytime**, 30-day pause available, 14-day grace on failed payments

## Common Operations

| Task | How |
|------|-----|
| New client onboarding | `workflows/client-onboarding.md` (mostly automated via n8n) |
| Client cancellation | `workflows/client-offboarding.md` (automated + manual steps) |
| Test the funnel | `workflows/SALES-FUNNEL-TESTING-GUIDE.md` |
| SMS compliance check | `workflows/sms-compliance-checklist.md` |
| Send mid-week tip | `python execution/twilio_sms.py --template coaching_midweek_tip --to <phone>` |
| Create tracker sheet | `python scripts/create-coaching-tracker-sheet.py` |
| Create Drive folders | `python scripts/create-coaching-drive-folders.py` |
| Check SMS inbox | `python execution/twilio_inbox_monitor.py` |
| Send onboarding email | `python execution/send_onboarding_email.py --email <email> --name <name>` |
