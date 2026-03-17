# FitAI Client Portal Migration Plan

## Trigger: PT Tracker shows 5+ active clients

## What This Migration Does
Move PT coaching client experience from Google Sheets + Drive folders to FitAI's built-in client portal at fitai.marceausolutions.com.

## Why Wait Until 5 Clients
- Sheets + n8n is battle-tested and working now
- Migration introduces new failure modes
- At 5 clients, the manual overhead of Sheets starts to hurt and the portal's automation justifies the switch

## Migration Steps
1. Verify FitAI client portal is functional (test with a dummy account)
2. Create n8n workflow: on new Stripe payment, create FitAI portal account instead of just Sheets entry
3. Migrate existing client data from PT Tracker Sheet to FitAI database
4. Update Coaching-Payment-Welcome workflow to use FitAI API for account creation
5. Update Monday-Checkin to pull client list from FitAI instead of Sheets
6. Keep Sheets as backup/reporting layer (read-only sync from FitAI)
7. Test full client journey end-to-end with a test account

## Estimated Effort: 2-3 sessions (4-6 hours)

## Rollback Plan
If FitAI portal has issues, revert n8n workflows to Sheets-based versions (they still exist).
