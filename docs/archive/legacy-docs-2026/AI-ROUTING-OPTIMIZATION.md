# AI Routing Optimization: Claude Code + Clawdbot + Ralph

*Created: 2026-01-28*
*Version: 1.0.0*

## Overview

This document defines intelligent routing between our three AI development agents, ensuring each task goes to the agent best suited to handle it - similar to how the fitness influencer AI routes image tasks to Grok and text tasks to Claude.

---

## The Three Agents

| Agent | Location | Availability | Strengths | Weaknesses |
|-------|----------|--------------|-----------|------------|
| **Claude Code** | Mac Local | When Mac awake | Interactive dev, complex debugging, deployment, real-time editing | Requires Mac to be on |
| **Clawdbot** | EC2 VPS (34.193.98.97) | 24/7 | Mobile access, quick research, PRD creation, orchestration | Limited file editing, no git push |
| **Ralph** | EC2 VPS (planned) | 24/7 | Autonomous multi-story execution, quality gates, overnight builds | Needs PRD, no real-time interaction |

---

## Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INCOMING TASK                                │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Is Mac available?         │
                    │  (awake, at computer)      │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │ YES               │                   │ NO
              ▼                   │                   ▼
    ┌─────────────────┐           │         ┌─────────────────┐
    │ Is it urgent or │           │         │ Is it a quick   │
    │ interactive?    │           │         │ task (<5 min)?  │
    └────────┬────────┘           │         └────────┬────────┘
             │                    │                  │
    ┌────────┴────────┐           │         ┌───────┴───────┐
    │YES              │NO         │         │YES            │NO
    ▼                 ▼           │         ▼               ▼
┌────────┐    ┌──────────────┐    │    ┌────────┐    ┌──────────┐
│CLAUDE  │    │Complexity    │    │    │CLAWDBOT│    │Complexity│
│CODE    │    │Score > 6?    │    │    │        │    │Score > 4?│
└────────┘    └──────┬───────┘    │    └────────┘    └────┬─────┘
                     │            │                       │
              ┌──────┴──────┐     │              ┌───────┴───────┐
              │YES          │NO   │              │YES            │NO
              ▼             ▼     │              ▼               ▼
         ┌────────┐   ┌────────┐  │         ┌────────┐     ┌────────┐
         │RALPH   │   │CLAUDE  │  │         │RALPH   │     │CLAWDBOT│
         │        │   │CODE    │  │         │(queue) │     │        │
         └────────┘   └────────┘  │         └────────┘     └────────┘
