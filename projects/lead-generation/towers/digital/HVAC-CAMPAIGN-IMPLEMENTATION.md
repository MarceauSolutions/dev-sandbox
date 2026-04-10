# SW Florida Comfort HVAC Campaign - Implementation Guide

**Quick Start Guide for Launching the Campaign**

---

## Current Status

✅ **Content Templates:** Complete (templates/business_content.json)
✅ **Infrastructure:** Scheduler built and working
✅ **Initial Posts:** 8 posts already scheduled
🟡 **Configuration:** Need to verify business config
🟡 **Automation:** Need to set up cron jobs
⚠️ **X Account:** Need to verify swflorida-hvac is configured

---

## Step 1: Verify Business Configuration

**Check if swflorida-hvac is configured:**

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# Check current configuration
python -m src.business_scheduler status

# Should show: swflorida-hvac with scheduled posts
```

**Expected Output:**
```
By Business:
  swflorida-hvac: 8 scheduled, 0 posted
```

---

## Step 2: Generate Week 1 Posts

**Generate 28 posts for Week 1** (4 posts/day × 7 days):

```bash
# Generate 20 more posts (we already have 8)
python -m src.business_scheduler schedule-batch \
    --business swflorida-hvac \
    --count 20 \
    --start-date 2026-01-21

# Verify total
python -m src.business_scheduler status
# Should show: swflorida-hvac: 28 scheduled
```

---

## Step 3: Add Grok Images (30-40% of Posts)

**Strategy:** Add images to ~8-10 of the 28 posts (30%)

**Which posts get images:**
- Seasonal reminders
- Stat hooks
- Service promos
- NOT emergency posts (urgency > visuals)

**Generate images:**

```bash
# Generate image for seasonal post
python -m src.grok_image_generator generate \
    --prompt "Professional HVAC technician servicing modern AC unit at Florida home, palm trees, clean professional style" \
    --output output/images/hvac_seasonal_1.png

# Generate image for stat hook
python -m src.grok_image_generator generate \
    --prompt "Infographic showing AC maintenance saves money, split comparison, modern design, blue and white colors" \
    --output output/images/hvac_stat_1.png

# Repeat for 6-8 more posts...
```

**Or use batch generation** (if implemented):
```bash
python -m src.grok_image_generator batch \
    --business swflorida-hvac \
    --count 8 \
    --style professional
```

---

## Step 4: Set Up Posting Automation

**Option A: Manual Testing (Recommended First)**

Test posting 1 post to verify everything works:

```bash
# Post next scheduled post for HVAC
python -m src.x_scheduler process \
    --business swflorida-hvac \
    --limit 1

# Check if it posted successfully
python -m src.x_scheduler history \
    --business swflorida-hvac \
    --last 5
```

**Option B: Automated Cron Jobs**

Once manual test succeeds, set up automation:

```bash
# Edit crontab
crontab -e

# Add these lines for HVAC posting (4 times daily):

# HVAC Morning Post (7 AM)
0 7 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --business swflorida-hvac --limit 1 >> logs/hvac_morning.log 2>&1

# HVAC Midday Post (12 PM)
0 12 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --business swflorida-hvac --limit 1 >> logs/hvac_midday.log 2>&1

# HVAC Afternoon Post (5 PM)
0 17 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --business swflorida-hvac --limit 1 >> logs/hvac_afternoon.log 2>&1

# HVAC Evening Post (9 PM)
0 21 * * * cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --business swflorida-hvac --limit 1 >> logs/hvac_evening.log 2>&1

# Weekly batch generation (Sunday 6 AM)
0 6 * * 0 cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.business_scheduler schedule-batch --business swflorida-hvac --count 28 >> logs/hvac_weekly_gen.log 2>&1
```

**Save and verify:**
```bash
# List cron jobs
crontab -l | grep hvac

# Create logs directory
mkdir -p logs
```

---

## Step 5: Call Tracking Setup

**Add question to Voice AI system** (if Voice AI is answering calls):

Update Voice AI prompt to ask:
```
"How did you hear about us? Was it from our website, a referral, social media, or something else?"
```

**Or manual tracking:**
- Train anyone answering phones to ask this question
- Track in spreadsheet or ClickUp custom field

---

## Step 6: Monitor & Track (First Week)

**Daily Checks:**

```bash
# Check if posts are publishing
python -m src.x_scheduler history --business swflorida-hvac --last 5

# Check posting status
python -m src.business_scheduler status

