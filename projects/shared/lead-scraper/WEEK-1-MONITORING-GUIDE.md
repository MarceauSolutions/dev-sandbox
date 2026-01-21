# Week 1 Outreach Monitoring Guide

**System Status**: ✅ DEPLOYED & RUNNING

Automated outreach is now live for both businesses with 10 daily cron jobs.

---

## Daily Monitoring (5 minutes)

### Morning Check (8:30 AM)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# 1. Check if daily-run executed
tail -20 output/outreach.log | grep "daily-run"

# 2. See what's scheduled for today
python -m src.outreach_scheduler status

# 3. Quick stats
python -m src.scraper stats
```

**What to look for**:
- ✅ "Scheduled X batches" message in log
- ✅ Pending batches in queue
- ❌ ERROR or WARNING messages

### Evening Check (6:00 PM)

```bash
# 1. Check what was sent today
tail -50 output/outreach.log | grep "sent"

# 2. Check for responses (check phone/email manually)
# SMS replies: Check your phone
# Email replies: Check inbox
```

---

## Weekly Summary (Every Sunday)

```bash
# View Week 1 performance
python -m src.weekly_monitor week-summary
```

**Expected Stats (Week 1)**:

| Business | Emails | SMS | Total | Expected Replies (2-5%) |
|----------|--------|-----|-------|------------------------|
| Marceau Solutions | 0-140 | 70 | 70-210 | 1-10 |
| SW Florida Comfort HVAC | 0-105 | 70 | 70-175 | 1-9 |

**Note**: Email count will be 0 until you add emails to leads

---

## Email Collection Progress

### Top 25 Priority Leads

📊 **File**: [output/priority_leads_email_collection.csv](output/priority_leads_email_collection.csv)

**Status**: ⏳ Pending manual collection

### Collection Workflow

**Option 1: Manual (Recommended for top 10)**

1. Open CSV in Google Sheets
2. For each business:
   - Visit website contact page
   - Search LinkedIn: "[Business Name] owner Naples"
   - Check About Us page
3. Fill in "Owner Email" column
4. Add to database:
   ```bash
   python scripts/add_email_to_lead.py "Business Name" "email@domain.com"
   ```

**Option 2: Hunter.io (Faster for 11-25)**

1. Sign up: [hunter.io](https://hunter.io) (free: 25 searches/month)
2. Use "Domain Search" for each website
3. Export results
4. Bulk import:
   ```bash
   # For each email found
   python scripts/add_email_to_lead.py "Business Name" "email@domain.com"
   ```

### Progress Tracker

- [ ] Emails collected: 0/25
- [ ] Added to database: 0/25
- [ ] Ready for outreach: 0/25

**Once 10+ emails are added**, re-run scheduler to start email campaigns:
```bash
python -m src.outreach_scheduler daily-run --business marceau-solutions
```

---

## Key Files

| File | Purpose |
|------|---------|
| `output/outreach.log` | All outreach activity |
| `output/outreach_history.json` | Campaign stats |
| `output/outreach_queue.json` | Scheduled batches |
| `output/priority_leads_email_collection.csv` | Top 25 leads for email collection |
| `output/leads.json` | Master lead database |

---

## Troubleshooting

### No SMS Being Sent

**Check**: 
```bash
grep "SMS batch" output/outreach.log
```

**Possible causes**:
- All leads already contacted (duplicate prevention working)
- Twilio account out of balance
- Check: `tail -50 output/outreach.log | grep ERROR`

### Cron Jobs Not Running

**Check**:
```bash
crontab -l | grep outreach_scheduler
# Should show 10 jobs
```

**Verify logs**:
```bash
ls -lh output/outreach.log
# Should be updating daily
```

### Email Batches Showing 0 Sent

**This is EXPECTED** - No emails will send until you add owner emails to leads.

Current status: 0/354 leads have emails (Apollo enrichment failed for small local businesses)

**Solution**: Manual email collection (see above)

---

## Success Metrics (Week 1)

**Primary Goals**:
- ✅ System running without errors
- ✅ SMS campaigns executing daily
- 📧 Email collection started (manual)
- 📊 Track response rates

**Response Rate Benchmarks**:
- **SMS**: 2-5% expected
- **Email**: 3-7% expected (once emails added)

**Week 1 Target**:
- Collect 10+ owner emails
- Get 1-3 SMS responses
- Zero system errors

---

## Next Week Actions

**If Week 1 successful**:
1. Scale up daily limits (20 → 30 emails, 10 → 15 SMS)
2. Add more businesses to scheduler
3. A/B test different message templates
4. Implement automated follow-up sequences

**If issues found**:
1. Review logs for patterns
2. Adjust send times
3. Refine targeting (pain points, categories)
4. Update message templates

---

## Quick Commands Reference

```bash
# Daily check
python -m src.outreach_scheduler status

# Weekly summary
python -m src.weekly_monitor week-summary

# Add email to lead
python scripts/add_email_to_lead.py "Business Name" "email@domain.com"

# View logs
tail -f output/outreach.log

# Manual send test
python -m src.scraper sms --category restaurant --limit 5 --dry-run
```

---

**Last Updated**: 2026-01-19
**System Version**: 1.0.0
**Status**: ✅ Active & Automated
