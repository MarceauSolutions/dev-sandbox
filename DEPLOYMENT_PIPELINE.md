# Deployment Pipeline - Standard Operating Procedure

This document defines the standard operating procedure for developing AI assistants in the dev-sandbox and deploying them to production.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEV-SANDBOX (Development)                         │
│                    github.com/MarceauSolutions/dev-sandbox                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Interview  │  │   Fitness   │  │   Amazon    │  │   Naples    │        │
│  │    Prep     │  │ Influencer  │  │   Seller    │  │   Weather   │        │
│  │  PowerPoint │  │     AI      │  │     AI      │  │   Report    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐        │
│  │                     SHARED RESOURCES                           │        │
│  │  • execution/ scripts    • directives/ SOPs                    │        │
│  │  • projects/shared/      • .env credentials                    │        │
│  │  • .claude/skills/       • credentials.json                    │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Deploy
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION DEPLOYMENTS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐                        │
│  │   Railway Apps      │    │   GitHub Repos      │                        │
│  │   (Web APIs)        │    │   (Skills + Docs)   │                        │
│  ├─────────────────────┤    ├─────────────────────┤                        │
│  │ • Interview Prep    │    │ • Interview Prep    │                        │
│  │ • Fitness Influencer│    │   Assistant Repo    │                        │
│  │ • Amazon Seller     │    │ • Fitness Assistant │                        │
│  │ • Naples Weather    │    │   Repo              │                        │
│  └─────────────────────┘    │ • Amazon Assistant  │                        │
│                             │   Repo              │                        │
│                             └─────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

### Dev-Sandbox Organization

```
dev-sandbox/
├── CLAUDE.md                      # Agent instructions (3-layer architecture)
├── DEPLOYMENT_PIPELINE.md         # This file - SOP for deployments
├── PROJECT_INDEX.md               # Quick navigation between projects
├── README.md                      # Repository overview
│
├── .env                           # Shared credentials (not committed)
├── .env.example                   # Credential template
├── credentials.json               # Google OAuth (not committed)
├── token.json                     # Google tokens (not committed)
│
├── .claude/skills/                # LOCAL skill definitions for dev testing
│   ├── interview-prep/
│   │   ├── SKILL.md
│   │   └── USE_CASES.json
│   ├── fitness-influencer-operations/
│   │   ├── SKILL.md
│   │   └── USE_CASES.json
│   ├── amazon-seller-operations/
│   │   └── SKILL.md
│   └── naples-weather-report/
│       └── SKILL.md
│
├── directives/                    # SOPs for each capability
│   ├── interview_prep.md
│   ├── pptx_interactive_edit.md
│   ├── fitness_influencer_operations.md
│   ├── amazon_seller_operations.md
│   └── generate_naples_weather_report.md
│
├── execution/                     # ALL executable scripts (shared location)
│   ├── interview_research.py
│   ├── interview_prep_api.py
│   ├── pptx_generator.py
│   ├── pptx_editor.py
│   ├── session_manager.py
│   ├── video_jumpcut.py
│   ├── educational_graphics.py
│   ├── amazon_sp_api.py
│   ├── amazon_fee_calculator.py
│   ├── gmail_monitor.py          # Shared across projects
│   ├── grok_image_gen.py         # Shared across projects
│   ├── revenue_analytics.py      # Shared across projects
│   ├── twilio_sms.py             # Shared across projects
│   └── ...
│
├── projects/                      # Project-specific development
│   ├── interview-prep -> ../interview-prep-pptx  # Symlink
│   ├── fitness-influencer/
│   │   ├── src/
│   │   ├── frontend/
│   │   └── README.md
│   ├── amazon-seller/
│   │   ├── src/
│   │   └── README.md
│   ├── naples-weather/
│   │   └── src/
│   └── shared/                    # Cross-project utilities
│       ├── ai/
│       ├── google/
│       ├── analytics/
│       └── communication/
│
├── interview-prep-pptx/           # Standalone project (Railway deployment)
│   ├── src/
│   ├── frontend/
│   ├── railway.json
│   ├── Procfile
│   ├── SKILL.md
│   └── README.md
│
├── deploy_to_skills.py            # Deployment script
└── .tmp/                          # Temporary/intermediate files
```

## Development Workflow

### Phase 1: Development (in dev-sandbox)

1. **Choose your project folder:**
   ```bash
   cd projects/fitness-influencer    # or
   cd interview-prep-pptx            # or
   cd projects/amazon-seller
   ```

2. **Develop scripts in `src/`:**
   - Write/edit Python scripts
   - Test locally
   - Use shared utilities from `projects/shared/`

3. **Update directive if needed:**
   - Edit `directives/{project_name}.md`
   - Add new capabilities, edge cases, learnings

4. **Update local skill definition:**
   - Edit `.claude/skills/{skill-name}/SKILL.md`
   - Add trigger phrases, update documentation

### Phase 2: Sync to Execution (for skills access)

After testing, sync scripts to `execution/` for skill access:

