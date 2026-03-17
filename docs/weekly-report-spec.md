# Weekly Report Automation — n8n Workflow Specification

> Workflow Name: `Weekly-Accountability-Report`
> Purpose: Sunday 7pm summary — numbers vs targets, wins, gaps, next week priorities
> Delivery: SMS + branded email
> Extends: Runs independently but complements Daily-Operations-Digest (`Hz05R5SeJGb4VNCl`)

---

## Workflow Architecture

```
[Cron: Sunday 7pm ET]
  → [Fetch Scorecard Data]
  → [Fetch Stripe Revenue]
  → [Fetch YouTube Stats (optional)]
  → [Calculate Metrics vs Targets]
  → [Determine Win/Gap/Priorities]
  → [Select Motivational Quote]
  → [Compose SMS Summary]
  → [Compose Email Summary]
  → [Send SMS via Twilio]
  → [Send Email via SMTP]
```

---

## Node Specifications

### Node 1: Cron Trigger
- **Type:** Schedule Trigger
- **Cron Expression:** `0 0 19 * * 0` (6-field: sec min hour dom mon dow, 0=Sunday)
- **Timezone:** America/New_York

### Node 2: Fetch Weekly Scorecard
- **Type:** Google Sheets
- **Sheet ID:** `${SCORECARD_SPREADSHEET_ID}`
- **Tab:** "Weekly Scorecard" (mode:id)
- **Operation:** Read — get current week row + target row
- **Also fetch:** "Daily Tracker" tab — this week's daily entries for detail

### Node 3: Fetch Stripe Revenue
- **Type:** HTTP Request
- **Calls:**
  1. `GET https://api.stripe.com/v1/balance` — current balance
  2. `GET https://api.stripe.com/v1/charges?created[gte]={{weekStartTimestamp}}&created[lte]={{weekEndTimestamp}}` — this week's charges
  3. `GET https://api.stripe.com/v1/subscriptions?status=active` — active MRR
- **Auth:** Bearer token from `STRIPE_SECRET_KEY`

### Node 4: Fetch YouTube Stats (Optional)
- **Type:** HTTP Request
- **URL:** `https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true`
- **Auth:** OAuth2 using YouTube credentials from .env
- **Purpose:** Get subscriber count, view count for the week
- **Fallback:** If unavailable, use manually entered value from Scorecard

### Node 5: Calculate Metrics (Code Node)
```javascript
// Inputs: scorecard data, stripe data, targets
const targets = {
  outreach: weekNumber <= 2 ? 500 : weekNumber <= 4 ? 500 : 300,
  meetings: weekNumber <= 2 ? 4 : 7,
  proposals: weekNumber <= 2 ? 2 : 4,
  clients: weekNumber <= 2 ? 1 : 1,
  mrr: weekNumber <= 2 ? 0 : weekNumber <= 4 ? 750 : 2000,
  videos: 2,
  shorts: 4,
  subscribers: weekNumber <= 4 ? 25 : weekNumber <= 8 ? 100 : 500,
  training: 4
};

// Compare actuals vs targets
const metrics = {};
for (const [key, target] of Object.entries(targets)) {
  const actual = scorecard[key] || 0;
  const pct = target > 0 ? Math.round((actual / target) * 100) : 100;
  metrics[key] = { actual, target, pct, status: pct >= 100 ? 'GREEN' : pct >= 60 ? 'YELLOW' : 'RED' };
}

// Find win (highest % above target) and gap (lowest % below target)
const sorted = Object.entries(metrics).sort((a, b) => b[1].pct - a[1].pct);
const win = sorted[0];
const gap = sorted[sorted.length - 1];

return [{ json: { metrics, win, gap, weekNumber, daysRemaining } }];
```

### Node 6: Select Motivational Quote (Code Node)
```javascript
const quotes = [
  { text: "You are one offer away.", author: "Alex Hormozi" },
  { text: "Volume solves all problems.", author: "Alex Hormozi" },
  { text: "The best time to plant a tree was 20 years ago. The second best time is now.", author: "Chinese Proverb" },
  { text: "Productized services take 1/100th the time of custom work.", author: "Nick Saraev" },
  { text: "Give away your best stuff for free. The paid product provides structure.", author: "Ryan Humiston" },
  { text: "The offer IS the business. If no one is buying, change the offer, not the effort.", author: "Alex Hormozi" },
  { text: "Consistency beats perfection. 2 good videos per week beats 1 perfect video per month.", author: "Ryan Humiston" },
  { text: "Retainers over projects. Monthly recurring revenue is the goal.", author: "Nick Saraev" },
  { text: "Your story IS the content. That's not a disadvantage — it's the most compelling story in fitness.", author: "Marceau Execution System" },
  { text: "Sell the outcome, not the automation. Clients don't care about n8n. They care about leads.", author: "Nick Saraev" },
  { text: "Speed to lead wins. Respond to every inquiry within 5 minutes.", author: "Alex Hormozi" },
  { text: "Embrace the Pain & Defy the Odds.", author: "William Marceau" }
];

const weekNumber = $input.first().json.weekNumber || 1;
const quote = quotes[(weekNumber - 1) % quotes.length];
return [{ json: { quote } }];
```

