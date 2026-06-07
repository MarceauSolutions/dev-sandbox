# Marketplace — agent notes

HVAC appointment marketplace (RoofProspect.ai equivalent). Lives in the
lead-generation tower because it consumes the same lead/appointment + Stripe + SMS infra.

## Files
- `config.py` — all knobs (pay structure, gating, Stripe mode). Money in CENTS.
- `models.py` — SQLite data layer. **Atomic exclusive purchase** + append-only credit
  ledger. `verify_ledger()` is the integrity invariant (cached balance == ledger sum).
- `payments.py` — Stripe credit top-up (gated by `PAYMENT_MODE`; credits granted only by
  verified webhook, idempotent on `stripe_ref`).
- `notifications.py` — best-effort SMS (`execution.twilio_sms.TwilioSMS`) + Telegram admin
  ping (direct Bot API). Failures never block a purchase.
- `templates.py` / `app.py` — Flask UI + routes. `seed.py` — Marceau Air + samples.
- `tests/test_marketplace.py` — 53-check battle-test (concurrency race, TCPA gate, masking,
  ledger, refunds, full HTTP). Run before any change.

## Invariants (do not break)
1. Money is integer cents end-to-end. No floats in storage.
2. Every balance change goes through `_ledger()`; `verify_ledger()` must stay empty.
3. `purchase_appointment` must remain a single immediate-transaction with the conditional
   `status='available'->'sold'` UPDATE — that is what makes exclusivity race-safe.
4. An appointment cannot be published without `consent_captured` (TCPA).
5. Public/masked appointment views must never include PII (`PUBLIC_COLS` only).

## Strategy context
Grok (2026-06-07) flagged this as a distraction from the HVAC/Aug-1-rent priority unless
appointment SUPPLY and buyer willingness-to-pay are validated first. Scope chosen:
**Marceau-Air-first** (public signup OFF, manual credits) so William eats his own dog food
before exposing competitors. Don't enable public signup / live Stripe without William's call.
