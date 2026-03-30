# Database Path Note

**IMPORTANT**: The `pipeline.db` in this directory is a SYMLINK to the canonical database at:
```
/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db
```

This ensures all sales-pipeline tools use the same database.

## Created: 2026-03-30

During audit, discovered that `auto_followup.py` was reading an empty local database 
while the real data was in `projects/shared/sales-pipeline/data/pipeline.db`.

Fixed by creating symlink so both paths resolve to the same file.

## DO NOT:
- Delete the symlink
- Create a new pipeline.db here
- Move the shared database without updating the symlink
