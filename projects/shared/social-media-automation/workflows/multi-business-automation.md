# Workflow: Multi-Business Social Media Automation

## Overview

Automated social media posting system for multiple client businesses. Currently configured for:
- **Square Foot Shipping & Storage** - Logistics/3PL services
- **SW Florida Comfort HVAC** - AC repair and installation

## Quick Start Commands

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/social-media-automation

# List configured businesses
python -m src.business_content_generator list-businesses

# Generate sample content for a business
python -m src.business_content_generator generate --business squarefoot-shipping --count 5

# Generate content for all businesses
python -m src.business_content_generator generate-all --count 3 --save

# Schedule a week of posts for all businesses
python -m src.business_scheduler schedule-week

# Run daily automation (generate + schedule + post)
python -m src.business_scheduler daily-run

# Check status
python -m src.business_scheduler status

# View scheduled posts
python -m src.business_scheduler view-queue
```

## Architecture

```
config/businesses.json         # Business configurations
templates/business_content.json # Content banks and templates per business
src/business_content_generator.py # Content generation
src/business_scheduler.py      # Scheduling and automation
src/x_api.py                   # X/Twitter API posting
output/business_schedule.json  # Schedule state
```

## Adding a New Business

1. **Add to `config/businesses.json`**:
```json
"new-business-id": {
  "name": "Business Name",
  "short_name": "Short Name",
  "owner": "Owner Name",
  "type": "business_type",
  "phone": "(XXX) XXX-XXXX",
  "website": "https://...",
  "services": [...],
  "hashtags": {...},
  "cta_options": [...]
}
```

2. **Add content to `templates/business_content.json`**:
```json
"new-business-id": {
  "content_bank": {
    "pain_points": [...],
    "solutions": [...],
    "benefits": [...],
    "stats": [...],
    "tips": [...]
  },
  "post_templates": {...},
  "campaigns": {...}
}
```

3. **Test**:
```bash
python -m src.business_content_generator generate --business new-business-id --count 3
```

## Automated Posting Setup

### Option 1: Manual Daily Run
Run each morning:
```bash
python -m src.business_scheduler daily-run
```

### Option 2: Cron Job (Recommended)
Add to crontab (`crontab -e`):
```cron
# Run business automation at 8am EST daily
0 8 * * * /Users/williammarceaujr./dev-sandbox/projects/social-media-automation/scripts/run_business_automation.sh >> /tmp/business_automation.log 2>&1
```

### Option 3: LaunchAgent (macOS)
Create `~/Library/LaunchAgents/com.marceausolutions.business-automation.plist`

## Content Strategy

### Square Foot Shipping
| Day | Theme | Content Type |
|-----|-------|--------------|
| Mon | Logistics Tips | Educational |
| Tue | Service Spotlight | Promotional |
| Wed | Client Success | Social Proof |
| Thu | Industry Insights | Stats/Data |
| Fri | Behind the Scenes | Engagement |

### SW Florida Comfort HVAC
| Day | Theme | Content Type |
|-----|-------|--------------|
| Mon | HVAC Tips | Educational |
| Tue | Energy Savings | Value |
| Wed | Testimonials | Social Proof |
| Thu | Maintenance | Reminders |
| Fri | Weekend Ready | Promotional |

## Posting Schedule

- **Posts per business per day**: 2
- **Optimal times (EST)**: 9:00 AM, 3:00 PM
- **Active days**: Monday-Friday
- **Weekend posts**: 1 per day (optional)

## Rate Limits

X Free Tier:
- 50 posts/day max
- 1,500 posts/month
- 2+ minutes between posts

With 2 businesses at 2 posts/day = 4 posts/day total (well under limit)

## Monitoring

```bash
# Check what's scheduled
python -m src.business_scheduler view-queue

# Check overall status
python -m src.business_scheduler status

# Check X API rate limits
python -m src.x_api status
```

## Troubleshooting

**"Rate limit exceeded"**
- Check `output/rate_limit_status.json`
- Wait until reset time
- Reduce posts per day

**"API credentials invalid"**
- Verify X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET in .env
- Re-authenticate if tokens expired

**"Content too long"**
- Tweets must be under 280 characters
- Generator automatically checks length
- Shorten content in templates/business_content.json

## Files Reference

| File | Purpose |
|------|---------|
| `config/businesses.json` | Business configurations |
| `templates/business_content.json` | Content templates and banks |
| `src/business_content_generator.py` | Content generation logic |
| `src/business_scheduler.py` | Scheduling automation |
| `output/business_schedule.json` | Schedule state |
| `output/all_businesses_posts.json` | Generated posts archive |
| `scripts/run_business_automation.sh` | Cron-ready automation script |

## Success Metrics

Track in X Analytics:
- Impressions per post
- Engagement rate (>2% target)
- Profile visits
- Link clicks to website
- Phone calls generated

---

Last Updated: 2026-01-18
