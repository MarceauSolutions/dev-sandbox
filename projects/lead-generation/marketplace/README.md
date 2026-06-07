# Marceau Air — HVAC Appointment Marketplace

A RoofProspect.ai-equivalent **pre-qualified appointment marketplace** for HVAC.
Confirmed homeowner appointments are listed; HVAC companies/techs spend **prepaid
credits** to buy them **exclusively** (only the buyer gets the contact info).

**Pay structure (mirrors RoofProspect):** prepaid credit wallet → pay-per-exclusive-appointment.
Signup grants free promo credits (default $300). Money is stored in **cents** everywhere.

## Quick start
```bash
cd projects/lead-generation/marketplace
MARKETPLACE_ADMIN_PASSWORD='choose-one' ./run.sh
# opens http://127.0.0.1:8767  (admin: /admin/login)
```
Seed creates **Marceau Air** as the first buyer + sample appointments.
- Contractor demo login: `ops@marceauair.com` / `MarceauAir!2026`
- Admin login: `MARKETPLACE_ADMIN_EMAIL` / `MARKETPLACE_ADMIN_PASSWORD`

## Test
```bash
python3 tests/test_marketplace.py   # 53 checks; isolated temp DB; no Stripe
```

## Phased rollout (Marceau-Air-first)
1. **Now (default):** `MARKETPLACE_PUBLIC_SIGNUP=false`, `MARKETPLACE_PAYMENT_MODE=manual`.
   Marceau Air is the only buyer; you add credits via admin. Prove supply + close rates.
2. **Open to others:** set `MARKETPLACE_PUBLIC_SIGNUP=true`. Self-signup + promo credits turn on.
3. **Take card payments:** add **Stripe TEST** keys, set `MARKETPLACE_PAYMENT_MODE=stripe`,
   point a Stripe webhook at `/webhook/stripe`. Only flip to the live key after a full test-mode pass.

## Config (root `.env`)
| Var | Default | Meaning |
|-----|---------|---------|
| `MARKETPLACE_PUBLIC_SIGNUP` | `false` | Open public self-signup |
| `MARKETPLACE_PAYMENT_MODE` | `manual` | `manual` (admin credits) or `stripe` |
| `MARKETPLACE_PROMO_CENTS` | `30000` | Signup promo credits ($300) |
| `MARKETPLACE_PROMO_CODE` | `` | If set, required to receive promo |
| `MARKETPLACE_MIN_TOPUP_CENTS` | `5000` | Min credit purchase ($50) |
| `MARKETPLACE_ADMIN_EMAIL/PASSWORD` | — | Admin console login |
| `STRIPE_TEST_SECRET_KEY` etc. | — | Preferred over live keys for the marketplace |

## Safety
- `STRIPE_SECRET_KEY` in repo `.env` is **LIVE**. The marketplace defaults to `manual`
  mode and surfaces `stripe_live` in `/health` and the admin header so a live key is
  never used by accident. Add `STRIPE_TEST_*` keys for safe E2E payment testing.
- **TCPA gate:** an appointment cannot be published until `consent_captured` is set.

## What is NOT in scope yet (honest gaps)
- Real homeowner **consent-capture form** (admin currently attests to consent).
- **Appointment supply** — the marketplace is empty without it (the real business work).
- Production hosting (gunicorn + HTTPS + domain), password reset, email verification, rate limiting.
- Stripe live end-to-end (code is present + gated; needs a test-mode pass first).