# Check engagement (if analytics implemented)
python -m src.campaign_analytics report --business swflorida-hvac
```

**What to Watch:**
- ✅ All 4 posts publish each day
- ✅ No errors in logs
- ✅ Impressions: 100+ per post (Week 1 goal)
- ✅ Engagement: 1%+ (likes, retweets, replies)

**Logs to check:**
```bash
# Check cron logs
tail -f logs/hvac_morning.log
tail -f logs/hvac_evening.log

# Check for errors
grep -i error logs/*.log
```

---

## Step 7: First Performance Review (After 7 Days)

**Metrics to Collect:**

```bash
# Posts published
python -m src.x_scheduler history --business swflorida-hvac --count 28

# Get analytics summary
# (Manually check X Analytics dashboard or build analytics script)
```

**Questions to Answer:**
1. Did all 28 posts publish successfully?
2. What was average impressions per post?
3. What was engagement rate?
4. Did we get any profile visits?
5. Did we get any phone calls mentioning social media?

**Adjust Based on Results:**

| If... | Then... |
|-------|---------|
| Engagement <1% | Test different posting times, add more images |
| Engagement >3% | Scale to 5 posts/day |
| No impressions | Check account settings, try hashtags |
| Phone calls = 0 | Add more aggressive CTAs, special offers |
| Phone calls >3 | Document what's working, scale up |

---

## Quick Command Reference

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# Check status
python -m src.business_scheduler status

# Generate 28 posts for week
python -m src.business_scheduler schedule-batch --business swflorida-hvac --count 28

# Post next scheduled post (manual test)
python -m src.x_scheduler process --business swflorida-hvac --limit 1

# View posting history
python -m src.x_scheduler history --business swflorida-hvac --last 10

# Check queue
python -m src.x_scheduler queue --business swflorida-hvac

# Generate Grok image
python -m src.grok_image_generator generate \
    --prompt "HVAC professional illustration" \
    --output output/images/hvac_test.png
```

---

## Troubleshooting

### Issue: Posts not publishing

**Check:**
```bash
# Verify queue has posts
python -m src.x_scheduler queue --business swflorida-hvac

# Check for errors
python -m src.x_scheduler process --business swflorida-hvac --limit 1 --verbose

# Verify X API credentials
grep X_API .env
```

### Issue: Low engagement

**Try:**
- Add more hashtags (#Naples #FortMyers #FloridaLiving)
- Post at different times (test 6 AM, 2 PM, 8 PM)
- Add more images (increase to 50%)
- Use more urgency ("Call now", "Limited time")

### Issue: Schema errors

**If you see ScheduledPost errors:**
```bash
# Check schema fix applied
grep -A 10 "class ScheduledPost" src/x_scheduler.py

# Should include: business_id, template_type, generate_image
```

### Issue: Grok images not working

**Check:**
```bash
# Verify Grok API key
grep XAI_API_KEY .env

# Test manual generation
python -c "from execution.grok_image_gen import GrokImageGenerator; g = GrokImageGenerator(); print(g.generate_image('test image', 1))"
```

---

## Success Checklist (Week 1)

- [ ] Verified 28 posts scheduled for Week 1
- [ ] Generated 6-8 Grok images
- [ ] Tested manual posting (1 post)
- [ ] Set up cron jobs (4 posts/day)
- [ ] Added call tracking question
- [ ] Monitored first 3 days of posting
- [ ] Documented any issues
- [ ] Collected Week 1 metrics
- [ ] Scheduled Week 1 review meeting

---

## Next Steps After Week 1

1. **Review Performance:** Analyze Week 1 data
2. **Optimize Templates:** Double down on high-engagement posts
3. **Generate Month 1 Content:** Create full 120-post library
4. **Add Tracking:** Implement analytics dashboard
5. **Test A/B:** Emergency vs Educational content
6. **Scale:** If successful, increase to 5 posts/day

---

## Contact & Support

**Questions about:**
- Content templates → See `templates/business_content.json`
- Posting schedule → See `src/business_scheduler.py`
- X API → See `src/x_scheduler.py`
- Grok images → See `execution/grok_image_gen.py`
- Campaign strategy → See `SW-FLORIDA-HVAC-CAMPAIGN-STRATEGY.md`

**Get help:**
```bash
python -m src.business_scheduler --help
python -m src.x_scheduler --help
```

**Refer to SOPs:**
- SOP 18: SMS Campaign Execution (similar workflow)
- SOP 22: Campaign Analytics & Tracking
- SOP 23: Cold Outreach Strategy Development
