# SOP: X Platform Campaign Execution

*Last Updated: 2026-01-15*
*Version: 1.0.0*

## Overview

Execute automated social media campaigns on X (Twitter) with rate limiting, UTM tracking, and engagement analytics.

**Free Tier Limits:**
- 1,500 posts/month (~50/day)
- 10,000 read requests/month
- 2-minute minimum gap between posts

## Prerequisites

### Environment Variables

Add to `.env`:

```bash
# X API Credentials (from developer.twitter.com)
X_API_KEY=your_consumer_key
X_API_SECRET=your_consumer_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
X_BEARER_TOKEN=your_bearer_token
```

### Install Dependencies

```bash
pip install tweepy python-dotenv
```

### Verify Setup

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# Check credentials
python -m src.x_api me

# Check rate limits
python -m src.x_api status
```

---

## Campaign Workflow

### Step 1: Create Campaign Content

**Objective**: Prepare posts with UTM-tracked links

**Guidelines:**
- Max 280 characters per post
- Include call-to-action
- Add landing page link (UTM auto-added)
- Use relevant hashtags (1-2 max)

**Example Posts:**

```
Fitness coaches: Stop leaving money on the table.

Our AI-powered landing page builder converts 3x better than generic templates.

Try it free: https://marceausolutions.com/fitness

#FitnessCoach #BusinessGrowth
```

---

### Step 2: Add Posts to Queue

**Commands:**

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# Add single post (auto-schedules to next optimal time)
python -m src.x_scheduler add "Your tweet text https://marceausolutions.com/fitness" \
    --campaign fitness-launch \
    --priority normal

# Add with specific schedule
python -m src.x_scheduler add "Your tweet text" \
    --schedule "2026-01-20 10:00" \
    --campaign fitness-launch

# Add high priority (posts sooner)
python -m src.x_scheduler add "Breaking news!" \
    --priority high \
    --campaign announcements

# View queue
python -m src.x_scheduler list
```

**Priority Levels:**
- `urgent`: Processed first, ASAP
- `high`: Processed early
- `normal`: Standard scheduling
- `low`: Fill-in when quota allows

---

### Step 3: Review Queue

**Check before processing:**

```bash
# List all scheduled
python -m src.x_scheduler list --status scheduled

# View queue statistics
python -m src.x_scheduler stats

# Check rate limit status
python -m src.x_api status
```

**Review Checklist:**
- [ ] All links include UTM tracking
- [ ] No typos or broken links
- [ ] Posts are within 280 characters
- [ ] Schedule times are optimal (9AM, 12PM, 3PM, 6PM, 8PM)

---

### Step 4: Process Queue (Post)

**Dry run first:**

```bash
# Preview what will be posted
python -m src.x_scheduler process --dry-run --max 3
```

**Post for real:**

```bash
# Process up to 5 posts
python -m src.x_scheduler process --max 5

# Process all ready posts
python -m src.x_scheduler process
```

**Automatic Processing (Future):**
- Set up cron job to run every hour
- `0 * * * * cd /path/to/project && python -m src.x_scheduler process`

---

### Step 5: Track Engagement

**Wait 24-48 hours for engagement data, then:**

```bash
# Update metrics for all posted tweets
python -m src.engagement_tracker update

# View overall report
python -m src.engagement_tracker report

# View campaign-specific report
python -m src.engagement_tracker report --campaign fitness-launch

# View conversion funnel
python -m src.engagement_tracker funnel --campaign fitness-launch

# Export to CSV
python -m src.engagement_tracker export
```

---

### Step 6: Analyze & Optimize

**Review:**

```bash
# Daily engagement stats
python -m src.engagement_tracker daily --days 7

# Link click stats
python -m src.link_manager stats
```

**Optimization Actions:**
1. Identify top-performing posts (highest engagement rate)
2. Create variations of winning posts
3. Pause/cancel underperforming scheduled posts
4. Adjust posting times based on engagement data

```bash
# Cancel underperforming scheduled post
python -m src.x_scheduler cancel POST_ID

# Reschedule to better time
python -m src.x_scheduler reschedule POST_ID "2026-01-21 18:00"
```

---

## Quick Reference Commands

