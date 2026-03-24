---
rule: E06
name: Build Foundations
hook: none — judgment required
trigger: When scoping any new tool, database, or system — especially one that might grow
---

## Rule

Before implementing, ask: "Will this need redoing in 3-6 months?" If yes, build the scalable version now. Shortcuts that create rework cost more total time than doing it right the first time.

## Why it exists

Multiple tools were built for "just today" that immediately needed rebuilding: the Google Sheet PT tracker that couldn't handle daily metrics, the Mac launchd email script that needed to be an n8n workflow, the markdown files that should have been a deployed system.

## How to apply

For any new system, ask these 4 questions:
1. **Will the data grow?** If yes → SQLite (not a JSON file or Google Sheet)
2. **Will more people use it?** If yes → design the multi-user schema now (even if only 1 user today)
3. **Will it run on a schedule?** If yes → n8n (not a cron job on Mac)
4. **Will it need a UI eventually?** If yes → build the FastAPI backend now, add frontend when needed

**The 3-month test**: Imagine this tool in 3 months with 10x the data and 2x the users. Does your current design still work? If no → redesign now.

## Examples

- Building a lead tracker → use SQLite from day 1, not a CSV (CSV breaks at 1000 rows + concurrent writes)
- Building a digest script → wire to n8n immediately, not Mac launchd (Mac launchd stops when laptop closes)
- Building a client portal → design the auth model now, even if William is the only user today
