# Workflow: Calendar Sync (Time Blocks)

## Overview

Sync time block schedules to Google Calendar. Used when William makes personal calendar requests.

## Prerequisites

- Google Calendar credentials at `~/.time-blocks/credentials.json`
- OAuth token at `~/.time-blocks/token.json`
- Time Blocks project at `projects/time-blocks/`

## Quick Commands

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/time-blocks

# View current config (working hours, recurring blocks)
python src/time_blocks.py config

# List available templates
python src/time_blocks.py templates

# Apply a template to today
python src/time_blocks.py apply-template productive_day --date today

# Sync to Google Calendar
python src/time_blocks.py sync --calendar "Time Blocks" --date today

# View today's schedule
python src/time_blocks.py view --date today

# List available Google Calendars
python src/time_blocks.py calendars
```

## Available Templates

| Template | Best For | Key Blocks |
|----------|----------|------------|
| `productive_day` | Standard workday | Workout, Creative, Project Building, Reading |
| `deep_work` | Focus-heavy day | Extended deep work sessions |
| `outreach_day` | Sales/leads | Cold emails, LinkedIn, follow-ups |
| `weekend` | Saturday | Relaxed pace, personal projects |
| `williams_weekly_routine` | Full week | Complex format with day-specific schedules |

## Updating Schedule Preferences

### Change Working Hours

Edit: `projects/time-blocks/config/user_preferences.json`

```json
{
  "working_hours": {
    "start": "06:00",
    "end": "21:00"
  }
}
```

### Change Recurring Blocks

Edit the same file, `recurring_blocks` section:

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
    }
  }
}
```

### Create/Modify Templates

Templates are in: `projects/time-blocks/templates/*.json`

## Common Requests & Actions

| Request | Action |
|---------|--------|
| "Update my calendar for today" | `apply-template` + `sync` |
| "Change workout days to Mon/Wed/Fri" | Edit user_preferences.json |
| "Add reading time every evening" | Edit user_preferences.json recurring_blocks |
| "Block 2 hours for deep work tomorrow" | `add` command or edit template |
| "Show my schedule" | `view --date today` |
| "Sync to calendar" | `sync --calendar "Time Blocks"` |

## Full Workflow: Update Schedule

1. **Understand the request**
   - What blocks need to change?
   - Recurring or one-time?

2. **Update configuration** (if recurring)
   ```bash
   # Edit user_preferences.json
   ```

3. **Apply template**
   ```bash
   python src/time_blocks.py apply-template productive_day --date today
   ```

4. **Sync to Google Calendar**
   ```bash
   python src/time_blocks.py sync --calendar "Time Blocks" --date today
   ```

5. **Verify**
   ```bash
   python src/time_blocks.py view --date today
   ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Template not found" | Check `templates/` directory, verify JSON format |
| Auth error | Re-run `python src/time_blocks.py auth` |
| Blocks not appearing in calendar | Check calendar name matches exactly |
| Duplicate events | Events may already exist - check calendar |

## Integration with Personal Assistant

When a calendar request comes in:

1. **Recognize as personal request** (mentions "my calendar", "schedule", etc.)
2. **Route to this workflow**
3. **Execute commands** in `projects/time-blocks/`
4. **Use existing Google credentials** at `~/.time-blocks/`

No need to set up new auth - credentials are already configured.
