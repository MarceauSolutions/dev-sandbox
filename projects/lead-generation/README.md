# Lead Generation Tower

Lead scraping, CRM management, SMS campaigns, outreach sequences, and sales pipeline tracking.

## Domain
- **ClickUp CRM**: List, create, update tasks
- **Sales Pipeline**: Deal tracking, outreach logging, trial metrics, follow-up management
- **Lead Scraping**: Apollo, Google Places, Sunbiz, Yelp, LinkedIn
- **SMS Campaigns**: Twilio outreach, inbox monitoring, opt-out management
- **Follow-up Sequences**: Automated nurture scheduling and campaign analytics

## Architecture
- Pure logic modules: `src/clickup_api.py`, `src/pipeline_api.py`
- Flask app with blueprints: `src/app.py` (port 5012)
- Pipeline DB shared utility: `execution/pipeline_db.py` (used by Clawdbot + Claude Code)
- No direct imports from other towers

## Endpoints (extracted from monolith)

| Route | Method | Description |
|-------|--------|-------------|
| `/clickup/list-tasks` | POST | List ClickUp tasks |
| `/clickup/create-task` | POST | Create ClickUp task |
| `/clickup/update-task` | POST | Update ClickUp task |
| `/pipeline/stats` | GET | Pipeline stats by tower |
| `/pipeline/deals` | GET | List deals (filter by tower/stage) |
| `/pipeline/deal/add` | POST | Create new deal |
| `/pipeline/deal/update` | POST | Update deal fields |
| `/pipeline/outreach/log` | POST | Log outreach attempt |
| `/pipeline/trial/log` | POST | Log trial day metrics |
| `/pipeline/trial/summary` | GET | Aggregated trial metrics |
| `/pipeline/followups` | GET | Due follow-ups |
| `/health` | GET | Tower health check |

## Running
```bash
python -m projects.lead_generation.src.app
# Or directly:
cd projects/lead-generation && python -c "from src.app import create_app; create_app().run(port=5012)"
```

## Version
1.1.0 — ClickUp CRM + Sales Pipeline extracted from monolithic agent_bridge_api.py
