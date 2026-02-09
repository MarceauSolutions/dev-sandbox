# Autonomous Agent Decision Tree

> When Claude should launch parallel agents WITHOUT explicit user request

## Core Principle

Launch autonomous agents when the task would clearly benefit from parallel research/work AND the overhead of asking permission would slow down obvious value delivery.

---

## Decision Matrix: When to Launch Agents Automatically

### ALWAYS Launch Agents (No Permission Needed)

| Trigger | Agent Type | SOPs |
|---------|------------|------|
| **New product/project idea mentioned** | Market Viability (4 agents) | SOP 17 |
| **"Should we build X?"** or **"Is X worth it?"** | Market Viability (4 agents) | SOP 17 |
| **Multiple valid implementation approaches** | Architecture Exploration (4 agents) | SOP 9 |
| **Complex feature with 5+ edge cases identified** | Multi-Agent Testing (4 agents) | SOP 2 |
| **Large refactor touching 4+ independent files** | Parallel Development (3-4 agents) | SOP 10 |
| **Research task spanning multiple domains** | Explore agents (2-4 parallel) | Task tool |

### ALWAYS Block (Pre-Commit Gate)

| Trigger | Action | SOPs |
|---------|--------|------|
| **New .py/.js/.ts files about to be committed** | BLOCK until Scenario 1 testing complete | testing-strategy.md |
| **Plan includes implementation phase without testing phase** | AUTO-ADD testing phase to plan | SOP 2/testing-strategy.md |
| **Code written but imports not verified** | RUN quick import test before commit | Operating Principle #9a |

**Incident that created this rule:** `docs/incidents/2026-02-08-untested-code-committed.md`

### ASK First (Permission Required)

| Situation | Why Ask |
|-----------|---------|
| Deploying to production | Irreversible |
| Spending money (API calls with cost) | Budget impact |
| Deleting/overwriting files | Data loss risk |
| Publishing to external services | Public visibility |
| Tasks with ambiguous scope | Might waste effort |

### NEVER Auto-Launch

| Situation | Why Not |
|-----------|---------|
| Simple single-file edits | Overkill |
| Quick lookups | Faster to do directly |
| User explicitly doing step-by-step | Respect their pace |
| Unclear requirements | Need clarification first |

---

## Specific Triggers → Agent Actions

### 1. Market Viability (SOP 17)

**Auto-trigger phrases:**
- "Should we build..."
- "Is there a market for..."
- "Would people pay for..."
- "I have an idea for..."
- "What about selling..."
- "Could we monetize..."

**Action:** Launch 4 parallel agents:
1. Agent 1: Market Size (TAM/SAM/SOM)
2. Agent 2: Competition Analysis
3. Agent 3: Customer Research
4. Agent 4: Monetization Models

**Output:** Consolidated viability scorecard with GO/NO-GO decision

---

### 2. Architecture Exploration (SOP 9)

**Auto-trigger phrases:**
- "How should we implement..."
- "What's the best way to..."
- "Should we use X or Y..."
- "Multiple ways to do this..."
- Any task with 3+ valid technical approaches

**Action:** Launch 3-4 parallel agents, each researching different approach:
- Agent 1: Approach A (e.g., Official API)
- Agent 2: Approach B (e.g., Web Scraping)
- Agent 3: Approach C (e.g., Third-Party Service)
- Agent 4: Approach D (e.g., Hybrid)

**Output:** Comparison matrix with recommendation

---

### 3. Multi-Agent Testing (SOP 2)

**Auto-trigger when ALL conditions met:**
- Complex feature just implemented
- Manual testing passed
- 5+ edge cases identified
- Feature has user-facing impact

**Action:** Launch 4 parallel testing agents with different focus areas

**Output:** Consolidated findings with Critical/Important/Nice-to-Have categorization

---

### 4. Parallel Development (SOP 10)

**Auto-trigger when:**
- Refactoring 4+ independent files
- Building system with 3+ decoupled components
- User mentions "in parallel" or "simultaneously"
- Clear component boundaries exist

**Action:** Launch agents to build different components in parallel

**Output:** Integrated codebase with all components merged

---

### 5. Research/Exploration

**Auto-trigger phrases:**
- "Find all..." / "Search for..."
- "What does the codebase do for..."
- "How does X work in the code..."
- "Where is Y implemented..."
- Open-ended questions about unfamiliar codebase

**Action:** Launch Explore agent(s) with appropriate thoroughness

**Output:** Findings with file references

---

### 6. Pre-Commit Testing Gate (NEW - 2026-02-08)

**Auto-trigger when:**
- New code files (`.py`, `.js`, `.ts`) are about to be committed
- A plan includes "implement X" phase without corresponding "test X" phase
- User says "commit this" or "push to GitHub" after code implementation

**Blocking Conditions:**
- ❌ No imports tested → BLOCK until `python -c "from module import X"` passes
- ❌ No manual run → BLOCK until basic functionality verified
- ❌ Plan missing test phase → AUTO-INSERT testing phase before commit phase

