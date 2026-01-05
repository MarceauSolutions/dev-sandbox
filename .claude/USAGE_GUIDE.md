# Claude Skills Development & Deployment Guide

## Quick Start

This guide shows you how to develop workflows using the DOE method and deploy them to Claude Skills for production use.

## The Complete Pipeline

```
Development (DOE)          →          Production (Skills)
------------------                    ---------------------
directives/*.md                       .claude/skills/*/SKILL.md
execution/*.py                        .claude/projects/*-skills.json
Test & iterate                        .claude/agents/*.json
```

## Step-by-Step Workflow

### 1. Develop in DOE Environment

**Create a directive:**
```bash
vim directives/amazon_pricing_optimizer.md
```

Write your SOP with:
- Goal
- Inputs/Outputs
- Tools/Scripts to use
- Edge cases
- Best practices

**Build execution script:**
```bash
vim execution/amazon_pricing_optimizer.py
```

Make it deterministic:
- Handle APIs
- Process data
- Save to `.tmp/`
- Return consistent results

**Test with Claude:**
```bash
# In Claude, ask naturally:
"Run the Amazon pricing optimizer for SKU ABC123"

# Claude will:
# 1. Read directives/amazon_pricing_optimizer.md
# 2. Execute execution/amazon_pricing_optimizer.py
# 3. Handle errors
# 4. Return results
```

**Iterate until stable:**
- Fix bugs
- Update directive with learnings
- Handle edge cases
- Test with real data

### 2. Deploy to Production

**When workflow is stable and tested:**

```bash
# Deploy to skills
python execution/deploy_to_skills.py amazon_pricing_optimizer --project amazon-assistant
```

This automatically:
- ✓ Creates `.claude/skills/amazon-pricing-optimizer/SKILL.md`
- ✓ References your execution scripts
- ✓ Adds to project manifest
- ✓ Makes it available to the agent

### 3. Use in Production

**The skill is now active!** Simply ask Claude naturally:

```
"Optimize pricing for all Amazon products"
```

Claude will:
1. Detect your request matches the skill
2. Load the SKILL.md instructions
3. Execute the workflow
4. Return results

## Project Management

### Create a New Project

```bash
python execution/manage_agent_skills.py create-project \
  --name omnipod-assistant \
  --description "Healthcare/diabetes expert assistant" \
  --domains "diabetes,medical-devices,healthcare"
```

This creates:
- `.claude/projects/omnipod-assistant-skills.json` (project manifest)
- `.claude/agents/omnipod-assistant.json` (agent configuration)

### Add Skills to a Project

```bash
# Deploy a skill and add it
python execution/deploy_to_skills.py diabetes_knowledge_base --project omnipod-assistant

# Or add an existing skill
python execution/manage_agent_skills.py add \
  --project omnipod-assistant \
  --skill medical-email-responder
```

### View Projects

```bash
# List all projects
python execution/manage_agent_skills.py list

# View project details
python execution/manage_agent_skills.py list --project amazon-assistant
```

### Remove Skills

```bash
python execution/manage_agent_skills.py remove \
  --project amazon-assistant \
  --skill old-deprecated-skill
```

### Configure a Project

```bash
python execution/manage_agent_skills.py configure --project amazon-assistant
```

Interactive prompts let you update:
- Description
- Knowledge domains
- Restrictions

## Example: Amazon Assistant Project

### Phase 1: Development (Week 1-2)

```bash
# Create directives for each workflow
directives/
  ├── amazon_process_orders.md
  ├── amazon_inventory_optimizer.md
  ├── amazon_pricing_optimizer.md
  └── amazon_review_monitor.md

# Build execution scripts
execution/
  ├── amazon_process_orders.py
  ├── amazon_inventory_optimizer.py
  ├── amazon_pricing_optimizer.py
  └── amazon_review_monitor.py

# Test each workflow manually
python execution/amazon_process_orders.py --test
python execution/amazon_inventory_optimizer.py --test
# etc...

# Test with Claude
"Process Amazon orders from the last 24 hours"
"Optimize inventory levels for low-stock items"
```

