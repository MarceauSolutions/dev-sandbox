# BOABFIT Client Tracking — Field Reference

> Research-backed schema for tracking the full client lifecycle.
> Source: Trainerize, Everfit, TrueCoach platform analysis + churn prediction research.
> Compiled: 2026-04-11

## Implementation Priority

### Tier 1 — Build immediately (in client_db.py now)
- `lifecycle_stage` (lead, onboarding, active, at_risk, completed, churned, alumni)
- `program_start_date`, `current_week_number`, `program_completed`
- `stripe_customer_id`, `payment_status`, `total_revenue_generated`
- `workout_completion_rate`, `last_workout_logged_at`, `days_since_last_activity`
- `consecutive_missed_check_ins`

### Tier 2 — Add by week 3 of live operation
- `check_in_frequency`, `last_check_in_submitted_at`
- `churn_risk_score` (computed from activity signals)
- `nps_score` (post-program survey)
- `lead_source`, `referred_by_client_id`
- `progress_photos_uploaded`

### Tier 3 — Add when >20 active clients
- `email_open_rate` (requires ESP with tracking)
- `last_message_received_at` (client-side engagement)
- `push_notifications_enabled`
- `discount_code_used`, `check_in_sentiment`, `ltv`

## Churn Risk Signals (weighted)

| Signal | Weight | Threshold |
|---|---|---|
| days_since_last_activity | HIGH | >7 = risk, >14 = critical |
| consecutive_missed_check_ins | HIGH | >=2 = escalate |
| cumulative_completion_rate | HIGH | <60% = at-risk |
| current_week_number | MEDIUM | Weeks 1-3 highest risk |
| payment_failure_count | HIGH | >=1 = flag |
| days_since_last_client_message | MEDIUM | >5 = flag |
| programs_purchased_count | MEDIUM (inverse) | >1 = lower risk |

## Renewal & Alumni Fields

- `nps_score` (0-10) at program end — >8 = ask for testimonial
- `testimonial_provided` — drives Instagram social proof
- `renewal_status` — not_offered, offered, accepted, declined
- `alumni_email_subscribed` — keep in nurture sequence

## Current Database Status (client_db.py)

Tables implemented: `clients`, `enrollments`, `communications`, `engagement`

Workout tracking requires the BOABFIT app to send events to the `engagement` table.
Stripe integration requires wiring Stripe webhooks to update `enrollments.stripe_payment_id` and `enrollments.amount_paid`.
