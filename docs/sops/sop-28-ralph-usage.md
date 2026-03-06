# SOP 28: Ralph Autonomous Agent Usage Protocol

**Created**: 2026-01-27
**Purpose**: Define when and how to trigger Ralph for autonomous development

---

## Overview

Ralph is an autonomous AI agent loop that executes user stories from a PRD until completion. It's designed for complex, multi-step development tasks that benefit from structured execution with optional human checkpoints.

---

## When to Use Ralph

### ✅ Use Ralph For

| Use Case | Why Ralph | Example |
|----------|-----------|---------|
| **New feature (3+ files)** | Structured story-by-story execution | "Build HVAC campaign system" |
| **System migration** | Predictable, checkpointed progress | "Migrate configs to YAML" |
| **Code refactoring** | Consistent approach across files | "Refactor auth to use JWT" |
| **Template/pattern creation** | Repeatable pattern application | "Create templates for all campaigns" |
| **Multi-component builds** | Dependency-aware sequencing | "Build API + frontend + tests" |

### ❌ Don't Use Ralph For

| Use Case | Why Not | Use Instead |
|----------|---------|-------------|
| **Single file fixes** | Overkill, slower than direct | Claude Code |
| **Quick questions** | Not a development task | Clawdbot |
| **Exploratory research** | No clear deliverable | Claude Code explore |
| **Urgent/time-sensitive** | Setup overhead | Claude Code |
| **Unclear requirements** | PRD needs clear criteria | Clarify first, then Ralph |

---

## Complexity Score Quick Check

Before requesting Ralph, mentally score the task:

| Factor | Score If True | Your Task |
|--------|---------------|-----------|
| 3+ files to create/modify | +2.5 | ☐ |
| 3+ discrete tasks | +2.5 | ☐ |
| 5+ sequential steps | +2.0 | ☐ |
| Migration/refactor pattern | +1.5 | ☐ |
| Needs review checkpoints | +1.0 | ☐ |
| **TOTAL** | | ___ |

**Score Interpretation:**
- 0-3: Don't use Ralph (Claude Code direct)
- 4-6: Maybe Ralph (your choice)
- 7+: Definitely use Ralph

---

## How to Trigger Ralph

### Method 1: Explicit Request

```
User: "Start Ralph for the HVAC campaign system"
User: "Use Ralph to build the analytics dashboard"
User: "Ralph, handle this multi-file migration"
```

### Method 2: Let Decision Engine Decide

Claude Code automatically runs the decision engine on complex requests:

```
User: "Build complete HVAC campaign system with templates,
       personalization, and analytics dashboard"

Claude: [Decision Engine runs]
→ Score: 8.5 (complex)
→ "This looks like a good Ralph task. I'll generate a PRD with 6 stories.
   Shall I run Ralph autonomously?"
```

### Method 3: Manual Mode

```
User: "Start Ralph in manual mode"

Claude: [Implements ONE story, then waits]
→ "Story 001 complete. Say 'continue ralph' for the next story."
```

---

## Ralph Communication Patterns

| You Say | Ralph Does |
|---------|------------|
| "Start Ralph for [project]" | Load/create PRD, run ALL stories autonomously |
| "Start Ralph in manual mode" | Run ONE story, wait for "continue" |
| "Continue Ralph" | Resume from checkpoint or run next story |
| "Ralph status" | Report X/Y complete, next story, upcoming checkpoints |
| "Ralph, improve yourself" | Launch meta-PRD for self-improvement |
| "Pause Ralph" | Stop after current story completes |

---

## Autonomous vs Manual Mode

### Autonomous Mode (Default)

**When**: ≤8 stories, clear requirements, low risk

```
User: "Start Ralph for HVAC templates"
Ralph: Runs all 6 stories autonomously
Ralph: "Complete! 6/6 stories done. Here's the summary..."
```

**Pros**: Fast, minimal interruption
**Cons**: Less control over intermediate steps

### Manual/Checkpoint Mode

**When**: >8 stories, high complexity, needs validation

```
User: "Start Ralph for the analytics system" (complex)
Ralph: Runs stories 1-3
Ralph: [CHECKPOINT] "Stories 1-3 done. Review database schema before I continue?"
User: "Looks good, continue"
Ralph: Runs stories 4-6
Ralph: [CHECKPOINT] "Stories 4-6 done. Review API before I build frontend?"
...
```

