# Architecture Decisions

> Cross-session conventions. All agents read this at session start.

## Decisions

### [DATE] — Decision Title
**Context**: Why was this decision needed?
**Decision**: What was decided?
**Consequences**: What does this mean for future work?

---

<!-- Add new decisions above this line -->

## Standing Conventions
- Shared code goes in `execution/`, project code in `projects/[name]/src/`
- Every web app gets a launch script in `scripts/`
- PDF for reports, web app for dashboards, automation platform for scheduled tasks
- CLI is never the final interface for user-facing tools
