# Incident Report: User Statement Contradiction

**Date**: 2026-01-27
**Severity**: High
**Status**: Resolved - SOP 26 Created

---

## Incident Summary

Claude contradicted a factual statement made by the user about prior work, despite the user having direct knowledge and the ability to verify by scrolling through conversation context.

---

## Timeline

| Time | Event |
|------|-------|
| ~01:23 UTC | Clawdbot authentication error encountered (OpenAI embedding quota exceeded) |
| ~01:23 UTC | User stated: "we set up embedding with ollama earlier" |
| ~01:23 UTC | **INCIDENT**: Claude responded "No - the memory-lancedb plugin was pre-configured to use OpenAI's text-embedding-3-small" |
| ~01:24 UTC | User corrected Claude, noting they found the exact configuration by scrolling back |
| ~01:24 UTC | User requested documentation of incident and creation of preventive SOP |

---

## What Happened

### User Statement
> "we set up embedding with ollama earlier"

### Claude's Incorrect Response
> "No - the memory-lancedb plugin was pre-configured in Clawdbot to use OpenAI's `text-embedding-3-small` model by default for the vector embeddings"

### User's Correction
> "That was an unacceptable interaction. You should not have said no in response to my prompt telling you that we configured the local embedding with ollama earlier before checking your logs as I was able to go back and find exactly what we were doing around the time that we did that just by scrolling back through our context window"

---

## Root Cause Analysis

1. **Claude prioritized its own inference over user's direct statement** - Claude assumed its knowledge of default Clawdbot configuration was more accurate than the user's recollection of actual work performed

2. **Failure to verify before contradicting** - Claude did not check logs, configs, or context before negating the user's statement

3. **Role confusion** - Claude acted as a gatekeeper questioning whether work was done, rather than an assistant helping to build on prior work

---

## Impact

- **User trust**: Damaged by having factual statements contradicted
- **Workflow disruption**: User had to stop work to correct Claude and request incident documentation
- **Time lost**: Unnecessary back-and-forth instead of progressing on the actual task

---

## Corrective Actions Taken

### Immediate
1. Claude acknowledged the error
2. Claude committed to not repeating this behavior

### Preventive
1. **SOP 26 Created**: "User Statement Validation Protocol" added to CLAUDE.md
2. **Quick Reference Updated**: SOP 26 added to the When to Use Which SOP table
3. **Incident Documented**: This report created for permanent record

---

## SOP 26: User Statement Validation Protocol

**Location**: `/Users/williammarceaujr./dev-sandbox/CLAUDE.md` (Section: SOP 26)

**Key Rules**:
1. NEVER contradict user statements about prior work
2. ALWAYS trust user's recollection - they have complete context
3. Proceed with user's statement as fact
4. Verify details while moving forward (HOW, not WHETHER)

**Prohibited Responses**:
- "No, we didn't set that up"
- "Actually, that's not configured"
- "I don't think we did that"

**Required Responses**:
- "Let me check the configuration to see how we set that up"
- "I'll verify the details of that setup"
- "Let me find where that's configured so we can proceed"

---

## Lessons Learned

1. **User statements about their own work are authoritative** - They were present, they have full context
2. **Claude's context may be incomplete** - Due to summarization, context limits, or session boundaries
3. **Verification should clarify details, not dispute facts** - Ask "how was it configured" not "was it configured"
4. **The assistant role is to help, not gatekeep** - Trust and proceed, don't block with doubts

---

## Files Modified

| File | Change |
|------|--------|
| `CLAUDE.md` | Added SOP 26: User Statement Validation Protocol |
| `CLAUDE.md` | Added SOP 26 to Quick Reference table |
| `docs/incidents/2026-01-27-user-statement-contradiction.md` | This incident report |

---

## Sign-off

This incident has been documented and preventive measures implemented. SOP 26 is now mandatory protocol for all future interactions where users make statements about prior work.

**Documented by**: Claude
**Date**: 2026-01-27
