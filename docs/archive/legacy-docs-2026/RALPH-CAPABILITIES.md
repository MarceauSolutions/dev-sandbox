# Ralph Autonomous Agent System - Capabilities Guide

*Last Updated: 2026-01-27*

## Overview

Ralph is an autonomous AI agent loop that executes user stories from a PRD (Product Requirements Document) until completion. It's designed for complex, multi-step development tasks with optional human checkpoints for validation.

## Core Architecture

```
User Request
    ↓
Decision Engine (analyze complexity)
    ↓
use_ralph? ──YES──→ Generate PRD → Launch Ralph Loop
    │
    NO
    ↓
Handle manually
```

## The Four Ralph Systems

| System | File | Purpose |
|--------|------|---------|
| **Decision Engine** | `ralph_decision_engine.py` | Analyzes requests, recommends Ralph usage |
| **Auto-Invoke** | `ralph_auto_invoke.py` | Generates PRDs, launches Ralph |
| **Docket System** | `docket.py` | Request queue with priorities & dependencies |
| **Meta-PRD Generator** | `ralph_meta_prd_generator.py` | Ralph improves itself |

## System Locations

```
/Users/williammarceaujr./dev-sandbox/
├── projects/shared/lead-scraper/src/
│   ├── ralph_decision_engine.py      ← Decision logic (359 lines)
│   ├── ralph_auto_invoke.py          ← Auto-launch (273 lines)
│   ├── ralph_meta_prd_generator.py   ← Self-improvement (408 lines)
│   └── docket.py                     ← Request queue (478 lines)
├── ralph/
│   ├── ralph.sh                      ← Main execution loop
│   ├── prompt.md                     ← Agent instructions
│   └── AGENTS.md                     ← Codebase knowledge
```

## Decision Engine

### How It Works

Calculates a **complexity score (0-10)** based on triggers:

**Use Ralph Triggers (positive scoring):**
| Trigger | Weight | Condition |
|---------|--------|-----------|
| File Count | 25% | 3+ files to create/modify |
| Task Count | 25% | 3+ discrete related tasks |
| Workflow Steps | 20% | 5+ sequential steps |
| Pattern Detection | 15% | Keywords: migration, refactor, template, system |
| Checkpoint Need | 10% | Keywords: complex, review, validate |
| Explicit Request | 5% | User says "use ralph" |

**Don't Use Ralph (negative scoring):**
| Trigger | Penalty | Condition |
|---------|---------|-----------|
| Single file edit | -0.5 | Fix typo, change line |
| Quick question | -0.5 | What is, how do I, explain |
| Time sensitive | -0.3 | Right now, immediately |
| Exploratory | -0.2 | Research, explore, investigate |

### Score Thresholds

| Score | Complexity | Recommendation | Est. Time | Stories |
|-------|------------|----------------|-----------|---------|
| 1-3 | Simple | ❌ No Ralph | 5-15 min | 1 |
| 4-6 | Medium | ⚠️ Maybe | 15-30 min | 2-3 |
| 7-10 | Complex | ✅ Yes | 30-90 min | 4-8 |
| 10-20 | Very Complex | ✅ Yes + Checkpoints | 90-180 min | 8-20 |

### Agent Type Selection

| Type | Keywords | Use For |
|------|----------|---------|
| `general` | feature, system, workflow | General development |
| `bash` | script, command, automation | CLI/bash tasks |
| `data` | database, migration, schema | Data engineering |
| `refactor` | refactor, optimize, clean up | Code refactoring |

### CLI Usage

```bash
# Analyze a request
python -m src.ralph_decision_engine analyze "Create HVAC campaign templates"

# Output to JSON file
python -m src.ralph_decision_engine analyze "request" --output decision.json
```

## Docket System (Request Queue)

### Request Schema

```json
{
  "request_id": "req_001",
  "description": "Create HVAC templates",
  "priority": "high",
  "status": "pending",
  "dependencies": ["req_000"],
  "ralph_decision": {
    "use_ralph": true,
    "estimated_stories": 5
  }
}
```

### Priority Levels

| Priority | Symbol | When | Order |
|----------|--------|------|-------|
| `urgent` | 🔥 | Blocking, customer critical | 1st |
| `high` | ⚡ | Important, soon | 2nd |
| `normal` | 📋 | Regular work | 3rd |
| `low` | 💤 | Nice to have | 4th |

### CLI Commands

```bash
# View all requests
python -m src.docket status

# Add new request
python -m src.docket add "Create HVAC templates" --priority high

# With dependencies
python -m src.docket add "Description" --depends-on req_001

# Get next recommended task
python -m src.docket next

# View optimized sequence
python -m src.docket sequence

# Mark complete
python -m src.docket complete req_001
```

## PRD Format

### Structure

