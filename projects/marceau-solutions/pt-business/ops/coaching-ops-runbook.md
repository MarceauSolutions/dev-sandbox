# Coaching Operations Runbook

**Last updated**: 2026-02-11
**Purpose**: Track operational notes, nuances, and things to remember for the fitness coaching business. This is the single source of truth for "things William needs to know."

---

## Quick Reference

| Resource | Link / ID |
|----------|-----------|
| Landing Page | https://marceausolutions.com/coaching |
| Stripe Dashboard | https://dashboard.stripe.com |
| Calendly Kickoff | https://calendly.com/wmarceau/kickoff-call |
| Calendly Strategy (free) | https://calendly.com/wmarceau/30min |
| Google Form (Intake) | https://docs.google.com/forms/d/e/1FAIpQLSfscvTEGRc7YxRiJdMslS6fj33ca3MOij1erZN6zy82JPNS4Q/viewform |
| Client Tracker Sheet | https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA/edit |
| Drive: Coaching Clients | Folder ID: `1v9iYh6Cb-1WC9ZRQXAl44LxgJS25mczJ` |
| n8n Dashboard | http://34.193.98.97:5678 |
| Twilio Phone | +1 855 239 9364 |
| Admin Phone (notifications) | +1 239 398 5676 |

---

## n8n Workflow Status

| Workflow | ID | Status | Notes |
|----------|-----|--------|-------|
| Coaching-Monday-Checkin | `aBxCj48nGQVLRRnq` | ACTIVE | Fires Mon 9am ET, reads active clients from Sheet, sends SMS |
| Coaching-Payment-Welcome | `1wS9VvXIt95BrR9V` | ACTIVE | Stripe checkout.session.completed → welcome SMS + email + Sheet + billing log |
| Coaching-Cancellation-Exit | `uKjqRexDIheaDJJH` | ACTIVE | Stripe subscription.deleted → feedback SMS + admin notify + Day 7/30 re-engage |
| Fitness-SMS-Outreach | `89XxmBQMEej15nak` | ACTIVE | Prospect outreach (pre-existing) |
| Fitness-SMS-Followup-Sequence | `VKC5cifm595JNcwG` | ACTIVE | Follow-up drip (pre-existing) |

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

## Client Onboarding Checklist (manual until Stripe HTTPS is fixed)

When a new client pays:
1. [ ] Send welcome SMS: `coaching_welcome` template
2. [ ] Send onboarding email: `python execution/send_onboarding_email.py`
3. [ ] Add to Client Roster tab in Google Sheet
4. [ ] Log payment in Billing tab
5. [ ] Duplicate `_TEMPLATE (Client Name)` Drive folder, rename to client name
6. [ ] Upload liability waiver, working-together, cancellation policy to their Resources folder (already in template)
7. [ ] Verify they booked kickoff call (check Calendly)
8. [ ] If no kickoff booked in 24h, send `coaching_kickoff_reminder` SMS

---

## Client Offboarding Checklist (manual until Stripe HTTPS is fixed)

When a client cancels:
1. [ ] Update Client Roster status to "Cancelled"
2. [ ] Send `coaching_cancel_feedback` SMS (immediate)
3. [ ] Send exit email (thank you + progress summary)
4. [ ] Day 7: Send `coaching_cancel_day7` SMS
5. [ ] Day 30: Send `coaching_cancel_day30` SMS
6. [ ] Client keeps access to their Drive folder permanently

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

- **Monthly**: $197/month via Stripe
- **Stripe fees**: $6.01/payment ($5.71 processing + $0.30 fixed)
- **Net per client**: $190.99/month
- **Cancel anytime**: No contracts, no cancellation fees
- **Pause**: Up to 30 days free pause on request
- **Failed payment grace**: 14 days before auto-cancel

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

## Change Log

| Date | Change |
|------|--------|
| 2026-02-11 | Set up nginx + SSL for `n8n.marceausolutions.com`. Activated all 3 Stripe/coaching workflows. HTTPS blocker resolved. |
| 2026-02-11 | Created runbook. Deployed 3 n8n workflows (1 active, 2 pending HTTPS). Created Client Tracker Sheet. Set up Drive folders. Received collaborator assets from sister. |
| 2026-02-10 | Rewrote SMS templates (19 fitness-specific). Created legal docs (waiver, cancellation, working-together). Created intake form (35 questions). |
| 2026-02-10 | Rewrote onboarding email for fitness coaching. Updated Calendly links. |
| 2026-02-10 | Approved client communication plan (4-phase: Outreach → Onboarding → Ongoing → Offboarding). |