```bash
# Project directory
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# === X API ===
python -m src.x_api status          # Rate limit status
python -m src.x_api me              # Account info
python -m src.x_api post "text"     # Direct post (bypasses scheduler)
python -m src.x_api get TWEET_ID    # Get tweet details

# === Scheduler ===
python -m src.x_scheduler add "text" --campaign NAME --priority normal
python -m src.x_scheduler list
python -m src.x_scheduler list --status scheduled
python -m src.x_scheduler stats
python -m src.x_scheduler process --dry-run
python -m src.x_scheduler process --max 5
python -m src.x_scheduler cancel POST_ID
python -m src.x_scheduler clear     # Remove completed posts

# === Link Manager ===
python -m src.link_manager track "https://example.com" --campaign NAME
python -m src.link_manager process "text with https://marceausolutions.com link"
python -m src.link_manager stats
python -m src.link_manager list --campaign NAME

# === Engagement ===
python -m src.engagement_tracker update
python -m src.engagement_tracker report --campaign NAME
python -m src.engagement_tracker daily --days 7
python -m src.engagement_tracker funnel
python -m src.engagement_tracker export
```

---

## Rate Limit Strategy

**Free Tier Budget: 1,500 posts/month**

| Strategy | Posts/Day | Posts/Month | Use Case |
|----------|-----------|-------------|----------|
| Conservative | 30 | 900 | Steady growth |
| Standard | 50 | 1,500 | Maximum reach |
| Burst | 75 | Exceeds | Campaign launches only |

**Optimal Posting Times (EST):**
- 9:00 AM - Morning commute
- 12:00 PM - Lunch break
- 3:00 PM - Afternoon slump
- 6:00 PM - End of workday
- 8:00 PM - Evening browsing

**Rate Limit Enforcement:**
- System tracks daily/monthly limits
- Minimum 2-minute gap between posts
- Automatic rejection if limits exceeded
- Status check before each post

---

## UTM Tracking Integration

**Automatic UTM Parameters:**

All links to configured landing pages automatically get:
- `utm_source=x`
- `utm_medium=social`
- `utm_campaign=[campaign_name]`

**Example:**

Original: `https://marceausolutions.com/fitness`

Tracked: `https://marceausolutions.com/fitness?utm_source=x&utm_medium=social&utm_campaign=fitness-launch`

**Landing Pages Tracked:**
- marceausolutions.com
- (Add more in `link_manager.py` LANDING_PAGES)

---

## Campaign Templates

### Product Launch

```
[PAIN POINT] keeping you up at night?

[SOLUTION] does [BENEFIT] in [TIMEFRAME].

Check it out: [LINK]

#[Niche] #[Industry]
```

### Social Proof

```
"[TESTIMONIAL QUOTE]" - [NAME], [TITLE]

See how [PRODUCT] helped [CUSTOMER] achieve [RESULT].

[LINK]
```

### Value-First

```
[NUMBER] [THING] that [OUTCOME]:

1. [TIP]
2. [TIP]
3. [TIP]

Want more? [LINK]
```

---

## Conversion Funnel

```
Post (Impressions)
    ↓
Engagement (Likes/Retweets)
    ↓
Click (UTM-tracked link)
    ↓
Landing Page View
    ↓
Form Submission (Conversion)
```

**Track at each stage:**
1. **Impressions**: X API metrics
2. **Engagement**: X API metrics
3. **Clicks**: LinkManager click tracking
4. **Conversions**: Form webhook / Google Analytics

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Rate limited" message | Wait for reset (check `x_api status`) |
| "Client not ready" | Check X API credentials in `.env` |
| "Tweet too long" | Keep under 280 chars (UTM adds ~80) |
| Posts not scheduling | Check queue with `list --status pending` |
| No engagement data | Wait 24-48h, then run `update` |
| Links not tracked | Verify domain in LANDING_PAGES list |

---

## Success Criteria

- [ ] X API credentials configured and verified
- [ ] First test post successfully published
- [ ] UTM tracking working on links
- [ ] Engagement metrics updating
- [ ] Campaign achieving target engagement rate (>2%)

---

## References

- [X API Documentation](https://developer.x.com/en/docs)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [UTM Best Practices](https://support.google.com/analytics/answer/1033867)
- [SOP 24: Daily/Weekly Digest](../../personal-assistant/workflows/daily-routine-sop.md)
