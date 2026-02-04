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

## Lead Scraper & SMS Campaign System

*Added: 2026-01-15*

### Overview

The lead-scraper project enables cold outreach campaigns via SMS and email, with automated follow-up sequences and CRM integration.

**Core Components:**
| Component | File | Purpose |
|-----------|------|---------|
| Lead Scraper | `src/scraper.py` | Google Places + Apollo enrichment |
| SMS Sender | `src/sms_outreach.py` | Twilio SMS integration |
| Campaign Runner | `src/campaign_runner.py` | Autonomous batch sending |
| Follow-Up Sequence | `src/follow_up_sequence.py` | 7-touch, 60-day automation |
| Twilio Webhook | `src/twilio_webhook.py` | SMS reply handling |
| Form Webhook | `src/form_webhook.py` | Landing page form processing |

### Key Configuration

**Environment Variables (.env):**
```bash
# Twilio SMS
TWILIO_ACCOUNT_SID=ACXXX
TWILIO_AUTH_TOKEN=XXX
TWILIO_PHONE_NUMBER=+18552399364

# Apollo Lead Enrichment
APOLLO_API_KEY=XXX

# ClickUp CRM
CLICKUP_API_TOKEN=XXX
CLICKUP_LIST_ID=901709132478

# Google Sheets (optional)
GOOGLE_SHEETS_SPREADSHEET_ID=XXX

# Notifications
NOTIFICATION_EMAIL=wmarceau@marceausolutions.com
```

### Hormozi Framework Implementation

| Principle | Implementation |
|-----------|---------------|
| Rule of 100 | Campaign runner with daily limits |
| Cocktail Party | Business name personalization in templates |
| Big Fast Value | Lead magnet offers (free mockup, audit) |
| Multi-touch | 7-touch sequence over 60 days |
| Still Looking | 9-word reactivation template |

### SMS Templates (Current)

| Template | Day | Message | Chars |
|----------|-----|---------|-------|
| `no_website_intro` | 0 | "Hi, this is William. I noticed $business_name doesn't have a website..." | 158 |
| `still_looking` | 2 | "Still looking to get more members at $business_name?" | 89 |
| `social_proof` | 5 | "Just helped a Naples gym add 40 members..." | 131 |
| `direct_question` | 10 | "Quick question for $business_name - do you have someone handling..." | 152 |
| `competitor_hook` | 15 | "Hi, calling about a gym near $business_name that just got 23 new members..." | 156 |
| `breakup` | 30 | "Hey, closing out my list of Naples gyms..." | 119 |
| `re_engage` | 60 | "Hey $business_name, wanted to check back in..." | 124 |

**CRITICAL**: All templates require William's approval before use.

### Lead Database Stats

```
Total Leads: 361
With Phone Numbers: 313 (86.7%)
With "no_website" Pain Point: 201 (55.7%)
Location: Naples, FL area
Categories: Gym, Fitness Center, Personal Trainer, Yoga Studio
```

### SOPs (Workflows)

| SOP | Location | Purpose |
|-----|----------|---------|
| Cold Outreach | `workflows/cold-outreach-sop.md` | Main campaign execution |
| Form Webhook | `workflows/form-webhook-sop.md` | Form processing pipeline |
| SMS Campaign | `workflows/sms-campaign-sop.md` | SMS-specific procedures |
| Multi-Touch | `workflows/multi-touch-followup-sop.md` | Follow-up sequence management |
| Webhook Monitoring | `workflows/webhook-monitoring-sop.md` | Reply handling and monitoring |

### Common Commands

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Check lead stats
python -m src.scraper stats

# Dry run SMS
python -m src.scraper sms --dry-run --limit 5 --pain-point no_website

# Send SMS (requires template approval)
python -m src.scraper sms --for-real --limit 100 --pain-point no_website

# Start Twilio webhook server
python -m src.twilio_webhook serve --port 5001

# Process form submission
python -m src.form_webhook process --data '{"name":"...", "email":"..."}' --source "test"

