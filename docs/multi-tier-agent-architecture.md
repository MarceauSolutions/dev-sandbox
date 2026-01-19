# Multi-Tier Agent Architecture

A framework for deploying manager agents that coordinate their own subagents, enabling complex parallel workflows with hierarchical oversight.

## When to Use This Architecture

### Use Multi-Tier Agents When:
- Task has 6+ independent components (exceeds single-tier capacity)
- Components have natural groupings (e.g., frontend vs backend vs testing)
- Need domain-specific expertise at different levels
- Want to avoid context overflow in a single coordinator
- Complex dependencies require intelligent routing

### Stick to Single-Tier When:
- 4 or fewer independent tasks
- Tasks are similar in nature (all research, all testing)
- Single coordinator can handle context
- Simpler is better for the use case

---

## Architecture Patterns

### Pattern 1: Coordinator → Parallel Managers → Parallel Workers

```
                    ┌─────────────────┐
                    │   COORDINATOR   │
                    │  (Main Claude)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ MANAGER 1     │   │ MANAGER 2     │   │ MANAGER 3     │
│ (Research)    │   │ (Development) │   │ (Testing)     │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
   ┌────┼────┐         ┌────┼────┐         ┌────┼────┐
   ▼    ▼    ▼         ▼    ▼    ▼         ▼    ▼    ▼
┌───┐ ┌───┐ ┌───┐   ┌───┐ ┌───┐ ┌───┐   ┌───┐ ┌───┐ ┌───┐
│W1 │ │W2 │ │W3 │   │W4 │ │W5 │ │W6 │   │W7 │ │W8 │ │W9 │
└───┘ └───┘ └───┘   └───┘ └───┘ └───┘   └───┘ └───┘ └───┘
```

**Use Case**: Large product development
- Manager 1: Market research agents
- Manager 2: Implementation agents (frontend, backend, API)
- Manager 3: Testing agents (unit, integration, edge cases)

### Pattern 2: Sequential Managers with Handoffs

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MANAGER 1     │────▶│   MANAGER 2     │────▶│   MANAGER 3     │
│ (Research)      │     │ (Design)        │     │ (Implementation)│
└───────┬─────────┘     └───────┬─────────┘     └───────┬─────────┘
        │                       │                       │
   ┌────┴────┐             ┌────┴────┐             ┌────┴────┐
   ▼         ▼             ▼         ▼             ▼         ▼
┌─────┐   ┌─────┐       ┌─────┐   ┌─────┐       ┌─────┐   ┌─────┐
│ W1  │   │ W2  │       │ W3  │   │ W4  │       │ W5  │   │ W6  │
└─────┘   └─────┘       └─────┘   └─────┘       └─────┘   └─────┘
```

**Use Case**: Phased projects where each stage depends on previous
- Manager 1 output becomes Manager 2 input
- Clear handoff points with consolidated deliverables

### Pattern 3: Specialized Managers with Shared Workers

```
                    ┌─────────────────┐
                    │   COORDINATOR   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ DOMAIN MGR 1  │   │ DOMAIN MGR 2  │   │ DOMAIN MGR 3  │
│ (AI/ML)       │   │ (Frontend)    │   │ (DevOps)      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌───────────────┐
                    │  SHARED POOL  │
                    │  (Workers)    │
                    └───────────────┘
```

**Use Case**: Cross-functional work requiring different expertise
- Each manager has domain expertise
- Workers are generalists that can be assigned by any manager

---

## Implementation

### Step 1: Coordinator Setup

The main Claude session acts as coordinator:

```markdown
## Coordinator Responsibilities
1. Decompose task into manager-level chunks
2. Launch manager agents in parallel
3. Monitor manager progress (via TaskOutput)
4. Consolidate manager outputs
5. Handle inter-manager dependencies
```

### Step 2: Manager Agent Prompts

```
==================================================
MANAGER AGENT: [DOMAIN]
==================================================

I am a MANAGER agent responsible for [DOMAIN] of [PROJECT].

MY ROLE: Coordinate [NUMBER] worker subagents to complete [DOMAIN] tasks.

MY SCOPE:
- [Task area 1]
- [Task area 2]
- [Task area 3]

SUBAGENT STRATEGY:
I will launch [N] parallel workers:
- Worker 1: [Specific task]
- Worker 2: [Specific task]
- Worker 3: [Specific task]

DELIVERABLE: Consolidated [DOMAIN] output with:
- Summary of findings from all workers
- Synthesized recommendations
- Any conflicts or inconsistencies noted
- Dependencies on other managers

COMMUNICATION:
- I will use the Task tool to launch my workers
- I will consolidate their outputs before reporting
- I will flag any blockers that require coordinator intervention
```

### Step 3: Worker Agent Prompts

```
==================================================
WORKER AGENT: [SPECIFIC TASK]
==================================================

I am a WORKER agent under [MANAGER NAME].

MY TASK: [Specific, narrow task]

MY WORKSPACE: [Absolute path]

DELIVERABLE: [Specific output format]

SCOPE LIMIT: I will ONLY focus on [specific task].
I will NOT attempt to solve problems outside my scope.

