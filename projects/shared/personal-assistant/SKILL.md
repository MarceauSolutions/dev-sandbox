# William's Personal AI Assistant

## Quick Reference

**When to use this skill:** Any personal request from William including:
- Calendar/scheduling (time blocks, appointments)
- Personal productivity (morning digest, routines)
- Google services (Calendar, Gmail, Drive)
- Life admin (reminders, notes, personal tracking)

## Request Routing Decision Tree

```
User Request
    │
    ├─► Personal Request? (calendar, schedule, personal productivity)
    │       └─► Use Personal Assistant workflows
    │
    ├─► Business Project? (Elder Tech, Fitness Influencer, etc.)
    │       └─► Route to specific project skill
    │
    ├─► New Idea/Opportunity?
    │       └─► Log to OPPORTUNITY-LOG.md
    │       └─► If significant: SOP 17 (Market Viability)
    │
    ├─► Repeatable Task Being Done?
    │       └─► Create workflow in appropriate project
    │       └─► If personal: workflows/ in this project
    │
    └─► General Question/Research?
            └─► Handle directly, no routing needed
```

## Integrated Capabilities

### 1. Time Blocks (Calendar Management)
**Project:** `projects/time-blocks/`
**Credentials:** `~/.time-blocks/` (Google Calendar OAuth)

**Commands:**
```bash
cd projects/time-blocks
python src/time_blocks.py config                    # Show settings
python src/time_blocks.py apply-template <name>    # Apply template
python src/time_blocks.py sync --calendar "Time Blocks" --date today
python src/time_blocks.py view --date today
```

**Templates Available:**
- `productive_day` - Full workday with workout, creative work, reading
- `deep_work` - Focus-heavy day
- `outreach_day` - Sales/lead generation focus
- `weekend` - Relaxed Saturday schedule
- `williams_weekly_routine` - Complete weekly schedule (complex format)

**Current Config:**
- Working Hours: 6 AM - 9 PM
- Workout: Mon/Wed/Fri/Sat 6-7 AM
- Creative Work: Mon/Wed/Fri/Sat 7:30-9:30 AM
- Reading: Daily 8-9 PM

### 2. Morning Digest
**Script:** `projects/personal-assistant/src/morning_digest.py`

Aggregates:
- Weather (Naples)
- Calendar events
- Email summary
- Task reminders
- Project status updates

### 3. Google Services
**Credentials Location:** `~/.time-blocks/` (shared OAuth)

Available APIs:
- Google Calendar (via time-blocks)
- Gmail (via email integrations)
- Google Drive (if configured)

## Workflows

| Workflow | Location | Purpose |
|----------|----------|---------|
| Daily Routine | `workflows/daily-routine-sop.md` | Morning/evening routines |
| Weekly Routine | `workflows/weekly-routine-sop.md` | Weekly planning/review |
| Calendar Sync | `workflows/calendar-sync.md` | Sync time blocks to calendar |
| Personal Request Routing | `workflows/request-routing.md` | How to route requests |

## Personal vs Business Decision

**Personal Request Indicators:**
- "my calendar", "my schedule"
- "remind me", "block time for"
- Personal activities (workout, reading, dog training)
- Life admin (appointments, errands)
- "for me", "I want to"

**Business Request Indicators:**
- Project names (Elder Tech, Fitness Influencer, HVAC)
- Client/customer references
- Revenue/pricing discussions
- Marketing/outreach tasks
- Technical implementation

**Hybrid (Personal + Business):**
- Time blocking for work tasks → Personal Assistant handles calendar, routes task details to project
- Personal branding content → Route to Fitness Influencer
- Interview prep → Route to Interview Prep skill

## Integration Points

### From Other Projects
Projects can request personal assistant actions:
- Schedule calendar events
- Send personal reminders
- Update morning digest

### To Other Projects
Personal assistant routes to:
- `interview-prep/` - Interview preparation
- `fitness-influencer/` - Content creation
- `amazon-seller/` - E-commerce operations
- `elder-tech-concierge/` - Elder tech business
- `hvac-distributors/` - HVAC quotes/research
- `time-blocks/` - Calendar management

## Files

```
projects/personal-assistant/
├── SKILL.md              # This file
├── README.md             # Project overview
├── VERSION               # 1.0.0
├── CHANGELOG.md          # Version history
├── src/
│   ├── morning_digest.py     # Daily digest generator
│   ├── routine_scheduler.py  # Routine management
│   └── digest_aggregator.py  # Aggregates project updates
├── workflows/
│   ├── daily-routine-sop.md
│   ├── weekly-routine-sop.md
│   ├── calendar-sync.md      # NEW
│   └── request-routing.md    # NEW
└── output/
    └── digests/              # Generated digests
```