**Action:**
1. Check if new code files were created in current session
2. Verify at minimum imports work
3. If basic tests not run, STOP and ask user before commit

**Output:** Either "✅ Testing complete, safe to commit" or "⚠️ Testing required before commit"

**Reference:** See `CLAUDE.md` Operating Principle #9a, `docs/testing-strategy.md`

**Incident:** This trigger was added after TikTok modules were committed without testing (2026-02-08)

---

## Implementation: How Claude Should Behave

### When User Mentions New Idea

```
User: "I'm thinking about packaging our Claude.md system to sell"

Claude's internal decision:
1. Is this a product/business idea? YES
2. Does it require market validation? YES
3. Would SOP 17 apply? YES
4. Launch 4 market viability agents automatically

Claude's response:
"Great idea. Let me run a market viability analysis to see if this is worth pursuing.
Launching 4 parallel agents to research market size, competition, customer pain,
and monetization options. I'll consolidate findings into a GO/NO-GO recommendation."

[Launches agents without asking permission]
```

### When Multiple Approaches Exist

```
User: "We need to add authentication to the API"

Claude's internal decision:
1. Are there multiple valid approaches? YES (JWT, OAuth, Session, API Keys)
2. Is this a significant architectural decision? YES
3. Would SOP 9 apply? YES
4. Launch architecture exploration agents

Claude's response:
"Authentication has several valid approaches. Let me research the options in parallel
to find the best fit for your use case."

[Launches 3-4 agents researching different auth approaches]
```

### When Complex Testing Needed

```
User: "The payment integration is complete, let's test it"

Claude's internal decision:
1. Is this a complex feature? YES
2. Are there multiple edge cases? YES (invalid cards, timeouts, refunds, etc.)
3. Would parallel testing help? YES
4. Has manual testing been done? CHECK FIRST

Claude's response:
"Payment integration has many edge cases. After we verify the happy path manually,
I'll launch multi-agent testing to cover edge cases in parallel."

[Waits for manual test, then launches test agents]
```

---

## Agent Launch Template

When launching autonomous agents, use this format:

```
I'm launching [N] parallel agents to [purpose]:

| Agent | Focus | Expected Output |
|-------|-------|-----------------|
| 1 | [Area] | [Deliverable] |
| 2 | [Area] | [Deliverable] |
| 3 | [Area] | [Deliverable] |
| 4 | [Area] | [Deliverable] |

I'll consolidate findings into [final deliverable] when complete.
```

---

## Notification Protocol

### During Agent Execution

- Brief status updates if agents take >2 minutes
- Don't interrupt with every agent completion notification
- Consolidate results before presenting to user

### After All Agents Complete

- Present consolidated summary (not raw outputs)
- Highlight key findings and recommendations
- Include decision/next steps
- Reference detailed files for deep dive

---

## Exception Handling

### If User Says "Don't Run Agents"

Respect immediately. Note preference for session.

### If Agents Seem Stuck

- Check after 5 minutes
- Offer to proceed with partial results
- Don't wait indefinitely

### If Results Conflict

- Present both perspectives
- Recommend further investigation
- Don't hide disagreement

---

## Quick Reference Card

| User Says | Claude Does |
|-----------|-------------|
| "Should we build X?" | Launch SOP 17 (4 agents) |
| "How should we implement X?" | Launch SOP 9 (3-4 agents) |
| "Test this thoroughly" | Launch SOP 2 (4 agents) after manual pass |
| "Build these components" | Launch SOP 10 if 3+ independent pieces |
| "Research X in codebase" | Launch Explore agent |
| "Find all X" | Launch Explore agent |
| "In parallel" | Launch multiple agents as specified |
| "Commit this" (after new code) | **BLOCK** until testing complete (Principle #9a) |
| Plan has "implement" without "test" | **AUTO-ADD** testing phase to plan |

---

## Related SOPs

All SOPs are located in `CLAUDE.md`. Use Ctrl+F/Cmd+F to search.

| SOP | Name | When to Use | Agents |
|-----|------|-------------|--------|
| **SOP 2** | Multi-Agent Testing | After implementation, test edge cases | 4 testing agents |
| **SOP 9** | Architecture Exploration | Before coding, research approaches | 3-4 research agents |
| **SOP 10** | Parallel Development | During coding, build components | 3-4 build agents |
| **SOP 17** | Market Viability | Before committing, validate idea | 4 market research agents |

**Quick Navigation**:
- `CLAUDE.md` → Search "### SOP 2:" for Multi-Agent Testing
- `CLAUDE.md` → Search "### SOP 9:" for Architecture Exploration
- `CLAUDE.md` → Search "### SOP 10:" for Parallel Development
- `CLAUDE.md` → Search "### SOP 17:" for Market Viability

---

**Last Updated:** 2026-02-08 (Added Pre-Commit Testing Gate - Principle #9a)
