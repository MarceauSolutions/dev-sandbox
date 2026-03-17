# Clawdbot Accountability System — Complete Specification

> **System**: Telegram-based daily accountability via Clawdbot (@w_marceaubot)
> **User**: William Marceau (Telegram chat ID: `5692454753`)
> **Platform**: n8n workflows + Clawdbot reply handler on EC2 (34.193.98.97)
> **Start Date**: March 17, 2026 (Monday of Week 1)
> **End Date**: June 7, 2026 (Sunday of Week 12)
> **Total Duration**: 84 days / 12 weeks

---

## Design Principles (E10 Best-Path Evaluation)

1. **Conversational** — Telegram, not terminal. William never opens a spreadsheet.
2. **Mobile-first** — All messages readable on phone without scrolling horizontally.
3. **Automatic** — Comes to him. He never initiates the check-in.
4. **Low-friction** — Replies like "47" or "87, 1, 2, 3" or "done". No structured forms.
5. **Usable on low-energy days** — Single number replies are valid. Clawdbot infers context from time of day.

---

## Interaction Flow Overview

```
6:45am ET (Mon-Fri)  →  Morning Check-In Message  →  William replies: energy level (1-10)
7:00pm ET (Mon-Fri)  →  EOD Report Prompt          →  William replies: "87, 1, 2, 3"
7:00pm ET (Sunday)   →  Weekly Summary              →  (no reply needed)
Anytime              →  William texts "status"       →  Current metrics returned
Milestone hit        →  Celebration message           →  (no reply needed)
```

---

## 1. Morning Check-In (6:45am ET, Mon-Fri)

### Trigger
n8n workflow `Morning-Accountability-Checkin` fires at cron `0 45 6 * * 1-5` (6-field, America/New_York).

### Message Format by Day

All messages include the day counter and a clear prompt for an energy level reply.

#### Monday — Week Opener
```
Week {X}/12. Day {Y}/90.

AI Services: {current_clients} client(s) (goal: 3)
Revenue: ${mrr}/mo (goal: $3K)

TODAY: Outreach blitz + offer assets.
What's your energy level? (1-10)
```

#### Tuesday — Content Day
```
Day {Y}/90. Content day.

Film topic: {next_video_topic}
Outreach blitz first — 100 minimum.

Energy? (1-10)
```

#### Wednesday — Naples Day
```
Day {Y}/90. Naples day.

5 businesses in person.
Pipeline: {prospect_count} prospects.

Energy? (1-10)
```

#### Thursday — Outreach + Film Day #2
```
Day {Y}/90. Outreach + Film Day #2.

{meetings_this_week} meetings booked this week (target: 3-5).
{daysRemaining} days left in the plan.

Energy? (1-10)
```

#### Friday — Scorecard Day
```
Day {Y}/90. Lighter day — 50 outreach.

This week:
  Outreach: {outreach_total}
  Meetings: {meetings}
  Videos: {videos}

How are you feeling? (1-10)
```

### Reply Handling
- William replies with a single number (1-10)
- Clawdbot logs it to Scorecard Google Sheet → **Daily Log** tab → `Morning_Energy` column
- Clawdbot responds with a brief acknowledgment based on energy level:
  - **8-10**: "High energy day. Channel it into outreach volume."
  - **5-7**: "Solid. Execute the fundamentals today."
  - **1-4**: "Low energy. Do the minimum: 50 outreach, 1 video. Rest is legit."

### Data Sources for Morning Message

| Variable | Source | Method |
|----------|--------|--------|
| `X` (week number) | Calculated | `Math.ceil((daysSinceStart + 1) / 7)` where start = 2026-03-17 |
| `Y` (day number) | Calculated | `daysSinceStart + 1` |
| `current_clients` | Google Sheets → 90-Day Goals tab | Row 1, "Current" column |
| `mrr` | Stripe API | `GET /v1/subscriptions?status=active` → sum plan amounts |
| `next_video_topic` | Google Sheets → Content Calendar tab | Next row where "Published" is blank |
| `prospect_count` | Google Sheets → Pipeline tab (Outreach Tracker sheet) | COUNT where Status != "Closed Won/Lost" |
| `meetings_this_week` | Google Sheets → Daily Log tab | SUM of `Meetings_Booked` where date is this week |
| `outreach_total` | Google Sheets → Daily Log tab | SUM of `Outreach_Count` where date is this week |
| `videos` | Google Sheets → Daily Log tab | SUM of `Videos_Filmed` where date is this week |
| `daysRemaining` | Calculated | `84 - daysSinceStart` |

