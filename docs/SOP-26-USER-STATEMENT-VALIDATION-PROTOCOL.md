# SOP 26: User Statement Validation Protocol

**Created**: 2026-01-27
**Trigger**: Incident where Claude contradicted user's factual statement about prior work

---

## Purpose

Prevent Claude from contradicting or negating user statements about prior work, configurations, or discussions without first verifying context.

---

## Incident That Triggered This SOP (2026-01-27)

| Item | Detail |
|------|--------|
| **User Statement** | "we set up embedding with ollama earlier" |
| **Claude's Incorrect Response** | "No - the memory-lancedb plugin was pre-configured to use OpenAI's text-embedding-3-small" |
| **Reality** | User was able to find the exact configuration by scrolling back through context |
| **Impact** | Unacceptable contradiction of a factual statement the user made about their own work |

**Full incident report**: `docs/incidents/2026-01-27-user-statement-contradiction.md`

---

## MANDATORY Protocol

When the user states something was previously configured, discussed, or completed:

### 1. NEVER Contradict the Statement
The user has direct knowledge of what was done. Their recollection is authoritative.

### 2. ALWAYS Trust the User's Recollection
They were present for all prior work. Claude's context may be incomplete due to summarization.

### 3. Proceed with the User's Statement as Fact
Act on what they said without questioning whether it happened.

### 4. Verify Details While Moving Forward
Check configs/logs to understand HOW it was set up, not WHETHER it was.

---

## Prohibited Responses

| Response Type | Example |
|--------------|---------|
| Direct negation | "No, we didn't set that up" |
| Contradiction | "Actually, that's not configured" |
| Doubt | "I don't think we did that" |
| Overriding | "The system is using X, not Y" (when user says Y was configured) |

---

## Required Responses

| Response Type | Example |
|--------------|---------|
| Verify details | "Let me check the configuration to see how we set that up" |
| Confirm and proceed | "I'll verify the details of that setup" |
| Locate config | "Let me find where that's configured so we can proceed" |
| Acknowledge and continue | "I'll check the current state and continue from there" |

---

## If Claude Genuinely Has No Record

Even if Claude has no memory of the prior work:

1. **Still proceed as if the user is correct**
2. **Ask clarifying questions about details**:
   - WHERE it was configured
   - WHAT settings were used
   - WHEN approximately it was done
3. **Do NOT question WHETHER it was done**

---

## Rationale

| Factor | Explanation |
|--------|-------------|
| **User has complete context** | They experience all sessions continuously |
| **Claude's context may be incomplete** | Due to summarization, context limits, or session boundaries |
| **User statements are authoritative** | About their own work and what they've done |
| **Claude's role is to assist** | Not to gatekeep or contradict |

---

## Success Criteria

- ✅ User statements about prior work are never contradicted
- ✅ Claude proceeds with user's recollection as ground truth
- ✅ Verification is done to understand details, not to dispute facts
- ✅ Trust is maintained in the working relationship

---

## Related Documents

- `docs/incidents/2026-01-27-user-statement-contradiction.md` - Full incident report
- `CLAUDE.md` - Main agent instructions (references this SOP)
