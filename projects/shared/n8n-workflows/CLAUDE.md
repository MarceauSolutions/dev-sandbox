# n8n Workflow Archives

**Status**: Reference / Archive | **Type**: n8n workflow JSON storage

## What It Does
Stores exported n8n workflow JSON files and planning docs for the Agent Orchestrator (agent_bridge_api.py) consolidation project. Historical versions and future consolidation plans.

## Key Files
| File | What |
|------|------|
| `CONSOLIDATION-PLAN.md` | v4→v5 consolidation plan (196→~170 nodes, 85→~55 endpoints) |
| `X-IMAGE-GENERATION-PIPELINE.md` | X/Twitter image generation pipeline design |
| `agent-orchestrator-v3*.json` | Historical workflow snapshots (v35-v39) |
| `agent-orchestrator-story8-*.json` | Story-8 checkpoint/current snapshots |
| `agent-orchestrator-minimal.json` | Minimal version for testing |

## Context
The `agent_bridge_api.py` on EC2 is the live Python Bridge (13,050 lines). These JSONs are n8n workflow exports, NOT the Python bridge itself.

Live n8n workflows: http://34.193.98.97:5678

## Related
- Python Bridge: `execution/agent_bridge_api.py` (EC2 localhost:5010)
- Consolidation SOP: See `CONSOLIDATION-PLAN.md` in this directory
- n8n health: `python scripts/health_check.py`