### Node 7: Compose SMS Summary (Code Node)
```javascript
const m = $input.first().json.metrics;
const win = $input.first().json.win;
const gap = $input.first().json.gap;
const week = $input.first().json.weekNumber;
const quote = $input.first().json.quote;

const statusEmoji = (s) => s === 'GREEN' ? '🟢' : s === 'YELLOW' ? '🟡' : '🔴';

const sms = `WEEK ${week}/12 REPORT

${statusEmoji(m.outreach.status)} Outreach: ${m.outreach.actual}/${m.outreach.target}
${statusEmoji(m.meetings.status)} Meetings: ${m.meetings.actual}/${m.meetings.target}
${statusEmoji(m.clients.status)} Clients: ${m.clients.actual}/${m.clients.target}
${statusEmoji(m.mrr.status)} MRR: $${m.mrr.actual}/$${m.mrr.target}
${statusEmoji(m.videos.status)} Videos: ${m.videos.actual}/${m.videos.target}
${statusEmoji(m.training.status)} Training: ${m.training.actual}/${m.training.target}

WIN: ${win[0]} at ${win[1].pct}%
FIX: ${gap[0]} at ${gap[1].pct}%

"${quote.text}" — ${quote.author}`;

return [{ json: { sms } }];
```

### Node 8: Compose Email (Code Node)
- **Subject:** `Week ${weekNumber}/12 — Marceau Execution System Report`
- **Body:** HTML-formatted version of the SMS with:
  - Color-coded bars for each metric (green/yellow/red)
  - Full breakdown table: Metric | Actual | Target | % | Status
  - Win of the week section (highlighted in gold)
  - Area needing attention (highlighted in red)
  - Next week's top 3 priorities (auto-suggested based on gaps)
  - Motivational closer with quote
  - Marceau Solutions branding (dark + gold, `#C9963C`)

### Node 9: Send SMS
- **Type:** Twilio
- **From:** `+18552399364`
- **To:** `+12393985676`
- **Body:** SMS from Node 7

### Node 10: Send Email
- **Type:** SMTP / Email Send
- **From:** `wmarceau@marceausolutions.com`
- **To:** `wmarceau@marceausolutions.com`
- **Subject:** From Node 8
- **Body:** HTML from Node 8
- **SMTP Config:** host=smtp.gmail.com, port=587, user=wmarceau@marceausolutions.com, pass from .env

### Node 11: Error Handler
- Wire to Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`)

---

## SMS Format (Character-Optimized for Twilio)

Max ~1600 chars per Twilio message (multi-segment). The template above runs ~450 chars — well within limits.

---

## Email Format — HTML Template Structure

```html
<div style="max-width:600px; margin:0 auto; font-family:Arial,sans-serif;">
  <div style="background:#333333; padding:20px; text-align:center;">
    <h1 style="color:#C9963C; margin:0;">Week X/12</h1>
    <p style="color:#f8fafc; margin:5px 0;">Marceau Execution System</p>
  </div>

  <div style="padding:20px;">
    <!-- Metric rows with color bars -->
    <!-- Win section (gold border) -->
    <!-- Gap section (red border) -->
    <!-- Top 3 priorities -->
  </div>

  <div style="background:#333333; padding:15px; text-align:center;">
    <p style="color:#C9963C; font-style:italic;">"Quote here"</p>
    <p style="color:#94a3b8; font-size:12px;">Marceau Solutions | Embrace the Pain & Defy the Odds</p>
  </div>
</div>
```

---

## Priority Auto-Suggestion Logic

Based on which metrics are RED or lowest percentage:
1. If outreach < 60% of target → "Priority: Hit 100 outreach actions EVERY day this week"
2. If meetings < 60% of target → "Priority: Improve your cold email hook — test 3 new subject lines"
3. If videos < 60% of target → "Priority: Batch film on your next HIGH energy day — 3 videos minimum"
4. If MRR < target and clients exist → "Priority: Upsell current clients to higher tier or add services"
5. If training < target → "Priority: Even on LOW days, do 20 minutes. Movement is medicine."

---

## Implementation Notes

1. **Create as new n8n workflow** — do NOT modify Daily-Operations-Digest
2. **Wire error output** to Self-Annealing
3. **Google Sheets nodes** must use mode:id (never mode:name)
4. **6-field cron** required for n8n
5. **Test** by manually triggering on a non-Sunday to verify data flow
6. **YouTube API** is optional — if not connected, skip gracefully and use Sheets value

---

## Activation Checklist

- [ ] Scorecard Google Sheet created with SCORECARD_SPREADSHEET_ID in .env
- [ ] n8n workflow created and all nodes wired
- [ ] SMS test sent successfully
- [ ] Email test sent successfully
- [ ] Error handler wired to Self-Annealing
- [ ] Workflow activated
- [ ] Added to SYSTEM-STATE.md
