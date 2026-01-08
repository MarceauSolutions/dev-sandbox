# AI Assistants Hub - Development Sandbox

Central development workspace for AI-powered automation assistants using the **3-Layer Architecture** (Directive → Orchestration → Execution).

## Quick Navigation

**See [PROJECT_INDEX.md](PROJECT_INDEX.md) for detailed file paths and switching between projects.**

## Active Projects

| Project | Status | Directory | Production URL |
|---------|--------|-----------|----------------|
| **Fitness Influencer** | Live | [`projects/fitness-influencer/`](projects/fitness-influencer/) | Railway |
| **Interview Prep** | Live | [`interview-prep-pptx/`](interview-prep-pptx/) | [Railway](https://interview-prep-pptx-production.up.railway.app/app) |
| **Amazon Seller** | Dev | [`projects/amazon-seller/`](projects/amazon-seller/) | - |
| **Naples Weather** | Dev | [`projects/naples-weather/`](projects/naples-weather/) | - |

## Repository Structure

```
dev-sandbox/
├── projects/                    # Individual AI assistant projects
│   ├── fitness-influencer/      # Fitness content automation
│   │   ├── src/                 # Python scripts
│   │   ├── frontend/            # Web interface
│   │   └── README.md
│   ├── interview-prep/          # → symlink to interview-prep-pptx/
│   ├── amazon-seller/           # Amazon SP-API automation
│   │   └── src/
│   ├── naples-weather/          # Weather report generator
│   └── shared/                  # Shared utilities across projects
│       ├── ai/                  # AI services (Grok)
│       ├── google/              # Google APIs (Gmail, Sheets)
│       ├── analytics/           # Business analytics
│       └── communication/       # SMS, email
│
├── interview-prep-pptx/         # Railway-linked Interview Prep project
│   ├── src/
│   ├── frontend/
│   ├── Procfile
│   └── railway.json
│
├── execution/                   # All execution scripts (skill access)
├── directives/                  # SOPs in Markdown format
├── .claude/skills/              # Skill configurations
│
├── PROJECT_INDEX.md             # Quick navigation guide
├── index.html                   # Main website homepage
├── setup_form.html              # Fitness Influencer setup form
└── deploy_to_skills.py          # Deployment pipeline
```

## Working on Projects

### Switch to a Project
```bash
cd projects/fitness-influencer   # Fitness Influencer
cd interview-prep-pptx           # Interview Prep
cd projects/amazon-seller        # Amazon Seller
```

### Key Locations by Project

| Project | Scripts | Frontend | Skill | Directive |
|---------|---------|----------|-------|-----------|
| Fitness | `projects/fitness-influencer/src/` | `projects/fitness-influencer/frontend/` | `.claude/skills/fitness-influencer-operations/` | `directives/fitness_influencer_operations.md` |
| Interview | `interview-prep-pptx/src/` | `interview-prep-pptx/frontend/` | `.claude/skills/interview-prep/` | `directives/interview_prep.md` |
| Amazon | `projects/amazon-seller/src/` | TODO | `.claude/skills/amazon-seller-operations/` | `directives/amazon_seller_operations.md` |

## Shared Utilities

Common services used across projects (located in `projects/shared/`):

| Utility | Path | Used By |
|---------|------|---------|
| Grok AI Images | `shared/ai/grok_image_gen.py` | Fitness, Interview |
| Gmail Monitor | `shared/google/gmail_monitor.py` | Fitness, Amazon |
| Revenue Analytics | `shared/analytics/revenue_analytics.py` | Fitness, Amazon |
| Twilio SMS | `shared/communication/twilio_sms.py` | Fitness, Amazon |

## Deployment

### Deploy to Railway
```bash
cd interview-prep-pptx
railway up
railway domain
```

### Deploy to Skills
```bash
python deploy_to_skills.py --project fitness-influencer-operations
```

## Environment Variables

All projects share the root `.env` file:

```env
# AI Services (All projects)
ANTHROPIC_API_KEY=xxx
XAI_API_KEY=xxx

# Google APIs (Fitness, Amazon)
GOOGLE_CREDENTIALS_PATH=credentials.json

# Amazon SP-API (Amazon only)
AMAZON_SELLER_ID=xxx
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx

# Video Services (Fitness only)
SHOTSTACK_API_KEY=xxx
CREATOMATE_API_KEY=xxx

# Communication (Fitness, Amazon)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
```

## 3-Layer Architecture

1. **Directives** (`directives/`) - SOPs defining what to do
2. **Orchestration** - Claude reads directives, makes decisions
3. **Execution** (`execution/`) - Deterministic Python scripts

## Development Workflow

1. **Edit in project folder** - `projects/{project}/src/` or `interview-prep-pptx/src/`
2. **Copy to execution** - For skill access: `cp {project}/src/*.py execution/`
3. **Update skill** - `.claude/skills/{skill-name}/SKILL.md`
4. **Deploy** - Railway or `deploy_to_skills.py`

## Jumping Between Projects

When switching projects mid-session, just say:
- "Let's work on Amazon seller" → Files in `projects/amazon-seller/`
- "Switch to fitness influencer" → Files in `projects/fitness-influencer/`
- "Back to interview prep" → Files in `interview-prep-pptx/`

Features can be shared between projects using `projects/shared/`.

## Session History

**📚 [View All Sessions](docs/sessions/README.md)**
