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

# Sync to Google Calendar
python src/time_blocks.py sync --calendar "Time Blocks"
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
- `productive_day` - Standard productive day with workout, planning, and project building
- `weekend` - Relaxed weekend schedule

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

## Example: Productive Day Template

```
06:00 - 07:00  Workout (exercise)
07:30 - 08:00  Planning & Review (admin)
12:00 - 12:30  Lunch (meal)
18:00 - 19:00  Cold Emails / Lead Scraping (work)
19:00 - 22:00  Project Building (work)
22:00 - 22:30  Dog Training (personal)
```

## Data Storage

All data is stored in `~/.time-blocks/`:
- `blocks.json` - Your scheduled blocks
- `token.json` - Google auth token
- `credentials.json` - Google OAuth credentials (you provide this)

## See Also

- [Create Schedule Workflow](workflows/create-schedule.md) - Detailed usage guide
