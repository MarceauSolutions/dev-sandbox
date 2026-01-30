# Claude Code Handoff: X Social Media Strategy Update

**Date:** 2026-01-30
**From:** Clawdbot (EC2)
**To:** Claude Code (MacBook)
**Priority:** High

---

## Executive Summary

William wants to pivot the X/Twitter content strategy from generic fitness tips to **"AI Builder in Public"** - showcasing the actual tools and systems being built at Marceau Solutions. This document contains everything needed to implement the new strategy.

---

## Current State

### Queue Status
- **Pending posts:** 0 (queue is empty - clean slate)
- **No posts need deletion** - we can start fresh

### What Was Posting
- Generic fitness coaching tips
- SquareFoot Shipping promos
- SW Florida HVAC content
- Links to marceausolutions.com/fitness

### The Problem
Content doesn't reflect William's actual expertise: **building AI automation systems**. The old strategy attracts fitness enthusiasts. The new strategy attracts business owners and AI builders - higher value audience.

---

## New Strategy: "AI Builder in Public"

### Positioning
**"Building AI automation for small businesses. Real tools. Real results."**

### Target Audience
1. Small business owners wanting automation
2. AI builders and developers
3. Solopreneurs looking for efficiency tools
4. Tech-curious entrepreneurs

### Content Pillars

| Pillar | % | Description |
|--------|---|-------------|
| Build Updates | 30% | What's being shipped (MCPs, Voice AI, automations) |
| Real Metrics | 25% | Client results with actual numbers |
| AI Insights | 25% | Observations about AI/automation for small business |
| Technical Tutorials | 15% | How-to content demonstrating expertise |
| Hot Takes | 5% | Contrarian views that spark discussion |

---

## Tasks to Complete

### 1. Generate New Content Queue

**Location:** `projects/shared/social-media-automation/`

**Use the new templates in:** `templates/ai-builder-content.json`

**Generate 2 weeks of posts (56 posts at 4/day):**

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# Use the business scheduler to generate posts
python -m src.business_scheduler generate \
    --business marceau-solutions \
    --template ai-builder \
    --days 14 \
    --posts-per-day 4
```

If that script doesn't exist or needs updating, create posts using `x_scheduler.py`:

```bash
python -m src.x_scheduler add "YOUR_POST_TEXT" \
    --priority normal \
    --campaign ai-builder-public
```

### 2. Update Content Templates

The new content template is already created at:
`templates/ai-builder-content.json`

**Update `templates/marceau-solutions-content.json`** to reference the new AI builder focus instead of fitness coaching.

Key changes:
- Change `service_offering` to focus on AI automation (Voice AI, MCPs, CRM)
- Update `content_bank` with AI/automation pain points and solutions
- Keep the case studies (they're good) but frame around automation ROI

### 3. Posting Frequency

**New Schedule:**
- **Weekdays:** 4 posts/day at 9 AM, 12 PM, 3 PM, 6 PM EST
- **Weekends:** 1-2 posts/day (reduce frequency)
- **Total:** ~24-28 posts/week

**Update `templates/content_strategy.json`:**

```json
{
  "posting_schedule": {
    "weekday": {
      "posts_per_day": 4,
      "times": ["09:00", "12:00", "15:00", "18:00"]
    },
    "weekend": {
      "posts_per_day": 2,
      "times": ["10:00", "16:00"]
    },
    "timezone": "America/New_York"
  }
}
```

### 4. Integrate Grok Image Generation

**Goal:** 50% of posts should have AI-generated images

**API Setup:**
- API Key location: `.env` file, variable `XAI_API_KEY`
- The key is already configured and verified working

**Implementation:**

#### Option A: Update existing `grok_image_gen.py`

Located at: `execution/grok_image_gen.py`

```python
from execution.grok_image_gen import GrokImageGenerator

grok = GrokImageGenerator()

# Generate image for a post
result = grok.generate_image(
    prompt="Modern tech workspace with code on screens, AI visualization, professional developer aesthetic",
    count=1
)
image_url = result[0]
```

#### Option B: Create integrated post generator

Create `src/ai_post_generator.py`:

```python
#!/usr/bin/env python3
"""
AI Post Generator with Grok Image Integration

Generates posts from templates with optional AI-generated images.
"""

import os
import json
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import existing modules
from .x_scheduler import PostScheduler
from ..execution.grok_image_gen import GrokImageGenerator

