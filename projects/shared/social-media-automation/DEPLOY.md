# X Automation Deployment Checklist

**Status**: Ready to deploy 🚀
**Created**: 2026-01-20
**System**: AI Automation Agency (marceau-solutions)

---

## Pre-Deployment Research (15 mins)

Run trend research to optimize hashtags and content:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation
python scripts/research_trends.py --export-report
```

**Review output**: `output/trend_research_report.json`

---

## Deployment Steps (5 mins)

### 1. Set Up Cron Jobs

```bash
bash scripts/setup_posting_schedule.sh
```

This creates 9 cron jobs (6 AM - 10 PM EST).

### 2. Verify Cron Setup

```bash
crontab -l | grep business_scheduler
```

You should see 9 entries.

### 3. Schedule First Day of Posts

```bash
python -m src.business_scheduler schedule-day --business marceau-solutions
```

### 4. View Queue

```bash
python -m src.business_scheduler view-queue --business marceau-solutions
```

You should see 25 scheduled posts.

### 5. Test Single Post (Dry Run)

```bash
# Generate 1 post with image
python -m src.business_content_generator preview --business marceau-solutions --count 1
```

---

## Go Live Options

### Option A: Start Immediately
```bash
python -m src.business_scheduler process --max 1
```

### Option B: Let Cron Handle It
Wait for next scheduled time (check `crontab -l`)

### Option C: Schedule Full Week Ahead
```bash
python -m src.business_scheduler schedule-week --business marceau-solutions
```

---

## Monitoring (Daily)

### Check Posting Logs
```bash
tail -50 projects/social-media-automation/output/posting.log
```

### View Stats
```bash
python -m src.business_scheduler status
```

### Check Rate Limits
```bash
cat projects/social-media-automation/output/rate_limit_status.json | python -m json.tool
```

---

## Expected Results (30 Days)

- **Posts**: 750 total (25/day × 30)
- **Images**: 375 Grok-generated (~50%)
- **Cost**: ~$26/month
- **Followers**: +500-1000
- **Engagement**: 2-5% (with images)

---

## Rollback / Pause

### Stop All Posting
```bash
# Remove cron jobs
crontab -l | grep -v business_scheduler | crontab -
```

### Clear Queue
```bash
python -m src.business_scheduler clear-queue --business marceau-solutions
```

---

## Support

- **Logs**: `projects/social-media-automation/output/posting.log`
- **Config**: `projects/social-media-automation/config/businesses.json`
- **Content**: `projects/social-media-automation/templates/business_content.json`
- **Plan**: `/Users/williammarceaujr./dev-sandbox/docs/X-AUTOMATION-PLAN-JAN-19-2026.md`

---

**Ready to lock it down? ✅**

Just run the research script, then the cron setup script, and you're live!
