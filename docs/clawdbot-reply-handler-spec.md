# Clawdbot Reply Handler — Accountability Parsing Specification

> **Purpose**: Enhance Clawdbot's existing Telegram message handler to parse William's accountability replies and log them to the Scorecard Google Sheet.
> **Location**: Enhancement to existing Clawdbot on EC2 (34.193.98.97)
> **No new services needed** — this is a parsing layer added to Clawdbot's message processing pipeline.

---

## Architecture Overview

```
William's Telegram Message
  → Clawdbot receives via Telegram Bot API (existing)
  → NEW: Accountability Parser (runs BEFORE general AI response)
  → If accountability pattern matched:
      → Log to Google Sheets
      → Send structured response
      → STOP (don't pass to general AI handler)
  → If no pattern matched:
      → Pass to existing Clawdbot AI handler (normal behavior)
```

The accountability parser is a **pre-filter**. It intercepts specific message patterns, handles them with structured logic (no AI inference needed), and only falls through to the general handler if no pattern matches.

---

## Parse Rules (Priority Order)

Rules are evaluated top-to-bottom. First match wins.

### Rule 1: Energy Level Reply (Single Number 1-10)

**Pattern**: Message is a single integer between 1 and 10 (with optional whitespace).

**Regex**: `^\s*([1-9]|10)\s*$`

**Context Check**: Only interpret as energy level if the **last outbound message to William** (within 4 hours) was a morning check-in. This prevents "5" in a random conversation from being logged as energy.

**Action**:
1. Log to Google Sheets → Daily Log tab:
   - `Date`: today (YYYY-MM-DD)
   - `Day_Number`: calculated from plan start (2026-03-17)
   - `Week_Number`: calculated
   - `Day_of_Week`: Mon/Tue/Wed/Thu/Fri
   - `Morning_Energy`: the number
2. Respond based on energy level:

| Energy | Response |
|--------|----------|
| 8-10 | "High energy day. Channel it into outreach volume." |
| 5-7 | "Solid. Execute the fundamentals today." |
| 3-4 | "Low energy. Do the minimum: 50 outreach, 1 video. Rest is legit." |
| 1-2 | "Rough day. Do what you can. Even 10 outreach messages is forward progress." |

**Google Sheets Write**:
- Sheet ID: `${SCORECARD_SPREADSHEET_ID}`
- Tab: Daily Log (use GID, mode:id)
- Operation: Append row
- Values: `{ Date, Day_Number, Week_Number, Day_of_Week, Morning_Energy }`

---

### Rule 2: EOD Numbers (4 Comma-Separated Numbers)

**Pattern**: Message contains 4 numbers separated by commas (with optional spaces).

**Regex**: `^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$`

**Parsed Values**:
- Group 1: `outreach_count` (typically 0-200)
- Group 2: `meetings_booked` (typically 0-5)
- Group 3: `videos_filmed` (typically 0-5)
- Group 4: `content_posted` (typically 0-10)

**Validation**:
- All values must be non-negative integers
- If outreach > 500 in a single day: reply "That's {n} outreach in one day — confirm? Reply 'yes' to log or correct your numbers." (sanity check)
- If any value is negative: reject with parse error message

**Action**:
1. Update today's row in Google Sheets → Daily Log tab:
   - If row exists for today (from morning energy): UPDATE the row
   - If no row exists: APPEND new row
   - Fields: `Outreach_Count`, `Meetings_Booked`, `Videos_Filmed`, `Content_Posted`
2. Fetch this week's running totals (SUM of Daily Log where Week_Number == current)
3. Compose response (see response templates below)
4. Check milestone conditions (see Rule 2a)

**Response Template — On Target (outreach >= 100):**
```
Logged. {outreach} outreach (target: 100) — solid.
{meetings} meeting(s) booked. {videos} video(s) filmed.
Running total this week: {weekly_outreach}/500.
Keep going.
```

**Response Template — Below Target (outreach > 0 and < 100):**
```
Logged. {outreach} outreach (target: 100) — {100 - outreach} short.
What got in the way?
Volume solves all problems. Tomorrow: make up the gap.
Weekly total: {weekly_outreach}/500.
```

**Response Template — Above Target (outreach >= 120):**
```
{outreach} outreach — ABOVE TARGET.
This is how you build momentum.
"Simple scales. Fancy fails." — Hormozi
Weekly total: {weekly_outreach}/500.
```

**Response Template — Zero Outreach:**
```
Logged. 0 outreach today.
{meetings} meeting(s), {videos} video(s), {content} content.
Everyone has off days. Reset tonight, attack tomorrow.
```

#### Rule 2a: Milestone Check (runs after EOD log)

After logging EOD numbers, check:

