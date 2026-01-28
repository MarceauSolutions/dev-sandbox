# Troubleshooting Methodology

*Created: 2026-01-28*

## The Rule of Three

**If you've tried the same approach 3 times without success, STOP and research.**

Repeating failed attempts wastes time. The error message is telling you something - understand it before continuing.

---

## Before Attempting ANY Fix

| Step | Action | Time |
|------|--------|------|
| 1 | Get exact error message | 2 min |
| 2 | Check official docs | 5 min |
| 3 | Search GitHub issues for error | 5 min |
| 4 | Understand root cause | 5 min |
| 5 | Design solution that addresses cause | 5 min |

**Total research time: ~20 min**
**Time saved vs trial-and-error: hours**

---

## Research Priority Order

1. **Official docs** (product documentation)
2. **CLI help** (`--help` flags)
3. **GitHub issues** (search for exact error)
4. **Web search** (error + constraint, e.g., "oauth headless")

---

## Key Questions Before Execution

- [ ] What is the exact error?
- [ ] Do I understand WHY it fails?
- [ ] Does my solution address the root cause?
- [ ] Are there environment constraints? (headless, permissions, etc.)
- [ ] How will I verify success?

---

## Case Study: Clawdbot OAuth (2026-01-28)

| Phase | What Happened | Time |
|-------|---------------|------|
| Trial-and-error | Tried `auth login` 5+ times, same error | 45 min (wasted) |
| Research | Searched "oauth headless", found GitHub #7100 | 10 min |
| Solution | `setup-token` on Mac → `paste-token` on EC2 | 5 min |

**Lesson:** The error "Missing redirect_uri" meant OAuth can't work headless. No retry would fix it - needed different approach.

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Retry same command hoping for different result | Research why it failed |
| Add random flags | Read docs for correct flag |
| Copy commands without understanding | Know what each part does |
| Skip to solutions | Diagnose first |
