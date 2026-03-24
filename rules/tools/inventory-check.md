# Tool: Inventory Check (inventory.py)

**File:** `scripts/inventory.py`
**When to use:** Before creating ANY new .py file. Search first — it probably already exists.

## Exact Commands

```bash
# Search for tools matching a keyword
python scripts/inventory.py search <keyword>

# List all projects
python scripts/inventory.py list

# List all scripts
python scripts/inventory.py scripts
```

## What It Searches

The inventory searches:
- `execution/` — all 106 shared utility scripts
- `scripts/` — utility and maintenance scripts
- `projects/` — project source files

Results show: file path, description, what it does.

## Interpreting Results

If a result looks like it covers your need:
1. Read the file: examine the function signatures and CLI flags
2. Check if it handles your exact use case, or can be adapted
3. If it needs a new feature, ADD to the existing file — don't create a parallel one

## Pre-flight Search Examples

```bash
# About to build a PDF generator
python scripts/inventory.py search pdf
# → execution/branded_pdf_engine.py — use this

# About to build an email sender
python scripts/inventory.py search email
# → execution/send_onboarding_email.py — use this

# About to build an SMS script
python scripts/inventory.py search sms
# → execution/twilio_sms.py — use this

# About to build a lead scraper
python scripts/inventory.py search lead
# → execution/[lead tools] or projects/shared/lead-scraper/

# About to build a data processor
python scripts/inventory.py search [your keyword]
# → check results before building anything new
```

## When to Create a New File Anyway

Only create a new file if:
1. The inventory search finds nothing relevant
2. The existing tool genuinely cannot be extended to cover the need
3. The task is truly novel

When creating a new file, document your inventory search in the commit message:
`feat: add [name].py — no existing tool for [capability] (inventory confirmed)`
