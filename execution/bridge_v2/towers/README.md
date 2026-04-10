# Tower-Specific Blueprints

Add tower-specific API endpoints here when a consumer needs them.
Each tower gets its own Blueprint file.

## Available to extract from agent_bridge_api.py (archived):

| Endpoint Group | Routes | Source Lines | Add When |
|---|---|---|---|
| **session/** | save, load, list, delete | ~4741-4926 | When n8n or Panacea needs session persistence |
| **task/** | create, update, status, result, list | ~4927-5116 | When background task management is needed |
| **todo/** | list, add, update, delete, clear | ~4580-4710 | When todo tracking via API is needed |
| **memory/** | add, get, summarize, list, clear | ~5636-5745 | When Panacea needs memory via bridge (currently uses Grok layer) |
| **cost/** | track, session, all, budget, pricing | ~5540-5635 | When API cost tracking is needed |

## How to add:
1. Create `towers/<tower_name>.py` with a Flask Blueprint
2. Register it in `app.py` via `create_app()`
3. Extract the endpoint code from `docs/archive/agent_bridge_api.py`
