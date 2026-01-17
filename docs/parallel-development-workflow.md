# Parallel Development Workflow

*Created: 2026-01-16*

This document captures the pattern for using parallel sub-agents to accelerate development while maintaining focus on execution.

---

## The Pattern: Execute + Research in Parallel

When facing multiple priorities, use this approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN AGENT (You)                         │
│                                                             │
│  PRIMARY TASK: Execute highest-priority actionable work     │
│  Example: Schedule X posts, write code, deploy              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Agent B    │  │   Agent C    │  │   Agent D    │      │
│  │  (Research)  │  │  (Research)  │  │  (Research)  │      │
│  │              │  │              │  │              │      │
│  │ Background   │  │ Background   │  │ Background   │      │
│  │ task running │  │ task running │  │ task running │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Sub-agents research secondary priorities while main        │
│  agent executes the top priority task.                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## When to Use This Pattern

**Use parallel agents when:**
- You have 3+ priorities and limited time
- Secondary tasks are research/planning (not execution)
- Tasks don't have dependencies on each other
- You want to maximize progress per session

**Don't use when:**
- Tasks are tightly coupled (results needed immediately)
- All tasks require user decisions before proceeding
- Single task is urgent and needs full attention

---

## Implementation Steps

### 1. Identify and Prioritize Tasks

```
Priority Assessment:
- P0 (Execute Now): Immediate, actionable, highest value
- P1 (Research): Can be delegated to sub-agent
- P2 (Research): Can be delegated to sub-agent
```

### 2. Launch Sub-Agents for Research Tasks

```python
# Launch agents in background with clear missions
Task(
    description="Agent B: [Short description]",
    prompt="[Detailed research instructions]",
    subagent_type="Explore",  # For research tasks
    run_in_background=True
)
```

**Key elements of a good agent prompt:**
- Clear mission statement
- Specific files/URLs to examine
- Explicit deliverables (save to specific path)
- "RESEARCH ONLY" constraint if not executing

### 3. Execute Primary Task

While agents research in background:
- Focus fully on P0 execution task
- Check agent progress periodically with `tail -20 /tmp/claude/.../tasks/[id].output`
- Don't wait for agents unless you need their output

### 4. Consolidate Results

When agents complete:
- Read their output files
- Integrate findings into your work
- Update DOCKET with new information
- Proceed to next execution phase

---

## Example: Today's Session (2026-01-16)

**Situation:** Three priorities identified:
- A: Schedule X posts (executable, P0)
- B: OpenRouter registration (research needed, P1)
- C: Fitness pricing implementation (research needed, P1)

**Approach:**
```
Main Agent → Execute Option A (X posts)
    └── Agent B → Research OpenRouter directories (background)
    └── Agent C → Research pricing implementation (background)
```

**Commands Used:**
```bash
# Launch Agent B
Task(description="Agent B: OpenRouter Registration",
     prompt="Research directories...",
     subagent_type="Explore",
     run_in_background=True)

# Launch Agent C
Task(description="Agent C: Fitness Pricing Research",
     prompt="Research pricing implementation...",
     subagent_type="Explore",
     run_in_background=True)
```

**Output Files:**
- Agent B: `/tmp/claude/.../tasks/[id].output`
- Agent C: `/tmp/claude/.../tasks/[id].output`

**Deliverables (saved by agents):**
- `workflows/openrouter-registration-plan.md`
- `workflows/pricing-implementation-plan.md`

---

## Agent Prompt Template

```markdown
You are Agent [X] researching [TOPIC].

**Context:** [Brief background on why this matters]

**Your Mission:** [One sentence objective]

**Research Tasks:**
1. [Specific task 1]
2. [Specific task 2]
3. [Specific task 3]

**Deliverables:**
Save your findings to: [EXACT FILE PATH]

Include:
1. [Section 1]
2. [Section 2]
3. [Section 3]

This is RESEARCH ONLY - do not [implement/submit/execute] anything.
```

---

## Checking Agent Progress

```bash
# See recent output from an agent
tail -30 /tmp/claude/-Users-williammarceaujr--dev-sandbox/tasks/[agent_id].output

# Check if agent completed
cat /tmp/claude/-Users-williammarceaujr--dev-sandbox/tasks/[agent_id].output | grep -i "complete\|done\|finished"
```

---

## Benefits of This Pattern

1. **Maximizes throughput** - Research happens while you execute
2. **Reduces context switching** - Main agent stays focused
3. **Prepares next steps** - When P0 done, P1/P2 research is ready
4. **Documents decisions** - Agents save findings to workflows/

---

## Integration with Existing SOPs

This pattern complements:
- **SOP 2 (Multi-Agent Testing)** - Similar parallel structure, different purpose
- **SOP 9 (Architecture Exploration)** - Research phase before implementation
- **SOP 10 (Parallel Development)** - Building components simultaneously

**Key difference:** This pattern is for mixed execute+research, not pure research or pure development.

---

## References

- [CLAUDE.md](../CLAUDE.md) - Main operating instructions
- [SOP 10: Multi-Agent Parallel Development](../CLAUDE.md#sop-10-multi-agent-parallel-development)
- [DOCKET.md](../projects/social-media-automation/DOCKET.md) - Priority tracking
