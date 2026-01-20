# Social Media Automation - Troubleshooting Guide

## Common Issues and Solutions

### Issue: "Error loading queue: ScheduledPost.__init__() got an unexpected keyword argument"

**Symptom**: Queue fails to load, posts not processing

**Cause**: Schema mismatch between ScheduledPost dataclass and queue JSON data

**Solution**: The migration logic in `_load_queue()` handles this automatically by:
1. Generating missing `id` fields for posts from business_scheduler
2. Adding default values for new fields (business_id, template_type, generate_image)
3. Adding default values for old fields (priority, status, etc.)

**Verification**:
```bash
python -m src.x_scheduler stats
# Should show all posts loaded successfully
```

### Issue: Cron jobs not running / posting not happening

**Symptom**: No automated posts being created

**Cause**: Incorrect path in crontab

**Solution**:
```bash
./update_cron_jobs.sh
# OR manually edit crontab:
crontab -e
# Update paths to: /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation
```

**Verification**:
```bash
crontab -l | grep social-media
# All paths should point to shared-multi-tenant/social-media-automation
```

### Issue: Posts stuck in "pending" status

**Symptom**: Posts in queue but not being posted

**Possible Causes**:

1. **Rate Limited** - X API limits posts per day
   ```bash
   # Check rate limit status
   tail -f output/posting.log
   # Look for "Rate limited" messages
   ```

2. **Scheduled time in future** - Posts wait until scheduled_time
   ```bash
   python -m src.x_scheduler list --status pending
   # Check scheduled times
   ```

3. **Cron jobs not running**
   ```bash
   ps aux | grep business_scheduler
   # Should show process if currently running
   ```

**Solution**: Wait for next cron execution or manually process:
```bash
python -m src.business_scheduler process --max 5
```

### Issue: Queue file corrupted

**Symptom**: JSON parsing errors when loading queue

**Solution**:
```bash
# Backup current queue
cp output/scheduled_posts.json output/scheduled_posts.json.backup

# Validate JSON
python -c "import json; json.load(open('output/scheduled_posts.json'))"

# If invalid, restore from backup or recreate
```

## Monitoring Commands

### Check Queue Status
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation

# Overall status
python -m src.business_scheduler status

# Queue statistics
python -m src.x_scheduler stats

# View pending posts
python -m src.x_scheduler list --status pending

# View ready to post
python -m src.x_scheduler list | grep "Scheduled.*$(date +%Y-%m-%d)"
```

### Check Posting Logs
```bash
# Real-time monitoring
tail -f output/posting.log

# Recent activity
tail -100 output/posting.log

# Count posts by status
grep "Tweet posted successfully" output/posting.log | wc -l
grep "Rate limited" output/posting.log | wc -l
```

### Manual Operations

**Process queue immediately**:
```bash
python -m src.business_scheduler process --max 5
```

**Schedule new posts**:
```bash
# Schedule today
python -m src.business_scheduler schedule-day --business marceau-solutions

# Schedule week ahead
python -m src.business_scheduler schedule-week --business marceau-solutions
```

**Clear completed posts**:
```bash
python -m src.x_scheduler clear
```

## Rate Limits

**X API Free Tier**:
- ~25 posts per 24 hours
- 2-minute cooldown between posts

**Current Schedule**: 9 cron jobs (8am - 10pm, every 2 hours)
- Each run processes up to 5-10 posts
- Rate limit ensures ~25 posts/day max

**Expected Behavior**:
- First post succeeds
- Subsequent posts hit rate limit ("Wait 119 seconds")
- Cron job 2 hours later processes next batch

## File Locations

```
/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation/
├── src/
│   ├── x_scheduler.py          # Queue management
│   ├── business_scheduler.py   # Multi-business orchestration
│   └── x_api.py                # X API client
├── output/
│   ├── scheduled_posts.json    # Queue state
│   ├── post_history.json       # Posted tweets
│   ├── posting.log             # Cron job logs
│   └── business_schedule.json  # Business scheduling data
├── config/
│   └── businesses.json         # Business configurations
└── update_cron_jobs.sh         # Cron path fix script
```

## Health Check Script

```bash
#!/bin/bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation

echo "=== Queue Health Check ==="
python -m src.x_scheduler stats 2>/dev/null | grep "Total posts"
python -m src.x_scheduler stats 2>/dev/null | grep -A 5 "By Status"

echo ""
echo "=== Ready to Post ==="
python -c "from src.x_scheduler import PostScheduler; s = PostScheduler(); print(f'{len(s.get_ready_posts())} posts ready')"

echo ""
echo "=== Recent Logs ==="
tail -5 output/posting.log

echo ""
echo "=== Cron Status ==="
crontab -l | grep social-media | wc -l | xargs echo "Active cron jobs:"
```

Save as `health_check.sh` and run: `chmod +x health_check.sh && ./health_check.sh`
