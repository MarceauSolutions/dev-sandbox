# Test Data Policy

**Last Updated:** 2026-03-28

## Problem

Test data inserted into production databases pollutes real pipeline stats and PA responses. "Test HVAC Co" appeared as a Trial Active lead, confusing the actual business state.

## Rules

### 1. Never Insert Test Records into Production DB

Test scripts should:
- Use in-memory SQLite (`:memory:`)
- Use a separate test database file (`pipeline_test.db`)
- Use mock objects instead of real DB inserts

### 2. Test Data Markers (if unavoidable)

If you MUST insert test data into a real DB:
- Use `555` phone numbers (e.g., `239-555-0100`)
- Use `@test*.com` emails
- Prefix company with `[TEST]` or `Test `
- **DELETE IMMEDIATELY after test completes**

### 3. Cleanup Script

Run after any development session that touched the DB:

```bash
/home/clawdbot/scripts/cleanup-test-data.sh
```

This removes records matching test patterns (555 phones, @test emails, "Test" companies).

### 4. Pre-Deployment Check

Before considering any pipeline work "done":
1. Run `cleanup-test-data.sh`
2. Verify with: `sqlite3 /home/clawdbot/data/pipeline.db "SELECT * FROM deals WHERE company LIKE 'Test%' OR contact_phone LIKE '%-555-%';"`

## Detection Patterns

```sql
-- Find test data
SELECT * FROM deals 
WHERE contact_phone LIKE '%-555-%'
   OR contact_email LIKE '%@test%'
   OR company LIKE 'Test %'
   OR company LIKE '%Test Co%';
```

## Incident: 2026-03-28

"Test HVAC Co" (id 224) was in Trial Active stage, causing PA to recommend calling a fake lead. Deleted manually. This policy prevents recurrence.