### Phase 2: Deployment (Week 3)

```bash
# Create project
python execution/manage_agent_skills.py create-project \
  --name amazon-assistant \
  --description "Amazon Seller automation and optimization tools" \
  --domains "amazon-sp-api,e-commerce,inventory-management"

# Deploy each workflow
python execution/deploy_to_skills.py amazon_process_orders --project amazon-assistant
python execution/deploy_to_skills.py amazon_inventory_optimizer --project amazon-assistant
python execution/deploy_to_skills.py amazon_pricing_optimizer --project amazon-assistant
python execution/deploy_to_skills.py amazon_review_monitor --project amazon-assistant

# View project
python execution/manage_agent_skills.py list --project amazon-assistant
```

Result:
```
Project: amazon-assistant
Skills:
  • amazon-process-orders
  • amazon-inventory-optimizer
  • amazon-pricing-optimizer
  • amazon-review-monitor
```

### Phase 3: Production Use

Now the Amazon Assistant agent has access to all 4 skills. Users can simply ask:

```
"Process today's Amazon orders"
"What products need restocking?"
"Optimize pricing for winter jackets"
"Show me recent negative reviews"
```

The agent automatically:
- Detects which skill to use
- Executes the appropriate workflow
- Returns results

## Example: Healthcare Project (Omnipod)

### Project Setup

```bash
# Create healthcare project
python execution/manage_agent_skills.py create-project \
  --name omnipod-assistant \
  --description "Healthcare diabetes management expert" \
  --domains "diabetes,insulin-pumps,medical-devices,endocrinology"
```

### Develop Skills

```bash
# In DOE environment
directives/
  ├── diabetes_knowledge_base.md
  ├── insulin_pump_troubleshooting.md
  ├── medical_email_responder.md
  └── clinical_data_analyzer.md

execution/
  ├── diabetes_knowledge_base.py
  ├── insulin_pump_troubleshooting.py
  ├── medical_email_responder.py
  └── clinical_data_analyzer.py

# Test with healthcare data
# Iterate until accurate
```

### Deploy

```bash
python execution/deploy_to_skills.py diabetes_knowledge_base --project omnipod-assistant
python execution/deploy_to_skills.py insulin_pump_troubleshooting --project omnipod-assistant
python execution/deploy_to_skills.py medical_email_responder --project omnipod-assistant
python execution/deploy_to_skills.py clinical_data_analyzer --project omnipod-assistant
```

### Production Use

Healthcare assistant now understands diabetes jargon and has specialized skills:

```
"Draft an email response about Omnipod 5 algorithm updates"
"Troubleshoot basal rate issues for pediatric patient"
"Analyze CGM data trends from the last 30 days"
```

## Granular Access Control

### Why It Matters

The Amazon Assistant should NOT have access to healthcare skills.
The Healthcare Assistant should NOT have access to e-commerce skills.

This prevents:
- Cross-contamination of knowledge
- Inappropriate responses
- Security issues

### How It Works

**Project manifests define boundaries:**

```json
// .claude/projects/amazon-assistant-skills.json
{
  "project": "amazon-assistant",
  "skills": ["amazon-*"],  // Only Amazon skills
  "restrictions": [
    "No access to healthcare-* skills",
    "No access to personal-* skills"
  ]
}
```

```json
// .claude/projects/omnipod-assistant-skills.json
{
  "project": "omnipod-assistant",
  "skills": ["diabetes-*", "insulin-*", "medical-*"],
  "restrictions": [
    "No access to amazon-* skills",
    "No access to e-commerce-* skills"
  ]
}
```

## File Structure Reference

