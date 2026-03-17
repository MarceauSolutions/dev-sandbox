# Accountability System — Clawdbot Knowledge

> Add this section to Clawdbot's KNOWLEDGE_BASE.md on EC2.
> This enables Clawdbot to parse William's accountability replies and log them to Google Sheets.

## Accountability System Overview

William is running a 90-day execution plan starting March 17, 2026 (Day 1).
- **Morning**: n8n sends a check-in message asking for energy level (1-10)
- **Evening**: n8n sends an EOD prompt asking for numbers
- **William replies**: Clawdbot parses the reply and logs to Google Sheets

## Scorecard Sheet
- **Sheet ID**: `1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o`
- **Tab: Daily Log** (GID: 1874200900) — columns: Date, Day_Number, Week_Number, Day_of_Week, Morning_Energy, Outreach_Count, Meetings_Booked, Videos_Filmed, Content_Posted, Training_Done, Notes

## Reply Parsing Rules (Priority Order)

1. **Single number 1-10**: Log as Morning_Energy for today
   - Example: "7" → energy level 7

2. **Four comma-separated numbers**: Log as EOD report
   - Format: outreach, meetings, videos, content
   - Example: "87, 1, 2, 3" → 87 outreach, 1 meeting, 2 videos, 3 content posted
   - Respond with context: compare to targets, running weekly total

3. **"status" / "dashboard" / "how am I doing"**: Return current week metrics
   - Pull from Weekly Summary tab, current week row
   - Show: outreach total, meetings, clients, revenue, videos, energy avg

4. **"scorecard"**: Return full weekly scorecard with targets

5. **"goals"**: Return 90-day goal progress from 90-Day Goals tab

6. **Large single number (>10)**: Log as outreach count only
   - Example: "47" → 47 outreach

7. **"trained" / "gym done"**: Mark Training_Done = TRUE for today

8. **"done"**: Context-dependent
   - If morning (before noon): log energy = 7 (default)
   - If evening (after 5pm): mark day complete

9. **"note: [text]"**: Log to Notes column for today

10. **"fix [field] [value]"**: Correct a previously logged value
    - Example: "fix outreach 95" → update today's outreach to 95

## Targets by Phase
- **Week 1-4**: Outreach 500/week, Meetings 3-5, Videos 2, Shorts 4
- **Month 2+**: Outreach 300/week, Meetings 5-10, Videos 2-3, Shorts 5+

## 90-Day Goals
1. 3 paying AI services clients
2. 500+ YouTube subscribers
3. 1 digital fitness product live ($19.99)
4. First group coaching cohort forming
5. $3,000/mo revenue

## Google Sheets API
Use the sheets API to append/update data. Auth via service account or OAuth token in .env.
- Append row: `POST /v4/spreadsheets/{sheetId}/values/Daily Log!A:K:append`
- Update cell: `PUT /v4/spreadsheets/{sheetId}/values/Daily Log!E{row}`

## Milestone Celebrations
When any of these conditions are met, send a celebration message:
1. First discovery call booked → "FIRST CALL BOOKED. This is where it starts."
2. First client signed → "CLIENT #1 SIGNED. The proof is building."
3. First paid client → "PAID CLIENT #1. Hormozi was right."
4. $1,000 MRR → "FIRST $1K MRR. The machine is working."
5. 100 YouTube subscribers → celebration message
6. 500 outreach messages cumulative → "500 messages. Your pitch is 10x better than message #1."
