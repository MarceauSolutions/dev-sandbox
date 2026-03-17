# Morning Accountability SMS — n8n Workflow Specification

> Workflow Name: `Morning-Accountability-SMS`
> Purpose: Daily 6:45am kick in the ass. Pull live data, send targeted SMS based on day of week.
> Trigger: Cron, Mon-Fri, 6:45am ET

---

## Workflow Architecture

```
[Cron Trigger] → [Get Day of Week] → [Switch Node: Day Router] → [Per-Day Branch] → [Fetch Live Data] → [Compose Message] → [Twilio SMS]
```

## Node Specifications

### Node 1: Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 45 6 * * 1-5` (6-field n8n format: sec min hour dom mon dow)
- **Timezone:** America/New_York
- **Note:** Mon=1, Fri=5. No weekends — those are rest/review days.

### Node 2: Get Context Data
- **Type:** Function (Code node)
- **Purpose:** Calculate week number, days remaining, pull what we need
- **Logic:**
```javascript
const planStartDate = new Date('2026-03-17'); // Monday of Week 1
const today = new Date();
const dayOfWeek = today.getDay(); // 0=Sun, 1=Mon...
const msPerDay = 86400000;
const daysSinceStart = Math.floor((today - planStartDate) / msPerDay);
const weekNumber = Math.min(12, Math.max(1, Math.ceil((daysSinceStart + 1) / 7)));
const daysRemaining = Math.max(0, 84 - daysSinceStart);
const percentComplete = Math.min(100, Math.round((daysSinceStart / 84) * 100));

return [{
  json: {
    dayOfWeek,
    weekNumber,
    daysRemaining,
    percentComplete,
    dayName: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][dayOfWeek]
  }
}];
```

### Node 3: Fetch Scorecard Data (Google Sheets)
- **Type:** Google Sheets node
- **Operation:** Read rows
- **Sheet ID:** `${SCORECARD_SPREADSHEET_ID}` (set after sheet creation)
- **Tab:** "Weekly Scorecard" (use GID, mode:id)
- **Range:** Last populated row (current week's data)
- **Extract:** Outreach Messages Sent, Clients Closed, MRR, Cumulative Revenue

### Node 4: Fetch Stripe MRR (optional enrichment)
- **Type:** HTTP Request
- **URL:** `https://api.stripe.com/v1/subscriptions?status=active`
- **Auth:** Bearer `${STRIPE_SECRET_KEY}`
- **Purpose:** Calculate live MRR from active subscriptions
- **Fallback:** If Stripe call fails, use Google Sheets MRR value

### Node 5: Switch — Day Router
- **Type:** Switch node
- **Route on:** `{{$node["Get Context Data"].json.dayOfWeek}}`
- **Routes:**
  - `1` → Monday branch
  - `2` → Tuesday branch
  - `3` → Wednesday branch
  - `4` → Thursday branch
  - `5` → Friday branch

### Node 6a-6e: Message Composers (one per day)

#### Monday — Week Opener
```
Week {{weekNumber}} of 12.

Target: 100 outreach actions today. You have {{clientCount}} client(s). Goal: 3 by week 12.

MRR: ${{mrr}} / $3,000 target.

Embrace the Pain. — WM
```

#### Tuesday — Content Day
```
Content day. Film 2-3 videos. 100 outreach actions.

Every video you don't post is a person you don't help.

Week {{weekNumber}}/12 | {{daysRemaining}} days left.
```

#### Wednesday — Naples Day
```
Naples day. 5 businesses in person. Cold email list building.

The fortune is in the follow-up.

Outreach this week so far: {{weeklyOutreach}}.
Target: 500. Get after it.
```

#### Thursday — Outreach + Film Day #2
```
Outreach + Film Day #2.

{{daysRemaining}} days until 90-day milestone.
You are {{percentToRevenue}}% to revenue goal.

"You are one offer away." — Hormozi
```

#### Friday — Review Day
```
Review day. Fill out the scorecard.

This week: {{weeklyOutreach}} outreach | {{meetingsBooked}} meetings | ${{weeklyRevenue}} revenue.

What was the #1 bottleneck? Attack it Monday.

Week {{weekNumber}} complete. {{12 - weekNumber}} to go.
```

### Node 7: Twilio SMS Send
- **Type:** Twilio node
- **From:** `+18552399364` (TWILIO_PHONE_NUMBER)
- **To:** `+12393985676` (William's phone)
- **Body:** Output from the day's message composer

### Node 8: Error Handler (wire to Self-Annealing)
- **Type:** Error Trigger → Self-Annealing-Error-Handler
- **On failure:** Log to self-annealing, do NOT retry SMS (avoid duplicate messages)

---

## Data Sources

| Data Point | Source | How to Get |
|---|---|---|
| Week number | Calculated from plan start date (2026-03-17) | Code node |
| Days remaining | 84 - days since start | Code node |
| Client count | Google Sheets "Weekly Scorecard" → Clients Closed cumulative | Sheets node |
| MRR | Stripe API → active subscriptions sum | HTTP Request |
| Weekly outreach | Google Sheets "Daily Tracker" → SUMIF this week | Sheets node |
| Meetings booked | Google Sheets "Weekly Scorecard" → current week | Sheets node |
| Weekly revenue | Stripe API or Sheets "Weekly Scorecard" | HTTP Request / Sheets |
| % to revenue goal | (Current MRR / 3000) * 100 | Code node |

---

## Implementation Notes

1. **Create the workflow in n8n** at `https://n8n.marceausolutions.com`
2. **Wire error output** to Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`)
3. **Test each day's message** by temporarily setting cron to fire in 2 minutes
4. **Google Sheets node** must use `mode:id` (never mode:name — see n8n gotchas in MEMORY.md)
5. **6-field cron required** — 5-field silently fails in n8n
6. **Twilio credential ID** in n8n: use the existing Twilio credential (same one SMS-Response-Handler-v2 uses)

---

## Activation Checklist

- [ ] Scorecard Google Sheet created (need SCORECARD_SPREADSHEET_ID)
- [ ] n8n workflow created with all nodes
- [ ] Twilio node tested with a manual trigger
- [ ] Each day's message template verified
- [ ] Error handler wired to Self-Annealing
- [ ] Workflow activated
- [ ] Added to SYSTEM-STATE.md workflow inventory
