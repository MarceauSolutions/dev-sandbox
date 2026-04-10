# Lead Generation Tower — Internal Agency

Full-service lead generation serving all Marceau Solutions towers. Owns shared infrastructure, maintains per-tower audience profiles and messaging.

## Structure
- `src/` — Shared engine (pipeline, SMS/email delivery, enrichment, scoring, follow-up sequences)
- `towers/digital/` — AI services clients (HVAC, med spa, dentist) — audience, templates, campaigns
- `towers/fitness/` — Fitness coaching clients (gym owners, influencers)
- `towers/labs/` — Product launches (DumbPhone Lock, etc.)

## Key Files
- `src/followup_prioritizer.py` — ranks leads by follow-up priority
- `src/email_sequence_engine.py` — multi-step email sequences
- `src/batch_outreach.py` — bulk SMS/email campaigns
