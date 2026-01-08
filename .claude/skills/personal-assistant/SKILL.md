---
name: personal-assistant
description: William's Personal AI Assistant - unified access to all dev-sandbox capabilities including interview prep, fitness operations, Amazon seller tools, and more. The master skill that routes requests to specialized project skills.
version: 1.0.0-dev
trigger_phrases:
  - help me with
  - I need to
  - can you
  - personal assistant
  - what can you do
model: opus
allowed_tools:
  - Bash(python:*)
  - Bash(python3:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - mcp:google-sheets
  - mcp:google-drive
  - mcp:amazon-sp-api
  - mcp:brave-search
  - mcp:filesystem
mcp_servers:
  - google-sheets     # Store data across all projects
  - google-drive      # Document storage and retrieval
  - amazon-sp-api     # Amazon seller operations
  - brave-search      # Web research for any project
  - filesystem        # File system operations
---

# William's Personal AI Assistant

## Overview

Master skill that provides unified access to all dev-sandbox project capabilities. Acts as an intelligent router that identifies intent and delegates to specialized skills.

## MCP Server Layer

This assistant has access to MCP (Model Context Protocol) servers, but **use them selectively** based on cost-benefit:

### When to Use MCP (Token-Intensive)
- External-facing AI assistants (shared systems)
- Operations requiring automatic rate limiting (Amazon SP-API)
- Standardized integrations for deployed products

### When to Prefer Python Scripts (Token-Efficient)
- Personal/internal tools (like this assistant)
- High-frequency operations
- One-off tasks
- When custom logic is needed

| MCP Server | Use For Personal Assistant? | Reason |
|------------|----------------------------|--------|
| `amazon-sp-api` | YES | Rate limiting worth the overhead |
| `google-sheets` | EVALUATE | Use scripts for simple ops, MCP for complex |
| `google-drive` | EVALUATE | Use scripts for simple ops |
| `brave-search` | NO | Claude's built-in search is sufficient |
| `filesystem` | NO | Native tools are more efficient |

**MCP Config**: `.claude/mcp-servers/mcp-config.json`

**Default behavior for Personal Assistant:** Prefer Python scripts in `execution/` unless MCP provides significant benefit (rate limiting, complex auth, etc.).

## Capabilities Overview

| Domain | Skills Available | MCP Servers | Trigger Examples |
|--------|------------------|-------------|------------------|
| **Interview Prep** | Research, presentations, mock interviews, quick outputs | google-sheets, google-drive, brave-search | "Prepare for Google interview", "Practice interview" |
| **Fitness Influencer** | Video editing, email, analytics, graphics | google-sheets, google-drive | "Create video ad", "Check fitness emails" |
| **Amazon Seller** | Inventory, fees, reviews | amazon-sp-api | "Check Amazon inventory", "Calculate FBA fees" |
| **Naples Weather** | Weather reports, PDF generation | filesystem | "Generate Naples weather report" |
| **Dev Operations** | Deployment, versioning, documentation | filesystem | "Deploy to skills", "Check project status" |

## How to Use

Just describe what you need. I'll route to the appropriate skill:

### Interview Preparation
```
"Help me prepare for my [Company] [Role] interview"
"Practice interview with me"
"Give me a cheat sheet for [Company]"
"Create interview presentation"
"Mock interview for Google PM"
```
→ Routes to: `.claude/skills/interview-prep/SKILL.md`

### Fitness Influencer Operations
```
"Create a video ad with [prompt]"
"Add jump cuts to my video"
"Check my fitness emails"
"Generate revenue report"
"Create educational graphic"
```
→ Routes to: `.claude/skills/fitness-influencer-operations/SKILL.md`

### Amazon Seller Operations
```
"Check my Amazon inventory"
"Calculate FBA fees for [product]"
"Show me review summary"
"Analyze Amazon costs"
```
→ Routes to: `.claude/skills/amazon-seller-operations/SKILL.md`

### Naples Weather
```
"Generate Naples weather report"
"Create weekly forecast"
"Weather report for Naples"
```
→ Routes to: `.claude/skills/naples-weather-report/SKILL.md`

### Dev Operations
```
"Deploy [project] to skills"
"Check deployment status"
"List all projects"
"Sync scripts to execution"
"Update session history"
```
→ Uses: `deploy_to_skills.py`, local docs

## Request Routing Logic

```
User Request → Parse Intent
│
├─ Interview-related keywords?
│   └─ "interview", "company", "role", "mock", "cheat sheet"
│   └─ → Read .claude/skills/interview-prep/SKILL.md
│   └─ → Execute interview-prep workflow
│
├─ Fitness-related keywords?
│   └─ "video", "fitness", "workout", "email", "revenue"
│   └─ → Read .claude/skills/fitness-influencer-operations/SKILL.md
│   └─ → Execute fitness workflow
│
├─ Amazon-related keywords?
│   └─ "amazon", "inventory", "FBA", "seller", "fees"
│   └─ → Read .claude/skills/amazon-seller-operations/SKILL.md
│   └─ → Execute amazon workflow
│
├─ Weather-related keywords?
│   └─ "weather", "naples", "forecast", "report"
│   └─ → Read .claude/skills/naples-weather-report/SKILL.md
│   └─ → Execute weather workflow
│
├─ Dev/deployment keywords?
│   └─ "deploy", "status", "version", "sync"
│   └─ → Use deploy_to_skills.py
│
└─ Unclear?
    └─ → Ask for clarification
    └─ → Show available capabilities
```

## Available Skills (Auto-Updated)

### Interview Prep (v1.2.0-dev)
- **Location**: `.claude/skills/interview-prep/SKILL.md`
- **Capabilities**:
  - AI-powered company/role research
  - PowerPoint presentation generation
  - Mock interview practice (behavioral, technical, case)
  - Quick outputs (cheat sheet, talking points, flashcards, checklist)
  - Live presentation editing

### Fitness Influencer (v1.0.0)
- **Location**: `.claude/skills/fitness-influencer-operations/SKILL.md`
- **Capabilities**:
  - Video creation and editing
  - Jump cut automation
  - AI image generation
  - Email monitoring
  - Revenue analytics
  - Calendar reminders

### Amazon Seller (v1.0.0)
- **Location**: `.claude/skills/amazon-seller-operations/SKILL.md`
- **Capabilities**:
  - Inventory management
  - FBA fee calculations
  - Review monitoring
  - Cost optimization

### Naples Weather (v1.0.0)
- **Location**: `.claude/skills/naples-weather-report/SKILL.md`
- **Capabilities**:
  - Weekly weather report generation
  - PDF output
  - Weather data fetching

## Quick Commands

### Check What's Available
```bash
# List all projects and versions
python deploy_to_skills.py --list

# Check specific project status
python deploy_to_skills.py --status interview-prep
```

### Access Project Documentation
```bash
# Read a skill file
cat .claude/skills/interview-prep/SKILL.md

# Read a directive
cat directives/interview_prep.md

# Check session history
cat docs/session-history.md
```

## Key Locations

| Need | Location |
|------|----------|
| How we work | `CLAUDE.md` |
| Project skills | `.claude/skills/` |
| Capability SOPs | `directives/` |
| Execution scripts | `execution/` |
| Session learnings | `docs/session-history.md` |
| Prompting guide | `docs/prompting-guide.md` |
| Deployment | `deploy_to_skills.py` |

## Session Management

This assistant maintains context across our conversations:
- **Session history**: `docs/session-history.md` (living document)
- **Prompting patterns**: `docs/prompting-guide.md` (living document)
- **Communication patterns**: `CLAUDE.md` (living document)

When we learn new patterns or preferences, they're documented for consistency.

## Development Workflow

When working on any project:
1. Skills are developed in project directories
2. Skills auto-deploy to `.claude/skills/` via `deploy_to_skills.py`
3. This master skill file routes to the appropriate project skill
4. Learnings are captured in living documents

## Version

- **Personal Assistant**: 1.0.0-dev
- **Last Updated**: 2026-01-08

## Related Files

- Project README: `projects/personal-assistant/README.md`
- Operating instructions: `CLAUDE.md`
- All project skills: `.claude/skills/*/SKILL.md`