# View ClickUp lists
python -m src.form_webhook clickup-lists
```

### Integration Points

| System | Integration | Status |
|--------|-------------|--------|
| Twilio | SMS send/receive | ✅ Ready |
| Apollo | Lead enrichment | ✅ Ready |
| ClickUp | CRM task creation | ✅ Ready |
| Google Sheets | Lead logging | ✅ Ready |
| SMTP Email | Notification emails | ✅ Ready |
| ngrok | Webhook exposure | ✅ Available |

### Deployment Pattern

Use GitHub Pages + ngrok to marceausolutions.com (NOT Netlify):
1. Push landing page to GitHub repo
2. Enable GitHub Pages
3. Use ngrok to tunnel webhook servers
4. Configure Twilio webhook URL with ngrok URL

### Cost Estimates

| Item | Cost | Notes |
|------|------|-------|
| SMS Outbound | $0.0079/msg | ~$0.79 per 100 |
| SMS Inbound | $0.0079/msg | Reply handling |
| Phone Number | $1.15/month | Twilio |
| Apollo | Per credit | Check balance |
| SMTP Email | Free | Via Gmail app password |

### Known Gotchas

| Issue | Solution |
|-------|----------|
| GOOGLE_SHEETS_SPREADSHEET_ID empty | Create spreadsheet, add ID to .env |
| Twilio carrier filtering | Review message for spam triggers |
| Low enrichment rate | Apollo needs websites to find contacts |
| Webhook not receiving | Check ngrok tunnel, update Twilio URL |

---

## EC2 Infrastructure & Agent Architecture

*Added: 2026-02-02*

### EC2 Instance Overview

**Instance:** `i-01752306f94897d7d`
**IP:** `34.193.98.97`
**Elastic IP:** Assigned (persistent)
**Cost:** ~$7/month (t3.micro or similar)

**Services Running:**
| Service | Port | Purpose |
|---------|------|---------|
| Clawdbot | 3100 | 24/7 Telegram AI assistant |
| n8n | 5678 | Workflow automation |

**DNS Records:**
| Subdomain | IP | Purpose |
|-----------|-----|---------|
| n8n.marceausolutions.com | 34.193.98.97 | n8n web UI |

### SSH Access

**Config Location:** `~/.ssh/config`
```
Host ec2
    HostName 34.193.98.97
    User ec2-user
    IdentityFile ~/.ssh/marceau-ec2-key.pem
    StrictHostKeyChecking no
```

**Quick Commands:**
```bash
# SSH into EC2
ssh ec2

# Check services
ssh ec2 "sudo systemctl status clawdbot"
ssh ec2 "sudo systemctl status n8n"

# View Clawdbot logs
ssh ec2 "sudo tail -50 /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log"

# Restart services
ssh ec2 "sudo systemctl restart clawdbot"
ssh ec2 "sudo systemctl restart n8n"
```

### Clawdbot Configuration

**Config File:** `/home/clawdbot/.clawdbot/clawdbot.json`
**Env File:** `/home/clawdbot/.clawdbot/.env`

**Telegram Bot Setup:**
1. Create bot via @BotFather on Telegram
2. Get bot token (format: `123456789:ABCDEF...`)
3. Update config:
   ```bash
   ssh ec2 "sudo sed -i 's|OLD_TOKEN|NEW_TOKEN|g' /home/clawdbot/.clawdbot/clawdbot.json"
   ssh ec2 "sudo systemctl restart clawdbot"
   ```
4. Message the bot to activate: `/start`

**Checking Telegram Connection:**
```bash
# Look for 401 errors (bad token) or successful starts
ssh ec2 "sudo tail -30 /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log | grep -i telegram"
```

**Common Issues:**
| Issue | Symptom | Fix |
|-------|---------|-----|
| Bad token | `401 Unauthorized` in logs | Update botToken in clawdbot.json |
| Bot not responding | No logs for telegram | Check bot is enabled in config |
| Service crashed | systemctl shows failed | Check logs, restart service |

### n8n Configuration

**Web UI:** http://n8n.marceausolutions.com:5678
**Config:** `/etc/n8n.env`

**Key Settings:**
```bash
N8N_SECURE_COOKIE=false  # Required for HTTP (non-HTTPS) access
```

**Firewall Setup:**
```bash
# Open port 5678
ssh ec2 "sudo firewall-cmd --permanent --add-port=5678/tcp && sudo firewall-cmd --reload"
```

**Importing Workflows:**
```bash
# SCP workflow files to EC2
scp workflow.json ec2:/tmp/

