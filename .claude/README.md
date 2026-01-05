# Claude Skills Development System

Complete pipeline for developing project-specific AI agents with granular skill access control.

## What We Built

A systematic approach to develop, test, and deploy AI workflows:

### Development Environment (DOE Method)
- **Directives:** Natural language SOPs in `directives/`
- **Execution:** Deterministic Python scripts in `execution/`
- **Orchestration:** Claude makes decisions and routes to tools
- **Purpose:** Fast iteration, testing, debugging

### Production Environment (Claude Skills)
- **Skills:** Production-ready workflows in `.claude/skills/`
- **Projects:** Organized skill collections in `.claude/projects/`
- **Agents:** Granular access control in `.claude/agents/`
- **Purpose:** Stable, tested, production deployment

### Automation Tools
- `execution/deploy_to_skills.py` - Deploy workflows to production
- `execution/manage_agent_skills.py` - Manage projects and permissions

## Current State

### Projects Deployed

1. **amazon-assistant** (1 skill)
   - amazon-seller-operations
   - Domains: amazon-sp-api, e-commerce, inventory-management, pricing-optimization

2. **weather-reports** (1 skill)
   - generate-naples-weather-report
   - Domains: meteorology, weather-forecasting, data-visualization

### Directory Structure

```
.claude/
├── agents/
│   ├── amazon-assistant.json
│   └── weather-reports.json
├── projects/
│   ├── amazon-assistant-skills.json
│   └── weather-reports-skills.json
├── skills/
│   ├── amazon-seller-operations/
│   │   └── SKILL.md
│   ├── generate-naples-weather-report/
│   │   └── SKILL.md
│   └── naples-weather-report/
│       └── SKILL.md
├── DOE_PIPELINE_REFERENCE.md       # DOE methodology
├── PROJECT_DEVELOPMENT_PIPELINE.md  # Complete pipeline docs
├── USAGE_GUIDE.md                   # Step-by-step guide
├── QUICK_REFERENCE.md               # Command reference
└── README.md                        # This file
```

## Quick Start

### 1. Develop a Workflow (DOE)

```bash
# Create directive
vim directives/my_workflow.md

# Create execution script
vim execution/my_workflow.py

# Test
python execution/my_workflow.py

# Iterate with Claude until stable
```

### 2. Deploy to Production

```bash
# Deploy to skills
python execution/deploy_to_skills.py my_workflow --project my-project

# Skill is now active!
```

### 3. Use in Production

Just ask Claude naturally:
```
"Run my workflow"
```

Claude automatically detects and uses the appropriate skill.

## Example Projects

### Amazon Assistant
Automate Amazon Seller operations:
- Process orders
- Optimize inventory
- Monitor reviews
- Adjust pricing

Skills are scoped to Amazon/e-commerce only.

### Healthcare Assistant (Future)
Medical domain expert for companies like Omnipod:
- Diabetes knowledge base
- Email responder with medical jargon
- Clinical data analysis
- Regulatory compliance

Skills are scoped to healthcare only - no access to e-commerce tools.

## Key Benefits

### Separation of Concerns
- **Development (DOE):** Fast, flexible, debuggable
- **Production (Skills):** Stable, controlled, secure

### Granular Access Control
- Each project has specific skills
- No cross-contamination between projects
- Appropriate tool permissions per agent

### Self-Annealing
- System learns from errors
- Directives updated with learnings
- Continuous improvement

### Scalability
- Easy to add new projects
- Simple to deploy new skills
- Clear organization

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Command reference card |
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | Complete usage guide with examples |
| [PROJECT_DEVELOPMENT_PIPELINE.md](PROJECT_DEVELOPMENT_PIPELINE.md) | Full pipeline documentation |
| [DOE_PIPELINE_REFERENCE.md](DOE_PIPELINE_REFERENCE.md) | DOE methodology explained |

## Commands

### Project Management
```bash
# Create project
python execution/manage_agent_skills.py create-project --name NAME

# List projects
python execution/manage_agent_skills.py list

# View project
python execution/manage_agent_skills.py list --project NAME

# Add skill
python execution/manage_agent_skills.py add --project NAME --skill SKILL

# Remove skill
python execution/manage_agent_skills.py remove --project NAME --skill SKILL
```

### Deployment
```bash
# Deploy to skills
python execution/deploy_to_skills.py DIRECTIVE --project PROJECT

# List all skills
python execution/manage_agent_skills.py list-skills
```

## Philosophy

**DOE = Directive, Orchestration, Execution**

1. **Directive** (Layer 1): Natural language SOP - What to do
2. **Orchestration** (Layer 2): Claude makes decisions - When and how
3. **Execution** (Layer 3): Python scripts do work - Reliably and consistently

This architecture solves the probabilistic vs deterministic mismatch:
- LLMs are probabilistic (good for decisions)
- Business logic is deterministic (needs consistency)
- DOE separates these concerns

## Next Steps

1. Review the [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Read the [USAGE_GUIDE.md](USAGE_GUIDE.md)
3. Start developing your first workflow in DOE
4. Deploy when stable
5. Build your project-specific agent

The system is ready to use!
