# Project Development Pipeline: DOE → Claude Skills

## Overview

This document defines the complete pipeline for developing project-specific AI agents with custom toolsets. The methodology separates **development** (DOE method in dev-sandbox) from **production** (Claude Skills with granular access control).

## The Two Environments

### 1. Development Environment (DOE Method)
**Location:** `/dev-sandbox/` (directives/, execution/)
**Purpose:** Rapid iteration, testing, debugging, fine-tuning
**Method:** Directive → Orchestration → Execution (DOE)

**Use for:**
- Building new workflows
- Testing API integrations
- Debugging scripts
- Experimenting with prompts
- Refining error handling
- Iterating on tool behavior

**Characteristics:**
- ✓ Fast iteration
- ✓ Easy debugging
- ✓ Full visibility into execution
- ✓ Can modify on the fly
- ✓ Test with real data

### 2. Production Environment (Claude Skills)
**Location:** `/.claude/skills/`
**Purpose:** Production-ready, stable, agent-accessible tools
**Method:** SKILL.md manifests with granular access control

**Use for:**
- Deployed, tested workflows
- Project-specific agent capabilities
- Controlled tool access per agent
- Production automation
- Client-facing applications

**Characteristics:**
- ✓ Stable, tested code
- ✓ Controlled access
- ✓ Project-scoped permissions
- ✓ Version controlled
- ✓ Team shareable

## Development → Production Pipeline

### Phase 1: Development (DOE Method)

**Step 1: Create Directive**
```
directives/amazon_process_orders.md
```
- Define goal, inputs, outputs
- Document API endpoints
- List edge cases
- Write SOP in natural language

**Step 2: Build Execution Tools**
```
execution/amazon_process_orders.py
```
- Implement deterministic Python scripts
- Handle API authentication
- Process data reliably
- Save outputs to .tmp/
- Test with real data

**Step 3: Iterate & Test**
- Run manually via Claude
- Fix bugs, update directive
- Refine error handling
- Document learnings
- Self-anneal until stable

**Step 4: Mark as Production-Ready**
When tool is:
- ✓ Tested with real data
- ✓ Error handling complete
- ✓ Edge cases documented
- ✓ API limits understood
- ✓ Performance acceptable

→ Ready to deploy to Claude Skills

### Phase 2: Deployment (Claude Skills)

**Step 5: Deploy to Skills**
```bash
python execution/deploy_to_skills.py amazon_process_orders
```

This script:
1. Reads `directives/amazon_process_orders.md`
2. Creates `.claude/skills/amazon-process-orders/SKILL.md`
3. Copies execution scripts (or references them)
4. Adds to project manifest (e.g., `amazon-assistant-skills.json`)
5. Validates skill format

**Step 6: Assign to Project**
Update project manifest:
```json
{
  "project": "amazon-assistant",
  "description": "Amazon Seller automation tools",
  "skills": [
    "amazon-process-orders",
    "amazon-inventory-optimizer",
    "amazon-sp-api-wrapper"
  ],
  "allowed_tools": ["Bash(python:*)", "Read", "Write"],
  "knowledge_domains": ["amazon-sp-api", "e-commerce", "inventory-management"]
}
```

### Phase 3: Agent Configuration

**Step 7: Create Agent Profile**
```
.claude/agents/amazon-assistant.json
```

Defines:
- Which skills this agent has access to
- Tool permissions
- Knowledge domains
- Project context

## Project Structure

```
dev-sandbox/
├── .claude/
│   ├── agents/                      # Agent-specific configurations
│   │   ├── amazon-assistant.json    # Amazon project agent
│   │   ├── omnipod-assistant.json   # Healthcare project agent
│   │   └── personal-assistant.json  # Personal productivity agent
│   │
│   ├── skills/                      # Production skills (deployed)
│   │   ├── amazon-process-orders/
│   │   │   └── SKILL.md
│   │   ├── amazon-inventory-optimizer/
│   │   │   └── SKILL.md
│   │   ├── diabetes-knowledge-base/
│   │   │   └── SKILL.md
│   │   └── email-responder/
│   │       └── SKILL.md
│   │
│   └── projects/                    # Project manifests
│       ├── amazon-assistant-skills.json
│       ├── omnipod-assistant-skills.json
│       └── personal-assistant-skills.json
│
├── directives/                      # Development directives (DOE)
│   ├── amazon_process_orders.md
│   ├── amazon_inventory_optimizer.md
│   └── diabetes_knowledge_base.md
│
├── execution/                       # Execution layer scripts
│   ├── amazon_process_orders.py
│   ├── amazon_inventory_optimizer.py
│   ├── deploy_to_skills.py          # Deployment automation
│   └── manage_agent_skills.py       # Agent configuration tool
│
└── .tmp/                           # Intermediate files
```

## Granular Skill Assignment

### Project Manifest System

Each project has a manifest defining its skill set:

