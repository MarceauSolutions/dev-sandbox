# Knowledge Base

Persistent knowledge, patterns, and learnings that apply across sessions.

**Purpose:** Store reusable knowledge, API details, common patterns, and best practices.

---

## Core Concepts

### DOE Pipeline
**What:** Directive, Orchestration, Execution
- **Directive** (Layer 1): Natural language SOP in markdown (`directives/*.md`)
- **Orchestration** (Layer 2): Claude makes intelligent routing decisions
- **Execution** (Layer 3): Deterministic Python scripts (`execution/*.py`)

**Why it works:**
- LLMs are probabilistic → Good for decisions
- Business logic is deterministic → Needs consistency
- DOE separates these concerns perfectly

**When to use DOE vs Skills:**
- **DOE**: Development, testing, iteration, debugging
- **Skills**: Production, stable workflows, client-facing

### Development Pipeline
1. Build in DOE (dev environment)
2. Test and iterate until stable
3. Deploy to Skills with `deploy_to_skills.py`
4. Assign to project-specific agent
5. Use in production via natural language

---

## APIs & Services

### National Weather Service API
**Base URL:** `https://api.weather.gov`

**Key Facts:**
- Free, no API key required
- Rate limited (don't call more than 1/minute)
- Requires User-Agent header
- Two-step process:
  1. Convert lat/lon to grid point: `/points/{lat},{lon}`
  2. Get forecast from grid point URL

**Example:**
```python
# Step 1: Get grid point
response = requests.get(
    f"https://api.weather.gov/points/{lat},{lon}",
    headers={"User-Agent": "(App Name, email)"}
)
forecast_url = response.json()['properties']['forecast']

# Step 2: Get forecast
forecast = requests.get(forecast_url, headers=headers).json()
periods = forecast['properties']['periods']  # 14 periods = 7 days
```

**Gotchas:**
- Must include User-Agent or request fails
- Forecast updates every 1-6 hours
- Sometimes returns incomplete data (handle gracefully)

### Amazon SP-API
**Location:** `execution/amazon_sp_api.py`

**Key Facts:**
- Requires OAuth refresh token
- Complex authorization flow
- Rate limits vary by endpoint
- LWA (Login with Amazon) for auth

**Setup:**
- Credentials in `.env`
- Refresh token obtained via OAuth flow
- Wrapper handles token refresh automatically

### Grok/xAI Image Generation API
**Location:** `execution/grok_image_gen.py`

**Key Facts:**
- Model: `grok-2-image-1212` (Aurora)
- Cost: $0.07 per image
- Up to 10 images per request
- Default size: 1024x768

**Setup:**
- Add `XAI_API_KEY` to `.env`
- Get key from: https://console.x.ai/

**Example:**
```python
generator = GrokImageGenerator()
image_urls = generator.generate_image(
    prompt="Fitness influencer workout",
    count=4
)
```

### Shotstack Video Generation API
**Location:** `execution/shotstack_api.py`

**Key Facts:**
- Cost: ~$0.04-$0.10 per video
- Creates videos from images with transitions
- Text overlays, background music included
- Multiple formats: mp4, gif, webm

**Setup:**
- Add `SHOTSTACK_API_KEY` to `.env`
- Set `SHOTSTACK_ENV=stage` for testing, `v1` for production
- Get key from: https://dashboard.shotstack.io/

**Example:**
```python
api = ShotstackAPI()
result = api.create_video_from_images(
    image_urls=["url1", "url2", "url3"],
    text_overlays=["HEADLINE", "", "CTA"],
    duration_per_image=3.5,
    transition="slideLeft",
    music="energetic"
)
# Returns render_id, wait for completion
final = api.wait_for_render(result["render_id"])
video_url = final["video_url"]
```

**Video Ad Pipeline (Grok + Shotstack):**
1. Generate images with Grok (~$0.28 for 4 images)
2. Create video with Shotstack (~$0.06)
3. Total: ~$0.35 per 15-second ad

---

## File Organization

### Project Structure
```
dev-sandbox/
├── .claude/                  # Claude configuration
│   ├── agents/              # Agent configs (per-project)
│   ├── projects/            # Project manifests (skill assignments)
│   ├── skills/              # Production skills (SKILL.md files)
│   ├── SESSION_LOG.md       # Session-by-session progress
│   ├── KNOWLEDGE_BASE.md    # This file
│   └── [other docs]
├── directives/              # Development directives (DOE)
├── execution/               # Execution scripts (deterministic)
├── .tmp/                    # Intermediate files (never commit)
├── .env                     # Environment variables
└── CLAUDE.md               # Core architecture docs
```

### Where Files Go
| Type | Location | Committed? |
|------|----------|------------|
| Directives (SOPs) | `directives/*.md` | Yes |
| Execution scripts | `execution/*.py` | Yes |
| Skills | `.claude/skills/*/SKILL.md` | Yes |
| Projects | `.claude/projects/*.json` | Yes |
| Agents | `.claude/agents/*.json` | Yes |
| Intermediate data | `.tmp/*` | No |
| API credentials | `.env` | No |
| Session logs | `.claude/SESSION_LOG.md` | Yes |

---

## Common Patterns

### Python Script Template
```python
#!/usr/bin/env python3
"""
Brief description of what this script does.
"""

import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Description')
    parser.add_argument('--input', required=True)
    args = parser.parse_args()

    # Do work
    result = process(args.input)

    # Save to .tmp
    output_file = Path(__file__).parent.parent / '.tmp' / 'output.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"✓ Done: {output_file}")
    return 0

if __name__ == "__main__":
    exit(main())
```

### Directive Template
```markdown
# [Workflow Name]

## Goal
[What this workflow accomplishes]

## Inputs
- Input 1: Description
- Input 2: Description

## Tools/Scripts
- `execution/script_name.py` - What it does

## Process
1. Step 1
2. Step 2
3. Step 3

## Outputs
- Output file location
- What user gets

## Edge Cases & Learnings
[As discovered during development]
```

### SKILL.md Template
```markdown
---
name: skill-name
description: Clear description for automatic triggering
allowed-tools: ["Bash(python:*)", "Read"]
---

# Skill Name

## Overview
[What this skill does]

## When to use
[Triggering conditions]

## Instructions
[Reference directive, list scripts]

## Notes
[Deployment info, restrictions]
```

---

## Best Practices

### Development (DOE)
- ✓ Always read files before editing
- ✓ Test with real data, not mock data
- ✓ Save intermediate files to `.tmp/`
- ✓ Update directive as you discover edge cases
- ✓ Keep execution scripts deterministic
- ✓ Don't deploy until stable

### Deployment (Skills)
- ✓ Only deploy tested workflows
- ✓ Reference directives (don't duplicate)
- ✓ Assign to appropriate project
- ✓ Test skill triggering after deployment
- ✓ Review agent access boundaries

### Git Commits
- ✓ Only commit when user explicitly requests
- ✓ Include .tmp in .gitignore
- ✓ Include .env in .gitignore
- ✓ Use descriptive commit messages
- ✓ End commits with Claude attribution

### Error Handling
- ✓ Try/except on all API calls
- ✓ Provide helpful error messages
- ✓ Log errors for debugging
- ✓ Update directive with discovered issues
- ✓ Self-anneal: fix, test, document

---

## Project-Specific Knowledge

### Amazon Assistant Project
**Goal:** Automate Amazon Seller operations

**Domains:**
- amazon-sp-api
- e-commerce
- inventory-management
- pricing-optimization

**Skills (current):**
- amazon-seller-operations

**Skills (planned):**
- amazon-process-orders
- amazon-inventory-optimizer
- amazon-pricing-optimizer
- amazon-review-monitor
- amazon-product-research

**API Access:**
- SP-API credentials in `.env`
- Refresh token obtained
- OAuth wrapper in `execution/amazon_sp_api.py`

### Weather Reports Project
**Goal:** Generate automated weather reports

**Domains:**
- meteorology
- weather-forecasting
- data-visualization

**Skills (current):**
- generate-naples-weather-report

**Skills (planned):**
- Multi-location weather reports
- Email delivery automation
- Weather alerts system

**API Access:**
- National Weather Service (free, no key)
- Naples, FL coordinates: 26.1420° N, 81.7948° W

### Fitness Influencer Project
**Goal:** Automate fitness influencer content creation and operations

**Status:** 🚀 **PRODUCTION LIVE** (as of 2026-01-07)

**Domains:**
- fitness-content
- video-editing
- social-media
- email-management
- revenue-analytics

**Skills (current):**
- fitness-influencer-operations

**Repositories:**
| Repo | Purpose | Status | URL |
|------|---------|--------|-----|
| dev-sandbox | Development/DOE | Active | github.com/MarceauSolutions/dev-sandbox |
| fitness-influencer-backend | FastAPI backend | Deployed to Railway | https://web-production-44ade.up.railway.app |
| fitness-influencer-frontend | Web UI | Placeholder | github.com/MarceauSolutions/fitness-influencer-frontend |
| marceausolutions.com | Website | Live | https://marceausolutions.com/assistant.html |

**All Capabilities (14 Scripts - ALL WORKING):**

| Category | Capability | Script | Cost | Status |
|----------|------------|--------|------|--------|
| Video | AI Video Ad Generation | `video_ads.py` | $0.28-0.33/video | ✅ Live |
| Video | Jump Cut Editing | `video_jumpcut.py` | FREE | ✅ Live |
| Video | Intelligent Router | `intelligent_video_router.py` | - | ✅ Live |
| Video | MoviePy Generator | `moviepy_video_generator.py` | FREE | ✅ Live |
| Video | Creatomate API | `creatomate_api.py` | $0.05/video | ✅ Live |
| Video | Creatomate Enhanced | `creatomate_api_enhanced.py` | $0.05/video | ✅ Live |
| Video | Shotstack API | `shotstack_api.py` | $0.06/video | ✅ Live |
| Graphics | Educational Graphics | `educational_graphics.py` | FREE | ✅ Live |
| Graphics | AI Image Generation | `grok_image_gen.py` | $0.07/image | ✅ Live |
| Business | Gmail Monitoring | `gmail_monitor.py` | FREE | ✅ Live |
| Business | Calendar Integration | `calendar_reminders.py` | FREE | ✅ Live |
| Business | Revenue Analytics | `revenue_analytics.py` | FREE | ✅ Live |
| Content | Workout Plan Generator | `workout_plan_generator.py` | FREE | ✅ Live |
| Content | Nutrition Guide Generator | `nutrition_guide_generator.py` | FREE | ✅ Live |

**API Access:**
- `XAI_API_KEY` - Grok image generation ($0.07/image)
- `SHOTSTACK_API_KEY` - Video generation backup ($0.06/video)
- `CREATOMATE_API_KEY` - Primary video generation ($0.05/video)
- `CREATOMATE_TEMPLATE_ID` - 508c3e40-b72d-483f-977f-c443c28f8dfc
- Google APIs - OAuth configured
  - Client ID: 915754256960-ujpassm3aaf9s8hkn3dbusm5euq5qhb2.apps.googleusercontent.com
  - Scopes: Gmail (readonly), Calendar (full), Sheets (full)
- Twilio - SMS (A2P 10DLC compliant)
- SendGrid - Email sequences

**Video Generation System (Cost-Optimized):**
```
Intelligent Router (intelligent_video_router.py)
├─ Try MoviePy first (FREE) ← Target 70% of requests
└─ Fallback to Creatomate ($0.05)
   └─ Fallback to Shotstack ($0.06)
```

**Creatomate Quality Presets:**
| Preset | Resolution | FPS | Bitrate |
|--------|------------|-----|---------|
| Low | 640x360 | 24 | 500k |
| Medium | 1280x720 | 30 | 2000k |
| High (default) | 1920x1080 | 30 | 5000k |
| Ultra | 1920x1080 | 60 | 8000k |
| 4K | 3840x2160 | 30 | 15000k |

**Example Commands:**
```bash
# Run the menu interface (non-technical users)
python fitness_assistant.py

# Setup Google APIs (one-time)
python execution/google_auth_setup.py

# Create video ad
python execution/video_ads.py --concept "fitness" --headline "Transform" --cta "Start Now"

# Create educational graphic
python execution/educational_graphics.py --title "Fitness Tips" --points "Protein,Weights,Active"

# Check emails (last 24 hours)
python execution/gmail_monitor.py --hours 24

# View calendar
python execution/calendar_reminders.py list --days 7

# High-quality video via Creatomate
python execution/creatomate_api_enhanced.py create-video \
  --template 508c3e40-b72d-483f-977f-c443c28f8dfc \
  --modifications '{"headline":"Transform Your Body","cta":"Start Today"}' \
  --quality high
```

**Live API Endpoints (Railway):**
| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/api/ai/chat` | AI-powered chat with dual arbitration | ✅ |
| `/api/video/edit` | Video editing with jump cuts | ✅ |
| `/api/video/generate` | Video generation via Shotstack | ✅ |
| `/api/graphics/create` | Educational graphics | ✅ |
| `/api/images/generate` | AI image generation via Grok | ✅ |
| `/api/email/digest` | Email summarization | ✅ |
| `/api/analytics/revenue` | Revenue analytics | ✅ |
| `/api/leads/submit` | Lead capture form | ✅ |
| `/api/sms/optin` | SMS welcome (Twilio) | ✅ |
| `/api/email/optin` | Email welcome sequence | ✅ |

**Cost Structure:**
```
Per Video Ad:
  AI Images (4 × Grok):     $0.28
  Video Assembly:           $0.00 (MoviePy) or $0.05 (Creatomate)
  Total:                    $0.28-$0.33

Monthly (200 videos):       $56-66
Annual:                     $672-792
Savings vs paid tools:      ~$2,300+/year
```

**Testing Completed (All Passed):**
- ✅ Gmail API - 18 emails fetched
- ✅ Calendar API - 5 events retrieved
- ✅ Google Auth Setup - All APIs authenticated
- ✅ Creatomate High Quality - 1920x1080 30fps
- ✅ Creatomate Ultra Quality - 1920x1080 60fps
- ✅ Creatomate RenderScript - Custom composition
- ✅ End-to-End Flow - marceausolutions.com → Railway

**Known Gotchas & Solutions:**
| Issue | Solution |
|-------|----------|
| MoviePy v2.x API changes | Use `from moviepy import` not `from moviepy.editor import` |
| Google API scope errors | Delete `token.json` and re-authenticate |
| Creatomate template failures | Ensure CREATOMATE_TEMPLATE_ID is set in .env |
| Silence detection too aggressive | Adjust threshold (default -40dB, can increase to -35dB) |

**Documentation:**
- `FITNESS_INFLUENCER_QUICK_START.md` - User guide
- `WEBSITE_INTEGRATION.md` - Deployment guide
- `GOOGLE_API_RECOMMENDATIONS.md` - API roadmap
- `directives/fitness_influencer_operations.md` - Complete SOP (500+ lines)
- `docs/sessions/2026-01-07-fitness-influencer-beta-release.md` - Beta release session
- `docs/sessions/2026-01-07-twilio-compliance-and-fitness-sync.md` - Compliance session

**Next Steps:**
1. ~~Deploy backend to Railway~~ ✅ DONE
2. ~~Connect frontend → backend~~ ✅ DONE
3. ~~Test full user flow~~ ✅ DONE
4. ~~Update Twilio compliance~~ ✅ DONE
5. Submit Twilio A2P 10DLC registration
6. Recruit beta testers
7. Monitor Railway logs for production issues
8. Consider automated sync script for execution files

---

## Commands Reference

### Deployment
```bash
# Deploy directive to skills
python execution/deploy_to_skills.py DIRECTIVE --project PROJECT

# Create new project
python execution/manage_agent_skills.py create-project --name NAME

# Add skill to project
python execution/manage_agent_skills.py add --project PROJECT --skill SKILL

# List projects
python execution/manage_agent_skills.py list

# View project details
python execution/manage_agent_skills.py list --project PROJECT
```

### Development
```bash
# Test execution script
python execution/SCRIPT.py --args

# Generate weather report
python execution/fetch_naples_weather.py
python execution/generate_weather_report.py

# Check skill deployment
python execution/manage_agent_skills.py list-skills
```

---

## Troubleshooting

### Skill Not Triggering
**Check:**
1. Is skill deployed? `manage_agent_skills.py list-skills`
2. Is skill in project manifest?
3. Is description clear and specific?
4. Try being more explicit in request

**Fix:**
- Update SKILL.md description
- Make it more specific to use case
- Add example trigger phrases

### Execution Script Failing
**Debug:**
1. Run script directly: `python execution/script.py`
2. Check for missing dependencies
3. Verify file paths are absolute
4. Check API credentials in `.env`
5. Look for rate limits

**Fix:**
- Install dependencies: `pip install package`
- Fix path resolution
- Update .env with correct credentials
- Add rate limiting/delays

### Import Errors
**Common causes:**
- Missing pip packages
- Wrong Python version
- Virtual environment not activated

**Fix:**
```bash
pip install package-name
# or
pip install -r requirements.txt
```

---

## User Preferences & Context

### Model Preference
- Prefers Opus 4.5 when available
- Use for complex, multi-step tasks
- Sonnet for simpler operations

### Working Style
- Values comprehensive documentation
- Prefers seeing the complete picture
- Likes granular control over deployments
- Wants to understand the "why" not just "how"

### Projects
- Working on Amazon Seller automation
- Interested in healthcare applications (Omnipod example)
- Building personal productivity tools
- Each project needs isolated skill sets

### Git Workflow
- Don't commit unless explicitly requested
- When committing, include Claude attribution
- Keep .tmp and .env out of git

---

## Quick Reference

**DOE = Directive, Orchestration, Execution**

**Development flow:**
1. Write directive in `directives/`
2. Build script in `execution/`
3. Test with Claude
4. Iterate until stable
5. Deploy with `deploy_to_skills.py`

**Key files to check each session:**
- `.claude/SESSION_LOG.md` - What we did last
- `.claude/KNOWLEDGE_BASE.md` - This file
- `directives/` - What workflows exist
- `.claude/projects/` - Active projects

**Update these files:**
- SESSION_LOG.md - After ~30 min of work, and at end of session
- KNOWLEDGE_BASE.md - When learning new APIs, patterns, or best practices
