# Company on a Laptop — Operations Cheatsheet

**Last Updated:** March 27, 2026  
**Filename:** `docs/OPERATINGH_SHEET.md` (consider renaming to `OPERATIONS-CHEATSHEET.md` later)  
**Purpose:** Central reference for all key commands, scheduled jobs, testing, troubleshooting, and daily routines.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Scheduled Jobs (Launchd)](#core-scheduled-jobs)
3. [Daily Testing & Verification](#daily-testing--verification)
4. [Live Operation Commands](#live-operation-commands)
5. [Health & Monitoring](#health--monitoring)
6. [Git & Save Commands](#git--save-commands)
7. [Troubleshooting](#troubleshooting)
8. [Clawdbot & Calendar Integration](#clawdbot--calendar-integration)
9. [Quick Daily Routine](#quick-daily-routine)

---

## System Overview

- **Active Towers**: lead-generation (full autonomous loop), personal-assistant (digest + scheduling)
- **Key Automation**: Daily lead acquisition + 6:30am morning digest + HOT lead SMS alerts
- **Human Role**: Review digest, handle high-ROI walk-ins/calls, approve calendar blocks
- **Goal**: Run autonomously during 7am–3pm work hours starting April 6

---

## Core Scheduled Jobs (Launchd)

| Time          | Job Name                          | Purpose                                      |
|---------------|-----------------------------------|----------------------------------------------|
| 6:30am        | com.marceau.pa.morning-digest     | Daily plan + health + pipeline + proposals   |
| 9:00am        | com.marceau.leadgen.daily-loop    | Full lead acquisition (discover → outreach)  |
| Every 15 min  | com.marceau.leadgen.check-responses | Twilio/Gmail replies + HOT lead alerts     |
| 5:30pm        | com.marceau.leadgen.digest        | Evening pipeline summary                     |

**Reload all jobs:**
```bash
cd ~/dev-sandbox/projects/lead-generation && bash launchd/install.sh
cd ~/dev-sandbox/projects/personal-assistant && bash launchd/install.sh

Daily Testing & Verification
Preview 6:30am digest:
Bashcd ~/dev-sandbox/projects/personal-assistant
python3 -m src.unified_morning_digest --preview
Run supervised live loop (recommended nightly):
Bashcd ~/dev-sandbox/projects/lead-generation
python3 -m src.daily_loop full --for-real
System health check:
Bashcd ~/dev-sandbox/projects/personal-assistant
python3 -m src.system_health_check

Live Operation Commands
Safe Git Save (use after every session or change):
Bashcd ~/dev-sandbox
./scripts/save.sh --include-new "your descriptive message here"
Check active launchd jobs:
Bashlaunchctl list | grep -iE "marceau|leadgen|pa.morning"

Health & Monitoring
Full health check:
Bashcd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check
View loop health log:
Bashcat ~/dev-sandbox/projects/lead-generation/logs/loop_health.json

Troubleshooting
If 6:30am digest doesn't arrive by 6:45am:
Bashcd ~/dev-sandbox/projects/personal-assistant && python3 -m src.system_health_check
Reload launchd jobs:
Bashcd ~/dev-sandbox/projects/lead-generation && bash launchd/install.sh
cd ~/dev-sandbox/projects/personal-assistant && bash launchd/install.sh
Check for any remaining stale references:
Bashlaunchctl list | grep -iE "sales-pipeline|shared|lead-scraper"

Clawdbot & Calendar Integration (Pending)

Mac-side API ready on port 5011
Test "yes schedule" manually:Bashcurl -X POST http://localhost:5011/scheduler/approve
Ralph needs to deploy Clawdbot handlers on EC2 (see HANDOFF.md for instructions)


Quick Daily Routine
Evening:

Run supervised live loop (optional)
Run ./scripts/save.sh

Morning:

Read 6:30am Telegram digest
Reply “yes schedule” if the proposed blocks look good
Execute high-ROI tasks (walk-ins/calls)

When you receive a HOT lead SMS:

Reply “1”, “2”, or “3”