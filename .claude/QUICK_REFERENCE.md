# Quick Reference: DOE → Skills Pipeline

## Development Workflow

```bash
# 1. Create directive
vim directives/my_workflow.md

# 2. Create execution script
vim execution/my_workflow.py

# 3. Test manually
python execution/my_workflow.py

# 4. Test with Claude
# Ask: "Run my workflow with test data"

# 5. Iterate until stable
# Fix bugs, update directive, repeat
```

## Deployment

```bash
# Deploy to production
python execution/deploy_to_skills.py my_workflow --project my-project

# That's it! Skill is now active.
```

## Project Management

```bash
# Create project
python execution/manage_agent_skills.py create-project \
  --name PROJECT \
  --description "Description" \
  --domains "domain1,domain2"

# List projects
python execution/manage_agent_skills.py list

# View project details
python execution/manage_agent_skills.py list --project PROJECT

# Add skill to project
python execution/manage_agent_skills.py add --project PROJECT --skill SKILL

# Remove skill from project
python execution/manage_agent_skills.py remove --project PROJECT --skill SKILL

# List all skills
python execution/manage_agent_skills.py list-skills
```

## File Locations

| What | Where |
|------|-------|
| Directives (dev) | `directives/*.md` |
| Execution scripts | `execution/*.py` |
| Skills (prod) | `.claude/skills/*/SKILL.md` |
| Project manifests | `.claude/projects/*-skills.json` |
| Agent configs | `.claude/agents/*.json` |
| Intermediate files | `.tmp/*` |

## The Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT (DOE)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Directive  │  │ Orchestration│  │  Execution   │       │
│  │  (.md SOP)  │→ │   (Claude)   │→ │  (Python)    │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  Test, iterate, debug, refine...                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ deploy_to_skills.py
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   PRODUCTION (Skills)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  SKILL.md   │  │   Project    │  │    Agent     │       │
│  │ (references │→ │   Manifest   │→ │  (granular   │       │
│  │  directive) │  │              │  │   access)    │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  Stable, tested, production-ready                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Develop in DOE** - Fast iteration, full debugging
2. **Deploy when stable** - Only production-ready workflows
3. **One project per use case** - Amazon, Healthcare, Personal, etc.
4. **Granular access** - Each agent sees only its skills
5. **Self-anneal** - Update directives as you learn

## Example: Complete Flow

```bash
# Day 1-3: Development
vim directives/amazon_optimizer.md        # Write SOP
vim execution/amazon_optimizer.py         # Build script
python execution/amazon_optimizer.py      # Test
# Iterate, fix bugs, test with real data

# Day 4: Deployment
python execution/deploy_to_skills.py amazon_optimizer --project amazon-assistant

# Day 5+: Production
# Just ask Claude: "Optimize my Amazon inventory"
# Agent uses the skill automatically
```

## Common Tasks

### Start a new project
```bash
python execution/manage_agent_skills.py create-project --name my-project
```

### Deploy a workflow
```bash
python execution/deploy_to_skills.py my_workflow --project my-project
```

### Check what's deployed
```bash
python execution/manage_agent_skills.py list --project my-project
```

### Add existing skill to project
```bash
python execution/manage_agent_skills.py add --project my-project --skill existing-skill
```

## Documentation

- **Full pipeline:** [PROJECT_DEVELOPMENT_PIPELINE.md](PROJECT_DEVELOPMENT_PIPELINE.md)
- **Usage guide:** [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **DOE method:** [DOE_PIPELINE_REFERENCE.md](DOE_PIPELINE_REFERENCE.md)
- **Core architecture:** [../CLAUDE.md](../CLAUDE.md)