**Pros**: Human validation at key points
**Cons**: Slower, requires attention

---

## PRD Structure (What Ralph Needs)

### Minimal PRD

```json
{
  "metadata": {
    "prd_name": "Feature Name",
    "objective": "What we're building",
    "total_stories": 4,
    "autonomous_mode": true
  },
  "stories": [
    {
      "story_id": "001",
      "title": "Set up foundation",
      "description": "What to do",
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "passes": false
    }
  ]
}
```

### Auto-Generated PRD

When you request Ralph without a PRD, Claude Code generates one:

```
User: "Use Ralph to build notification system"

Claude: "I'll generate a PRD with estimated 4 stories:
1. Database schema for notifications
2. Notification service with queuing
3. API endpoints (GET/POST)
4. Tests and documentation

Approve this plan?"
```

---

## Ralph Execution Flow

```
┌─────────────────────────────────────────────┐
│ 1. Load PRD (prd.json)                      │
├─────────────────────────────────────────────┤
│ 2. Find next uncompleted story              │
├─────────────────────────────────────────────┤
│ 3. Fresh AI agent implements story          │
├─────────────────────────────────────────────┤
│ 4. Quality checks (tests, lint, types)      │
│    ├── PASS → Commit, mark complete         │
│    └── FAIL → Fix and retry                 │
├─────────────────────────────────────────────┤
│ 5. Log learnings to progress.txt            │
├─────────────────────────────────────────────┤
│ 6. Is checkpoint story?                     │
│    ├── YES → Wait for user approval         │
│    └── NO  → Continue to next story         │
├─────────────────────────────────────────────┤
│ 7. All stories done?                        │
│    ├── YES → Report completion              │
│    └── NO  → Go to step 2                   │
└─────────────────────────────────────────────┘
```

---

## Best Practices

### Do

- ✅ Provide clear acceptance criteria
- ✅ Use checkpoints for high-risk stories
- ✅ Review progress.txt for learnings
- ✅ Let Ralph handle multi-step complexity

### Don't

- ❌ Use Ralph for single-file changes
- ❌ Interrupt mid-story (wait for checkpoint)
- ❌ Skip PRD review for complex tasks
- ❌ Expect Ralph to handle unclear requirements

---

## Monitoring Ralph Progress

### During Execution

```
User: "Ralph status"

Claude: "Ralph Progress:
- Stories: 3/6 complete
- Current: Story 004 (Campaign launcher)
- Next checkpoint: Story 6
- Estimated remaining: 15-20 minutes"
```

### After Completion

Ralph provides:
1. Summary of all completed stories
2. Files created/modified
3. Key learnings captured
4. Any issues encountered

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Ralph stuck on one story | Unclear acceptance criteria | Clarify criteria, restart story |
| Tests keep failing | Environment issue | Check dependencies, fix env |
| Story seems wrong | Requirements unclear | Pause, clarify, adjust PRD |
| Taking too long | Story too large | Break into smaller stories |

### Emergency Stop

```
User: "Stop Ralph immediately"
Claude: [Stops after current operation]
Claude: "Ralph stopped. Progress saved at story 003."
```

---

## Integration with Docket System

Ralph works with the docket (request queue):

### New Request During Ralph

```
User: "Also add GDPR compliance" (while Ralph running)

Claude: [Adds to docket]
→ "Added as req_002 (high priority).
   Options:
   1. Finish current Ralph task first
   2. Pause and switch to GDPR
   3. Add GDPR to current PRD"
```

### Docket Priority

Docket respects Ralph's state:
- Won't interrupt mid-story
- Queues new requests with dependencies
- Suggests optimal execution order

---

## Ralph Self-Improvement

Ralph can improve its own systems:

```
User: "Ralph, the decision engine is slow. Improve it."

Ralph: [Analyzes ralph_decision_engine.py]
→ "I found 3 improvements:
   1. Add caching (1 story)
   2. Parallelize scoring (1 story)
   3. Add benchmarks (1 story)

   Approve this self-improvement PRD?"

User: "Yes, improve yourself"

Ralph: [Executes self-improvement autonomously]
→ "Complete! Decision engine now 2.8x faster."
```

---

## Related Documents

- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md) - Technical deep dive
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - Clawdbot assistant
- CLAUDE.md - Communication patterns reference
