# Project Index - Quick Navigation

Use this guide to quickly switch between projects and find the right files.

**Full deployment documentation:** See [DEPLOYMENT_PIPELINE.md](DEPLOYMENT_PIPELINE.md)

## Quick Commands

```bash
# Switch to a project
cd interview-prep-pptx               # Interview Prep PowerPoint
cd projects/fitness-influencer       # Fitness Influencer AI
cd projects/amazon-seller            # Amazon Seller Operations
cd projects/naples-weather           # Naples Weather Report

# Sync scripts to execution/ (required for skills)
python deploy_to_skills.py --sync-execution --project interview-prep
python deploy_to_skills.py --sync-all       # Sync ALL projects

# Deploy to production
python deploy_to_skills.py --project interview-prep
python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant

# List all projects
python deploy_to_skills.py --list
```

---

## Project Overview

| Project | Status | Directory | Skill | Live URL |
|---------|--------|-----------|-------|----------|
| **Interview Prep** | Live | `interview-prep-pptx/` | `interview-prep` | [Railway](https://interview-prep-pptx-production.up.railway.app/app) |
| **Fitness Influencer** | Live | `projects/fitness-influencer/` | `fitness-influencer-operations` | [Railway](https://api-production-1edc.up.railway.app) |
| **Website Builder** | Dev | `projects/website-builder/` | - | - |
| **Amazon Seller** | Dev | `projects/amazon-seller/` | `amazon-seller-operations` | - |
| **Naples Weather** | Dev | `projects/naples-weather/` | `naples-weather-report` | - |

### Current Marketing Site Status

**Rollback Applied (2026-01-09):** All marketing pages show "Coming Soon" with inquiry forms. Following DOE architecture - deploy only when execution layer is solid.

---

## Interview Prep PowerPoint

**Trigger phrases:** "interview prep", "research company", "create presentation", "PowerPoint"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `interview-prep-pptx/src/` |
| Frontend | `interview-prep-pptx/frontend/index.html` |
| SKILL.md | `interview-prep-pptx/SKILL.md` |
| Directive | `directives/interview_prep.md` |
| Railway config | `interview-prep-pptx/railway.json` |

### Scripts
- `interview_research.py` - Company/role research via Claude
- `pptx_generator.py` - PowerPoint generation
- `pptx_editor.py` - Slide editing (text, images, new slides)
- `session_manager.py` - Session tracking for edits
- `interview_prep_api.py` - FastAPI REST API
- `grok_image_gen.py` - AI image generation (shared)

### Deploy
```bash
# Sync to execution/ first
python deploy_to_skills.py --sync-execution --project interview-prep

# Deploy to Railway
cd interview-prep-pptx && railway up
```

**Live URL:** https://interview-prep-pptx-production.up.railway.app/app

---

## Fitness Influencer AI

**Version:** 1.0.0
**Live URL:** https://api-production-1edc.up.railway.app
**Trigger phrases:** "video editing", "create graphic", "email summary", "revenue analytics"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/fitness-influencer/src/` |
| Chat frontend | `projects/fitness-influencer/frontend/chat.html` |
| Dashboard | `projects/fitness-influencer/frontend/dashboard.html` |
| Dual-AI Router | `projects/fitness-influencer/src/dual_ai_router.py` |
| Chat API | `projects/fitness-influencer/src/chat_api.py` |
| SKILL.md | `.claude/skills/fitness-influencer-operations/SKILL.md` |
| Directive | `directives/fitness_influencer_operations.md` |

### Architecture
- **Dual-AI System**: Claude (intent/routing) + Grok (images/cost optimization)
- **Cost Guardrails**: Operations >$0.10 require user confirmation
- **Cost Tiers**: FREE, LOW (<$0.10), MEDIUM ($0.10-$0.30), HIGH (>$0.30)

### Scripts
- `dual_ai_router.py` - Dual-AI decision routing with cost tiers
- `chat_api.py` - FastAPI backend with Claude tool use
- `video_jumpcut.py` - Jump-cut video editing (FREE)
- `educational_graphics.py` - Create fitness graphics (FREE)
- `grok_image_gen.py` - AI image generation ($0.07/image)
- `video_ads.py` - Shotstack video ads ($0.34)
- `gmail_monitor.py` - Email summarization (FREE)
- `revenue_analytics.py` - Revenue tracking (FREE)
- `workout_plan_generator.py` - Workout plans (FREE)
- `nutrition_guide_generator.py` - Nutrition guides (FREE)

### API Endpoints
- `GET /` - Chat interface
- `GET /dashboard` - Tool dashboard
- `GET /health` - Service health + AI status
- `POST /api/chat` - Chat with dual-AI routing
- `GET /api/costs` - Session cost summary
- `POST /api/upload` - File upload for video editing

### Deploy
```bash
cd projects/fitness-influencer && railway up
```

---

## Amazon Seller Operations

**Trigger phrases:** "Amazon seller", "inventory", "FBA fees", "SP-API"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/amazon-seller/src/` |
| SKILL.md | `.claude/skills/amazon-seller-operations/SKILL.md` |
| Directive | `directives/amazon_seller_operations.md` |

### Scripts
- `amazon_sp_api.py` - Core SP-API client
- `amazon_fee_calculator.py` - FBA fee calculations
- `amazon_inventory_optimizer.py` - Restock recommendations
- `amazon_oauth_server.py` - OAuth authentication
- `gmail_monitor.py` - Supplier emails (shared)
- `revenue_analytics.py` - Revenue tracking (shared)
- `twilio_sms.py` - SMS notifications (shared)

### Deploy
```bash
python deploy_to_skills.py --sync-execution --project amazon-seller
cd projects/amazon-seller && railway init && railway up
```

---

## Website Builder AI

**Version:** 0.2.0
**Trigger phrases:** "build website", "generate site", "website builder"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/website-builder/src/` |
| Output | `projects/website-builder/output/` |
| Requirements | `projects/website-builder/requirements.txt` |

### Scripts
- `research_engine.py` - Company/owner research + social integration
- `social_profile_analyzer.py` - Social media profile analysis
- `web_search.py` - Brave/Tavily web search integration
- `personality_synthesizer.py` - Brand personality synthesis
- `content_generator.py` - AI-powered copywriting
- `site_builder.py` - HTML/CSS generation with personality styling
- `website_builder_api.py` - FastAPI backend

### API Endpoints

**Basic Workflow:**
- `POST /api/research` - Research company (basic)
- `POST /api/generate` - Generate content
- `POST /api/build` - Build static site
- `POST /api/workflow` - Full basic workflow

**Social Research Workflow:**
- `POST /api/research/social` - Research with social profiles
- `POST /api/generate/personality` - Personality-driven content
- `POST /api/build/personality` - Personality-styled site
- `POST /api/workflow/social` - Full social workflow

### Run Locally
```bash
cd projects/website-builder/src
uvicorn website_builder_api:app --reload --port 8001
# API docs at http://localhost:8001/docs
```

---

## Naples Weather Report

**Trigger phrases:** "Naples weather", "weekly forecast", "weather report"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/naples-weather/src/` |
| SKILL.md | `.claude/skills/naples-weather-report/SKILL.md` |
| Directive | `directives/generate_naples_weather_report.md` |

### Scripts
- `fetch_naples_weather.py` - Weather API client
- `generate_weather_report.py` - Report generation
- `markdown_to_pdf.py` - PDF export

### Deploy
```bash
python deploy_to_skills.py --sync-execution --project naples-weather
```

---

## Shared Resources

### Shared Scripts (in `execution/`)

| Script | Used By | Purpose |
|--------|---------|---------|
| `grok_image_gen.py` | Interview, Fitness | AI image generation via Grok |
| `gmail_monitor.py` | Fitness, Amazon | Email summarization |
| `revenue_analytics.py` | Fitness, Amazon | Business metrics |
| `twilio_sms.py` | Fitness, Amazon | SMS notifications |
| `google_auth_setup.py` | All Google | OAuth setup |

### Environment Variables (root `.env`)

```env
# AI Services (All projects)
ANTHROPIC_API_KEY=xxx           # Claude API
XAI_API_KEY=xxx                 # Grok image generation

# Google APIs (Fitness, Amazon)
GOOGLE_CREDENTIALS_PATH=credentials.json

# Amazon SP-API (Amazon only)
AMAZON_REFRESH_TOKEN=xxx
AMAZON_LWA_APP_ID=xxx
AMAZON_LWA_CLIENT_SECRET=xxx

# Communication (Fitness, Amazon)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=xxx

# Video (Fitness only)
CREATOMATE_API_KEY=xxx
```

---

## Skills Location

All local skill definitions in `.claude/skills/`:

```
.claude/skills/
├── interview-prep/
│   ├── SKILL.md
│   └── USE_CASES.json
├── fitness-influencer-operations/
│   ├── SKILL.md
│   └── USE_CASES.json
├── amazon-seller-operations/
│   └── SKILL.md
└── naples-weather-report/
    └── SKILL.md
```

---

## Development Workflow

### 1. Develop in Project Folder
```bash
cd interview-prep-pptx/src/
# Edit scripts, test locally
```

### 2. Sync to Execution (for skills)
```bash
python deploy_to_skills.py --sync-execution --project interview-prep
```

### 3. Update Skill Definition
```bash
# Edit .claude/skills/{skill}/SKILL.md or project SKILL.md
```

### 4. Deploy to Production
```bash
# Railway (web apps)
cd interview-prep-pptx && railway up

# GitHub repo (skills)
python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant
```

### 5. Commit Changes
```bash
git add -A && git commit -m "feat: Description" && git push
```

---

## Jumping Between Projects

When switching projects mid-session:

1. **Say which project:** "Let's work on Amazon seller"
2. **Reference this index:** Files are in `projects/amazon-seller/`
3. **After changes:** Sync to execution + update skill
4. **Deploy:** Railway for web apps, GitHub for skills

### Example: Copy feature between projects

"Add email notifications to Amazon seller like we have in Fitness"

1. Check Fitness: `projects/fitness-influencer/src/`
2. It uses shared: `execution/twilio_sms.py`
3. Add to Amazon config in `deploy_to_skills.py`
4. Sync: `python deploy_to_skills.py --sync-execution --project amazon-seller`
5. Update skill: `.claude/skills/amazon-seller-operations/SKILL.md`
