# agent_bridge_api.py Modularization Plan

## Trigger: 3+ incidents traced to bridge complexity in health_check.py logs

## What This Does
Break the 13,050-line monolith into focused modules.

## Why Wait
- It works now. Don't fix what isn't broken pre-revenue.
- Modularization is high-effort, low-immediate-value
- Only becomes critical when the complexity causes actual failures

## Modularization Plan
1. agent_bridge_router.py — Intent routing logic
2. agent_bridge_tasks.py — Task execution handlers
3. agent_bridge_memory.py — mem0 interaction
4. agent_bridge_tools.py — Tool resolution
5. agent_bridge_api.py — FastAPI wrapper (imports from above)

## Estimated Effort: 2-3 sessions (5-8 hours)