---

## 2. End-of-Day Check-In (7:00pm ET, Mon-Fri)

### Trigger
n8n workflow `EOD-Accountability-Checkin` fires at cron `0 0 19 * * 1-5` (6-field, America/New_York).

### Outbound Message
```
EOD report time.

Reply with your numbers (comma-separated):
outreach, meetings, videos, content posted

Example: 87, 1, 2, 3
```

### Reply Handling
- William replies: `87, 1, 2, 3`
- Clawdbot parses: outreach=87, meetings=1, videos=2, content=3
- Logs all four values to Scorecard Google Sheet → **Daily Log** tab
- Responds with contextual feedback:

#### Response Templates

**On target or above (outreach >= 100):**
```
Logged. {outreach} outreach (target: 100) — solid.
{meetings} meeting(s) booked. {videos} video(s) filmed.
Running total this week: {weekly_outreach}/500.
Keep going.
```

**Below target (outreach < 100 but > 0):**
```
Logged. {outreach} outreach (target: 100) — {shortfall} short.
What got in the way?
Volume solves all problems. Tomorrow: make up the gap.
Weekly total: {weekly_outreach}/500.
```

**Above target (outreach >= 120):**
```
{outreach} outreach — ABOVE TARGET.
This is how you build momentum.
"Simple scales. Fancy fails." — Hormozi
Weekly total: {weekly_outreach}/500. {emoji}
```

**Minimal reply (just a single number, no commas):**
- If time is after 5pm ET and the number is > 10: interpret as outreach count only
- Log outreach, set meetings/videos/content to 0
- Reply: "Logged {number} outreach. Reply with meetings, videos, content if you have them — or I'll log zeros."

### Milestone Check (inline)
After logging, Clawdbot checks if any milestone threshold was crossed:
- Cumulative outreach >= 500 → trigger Milestone 6
- First meeting ever (cumulative meetings == 1) → trigger Milestone 1
- If milestone triggered → call Milestone-Celebration-Engine webhook

---

## 3. Sunday Weekly Summary (7:00pm ET)

### Trigger
n8n workflow `Weekly-Accountability-Report` fires at cron `0 0 19 * * 0` (6-field, America/New_York).

### Data Collection
- Fetch all Daily Log rows where `Week_Number` == current week
- Fetch 90-Day Goals current values
- Fetch Stripe MRR via API
- Calculate all totals and averages

### Message Format
```
WEEK {X}/12 SCORECARD

AI SERVICES:
  Outreach: {total}/500 {status_emoji}
  Meetings: {count}/3-5 {status_emoji}
  Proposals: {count}
  Clients: {current} (goal: 3 by week 12)
  Revenue: ${mrr}/mo

FITNESS CONTENT:
  Videos published: {count}/2 {status_emoji}
  Shorts posted: {count}/4 {status_emoji}

HEALTH:
  Training sessions: {count}/5
  Avg energy: {avg}/10

Win of the week: {auto_win}
Focus area: {auto_focus}

Next week priority: {auto_priority}
```

### Status Emoji Logic
| Condition | Emoji |
|-----------|-------|
| >= 100% of target | `[ON TRACK]` |
| >= 75% of target | `[CLOSE]` |
| >= 50% of target | `[BEHIND]` |
| < 50% of target | `[OFF TRACK]` |

### Auto-Detection Logic

**Win of the week**: Highest metric vs. target percentage. Example: If outreach was 110% of target but meetings were only 60%, the win is outreach.

**Focus area**: Lowest metric vs. target percentage. "Meetings at 60% of target — book more discovery calls."

**Next week priority**: Based on focus area + week number:
- Weeks 1-4: Always "Volume. More outreach."
- Weeks 5-8: "Convert pipeline. Follow up on proposals."
- Weeks 9-12: "Close deals. Upsell existing clients."