OUTPUT FORMAT:
- FINDINGS.md in my workspace
- Clear success/failure status
- Any blockers or questions for my manager
```

### Step 4: Launching Managers

From the coordinator (main Claude session):

```python
# Conceptual - actual implementation uses Task tool

# Launch all managers in parallel
manager_prompts = [
    ("research-manager", research_manager_prompt),
    ("dev-manager", dev_manager_prompt),
    ("test-manager", test_manager_prompt),
]

# Single message with multiple Task tool calls
for name, prompt in manager_prompts:
    Task(
        description=f"{name}",
        prompt=prompt,
        subagent_type="general-purpose",
        run_in_background=True
    )
```

### Step 5: Monitoring Progress

```bash
# Check manager status
TaskOutput(task_id="manager-1-id", block=False)
TaskOutput(task_id="manager-2-id", block=False)
TaskOutput(task_id="manager-3-id", block=False)
```

---

## When to Launch Multi-Tier Agents Automatically

Add to autonomous agent triggers (see `autonomous-agent-decision-tree.md`):

| Trigger | Action |
|---------|--------|
| Task has 8+ independent components | Auto-launch 2-3 manager agents |
| Distinct domain expertise needed | Create domain-specific managers |
| Context limit concern (>50K tokens expected) | Split into manager tiers |
| User says "run agents in parallel for X, Y, Z" where X, Y, Z are large | Multi-tier approach |

---

## Example: Full Product Development

### Scenario
Building a new mobile app with research, development, and testing phases.

### Coordinator Decomposition

```
PROJECT: CraveSmart Mobile App

MANAGER 1: Market Research Manager
├── Worker 1: Market size research
├── Worker 2: Competition analysis
├── Worker 3: Customer research
└── Worker 4: Monetization research

MANAGER 2: Development Manager
├── Worker 1: iOS app structure
├── Worker 2: Backend API
├── Worker 3: Apple Health integration
└── Worker 4: Clue/Terra integration

MANAGER 3: Testing Manager
├── Worker 1: Unit test coverage
├── Worker 2: Integration testing
├── Worker 3: Edge case testing
└── Worker 4: Performance testing
```

### Manager 1 Prompt (Research)

```
I am the MARKET RESEARCH MANAGER for CraveSmart.

MY MISSION: Coordinate 4 research workers to validate market viability.

WORKERS I WILL LAUNCH:
1. Market Size Worker - TAM/SAM/SOM analysis
2. Competition Worker - Competitive landscape
3. Customer Worker - Target persona and pain points
4. Monetization Worker - Pricing and unit economics

DELIVERABLE: Consolidated market viability report with:
- GO/NO-GO recommendation
- Scores from all 4 workers
- Key findings synthesis
- Risks and opportunities

I will launch all 4 workers in parallel, wait for completion,
then synthesize into a single report for the coordinator.
```

---

## Permission Handling for Background Agents

**Known Issue**: Background agents launched via Task tool may have WebSearch and other permissions auto-denied.

### Mitigation Strategies

1. **Pre-research in foreground**: Do critical web searches in coordinator before launching agents
2. **Provide context**: Include relevant search results in agent prompts
3. **Allow fallback**: Agents can use training data with acknowledgment
4. **Post-validation**: Coordinator validates findings with live searches after agents complete

### Permission Flow

```
Coordinator (foreground)
├── Has: WebSearch, all permissions
├── Action: Do critical searches FIRST
└── Pass findings to managers in prompts

Manager (background)
├── Has: Limited permissions (no WebSearch)
├── Action: Use provided context + training data
└── Flag: "Could not verify X with live search"

Worker (background via manager)
├── Has: Limited permissions
├── Action: Focus on specific task with given context
└── Flag: Any verification needs
```

---

## Best Practices

### DO:
- Launch managers in parallel when independent
- Give each manager clear scope boundaries
- Include absolute paths in all prompts
- Have managers consolidate before reporting to coordinator
- Validate critical findings with live searches post-completion

### DON'T:
- Create more than 3 tiers (coordinator → manager → worker)
- Give workers overlapping responsibilities
- Skip the consolidation step
- Assume background agents have full permissions
- Launch workers directly from coordinator (use managers)

---

## Integration with Existing SOPs

| SOP | Multi-Tier Integration |
|-----|------------------------|
| SOP 2: Multi-Agent Testing | Testing Manager coordinates edge case workers |
| SOP 9: Architecture Exploration | Research Manager coordinates approach workers |
| SOP 10: Parallel Development | Development Manager coordinates component workers |
| SOP 17: Market Viability | Research Manager coordinates 4 research workers |

---

## Communication Patterns

| William Says | Claude Does |
|--------------|-------------|
| "Run this with manager agents" | Create coordinator → manager → worker hierarchy |
| "Break this into managed teams" | Identify domain boundaries, create managers |
| "Coordinate multiple agent groups" | Multi-tier architecture with consolidation |
| "Run X, Y, Z in parallel with subagents" | 3 managers, each with relevant workers |

---

*Document Version: 1.0.0*
*Created: January 18, 2026*
