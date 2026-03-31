# Lead Generation System — Operating Sheet

## Quick Reference

### Daily Schedule (Weekdays)
| Time (ET) | Job | What It Does |
|-----------|-----|--------------|
| 6:30am | Morning Digest | Pipeline summary + lead gen digest |
| 8:00am | Weekly Lead Gen | **Monday only** — fresh lead list |
| 9:00am | Daily Loop | Process pipeline, outreach, follow-ups |
| 9am-6pm | Response Check | Every 30 min, check for replies |
| 9:00pm | Evening Digest | Day summary to Telegram |

### Key Commands

```bash
# Check lead generation system
python3 -m projects.lead_generation.src.generate_new_lead_list status
python3 -m projects.lead_generation.src.generate_new_lead_list should-run

# Manual lead generation (dry run first!)
python3 -m projects.lead_generation.src.generate_new_lead_list generate --limit 50 --dry-run
python3 -m projects.lead_generation.src.generate_new_lead_list generate --limit 50  # Live

# Force generation (ignores schedule)
python3 -m projects.lead_generation.src.generate_new_lead_list generate --force --limit 100

# Check daily loop
python3 -m projects.lead_generation.src.daily_loop status
python3 -m projects.lead_generation.src.daily_loop full --dry-run  # Preview
python3 -m projects.lead_generation.src.daily_loop full --for-real  # Live

# View recent logs
tail -100 /home/clawdbot/logs/weekly_lead_gen.log
tail -100 /home/clawdbot/logs/daily_loop_ec2.log

# Check what outcome_learner has learned
python3 -m projects.personal_assistant.src.outcome_learner insights
```

---

## Lead Generation Flow

### Weekly Generation (Monday 8am ET)

```
1. DISCOVER
   ├── Apollo API (best contacts)
   ├── Google Places
   └── Existing leads pool

2. DEDUPLICATE
   ├── By company name
   ├── By phone number
   └── By email address

3. ICP SCORE
   ├── Industry fit (0-30 pts)
   ├── Company size (0-25 pts)
   ├── Location (0-25 pts)
   └── Contact quality (0-30 pts)

4. TIER
   ├── Tier 1: 80+ score (priority)
   ├── Tier 2: 50-79 score
   ├── Tier 3: 20-49 score
   └── Discard: <20 score

5. ENRICH (Apollo)
   ├── Verify emails
   └── Find phones

6. EXPORT
   ├── CSV: output/weekly_lists/leads_YYYYMMDD.csv
   └── Pipeline: Imported as "Prospect" stage
```

### ICP Scoring Details

| Factor | Max Points | Best Value |
|--------|------------|------------|
| **Industry** | 30 | HVAC, Plumbing, Med Spa |
| **Company Size** | 25 | 1-10 employees |
| **Location** | 25 | Naples, FL |
| **Contact Quality** | 30 | Verified email + phone + owner name |

**Industries by Score:**
- 30: HVAC, Plumbing
- 28: Med Spa
- 25: Electrical, Dental, Chiro
- 22: Roofing, Pest Control
- 20: Fitness, Landscaping, Pool
- 18: Auto Repair
- 15: Real Estate
- 10: Restaurant
- 8: Retail

---

## Self-Improvement System

### Outcome Learner Integration

The system learns from recorded outcomes and adjusts:

1. **Lead Generation Frequency**
   - Default: 7 days (weekly)
   - High conversion (>60%): 5 days
   - Low conversion (<20%): 10 days

2. **ICP Score Adjustments**
   - Industries with >50% conversion: +10 points
   - Industries with >25% conversion: +5 points
   - Industries with 0% conversion: -15 points

3. **Industry Prioritization**
   - Ranked by historical conversion rate
   - Top performers get discovery priority

### Recording Outcomes

After calls/visits, record results:

```
result [company]: meeting_booked
result [company]: client_won
result [company]: not_interested
result [company]: no_show
result [company]: callback
```

---

## Troubleshooting

### Generation Not Running

1. Check if it should run:
   ```bash
   python3 -m projects.lead_generation.src.generate_new_lead_list should-run
   ```

2. Check last generation:
   ```bash
   python3 -m projects.lead_generation.src.generate_new_lead_list status
   ```

3. Force a generation:
   ```bash
   python3 -m projects.lead_generation.src.generate_new_lead_list generate --force
   ```

### Low Quality Leads

1. Check ICP scoring weights in `generate_new_lead_list.py`
2. Review outcome_learner insights:
   ```bash
   python3 -m projects.personal_assistant.src.outcome_learner insights
   ```
3. Manually adjust industry weights if needed

### Too Many Duplicates

Check what's in pipeline:
```bash
sqlite3 /home/clawdbot/data/pipeline.db "SELECT COUNT(*), stage FROM deals GROUP BY stage"
```

### No Apollo/Google Places Data

1. Check API keys in `.env`:
   - `APOLLO_API_KEY`
   - `GOOGLE_PLACES_API_KEY`

2. System falls back to existing leads if APIs unavailable

---

## File Locations

| File | Purpose |
|------|---------|
| `src/generate_new_lead_list.py` | Weekly lead generation |
| `src/daily_loop.py` | Main orchestration loop |
| `src/campaign_auto_launcher.py` | Outreach automation |
| `logs/lead_generation_state.json` | Generation history |
| `logs/generation_digest.json` | Last generation summary |
| `output/weekly_lists/` | CSV exports |
| `/home/clawdbot/data/pipeline.db` | Pipeline database |
| `/home/clawdbot/logs/weekly_lead_gen.log` | Cron logs |

---

## Cron Jobs

```cron
# Weekly Lead Generation (Monday 8am ET = 12:00 UTC)
0 12 * * 1 cd /home/clawdbot/dev-sandbox && python3 -m projects.lead_generation.src.generate_new_lead_list generate --limit 100

# Daily Loop (9am ET = 13:00 UTC, weekdays)
0 13 * * 1-5 cd /home/clawdbot/dev-sandbox && python3 -m projects.lead_generation.src.daily_loop full --for-real
```

---

## Zero-Human Operation

During William's work hours (7am-3pm ET):

1. **Lead Generation** (Monday): Runs automatically at 8am
2. **Daily Loop**: Runs at 9am, processes pipeline
3. **Response Monitoring**: Every 30 minutes
4. **Hot Lead Alerts**: Immediate SMS if someone replies positively
5. **Follow-ups**: Auto-sent based on sequences

**Only intervention needed:**
- Reply to hot lead SMS (1=Calendly, 2=Phone, 3=Pass)
- Record outcomes after calls (`result [company]: [outcome]`)

---

*Last Updated: 2026-03-30*
