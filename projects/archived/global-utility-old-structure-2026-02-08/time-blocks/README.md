# Time Blocks

A personal productivity tool for creating time blocks in your calendar. Schedule focused work periods throughout the day so you know exactly what you're doing at any given time.

## Philosophy

- **NOT a full day scheduler** - just blocks for focused activities
- Time between blocks is "free time" for whatever
- Easy to create recurring blocks
- Visual representation of your day
- Syncs to Google Calendar

## Installation

```bash
# Core functionality
pip install -r requirements.txt

# For Google Calendar integration
pip install google-auth-oauthlib google-api-python-client
```

## Quick Start

```bash
# Create a single block
python src/time_blocks.py add --start 6:00 --end 7:00 --activity "Workout" --category exercise

# Apply a template
python src/time_blocks.py apply-template productive_day

# View today's blocks
python src/time_blocks.py view --date today

# View as timeline
python src/time_blocks.py view --date today --timeline

# Sync to Google Calendar
python src/time_blocks.py sync --calendar "Time Blocks"

# Show current configuration
python src/time_blocks.py config
```

## Configuration

### Working Hours
All blocks are validated against your working hours (default: 6 AM - 9 PM).
Edit `config/user_preferences.json` to customize:

```json
{
  "working_hours": {
    "start": "06:00",
    "end": "21:00"
  }
}
```

### Recurring Blocks
The config file also defines your recurring blocks:

```json
{
  "recurring_blocks": {
    "workout": {
      "time": {"start": "06:00", "end": "07:00"},
      "days": ["mon", "wed", "fri", "sat"],
      "category": "exercise"
    },
    "reading": {
      "time": {"start": "20:00", "end": "21:00"},
      "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
      "category": "learning"
    },
    "creative_work": {
      "time": {"start": "07:30", "end": "09:30"},
      "days": ["mon", "wed", "fri", "sat"],
      "category": "work"
    }
  }
}
```

## Features

### Categories
- `work` - Client work, projects, deep work (Blue)
- `exercise` - Workouts, physical activity (Red)
- `personal` - Dog training, hobbies (Yellow)
- `rest` - Recovery, relaxation (Green)
- `admin` - Planning, email (Cyan)
- `meal` - Meals and breaks (Orange)
- `learning` - Reading, courses (Purple)
- `social` - Meetings, calls (Dark Green)

### Templates
Pre-built schedules you can apply to any day:
- `productive_day` - Standard productive day with workout, creative work, and project building
- `deep_work` - Maximum focus day with minimal interruptions
- `outreach_day` - Focus on cold emails, lead generation, and client outreach
- `weekend` - Relaxed weekend schedule with flexibility
- `williams_weekly_routine` - Complete weekly schedule with day-specific blocks

### Google Calendar Integration
- Creates events with category-based colors
- Supports recurring events
- Avoids duplicating existing events

## Commands

| Command | Description |
|---------|-------------|
| `add` | Add a time block |
| `remove` | Remove a block by index |
| `clear` | Clear all blocks for a day |
| `view` | View schedule (list or timeline) |
| `apply-template` | Apply a template to a date |
| `save-template` | Save current schedule as template |
| `templates` | List available templates |
| `sync` | Sync to Google Calendar |
| `calendars` | List Google calendars |
| `auth` | Authenticate with Google |
| `config` | Show current configuration |

## Example: Productive Day Template

```
06:00 - 07:00  Workout (exercise) - Mon/Wed/Fri/Sat
07:30 - 09:30  Creative Work (work)
10:00 - 10:30  Planning & Review (admin)
12:00 - 12:30  Lunch (meal)
13:00 - 14:00  Cold Emails / Lead Scraping (work)
14:30 - 17:00  Project Building (work)
17:30 - 18:30  Dog Training (personal)
19:00 - 20:00  Project Building - Evening (work)
20:00 - 21:00  Reading (learning)
```

## Data Storage

All data is stored in `~/.time-blocks/`:
- `blocks.json` - Your scheduled blocks
- `token.json` - Google auth token
- `credentials.json` - Google OAuth credentials (you provide this)

Configuration is stored in `config/user_preferences.json` in the project directory.

## See Also

- [Create Schedule Workflow](workflows/create-schedule.md) - Detailed usage guide
