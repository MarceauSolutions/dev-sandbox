# Incident Report: Untested Code Committed

**Date**: 2026-02-08
**Severity**: Medium
**Status**: Resolved (patch applied)

## Summary

TikTok API modules (`tiktok_auth.py`, `tiktok_api.py`, `tiktok_scheduler.py`) were implemented and committed without running through the testing pipeline defined in `testing-strategy.md`.

## Timeline

1. **2026-02-08 (earlier session)**: Project Deployment Sweep plan created with 7 phases
2. **Phase 4**: TikTok modules implemented (3 new Python files, ~800 lines of code)
3. **Phase 5-6**: Documentation updated
4. **Phase 7**: Code committed and pushed to GitHub
5. **Gap identified**: No testing phase existed between Phase 4 (implementation) and Phase 7 (commit)

## Root Cause Analysis

### Primary Cause
The plan file (`velvety-conjuring-goblet.md`) defined implementation phases but **did not include testing phases**. The plan was treated as "organization/finalization" rather than "new feature development" despite including new code implementation.

### Contributing Factors
1. **Plan mode gap**: When creating implementation plans, testing phases were not automatically included
2. **Missing trigger**: No autonomous trigger existed to catch "new code written but not tested"
3. **Context framing**: The task was framed as "deployment sweep" (migration/cleanup) rather than "new feature implementation" despite including new code

### Why SOPs Weren't Followed
- The SOPs exist (SOP 2, testing-strategy.md)
- But they weren't triggered because:
  - No explicit "test the TikTok code" instruction was given
  - The plan jumped from "implement" to "commit" without a testing checkpoint
  - No autonomous trigger existed to catch untested code

## Impact

- 3 new Python files committed without verification they work
- Modules may have bugs that would have been caught by manual testing
- Risk of breaking production if these modules are used without testing

## Resolution

### Immediate Fix
Added to CLAUDE.md Operating Principles:

```markdown
9a. **Pre-commit testing gate** - BEFORE committing new code implementations:
   - **ALWAYS** run at minimum Scenario 1 (Manual Testing) from testing-strategy.md
   - **NEVER** commit new `.py` files without verifying they at least run
   - **CHECK** if plan includes implementation phases → testing phases MUST follow
   - When creating plans with code implementation, automatically add testing phases
   - If about to commit and new code hasn't been tested: STOP and ask user
```

Added new autonomous trigger:
```markdown
- **New code written → BLOCK commit until testing complete** (see #9a below)
```

### Follow-up Actions Required
1. [ ] Run manual testing on TikTok modules (Scenario 1)
2. [ ] Verify imports work: `python -c "from src.tiktok_api import TikTokAPI"`
3. [ ] Update `docs/autonomous-agent-decision-tree.md` with new trigger

## Prevention

### For Future Plans
When a plan includes ANY phase that writes new code (`.py`, `.js`, `.ts`, etc.):
1. Automatically add a testing phase after the implementation phase
2. The testing phase should reference `testing-strategy.md` Scenario 1 at minimum
3. Commit phase should ONLY come after testing phase passes

### Example Correct Plan Structure
```
Phase 4: Implement TikTok API modules
Phase 4a: Test TikTok modules (Scenario 1 - Manual Testing)
Phase 5: Documentation
Phase 6: Pre-deployment verification (if deploying)
Phase 7: Git commit (ONLY after Phase 4a passes)
```

## Lessons Learned

1. **Framing matters**: Even "organizational" tasks can include new code that needs testing
2. **Plans need testing checkpoints**: Any implementation phase must be followed by a testing phase
3. **Autonomous triggers are powerful**: Adding the pre-commit gate prevents future occurrences
4. **Self-annealing works**: This incident led to a patch that strengthens the system

## Related Documents
- `CLAUDE.md` - Operating Principle #9a (new)
- `docs/testing-strategy.md` - Testing pipeline
- `docs/autonomous-agent-decision-tree.md` - Trigger matrix (needs update)
