# Workflow: Post Performance Tracking & Optimization

## Overview

Track social media post performance to optimize content strategy, posting times, and image investment ROI.

## Key Metrics Tracked

1. **Engagement Metrics**
   - Impressions (views)
   - Likes
   - Retweets
   - Replies
   - Engagement rate = (likes + retweets + replies) / impressions × 100

2. **Image ROI**
   - Posts with vs without Grok images
   - Cost per engagement for image posts ($0.07 / total engagements)
   - Engagement lift from images

3. **Template Performance**
   - Which templates get highest engagement
   - Average engagement rate per template

4. **Timing Optimization**
   - Best hours to post (0-23)
   - Best days of week
   - Engagement rates by time slot

## Data Collection Workflow

### Manual Recording (After Each Post)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

python -m src.post_analytics record \
    --post-id "1234567890" \
    --business-id "marceau-solutions" \
    --content "Your post text here" \
    --template "service_highlight" \
    --campaign "general-awareness" \
    --posted-at "2026-01-20T09:00:00Z" \
    --has-image \
    --impressions 1000 \
    --likes 50 \
    --retweets 10 \
    --replies 5
```

**When to record:**
- After 24 hours (engagement stabilizes)
- After 7 days (for long-tail engagement)

### Automated Collection (Future Enhancement)

Use X API to automatically fetch metrics:

```python
# In x_scheduler.py or new script
from src.post_analytics import PostAnalytics
from src.x_api import XAPIClient

client = XAPIClient()
analytics = PostAnalytics()

# Get tweet metrics from X API
tweet_metrics = client.get_tweet_metrics(tweet_id)

# Record automatically
analytics.record_post_metrics(
    post_id=tweet_id,
    business_id=business_id,
    content=tweet_text,
    template_type=template,
    campaign=campaign,
    posted_at=posted_at,
    has_image=bool(media_paths),
    impressions=tweet_metrics["impressions"],
    likes=tweet_metrics["likes"],
    retweets=tweet_metrics["retweets"],
    replies=tweet_metrics["replies"]
)
```

## Analysis Workflows

### 1. Weekly Performance Review

Run every Monday morning:

```bash
# Generate full report
python -m src.post_analytics report
```

**Review:**
- Overall engagement trends
- Image vs non-image performance
- Are images worth $0.07 per post?

**Decision:**
- Increase/decrease image percentage based on ROI
- If engagement lift < 50% and cost/engagement > $0.01, reduce images
- If engagement lift > 100%, increase images

### 2. Template Optimization

Run bi-weekly:

```bash
# See which templates perform best
python -m src.post_analytics templates
```

**Actions:**
- Increase frequency of top 3 templates
- Reduce or retire bottom 2 templates
- Update content bank for low-performing templates

### 3. Posting Time Optimization

Run monthly:

```bash
# Find best posting times
python -m src.post_analytics best-times
```

**Actions:**
- Update `config/businesses.json` with optimal posting times
- Shift schedule toward high-engagement hours
- Remove low-engagement time slots

Example update:
```json
{
  "marceau-solutions": {
    "posting_schedule": {
      "optimal_times": [9, 12, 18, 20]  // Update based on analytics
    }
  }
}
```

### 4. Image ROI Analysis

Run monthly:

```bash
# Compare image vs non-image performance
python -m src.post_analytics compare-media
```

**Decision Matrix:**

| Engagement Lift | Cost/Engagement | Action |
|----------------|-----------------|--------|
| > 100% | < $0.01 | Increase to 75% images |
| 50-100% | < $0.01 | Keep at 50% images |
| < 50% | > $0.01 | Reduce to 25% images |
| < 25% | > $0.02 | Stop using images |

## Data Files

| File | Purpose |
|------|---------|
| `output/post_analytics.json` | All post metrics and summary stats |
| `output/scheduled_posts.json` | Posted queue (source for automation) |
| `output/images/` | Generated Grok images |

## Success Criteria

### Minimum Data Requirements

Before making strategy changes:
- **At least 30 posts** tracked (statistical significance)
- **Mix of image/non-image** (15+ each)
- **Multiple templates** tested (5+ per template)
- **7+ days** of data (account for day-of-week variance)

### KPIs to Track

| Metric | Target | Action if Below |
|--------|--------|----------------|
| Avg Engagement Rate | > 2% | Review template quality |
| Image Engagement Lift | > 50% | Reduce image % if below |
| Cost per Engagement | < $0.01 | Reduce images if above |
| Posts per Day | 20-30 | Adjust schedule |

## Optimization Cycle

```
1. POST → 2. COLLECT (24h later) → 3. ANALYZE (weekly) → 4. OPTIMIZE (update config)
   ↑                                                                          │
   └──────────────────────────────────────────────────────────────────────────┘