```

---

## Routing Rules by Task Type

### Route to CLAUDE CODE when:

| Task Type | Example | Why Claude Code |
|-----------|---------|-----------------|
| Interactive debugging | "This error keeps happening, help me fix it" | Real-time back-and-forth needed |
| Complex file editing | "Refactor this module" | Direct file system access |
| Git operations | "Commit and push these changes" | Git credentials on Mac |
| Deployment | "Deploy to PyPI" | Build tools, credentials |
| Live testing | "Run this and show me output" | Immediate feedback loop |
| Architecture decisions | "Should we use X or Y approach?" | Needs exploration + editing |
| Code review | "Review this PR" | Interactive discussion |
| Urgent fixes | "Production is broken!" | Immediate attention |

**Trigger phrases:**
- "help me debug..."
- "fix this error..."
- "deploy..."
- "push to..."
- "let's work on..."
- "show me..."
- "run and test..."

### Route to CLAWDBOT when:

| Task Type | Example | Why Clawdbot |
|-----------|---------|--------------|
| Quick research | "What's the best library for X?" | No file changes needed |
| Status checks | "What's running on EC2?" | Quick command execution |
| PRD creation | "Create a PRD for X feature" | Specialized skill |
| Mobile requests | Any Telegram/WhatsApp message | 24/7 availability |
| Scheduling | "Remind me to check X tomorrow" | Calendar integration |
| Email triage | "Summarize my unread emails" | Gmail access |
| Question answering | "How does our auth work?" | Documentation lookup |
| Task delegation | "Have Ralph build X overnight" | Orchestration role |

**Trigger phrases:**
- "research..."
- "what is..."
- "how does..."
- "create a PRD for..."
- "remind me..."
- "check my..."
- "schedule..."
- "tell Ralph to..."

### Route to RALPH when:

| Task Type | Example | Why Ralph |
|-----------|---------|-----------|
| Multi-story features | "Build a complete auth system" | Autonomous execution |
| Overnight builds | "Build this while I sleep" | 24/7, no interaction |
| Codebase optimization | "Refactor all duplicate code" | Systematic, methodical |
| Documentation generation | "Generate docs for all APIs" | Batch processing |
| Test creation | "Add tests for all modules" | Comprehensive coverage |
| Migration tasks | "Migrate from X to Y" | Multi-step, quality gates |

**Complexity Score Triggers (7+ = Ralph):**
- Multi-file changes (3+ files)
- New feature with tests
- Refactoring across modules
- Database schema changes
- API endpoint additions

---

## Complexity Scoring System

Score each factor 0-2, sum for total (0-10):

| Factor | 0 | 1 | 2 |
|--------|---|---|---|
| **Files affected** | 1 file | 2-3 files | 4+ files |
| **New code vs edits** | Minor edits | Mixed | Mostly new |
| **Tests required** | None | Some | Comprehensive |
| **Dependencies** | None | Internal | External/new |
| **Risk level** | Low | Medium | High |

**Routing by score:**
- **0-3**: Claude Code (quick task) or Clawdbot (if mobile/research)
- **4-6**: Claude Code (interactive) or Ralph (if user unavailable)
- **7-10**: Ralph (autonomous execution with PRD)

---

## Handoff Protocols

### Claude Code → Clawdbot
When Mac going to sleep or user stepping away:
```
1. Commit current work to git
2. Push to GitHub
3. Send Telegram message with status:
   "Pushed [branch]: [description]. Clawdbot has context."
4. Clawdbot can answer questions about the work
```

### Claude Code → Ralph
For complex features user wants built autonomously:
```
1. Create PRD with stories (use PRD skill)
2. Save to: /home/clawdbot/ralph/prd-{name}.json
3. Trigger Ralph: "Ralph: Build [name]"
4. Ralph executes, commits, pushes
5. Clawdbot notifies when complete
```

### Clawdbot → Claude Code
When task requires interactive development:
```
1. Clawdbot responds: "This needs Claude Code. Here's what to tell it:"
2. Provides context summary
3. User starts Claude Code session with context
```

### Clawdbot → Ralph
For autonomous tasks requested via mobile:
```
1. Clawdbot creates PRD
2. Saves to Ralph directory
3. Triggers Ralph execution
4. Monitors progress
5. Sends completion notification
```

### Ralph → Clawdbot
After completing PRD:
```
1. Ralph commits all work
2. Pushes to GitHub
3. Sends webhook to Clawdbot
4. Clawdbot notifies user via Telegram
```

### Ralph → Claude Code
If Ralph encounters blocker:
```
1. Ralph marks story as blocked
2. Logs issue to progress.txt
3. Clawdbot notifies user
4. User continues with Claude Code
```

---

## Mobile-First Workflow

The goal: Handle everything from phone when possible.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MOBILE REQUEST (Telegram)                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  CLAWDBOT ANALYZES        │
                    │  Task type, complexity    │
                    └─────────────┬─────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CAN DO NOW     │    │  NEEDS DEV      │    │  COMPLEX BUILD  │
│  (research,     │    │  (wait for Mac) │    │  (Ralph task)   │
│   quick tasks)  │    │                 │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
   Clawdbot does         Queue for later          Create PRD
   it immediately        Claude Code session      Trigger Ralph
         │                      │                      │
         ▼                      ▼                      ▼
   Reply with result     "Added to docket,       "Building overnight,
                         will notify when        ETA: 6 AM"
                         Mac is available"
```