```python
# Cumulative outreach
cumulative_outreach = sum(all Daily_Log Outreach_Count)
if cumulative_outreach >= 500 and not milestone_achieved(6):
    trigger_milestone(6, {"cumulative_outreach": cumulative_outreach})

if cumulative_outreach >= 1000 and not milestone_achieved("outreach_1000"):
    # Bonus milestone — not in original 10 but worth celebrating
    pass

# First meeting ever
cumulative_meetings = sum(all Daily_Log Meetings_Booked)
if cumulative_meetings == 1 and not milestone_achieved(1):
    trigger_milestone(1, {"first_meeting_date": today})
```

**trigger_milestone()** makes an HTTP POST to the Milestone-Celebration-Engine n8n webhook:
```
POST https://n8n.marceausolutions.com/webhook/milestone-celebration
Content-Type: application/json
{
  "milestone_id": 6,
  "data": { "cumulative_outreach": 512 }
}
```

---

### Rule 3: Status/Dashboard Commands

**Pattern**: Message matches any of these keywords (case-insensitive):

| Keyword(s) | Response Type |
|------------|---------------|
| `status`, `dashboard`, `how am I doing`, `numbers` | Current week metrics + 90-day progress |
| `scorecard` | Full weekly summary (same as Sunday report format) |
| `goals` | 90-day goal progress only |

**Regex**: `^\s*(status|dashboard|how am i doing|numbers|scorecard|goals)\s*[?]?\s*$` (case-insensitive)

#### "status" Response
```
Day {Y}/90 | Week {X}/12

This week so far:
  Outreach: {weekly_total} / 500
  Meetings: {count} / 3-5
  Videos: {count} / 2

90-day progress:
  Clients: {current}/3
  Revenue: ${mrr}/$3,000
  YouTube: {subs}/500
```

#### "scorecard" Response
Full weekly summary in the same format as the Sunday Weekly-Accountability-Report message (see main spec).

#### "goals" Response
```
90-DAY GOALS (Day {Y}/84)

1. 3 AI clients: {current}/3 ({pct}%)
2. 500 YouTube subs: {current}/500 ({pct}%)
3. Digital product live: {status}
4. Group coaching forming: {waitlist}/5 signups
5. $3K/mo revenue: ${mrr}/$3,000 ({pct}%)

Days remaining: {remaining}
```

**Data Sources**: All fetched from Google Sheets (Scorecard) + Stripe API at query time.

---

### Rule 4: Single Large Number (Outreach-Only Shortcut)

**Pattern**: Single number > 10 (not an energy level).

**Regex**: `^\s*(\d+)\s*$` where parsed integer > 10

**Context Check**: Only if the last outbound message (within 4 hours) was an EOD check-in prompt.

**Action**:
1. Interpret as outreach count only
2. Log to Daily Log: `Outreach_Count` = the number, others = 0
3. Reply: "Logged {n} outreach. Send meetings, videos, content numbers if you have them — or I'll keep zeros."

**Follow-up**: If William replies within 30 minutes with 3 comma-separated numbers, update the same row:
- Regex for follow-up: `^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$`
- Maps to: meetings, videos, content

---

### Rule 5: Free-Text Note

**Pattern**: Any message that starts with `note:` or `notes:` (case-insensitive).

**Regex**: `^\s*notes?:\s*(.+)$` (case-insensitive, dotall)

**Action**:
1. Append the text after "note:" to today's Daily Log row → `Notes` column
2. Reply: "Noted."

---

### Rule 6: Training Session Log

**Pattern**: `trained`, `trained today`, `workout done`, `gym done`, `session done`

**Regex**: `^\s*(trained|trained today|workout done|gym done|session done)\s*$` (case-insensitive)

**Action**:
1. Set today's Daily Log → `Training_Session` = true
2. Reply: "Training logged. {weekday_training_count}/5 this week."

---

### Rule 7: "done" Shortcut

**Pattern**: Message is just `done` (case-insensitive).

**Regex**: `^\s*done\s*$`

**Context Check**: If last outbound was morning check-in → log energy as 5 (neutral). If last outbound was EOD prompt → reply "Done with what? Send your numbers: outreach, meetings, videos, content."

---

### Rule 8: Correction

**Pattern**: `fix`, `correct`, `update` followed by a field name and value.

**Examples**:
- "fix outreach 95" → update today's Outreach_Count to 95
- "correct meetings 2" → update today's Meetings_Booked to 2

**Regex**: `^\s*(fix|correct|update)\s+(outreach|meetings|videos|content|energy)\s+(\d+)\s*$`

**Action**:
1. Update the specified field in today's Daily Log row
2. Reply: "Updated {field} to {value} for today."

---

## Context Tracking

Clawdbot needs to track the **last outbound accountability message** to William, so it can interpret ambiguous replies (like a bare number).

### Implementation

