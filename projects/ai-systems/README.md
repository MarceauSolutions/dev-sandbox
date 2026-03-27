# AI Systems Tower

Core AI infrastructure: orchestration, learning, personas, goals, knowledge bases, and agent intelligence.

## Architecture

7 Flask blueprint modules, 95 routes total:

| Module | Routes | Endpoints | Domain |
|--------|--------|-----------|--------|
| `cost_tracking.py` | 5 | `/cost/*` | Token cost tracking, budgets, pricing |
| `memory.py` | 5 | `/memory/*` | Conversation memory, summaries |
| `orchestration.py` | 12 | `/templates/*`, `/orchestration/*`, `/scheduler/*` | Agent templates, multi-agent coordination, scheduling |
| `knowledge.py` | 5 | `/kb/*` | Knowledge bases, RAG, semantic search |
| `plugins.py` | 7 | `/plugins/*` | Tool plugins (Python, HTTP, MCP) |
| `intelligence.py` | 45 | `/learning/*`, `/recording/*`, `/context/*`, `/agents/*`, `/personas/*`, `/goals/*`, `/macros/*`, `/audit/*` | Learning, workflow recording, context injection, inter-agent comms, personas, goals, macros, audit |
| `media.py` | 16 | `/behavior/*`, `/media/*`, `/error/*`, `/notify/*`, `/agent/*` | Adaptive behavior, media generation, error analysis, notifications |

## Key Files
- `models.py` — 20+ data model classes (SessionCost, AgentPersona, Goal, etc.)
- `app.py` — Flask entry point with blueprint registration (port 5013)
- No imports from monolith — fully independent

## Running
```bash
python -m projects.ai_systems.src.app
```

## Version
1.2.0 — Refactored from raw extraction into 7 modular Flask blueprints
