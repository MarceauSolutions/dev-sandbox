# Workflow: Personal Request Routing

## Overview

This workflow defines how to identify and route personal requests vs business requests, ensuring the right tools and credentials are used.

## Decision Framework

### Step 1: Identify Request Type

| Signal | Type | Route To |
|--------|------|----------|
| "my calendar", "schedule", "time block" | Personal | Personal Assistant → Time Blocks |
| "remind me", "don't forget" | Personal | Personal Assistant → Reminders |
| Workout, reading, dog training, personal activities | Personal | Personal Assistant |
| Project names (Elder Tech, Fitness, HVAC) | Business | Specific project skill |
| Client/customer/pricing | Business | Specific project skill |
| "new idea", "we could build" | Opportunity | Log to OPPORTUNITY-LOG.md |
| Repeatable task being performed | Workflow | Create workflow in appropriate project |

### Step 2: Route Personal Requests

```
Personal Request
    │
    ├─► Calendar-related?
    │       └─► Use time-blocks project
    │       └─► Credentials: ~/.time-blocks/
    │       └─► Commands: apply-template, sync, view
    │
    ├─► Morning routine / digest?
    │       └─► Use personal-assistant/src/morning_digest.py
    │
    ├─► Personal reminder / note?
    │       └─► Log appropriately
    │       └─► Consider calendar event or task
    │
    └─► Personal research / question?
            └─► Handle directly
```

### Step 3: Route Business Requests

```
Business Request
    │
    ├─► Elder Tech related?
    │       └─► projects/elder-tech-concierge/
    │
    ├─► Fitness / content creation?
    │       └─► projects/fitness-influencer/
    │
    ├─► HVAC quotes / research?
    │       └─► projects/hvac-distributors/
    │
    ├─► Amazon selling?
    │       └─► projects/amazon-seller/ (MCP available)
    │
    ├─► Interview prep?
    │       └─► projects/interview-prep/
    │
    └─► New project?
            └─► SOP 0: Project Kickoff
```

## Examples

### Personal Request Examples

**"Update my calendar so workouts are Mon/Wed/Fri/Sat 6-7 AM"**
- Type: Personal (calendar)
- Route: Personal Assistant → Time Blocks
- Action: Update user_preferences.json, apply template, sync to Google Calendar

**"Block time for reading every evening"**
- Type: Personal (calendar)
- Route: Personal Assistant → Time Blocks
- Action: Add recurring block, sync to calendar

**"Remind me to call the dentist"**
- Type: Personal (reminder)
- Route: Personal Assistant
- Action: Create calendar event or add to task list

### Business Request Examples

**"Send bulk pricing inquiries to iPad wholesalers"**
- Type: Business (Elder Tech)
- Route: projects/elder-tech-concierge/src/procurement/
- Action: Run inquiry_manager.py

**"Find HVAC companies in Naples for service call pricing"**
- Type: Business (HVAC research)
- Route: projects/hvac-distributors/
- Action: Web research, create research document

**"Generate content for X this week"**
- Type: Business (Fitness Influencer)
- Route: projects/fitness-influencer/ or projects/social-media-automation/
- Action: Use content generator tools

### Hybrid Examples

**"Schedule deep work blocks for the Elder Tech admin dashboard"**
- Calendar aspect: Personal Assistant handles time blocking
- Work aspect: Note the task is for Elder Tech project
- Action: Create time blocks, sync to calendar

## Credential Locations

| Service | Credential Location | Used By |
|---------|---------------------|---------|
| Google Calendar | `~/.time-blocks/credentials.json` | Time Blocks, Personal Assistant |
| Google Calendar Token | `~/.time-blocks/token.json` | Time Blocks |
| Gmail | `~/.credentials/gmail/` | Email integrations |
| Twilio | `.env` files in projects | Elder Tech, SMS features |
| OpenAI/Anthropic | `.env` files | Various AI features |

## When to Create a New Workflow

Use the scoring matrix from SOP 6:

| Factor | 0 | 1 | 2 | 3 |
|--------|---|---|---|---|
| **Recurrence** | One-time | Unlikely | Probable | Frequent |
| **Consistency** | Doesn't matter | Nice to have | Important | Critical |
| **Complexity** | Trivial (<3 steps) | Simple | Moderate | Complex (10+ steps) |
| **Onboarding** | Only I'll do this | Might help others | Would help | Essential |

**Score 7+:** Create workflow immediately
**Score 4-6:** Create after second occurrence
**Score 0-3:** Skip, note in session-history if notable

## When to Log as Opportunity

Log to `OPPORTUNITY-LOG.md` when:
- New product/service idea emerges
- Market opportunity identified
- Potential revenue stream discussed
- "We could build..." or "What if we..." statements

Then decide:
- Small idea: Just log it
- Significant idea: Run SOP 17 (Market Viability Analysis)