---

## 4. Ad-Hoc Status Check (Anytime)

### Trigger Words
William texts Clawdbot any of: `status`, `dashboard`, `how am I doing`, `scorecard`, `goals`, `numbers`

### Response by Keyword

#### "status" / "dashboard" / "how am I doing" / "numbers"
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

#### "scorecard"
Returns the full weekly summary format (same as Sunday report) for the current in-progress week.

#### "goals"
```
90-DAY GOALS (Day {Y}/84)

1. 3 AI clients: {current}/3 ({pct}%)
2. 500 YouTube subs: {current}/500 ({pct}%)
3. Digital product live: {status}
4. Group coaching forming: {waitlist}/5 signups
5. $3K/mo revenue: ${mrr}/$3,000 ({pct}%)

Days remaining: {remaining}
```

---

## 5. Milestone Celebrations

Defined in `docs/milestone-celebrations.md` (already exists — 10 milestones defined). The Telegram adaptation:

- All celebration messages are sent via Telegram instead of SMS
- Message format stays the same but uses Telegram markdown for emphasis
- Milestone-Celebration-Engine n8n workflow handles delivery

### Milestone Triggers (Clawdbot-side)
After every EOD log, Clawdbot checks:
1. Cumulative outreach thresholds (500, 1000, 2000)
2. First meeting (cumulative meetings == 1)
3. Client count transitions (0→1, etc.)

After every weekly summary, n8n checks:
1. MRR thresholds ($1K, $3K)
2. YouTube subscriber thresholds (100, 500)
3. Week 12 completion

---

## n8n Workflow Specifications

### Workflow 1: Morning-Accountability-Checkin

| Field | Value |
|-------|-------|
| **Name** | `Morning-Accountability-Checkin` |
| **Trigger** | Schedule Trigger, cron `0 45 6 * * 1-5`, timezone `America/New_York` |
| **Error Workflow** | Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`) |

**Node Chain:**
```
Schedule Trigger
  → Code: Calculate Context
  → Google Sheets: Fetch Daily Log (this week's rows)
  → Google Sheets: Fetch 90-Day Goals
  → HTTP Request: Stripe MRR (GET /v1/subscriptions?status=active)
  → Code: Calculate Variables (week/day numbers, totals, MRR sum)
  → Switch: Day of Week Router (Mon=1 through Fri=5)
  → [5 branches] Set: Compose Day-Specific Message
  → Telegram: Send Message (chat ID 5692454753, parse_mode: Markdown)
```

**Code Node: Calculate Context**
```javascript
const planStartDate = new Date('2026-03-17T00:00:00-04:00');
const now = new Date();
const msPerDay = 86400000;
const daysSinceStart = Math.floor((now - planStartDate) / msPerDay);
const dayNumber = Math.max(1, daysSinceStart + 1);
const weekNumber = Math.min(12, Math.max(1, Math.ceil(dayNumber / 7)));
const daysRemaining = Math.max(0, 84 - daysSinceStart);
const dayOfWeek = now.getDay(); // 0=Sun, 1=Mon...

return [{
  json: {
    dayNumber,
    weekNumber,
    daysRemaining,
    dayOfWeek,
    weekStartDate: new Date(planStartDate.getTime() + (weekNumber - 1) * 7 * msPerDay).toISOString().split('T')[0]
  }
}];
```

**Google Sheets Nodes:**
- Sheet ID: `${SCORECARD_SPREADSHEET_ID}` (from .env)
- MUST use `mode:id` with numeric GIDs (never mode:name)
- Daily Log tab GID: set after sheet creation
- 90-Day Goals tab GID: set after sheet creation

**Stripe MRR Node:**
- Type: HTTP Request
- Method: GET
- URL: `https://api.stripe.com/v1/subscriptions?status=active&limit=100`
- Auth: HTTP Header Auth → `Authorization: Bearer ${STRIPE_SECRET_KEY}`
- onError: `continueRegularOutput` (MRR display is nice-to-have, not critical)

**Telegram Send Node:**
- Type: Telegram node
- Chat ID: `5692454753`
- Parse Mode: Markdown
- Credential: Clawdbot Telegram credential (`RlAwU3xzcX4hifgj`)

---

### Workflow 2: EOD-Accountability-Checkin

| Field | Value |
|-------|-------|
| **Name** | `EOD-Accountability-Checkin` |
| **Trigger** | Schedule Trigger, cron `0 0 19 * * 1-5`, timezone `America/New_York` |
| **Error Workflow** | Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`) |

**Node Chain:**
```
Schedule Trigger
  → Code: Calculate day/week context
  → Telegram: Send EOD Prompt (chat ID 5692454753)
```

The EOD prompt is a fixed message (no data fetch needed):
```
EOD report time.

Reply with your numbers (comma-separated):
outreach, meetings, videos, content posted

Example: 87, 1, 2, 3
```

**Reply handling** is NOT in this workflow. It happens in Clawdbot's message handler (see `docs/clawdbot-reply-handler-spec.md`).

---

### Workflow 3: Weekly-Accountability-Report

| Field | Value |
|-------|-------|
| **Name** | `Weekly-Accountability-Report` |
| **Trigger** | Schedule Trigger, cron `0 0 19 * * 0`, timezone `America/New_York` |
| **Error Workflow** | Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`) |

