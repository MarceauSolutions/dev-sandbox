# Personal AI Assistant

## What This Does
Unified personal productivity assistant that aggregates data from Gmail, SMS, Google Calendar, forms, and campaigns into a morning digest. Manages daily/weekly routines based on the Hormozi high-agency framework: proactive high-willpower tasks (study, strategy) in the morning, reactive tasks (email, editing, social media) in the afternoon.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant

# Morning digest
python -m src.morning_digest --preview       # Preview without sending email
python -m src.morning_digest                  # Generate and send via SMTP

# Digest data only (no email)
python -m src.digest_aggregator --hours 24

# Calendar management
python -m src.routine_scheduler setup         # Create all recurring reminders
python -m src.routine_scheduler list          # List existing reminders
python -m src.routine_scheduler delete        # Remove routine reminders

# Smart calendar with content strategy
python -m src.smart_calendar

# Fitness calendar
python -m src.fitness_calendar

# Idea queue (from Telegram)
python -m src.ideas_queue list                # Show pending ideas
python -m src.ideas_queue complete 3          # Mark idea #3 done

# AI news digest
python -m src.ai_news_digest

# Restaurant finder
python -m src.restaurant_finder
```

## Architecture
- **`src/morning_digest.py`** - Generates and sends formatted morning digest emails via SMTP
- **`src/digest_aggregator.py`** - Combines data from Gmail, SMS, forms, calendar, campaigns
- **`src/routine_scheduler.py`** - Creates recurring Google Calendar events (daily/weekly/monthly)
- **`src/smart_calendar.py`** - Content strategy + project work blocks
- **`src/fitness_calendar.py`** - Workout schedule management
- **`src/ideas_queue.py`** - Process ideas captured via Telegram
- **`src/ai_news_digest.py`** - AI/tech news aggregation
- **`src/restaurant_finder.py`** - Local restaurant recommendations
- **`src/create_time_blocks.py`** - Time blocking for focus work
- **`workflows/daily-routine-sop.md`** - Full Hormozi daily schedule (7 AM - 10 PM)
- **`workflows/weekly-routine-sop.md`** - Weekly/monthly review cadence

## Project-Specific Rules
- Hormozi framework: morning = high-agency (study, strategy), afternoon = reactive (email, editing)
- Non-negotiable 2-hour workout block at 9 AM daily
- Google OAuth required for Calendar integration -- needs `credentials.json` and `token.json`
- SMTP credentials needed for digest email delivery (configured in root `.env`)
- No frontend -- interaction happens through Claude Code chat
- Digest schedule: Daily 8 AM, Weekly Monday, Bi-weekly, Monthly 1st
- Reading list rotation: Business (Mon/Wed), Fitness (Tue/Thu), Psychology (Fri)

## Relevant SOPs
- SOP 24: Daily/Weekly Digest System (setup, commands, data sources)
- `workflows/daily-routine-sop.md` - Detailed daily schedule with Hormozi framework
- `workflows/weekly-routine-sop.md` - Weekly/monthly review tasks
- `workflows/digest-aggregator-workflow.md` - How the digest pipeline works
