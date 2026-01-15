# Product Opportunity Capture Method

*Internal Method - Marceau Solutions*
*Version: 2026-01-15*

---

## Purpose

Systematically identify workflows, SOPs, and automations that could be productized and sold externally, without interrupting ongoing work.

## Problem Statement

During normal operations, valuable workflows and automations are created on-the-fly:
- SOP 6: Workflow Creation
- SOP 21: SOP Creation (meta-method)
- Ad-hoc scripts and automations

Some of these could be sold as products, but without a capture system:
- Ideas are forgotten
- No systematic review process
- No connection to viability analysis (SOP 17)

## Solution

A two-phase capture and review system:

### Phase 1: Capture (During Work)
- Ask: "Could someone pay for this?"
- If yes: Log in `OPPORTUNITY-LOG.md` (30 seconds)
- Continue working (don't stop to analyze)

### Phase 2: Review (Weekly)
- Friday 4 PM via time-blocks calendar
- For each pending opportunity:
  - Low potential → Archive with reason
  - High potential → Run SOP 17 (Market Viability Analysis)
  - If SOP 17 = GO → Create project via SOP 0

## Decision Tree

```
Building a new workflow/automation?
│
├── Step 1: Is it repeatable internally?
│   └── YES → Create Workflow (SOP 6) or SOP (SOP 21)
│
├── Step 2: Could external users pay for this?
│   ├── NO → Done (just internal workflow)
│   └── YES → Log in OPPORTUNITY-LOG.md
│
└── Weekly Review (Friday 4 PM):
    └── For each pending opportunity:
        ├── Low potential → Archive with reason
        └── High potential → Run SOP 17
            └── If GO → SOP 0 (Project Kickoff)
```

## Files

| File | Purpose |
|------|---------|
| `OPPORTUNITY-LOG.md` | Running log of opportunities |
| `DEFINITION.md` | This file - method definition |

## Integration Points

| Component | Integration |
|-----------|-------------|
| **SOP 6** (Workflow Creation) | Add step: "Could this be a product?" |
| **SOP 21** (SOP Creation) | Add step: "Could this be a product?" |
| **time-blocks** | Weekly recurring: Friday 4 PM review |
| **CLAUDE.md** | Communication pattern: "Log this as a product opportunity" |

## Communication Patterns

| User Says | Claude Does |
|-----------|-------------|
| "Log this as a product opportunity" | Add entry to OPPORTUNITY-LOG.md |
| "This could be a product" | Ask for details, add to OPPORTUNITY-LOG.md |
| "Weekly product review" | Open OPPORTUNITY-LOG.md, review pending items |
| "What product opportunities do we have?" | Read and summarize OPPORTUNITY-LOG.md |

## Success Metrics

| Metric | Target |
|--------|--------|
| Opportunities logged per month | 3-5 |
| % reviewed within 7 days | 100% |
| % pursued after SOP 17 | 20-30% |
| Converted to revenue (year 1) | 1-2 products |

## References

- SOP 6: Workflow Creation
- SOP 17: Market Viability Analysis
- SOP 0: Project Kickoff
- `projects/time-blocks/` - Calendar scheduling tool

---

*Method Complete - 2026-01-15*
