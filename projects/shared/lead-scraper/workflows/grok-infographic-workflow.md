# Grok Imagine Infographic Workflow

## Overview
Generate professional infographics using Grok Imagine (Aurora model) for cold outreach campaigns and social media content.

**Cost**: $0.07 per image
**Time**: ~10-15 seconds per image
**API**: xAI API (XAI_API_KEY in .env)

## Use Cases

### Cold Outreach Infographics
Send professional infographics via MMS to stand out from text-only messages.

Available templates:
- `no_website` - "80% of customers search online first"
- `few_reviews` - "93% read reviews before buying"
- `no_online_payments` - "67% prefer paying online"
- `local_seo` - "46% of Google searches are local"
- `competitor_analysis` - "Your competitors are already online"

### Social Media Infographics
Create shareable content for X/Twitter and LinkedIn.

Available templates:
- `automation_stats` - "AI Automation saves 40+ hours/month"
- `business_growth` - "3X Your Business Growth"
- `time_savings` - "What would you do with 10 extra hours?"
- `ai_tips` - "5 Ways AI Can Help Your Business Today"
- `cost_comparison` - "Hire an Employee vs. AI Automation"

## Commands

### List Available Templates
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.grok_infographic_gen list
```

### Generate Cold Outreach Infographic
```bash
python -m src.grok_infographic_gen cold-outreach --pain-point no_website
```

### Generate Social Media Infographic
```bash
python -m src.grok_infographic_gen social --topic automation_stats
```

### Generate Custom Infographic
```bash
python -m src.grok_infographic_gen custom --text "Your custom message here" --style professional
```

Styles: `professional`, `modern`, `minimal`, `bold`, `stats`

### Generate Batch (All Templates)
```bash
# All cold outreach templates
python -m src.grok_infographic_gen batch --type cold_outreach --all

# All social media templates
python -m src.grok_infographic_gen batch --type social_media --all

# Specific items
python -m src.grok_infographic_gen batch --type cold_outreach --items no_website few_reviews
```

## Output Location
All generated infographics are saved to:
```
projects/shared/lead-scraper/output/infographics/
```

Filename format: `{type}_{template}_{timestamp}.png`

## Best Practices

### For Cold Outreach
1. **Match infographic to pain point** - Use `no_website` template for leads without websites
2. **Attach to MMS** - Higher engagement than text-only SMS
3. **Follow up with value** - Don't just send image; include a personalized message

### For Social Media
1. **Post with engaging caption** - The infographic grabs attention; caption drives action
2. **Add your logo** - Grok's text accuracy isn't perfect; overlay real logo in post-processing
3. **Schedule strategically** - Use `x_scheduler.py` to queue posts at optimal times

### Prompt Tips for Custom Infographics
- Keep text short (20 words max for best accuracy)
- Be specific about colors and style
- Request "text clearly visible and spelled correctly"
- Avoid complex layouts with multiple text blocks

## Cost Tracking
Session costs are displayed after each generation. For batch operations:
```
📊 BATCH SUMMARY:
   Generated: 5/5
   Total cost: $0.35
```

## Integration with Other Tools

### With SMS Campaign (MMS)
```python
from src.grok_infographic_gen import GrokInfographicGenerator

# Generate infographic
gen = GrokInfographicGenerator()
result = gen.generate_cold_outreach("no_website")

# Use path in MMS (Twilio supports MMS with media URLs)
image_path = result['path']
```

### With Social Media Scheduler
```python
from src.grok_infographic_gen import GrokInfographicGenerator
from src.x_scheduler import PostScheduler

# Generate and schedule
gen = GrokInfographicGenerator()
result = gen.generate_social_media("automation_stats")

# Add to queue with media
scheduler = PostScheduler()
# Note: X API media attachment would be handled separately
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "XAI_API_KEY not found" | Add key to `/Users/williammarceaujr./dev-sandbox/.env` |
| Text in image misspelled | AI limitation; overlay correct text in post-processing |
| Image too generic | Add more specific details to prompt in template |
| API timeout | Increase timeout or retry; network issues |

## Examples

### Generated Cold Outreach Infographic (no_website)
- Dark professional background
- Large "80%" statistic
- "Is your business invisible?" subtext
- "Free Website Audit" CTA button
- Branding placeholder at bottom

### Generated Social Media Infographic (automation_stats)
- Cyan gradient background
- "AI Automation saves 40+ hours/month" headline
- Icon list with Email, Social, Lead Follow-up
- Clean, shareable format

## Session History
- 2026-01-26: Initial implementation with 5 cold outreach + 5 social media templates
- Cost per batch (all templates): ~$0.70