class AIPostGenerator:
    def __init__(self):
        self.scheduler = PostScheduler()
        self.grok = GrokImageGenerator()
        self.templates = self._load_templates()
    
    def _load_templates(self):
        template_path = Path(__file__).parent.parent / "templates" / "ai-builder-content.json"
        with open(template_path) as f:
            return json.load(f)
    
    def generate_post_with_image(self, pillar: str, post_text: str) -> dict:
        """Generate a post with an AI-generated image."""
        
        # Get image prompts for this pillar
        prompts = self.templates["ai-builder-strategy"]["image_prompts_for_grok"].get(pillar, [])
        
        if not prompts:
            return {"text": post_text, "image_url": None}
        
        # Generate image
        prompt = random.choice(prompts)
        try:
            result = self.grok.generate_image(prompt, count=1)
            image_url = result[0] if result else None
        except Exception as e:
            print(f"Image generation failed: {e}")
            image_url = None
        
        return {
            "text": post_text,
            "image_url": image_url,
            "image_prompt": prompt
        }
    
    def queue_post_with_image(self, pillar: str, post_text: str, campaign: str = "ai-builder-public"):
        """Queue a post, downloading image if generated."""
        
        result = self.generate_post_with_image(pillar, post_text)
        
        media_paths = []
        if result["image_url"]:
            # Download image to local path
            import requests
            image_path = f"output/images/{hash(post_text)}.png"
            os.makedirs("output/images", exist_ok=True)
            
            response = requests.get(result["image_url"])
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            media_paths = [image_path]
        
        # Add to queue
        return self.scheduler.add_post(
            text=post_text,
            campaign=campaign,
            media_paths=media_paths
        )
```

#### Image Prompt Library

Use these prompts from `ai-builder-content.json`:

**Build Updates:**
- "Modern tech workspace with multiple monitors showing code and dashboards, professional developer aesthetic, dark mode UI, clean minimalist design"
- "Abstract visualization of AI neural network connecting to business icons, blue and purple gradient, futuristic but professional"

**Real Metrics:**
- "Professional business infographic showing upward trending charts, modern data visualization, green growth indicators"
- "Before/after split showing chaos vs organized dashboard, high contrast professional style"

**AI Insights:**
- "Thought leader style image: abstract brain connected to business elements, modern AI visualization"
- "Light bulb moment visualization: AI-themed eureka concept, modern tech aesthetic"

**Technical Tutorials:**
- "Clean architecture diagram showing system components and data flow, modern technical documentation style"
- "Code editor screenshot aesthetic with highlighted syntax, modern dark theme"

**Hot Takes:**
- "Bold statement graphic with strong typography, contrarian energy, modern social media aesthetic"
- "Disruption concept: old way crossed out, new way highlighted, bold modern design"

### 5. Delete/Archive Old Content

**Current queue is empty** - no deletions needed.

**If old scheduled posts exist in future**, use:

```bash
# View queue
python -m src.x_scheduler list --status pending

# Archive old posts that don't fit new strategy
python -m src.x_scheduler archive-old --hours 0  # Archives all overdue

# Or manually cancel specific posts
python -m src.x_scheduler cancel POST_ID
```

**Content to DELETE if found:**
- Generic fitness tips without automation angle
- Posts linking to marceausolutions.com/fitness (unless relevant to fitness automation)
- SW Florida HVAC and SquareFoot Shipping content (unless William wants to keep these)

**Content to KEEP:**
- Any posts with real metrics/case studies
- Voice AI deployment results
- Apollo MCP announcements
- Any "building in public" style content

---

## Sample Posts Ready to Queue

Copy these directly into the scheduler:

### Build Updates (Week 1)

```
Just shipped: Apollo MCP v1.1.0

Natural language lead scraping for Claude.

→ "Find HVAC companies in Naples"
→ Auto-qualify by job title
→ Export to CRM in one command

Built with Python + Apollo API

PyPI: pip install apollo-mcp

#MCP #BuildInPublic
```

```
This week I built:

A 7-touch SMS follow-up sequence that runs itself.

Day 0: Initial outreach
Day 2: "Still interested?"
Day 5: Value add
Day 10: Case study
Day 15: Last chance

111 leads enrolled. Watching the data.

#Automation
```

```
Deployed to production: Voice AI phone system

What it does:
• Answers calls 24/7
• Qualifies leads (name, need, urgency)
• Books appointments
• Logs everything to CRM

Latency: 800ms
Cost: $99/mo

Replacing $2,500/mo receptionists.
```

```
Building Ralph: autonomous AI dev agent

What it does:
• Reads PRD
• Writes code
• Runs tests
• Commits to GitHub
• Pings me when done

Currently: 10 iterations/run, 90% success rate

Complex builds while I sleep.

#AI #DevTools
```

### Real Metrics (Week 1)

```
Week 1 results for HVAC company:

📞 47 calls answered (was missing 30%)
📅 12 appointments booked
💰 $8,400 recovered revenue
⏱️ 0 calls missed at night

Voice AI + CRM. $99/mo.

The owner just shows up to jobs now.
```

```
Apollo MCP saved us 80% on lead gen credits.

