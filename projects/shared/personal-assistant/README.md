# William's Personal AI Assistant

A unified AI assistant that aggregates all capabilities from dev-sandbox projects. No frontend needed - interaction happens through Claude Code chat.

## Architecture

This project follows the same DOE (Directive-Orchestration-Execution) architecture as all other projects, with one key difference: **no frontend deployment**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEV-SANDBOX (Development)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                     PROJECT SKILLS                              │    │
│  │                                                                 │    │
│  │  interview-prep/   fitness-influencer/   amazon-seller/        │    │
│  │  naples-weather/   resume/   [future projects...]              │    │
│  │                                                                 │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                             │                                           │
│                             │ Auto-deploy                               │
│                             ▼                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              PERSONAL AI ASSISTANT                              │    │
│  │                                                                 │    │
│  │  .claude/skills/personal-assistant/                            │    │
│  │  ├── SKILL.md (aggregated capabilities)                        │    │
│  │  ├── VERSION                                                   │    │
│  │  └── USE_CASES.json                                            │    │
│  │                                                                 │    │
│  │  + All skills from other projects                              │    │
│  │  + Personal productivity tools                                 │    │
│  │  + Session/context management                                  │    │
│  │                                                                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Interaction
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE CHAT (Interface)                         │
│                                                                         │
│  User: "Research Google for PM interview"                              │
│  Claude: [Reads personal-assistant SKILL.md]                           │
│          [Routes to interview-prep skill]                              │
│          [Executes workflow]                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## How It Works

1. **Skills are developed** in their respective projects (interview-prep, fitness-influencer, etc.)
2. **Skills auto-deploy** to `.claude/skills/` via `deploy_to_skills.py`
3. **Personal assistant SKILL.md** aggregates all capabilities
4. **You interact** via Claude Code chat - no frontend needed
5. **Claude reads** the skill files and executes appropriate workflows

## Capabilities (Aggregated from All Projects)

### Interview Prep
- Research companies and roles
- Generate PowerPoint presentations
- Mock interview practice
- Cheat sheets, flashcards, checklists

### Fitness Influencer
- Video editing (jump cuts)
- AI image generation
- Email management
- Revenue analytics

### Amazon Seller
- Inventory management
- Fee calculations
- Review monitoring

### Naples Weather
- Weekly weather reports
- PDF generation

### Resume
- Role-tailored resume generation (SWE, AI/ML, Tech Lead, PM)
- Job-specific customization
- ATS optimization

### Personal Productivity (Planned)
- Task management
- Note organization
- Calendar integration

## File Structure

```
projects/personal-assistant/
├── README.md                 # This file
├── VERSION                   # Current version
├── CHANGELOG.md              # Version history
├── src/
│   └── (personal tools)      # Any personal-specific scripts
└── workflows/
    └── (personal workflows)  # Any personal-specific workflows

.claude/skills/personal-assistant/
├── SKILL.md                  # Master skill file (reads from all projects)
├── VERSION                   # Deployed version
└── USE_CASES.json            # Example use cases
```

## Deployment

Skills deploy to personal assistant automatically when you run:
```bash
python deploy_to_skills.py --project [any-project]
```

The personal assistant SKILL.md is the **entry point** that knows about all other skills.

## Usage

Just talk to me in Claude Code chat:

```
"Help me prepare for my Google interview"
→ Routes to interview-prep skill

"Create a video with jump cuts"
→ Routes to fitness-influencer skill

"Check my Amazon inventory"
→ Routes to amazon-seller skill

"Generate Naples weather report"
→ Routes to naples-weather skill

"Tailor my resume for Stripe backend engineer"
→ Routes to resume skill
```

## Key Differences from Other Projects

| Aspect | Other Projects | Personal Assistant |
|--------|----------------|-------------------|
| Frontend | Web UI on Railway | None (Claude Code chat) |
| Deployment | Railway + GitHub | Local skills only |
| Users | Public/external | William only |
| Interaction | HTTP API | Direct tool execution |

## Version History

See CHANGELOG.md for version history.
