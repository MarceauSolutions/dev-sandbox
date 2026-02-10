# SOP 21: SOP Creation Method (Meta-Method)

**When**: A recurring process is identified that needs documentation

**Purpose**: Systematically decide when and how to create new SOPs on-the-fly

**Agent**: Any agent. Claude Code for complex SOPs. Clawdbot for simple SOPs. Ralph: N/A.

**Trigger Conditions**:
- Task repeated 2+ times
- Complex multi-step process completed
- New integration/tool set up
- Process others (or future Claude sessions) will need to replicate

**Decision Tree**:
```
Is this task repeatable?
├── NO → Skip SOP, note in session-history.md if notable
└── YES → Score using SOP 6 matrix (Recurrence, Consistency, Complexity, Onboarding)
          ├── Score 0-3 → Skip or create after 2nd occurrence
          ├── Score 4-6 → Create lightweight SOP
          └── Score 7-12 → Create full SOP immediately
```

**Lightweight SOP Template** (scores 4-6):
```markdown
# SOP: [Name]

*Created: YYYY-MM-DD*

## Purpose
[One sentence: what this SOP does]

## When to Use
[Trigger conditions]

## Steps
1. [Step]
2. [Step]
3. [Step]

## Commands
\`\`\`bash
[key commands]
\`\`\`

## Verification
- [ ] [How to know it worked]
```

**Full SOP Template** (scores 7-12):
```markdown
# SOP: [Name]

*Last Updated: YYYY-MM-DD*
*Version: 1.0.0*

## Overview
[What this SOP covers]

## Prerequisites
| Requirement | Check | Expected |
|-------------|-------|----------|
| ... | ... | ... |

## Steps
### Step 1: [Name]
**Objective**: ...
**Actions**: ...
**Verification**: You should see...

[Repeat for each step]

## Troubleshooting
| Issue | Cause | Solution |
|-------|-------|----------|

## Rollback Procedures
[How to undo/recover]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Commands Reference
\`\`\`bash
[All commands used]
\`\`\`
```

**Integration**:
- Add new SOP to CLAUDE.md Quick Reference table
- Add communication pattern if relevant
- Reference in SOP 6 (Workflow Creation)

**Location for meta-method documentation**: `methods/sop-creation/`

**Success Criteria**:
- [ ] Task scored using SOP 6 matrix (Recurrence, Consistency, Complexity, Onboarding)
- [ ] Appropriate template used (Lightweight 4-6, Full 7-12)
- [ ] SOP added to CLAUDE.md Quick Reference table
- [ ] Communication pattern added (if applicable)

**References**: SOP 6 (Workflow Creation), SOP 20 (Internal Method Development)
