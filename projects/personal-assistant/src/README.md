# Legal Case Manager

Personal case management system for tracking a housing discrimination case. Provides tools for evidence cataloging, deadline tracking, timeline construction, document generation, and communication logging.

## SOP 32 Routing Result

| Field | Value |
|-------|-------|
| **Type** | Company-Specific Project (personal) |
| **Location** | `projects/marceau-solutions/legal-case-manager/` |
| **Deploy To** | None (personal use, stays in dev-sandbox) |
| **Next SOP** | Lightweight SOP 0 → SOP 1 |
| **Skip SOPs** | SOP 17 (not a product), SOPs 11-16 (no publishing), SOP 31 (not standalone) |

## Structure

```
src/                    Python tools
workflows/              Case-specific operational SOPs
templates/              Document and data templates
data/                   Sensitive case data (GITIGNORED)
```

## Quick Start

See `CLAUDE.md` for full instructions and case-specific SOPs.

## Privacy

All files in `data/` are gitignored. No personally identifiable information (PII) or case evidence should ever be committed to version control.