**Example: Amazon Assistant**
```json
{
  "project": "amazon-assistant",
  "description": "Complete Amazon Seller automation",
  "version": "1.0.0",
  "skills": [
    "amazon-sp-api-wrapper",
    "amazon-process-orders",
    "amazon-inventory-optimizer",
    "amazon-product-research",
    "amazon-pricing-optimizer",
    "amazon-review-monitor"
  ],
  "allowed_tools": [
    "Bash(python execution/amazon_*.py:*)",
    "Read",
    "Write",
    "Grep"
  ],
  "knowledge_domains": [
    "amazon-sp-api",
    "e-commerce",
    "inventory-management",
    "pricing-strategies"
  ],
  "restrictions": [
    "No access to personal-* skills",
    "No access to healthcare-* skills"
  ]
}
```

**Example: Omnipod/Insulet Assistant**
```json
{
  "project": "omnipod-assistant",
  "description": "Healthcare/diabetes domain expert assistant",
  "version": "1.0.0",
  "skills": [
    "diabetes-knowledge-base",
    "insulin-pump-expert",
    "medical-email-responder",
    "clinical-data-analyzer",
    "regulatory-compliance-checker"
  ],
  "allowed_tools": [
    "Bash(python execution/healthcare_*.py:*)",
    "Read",
    "Grep",
    "WebFetch"
  ],
  "knowledge_domains": [
    "diabetes-management",
    "insulin-delivery-systems",
    "medical-devices",
    "healthcare-regulations",
    "clinical-terminology"
  ],
  "jargon": {
    "enabled": true,
    "domains": ["diabetes", "endocrinology", "medical-devices"]
  },
  "restrictions": [
    "No access to amazon-* skills",
    "No access to personal-* skills",
    "No execution of non-healthcare scripts"
  ]
}
```

### Agent Selection

When starting a project:

```bash
# Development mode (DOE)
claude --project amazon-assistant --mode dev

# Production mode (Skills only)
claude --project amazon-assistant --mode prod

# List available projects
claude --list-projects
```

## Workflow Examples

### Example 1: Amazon Assistant Development

**Day 1: Build in DOE**
```bash
# Create directive
vim directives/amazon_pricing_optimizer.md

# Build execution script
vim execution/amazon_pricing_optimizer.py

# Test manually
python execution/amazon_pricing_optimizer.py --sku ABC123

# Iterate with Claude
claude
> "Run the Amazon pricing optimizer for SKU ABC123"
> [Claude reads directive, runs script, returns results]
> [Find bugs, fix, repeat]
```

**Day 5: Deploy to Production**
```bash
# Deploy when stable
python execution/deploy_to_skills.py amazon_pricing_optimizer

# Add to project manifest
python execution/manage_agent_skills.py add \
  --project amazon-assistant \
  --skill amazon-pricing-optimizer

# Test in production mode
claude --project amazon-assistant --mode prod
> "Optimize pricing for all products"
```

### Example 2: New Project (Healthcare)

**Create new project:**
```bash
python execution/manage_agent_skills.py create-project \
  --name omnipod-assistant \
  --description "Healthcare/diabetes expert" \
  --domains "diabetes,medical-devices,healthcare"
```

**Develop skills in DOE:**
1. Create `directives/diabetes_knowledge_base.md`
2. Build `execution/diabetes_knowledge_base.py`
3. Test, iterate, refine
4. Deploy: `python execution/deploy_to_skills.py diabetes_knowledge_base`
5. Assign: `python execution/manage_agent_skills.py add --project omnipod-assistant --skill diabetes-knowledge-base`

**Use in production:**
```bash
claude --project omnipod-assistant
> "Draft an email response about Omnipod 5 algorithm updates"
> [Agent has access to diabetes knowledge, medical email responder, etc.]
> [Agent does NOT have access to Amazon or personal skills]
```

## Best Practices

### Development (DOE)
1. ✓ Always start in DOE for new workflows
2. ✓ Test with real data, real APIs
3. ✓ Document edge cases as you find them
4. ✓ Update directives with learnings
5. ✓ Keep execution scripts in `execution/`
6. ✓ Use `.tmp/` for all intermediate files

### Deployment (Skills)
1. ✓ Only deploy tested, stable workflows
2. ✓ Use semantic versioning for skills
3. ✓ Assign skills to specific projects
4. ✓ Review project manifests before deployment
5. ✓ Test agent access boundaries
6. ✓ Document skill dependencies

### Agent Configuration
1. ✓ Keep project manifests updated
2. ✓ Be explicit about restrictions
3. ✓ Define clear knowledge domains
4. ✓ Use jargon-specific configurations
5. ✓ Test cross-contamination (ensure no access to wrong skills)

## Key Advantages

### DOE Development
- Fast iteration without skill overhead
- Full debugging visibility
- Easy modification
- No production impact

### Skills Deployment
- Stable, version-controlled tools
- Granular access control
- Project-specific capabilities
- Professional, client-ready

### Combined Pipeline
- Best of both worlds
- Clear dev → prod path
- Reduced errors
- Scalable across projects

## Migration Path

**Existing workflows → This pipeline:**

1. Move existing directives to `directives/`
2. Move existing scripts to `execution/`
3. Test in DOE mode
4. Create project manifest
5. Deploy tested workflows to skills
6. Configure agent access
7. Switch to production mode

## Next Steps

1. Build `execution/deploy_to_skills.py`
2. Build `execution/manage_agent_skills.py`
3. Create project manifests
4. Test with Amazon Assistant project
5. Document agent invocation
6. Build CLI commands for project switching

This pipeline gives you complete control over tool development and production deployment with clean separation of concerns.
