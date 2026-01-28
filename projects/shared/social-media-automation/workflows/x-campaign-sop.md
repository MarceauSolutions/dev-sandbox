# SOP: X Platform Campaign Execution

*Last Updated: 2026-01-21*
*Version: 2.0.0*

## Overview

Execute automated social media campaigns on X (Twitter) with rate limiting, UTM tracking, and engagement analytics.

## X Premium Subscription ($8/month) - ACTIVE

We now have X Premium, which provides significant advantages:

### Content Capabilities
| Feature | Free | Premium ($8/mo) |
|---------|------|-----------------|
| Post length | 280 chars | **25,000 chars** |
| Video upload | 2 min | **3 hours (8GB)** |
| Edit posts | ❌ | ✅ (limited) |
| Bookmark folders | ❌ | ✅ |

### Visibility & Reach
- **Blue Checkmark**: Verified account (after approval)
- **Reply Prioritization**: Our replies appear higher in threads
- **Algorithmic Boost**: Posts get preference in For You feed
- **50% fewer ads**: Better user experience when browsing

### Monetization (Future)
- **Creator Revenue Sharing**: Eligible to apply (requires 500+ followers, 5M impressions in 3 months)
- **Creator Subscriptions**: Can offer paid subscriptions to followers

### AI & Tools
- **Grok Access**: X's AI assistant for research and content ideas
- **Media Studio**: Advanced media management
- **Enhanced Analytics**: Detailed audience insights

---

## API Tier (Separate from Premium)

**Current: Free API Tier Limits:**
- 1,500 posts/month (~50/day)
- 10,000 read requests/month
- 2-minute minimum gap between posts

**Note**: X Premium subscription does NOT upgrade API access. API upgrades require separate Basic ($100/mo) or Pro ($5,000/mo) plans.

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

### Product Launch (280 chars - API posts)

```
[PAIN POINT] keeping you up at night?

[SOLUTION] does [BENEFIT] in [TIMEFRAME].

Check it out: [LINK]

#[Niche] #[Industry]
```

### Social Proof (280 chars - API posts)

```
"[TESTIMONIAL QUOTE]" - [NAME], [TITLE]

See how [PRODUCT] helped [CUSTOMER] achieve [RESULT].

[LINK]
```

### Value-First (280 chars - API posts)

```
[NUMBER] [THING] that [OUTCOME]:

1. [TIP]
2. [TIP]
3. [TIP]

Want more? [LINK]
```

---

## Premium Long-Form Templates (25,000 chars - Manual posts via web/app)

### Educational Thread Starter

```
🧵 [NUMBER] things I learned about [TOPIC] that changed everything:

[INTRODUCTION - 2-3 sentences explaining why this matters]

Let me break it down...

1/ [POINT ONE]
[Detailed explanation with specific examples, data, or case studies.
Premium allows you to include the full context without thread fragmentation.]

2/ [POINT TWO]
[Continue with rich detail...]

[... continue for all points ...]

Key takeaway: [SUMMARY]

If this was helpful, follow for more [TOPIC] insights.

Want the full breakdown? [LINK]
```

### Case Study Post

```
How [CLIENT/EXAMPLE] went from [BEFORE STATE] to [AFTER STATE] in [TIMEFRAME]:

📊 The Situation:
[Detailed description of the problem - be specific with numbers]

🔧 What We Did:
[Step-by-step breakdown of the solution]

📈 The Results:
• [Metric 1]: [Before] → [After]
• [Metric 2]: [Before] → [After]
• [Metric 3]: [Before] → [After]

💡 Key Lessons:
1. [Lesson]
2. [Lesson]
3. [Lesson]

Want similar results? Let's talk: [LINK]
```

### Authority Building Post

```
I've spent [TIME] working on [EXPERTISE AREA]. Here's what most people get wrong:

❌ Common Mistake #1: [MISTAKE]
Why it fails: [EXPLANATION]
What works instead: [SOLUTION]

❌ Common Mistake #2: [MISTAKE]
Why it fails: [EXPLANATION]
What works instead: [SOLUTION]

❌ Common Mistake #3: [MISTAKE]
Why it fails: [EXPLANATION]
What works instead: [SOLUTION]

The pattern? [INSIGHT]

I help [TARGET AUDIENCE] avoid these mistakes and [OUTCOME].

DM "HELP" or visit [LINK] to learn more.
```

---

## Premium Video Strategy (Up to 3 hours)

With Premium, you can upload videos up to 3 hours and 8GB. Use this for:

1. **Full Tutorials**: Complete walkthroughs instead of clips
2. **Webinar Replays**: Post entire recordings
3. **Client Testimonials**: Unedited, authentic social proof
4. **Behind-the-Scenes**: Extended day-in-the-life content
5. **Screen Recordings**: Full software demos

**Best Practices:**
- Add captions (80% watch without sound)
- Hook in first 3 seconds
- Include CTA in video and caption
- Post native (not YouTube links) for better reach

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

- [x] X Premium subscription active ($8/mo)
- [ ] X API credentials configured and verified
- [ ] First test post successfully published
- [ ] UTM tracking working on links
- [ ] Engagement metrics updating
- [ ] Campaign achieving target engagement rate (>2%)
- [ ] Blue checkmark verified
- [ ] First long-form post (>280 chars) published manually

---

## Premium Strategy Recommendations

### Daily Workflow
1. **API Posts (automated)**: Short announcements, links, quick tips
2. **Manual Premium Posts (1-2/day)**: Long-form value content, threads, case studies
3. **Video Content (1-2/week)**: Tutorials, demos, testimonials

### Content Mix
| Type | Frequency | Channel |
|------|-----------|---------|
| Quick tips/links | 3-5/day | API (automated) |
| Long-form educational | 1/day | Manual (Premium) |
| Video content | 2/week | Manual (Premium) |
| Engagement replies | Ongoing | Manual (Premium boost) |

### Monetization Path
1. ✅ Get Premium ($8/mo) - DONE
2. Build to 500+ followers
3. Generate 5M impressions over 3 months
4. Apply for Creator Revenue Sharing
5. Consider Premium+ ($40/mo) when monetized

---

## References

- [X API Documentation](https://developer.x.com/en/docs)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [UTM Best Practices](https://support.google.com/analytics/answer/1033867)
- [SOP 24: Daily/Weekly Digest](../../personal-assistant/workflows/daily-routine-sop.md)
- [X Premium Features](https://socialrails.com/social-media-terms/x-premium-features)
- [Is X Premium Worth It?](https://www.tryordinal.com/blog/is-x-premium-worth-it-a-complete-guide-for-creators-and-brands)