Store in memory (mem0 or local state):
```json
{
  "last_accountability_message": {
    "type": "morning_checkin" | "eod_prompt" | "weekly_summary",
    "timestamp": "2026-03-17T06:45:00-04:00",
    "expecting_reply": true
  }
}
```

This is set by the n8n workflows when they send a message, via a secondary webhook call:
```
POST https://34.193.98.97:5020/api/v1/memories/
{
  "data": "last_accountability_message: morning_checkin at 2026-03-17T06:45:00",
  "user_id": "william",
  "metadata": { "type": "accountability_context" }
}
```

Or simpler: Clawdbot can check its own Telegram message history to see if the last bot message (within 4 hours) was a check-in.

---

## Google Sheets Write Operations

### Append Row (new day, morning energy)
```
POST https://sheets.googleapis.com/v4/spreadsheets/{SCORECARD_ID}/values/Daily_Log!A:J:append
?valueInputOption=USER_ENTERED

{
  "values": [[
    "2026-03-17",  // Date
    1,              // Day_Number
    1,              // Week_Number
    "Monday",       // Day_of_Week
    7,              // Morning_Energy
    "",             // Outreach_Count (empty until EOD)
    "",             // Meetings_Booked
    "",             // Videos_Filmed
    "",             // Content_Posted
    ""              // Notes
  ]]
}
```

### Update Row (EOD numbers for existing day)
```
PUT https://sheets.googleapis.com/v4/spreadsheets/{SCORECARD_ID}/values/Daily_Log!F{row}:I{row}
?valueInputOption=USER_ENTERED

{
  "values": [[87, 1, 2, 3]]
}
```

### Read Weekly Totals
```
GET https://sheets.googleapis.com/v4/spreadsheets/{SCORECARD_ID}/values/Daily_Log!A:I
```
Then filter in code where `Week_Number == currentWeek` and sum.

---

## Edge Cases

| Scenario | Handling |
|----------|----------|
| William replies "7" at 2pm (no recent check-in) | Falls through to general Clawdbot AI handler — NOT logged as energy |
| William replies "87, 1, 2, 3" at 8am | Still logged as EOD numbers (time doesn't gate EOD logging, only context) |
| William sends "87,1,2,3" (no spaces) | Regex handles optional whitespace — valid parse |
| William sends "87 1 2 3" (spaces, no commas) | Does NOT match Rule 2. Falls through. Clawdbot AI may ask "Did you mean 87, 1, 2, 3?" |
| William sends "status" in the middle of a conversation | Accountability parser catches it (Rule 3) before general handler |
| William sends a message that looks like numbers but is part of a conversation | Context check prevents false positives — only parse as accountability if recent check-in prompt exists |
| Two EOD submissions in one day | Second submission overwrites the first (UPDATE, not APPEND) |
| Missing a day entirely | Row stays empty or absent. Weekly summary counts it as zero. No nagging. |
| Weekend messages | Status/goals/scorecard commands work 7 days a week. Energy/EOD logging only on weekdays (Mon-Fri). |

---

## Implementation Notes

1. **No new EC2 services** — this is code added to Clawdbot's existing message handler
2. **Google Sheets auth** — Clawdbot already has Sheets API credentials on EC2
3. **Stripe API** — credentials in `.env` on EC2 (same as used by revenue-report.py)
4. **Parse order matters** — Rules 1-8 evaluated in order; first match wins
5. **Context window** — 4 hours. After 4 hours, bare numbers are NOT interpreted as accountability replies.
6. **All Sheets operations use numeric GIDs** (mode:id pattern, matching n8n convention)
7. **Logging** — Every parsed reply should log to EC2 syslog: `clawdbot: accountability_parse type=eod outreach=87 meetings=1 videos=2 content=3`

---

## Activation Checklist

- [ ] Accountability parser code added to Clawdbot message handler
- [ ] Rule 1 (energy level) tested: send "7" after morning check-in → logged + response
- [ ] Rule 2 (EOD numbers) tested: send "87, 1, 2, 3" after EOD prompt → logged + response
- [ ] Rule 3 (status commands) tested: send "status" → current metrics returned
- [ ] Rule 4 (single large number) tested: send "47" after EOD prompt → logged as outreach
- [ ] Rule 5 (notes) tested: send "note: had a great meeting with HVAC prospect"
- [ ] Rule 6 (training) tested: send "trained" → training logged
- [ ] Rule 7 (done) tested: send "done" → context-appropriate response
- [ ] Rule 8 (correction) tested: send "fix outreach 95" → updated
- [ ] Context tracking working: bare numbers only parsed when recent check-in exists
- [ ] Milestone check working: EOD log triggers milestone webhook when thresholds crossed
- [ ] Google Sheets writes verified: Daily Log rows appearing correctly
- [ ] Edge case: no false positives in normal conversation
- [ ] Clawdbot systemd service restarted and stable after code change