**Node Chain:**
```
Schedule Trigger
  → Code: Calculate week number
  → Google Sheets: Fetch ALL Daily Log rows for this week
  → Google Sheets: Fetch 90-Day Goals
  → HTTP Request: Stripe MRR
  → Code: Calculate totals, averages, vs targets
  → Code: Auto-detect win + focus area + next priority
  → Code: Compose weekly summary message
  → Telegram: Send Weekly Summary (chat ID 5692454753)
  → Google Sheets: Write to Weekly Summary tab
  → Code: Check milestone conditions
  → IF milestone triggered → HTTP Request: POST to Milestone-Celebration-Engine webhook
```

**Totals Calculation Logic (Code Node):**
```javascript
// Input: dailyLogRows (array of this week's daily entries)
const totals = {
  outreach: dailyLogRows.reduce((sum, r) => sum + (r.Outreach_Count || 0), 0),
  meetings: dailyLogRows.reduce((sum, r) => sum + (r.Meetings_Booked || 0), 0),
  videos: dailyLogRows.reduce((sum, r) => sum + (r.Videos_Filmed || 0), 0),
  content: dailyLogRows.reduce((sum, r) => sum + (r.Content_Posted || 0), 0),
  training: dailyLogRows.filter(r => r.Training_Session === true).length,
  avgEnergy: dailyLogRows.reduce((sum, r) => sum + (r.Morning_Energy || 0), 0) / dailyLogRows.length
};

// Targets
const targets = {
  outreach: 500,
  meetings_min: 3, meetings_max: 5,
  videos: 2,
  shorts: 4,
  training: 5,
  energy: 6
};

// Status detection
function statusEmoji(actual, target) {
  const pct = actual / target;
  if (pct >= 1.0) return '[ON TRACK]';
  if (pct >= 0.75) return '[CLOSE]';
  if (pct >= 0.50) return '[BEHIND]';
  return '[OFF TRACK]';
}

// Win = highest % vs target
// Focus = lowest % vs target
const metrics = [
  { name: 'Outreach', pct: totals.outreach / targets.outreach },
  { name: 'Meetings', pct: totals.meetings / targets.meetings_min },
  { name: 'Videos', pct: totals.videos / targets.videos },
  { name: 'Training', pct: totals.training / targets.training }
];
metrics.sort((a, b) => b.pct - a.pct);
const win = metrics[0].name;
const focus = metrics[metrics.length - 1].name;
```

---

### Workflow 4: Milestone-Celebration-Engine

| Field | Value |
|-------|-------|
| **Name** | `Milestone-Celebration-Engine` |
| **Trigger** | Webhook (internal), path: `/webhook/milestone-celebration` |
| **Error Workflow** | Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`) |

**Node Chain:**
```
Webhook Trigger (POST, body: { milestone_id: 1-10, data: {...} })
  → Google Sheets: Check Milestones tab (has this been achieved already?)
  → IF already achieved → Stop (no duplicate celebrations)
  → Switch: milestone_id (1-10)
  → [10 branches] Set: Compose celebration message
  → Telegram: Send Celebration (chat ID 5692454753)
  → Google Sheets: Write to Milestones tab (Achieved_Date = now, Celebration_Sent = true)
