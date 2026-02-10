<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 24: Daily/Weekly Digest System

**When**: Reviewing business operations or setting up automated digest delivery

**Purpose**: Aggregate data from multiple sources (Gmail, SMS, Forms, Calendar, Campaigns) into unified morning digest with prioritized action items

**Agent**: Claude Code (setup, debugging). Clawdbot ("Run morning digest" command). Ralph: N/A.

**Key Files**:
```
projects/shared/personal-assistant/
├── src/
│   ├── digest_aggregator.py    # Combines all data sources
│   ├── morning_digest.py       # Generates + sends digest via SMTP
│   └── routine_scheduler.py    # Creates calendar reminders
├── workflows/
│   ├── daily-routine-sop.md    # Morning checklist (8-10:30 AM)
│   └── weekly-routine-sop.md   # Weekly/monthly tasks
└── output/digests/             # Historical digests (JSON)
```

**Commands**:

```bash
# Preview morning digest (no email sent)
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant
python -m src.morning_digest --preview

# Send digest email
python -m src.morning_digest

# Check digest data only
python -m src.digest_aggregator --hours 24

# Create calendar reminders (one-time setup)
python -m src.routine_scheduler --create-all
```

**Data Sources Aggregated**:

| Source | Data Retrieved |
|--------|----------------|
| Gmail API | Emails categorized (urgent, sponsorship, business, customer) |
| SMS Campaigns | Hot leads, callbacks, questions, opt-outs |
| Form Submissions | New inquiries with source tracking |
| Google Calendar | Today's events + upcoming week |
| Campaign Analytics | Response rates, funnel metrics |

**Digest Schedule**:

| Frequency | Tasks | Time |
|-----------|-------|------|
| Daily | Morning digest review, SMS replies, Form submissions | 8:00-10:30 AM |
| Weekly (Mon) | Campaign performance, ClickUp pipeline, Week preview | 9:00-10:30 AM |
| Bi-weekly | Revenue analytics, API costs, Inventory check | 10:30-11:30 AM |
| Monthly | Revenue report, ROI analysis, Churn, Storage fees | 1st of month |

**Setup Requirements**:

1. **Environment variables** (in `.env`):
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   DIGEST_RECIPIENT=your-email@gmail.com
   ```

2. **Google OAuth** (first time):
   - Place `credentials.json` in project root
   - Run once to generate `token.json`

**Communication Patterns**:
- "Run morning digest" → `python -m src.morning_digest --preview`
- "Send the digest" → `python -m src.morning_digest`
- "Set up calendar reminders" → `python -m src.routine_scheduler --create-all`

**Success Criteria**:
- ✅ Morning digest delivers at 8 AM with all summaries
- ✅ Action items prioritized (hot leads first)
- ✅ Calendar reminders created for all routine tasks
- ✅ Historical digests saved in `output/digests/`

**References**: `projects/shared/personal-assistant/workflows/daily-routine-sop.md`, `projects/shared/personal-assistant/workflows/weekly-routine-sop.md`

