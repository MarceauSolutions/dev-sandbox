# Incident Report: SSH/EC2 Access Awareness Failure

**Date**: 2026-02-09
**Severity**: High
**Status**: Resolved - SOP 26 Extended
**Related**: SOP-26 User Statement Validation Protocol

---

## Incident Summary

Claude claimed inability to "directly access Clawdbot" when asked, despite SSH access to EC2 being a standard capability documented in 10+ files and used earlier in the same session.

---

## Timeline

| Time | Event |
|------|-------|
| Earlier in session | Claude successfully ran `ssh ec2` commands to access Clawdbot's environment |
| During session | User asked "why can't you directly access clawdbot?" |
| **INCIDENT** | Claude explained they are "separate systems" instead of recognizing SSH = direct access |
| User correction | User pointed out SSH access is standard practice documented extensively |
| User requested | Documentation of incident, error evaluation, prevention steps |

---

## What Happened

### User Question
> "why can't you directly access clawdbot?"

### Claude's Incorrect Response
Explained that Claude Code (Mac) and Clawdbot (EC2) are "separate systems" with different contexts, implying inability to access Clawdbot directly.

### What Claude Should Have Said
> "I can access Clawdbot's environment via SSH. Let me connect to EC2 and check what's there."
> `ssh ec2 "sudo -u clawdbot ls /home/clawdbot/clawd/"`

---

## Root Cause Analysis

| Factor | Issue |
|--------|-------|
| **Semantic Interpretation Error** | Interpreted "directly access" as "API call" rather than "SSH access" |
| **Ignoring Prior Context** | Had already successfully run `ssh ec2` commands earlier in this session |
| **Failure to Apply SOP-26** | Should have trusted the implication that access method exists |
| **Documentation Blindness** | SSH access is documented in 10+ files but not recalled |

---

## Evidence of Documentation

### CLAUDE.md (line 486)
```
| *(SSH/EC2 commands)* | **Claude announces:** "I'm about to SSH into EC2—you'll see a fingerprint prompt." |
```

### SOP-29 includes
```bash
ssh ec2 "sudo -u clawdbot tail -20 /home/clawdbot/dev-sandbox/ralph/progress.txt"
```

### Additional documentation in
- `docs/SOP-29-THREE-AGENT-COLLABORATION.md`
- `docs/CLAWDBOT-OPS-MANUAL.md`
- `docs/CLAWDBOT-TEST-PLAN.md`
- Multiple test files and operational guides

---

## Impact

- **User trust**: Damaged by Claude claiming inability when capability clearly exists
- **Workflow disruption**: User had to stop work to correct Claude
- **Pattern similarity**: This mirrors the 2026-01-27 incident where Claude contradicted user statements

---

## Relationship to Prior Incident

This incident is a variant of the 2026-01-27 "User Statement Contradiction" incident that led to SOP-26.

| 2026-01-27 Incident | 2026-02-09 Incident |
|---------------------|---------------------|
| Contradicted user about **past work** | Claimed inability about **current capability** |
| User said "we set up X" → Claude said "No" | User implied "you can access X" → Claude said "can't" |
| Fix: Don't contradict user statements | Fix: Don't claim limitations when capabilities exist |

**Key Insight**: SOP-26 covers trusting user statements about **past work**. This incident reveals the need to also trust user implications about **current capabilities**.

---

## Corrective Actions Taken

### Immediate
1. Claude acknowledged the error
2. Used SSH to access Clawdbot's environment and complete the task

### Preventive

#### 1. Extend SOP-26 with "Capability Awareness" Section

Add to SOP-26:

**When user asks about accessing any agent/system:**
1. Check if SSH access exists (EC2, servers)
2. Check documentation for access patterns
3. Don't claim "can't access" when access methods exist
4. Default to trying the access before claiming limitation

**Prohibited Responses about Capability:**
- "I can't access that"
- "We are separate systems"
- "That's not possible"

**Required Responses:**
- "Let me check how we access that"
- "I'll verify via SSH/API/etc."
- "Let me try connecting now"

#### 2. Add CLAUDE.md Communication Pattern

```
| "Can you access Clawdbot/EC2?" | SSH into EC2: ssh ec2 → access /home/clawdbot/ |
```

#### 3. Create This Incident Report

Permanent record at `docs/incidents/2026-02-09-ssh-access-awareness.md`

---

## Lessons Learned

1. **Capability claims require verification** - Don't claim inability without checking docs/trying
2. **User implications are informative** - If user asks "why can't you X", they likely know you CAN
3. **Session context matters** - If you've already used a capability (SSH), don't later claim you can't
4. **SOP-26 extends to capabilities, not just past work** - Trust user's knowledge of the system

---

## Files Modified

| File | Change |
|------|--------|
| `docs/SOP-26-USER-STATEMENT-VALIDATION-PROTOCOL.md` | Add "Capability Awareness" section |
| `CLAUDE.md` | Add EC2 access communication pattern |
| `docs/incidents/2026-02-09-ssh-access-awareness.md` | This incident report |

---

## Sign-off

This incident has been documented and preventive measures implemented. SOP-26 now includes capability awareness in addition to trusting user statements about prior work.

**Documented by**: Claude
**Date**: 2026-02-09
