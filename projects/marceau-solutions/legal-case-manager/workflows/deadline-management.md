# Workflow: Deadline Management

## Overview
Track all case-related deadlines including statutes of limitations, filing windows, response deadlines, and court dates. Missing a deadline can be fatal to a case.

## When to Use
- New deadline identified (filing window, court date, response due)
- Daily morning check for upcoming deadlines
- After any filing or court action that creates new deadlines

## Critical Housing Discrimination Deadlines

| Deadline Type | Time Limit | Measured From | Statute |
|---------------|-----------|---------------|---------|
| HUD Complaint | 1 year | Last discriminatory act | 42 USC 3610(a)(1)(A)(i) |
| FCHR Complaint | 365 days | Last discriminatory act | FL Stat. 760.34(1) |
| Federal Lawsuit (FHA) | 2 years | Last discriminatory act | 42 USC 3613(a)(1)(A) |
| State Lawsuit (FL) | 2 years | Last discriminatory act | FL Stat. 95.11 |
| HUD Investigation | 100 days | Filing date | 42 USC 3610(a)(1)(B)(iv) |
| FCHR Investigation | 180 days | Filing date | FL Stat. 760.35 |
| Right to Sue (after FCHR) | 1 year | Issuance of notice | FL Stat. 760.35 |

**Continuing Violation Doctrine**: If discrimination is ongoing, the statute may run from the most recent act, not the first. Document every instance.

## Steps

### 1. Add a New Deadline
```bash
python src/deadline_tracker.py add \
    --name "HUD Complaint Filing Deadline" \
    --date 2027-01-15 \
    --category statute \
    --alert-days 90,30,14,7,3,1 \
    --notes "1 year from discriminatory act on 2026-01-15"
```

**Categories**: `statute` (statute of limitations), `filing` (response/filing due), `court` (hearing/trial date), `administrative` (agency deadline), `personal` (self-imposed action item)

### 2. Daily Check
```bash
python src/deadline_tracker.py check
```

Run this every morning. Output shows:
- Overdue items (RED)
- Due within 7 days (YELLOW)
- Due within 30 days (upcoming)

### 3. Review Alerts
```bash
python src/deadline_tracker.py alert
```

### 4. After a Filing Creates New Deadlines
When you file something, opposing party usually has a response window. Add it immediately:
```bash
python src/deadline_tracker.py add \
    --name "Respondent answer to complaint" \
    --date [date+30] \
    --category filing \
    --alert-days 30,14,7,3,1
```

### 5. Mark Complete
```bash
python src/deadline_tracker.py complete --name "HUD Complaint Filing Deadline" --notes "Filed on 2026-03-01"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Unsure of exact deadline date | Research statute, consult attorney, err on the EARLIER date |
| Deadline approaching with no action | Escalate immediately - contact attorney or file emergency motion |
| Multiple deadlines for same filing | Track all - some are firm (statutory), some are soft (administrative) |

## Success Criteria
- [ ] All known deadlines entered with alert thresholds
- [ ] Daily check run (or automated via cron/n8n)
- [ ] No deadline missed
- [ ] New deadlines added immediately when created by filings/orders
