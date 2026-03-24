---
rule: E09
name: Pre-Flight Mandatory
hook: none — checklist discipline required
trigger: Before starting any task (every task, no exceptions)
---

## Rule

Run the pre-flight checklist before every task. Search inventory for existing tools, check service status, verify standards. SOP 33 documents the full procedure. Never skip this step under time pressure.

## Why it exists

Tools were rebuilt from scratch that already existed in `execution/`. Paid APIs were called when free equivalents were available. Time was wasted on approaches that violated service standards discovered only after implementation.

## Pre-Flight Checklist

```
[ ] 1. Search inventory: python scripts/inventory.py search <keyword>
[ ] 2. Check SYSTEM-STATE.md: is there an existing system for this?
[ ] 3. Check HANDOFF.md: is this task already in progress by another agent?
[ ] 4. Check project CLAUDE.md: are there project-specific constraints?
[ ] 5. Check service-standards.md: are there approved tools for this need?
[ ] 6. Check .env: are needed API keys present?
[ ] 7. Check execution/: is there a shared utility I can reuse?
```

Full SOP: `docs/sops/sop-33-preflight.md` (if it exists)

## How to apply

For tasks >5 minutes:
- Run steps 1-7 above before writing any code
- Document what you found in the task response: "Pre-flight: found X in execution/, using it instead of writing new"

For quick tasks:
- At minimum run step 1 (inventory search) and step 2 (SYSTEM-STATE check)

## Examples

- About to build a lead enrichment script → search `execution/` first: `python scripts/inventory.py search apollo`
- About to send an SMS → check `.env` for TWILIO_ACCOUNT_SID before writing any code
- About to build a web dashboard → check SYSTEM-STATE.md to confirm no existing dashboard covers this need
