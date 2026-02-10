# SOP 19: Multi-Touch Follow-Up Sequence

**When**: Managing automated follow-up sequences for non-responding leads

**Purpose**: Execute the 7-touch, 60-day follow-up sequence based on Hormozi's "Still Looking" framework

**Agent**: Claude Code (setup). Clawdbot (daily processing). Ralph: N/A. Note: Consider n8n workflow replacement.

**Prerequisites**:
- ✅ SOP 18 campaign created (initial outreach complete)
- ✅ Lead list loaded with valid phone numbers
- ✅ Follow-up templates approved
- ✅ Twilio balance sufficient for sequence duration

**Sequence Architecture**:
```
Day 0:  Initial outreach (intro message)
Day 2:  Follow-up #1 (still_looking)
Day 5:  Follow-up #2 (social_proof)
Day 10: Follow-up #3 (direct_question)
Day 15: Follow-up #4 (availability)
Day 30: Follow-up #5 (breakup)
Day 60: Follow-up #6 (re_engage)
```

**Steps**:

1. **Create campaign with sequence**:
   ```bash
   python -m src.follow_up_sequence create \
       --name "Naples Gyms No Website" \
       --pain-point no_website \
       --limit 100
   ```

2. **Send initial outreach (Day 0)**:
   ```bash
   python -m src.follow_up_sequence send --campaign {campaign_id} --day 0
   ```

3. **Process due follow-ups** (run daily via cron or manually):
   ```bash
   python -m src.follow_up_sequence process-due
   ```

4. **Handle responses**:
   ```bash
   # Mark lead as responded
   python -m src.follow_up_sequence mark-responded \
       --campaign {campaign_id} \
       --phone "+1XXXXXXXXXX" \
       --outcome positive  # positive, negative, callback_scheduled, not_interested
   ```

5. **View campaign status**:
   ```bash
   python -m src.follow_up_sequence status --campaign {campaign_id}
   python -m src.follow_up_sequence report --format daily
   ```

**Exit Conditions** (lead removed from sequence):
- Lead replies (any response)
- Lead opts out (STOP)
- Delivery fails 2x consecutive
- Callback scheduled
- Day 60 completed

**Success Criteria**:
- ✅ Overall reply rate >5%
- ✅ Opt-out rate <3%
- ✅ Delivery rate >95%
- ✅ >80% reach Day 60

**References**: `projects/shared/lead-scraper/workflows/multi-touch-followup-sop.md`
