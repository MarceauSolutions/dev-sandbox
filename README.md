# Development Sandbox (dev-sandbox)

This is your **development and experimentation workspace** using the Directive-Orchestration-Execution (DOE) methodology.

## Purpose

Use this workspace to:
- 🧪 Tinker and experiment with new ideas
- 🔨 Build complex workflows from scratch
- 🐛 Debug and perfect automation scripts
- 📝 Develop detailed SOPs (directives)
- 🔄 Test self-annealing systems
- 💡 Prototype random crazy projects

**DO NOT use for production work.** Once a project is stable and tested, deploy it to a dedicated Skills workspace.

## Architecture Overview

This workspace follows a 3-layer architecture that separates concerns:

1. **Directives** (`directives/`) - Natural language SOPs that define what to do
2. **Orchestration** - AI agent that reads directives and makes decisions
3. **Execution** (`execution/`) - Deterministic Python scripts that do the work

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# (Google Cloud, Modal, Slack, etc.)
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install modal google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv requests
```

### 3. Google Cloud Setup (for Sheets/Slides)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API and Google Slides API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json` and place in workspace root
6. First run will generate `token.json` automatically

### 4. Modal Setup (for webhooks)

```bash
# Install Modal CLI
pip install modal

# Authenticate
modal token new

# Deploy webhooks (if configured)
modal deploy execution/modal_webhook.py
```

## Directory Structure

```
.
├── CLAUDE.md              # System instructions (mirrored to AGENTS.md, GEMINI.md)
├── README.md              # This file
├── .env                   # Environment variables (not committed)
├── .env.example           # Template for environment variables
├── credentials.json       # Google OAuth credentials (not committed)
├── token.json            # Google OAuth token (not committed)
├── directives/           # Natural language SOPs
├── execution/            # Python scripts (deterministic tools)
│   ├── modal_webhook.py  # Modal webhook handler
│   └── webhooks.json     # Webhook configuration
└── .tmp/                 # Temporary files (never committed)
```

## How It Works

### Creating a Directive

Directives are markdown files in `directives/` that define:
- Goal/purpose
- Required inputs
- Available tools (scripts to use)
- Expected outputs
- Edge cases and error handling

Example structure:
```markdown
# Directive: Task Name

## Goal
What this directive accomplishes

## Inputs
- Input 1: description
- Input 2: description

## Tools
- `execution/script_name.py` - What it does

## Process
1. Step 1
2. Step 2
3. Step 3

## Outputs
What gets produced

## Edge Cases
- Case 1: How to handle
- Case 2: How to handle
```

### Creating an Execution Script

Scripts in `execution/` should be:
- Deterministic (same input = same output)
- Single-purpose
- Well-documented
- Error-handling focused

### Self-Annealing Loop

When errors occur:
1. AI fixes the issue
2. Updates the script
3. Tests to verify
4. Updates the directive with learnings
5. System is now stronger

## Cloud Deliverables

This system produces cloud-based deliverables (Google Sheets, Slides, etc.) rather than local files. Local files in `.tmp/` are only intermediates and can be regenerated.

## Webhooks

Event-driven execution via Modal. Each webhook maps to a directive.

List webhooks:
```
https://nick-90891--claude-orchestrator-list-webhooks.modal.run
```

Execute directive:
```
https://nick-90891--claude-orchestrator-directive.modal.run?slug={slug}
```

See `directives/add_webhook.md` for complete setup instructions.

