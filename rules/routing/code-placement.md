# Code Placement Rules

> Summary version lives in `rules/routing/ROUTING.md` tree #4.

## The DOE Architecture

**D**irective → **O**rchestration → **E**xecution

- **Directive**: What to do (a spec, a PRD, a workflow definition)
- **Orchestration**: How to coordinate (a script that calls multiple execution modules)
- **Execution**: The actual work (the Python functions that do the thing)

This structure applies strictly to `execution/` (shared utilities). Project code in `projects/[name]/src/` can be more flexible.

## Placement Decision

| Condition | Goes In | Example |
|-----------|---------|---------|
| Used by 2+ projects | `execution/` | `execution/branded_pdf_engine.py`, `execution/twilio_sms.py` |
| Used by 1 project only | `projects/[tower]/[project]/src/` | `projects/marceau-solutions/fitness/tools/fitness-influencer/src/` |
| Generated output / pipeline result | `projects/[name]/output/` | `projects/marceau-solutions/digital/outputs/*.csv` |
| Truly temporary (dev scratch) | `/tmp` | Never committed to git |
| Scheduled automation | n8n workflow | NOT a Python cron script |

## Promoting from projects/ to execution/

When a second project starts using a script that lives in `projects/[name]/src/`, move it:

1. Copy to `execution/[descriptive_name].py`
2. Update both projects to import from `execution/`
3. Verify no circular imports
4. Update `python scripts/inventory.py` metadata if applicable
5. Commit with message: `refactor: promote [name] to shared execution/`

## Current execution/ inventory

Always search before creating: `python scripts/inventory.py search <keyword>`

106 scripts currently in `execution/`. Key ones:
- `execution/branded_pdf_engine.py` — PDF generation (10 templates)
- `execution/send_onboarding_email.py` — SMTP email pattern
- `execution/twilio_sms.py` — SMS sending
- `execution/pdf_router.py` — auto-routes content to correct PDF template
- `execution/context_preloader.py` — surfaces relevant files per project
- `execution/session_summarizer.py` — captures session work
- `execution/memory_consolidator.py` — audits and maintains memory files
- `execution/accountability_handler.py` — accountability system

## Project Source Layout

```
projects/marceau-solutions/
├── fitness/
│   ├── clients/
│   │   ├── boabfit/              # Julia's brand
│   │   └── pt-business/          # William's coaching
│   └── tools/
│       ├── fitness-influencer/src/   # FitAI platform source
│       ├── fitness-influencer-mcp/
│       └── trainerize-mcp/
├── digital/
│   ├── clients/[name]/
│   └── tools/
│       ├── website-builder/src/
│       └── web-dev/
├── media/tools/[platform]-creator/
└── labs/[project]/src/
```