```bash
# Interview Prep
cp interview-prep-pptx/src/*.py execution/

# Fitness Influencer
cp projects/fitness-influencer/src/*.py execution/

# Amazon Seller
cp projects/amazon-seller/src/*.py execution/

# Or use the sync command:
python deploy_to_skills.py --sync-execution --project interview-prep
```

### Phase 3: Deploy to Production

#### Option A: Railway (Web APIs)

For projects with web interfaces:

```bash
cd interview-prep-pptx
railway up

# Or for other projects:
cd projects/fitness-influencer
railway up
```

#### Option B: GitHub Skills Repository

For AI assistant capabilities, deploy to dedicated GitHub repos:

```bash
python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant
python deploy_to_skills.py --project fitness-influencer --repo MarceauSolutions/fitness-influencer-assistant
python deploy_to_skills.py --project amazon-seller --repo MarceauSolutions/amazon-seller-assistant
```

This will:
1. Copy SKILL.md, USE_CASES.json to the repo's `.claude/skills/` directory
2. Copy required scripts to the repo
3. Commit and push changes

## Shared Resources

### Credentials (Single Source of Truth)

All projects share the root `.env` file:

| Variable | Used By | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | All | Claude API for AI research |
| `XAI_API_KEY` | Interview, Fitness | Grok image generation |
| `GOOGLE_CREDENTIALS_PATH` | Fitness, Amazon | Gmail, Sheets access |
| `AMAZON_*` | Amazon only | SP-API access |
| `TWILIO_*` | Fitness, Amazon | SMS notifications |
| `CREATOMATE_API_KEY` | Fitness | Video rendering |

### Shared Scripts

Scripts used by multiple projects:

| Script | Projects | Purpose |
|--------|----------|---------|
| `grok_image_gen.py` | Interview, Fitness | AI image generation |
| `gmail_monitor.py` | Fitness, Amazon | Email summarization |
| `revenue_analytics.py` | Fitness, Amazon | Business metrics |
| `twilio_sms.py` | Fitness, Amazon | SMS notifications |
| `google_auth_setup.py` | All Google | OAuth setup |

## Project-Specific Details

### Interview Prep PowerPoint

| Attribute | Value |
|-----------|-------|
| Development | `interview-prep-pptx/src/` |
| Frontend | `interview-prep-pptx/frontend/index.html` |
| Skill | `.claude/skills/interview-prep/` |
| Directive | `directives/interview_prep.md` |
| Railway URL | https://interview-prep-pptx-production.up.railway.app/app |
| Scripts | `interview_research.py`, `pptx_generator.py`, `pptx_editor.py`, `session_manager.py`, `interview_prep_api.py` |

### Fitness Influencer AI

| Attribute | Value |
|-----------|-------|
| Development | `projects/fitness-influencer/src/` |
| Frontend | `projects/fitness-influencer/frontend/index.html` |
| Skill | `.claude/skills/fitness-influencer-operations/` |
| Directive | `directives/fitness_influencer_operations.md` |
| Railway URL | (Railway deployment) |
| Scripts | `video_jumpcut.py`, `educational_graphics.py`, `gmail_monitor.py`, `revenue_analytics.py` |

### Amazon Seller AI

| Attribute | Value |
|-----------|-------|
| Development | `projects/amazon-seller/src/` |
| Skill | `.claude/skills/amazon-seller-operations/` |
| Directive | `directives/amazon_seller_operations.md` |
| Railway URL | Not deployed yet |
| Scripts | `amazon_sp_api.py`, `amazon_fee_calculator.py`, `amazon_inventory_optimizer.py` |

### Naples Weather Report

| Attribute | Value |
|-----------|-------|
| Development | `projects/naples-weather/src/` |
| Skill | `.claude/skills/naples-weather-report/` |
| Directive | `directives/generate_naples_weather_report.md` |
| Scripts | `fetch_naples_weather.py`, `generate_weather_report.py` |

## Deployment Checklist

Before deploying any project:

- [ ] Scripts tested locally
- [ ] Directive updated with any new learnings
- [ ] SKILL.md has correct trigger phrases
- [ ] Scripts synced to `execution/` directory
- [ ] Environment variables documented in `.env.example`
- [ ] README.md updated with any new features

## Commands Reference

```bash
# Switch to a project
cd projects/fitness-influencer
cd interview-prep-pptx
cd projects/amazon-seller

# Sync scripts to execution
cp interview-prep-pptx/src/*.py execution/
cp projects/fitness-influencer/src/*.py execution/

# Deploy to Railway
cd interview-prep-pptx && railway up

# Deploy to skills repo (future)
python deploy_to_skills.py --project interview-prep --repo MarceauSolutions/interview-prep-assistant

# Test a skill locally
source .env && python execution/interview_research.py --company "Apple" --role "Engineer"

# Check git status
git status
git add -A && git commit -m "feat: Description" && git push
```

## Version Control Strategy

1. **dev-sandbox**: Main development repo - all work happens here
2. **Project Repos**: Receive deployed skills via `deploy_to_skills.py`
3. **Website Repo**: Separate repo for marceausolutions.com

Changes flow: `dev-sandbox` → `project-specific repos` → `production`

Never edit production repos directly. Always develop in dev-sandbox first.
