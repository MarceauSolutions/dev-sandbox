# MailAssist — AI Email Assistant

## What It Does
Web app that connects to a user's Gmail account via OAuth and provides AI-powered email operations:
- **Smart Search**: Natural language email search ("find the email from my insurance company")
- **Thread Analysis**: AI-powered thread summaries with sentiment, urgency, action items
- **Document Generation**: Create summaries, timelines, evidence packages, action plans from threads
- **Draft Responses**: Describe your intent in plain English → AI drafts the reply → review and send
- **Send/Save Drafts**: Send directly or save to Gmail drafts for later

## How to Access
```bash
./scripts/email-assistant.sh
# Opens http://127.0.0.1:8791
```

## Architecture
```
email-assistant/
├── src/
│   ├── app.py              # FastAPI web server (port 8791)
│   ├── gmail_service.py    # Gmail API OAuth + operations
│   └── ai_engine.py        # Claude API for analysis/drafting
├── static/
│   └── style.css           # Marceau branded UI (dark + gold)
├── templates/
│   └── index.html          # Single-page app frontend
├── data/                   # Session tokens (gitignored)
├── requirements.txt
└── CLAUDE.md               # This file
```

## Prerequisites
1. **Google Cloud OAuth credentials** — Download from console, save as `credentials.json` in dev-sandbox root
   - Application type: **Web application**
   - Redirect URI: `http://127.0.0.1:8791/auth/callback`
   - Scopes: gmail.readonly, gmail.send, gmail.compose, gmail.modify
2. **ANTHROPIC_API_KEY** in `.env` — for AI features
3. Python packages: `pip install -r requirements.txt`

## Key Patterns
- Builds on existing `execution/gmail_api_monitor.py` OAuth patterns
- Uses web OAuth flow (not desktop) for browser-based auth
- Per-user session management via cookies + credential files
- AI engine uses Claude Sonnet for cost-efficient analysis/drafting
- All email data stays local — no external storage

## Cost
- Gmail API: FREE
- Claude API (Sonnet): ~$0.003 per search query, ~$0.01-0.03 per analysis/draft

## Generated Files
- `data/session_*.json` — OAuth credential files per user session (gitignored)