# Import via n8n CLI
ssh ec2 "n8n import:workflow --input=/tmp/workflow.json"
```

**Google OAuth for n8n:**
1. Add redirect URI in Google Cloud Console:
   `http://n8n.marceausolutions.com:5678/rest/oauth2-credential/callback`
2. Use "Web application" OAuth client (not Desktop)
3. In n8n: Credentials → Add → Google Sheets OAuth2 API

### Three-Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUESTS                           │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
              ┌───────▼───────┐   ┌───────▼───────┐
              │   TELEGRAM    │   │   VS CODE     │
              │   (Mobile)    │   │   (Desktop)   │
              └───────┬───────┘   └───────┬───────┘
                      │                   │
                      ▼                   ▼
              ┌───────────────┐   ┌───────────────┐
              │  CLAWDBOT     │   │  CLAUDE CODE  │
              │  (EC2 24/7)   │   │  (Local Mac)  │
              │  Score 0-6    │   │  Interactive  │
              └───────┬───────┘   └───────┬───────┘
                      │                   │
                      └─────────┬─────────┘
                                │
                        ┌───────▼───────┐
                        │    RALPH      │
                        │  (Complex)    │
                        │  Score 7-10   │
                        └───────────────┘
```

**Routing Rules:**
| Complexity | Score | Handler | Examples |
|------------|-------|---------|----------|
| Trivial | 0-3 | Clawdbot | Quick questions, status checks |
| Simple | 4-6 | Clawdbot | Single file edits, simple scripts |
| Complex | 7-10 | Ralph | Multi-file features, refactoring |
| Mac-specific | Any | Claude Code | PyPI, MCP Registry, Xcode |

**Communication Between Agents:**
| From | To | Method |
|------|-----|--------|
| Clawdbot → Local | Git push + Telegram notification |
| Local → Clawdbot | Git (Clawdbot pulls) |
| Clawdbot → Ralph | Creates PRD in repo, notifies user |
| Ralph → Clawdbot | Webhook notification when done |

### Google Sheets IDs (n8n Workflows)

| Purpose | Spreadsheet ID |
|---------|---------------|
| Ideas_Queue | `1KfTupeA0VQASuYHccG4SmC9vFtJMtY0prJXe5xt36rE` |
| SMS_Responses | `1egMBLln5cIGgwn1zeG9begxpv5VxvyY1IoIIiI1ix64` |
| Form_Submissions | `1iXAvYMJBqAH-VBWBiy4mXpGXP6wxLWy23U2HaHUtmk4` |
| Opt_Outs | `1j2or4TWWAYh_KUX3fXDbrSby16cs9j3h2P3xU-f93Z0` |

### Credential Consolidation (Google Cloud)

**Unified Project:** `fitness-influencer-assistant`

**OAuth Client to Use:** "Fitness AI Assistant Web" (Web application type)
- Supports redirect URIs (required for n8n)
- Client ID: `915754256960-608f...`

**Deactivated Projects** (security cleanup 2026-02-02):
- n8nAIAgent
- N8nContactForm
- YouTubecreator MCP
- CalendarLink
- My First Project

**Best Practice:** Use ONE Google Cloud project with all APIs enabled:
- Google Sheets API
- Google Calendar API
- Gmail API
- Google Drive API
- YouTube Data API v3
- Google Places API

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
