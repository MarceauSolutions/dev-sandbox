# Hormozi-Style Cold Outreach Optimization Protocol

> Based on Alex Hormozi's "100M Leads" framework: Track everything, test constantly, scale winners, kill losers.

## Core Principles

1. **Rule of 100**: Do 100 outreaches per day minimum
2. **Track Everything**: Every response linked to template that generated it
3. **Weekly Optimization**: Review and adjust strategy every Monday
4. **Kill Fast**: Underperforming templates get cut immediately
5. **Scale Winners**: 70% volume to best performers

---

## Automation Schedule

| Frequency | Script | Purpose |
|-----------|--------|---------|
| Daily 9 AM | `daily_followup_cron.sh` | Enroll leads, send follow-ups, sync responses |
| Monday 9 AM | `weekly_optimization_review.sh` | Full performance review, optimization |
| Tue-Fri 9 AM | `sms-scheduler (launchd)` | Additional campaign sends |

---

## Daily Workflow

The daily cron job (`scripts/daily_followup_cron.sh`) runs these steps:

1. **Check Lead Inventory** - Alerts if running low
2. **Enroll Apollo Leads** - 20 new leads per day with template rotation
3. **Send Follow-ups** - Process all due touchpoints
4. **Sync Responses** - Link replies to templates for tracking
5. **Check Alerts** - Flag concerning metrics (high opt-out, low response)

**Commands to run manually:**
```bash
# Check current status
python -m src.response_tracker report

# Check lead inventory
python -m src.lead_monitor status

# Check optimizer recommendations
python -m src.outreach_optimizer status
```

---

## Weekly Optimization Review (Every Monday)

The weekly review (`scripts/weekly_optimization_review.sh`) generates:

1. **Performance Report** - Response rates by template
2. **Winner/Loser Analysis** - Which templates to scale or kill
3. **Next Week's Allocation** - Recommended volume distribution
4. **Lead Inventory Check** - Days of leads remaining
5. **Alert Summary** - Any concerning metrics

**Key Metrics to Review:**

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Response Rate | >5% | Test new templates |
| Opt-Out Rate | <5% | Review message tone |
| Quality Score | >0 | Kill template if negative |
| Hot Lead % | >20% of responses | Improve qualification |

---

## Template A/B Testing Protocol

### Exploration Phase (First 50 sends per template)
- Equal distribution across all templates
- Goal: Gather enough data to evaluate
- Duration: Usually 1-2 weeks

### Exploitation Phase (After 50+ sends)
- 70% volume to best performer
- 30% split among test templates
- Review weekly, adjust allocation

### When to Create New Templates

1. **Best template < 5% response** - All templates underperforming
2. **Negative quality score** - Template generates opt-outs
3. **Feedback patterns** - Common objections in replies
4. **New lead source** - Different audience needs different angle

### Template Creation Guidelines

Per Hormozi framework:
- **Lead with curiosity** - Questions > statements
- **Be specific** - Use business name, numbers
- **Social proof if honest** - Only real results
- **Clear CTA** - One action, easy to do
- **Under 160 chars** - Single SMS segment

---

## Response Categories

| Category | Definition | Action |
|----------|------------|--------|
| **hot_lead** | "Yes", "interested", "call me" | Immediate follow-up call |
| **warm_lead** | Questions, "tell me more" | Send info, schedule call |
| **cold_lead** | "Not now", "maybe later" | Continue sequence |
| **opt_out** | "STOP", "remove me" | Add to opt-out list |

---

## Key Commands Reference

```bash
# === DAILY MONITORING ===
python -m src.response_tracker report     # Response rates by template
python -m src.response_tracker alert      # Check for problems
python -m src.lead_monitor status         # Lead inventory

# === OPTIMIZATION ===
python -m src.outreach_optimizer status   # Template allocation
python -m src.response_tracker weekly     # Weekly review

# === MANUAL OPERATIONS ===
python -m src.apollo_leads_loader enroll --limit 20 --for-real  # Add leads
python -m src.follow_up_sequence process --for-real             # Send follow-ups
python -m src.response_tracker sync                             # Sync replies

# === TROUBLESHOOTING ===
cat output/sms_replies.json | jq '.replies[-5:]'   # Last 5 replies
cat output/response_links.json | jq '.links | length'  # Total linked
```

---

## Escalation Triggers

### Immediate Action Required

1. **Opt-out rate > 10%** - Stop campaign, review message
2. **Carrier complaints** - Twilio notification, pause sends
3. **Lead inventory < 50** - Run new Apollo search

### Weekly Review Flags

1. **Response rate < 2%** after 100+ sends - Major template overhaul
2. **No hot leads** in 2+ weeks - Revisit offer/value prop
3. **Quality score negative** for all templates - Reset strategy

---

## Measurement Dashboard

Run `python -m src.response_tracker report` for:

```
📊 RESPONSE RATE ANALYSIS (Hormozi Framework)
======================================================================
📈 OVERALL METRICS:
   Total Sent:     1,000
   Total Responses: 50 (5.0%)
   Hot Leads:      10
   Warm Leads:     15
   Opt-Outs:       25

📋 BY TEMPLATE:
Template                    Sent   Resp   Rate   Hot  Warm OptOut  Score
--------------------------------------------------------------------------
🏆 apollo_b2b_intro          400     25   6.3%    8    10      7   0.15
   apollo_decision_maker     350     18   5.1%    2     5     11  -0.02
   apollo_automation_offer   250      7   2.8%    0     0      7  -0.08
```

---

## Version History

- **2026-01-21**: Initial protocol with response_tracker.py
- Created automation scripts
- Set up daily and weekly cron jobs
