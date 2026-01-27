# Unified Tool Orchestration System

*Created: 2026-01-27*

## Overview

This document defines the unified orchestration layer for William's three AI development tools:
- **Clawdbot** - Mobile AI assistant (Telegram/WhatsApp)
- **Claude Code** - Development environment (Terminal)
- **Ralph** - Autonomous development agent (PRD-based loops)

## The Tool Hierarchy

```
┌──────────────────────────────────────────────────────────────────┐
│                    UNIFIED ORCHESTRATION LAYER                    │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │              TASK ROUTING DECISION ENGINE               │    │
│   │                                                         │    │
│   │  Input: Any user request (mobile, terminal, or PRD)     │    │
│   │  Output: Route to optimal tool                          │    │
│   └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│   ┌────────────────┐ ┌─────────────┐ ┌────────────────┐         │
│   │   CLAWDBOT    │ │ CLAUDE CODE │ │     RALPH      │         │
│   │               │ │             │ │                │         │
│   │ • Mobile      │ │ • Terminal  │ │ • Autonomous   │         │
│   │ • Quick tasks │ │ • Dev work  │ │ • Multi-story  │         │
│   │ • Research    │ │ • File ops  │ │ • Checkpoints  │         │
│   │ • Scheduling  │ │ • Git       │ │ • Self-anneal  │         │
│   └───────┬───────┘ └──────┬──────┘ └───────┬────────┘         │
│           │                │                │                    │
│           └────────────────┼────────────────┘                   │
│                            ▼                                     │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                  SHARED STATE LAYER                     │    │
│   │                                                         │    │
│   │  • Docket (request queue with priorities)               │    │
│   │  • Project files (dev-sandbox)                          │    │
│   │  • Clawdbot contributions (synced outputs)              │    │
│   │  • PRDs and progress.txt (Ralph state)                  │    │
│   │  • Session history (learning log)                       │    │
│   └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

## Tool Capabilities Matrix

| Capability | Clawdbot | Claude Code | Ralph |
|------------|----------|-------------|-------|
| **Mobile access** | ✅ Primary | ❌ | ❌ |
| **File editing** | ❌ | ✅ Primary | ✅ Via loop |
| **Git operations** | ❌ | ✅ Primary | ✅ Automated |
| **Multi-file changes** | ❌ | ✅ | ✅ Primary |
| **Autonomous execution** | ❌ | Limited | ✅ Primary |
| **Research/web search** | ✅ | ✅ | ❌ |
| **Quick questions** | ✅ Primary | ✅ | ❌ |
| **Complex coding** | ❌ | ✅ Primary | ✅ |
| **Scheduling/reminders** | ✅ Primary | ❌ | ❌ |
| **Checkpointed work** | ❌ | ❌ | ✅ Primary |

## Task Routing Decision Tree

```
                          ┌─────────────────┐
                          │ NEW USER REQUEST │
                          └────────┬────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │ Where did request originate? │
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
    ┌─────────────┐         ┌─────────────┐        ┌─────────────┐
    │ Mobile      │         │ Terminal    │        │ PRD/Docket  │
    │ (Telegram/  │         │ (Claude     │        │ (Scheduled) │
    │  WhatsApp)  │         │  Code)      │        │             │
    └──────┬──────┘         └──────┬──────┘        └──────┬──────┘
           │                       │                      │
           ▼                       ▼                      ▼
    ┌─────────────┐         ┌─────────────┐        ┌─────────────┐
    │ Clawdbot    │         │ Claude Code │        │ Ralph       │
    │ handles     │         │ handles     │        │ handles     │
    │ directly    │         │ directly    │        │ directly    │
    └──────┬──────┘         └──────┬──────┘        └─────────────┘
           │                       │
           ▼                       ▼
    ┌─────────────────────────────────────────────┐
    │         Is this a DEVELOPMENT task?          │
    └─────────────────────────────────────────────┘
           │                       │
           NO                      YES
           │                       │
           ▼                       ▼
    ┌─────────────┐         ┌─────────────────────┐
    │ Clawdbot    │         │ Run Decision Engine │
    │ completes   │         │ (SOP 28)            │
    │ task        │         └──────────┬──────────┘
    └─────────────┘                    │
                              ┌────────┴────────┐
                              │                 │
                           Score < 7         Score ≥ 7
                              │                 │
                              ▼                 ▼
                       ┌─────────────┐   ┌─────────────┐
                       │ Claude Code │   │ Ralph       │
                       │ direct      │   │ (generate   │
                       │ execution   │   │  PRD, run)  │
                       └─────────────┘   └─────────────┘
```

## Handoff Protocols

### Protocol 1: Clawdbot → Claude Code

**When**: Clawdbot receives development request

```
1. USER → Clawdbot: "Build a fitness tracker dashboard"

2. CLAWDBOT:
   a. Recognize as development task
   b. Create PRD outline (if complex)
   c. Save to ~/output/req-XXX/
   d. Notify: "This needs Claude Code. I've created an outline."

3. SYNC (manual or automated):
   ./scripts/sync-clawdbot-outputs.sh

4. CLAUDE CODE:
   a. Receives notification
   b. Pulls PRD outline
   c. Runs decision engine
   d. Routes to self or Ralph
```

### Protocol 2: Claude Code → Ralph

**When**: Claude Code detects complex multi-file task

```
1. USER → Claude Code: "Refactor the authentication system"