```json
{
  "metadata": {
    "prd_name": "HVAC Campaign System",
    "objective": "Build automated template system",
    "total_stories": 6,
    "completed_stories": 0,
    "autonomous_mode": true,
    "checkpoint_stories": [3],
    "branchName": "feature/hvac-campaigns"
  },
  "stories": [
    {
      "story_id": "001",
      "title": "Set up database schema",
      "description": "Create schema for HVAC leads",
      "acceptance_criteria": [
        "Schema created",
        "Migration works",
        "Tests pass"
      ],
      "files_to_create": ["src/models/hvac_lead.py"],
      "files_to_modify": [],
      "passes": false,
      "dependencies": [],
      "checkpoint": false
    }
  ]
}
```

### Story Fields

| Field | Required | Description |
|-------|----------|-------------|
| `story_id` | Yes | Unique ID (001, 002...) |
| `title` | Yes | Human-readable title |
| `description` | Yes | What needs to be done |
| `acceptance_criteria` | Yes | Completion criteria |
| `files_to_create` | No | New files to create |
| `files_to_modify` | No | Existing files to edit |
| `passes` | Yes | Is story complete? |
| `dependencies` | No | Stories that must finish first |
| `checkpoint` | No | Pause for human review? |

## Ralph Execution Loop

### How It Works

```
1. Load PRD
2. Pick next uncompleted story
3. Fresh AI agent implements story
4. Run quality checks (tests, lint)
5. If pass → commit → mark passes: true
6. Log progress to progress.txt
7. Repeat until all stories done
```

### Fresh Context Design

Each iteration starts with a FRESH AI context. Memory persists through:
- Git history (previous commits)
- progress.txt (learnings)
- prd.json (story status)
- AGENTS.md (codebase patterns)

### progress.txt Format

```markdown
## Codebase Patterns
- Use IF NOT EXISTS for migrations
- Export types from models.py

## 2026-01-27 10:15 - Story 001
- Created HVAC lead schema
- Files: src/models/hvac_lead.py
- **Learnings:**
  - Field names must match template variables
  - Phone validation required before SMS
```

## Communication Patterns

| User Says | Claude Does |
|-----------|-------------|
| "Start Ralph for [project]" | Read prd.json, run ALL stories autonomously |
| "Start Ralph in manual mode" | Implement ONE story, wait for continue |
| "Continue Ralph" | Resume from checkpoint or next story |
| "Ralph status" | Show X/Y complete, next story |
| "Ralph, improve yourself" | Launch meta-PRD generator |

## Meta-System (Self-Improvement)

Ralph can analyze and improve its own code:

```bash
# Analyze a system
python -m src.ralph_meta_prd_generator analyze-system docket

# Generate improvement PRD
python -m src.ralph_meta_prd_generator improve docket "Add export"
```

### Safety Measures
- Requires explicit user approval
- Generates safety warnings
- Suggests backup before changes

## When to Use Ralph

### ✅ Use Ralph When

- Building new features with 3+ files
- Complex multi-step workflows
- System migrations or refactors
- Creating template/pattern-based code
- Tasks with clear acceptance criteria

### ❌ Don't Use Ralph When

- Single file edits
- Quick fixes (typo, one-liner)
- Research/exploration tasks
- Questions (what is, how do I)
- Time-sensitive emergencies

## Integration with Claude Code

| Scenario | Workflow |
|----------|----------|
| Simple request | Claude handles directly |
| Complex request | Decision engine → Ralph PRD → Autonomous execution |
| Mid-work interrupt | New request → Docket → Continue or switch |
| Self-improvement | Meta-PRD → User approval → Ralph executes |

## Autonomous Mode vs Manual Mode

### Autonomous Mode (default for ≤8 stories)
- Ralph runs all stories without interruption
- User reviews final result only

### Manual/Checkpoint Mode (for >8 stories)
- Stories grouped in batches of 3
- User reviews at each checkpoint
- Allows mid-course corrections

## Example Workflow

```
User: "Build complete HVAC campaign system with templates,
       personalization, and analytics"

Claude: [Decision Engine]
→ Score: 8.5 (complex)
→ Estimated: 6 stories, 30-90 min
→ "Use Ralph! Generating PRD..."

Ralph Execution:
1. Story 001: Database schema ✅
2. Story 002: Message templates ✅
3. Story 003: Personalization ✅ [CHECKPOINT]
   → User reviews, approves
4. Story 004: Campaign launcher ✅
5. Story 005: Analytics ✅
6. Story 006: Documentation ✅

Result: Full system built autonomously with one human checkpoint
```

## Related Documents

- [CLAWDBOT-CAPABILITIES.md](CLAWDBOT-CAPABILITIES.md) - Personal AI assistant
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md) - When/how to use Ralph
- CLAUDE.md - Communication patterns and triggers