---

## Example Routing Scenarios

### Scenario 1: "Add a logout button" (via Telegram, 11 PM)

**Analysis:**
- Files: 2-3 (component + handler)
- Complexity: 4/10
- User: Going to sleep
- Mac: Off

**Route:** RALPH
- Clawdbot creates mini-PRD
- Ralph implements overnight
- Morning notification with completed code

### Scenario 2: "Why is the API returning 500?" (via Telegram, 3 PM)

**Analysis:**
- Type: Debugging
- Urgency: High
- Interaction: Needed
- Mac: Available

**Route:** CLAUDE CODE
- Clawdbot responds: "This needs debugging. Start Claude Code."
- Provides context: "Error in [file], likely [hypothesis]"

### Scenario 3: "What's our Apollo API rate limit?"

**Analysis:**
- Type: Research/Question
- Files: None
- Time: <2 min

**Route:** CLAWDBOT
- Answers immediately from docs/memory
- No handoff needed

### Scenario 4: "Build complete user onboarding flow"

**Analysis:**
- Files: 10+
- Complexity: 9/10
- New feature: Yes
- Tests: Required

**Route:** RALPH (via Clawdbot PRD)
- Clawdbot creates comprehensive PRD
- 5+ stories with acceptance criteria
- Ralph executes over several hours
- Quality gates at each checkpoint

---

## Integration with Existing SOPs

| SOP | Primary Agent | Handoff Pattern |
|-----|---------------|-----------------|
| SOP 0 (Kickoff) | Claude Code | Creates PRD → Ralph can execute |
| SOP 2 (Testing) | Claude Code | Ralph can run test suites |
| SOP 9 (Exploration) | Multiple agents | Clawdbot for research, Claude Code for decisions |
| SOP 11-14 (MCP) | Claude Code | Deployment requires local tools |
| SOP 17 (Market Analysis) | Clawdbot | Research phase, then Claude Code for action |
| SOP 18-19 (SMS) | Clawdbot | Campaign monitoring 24/7 |

---

## Communication Patterns (Add to CLAUDE.md)

| User Says | Routes To | Action |
|-----------|-----------|--------|
| "Quick question..." | Clawdbot | Answer from memory/docs |
| "Build X while I sleep" | Ralph (via Clawdbot) | Create PRD, queue for Ralph |
| "Help me debug..." | Claude Code | Interactive session |
| "Deploy X" | Claude Code | Requires local credentials |
| "Research X" | Clawdbot | Web search, summarize |
| "Create PRD for..." | Clawdbot | PRD creation skill |
| "Ralph: Build..." | Ralph | Direct Ralph trigger |
| "Status?" | Clawdbot | Check all systems |

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Claude Code routing | ✅ Ready | Manual selection by user |
| Clawdbot task detection | ⚠️ Partial | Needs intent classification |
| Ralph trigger from Clawdbot | ❌ Not Ready | Requires Phase 2 (Amp CLI) |
| Webhook notifications | ❌ Not Ready | Requires Phase 3 |
| Automatic handoffs | ❌ Not Ready | Future enhancement |

---

## Next Steps

1. **Phase 1**: Fix Clawdbot memory so it remembers routing preferences
2. **Phase 2**: Install Ralph on EC2 so Clawdbot can trigger it
3. **Phase 3**: Deploy webhooks for completion notifications
4. **Phase 4**: Implement automatic handoff detection

---

## Metrics to Track

- Tasks routed correctly (user satisfaction)
- Time to completion by agent
- Handoff success rate
- Mobile vs desktop task distribution
- Ralph overnight completion rate

---

*This routing system enables true mobile-first development: ask from your phone, get results from the right agent.*
