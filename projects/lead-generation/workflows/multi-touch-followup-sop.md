# SOP: Multi-Touch Follow-Up Sequence Management

*Last Updated: 2026-01-15*
*Version: 1.0.0*

**Extends**: [cold-outreach-sop.md](cold-outreach-sop.md)

## Overview

This SOP covers the 7-touch, 60-day follow-up sequence for leads who don't respond to initial outreach. Based on Hormozi's "Still Looking" framework - persistence without annoyance.

## Sequence Architecture

```
Day 0:  Initial outreach (intro message)
Day 2:  Follow-up #1 (still_looking)
Day 5:  Follow-up #2 (social_proof)
Day 10: Follow-up #3 (direct_question)
Day 15: Follow-up #4 (competitor_hook)
Day 30: Follow-up #5 (breakup message)
Day 60: Follow-up #6 (re_engage)
```

### Template Sequence

| Day | Template | Purpose | Tone |
|-----|----------|---------|------|
| 0 | `no_website_intro` | Initial value proposition | Helpful |
| 2 | `still_looking` | 9-word reactivation | Casual |
| 5 | `social_proof` | Reference success story | Credible |
| 10 | `direct_question` | Binary yes/no question | Direct |
| 15 | `competitor_hook` | Create open loop | Curious |
| 30 | `breakup` | Scarcity/closing file | Final offer |
| 60 | `re_engage` | Long-term check-in | Friendly |

---

## Starting a Sequence

### Step 1: Create Campaign with Sequence

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Start new campaign with sequence tracking
python -m src.follow_up_sequence create \
    --name "Naples Gyms No Website" \
    --pain-point no_website \
    --limit 100
```

This creates:
- Campaign entry in `output/campaigns/{campaign_id}/`
- Lead assignments to Day 0
- Schedule for all 7 touches

### Step 2: Send Day 0 (Initial)

```bash
python -m src.follow_up_sequence send --campaign {campaign_id} --day 0
```

### Step 3: Automated Follow-Ups

Set up cron job or run daily:

```bash
# Check and send due follow-ups
python -m src.follow_up_sequence process-due

# Or run specific day manually
python -m src.follow_up_sequence send --campaign {campaign_id} --day 2
```

---

## Managing Active Sequences

### View Sequence Status

```bash
# List all active campaigns
python -m src.follow_up_sequence list

# View specific campaign
python -m src.follow_up_sequence status --campaign {campaign_id}
```

Output:
```
Campaign: Naples Gyms No Website
Started: 2026-01-15
Leads: 100

Day | Sent | Delivered | Replied | Opted-Out
----|------|-----------|---------|----------
 0  | 100  |    98     |    3    |    1
 2  |  96  |    94     |    2    |    0
 5  |  94  |    92     |    1    |    1
...
```

### Handle Responses

When a lead responds:
1. **Positive**: Remove from sequence, create ClickUp task for sales call
2. **Negative**: Mark as "not interested", stop sequence
3. **STOP**: Auto-removed, added to opt-out list

```bash
# Mark lead as responded
python -m src.follow_up_sequence mark-responded \
    --campaign {campaign_id} \
    --phone "+1XXXXXXXXXX" \
    --outcome positive

# Outcomes: positive, negative, callback_scheduled, not_interested
```

### Pause/Resume Sequence

```bash
# Pause entire campaign
python -m src.follow_up_sequence pause --campaign {campaign_id}

# Resume
python -m src.follow_up_sequence resume --campaign {campaign_id}

# Pause specific lead
python -m src.follow_up_sequence pause-lead \
    --campaign {campaign_id} \
    --phone "+1XXXXXXXXXX"
```

---

## Sequence Rules

### Exit Conditions (Lead Removed from Sequence)

| Condition | Action |
|-----------|--------|
| Lead replies (any response) | Remove, create follow-up task |
| Lead opts out (STOP) | Remove, add to global opt-out |
| Delivery fails 2x consecutive | Remove, mark invalid |
| Callback scheduled | Remove, mark converted |
| Day 60 completed | Archive, sequence complete |

### Timing Rules

| Rule | Implementation |
|------|----------------|
| Min gap between touches | 48 hours |
| No weekend sends | Skip Sat/Sun, resume Monday |
| No holiday sends | Define holiday blackout dates |
| Time window | 9am - 6pm recipient local time |

---

## Reporting

### Daily Report

```bash
python -m src.follow_up_sequence report --format daily
```

Output:
```
=== Follow-Up Sequence Report (2026-01-15) ===

Due Today: 45 messages across 3 campaigns
Sent Today: 45
Replies Today: 3
Opt-Outs Today: 1

Top Performing Template: social_proof (4.2% reply rate)
Worst Performing: breakup (0.8% reply rate)
```

### Campaign Funnel

```bash
python -m src.follow_up_sequence funnel --campaign {campaign_id}
```

Output:
```
Campaign: Naples Gyms No Website
Funnel Analysis:

Day 0:  100 → 3 replies (3.0%)
Day 2:   97 → 2 replies (2.1%)
Day 5:   95 → 1 reply  (1.1%)
Day 10:  94 → 0 replies (0.0%)
...

Total Conversion: 8/100 (8.0%)
Average Touch to Reply: 2.3
```

---

## Troubleshooting

### Leads Not Advancing

| Symptom | Cause | Solution |
|---------|-------|----------|
| Stuck on Day 0 | Day 2 not triggered | Check `process-due` cron |
| Skipping days | Date calculation error | Verify timezone settings |
| All pending | Campaign paused | Run `resume --campaign` |

### Duplicate Messages

```bash
# Check if lead already received message
python -m src.follow_up_sequence history --phone "+1XXXXXXXXXX"

# Shows all touches sent to this lead
```

### Sequence Not Stopping

```bash
# Force remove lead from all sequences
python -m src.follow_up_sequence force-remove --phone "+1XXXXXXXXXX"
```

---

## Rollback Procedures

### Stop All Active Sequences

```bash
python -m src.follow_up_sequence pause-all
```

### Revert Specific Touch

If wrong message sent:
1. Cannot unsend SMS
2. Document error in campaign notes
3. Consider sending correction message

```bash
python -m src.follow_up_sequence add-note \
    --campaign {campaign_id} \
    --note "Day 5 sent with wrong template - corrected in Day 10"
```

### Archive Campaign

```bash
python -m src.follow_up_sequence archive --campaign {campaign_id}
# Stops all future sends, preserves history
```

---

## Success Criteria

### Sequence Performance

| Metric | Target | Concern Threshold |
|--------|--------|-------------------|
| Overall reply rate | >5% | <2% |
| Day 0 reply rate | >3% | <1% |
| Opt-out rate | <3% | >5% |
| Delivery rate | >95% | <90% |
| Sequence completion | >80% reach Day 60 | <60% |

### Per-Template Analysis

Track which templates perform best:
```bash
python -m src.follow_up_sequence template-performance
```

Iterate: Replace underperforming templates with variants.

---

## Quick Reference

```bash
# Create new sequence campaign
python -m src.follow_up_sequence create --name "Campaign Name" --pain-point X --limit 100

# Send specific day
python -m src.follow_up_sequence send --campaign ID --day N

# Process all due follow-ups
python -m src.follow_up_sequence process-due

# View campaign status
python -m src.follow_up_sequence status --campaign ID

# Mark lead responded
python -m src.follow_up_sequence mark-responded --campaign ID --phone X --outcome positive

# Pause campaign
python -m src.follow_up_sequence pause --campaign ID

# Daily report
python -m src.follow_up_sequence report --format daily

# Archive completed
python -m src.follow_up_sequence archive --campaign ID
```
