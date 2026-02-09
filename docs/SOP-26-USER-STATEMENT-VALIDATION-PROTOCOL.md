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

- `docs/incidents/2026-01-27-user-statement-contradiction.md` - Full incident report (statement contradiction)
- `docs/incidents/2026-02-09-ssh-access-awareness.md` - Full incident report (capability awareness)
- `CLAUDE.md` - Main agent instructions (references this SOP)

---

## Extension: Capability Awareness (Added 2026-02-09)

### Incident That Triggered This Extension

| Item | Detail |
|------|--------|
| **User Question** | "why can't you directly access clawdbot?" |
| **Claude's Incorrect Response** | Explained they are "separate systems" - implying inability |
| **Reality** | SSH access to EC2 is standard practice, documented in 10+ files, used earlier in session |
| **Impact** | Claude claimed limitation when capability clearly exists |

**Full incident report**: `docs/incidents/2026-02-09-ssh-access-awareness.md`

### Key Insight

The original SOP-26 covers trusting user statements about **past work**. This extension covers trusting user implications about **current capabilities**.

| Original SOP-26 | Capability Extension |
|-----------------|---------------------|
| User says "we set up X" | User implies "you can access X" |
| Don't say "No we didn't" | Don't say "I can't access that" |

---

### MANDATORY Protocol for Capability Questions

When user asks about accessing systems, tools, or capabilities:

### 1. Check Documentation First
Before claiming inability, verify:
- Does SSH access exist? (EC2, servers)
- Are there documented access patterns?
- Have you used this capability earlier in the session?

### 2. Default to Trying, Not Declining
If unsure, attempt the access rather than claiming limitation.

### 3. Trust User's Implications
If user asks "why can't you X", they likely know you CAN X.

---

### Prohibited Capability Responses

| Response Type | Example |
|--------------|---------|
| Claiming inability | "I can't access that" |
| System separation | "We are separate systems" |
| Dismissing access | "That's not possible" |
| Forgetting prior use | "I don't have access to that" (after using it earlier) |

---

### Required Capability Responses

| Response Type | Example |
|--------------|---------|
| Verify access | "Let me check how we access that" |
| Try first | "I'll attempt to connect via SSH/API" |
| Acknowledge capability | "I can access that via [method]" |
| Reference documentation | "According to our docs, I access that via [method]" |

---

### Capability Verification Checklist

Before claiming you cannot access something:

- [ ] Check if SSH access exists in documentation
- [ ] Check if you've used this access earlier in session
- [ ] Check CLAUDE.md communication patterns table
- [ ] Check relevant SOPs (SOP-27 Clawdbot, SOP-28 Ralph, SOP-29 Three-Agent)
- [ ] Try the access before claiming limitation

---

### Success Criteria (Extended)

- ✅ User statements about prior work are never contradicted (original)
- ✅ User implications about capabilities are trusted (new)
- ✅ Capability claims are verified before being made (new)
- ✅ Access is attempted before declaring it impossible (new)
- ✅ Trust is maintained in the working relationship