2. CLAUDE CODE:
   a. Run decision engine
   b. Score: 8.5 (complex)
   c. Generate PRD with 6 stories
   d. Ask: "Use Ralph for this?"

3. USER: "Yes"

4. RALPH:
   a. Load PRD
   b. Execute stories autonomously
   c. Checkpoint at story 3 (optional)
   d. Complete and report
```

### Protocol 3: Claude Code → Clawdbot

**When**: Need to notify/communicate while coding

```
1. CLAUDE CODE: Completes feature

2. USER → Claude Code: "Tell John the feature is ready"

3. CLAUDE CODE:
   a. Draft message
   b. Route to Clawdbot for delivery
   c. (Future: Direct API integration)
```

### Protocol 4: Parallel Tool Usage

**When**: Multiple independent tasks

```
┌─────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION                        │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ CLAWDBOT         │  │ RALPH            │                 │
│  │ • Research       │  │ • Story 1: DB    │                 │
│  │   competitor     │  │ • Story 2: API   │                 │
│  │   pricing        │  │ • Story 3: UI    │                 │
│  │                  │  │                  │                 │
│  │ (runs async)     │  │ (runs async)     │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│           └──────────┬──────────┘                           │
│                      ▼                                       │
│           ┌──────────────────┐                              │
│           │ MERGE RESULTS    │                              │
│           │ • Clawdbot       │                              │
│           │   research →     │                              │
│           │   Claude Code    │                              │
│           │ • Ralph stories  │                              │
│           │   → Review       │                              │
│           └──────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## Shared State Management

### The Docket (Request Queue)

Central queue for all tools to read/write:

```
/Users/williammarceaujr./dev-sandbox/
├── .tmp/
│   ├── clawdbot-inbox/          # Clawdbot outputs
│   │   └── req-001/
│   ├── clawdbot-notifications/  # Action routing
│   └── docket.json              # Unified request queue
```

### docket.json Schema

```json
{
  "requests": [
    {
      "id": "req-001",
      "source": "clawdbot",
      "channel": "telegram",
      "timestamp": "2026-01-27T10:30:00Z",
      "description": "Build fitness tracker dashboard",
      "status": "pending",
      "priority": "high",
      "routed_to": "ralph",
      "prd_path": ".tmp/clawdbot-inbox/req-001/prd-outline.json",
      "dependencies": [],
      "notes": "Clawdbot created initial outline"
    },
    {
      "id": "req-002",
      "source": "claude_code",
      "timestamp": "2026-01-27T11:00:00Z",
      "description": "Fix authentication bug",
      "status": "in_progress",
      "priority": "urgent",
      "routed_to": "claude_code",
      "dependencies": []
    }
  ],
  "metadata": {
    "last_updated": "2026-01-27T11:00:00Z",
    "total_requests": 2,
    "pending": 1,
    "in_progress": 1,
    "completed": 0
  }
}
```

## Communication Patterns

### Orchestration Commands

| Command | Action |
|---------|--------|
| "Show docket" | Display unified request queue |
| "Route [request] to Ralph" | Move request from pending to Ralph |
| "Sync Clawdbot" | Pull latest Clawdbot outputs |
| "Check tool status" | Show status of all tools |
| "Parallel: [task1] and [task2]" | Run tasks on different tools simultaneously |

### Status Check

```
📊 Tool Orchestration Status
============================

🤖 Clawdbot (VPS 44.193.244.59)
   Status: ✅ Online
   Channel: Telegram active
   Pending outputs: 2

💻 Claude Code (Local)
   Status: ✅ Active (this session)
   Current task: Unified orchestration docs

🔄 Ralph
   Status: ⏸️ Idle
   Last run: 2026-01-26 (MCP publishing)
   PRDs available: 3

📥 Docket
   Pending: 3
   In Progress: 1
   Blocked: 0
```

## Best Practices

### Do

- ✅ Let decision engine route complex tasks
- ✅ Use Clawdbot for research while Ralph builds
- ✅ Check docket before starting new work
- ✅ Sync Clawdbot outputs daily

### Don't

- ❌ Manually route tasks without checking decision engine
- ❌ Run Ralph and Claude Code on same files simultaneously
- ❌ Ignore Clawdbot notifications
- ❌ Skip handoff protocols

## Integration Checklist

- [x] Clawdbot VPS running with OAuth
- [x] Sync script for Clawdbot outputs
- [x] Action router for notifications
- [x] Ralph decision engine
- [x] Ralph auto-invoke system
- [x] Docket system
- [x] SOP 27: Clawdbot usage
- [x] SOP 28: Ralph usage
- [ ] Unified docket CLI (pending)
- [ ] Real-time webhook integration (pending)
- [ ] Cross-tool status dashboard (pending)

## Future Enhancements

1. **Unified CLI**: Single command to interact with all tools
2. **Auto-sync daemon**: Continuous Clawdbot output monitoring
3. **Cross-tool analytics**: Track productivity across tools
4. **Smart routing**: ML-based task routing optimization
5. **Voice interface**: Speak to orchestration layer

## Related Documents

- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md)
- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md)
- [CLAWDBOT-PROJECT-INTEGRATION.md](CLAWDBOT-PROJECT-INTEGRATION.md)
- [CLAWDBOT-MONITORING-SYSTEM.md](CLAWDBOT-MONITORING-SYSTEM.md)
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md)
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md)