```
dev-sandbox/
├── .claude/
│   ├── agents/                          # Agent configurations
│   │   ├── amazon-assistant.json
│   │   └── omnipod-assistant.json
│   │
│   ├── projects/                        # Project manifests
│   │   ├── amazon-assistant-skills.json
│   │   └── omnipod-assistant-skills.json
│   │
│   ├── skills/                          # Production skills
│   │   ├── amazon-process-orders/
│   │   │   └── SKILL.md
│   │   ├── diabetes-knowledge-base/
│   │   │   └── SKILL.md
│   │   └── naples-weather-report/
│   │       └── SKILL.md
│   │
│   ├── DOE_PIPELINE_REFERENCE.md        # DOE methodology
│   ├── PROJECT_DEVELOPMENT_PIPELINE.md  # This complete pipeline
│   └── USAGE_GUIDE.md                   # This file
│
├── directives/                          # Development directives
│   ├── amazon_process_orders.md
│   ├── diabetes_knowledge_base.md
│   └── generate_naples_weather_report.md
│
├── execution/                           # Execution scripts
│   ├── amazon_process_orders.py
│   ├── diabetes_knowledge_base.py
│   ├── deploy_to_skills.py              # Deployment tool
│   ├── manage_agent_skills.py           # Project management tool
│   └── fetch_naples_weather.py
│
├── .tmp/                                # Intermediate files
│   └── *.json, *.pdf, *.csv, etc.
│
└── CLAUDE.md                            # Core architecture docs
```

## Commands Reference

### Development

```bash
# Test a workflow manually
python execution/SCRIPT_NAME.py

# Test with Claude
# Just ask Claude naturally about the workflow
```

### Deployment

```bash
# Deploy a directive to skills
python execution/deploy_to_skills.py DIRECTIVE_NAME --project PROJECT_NAME

# Deploy without adding to project
python execution/deploy_to_skills.py DIRECTIVE_NAME
```

### Project Management

```bash
# Create project
python execution/manage_agent_skills.py create-project --name NAME --domains "domain1,domain2"

# Add skill
python execution/manage_agent_skills.py add --project PROJECT --skill SKILL

# Remove skill
python execution/manage_agent_skills.py remove --project PROJECT --skill SKILL

# List projects
python execution/manage_agent_skills.py list

# View project details
python execution/manage_agent_skills.py list --project PROJECT

# Configure project
python execution/manage_agent_skills.py configure --project PROJECT

# List available skills
python execution/manage_agent_skills.py list-skills
```

## Best Practices

### Development (DOE)
- ✓ Always test with real data
- ✓ Handle all edge cases
- ✓ Update directives as you learn
- ✓ Keep execution scripts deterministic
- ✓ Use `.tmp/` for intermediate files
- ✓ Don't deploy until stable

### Deployment (Skills)
- ✓ Only deploy tested workflows
- ✓ Assign skills to specific projects
- ✓ Define clear knowledge domains
- ✓ Set appropriate restrictions
- ✓ Review agent access boundaries
- ✓ Version your skills

### Project Organization
- ✓ One project per use case/client
- ✓ Clear naming conventions
- ✓ Document knowledge domains
- ✓ Explicit restrictions
- ✓ Regular skill audits

## Troubleshooting

### Skill not triggering

**Check:**
1. Is skill deployed? `python execution/manage_agent_skills.py list-skills`
2. Is skill in project? `python execution/manage_agent_skills.py list --project PROJECT`
3. Is SKILL.md description clear?
4. Try being more explicit in your request

### Wrong skill activating

**Solution:**
1. Review skill descriptions
2. Make descriptions more specific
3. Add restrictions to project manifests
4. Update `allowed-tools` to be more restrictive

### Execution script failing

**Debug:**
1. Test script directly: `python execution/SCRIPT.py`
2. Check error logs
3. Update directive with fix
4. Redeploy: `python execution/deploy_to_skills.py DIRECTIVE --project PROJECT`

## Next Steps

1. **Start developing:** Create your first directive and execution script
2. **Test in DOE:** Iterate until stable
3. **Deploy to skills:** Use `deploy_to_skills.py`
4. **Create projects:** Organize skills by use case
5. **Use in production:** Ask Claude naturally

The pipeline is ready! Start building your first project-specific agent.
