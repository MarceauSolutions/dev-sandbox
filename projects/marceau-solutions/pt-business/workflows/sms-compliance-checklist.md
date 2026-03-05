# SMS TCPA Compliance Checklist

**Based on**: SOP 18 (SMS Campaign Execution)
**Review frequency**: Before every campaign, and monthly audit

---

## Every SMS Must Include

1. **Identification**: "This is William" or "— William" signature
2. **Opt-out**: "Reply STOP to opt out" (on first message in any sequence)
3. **Business name**: "Marceau Solutions" or "William Marceau Coaching" somewhere in the first message

## Sending Windows

- **Earliest**: 8:00 AM recipient's local time
- **Latest**: 9:00 PM recipient's local time
- **Best window**: 10 AM - 2 PM and 5 PM - 7 PM
- **Never**: Sundays before 10 AM, holidays

## Consent Requirements

| Message Type | Consent Needed | How You Get It |
|-------------|---------------|----------------|
| Welcome SMS (after quiz/challenge) | Implied — they gave you their phone number | Quiz/challenge form submission |
| Nurture sequence | Implied — part of the lead magnet they signed up for | Same form |
| Coaching client SMS | Express — they're paying you | Payment = consent |
| Cold outreach (prospects) | Express written consent required | Must have opted in somewhere |
| Re-engagement (cancelled) | Prior business relationship | 18-month window |

## Campaign Execution (SOP 18 Compliance)

Before any batch SMS send:

- [ ] All templates reviewed for TCPA compliance
- [ ] Opt-out language present in first message
- [ ] Sending within 8 AM - 9 PM window
- [ ] **Dry run**: Send to yourself first (1 message)
- [ ] **Small batch**: Send to 5 leads, wait 24h, check delivery rate
- [ ] **Medium batch**: Send to 10 leads, wait 24h, check metrics
- [ ] **Full send**: Only after delivery rate >95% confirmed

## Opt-Out Handling

When someone replies STOP:
1. Immediately stop all automated sequences (n8n)
2. Update Leads sheet: set status to "opted_out"
3. Add to suppression list
4. Send confirmation: "You've been unsubscribed. No more messages."
5. **Never** message them again unless they explicitly re-subscribe

## Monthly Audit

- [ ] Review all 19 SMS templates in `execution/twilio_sms.py`
- [ ] Verify "Reply STOP" present in first message of each sequence
- [ ] Check Twilio logs for opt-out requests — are they being honored?
- [ ] Review sending times — any messages outside 8 AM - 9 PM?
- [ ] Update suppression list
- [ ] Check Twilio balance (>$10 minimum)

## Current Template Status (Audited March 4, 2026)

| Template | Has ID? | Has STOP? | Compliant? |
|----------|---------|-----------|------------|
| **Prospect Outreach** | | | |
| outreach_day0 | YES ("This is William from Marceau Solutions") | YES | YES |
| outreach_day2 | YES ("This is William") | No (follow-up in sequence) | YES |
| outreach_day5 | YES ("— William") | No (follow-up) | YES |
| outreach_day10 | YES ("— William") | No (follow-up) | YES |
| outreach_day15 | YES ("— William") | No (follow-up) | YES |
| outreach_day30 | YES ("— William") | No (follow-up) | YES |
| outreach_day60 | YES ("— William") | No (follow-up) | YES |
| **Client Onboarding** | | | |
| coaching_welcome | YES ("This is William") | YES | YES |
| coaching_kickoff_reminder | YES ("— William") | No (follow-up) | YES |
| coaching_pre_call | YES ("— William") | No (active client) | YES |
| **Weekly Check-Ins** | | | |
| coaching_monday_checkin | YES ("— William") | No (active client) | YES |
| coaching_midweek_tip | YES ("— William") | No (active client) | YES |
| coaching_no_response | YES ("— William") | No (active client) | YES |
| **Offboarding** | | | |
| coaching_cancel_feedback | YES ("This is William") | YES | YES |
| coaching_cancel_day7 | YES ("— William") | No (prior relationship) | YES |
| coaching_cancel_day30 | YES ("— William") | No (prior relationship) | YES |
| **Billing** | | | |
| coaching_payment_failed | YES ("— William") | No (active client) | YES |
| coaching_payment_failed_followup | YES ("— William") | No (active client) | YES |
| **Testimonials** | | | |
| coaching_testimonial_30day | YES ("— William") | No (active client) | YES |
| coaching_testimonial_90day | YES ("— William") | No (active client) | YES |
| coaching_referral_reward | YES ("— William") | No (active client) | YES |
| **General** | | | |
| appointment_reminder | YES ("This is William") | No (scheduling) | YES |

**Last audit**: March 4, 2026 — All 19 templates COMPLIANT.
- First message in each sequence has "Reply STOP to opt out"
- All messages have sender identification ("This is William" or "— William")
- Sequences that start with STOP language: outreach_day0, coaching_welcome, coaching_cancel_feedback
