# Project Index - Quick Navigation

Use this guide to quickly switch between projects and find the right files.

## Quick Commands

```bash
# Switch to a project
cd projects/fitness-influencer   # Fitness Influencer AI
cd projects/interview-prep       # Interview Prep PowerPoint
cd projects/amazon-seller        # Amazon Seller Operations
```

---

## Project Overview

| Project | Status | Directory | Skill | Deployment |
|---------|--------|-----------|-------|------------|
| **Fitness Influencer** | Live | `projects/fitness-influencer/` | `fitness-influencer-operations` | Railway |
| **Interview Prep** | Live | `projects/interview-prep/` | `interview-prep` | [Railway](https://interview-prep-pptx-production.up.railway.app/app) |
| **Amazon Seller** | Dev | `projects/amazon-seller/` | `amazon-seller-operations` | - |
| **Naples Weather** | Dev | `projects/naples-weather/` | `naples-weather-report` | - |

---

## Fitness Influencer AI

**When user says:** "Work on fitness influencer", "edit video", "create graphic", "email summary"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/fitness-influencer/src/` |
| Frontend | `projects/fitness-influencer/frontend/index.html` |
| Directive | `directives/fitness_influencer_operations.md` |
| Skill | `.claude/skills/fitness-influencer-operations/SKILL.md` |
| Execution (legacy) | `execution/video_jumpcut.py`, `execution/educational_graphics.py`, etc. |

### Scripts
- `video_jumpcut.py` - Jump-cut video editing
- `educational_graphics.py` - Create fitness graphics
- `gmail_monitor.py` - Email summarization (shared)
- `revenue_analytics.py` - Revenue tracking (shared)
- `grok_image_gen.py` - AI image generation (shared)
- `workout_plan_generator.py` - Workout plans
- `nutrition_guide_generator.py` - Nutrition guides
- `twilio_sms.py` - SMS notifications (shared)

### Deploy
```bash
cd projects/fitness-influencer
railway up
```

---

## Interview Prep PowerPoint

**When user says:** "Interview prep", "research company", "create presentation", "PowerPoint"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/interview-prep/src/` |
| Frontend | `projects/interview-prep/frontend/index.html` |
| Directive | `directives/interview_prep.md` |
| Skill | `.claude/skills/interview-prep/SKILL.md` |
| Execution (legacy) | `execution/interview_research.py`, `execution/pptx_generator.py`, etc. |

### Scripts
- `interview_research.py` - Company/role research via Claude
- `pptx_generator.py` - PowerPoint generation
- `pptx_editor.py` - Slide editing (text, images, new slides)
- `grok_image_gen.py` - AI image generation (shared)
- `interview_prep_api.py` - FastAPI backend

### Deploy
```bash
cd projects/interview-prep
railway up --service interview-prep-pptx
```

**Live URL:** https://interview-prep-pptx-production.up.railway.app/app

---

## Amazon Seller Operations

**When user says:** "Amazon seller", "inventory", "FBA fees", "SP-API"

### Key Files
| Purpose | Path |
|---------|------|
| Main scripts | `projects/amazon-seller/src/` |
| Frontend | `projects/amazon-seller/frontend/` (TODO) |
| Directive | `directives/amazon_seller_operations.md` |
| Skill | `.claude/skills/amazon-seller-operations/SKILL.md` |
| Execution (legacy) | `execution/amazon_*.py` |

### Scripts
- `amazon_sp_api.py` - Core SP-API client
- `amazon_fee_calculator.py` - FBA fee calculations
- `amazon_inventory_optimizer.py` - Restock recommendations
- `amazon_oauth_server.py` - OAuth authentication
- `setup_amazon_auth.py` - Credential setup wizard
- `gmail_monitor.py` - Supplier emails (shared)
- `revenue_analytics.py` - Revenue tracking (shared)

### Deploy
```bash
cd projects/amazon-seller
railway init
railway up
```

---

## Shared Utilities

Files used by multiple projects. Located in `projects/shared/`.

| Utility | Used By | Path |
|---------|---------|------|
| Grok Image Gen | Fitness, Interview | `projects/shared/ai/grok_image_gen.py` |
| Gmail Monitor | Fitness, Amazon | `projects/shared/google/gmail_monitor.py` |
| Revenue Analytics | Fitness, Amazon | `projects/shared/analytics/revenue_analytics.py` |
| Twilio SMS | Fitness, Amazon | `projects/shared/communication/twilio_sms.py` |
| Google Auth | All | `projects/shared/google/google_auth_setup.py` |

---

## Skills Location

All skills are in `.claude/skills/`:

```
.claude/skills/
├── fitness-influencer-operations/
│   ├── SKILL.md
│   └── USE_CASES.json
├── interview-prep/
│   ├── SKILL.md
│   └── USE_CASES.json
├── amazon-seller-operations/
│   └── SKILL.md
└── naples-weather-report/
    └── SKILL.md
```

---

## Execution Scripts (Legacy Location)

The `execution/` directory contains all scripts for backward compatibility with existing skills. When developing:

1. **Edit in `projects/{project}/src/`** - Primary development location
2. **Copy to `execution/`** - For skill access
3. **Deploy** - Push to Railway or run `deploy_to_skills.py`

---

## Environment Variables

All projects share the root `.env` file:

```env
# AI Services (All projects)
ANTHROPIC_API_KEY=xxx
XAI_API_KEY=xxx

# Google (Fitness, Amazon)
GOOGLE_CREDENTIALS_PATH=credentials.json

# Amazon SP-API (Amazon only)
AMAZON_SELLER_ID=xxx
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx
AMAZON_REFRESH_TOKEN=xxx

# Video Services (Fitness only)
SHOTSTACK_API_KEY=xxx
CREATOMATE_API_KEY=xxx

# Communication (Fitness, Amazon)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=xxx
```

---

## Jumping Between Projects

When switching projects mid-session:

1. **Say which project:** "Let's switch to Amazon seller"
2. **Reference this index:** Files are in `projects/amazon-seller/`
3. **Edit appropriate files:** Both `projects/*/src/` AND `execution/`
4. **Deploy if needed:** `railway up` or `deploy_to_skills.py`

### Example: Add feature to multiple projects

"Add email notifications to Amazon seller like we have in Fitness"

1. Check Fitness implementation: `projects/fitness-influencer/src/twilio_sms.py`
2. It uses shared utility: `projects/shared/communication/twilio_sms.py`
3. Import in Amazon project: Add to `projects/amazon-seller/src/`
4. Copy to execution: `cp projects/amazon-seller/src/new_file.py execution/`
5. Update skill: `.claude/skills/amazon-seller-operations/SKILL.md`