## Development → Production Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. DEVELOP (Here - DOE Workspace)                          │
├─────────────────────────────────────────────────────────────┤
│  • Create directive in directives/                          │
│  • Build Python scripts in execution/                       │
│  • Test manually with step-by-step orchestration            │
│  • Iterate until it works perfectly                         │
│  • Document learnings in directive                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. DEPLOY (Skills Workspace)                               │
├─────────────────────────────────────────────────────────────┤
│  • Run: python deploy_to_skills.py --project project-name   │
│  • Creates new Skills workspace for the project             │
│  • Converts directive → SKILL.md                            │
│  • Copies tested scripts to skill/scripts/                  │
│  • Add trigger phrases for auto-activation                  │
│  • Use in production via natural language                   │
└─────────────────────────────────────────────────────────────┘
```

## Deployed Projects

Projects developed here and deployed to production Skills workspaces:

### ✅ Client Onboarding + Sales CRM (Deployed)
**Skills Workspace:** `/Users/williammarceaujr./youtubeworkspace-skills/`

**What it does:**
- Client onboarding emails with Calendly
- ClickUp CRM with 7-stage pipeline
- Full customer information tracking

**Developed from:**
- `directives/onboard_client.md` → `client-onboarding` skill
- `directives/sales_crm.md` → `sales-crm-management` skill
- `execution/clickup_*.py` → `clickup-operations` skill

---

### 🔧 Amazon Seller Operations (In Development)
**Status:** Core functionality built, awaiting SP-API credentials

**What it does:**
- Inventory reorder optimization with cost-benefit analysis
- FBA fee calculations and storage cost projections (2026 rates)
- Review monitoring and compliance flagging
- Buy box tracking and price optimization
- Multi-marketplace operations

**Built so far:**
- `directives/amazon_seller_operations.md` - Master directive with 10 use cases
- `execution/amazon_sp_api.py` - Base API wrapper with caching
- `execution/amazon_inventory_optimizer.py` - Inventory optimizer
- `docs/AMAZON_SETUP.md` - Complete setup guide

**Next steps:**
- Complete SP-API developer registration
- Configure AWS IAM role and credentials
- Test with real seller data

---

### 📄 Markdown to PDF Converter (Complete)
**Status:** Ready to use

**What it does:**
- Convert markdown files to professional PDFs
- Automatic styling with headers, code blocks, tables
- Table of contents generation
- Syntax highlighting for code
- Batch conversion support

**Built:**
- `directives/convert_markdown_to_pdf.md` - Complete directive
- `execution/markdown_to_pdf.py` - Converter script
- `execution/styles/default_pdf.css` - Professional stylesheet
- `docs/PDF_CONVERSION_GUIDE.md` - Usage guide

**Usage:**
```bash
# Single file
python execution/markdown_to_pdf.py --input file.md --output file.pdf

# Batch convert all session notes
python execution/markdown_to_pdf.py --batch "docs/sessions/*.md" --output-dir pdfs/
```

---

### 🚧 Future Projects (In Development)

Add new projects here as you develop them.

## Deploying to Production

When a project is ready for production, run:

```bash
python deploy_to_skills.py --project project-name
```

This will:
1. Create new Skills workspace: `~/youtubeworkspace-skills-{project-name}/`
2. Convert directive to SKILL.md format
3. Copy tested scripts
4. Set up proper directory structure
5. Create documentation

## Best Practices

### Development
1. **Check for tools first** - Before creating scripts, check if one exists
2. **Update directives** - Document learnings as you go
3. **Test deterministically** - Execution scripts should be reliable
4. **Use cloud deliverables** - Don't rely on local files for final output
5. **Self-anneal** - Fix errors and improve the system continuously

### Before Deploying
1. **Test end-to-end** - Run the full workflow multiple times
2. **Document everything** - Directive should be complete
3. **Handle errors gracefully** - Scripts should fail safely
4. **Use production credentials** - Test with real services
5. **Verify edge cases** - Make sure all scenarios work

## Session History

This workspace maintains detailed session notes to preserve context across work sessions. Think of it like version control for knowledge - every configuration, decision, and learning is documented.

**📚 [View All Sessions](docs/sessions/README.md)**

### Recent Sessions

| Date | Topic | Quick Summary |
|------|-------|---------------|
| [2026-01-04](docs/sessions/2026-01-04-git-restructure-and-github-setup.md) | Git Restructure & GitHub Setup | Fixed git repo structure, pushed repos to GitHub organization, created session memory system |

### Why Session History?

Just like Python scripts in `execution/` preserve workflows for reuse, session notes preserve:
- System configurations and how to replicate them
- Decisions made and their rationale
- Commands and shortcuts for common tasks
- Gotchas encountered and solutions found

This prevents having to re-explain or rediscover things in future sessions.

## Support

For questions or issues, refer to CLAUDE.md for detailed operating principles.

## Related Files

- [WORKSPACES_OVERVIEW.md](../WORKSPACES_OVERVIEW.md) - DOE vs Skills comparison
- [deploy_to_skills.py](deploy_to_skills.py) - Deployment script
- [Session History](docs/sessions/README.md) - Detailed notes from all work sessions
