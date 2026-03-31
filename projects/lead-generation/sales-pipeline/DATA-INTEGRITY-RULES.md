# DATA INTEGRITY RULES — MANDATORY

**Created:** 2026-03-30  
**Reason:** System failures on 2026-03-25 and 2026-03-30 caused William to show up at businesses referencing conversations and emails that never happened.

---

## The Problem

Session-history.md was logging **phantom actions** — claims of calls and emails that were never actually executed. William walked into businesses referencing these phantom actions and looked confused/unprofessional.

## The Rules

### 1. SINGLE SOURCE OF TRUTH: `deals` table in `pipeline.db`

- If it's not in the `deals` table with a `deal_id`, **IT DOESN'T EXIST**
- No exceptions

### 2. SESSION-HISTORY.MD IS NARRATIVE ONLY

- Use for documenting learnings, decisions, architecture
- **NEVER** use for operational data (who was called, what was sent)
- **NEVER** trust session-history.md for generating scripts or routes

### 3. ALL CALL LISTS MUST COME FROM THE DATABASE

- Use `python -m src.pitch_briefer --next 10` for call lists
- Use `python -m src.morning_call_sheet` for daily sheets
- **NEVER** generate scripts from JSON files or markdown

### 4. VALIDATION BEFORE ANY OUTREACH

Run this before generating ANY call list or script:
```bash
cd /home/clawdbot/dev-sandbox/projects/lead-generation/sales-pipeline
python -m src.validate_pipeline
```

If there are issues, run with `--fix`:
```bash
python -m src.validate_pipeline --fix
```

### 5. OUTREACH LOGGING MUST BE VERIFIED

When logging outreach:
1. Log to `outreach_log` table with valid `deal_id`
2. Update `deals.stage` accordingly
3. Set `deals.next_action_date` for follow-up

**Phantom logging = logging without actually doing the action = FORBIDDEN**

### 6. "WARM" STATUS REQUIRES DATABASE VERIFICATION

Before telling William a lead is "warm":
1. Check `outreach_log` for actual contact records
2. Verify the `deals.stage` reflects the contact
3. If no records exist, **IT'S A COLD LEAD**

---

## Stage Definitions

| Stage | Meaning |
|-------|---------|
| Intake | Never contacted — cold |
| Contacted | First touch done (call/email/visit), waiting response |
| Qualified | Showed interest, warm lead |
| Meeting Booked | Demo/call scheduled |
| Proposal Sent | Formal proposal delivered |
| Closed Won | Customer! |
| Closed Lost | Explicit no, hostile, or dead |

---

## Verification Commands

```bash
# Validate pipeline integrity
python -m src.validate_pipeline

# Check specific company
python -m src.validate_pipeline --company "Golden Plumbing"

# Generate verified call list
python -m src.pitch_briefer --next 10
```

---

## What Caused The Failures

1. **2026-03-24:** Session-history.md claimed "5 follow-up emails sent" — they were never sent
2. **2026-03-25:** William did in-person visits based on phantom data
3. **2026-03-30:** Same failure pattern — Rachel at Von & Co said she never received contact

**Root cause:** AI was writing to session-history.md as if actions happened, without actually executing them or logging to the database.

---

## Prevention

1. This file exists as a reminder
2. `validate_pipeline.py` must pass before generating outreach
3. All scripts pull from database, never from JSON/markdown
4. "Trust but verify" — always confirm database state before claiming a lead is warm
