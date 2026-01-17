# SOP 5: Session Documentation

**When**: At the end of significant work sessions or when major learnings occur

## Purpose

Capture session progress, learnings, and patterns to maintain continuity across sessions. Good session documentation prevents re-learning and enables future Claude sessions to pick up where you left off.

## Prerequisites

- Completed meaningful work in current session
- Discovered new patterns or learnings worth preserving

## When to Document

### Full Documentation (End of Session)

Document at end of session when:
- Major milestone completed
- Session lasted 30+ minutes
- Significant code changes made
- New patterns discovered

### Quick Save (Mid-Session)

Save progress mid-session when:
- Completing a major milestone
- Before risky operations
- Every 30-60 minutes of intensive work
- After figuring something out that took effort

## Steps

### Step 1: Create Session History File

If it doesn't exist:

```bash
mkdir -p docs
touch docs/session-history.md
```

### Step 2: Add Session Entry

```markdown
## 2026-01-16: [Session Title]

**Context:** [What you were working on]

**Accomplished:**
- [Key achievement 1]
- [Key achievement 2]
- [Key achievement 3]

**Key Learnings:**
1. [Learning with brief explanation]
2. [Pattern discovered]
3. [Gotcha to remember]

**New Communication Patterns:**
| User Says | Claude Does |
|-----------|-------------|
| "[phrase]" | [action] |

**Files Created/Updated:**
- `path/to/file.ext` - [What changed]

**Next Session:**
- [ ] [Task to continue]
- [ ] [Thing to follow up on]
```

### Step 3: Update CLAUDE.md (If New Patterns)

If you discovered new communication patterns, add to CLAUDE.md:

```markdown
## Communication Patterns

| User Says | Claude Does |
|-----------|-------------|
| "your new phrase" | [what Claude should do] |
```

### Step 4: Commit Documentation

```bash
git add docs/session-history.md CLAUDE.md
git commit -m "docs: Session learnings from 2026-01-16"
```

## Session History Template

```markdown
# Session History

This file tracks session progress and learnings for continuity.

---

## 2026-01-16: [Title]

**Context:** [What you were working on]

**Accomplished:**
-

**Key Learnings:**
1.

**Files Changed:**
-

**Next Session:**
- [ ]

---

## 2026-01-15: [Previous Session]

...
```

## What to Document

### Always Document

- Breakthroughs or "aha" moments
- Commands or patterns that took multiple tries
- Errors and how you fixed them
- New workflows you established

### Skip Documenting

- Trivial changes (typo fixes)
- Standard operations (basic git commands)
- Things already in documentation

## Quick Save Checklist

For mid-session saves, just:

1. Update relevant tracking doc (mark items complete)
2. Commit if files changed
3. Brief bullet in session-history.md

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Session history getting long | Archive old entries to `docs/archive/` |
| Forgot to document | Add retroactively, note the date gap |
| Not sure what to document | If you'd be frustrated re-discovering it, document it |
| Taking too long | Start with bullets, expand only if needed |

## Session Handoff (Between Sessions)

When starting a new session:

1. Tell Claude: "Read docs/session-history.md for context"
2. Mention what you want to continue
3. Claude will pick up from where you left off

Example:
> "I'm continuing from yesterday's session. Please read session-history.md and help me finish the authentication feature."

## Success Criteria

- ✅ Session entry added to session-history.md
- ✅ Key learnings documented (not just what, but why)
- ✅ Next steps clear for future sessions
- ✅ New patterns added to CLAUDE.md if discovered
- ✅ Changes committed to git

---

*Part of the Claude Development Framework - Free Tier*
