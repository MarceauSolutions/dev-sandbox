# Personal Assistant Tower

William's personal automation — scheduling, email management, health monitoring, and the Panacea unified agent.

## Key Components
- `src/panacea_relay.py` — Unified EC2 agent (Telegram + Grok + Claude Code)
- `src/grok_strategic_layer.py` — Grok API consultation (shared with Mac)
- `src/morning_digest.py` — Daily briefing aggregator
- `src/gmail_api.py` — Gmail operations

## Services
- Panacea: EC2 systemd service (`panacea.service`)
