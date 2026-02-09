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

### 1. Smart Calendar (AI-Powered Scheduling) ⭐ NEW
**Script:** `projects/shared/personal-assistant/src/smart_calendar.py`
**Credentials:** `~/dev-sandbox/credentials.json` (Google Calendar OAuth)

**Philosophy:**
- Hormozi-style prioritization: Revenue impact → Operations → Admin
- Energy management: Hard tasks in morning, admin in afternoon
- Habit stacking: Consistent daily routines compound
- Content velocity: Daily posts > weekly polished content

**Three-Agent Integration (SOP-29):**
| Agent | Use Case | Example |
|-------|----------|---------|
| **Claude Code** | Interactive planning, complex scheduling | "Help me plan next week with these priorities..." |
| **Clawdbot** | Quick mobile requests | "Block tomorrow for content" |
| **Ralph** | Complex multi-week schedule generation | PRD with detailed schedule requirements |

**Commands:**
```bash
cd projects/shared/personal-assistant

# Natural language scheduling
python -m src.smart_calendar --schedule "Block tomorrow for content and habits"
python -m src.smart_calendar --schedule "Schedule next week with focus on business"

# Generate full week
python -m src.smart_calendar --week

# Preview without creating (dry run)
python -m src.smart_calendar --week --dry-run

# Specific date
python -m src.smart_calendar --date 2026-02-17 --schedule "Block for deep work"
```

**Default Daily Habits (Mon-Fri):**
| Time | Activity | Purpose |
|------|----------|---------|
| 6:00-7:00 AM | 💪 Workout | Non-negotiable fitness credibility |
| 7:00-7:30 AM | 🇪🇸 Spanish | 2x audience (Hispanic market) |
| 7:30-8:00 AM | 📚 Reading | Ideas from inputs |
| 5:00-5:30 PM | 🐕 Dog Training | Discipline + content |
| 8:00-8:30 PM | 📱 Daily Post | Volume > perfection |

**Content Schedule:**
| Day | Block | Focus |
|-----|-------|-------|
| Mon | 11 AM-12 PM | 🎬 Film 2-3 short clips |
| Wed | 2-3:30 PM | 🎬 Medium-form content |
| Thu | 9 AM-12 PM | 🎬 BATCH DAY - Long-form YouTube |
| Fri | 10:30 AM-12 PM | 🎬 Publish best of week |
| Sun | 2-4 PM | 📅 Week prep + content batching |

### 1b. Legacy Time Blocks (Templates)
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
projects/shared/personal-assistant/
├── SKILL.md                  # This file
├── README.md                 # Project overview
├── VERSION                   # 1.0.0
├── CHANGELOG.md              # Version history
├── src/
│   ├── smart_calendar.py     # ⭐ AI-powered scheduling (NEW)
│   ├── create_time_blocks.py # Hardcoded time block creator
│   ├── morning_digest.py     # Daily digest generator
│   ├── routine_scheduler.py  # Routine management
│   ├── digest_aggregator.py  # Aggregates project updates
│   ├── ideas_queue.py        # Telegram ideas queue
│   └── fitness_calendar.py   # Fitness-specific calendar
├── workflows/
│   ├── daily-routine-sop.md
│   ├── weekly-routine-sop.md
│   ├── calendar-sync.md
│   └── request-routing.md
└── output/
    └── digests/              # Generated digests
```