```

### Monthly Optimization Process

**Week 1:** Collect data, no changes
**Week 2:** Collect data, no changes
**Week 3:** Run analytics, identify opportunities
**Week 4:** Implement 1-2 changes, A/B test

**Changes to test (one at a time):**
- Increase/decrease image percentage
- Shift posting times
- Increase frequency of top template
- Reduce frequency of bottom template
- Test new template variant

## Sample Report Interpretation

```
SUMMARY
Total Posts: 50
Posts with Images: 25 (50.0%)
Avg Engagement Rate: 3.2%

IMAGE VS NON-IMAGE
With Images: 4.1% engagement, $0.0088 per engagement
Without Images: 2.3% engagement
Lift: +78% engagement

DECISION: Images are working! 78% lift at $0.009/engagement is excellent ROI.
ACTION: Keep 50% image strategy.
```

```
TOP TEMPLATES
1. case_study_update - 5.2% engagement
2. service_highlight - 3.8% engagement
3. stat_insight - 3.1% engagement
4. behind_scenes - 1.9% engagement
5. tech_tutorial - 1.4% engagement

DECISION: Case studies perform 2.7x better than tutorials
ACTION: Increase case_study from 20% to 30%, reduce tech_tutorial to 10%
```

```
BEST POSTING TIMES
Top Hours: 12:00 (4.2%), 18:00 (3.9%), 9:00 (3.1%)
Top Days: Tuesday (3.8%), Thursday (3.5%), Monday (3.2%)

DECISION: Lunchtime and evening perform best
ACTION: Add more posts at 12:00 and 18:00, reduce morning posts
```

## Integration with Existing Workflows

### With SMS Campaigns (SOP 18-19)

Track X post engagement alongside SMS response rates to compare channel effectiveness.

### With Content Generation

Feed template performance data back into content generation to prioritize high-performing templates.

### With Scheduling

Use best-times analysis to update posting schedule automatically:

```python
# In business_scheduler.py
from src.post_analytics import PostAnalytics

analytics = PostAnalytics()
best_times = analytics.find_best_posting_times()

# Use top 5 hours for scheduling
optimal_hours = [hour for hour, _ in best_times["best_hours"][:5]]
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Low engagement across all posts | Content quality or audience issue | Review content bank, check follower growth |
| Images not improving engagement | Poor image prompts or irrelevant images | Refine `_build_image_prompt()` method |
| Engagement dropping over time | Audience fatigue or algorithm change | Increase content variety, test new templates |
| High variance in metrics | Small sample size | Collect more data (30+ posts minimum) |

## Future Enhancements

1. **Automated X API Integration**
   - Fetch metrics automatically after 24h
   - No manual recording needed

2. **A/B Testing Framework**
   - Test image prompts head-to-head
   - Test template variants
   - Statistical significance testing

3. **Predictive Analytics**
   - Predict engagement before posting
   - Recommend optimal template for time slot

4. **Multi-Platform Tracking**
   - LinkedIn, Instagram, TikTok
   - Cross-platform performance comparison

## References

- X API Documentation: https://developer.twitter.com/en/docs/twitter-api/metrics
- `src/post_analytics.py`: Analytics engine
- `src/business_scheduler.py`: Posting automation
- `src/business_content_generator.py`: Template system
