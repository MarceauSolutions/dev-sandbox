# Calendar Management Rules

> MANDATORY for all agents: Claude Code, Clawdbot/Panacea, Ralph

## Two Calendars — One Purpose Each

| Calendar | ID | Purpose | Color |
|----------|----|---------|-------|
| **Primary** (`wmarceau@marceausolutions.com`) | `primary` | Specific events: meetings, calls with named people, in-person visits, milestones | Green |
| **Time Blocks** | `c_710cb4eceeac036e44157b8626fe6447b430ce3fd0100020d4b32fc44af1f164@group.calendar.google.com` | Daily routine structure, work blocks, breaks, training | Blue |

**Rule**: NEVER put routine blocks on primary. NEVER put specific named events on Time Blocks.

## Before Creating ANY Calendar Event

1. **List events for that day on BOTH calendars** — check for conflicts
2. **Match the existing pattern** — read at least 2 other days on Time Blocks before creating
3. **No duplicates** — if a block already exists, update it, don't create another
4. **No overlaps** — every minute should belong to exactly one event, not two

## Daily Time Blocks Structure (Sprint Period: Mar 23 – Apr 5)

This is the BASE template. Day-specific work blocks replace the `[DEEP WORK]` slot.

```
6:15 - 7:00   Dog Walk + Morning Routine
7:00 - 7:30   Dashboard Review & Metrics
7:30 - 9:00   OUTREACH BLITZ — Rule of 100 (or day-specific outreach block)
9:00 - 9:15   Break / Hand Therapy
9:15 - 11:15  [DEEP WORK] — varies by day (calls, in-person, build, proposals)
11:15 - 11:30 Break
11:30 - 12:00 Quick Follow-ups / Proposals
12:00 - 1:00  Lunch
1:00 - 2:30   [AFTERNOON WORK] — varies by day
2:30 - 2:45   Break / Hand Therapy
2:45 - 3:45   Training — Defy the Odds Athletic Program
4:00 - 4:30   Spanish Study
4:30 - 5:00   Dog Walk / Dog Training
```

### Day Variations (Deep Work + Afternoon blocks)

| Day | Morning Deep Work (9:15-11:15) | Afternoon Work (1:00-2:30) | Evening |
|-----|-------------------------------|---------------------------|---------|
| Mon | Sales Playbook / Build session | Setup tasks (Stripe, DNS, Apollo) | Evening extension 5:00-6:30 |
| Tue | Phone Blitz 100 min (9:00-11:30) | Apollo Sequences / Enrichment | Ends at 3:45 (compensating) |
| Wed | In-Person Visits (specific stops on Primary) | Follow-up Calls | — |
| Thu | Cold Email Batch + Warm DMs | Build session (n8n, Claude Code) | — |
| Fri | Discovery Calls / Proposal Writing | Sales Readiness + Dry Run | — |
| Sat | Content Batch Film Day | LOW ENERGY DAY — lighter schedule | — |

### Training Time — NEVER at 5am

Training is in the **evening: 6:00 - 8:00pm** (William's current preference as of March 2026).
Previous Time Blocks show 2:45pm but William has been training at 6-8pm lately.
The 5am-7am slot on primary was a one-time error. Do not repeat.
**Rule**: Training is NEVER before noon. Default to 6:00-8:00pm unless William says otherwise.

## Color Rules

**No colorId on routine blocks.** They inherit the calendar's default color.

Only use colorId on Time Blocks for special/one-off events:

| colorId | Color | Use For |
|---------|-------|---------|
| `2` | Sage | Claude Code build tasks (William reviews output) |
| `5` | Banana | One-off tasks (trademark, setup, etc.) |
| `6` | Tangerine | Integration/setup work (Stripe, Apollo, DNS) |
| `9` | Blueberry | Evening extensions |

**Primary calendar**: No colorId. Green is default. Don't override.

## When Adapting for Special Days (like in-person blitz)

1. Keep the morning routine blocks (Dog Walk, Dashboard, Break) on Time Blocks
2. Replace the Outreach Blitz block with the day-specific activity
3. Put SPECIFIC stops/meetings on Primary with full details (address, phone, script)
4. Fill gaps between stops with Time Blocks (e.g., "Cold Calls Between Stops")
5. Keep the afternoon structure intact (Break → Training → Spanish → Dog Walk)
6. NEVER create a giant 3-hour "In-Person Visits" block that overlaps individual stops

## Post-April 6 Schedule Change

When William starts his job (7am-3pm weekdays):
- Morning routine shifts earlier
- Business work moves to evenings/weekends
- Training stays at 3:00-3:45pm (right after work)
- This template will need a full rebuild — do NOT use the sprint template after April 6

## Agent Handoff Rules

- **Claude Code**: Can create/update/delete events on both calendars via MCP
- **Clawdbot/Panacea**: Can suggest schedule changes via Telegram but MUST NOT create events without checking existing pattern first. If creating events, MUST read both calendars for the target day FIRST.
- **Ralph**: No calendar access. Communicate schedule needs via HANDOFF.md.
- **All agents**: After modifying calendar, note changes in HANDOFF.md so other agents know
