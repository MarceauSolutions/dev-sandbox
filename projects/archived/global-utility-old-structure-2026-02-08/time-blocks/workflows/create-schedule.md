# Workflow: Create and Manage Time Block Schedule

## Overview
This workflow covers creating time blocks for focused work periods, applying templates, viewing schedules, and syncing to Google Calendar.

## Prerequisites
- Python 3.10+
- For Google Calendar sync:
  - Google Cloud project with Calendar API enabled
  - OAuth credentials file at `~/.time-blocks/credentials.json`
  - Required packages: `pip install google-auth-oauthlib google-api-python-client`

## Quick Start

### 1. Create a Single Block
```bash
# With end time
python src/time_blocks.py add --start 6:00 --end 7:00 --activity "Workout" --category exercise

# With duration (in minutes)
python src/time_blocks.py add --start 19:00 --duration 180 --activity "Project Building" --category work --priority critical
```

### 2. Apply a Template
```bash
# See available templates
python src/time_blocks.py templates

# Apply template to today
python src/time_blocks.py apply-template productive_day --date today

# Apply to specific date
python src/time_blocks.py apply-template productive_day --date 2026-01-15
```

### 3. View Schedule
```bash
# View today's blocks
python src/time_blocks.py view --date today

# Timeline view
python src/time_blocks.py view --date today --timeline
```

### 4. Sync to Google Calendar
```bash
# First time: authenticate
python src/time_blocks.py auth

# Sync today's blocks
python src/time_blocks.py sync --calendar "Time Blocks" --date today

# Force sync (even if events exist)
python src/time_blocks.py sync --calendar "Work Blocks" --date today --force
```

## Categories

| Category | Color in Calendar | Use For |
|----------|------------------|---------|
| `work` | Blue | Client work, projects, deep work |
| `exercise` | Red | Workouts, physical activity |
| `personal` | Yellow | Dog training, hobbies, personal tasks |
| `rest` | Green | Recovery, relaxation, breaks |
| `admin` | Cyan | Planning, email, admin tasks |
| `meal` | Orange | Breakfast, lunch, dinner |
| `learning` | Purple | Reading, courses, skill building |
| `social` | Dark Green | Meetings, calls, social events |

## Priority Levels

| Priority | When to Use |
|----------|------------|
| `critical` | Must happen, non-negotiable (e.g., client deadline) |
| `high` | Important, should do (e.g., workout, daily habit) |
| `medium` | Default, good to do |
| `low` | Nice to have, can skip if needed |

## Recurring Blocks

Create blocks that repeat on specific days:
```bash
python src/time_blocks.py add \
  --start 6:00 --duration 60 \
  --activity "Workout" --category exercise \
  --recurring --days mon tue wed thu fri
```

## Managing Blocks

```bash
# Remove a block by index (shown in view)
python src/time_blocks.py remove 0 --date today

# Clear all blocks for a day
python src/time_blocks.py clear --date today

# Save current schedule as a new template
python src/time_blocks.py save-template my_custom_day --date today
```

## Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Calendar API"
4. Go to "Credentials" > "Create Credentials" > "OAuth 2.0 Client IDs"
5. Application type: "Desktop app"
6. Download JSON and save as `~/.time-blocks/credentials.json`
7. Run `python src/time_blocks.py auth` to complete setup

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Credentials | `~/.time-blocks/credentials.json` | Google OAuth config |
| Token | `~/.time-blocks/token.json` | Auth token (auto-created) |
| Blocks | `~/.time-blocks/blocks.json` | Your saved schedules |
| Templates | `projects/time-blocks/templates/` | Reusable templates |

## Typical Daily Workflow

1. **Morning**: Apply template for the day
   ```bash
   python src/time_blocks.py apply-template productive_day
   ```

2. **Adjust**: Add/remove blocks as needed
   ```bash
   python src/time_blocks.py add --start 14:00 --duration 60 --activity "Client Call" --category work
   ```

3. **Sync**: Push to calendar
   ```bash
   python src/time_blocks.py sync --calendar "Time Blocks"
   ```

4. **Review**: Check your schedule
   ```bash
   python src/time_blocks.py view --timeline
   ```

## Troubleshooting

### "Google Calendar libraries not installed"
```bash
pip install google-auth-oauthlib google-api-python-client
```

### "No credentials file found"
Follow the Google Calendar Setup steps above.

### "Authentication failed"
Delete `~/.time-blocks/token.json` and run `python src/time_blocks.py auth` again.

### Events duplicated in calendar
Use `--skip-existing` (default) or check if you're using different calendar names.
