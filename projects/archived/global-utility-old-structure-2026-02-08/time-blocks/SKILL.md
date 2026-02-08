# Time Blocks Skill

## Purpose
Personal productivity tool for creating and managing time blocks in William's calendar.

## Trigger Phrases
- "Schedule my day"
- "Create time blocks"
- "Block out time for..."
- "Apply productive day template"
- "What's on my schedule?"
- "Sync my blocks to calendar"

## Capabilities

### 1. Create Time Blocks
**Trigger**: "Block out [time] for [activity]"
**Action**: Create a time block with the specified details
**Example**: "Block out 6-7am for workout"

### 2. Apply Templates
**Trigger**: "Apply [template] template" or "Use productive day schedule"
**Action**: Apply a pre-built template to today or specified date
**Templates**: productive_day, weekend

### 3. View Schedule
**Trigger**: "Show my schedule" or "What's on my calendar today?"
**Action**: Display the day's time blocks

### 4. Sync to Calendar
**Trigger**: "Sync to Google Calendar" or "Push blocks to calendar"
**Action**: Create events in Google Calendar from time blocks

### 5. Quick Add Common Blocks
**Trigger**: "Add workout", "Add project time", "Add client work"
**Action**: Add pre-configured blocks for common activities

## Quick Commands

```bash
# Add a block
python src/time_blocks.py add --start 6:00 --duration 60 --activity "Workout" --category exercise

# Apply template
python src/time_blocks.py apply-template productive_day

# View schedule
python src/time_blocks.py view

# Sync to calendar
python src/time_blocks.py sync --calendar "Time Blocks"
```

## Integration with Personal Assistant

When William asks to schedule his day or manage time blocks, use this skill to:
1. Apply appropriate template based on day of week
2. Adjust blocks based on specific requests
3. Sync to Google Calendar when asked

## Common Activities

| Activity | Category | Typical Duration | Typical Time |
|----------|----------|-----------------|--------------|
| Workout | exercise | 60 min | 6:00 AM |
| Planning | admin | 30 min | 7:30 AM |
| Cold Emails | work | 60 min | 6:00 PM |
| Project Building | work | 180 min | 7:00 PM |
| Dog Training | personal | 30 min | 10:00 PM |

## Data Location
- Blocks: `~/.time-blocks/blocks.json`
- Templates: `projects/time-blocks/templates/`
