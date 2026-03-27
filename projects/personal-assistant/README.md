# Personal Assistant Tower

Personal automation: Gmail, Google Sheets, Twilio SMS, calendar scheduling, and routine optimization.

## Domain
- **Gmail**: List, read, send, draft, search (single + multi-account)
- **Google Sheets**: Read, write, append
- **Twilio SMS**: Send, list (inbound/outbound)
- **Calendar**: Reminders, Calendly booking monitoring
- **Email Monitoring**: Gmail reply watcher, API monitor

## Architecture
- Pure logic modules: `src/gmail_api.py`, `src/sheets_api.py`, `src/sms_api.py`
- Flask app with blueprints: `src/app.py` (port 5011)
- No direct imports from other towers — uses standardized API interfaces

## Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/gmail/list` | POST | List inbox emails |
| `/gmail/read` | POST | Read specific email by ID |
| `/gmail/send` | POST | Send email via SMTP |
| `/gmail/draft` | POST | Create Gmail draft |
| `/gmail/search` | POST | Search single account |
| `/gmail/search-all` | POST | Search all Gmail accounts |
| `/sheets/read` | POST | Read sheet data |
| `/sheets/write` | POST | Write to sheet |
| `/sheets/append` | POST | Append rows to sheet |
| `/sms/send` | POST | Send SMS via Twilio |
| `/sms/list` | POST | List SMS messages |
| `/health` | GET | Tower health check |

## Running
```bash
python -m projects.personal_assistant.src.app
# Or directly:
cd projects/personal-assistant && python -c "from src.app import create_app; create_app().run(port=5011)"
```

## Version
1.1.0 — Extracted from monolithic agent_bridge_api.py