```

**Webhook Input Schema:**
```json
{
  "milestone_id": 6,
  "data": {
    "cumulative_outreach": 512,
    "conversion_rate": "2.3%"
  }
}
```

**Celebration messages**: Use the 10 messages already defined in `docs/milestone-celebrations.md`, but deliver via Telegram instead of SMS. All messages remain identical in content.

---

## Google Sheets Integration

### Sheet: Marceau Execution System — Scorecard
- **Spreadsheet ID**: Store in `.env` as `SCORECARD_SPREADSHEET_ID`
- **Structure**: Defined in `docs/scorecard-sheet-auto-structure.json`
- **All n8n nodes MUST use `mode:id` with numeric GIDs** (never mode:name or mode:list)

### Tabs Referenced by This System

| Tab | Purpose | Written By |
|-----|---------|------------|
| Daily Log | Morning energy + EOD numbers | Clawdbot reply handler |
| Weekly Summary | Auto-calculated week totals | Weekly-Accountability-Report workflow |
| 90-Day Goals | Goal tracking + progress | Manual + weekly auto-update |
| Milestones | Achievement log | Milestone-Celebration-Engine |
| Content Calendar | Video topics for Tuesday messages | Manual (pre-populated) |

---

## Clawdbot Configuration

### What Changes on Clawdbot (EC2)

Clawdbot's existing message handler (`agent_bridge_api.py` or equivalent) needs a new parsing layer for accountability replies. This is specified in `docs/clawdbot-reply-handler-spec.md`.

**No new services or processes are needed.** Clawdbot already:
- Runs as a systemd service on EC2
- Receives all Telegram messages from William
- Has access to Google Sheets API credentials
- Can make HTTP requests (for Stripe, n8n webhooks)

The reply handler is an enhancement to Clawdbot's existing message processing, not a new service.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Stripe API fails | Use last known MRR from Sheets. Show "MRR: (last known) ${amount}" |
| Google Sheets read fails | Send message without data: "Morning check-in. Data fetch failed — logging anyway. Energy? (1-10)" |
| Google Sheets write fails | Queue the write, retry in 5 min. Alert to Telegram: "Failed to log your numbers. Will retry." |
| Telegram send fails | Self-Annealing fires. n8n retries once. If still fails → log error, skip this check-in. |
| William doesn't reply by 9am (morning) | No follow-up. Not a nag system — it's accountability. |
| William doesn't reply by 10pm (EOD) | At 10pm, send: "No EOD numbers yet. Reply anytime tonight or I'll log zeros for today." |
| Clawdbot can't parse reply | Reply: "Didn't catch that. Send a number (1-10) for energy, or 4 numbers comma-separated for EOD (outreach, meetings, videos, content)." |

---

## Activation Checklist

- [ ] Scorecard Google Sheet created with all tabs (Daily Log, Weekly Summary, 90-Day Goals, Milestones, Content Calendar)
- [ ] `SCORECARD_SPREADSHEET_ID` added to `.env`
- [ ] All tab GIDs documented and added to `memory/sheets-gids.md`
- [ ] n8n workflow: Morning-Accountability-Checkin created and tested
- [ ] n8n workflow: EOD-Accountability-Checkin created and tested
- [ ] n8n workflow: Weekly-Accountability-Report created and tested
- [ ] n8n workflow: Milestone-Celebration-Engine created and tested
- [ ] Clawdbot reply handler updated (energy level parsing, EOD parsing, status commands)
- [ ] All 4 workflows wired to Self-Annealing-Error-Handler
- [ ] All 4 workflows use Telegram (not SMS) for delivery
- [ ] All Google Sheets nodes use mode:id with numeric GIDs
- [ ] All cron expressions are 6-field format
- [ ] Timezone set to America/New_York on all schedule triggers
- [ ] End-to-end test: morning message → reply energy → EOD prompt → reply numbers → verify Sheets updated
- [ ] All 4 workflows added to SYSTEM-STATE.md
- [ ] Session history updated
