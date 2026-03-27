# Lead Generation Tower Directive

## Domain
Lead scraping, scoring, outreach campaigns, follow-up sequences, SMS/email automation, pipeline management, and client acquisition.

## Core Capabilities
- **Daily Acquisition Loop** (`daily_loop.py`): 8-stage autonomous pipeline — discover, score, enrich, outreach, monitor, classify, follow-up, report
- **Hot Lead Handler** (`hot_lead_handler.py`): SMS alert → William reply (1/2/3) → Calendly handoff
- **Pipeline API** (`pipeline_api.py`): Deal CRUD, outreach logging, trial metrics, follow-ups
- **ClickUp CRM** (`clickup_api.py`): Task management integration
- **Lead Scraping**: Apollo, Google Places, Sunbiz, Yelp
- **SMS Campaigns**: Twilio outreach, opt-out management, TCPA compliance
- **Follow-Up Sequences**: 3-touch email sequences with auto-stop
- **Campaign Analytics**: Template A/B testing, response tracking
- **Self-Monitoring**: Consecutive failure alerts via Telegram

## Entry Point
- Flask app: `src/app.py` (port 5012)
- 4 launchd jobs: daily loop (9am), response check (15min), digest (5:30pm)

## Integration Points
- **pipeline.db** (shared): Canonical deal/outreach/trial data — written by lead-gen, read by personal-assistant and fitness-influencer
- **personal-assistant**: Morning digest reads pipeline data. Calendly handoff sends emails via PA's gmail_api.
- **execution/pipeline_db.py**: Shared DB access module

## Current Version
1.1.0
