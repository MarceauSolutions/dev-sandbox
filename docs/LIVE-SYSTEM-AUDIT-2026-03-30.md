# LIVE SYSTEM AUDIT — Company on a Laptop
**Timestamp:** 2026-03-30 14:45 UTC  
**Source:** Direct system queries (not cached)

---

## EXECUTIVE SUMMARY

| Metric | Live Value | Status |
|--------|------------|--------|
| **Towers** | 6/6 have src/ | ✅ All exist |
| **Active Towers** | 3 mature (ai-systems, lead-gen, PA) | 🟡 3 dev-only |
| **n8n Workflows** | 76 total (67 active) | ✅ |
| **PA Service (8786)** | Healthy, 24 handlers | ✅ |
| **Pipeline Deals** | 205 total (108 Contacted, 81 Intake) | ✅ |
| **Outcomes Recorded** | **5/5 required** | ✅ |
| **Weekly Lead Gen** | NEW — Integrated | ✅ |

---

## 1. TOWER STRUCTURE (Live)

| Tower | VERSION | README | src/*.py | Status |
|-------|---------|--------|----------|--------|
| **ai-systems** | 1.2.0 | ✅ | 34 files | ✅ MATURE |
| **amazon-seller** | 1.0.0-dev | ✅ | 18 files | 🟡 DEV |
| **fitness-influencer** | 1.0.0-dev | ✅ | 129 files | 🟡 DEV |
| **lead-generation** | 1.1.0 | ✅ | 98 files | ✅ MATURE |
| **mcp-services** | 1.0.0-dev | ✅ | 23 files | 🟡 DEV |
| **personal-assistant** | 1.2.0 | ✅ | 47 files | ✅ MATURE |

---

## 2. AUTONOMOUS SYSTEMS

### 🆕 Weekly Lead List Generation (NEW)
**Location:** `projects/lead-generation/src/generate_new_lead_list.py`  
**Schedule:** Monday 8am ET (12:00 UTC)  
**Cron:** `0 12 * * 1`

| Feature | Status |
|---------|--------|
| ICP Tiering/Scoring | ✅ Tier 1/2/3 scoring |
| Deduplication | ✅ Against pipeline.db |
| Enrichment | ✅ Apollo integration |
| CSV Export | ✅ Dated files |
| Pipeline Import | ✅ As "Prospect" stage |
| Outcome Learner Integration | ✅ Dynamic frequency |
| Morning Digest Integration | ✅ Summary included |

**ICP Scoring Weights:**
- Industry fit: up to 30 points (HVAC, Plumbing, Med Spa highest)
- Company size: up to 25 points (1-10 employees ideal)
- Location: up to 25 points (Naples highest)
- Contact quality: up to 30 points (verified email, phone, owner name)

**Tier Thresholds:**
- Tier 1: 80+ score
- Tier 2: 50-79 score
- Tier 3: 20-49 score
- Discard: <20 score

### Daily Loop (9 Stages)
**Location:** `projects/lead-generation/src/daily_loop.py`

| Stage | Function | Status |
|-------|----------|--------|
| 0. COMPLIANCE | CLAUDE.md checks | ✅ |
| 0.5 LEAD GEN | Weekly list (Mon only) | ✅ NEW |
| 1. DISCOVER | Process existing leads | ✅ (capped on non-gen days) |
| 2. SCORE | ML scoring, top 20% filter | ✅ |
| 3. ENRICH | Contact verification | ✅ |
| 4. OUTREACH | Initial email (10/day cap) | ✅ |
| 5. MONITOR | Gmail + Twilio checking | ✅ |
| 6. CLASSIFY | Hot/Warm/Cold classification | ✅ |
| 7. FOLLOW-UP | 3-touch sequences | ✅ |
| 7b. EMAIL SEQ | Gmail API sequences | ✅ |
| 8. CROSS-TOWER | PA/Fitness handoffs | ✅ |
| 8. REPORT | Daily digest to Telegram | ✅ |
| 9. TOWER SIGNALS | Project detection | ✅ |

### Unified Morning Digest
**Location:** `projects/personal-assistant/src/unified_morning_digest.py`  
**Schedule:** 6:30am ET  
**Status:** ✅ Operational  
**NEW:** Includes lead generation summary on Mondays

### Hot Lead Handler
**Location:** `projects/lead-generation/src/hot_lead_handler.py`  
**Reply Actions:** 1=Calendly, 2=Phone, 3=Pass  
**Status:** ✅ Operational

### Cross-Tower Sync
**Location:** `execution/cross_tower_sync.py`  
**Cycle:** 30 minutes (business hours)  
**Status:** ✅ Operational

### Outcome Learner (Self-Improvement)
**Location:** `projects/personal-assistant/src/outcome_learner.py`  
**Status:** ✅ 5 outcomes learned

**Learned Preferences:**
- Best channel: Call
- Industry rankings: Prioritized by conversion rate
- Follow-up timing: Adapts based on data volume
- **NEW:** Adjusts lead generation frequency

---

## 3. PIPELINE STATUS (Live)

```
Stage Distribution:
 108  Contacted
  81  Intake
  13  Closed Lost
   3  Qualified
```

**Recent Activity:**
- 2026-03-24: 106 new deals
- 2026-03-23: 99 new deals

---

## 4. CRON JOBS (EC2)

| Job | Schedule | Status |
|-----|----------|--------|
| **Weekly Lead Gen** | Mon 8am ET | ✅ NEW |
| Daily Loop | 9am ET M-F | ✅ |
| Morning Digest | 6:30am ET | ✅ |
| Evening Digest | 9pm ET | ✅ |
| Email Sequences | 9am ET M-F | ✅ |
| Cross-Tower Sync | Every 30min | ✅ |
| Fitness Daily Loop | 8am ET | ✅ |
| Coaching Loop | M/W/F | ✅ |
| Pipeline Backup | 8:55am ET | ✅ |

---

## 5. VERIFICATION COMMANDS

```bash
# Check lead generation status
python3 -m projects.lead_generation.src.generate_new_lead_list status

# Check if generation should run
python3 -m projects.lead_generation.src.generate_new_lead_list should-run

# Dry run generation
python3 -m projects.lead_generation.src.generate_new_lead_list generate --limit 20 --dry-run

# View last digest
python3 -m projects.lead_generation.src.generate_new_lead_list digest

# Check daily loop health
python3 -m projects.lead_generation.src.daily_loop status

# Check outcome learner
python3 -m projects.personal_assistant.src.outcome_learner insights

# Check cron jobs
crontab -l | grep -E "(LEAD|daily_loop|generate)"

# View generation logs
tail -50 /home/clawdbot/logs/weekly_lead_gen.log

# View daily loop logs
tail -50 /home/clawdbot/logs/daily_loop_ec2.log
```

---

## 6. SELF-IMPROVEMENT FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    WEEKLY LEAD GENERATION                     │
│                   (Monday 8am ET default)                    │
├─────────────────────────────────────────────────────────────┤
│  1. Check outcome_learner for frequency preference          │
│     - More outcomes = more confident scheduling             │
│     - High conversion = more frequent (5 days)              │
│     - Low conversion = less frequent (10 days)              │
│                                                             │
│  2. Discover from multiple sources                          │
│     - Apollo (best contact data)                            │
│     - Google Places                                         │
│     - Existing leads                                        │
│                                                             │
│  3. Deduplicate against pipeline.db                         │
│     - By company name                                       │
│     - By phone number                                       │
│     - By email address                                      │
│                                                             │
│  4. ICP Score and Tier                                      │
│     - Apply base scoring (industry, size, location)         │
│     - Apply learned preferences (boost/penalize industries) │
│     - Assign tiers (1/2/3/Discard)                          │
│                                                             │
│  5. Enrich (Apollo)                                         │
│     - Verify emails                                         │
│     - Find phone numbers                                    │
│     - Get owner names                                       │
│                                                             │
│  6. Export & Import                                         │
│     - CSV to output/weekly_lists/                           │
│     - Import to pipeline.db as "Prospect"                   │
│                                                             │
│  7. Update state & save digest                              │
│     - Track generation history                              │
│     - Provide summary for morning digest                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     DAILY LOOP (9am ET)                      │
│                   (M-F, weekdays only)                       │
├─────────────────────────────────────────────────────────────┤
│  Stage 0.5: Check if generation day                         │
│     - If yes: Run lead generation first                     │
│     - If no: Skip (leads already in pipeline)               │
│                                                             │
│  Stages 1-4: Process & Outreach (capped on non-gen days)    │
│  Stages 5-6: Monitor responses                              │
│  Stage 7: Follow-up sequences                               │
│  Stage 8: Report & cross-tower sync                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTCOME RECORDING                          │
│              (William records call/visit results)            │
├─────────────────────────────────────────────────────────────┤
│  "result [company]: [outcome]"                              │
│                                                             │
│  Outcomes: meeting_booked, client_won, not_interested, etc. │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTCOME LEARNER                            │
│               (Extracts patterns from outcomes)              │
├─────────────────────────────────────────────────────────────┤
│  - Which industries convert best?                           │
│  - Which channels work?                                     │
│  - Optimal follow-up timing                                 │
│  - Saves to learned_preferences.json                        │
│                                                             │
│  FEEDS BACK INTO:                                           │
│  - Lead generation frequency                                │
│  - ICP scoring adjustments                                  │
│  - Industry prioritization                                  │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2026-03-30 14:45 UTC
