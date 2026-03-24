# SOP 25 — Documentation Decision Framework

> Not everything needs documentation. This framework decides when it's worth it.

## Document When:
- **Effort > 30 minutes** — Worth capturing for future reference
- **Non-obvious decisions** — "Why did we do it this way?"
- **Setup/config** — Someone (including future you) will need to reproduce this
- **API integrations** — Keys, endpoints, rate limits, gotchas
- **Recurring tasks** — If you'll do it again, write an SOP

## Skip Documentation When:
- Code is self-explanatory
- It's a one-time fix
- Standard library/framework usage
- The git commit message captures it

## Where to Document:
| Type | Location |
|------|----------|
| How to do a task | `docs/sops/sop-XX-name.md` |
| Architecture decision | `docs/architecture-decisions.md` |
| Project context | Project's `CLAUDE.md` |
| Session notes | `docs/session-history.md` |
| System state | `docs/system-state.md` |
| API keys/config | `.env` (with comments) |
