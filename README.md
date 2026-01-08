# AI Assistants Hub - Development Sandbox

Central development workspace for AI-powered automation assistants using the **3-Layer Architecture** (Directive → Orchestration → Execution).

## Active Projects

| Project | Status | Production URL | Description |
|---------|--------|----------------|-------------|
| [Fitness Influencer](projects/fitness-influencer/) | **Live** | Railway | Video editing, graphics, email, analytics |
| [Interview Prep](projects/interview-prep/) | **Live** | [Railway](https://interview-prep-pptx-production.up.railway.app/app) | Company research & PowerPoint generation |
| [Amazon Seller](projects/amazon-seller/) | Dev | - | SP-API inventory & fee management |
| [Naples Weather](projects/naples-weather/) | Dev | - | Automated weather report generation |

## Repository Structure

```
dev-sandbox/
├── projects/                    # Individual AI assistant projects
│   ├── fitness-influencer/      # Fitness content automation
│   │   ├── src/                 # Python scripts
│   │   ├── frontend/            # Web interface
│   │   └── README.md
│   ├── interview-prep/          # Interview preparation tool
│   │   ├── src/
│   │   ├── frontend/
│   │   └── README.md
│   ├── amazon-seller/           # Amazon SP-API automation
│   └── naples-weather/          # Weather report generator
│
├── execution/                   # All execution scripts (shared location)
├── directives/                  # SOPs in Markdown format
│
├── .claude/
│   └── skills/                  # Skill configurations for Claude
│       ├── fitness-influencer-operations/
│       │   ├── SKILL.md
│       │   └── USE_CASES.json
│       ├── interview-prep/
│       │   ├── SKILL.md
│       │   └── USE_CASES.json
│       ├── amazon-seller-operations/
│       └── naples-weather-report/
│
├── index.html                   # Main website homepage
├── deploy_to_skills.py          # Deployment pipeline
└── CLAUDE.md                    # Agent instructions
```

## 3-Layer Architecture

### Layer 1: Directive (What to do)
- SOPs written in Markdown in `directives/`
- Define goals, inputs, tools, outputs, and edge cases
- Natural language instructions

### Layer 2: Orchestration (Decision making)
- Claude reads directives and calls execution scripts
- Handles errors, asks for clarification
- Updates directives with learnings

### Layer 3: Execution (Doing the work)
- Deterministic Python scripts in `execution/`
- API calls, data processing, file operations
- Reliable, testable, fast

## Quick Start

### Run Interview Prep (Local)
```bash
source .env && ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" python execution/interview_research.py \
  --company "Google" --role "Software Engineer"
python execution/pptx_generator.py --input .tmp/interview_research_google.json
```

### Run Fitness Video Editor
```bash
python execution/video_jumpcut.py --input raw_video.mp4 --output edited.mp4
```

### Deploy a Project to Skills
```bash
python deploy_to_skills.py --project fitness-influencer-operations
```

## Skills Deployment Pipeline

To deploy a tested project as a Claude skill:

1. **Develop** in `execution/` and document in `directives/`
2. **Test** thoroughly using the directive workflow
3. **Create skill** in `.claude/skills/{skill-name}/`
   - `SKILL.md` - Skill definition with trigger phrases
   - `USE_CASES.json` - Known use cases for learning
4. **Deploy** to Railway or run `deploy_to_skills.py`

### Skill Registration

Skills are automatically available when their `SKILL.md` is in `.claude/skills/`. Key components:

```yaml
---
name: skill-name
description: What triggers this skill
allowed-tools: Bash(python:*), Read
---
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# AI APIs
ANTHROPIC_API_KEY=your_key
XAI_API_KEY=your_key

# Google APIs
GOOGLE_CREDENTIALS_PATH=credentials.json

# Video Services
SHOTSTACK_API_KEY=your_key
CREATOMATE_API_KEY=your_key

# Communication
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
```

## Website

The main website (`index.html`) provides access to all AI assistants:
- Dropdown menu for quick access
- Module cards with feature lists
- Direct links to deployed apps

## Documentation Index

### Project Documentation
- [Fitness Influencer Guide](projects/fitness-influencer/README.md)
- [Interview Prep Guide](projects/interview-prep/README.md)
- [Amazon Seller Guide](projects/amazon-seller/README.md)

### Directives (SOPs)
- [fitness_influencer_operations.md](directives/fitness_influencer_operations.md)
- [interview_prep.md](directives/interview_prep.md)
- [pptx_interactive_edit.md](directives/pptx_interactive_edit.md)
- [amazon_seller_operations.md](directives/amazon_seller_operations.md)

### Skills Configuration
- [Fitness Influencer Skill](.claude/skills/fitness-influencer-operations/SKILL.md)
- [Interview Prep Skill](.claude/skills/interview-prep/SKILL.md)

## Development Workflow

1. **Start here** - All development happens in this workspace
2. **Create directive** - Document the workflow in `directives/`
3. **Build scripts** - Create execution scripts in `execution/`
4. **Test locally** - Use directives to test the workflow
5. **Create skill** - Add skill config to `.claude/skills/`
6. **Deploy** - Push to Railway or run `deploy_to_skills.py`

## Deploying to Production

### Railway Deployment (Recommended)
```bash
cd projects/interview-prep
railway init
railway up
railway domain
```

### Skills Deployment
```bash
python deploy_to_skills.py --project project-name
```

## Session History

This workspace maintains detailed session notes to preserve context across work sessions.

**📚 [View All Sessions](docs/sessions/README.md)**

## License

Private repository - Marceau Solutions
