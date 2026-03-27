# Modular Multi-Tower Architecture Guide

> This document defines the modular multi-tower architecture for laptop-based company operations. Read this at the start of every session.

## Overview

The system operates as a **modular multi-tower company** where each tower represents a specialized business unit. Towers operate independently but can communicate through standardized protocols. The entire system runs on a laptop with lightweight, version-controlled, and observable development practices.

## Tower Structure

### Core Towers

| Tower | Domain | Location | Lead |
|-------|--------|----------|------|
| **ai-systems** | AI infrastructure and tooling | `projects/ai-systems/` | Claude/Cline |
| **amazon-seller** | Amazon marketplace operations | `projects/amazon-seller/` | Claude/Cline |
| **fitness-influencer** | Fitness content and influencer operations | `projects/fitness-influencer/` | Claude/Cline |
| **lead-generation** | Lead scraping and outreach | `projects/lead-generation/` | Claude/Cline |
| **mcp-services** | Model Context Protocol servers | `projects/mcp-services/` | Claude/Cline |
| **personal-assistant** | Personal automation and scheduling | `projects/personal-assistant/` | Claude/Cline |

### Tower Independence

Each tower maintains:
- **Own codebase**: `projects/[tower-name]/src/`
- **Own workflows**: `projects/[tower-name]/workflows/`
- **Own version control**: Tracked in dev-sandbox git
- **Own deployment**: Separate production repos when needed

## Separation of Concerns

### Tower Responsibilities

**ai-systems**: Core AI infrastructure, shared utilities, model integrations
**amazon-seller**: SP-API integration, inventory management, seller operations
**fitness-influencer**: Video editing automation, content creation, social media
**lead-generation**: Lead scraping, SMS campaigns, follow-up sequences
**mcp-services**: MCP server development, PyPI publishing, registry management
**personal-assistant**: Email digests, calendar management, routine automation

### Shared Resources

**Location**: `execution/` and `projects/shared/`
- Cross-tower utilities (gmail_monitor.py, twilio_sms.py)
- Multi-tenant tools used by 2+ towers
- Infrastructure components

**Location**: `docs/`
- Architecture documentation
- Shared workflows and SOPs
- System-wide standards

## Communication Protocols

### Inter-Tower Communication

1. **Direct API Calls**: Towers can import and use functions from other towers
2. **Shared Data**: Common data formats in `data/` directory
3. **Event System**: Pub/sub pattern for cross-tower notifications
4. **MCP Protocol**: Standardized interface for AI agent interactions

### Handoff Procedures

**When Tower A needs Tower B's capability**:
1. Tower A identifies requirement
2. Check if Tower B has existing solution
3. If yes: Import and use directly
4. If no: Tower B develops capability, then Tower A integrates

**Example**: Fitness tower needs lead data → Import from lead-generation tower

### Standardized Interfaces

All towers expose capabilities through:
- **Python modules**: `from projects.[tower].src import [capability]`
- **CLI commands**: `python -m projects.[tower].src.[script]`
- **MCP servers**: For AI agent integration

## Agent Operating Rules

### Core Operating Principles

**Always check the Focus Chain markdown as the single source of truth for progress**

**When user says "work on [tower]", switch context and work inside `projects/[tower]/`**

**Use the simplified CLAUDE.md as the primary architecture guide at the start of every session**

### Research-First Execution Policy (MANDATORY)

**Before executing ANY task, Claude MUST:**
1. **Check data first** — Read pipeline.db, outcome tracking, and existing code before recommending an approach
2. **Do NOT execute William's first instinct** — If William says "do X", validate X against data before proceeding. Ask "have you considered Y?" if data suggests a better path
3. **Present alternatives with tradeoffs** — Never present only one option. Show 2-3 approaches with pros/cons
4. **Verify before declaring complete** — Test from the user's perspective (not just syntax checks). If it touches EC2, SSH and verify. If it touches n8n, check the n8n database.
5. **Never give false completion signals** — If something isn't working end-to-end, say so. "Partially done" is honest. "Complete" when it's not is a trust violation.

**Current goals** (read `projects/personal-assistant/data/goals.json` for details):
- Short-term: Land first AI client by April 6
- Medium-term: 3 paying clients by May 15
- Long-term: Replace day job income with Marceau Solutions
- Post-April 6: Run business evenings/weekends while at Collier County 7am-3pm

**Update goals**: `cd projects/personal-assistant && python3 -m src.goal_manager show`

### Primary Agent Role

**Cline/Grok serves as the central orchestrator** for all tower operations:

- **Reads directives**: Understands tower requirements from `directives/[tower].md`
- **Orchestrates execution**: Calls appropriate scripts and utilities
- **Handles communication**: Manages inter-tower handoffs
- **Maintains architecture**: Ensures separation of concerns
- **Self-anneals**: Updates documentation and improves processes

### Agent Communication Patterns

| User Says | Agent Does |
|-----------|------------|
| "Work on [tower]" | Switch context to that tower's directory |
| "Deploy [tower]" | Run deployment pipeline for that tower |
| "Integrate [tower A] with [tower B]" | Set up communication protocol between towers |
| "Add capability to [tower]" | Create new module in tower's src/ |
| "Cross-tower [task]" | Identify which towers involved, orchestrate handoff |

