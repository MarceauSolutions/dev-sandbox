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

**Domains:**
- fitness-content
- video-editing
- social-media
- email-management

**Skills (current):**
- fitness-influencer-operations

**Repositories:**
| Repo | Purpose | Status |
|------|---------|--------|
| dev-sandbox | Development/DOE | Active |
| fitness-influencer-backend | FastAPI backend | Scripts synced, not deployed |
| fitness-influencer-frontend | Web UI | Empty - needs implementation |
| marceausolutions.com | Website | Has fitness.html, assistant.html |

**Capabilities (WORKING):**
- ✅ AI image generation (Grok) - $0.07/image
- ✅ Video ad creation (Creatomate) - $0.05/video
- ✅ Video ad creation (Shotstack) - $0.06/video (backup)
- ✅ Video jump cuts (FFmpeg/MoviePy) - FREE
- ✅ Educational graphics (Pillow) - FREE
- ✅ Workout plan generator - FREE
- ✅ Nutrition guide generator - FREE
- ✅ Gmail monitoring (Gmail API) - tested working
- ✅ Calendar integration (Google Calendar) - tested working
- ✅ Google Auth setup - unified script

**Capabilities (Pending Integration):**
- ⏳ Revenue analytics (Google Sheets) - script exists
- ⏳ Canva integration - script exists, API pending
- ⏳ End-to-end video workflow (video_ads.py → enhanced API)

**API Access:**
- `XAI_API_KEY` - Grok image generation
- `SHOTSTACK_API_KEY` - Video generation (backup)
- `CREATOMATE_API_KEY` - Primary video generation
- `CREATOMATE_TEMPLATE_ID` - 508c3e40-b72d-483f-977f-c443c28f8dfc
- Google APIs - Configured with OAuth
  - Client ID: 915754256960-ujpassm3aaf9s8hkn3dbusm5euq5qhb2.apps.googleusercontent.com

**Video Generation System:**
```
Intelligent Router (intelligent_video_router.py)
├─ Try MoviePy first (FREE)
└─ Fallback to Creatomate ($0.05)
   └─ Fallback to Shotstack ($0.06)
```

**Creatomate Quality Presets:**
- Low: 640x360, 24fps, 500k bitrate
- Medium: 1280x720, 30fps, 2000k bitrate
- High: 1920x1080, 30fps, 5000k bitrate (default)
- Ultra: 1920x1080, 60fps, 8000k bitrate
- 4K: 3840x2160, 30fps, 15000k bitrate

**Example Video Ad Pipeline:**
```bash
# Option 1: Direct Creatomate (quality control)
python execution/creatomate_api_enhanced.py create-video \
  --template 508c3e40-b72d-483f-977f-c443c28f8dfc \
  --modifications '{"headline":"Transform Your Body","cta":"Start Today"}' \
  --quality high

# Option 2: Full pipeline (Grok + Creatomate)
python execution/grok_image_gen.py --prompt "Fitness workout" --count 4
python execution/creatomate_api_enhanced.py create-video --images "url1,url2,url3,url4"
```

**Production Status (2026-01-07):**
- ✅ All execution scripts tested
- ✅ Backend repo synced with latest scripts
- ❌ Backend not deployed to hosting
- ❌ Frontend UI not built
- ❌ End-to-end user flow untested

**Next Steps (Priority Order):**
1. Deploy backend to Railway
2. Build frontend UI (React or simple HTML)
3. Connect frontend → backend → execution scripts
4. Test full user flow
5. Recruit beta testers

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