Old way: Enrich everyone, waste credits on bad leads
New way: Search → Score → Filter → Enrich winners only

$500/mo → $100/mo for same output.

Automation isn't just faster. It's cheaper.
```

### AI Insights (Week 1)

```
Why Voice AI matters more than chatbots:

1. 78% of customers call before buying
2. Most small businesses miss 30-40% of calls
3. Phone converts 10x better than chat

Everyone's building chatbots. I'm building phone systems.

Different game.
```

```
The AI tools that actually work for small business:

✅ Voice AI for phones (never miss a call)
✅ Automated follow-up sequences
✅ Lead qualification bots
✅ CRM auto-logging

❌ Generic chatbots
❌ "AI content writers"
❌ Fancy dashboards nobody uses

Simple > Complex
```

### Hot Takes (Week 1)

```
Unpopular opinion:

Most AI startups will fail because they're building solutions for problems that don't exist.

Small businesses don't need "AI-powered insights."

They need to stop missing phone calls.

Build boring. Solve real problems.
```

```
ChatGPT wrappers are dead.

What's working:
• Vertical-specific tools
• Workflow automation
• Integration layers (MCPs)
• Voice interfaces

General AI → Commoditized
Specific automation → Valuable

Pick a niche. Build deep.
```

---

## Cron Job Setup

**Ensure the posting cron is running:**

```bash
# Check current crons
crontab -l

# Should have something like:
# 0 9,12,15,18 * * 1-5 cd /path/to/social-media-automation && python -m src.x_scheduler process --max 1
# 0 10,16 * * 6,7 cd /path/to/social-media-automation && python -m src.x_scheduler process --max 1
```

**Update cron for new frequency:**

```bash
crontab -e

# Add these lines:
# Weekday posts (Mon-Fri at 9am, 12pm, 3pm, 6pm EST)
0 9,12,15,18 * * 1-5 cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --max 1 >> /tmp/x_cron.log 2>&1

# Weekend posts (Sat-Sun at 10am, 4pm EST)
0 10,16 * * 6,7 cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation && python -m src.x_scheduler process --max 1 >> /tmp/x_cron.log 2>&1
```

---

## Grok Image API Details

**Endpoint:** https://api.x.ai/v1/images/generations

**Cost:** $0.07 per image

**Example API Call:**

```python
import requests
import os

def generate_grok_image(prompt: str) -> str:
    """Generate image using Grok API."""
    
    api_key = os.getenv("XAI_API_KEY")
    
    response = requests.post(
        "https://api.x.ai/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-2-image",
            "prompt": prompt,
            "n": 1,
            "response_format": "url"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return data["data"][0]["url"]
    else:
        raise Exception(f"Grok API error: {response.text}")
```

**Budget:** At $0.07/image and 50% image rate:
- 14 images/week = ~$1/week
- Very cost-effective for engagement boost

---

## Verification Checklist

After implementation, verify:

- [ ] New posts in queue (`python -m src.x_scheduler list`)
- [ ] Queue has 14+ days of content
- [ ] Mix follows content pillars (30/25/25/15/5)
- [ ] ~50% of posts have images attached
- [ ] Cron jobs running (`crontab -l`)
- [ ] First scheduled post time is correct
- [ ] Campaign tag is "ai-builder-public"
- [ ] Links point to marceausolutions.com (not /fitness)
- [ ] Hashtags include #BuildInPublic #AI #Automation

---

## Quick Commands Reference

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/shared/social-media-automation

# View queue
python -m src.x_scheduler list

# View queue stats
python -m src.x_scheduler stats

# Add a post manually
python -m src.x_scheduler add "Post text here" --campaign ai-builder-public

# Process one post now (test)
python -m src.x_scheduler process --max 1 --dry-run

# Process one post for real
python -m src.x_scheduler process --max 1

# Check rate limit status
python -m src.x_api status

# Generate Grok image (standalone test)
python -m execution.grok_image_gen --prompt "Test prompt" --count 1

# Deduplicate queue
python -m src.x_scheduler dedupe

# Clear archived posts
python -m src.x_scheduler clear-archived
```

---

## Summary

1. **Queue is empty** - start fresh with new content
2. **New strategy:** AI Builder in Public (not fitness tips)
3. **Frequency:** 4 posts/day weekdays, 2 posts/day weekends
4. **Images:** 50% of posts with Grok-generated images ($0.07 each)
5. **Content templates:** `templates/ai-builder-content.json`
6. **Sample posts:** Ready to copy above
7. **Campaign tag:** `ai-builder-public`

**The goal:** Attract followers who value AI automation expertise, not generic fitness content. Show real builds, real metrics, real insights.

---

*Generated by Clawdbot on 2026-01-30*