### Agent Best Practices

1. **Tower-first thinking**: Always consider which tower owns the capability
2. **Minimize coupling**: Keep towers independent, use protocols for communication
3. **Document handoffs**: Update workflows when towers interact
4. **Version control**: Commit changes to dev-sandbox after tower work
5. **Observable operations**: Log actions, provide status updates

## Version Control & Deployment

### Single Development Repository

**All tower development occurs in the single `dev-sandbox/` git repository**:
- No nested git repositories within towers
- All changes tracked in one place for easy coordination
- Weekly verification ensures no accidental nested repos

### Optional Production Deployment

**Production deployments create separate repositories when needed**:
- `~/production/[tower]-prod/` - Standalone production environment
- `~/websites/[domain]/` - Web deployments
- `~/active-projects/[repo]/` - GitHub-published projects

**Deployment is optional**: Towers can remain in development-only state indefinitely

## Laptop-Based Development Best Practices

### Lightweight Architecture

**No heavy infrastructure required**:
- All code runs locally on laptop
- No cloud dependencies for development
- Production deployments are optional and separate
- Version control handles all coordination

### Version Control Strategy

**Single source of truth**: `dev-sandbox/` git repository
- All towers tracked in one repo
- No nested git repositories
- Weekly verification: `find . -name ".git" -type d` shows only `./.git`

**Deployment creates separate repos**:
- Production: `~/production/[tower]-prod/`
- Websites: `~/websites/[domain]/`
- GitHub projects: `~/active-projects/[repo]/`

### Observable Operations

**All operations must be**:
- **Logged**: Actions recorded for review
- **Reproducible**: Commands documented and repeatable
- **Recoverable**: Changes can be rolled back
- **Auditable**: History shows what happened and why

### Development Workflow

```
1. Read tower directive: directives/[tower].md
2. Work in tower directory: projects/[tower]/
3. Use shared utilities: execution/*.py when applicable
4. Test locally on laptop
5. Commit to dev-sandbox
6. Deploy to production (optional)
```

### File Organization Standards

```
dev-sandbox/
├── projects/
│   ├── [tower-name]/          # Tower-specific code
│   │   ├── src/               # Python modules
│   │   ├── workflows/         # Task procedures
│   │   ├── VERSION            # Current version
│   │   └── README.md          # Tower documentation
│   └── shared/                # Multi-tower utilities
├── execution/                 # Cross-tower shared utilities
├── docs/                      # System documentation
├── directives/                # Tower capability definitions
└── data/                      # Shared data files
```

## Tower Development Lifecycle

### 1. Tower Initialization
```bash
# Create new tower structure
mkdir -p projects/[new-tower]/{src,workflows}
echo "1.0.0-dev" > projects/[new-tower]/VERSION
```

### 2. Define Capabilities
Create `directives/[new-tower].md` with:
- What the tower does
- Key capabilities
- Integration points with other towers

### 3. Implement Features
- Code in `projects/[new-tower]/src/`
- Workflows in `projects/[new-tower]/workflows/`
- Use shared utilities from `execution/` when possible

### 4. Test Locally
- Manual testing first
- Multi-agent testing for complex features
- All testing happens on laptop

### 5. Deploy (Optional)
```bash
python deploy_to_skills.py --project [new-tower] --version 1.0.0
```
Creates `~/production/[new-tower]-prod/` with separate git repo

### 6. Integrate with Other Towers
- Expose capabilities through standardized interfaces
- Document handoff procedures
- Update communication protocols

## Key Commands

### Tower Management
```bash
# List all towers
ls projects/

# Work on specific tower
cd projects/[tower-name]

# Check tower status
cat projects/[tower-name]/VERSION

# Deploy tower
python deploy_to_skills.py --project [tower-name] --version X.Y.Z
```

### Inter-Tower Operations
```bash
# Use capability from another tower
python -c "from projects.[tower].src import [capability]"

# Run cross-tower workflow
python -m projects.[tower-a].workflows.[workflow] --integrate [tower-b]
```

### System Maintenance
```bash
# Verify no nested repos
find . -name ".git" -type d

# Commit all tower changes
git add projects/ && git commit -m "feat: Update [towers]"

# Check shared utilities
ls execution/
```

## Operating Principles

1. **Tower Independence**: Each tower owns its domain and can operate standalone
2. **Protocol-Based Communication**: Towers communicate through defined interfaces, not direct coupling
3. **Agent-Centric Orchestration**: Cline/Grok coordinates all operations and maintains architecture
4. **Laptop-First Development**: All development happens locally, production is optional
5. **Observable by Default**: Every operation is logged, documented, and recoverable
6. **Self-Annealing System**: Documentation and processes improve through use

## Quick Start

1. **Choose tower**: `cd projects/[tower-name]`
2. **Read directive**: `cat ../../directives/[tower-name].md`
3. **Check workflows**: `ls workflows/`
4. **Run capability**: `python -m src.[script]`
5. **Commit changes**: `git add . && git commit -m "feat: [description]"`

---

**Architecture**: Modular towers with standardized communication
**Agent**: Cline/Grok as central orchestrator
**Platform**: Laptop-based, version-controlled, observable
**Principle**: Independent towers, coordinated through protocols.