# Personal Assistant Tower Directive

## Domain
Email management, calendar scheduling, morning digests, routine automation, and inter-tower information aggregation.

## Core Capabilities
- **Unified Morning Digest**: Aggregates pipeline, Gmail, Calendar, Twilio, health check → Telegram at 6:30am
- **System Health Check**: Verifies launchd, pipeline.db, Gmail token, Twilio, daily loop, .env keys
- **Gmail API**: List, read, send, draft, search (single + multi-account)
- **Google Sheets**: Read, write, append
- **Twilio SMS**: Send, list
- **Gmail Monitoring**: Inbox watcher, reply tracker, API monitor
- **Calendly Monitor**: Detects bookings, matches to pipeline leads
- **Calendar Reminders**: Event-based notifications
- **Smart Calendar**: Time block management, routine scheduling

## Entry Point
- Flask app: `src/app.py` (port 5011)
- 1 launchd job: morning digest (6:30am)

## Integration Points
- **pipeline.db** (read): Pulls deal stages, hot leads, follow-ups for morning digest
- **lead-generation**: Receives Calendly handoff requests → sends email via Gmail API
- **execution/**: Uses multi_gmail_search, agent_calendar_gateway (shared)

## Current Version
1.1.0
