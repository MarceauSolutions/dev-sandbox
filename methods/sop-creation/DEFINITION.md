# Method: SOP Creation (Meta-Method)

*Created: 2026-01-15*
*Version: 2026-01-15*

## Problem Statement

SOPs should be created systematically when recurring processes are identified, not ad-hoc. We need a consistent method to:
1. Decide WHEN to create an SOP (vs skipping or noting in session-history)
2. Decide WHAT level of detail is appropriate (lightweight vs full)
3. Ensure consistency across all SOPs
4. Integrate new SOPs into CLAUDE.md properly

## Who Uses This Method

- **Claude**: When completing tasks and identifying repeatable patterns
- **William**: When reviewing workflows and identifying documentation gaps

## Success Criteria

- Consistent SOP format across the codebase
- Clear decision criteria for when to create SOPs
- No "orphan" SOPs (all integrated into Quick Reference table)
- Reduced time spent recreating previously-solved processes

## Inputs

- Completed task or process
- Frequency of occurrence (estimated)
- Complexity level
- Who needs to replicate this (onboarding value)

## Outputs

1. **Decision**: Create SOP / Skip / Note only
2. **SOP Level**: Lightweight (template) / Full (comprehensive)
3. **SOP Document**: In appropriate location
4. **Integration**: Added to CLAUDE.md Quick Reference

## Decision Tree

```
Is this task repeatable?
├── NO → Skip SOP
│        └── Notable? → Add brief note to session-history.md
│
└── YES → Score using SOP 6 matrix
          │
          ├── Score 0-3 (Low) → Skip or create after 2nd occurrence
          │
          ├── Score 4-6 (Medium) → Create Lightweight SOP
          │   └── Use LIGHTWEIGHT-TEMPLATE.md
          │
          └── Score 7-12 (High) → Create Full SOP immediately
              └── Use FULL-TEMPLATE.md
```

## Scoring Matrix (from SOP 6)

| Factor | 0 | 1 | 2 | 3 |
|--------|---|---|---|---|
| **Recurrence** | One-time | Unlikely | Probable | Frequent |
| **Consistency** | Doesn't matter | Nice to have | Important | Critical |
| **Complexity** | Trivial (<3 steps) | Simple | Moderate | Complex (10+ steps) |
| **Onboarding** | Only I'll do this | Might help others | Would help | Essential for handoff |

**Total Score**: Sum of all factors (0-12)

## Integration Steps

After creating an SOP:
1. Add to CLAUDE.md Quick Reference table
2. Add communication pattern (if applicable)
3. Reference from related SOPs
4. Update KNOWLEDGE_BASE.md (if contains learnings)

## Relationship to SOP 6 (Workflow Creation)

- **SOP 6**: Creates workflow files in `[project]/workflows/`
- **SOP 21 (this)**: Decides WHETHER to create and WHAT format to use
- **Difference**: SOP 21 adds the decision layer before SOP 6 executes

## Templates

See:
- `LIGHTWEIGHT-TEMPLATE.md` - For scores 4-6
- `FULL-TEMPLATE.md` - For scores 7-12
