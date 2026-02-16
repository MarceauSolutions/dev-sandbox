# Agent Instructions

> This entire file fits in context. Detailed SOPs are in `docs/sops/`. Project-specific guidance is in each project's `CLAUDE.md`.

## Architecture

**Two-tier DOE system:**
- **Shared utilities** (`execution/*.py`): Used by 2+ projects. Strict Directive → Orchestration → Execution.
- **Project code** (`projects/[name]/src/`): Single-project logic. Flexible architecture.

**Where to put code:** `execution/` if shared (2+ projects), `projects/[name]/src/` if project-specific.

## Critical Rules (Always Enforced)

1. **Check existing tools BEFORE creating new ones** — Run: `python scripts/inventory.py search <keyword>`
2. **Never nest git repos** — `find . -name ".git" \( -type d -o -type f \)` should only show `./.git`
3. **Test before committing** — New `.py` files must at minimum pass syntax check. Pre-commit hook enforces this.
4. **DOE discipline** — Directive must exist before deploying. Never deploy untested code.
5. **Never contradict user statements** about prior work. Trust and proceed. (SOP 26)
6. **Document efforts >30 min** immediately using `docs/SOP-25-DOCUMENTATION-DECISION-FRAMEWORK.md` decision tree.
7. **Rule of Three** — If same approach fails 3 times, STOP. Research root cause before retrying.

## Commands & Shortcuts

| Slash Command | What It Does |
|---------------|-------------|
| `/deploy` | Load deployment SOP |
| `/new-project` | Project kickoff + init SOPs |
| `/publish-mcp` | MCP packaging + publishing SOPs |
| `/test` | Testing strategy |
| `/market-check` | Market viability analysis (4 agents) |
| `/inventory` | Search existing tools |
| `/photos` | Interactive photo export + resize from Photos.app |

| Quick Command | Run |
|--------------|-----|
| Search tools | `python scripts/inventory.py search <keyword>` |
| List projects | `python scripts/inventory.py list` |
| List scripts | `python scripts/inventory.py scripts` |
| Check nested repos | `find . -name ".git" \( -type d -o -type f \)` |
| Deploy | `python deploy_to_skills.py --project <name> --version X.Y.Z` |

## Communication Patterns

| William Says | Claude Does |
|-------------|------------|
| "Deploy" / "Ship it" | `/deploy` SOP |
| "New project" | `/new-project` SOP |
| "Should we build X?" | Auto-launch SOP 17 (market viability, 4 agents) |
| "How should we implement X?" | Auto-launch SOP 9 (architecture exploration, 3-4 agents) |
| "Run morning digest" | `cd projects/shared/personal-assistant && python -m src.morning_digest --preview` |
| "Check leads" | `cd projects/shared/lead-scraper && python -m src.campaign_analytics report` |
| "Continue from last session" | Check `docs/session-history.md` |
| "Roll back" | `docs/sops/sop-07-rollback.md` |
| "Publish to registry" | `/publish-mcp` |
| "Run SMS campaign" | `docs/sops/sop-18-sms-campaign.md` |
| "Download photos" / "Export photos" | `/photos` interactive flow |

## Where Things Live

| What | Location |
|------|----------|
| **SOPs (all 28)** | `docs/sops/INDEX.md` — loaded on-demand |
| **Architecture guide** | `docs/architecture-guide.md` |
| **Testing strategy** | `docs/testing-strategy.md` |
| **Deployment pipeline** | `docs/deployment.md` |
| **Repository rules** | `docs/repository-management.md` |
| **App type decision** | `docs/app-type-decision-guide.md` |
| **Credentials & API keys** | `.env` (root of dev-sandbox) |
| **Capability SOPs** | `directives/` |
| **Task procedures** | `[project]/workflows/` |
| **Session learnings** | `docs/session-history.md` |
| **Archived docs** | `docs/archive/` |

## Project Layout

```
dev-sandbox/                    # ONE git repo (parent tracks everything)
├── CLAUDE.md                   # This file (always in context)
├── .env                        # All API keys and secrets
├── scripts/                    # Inventory, company setup, maintenance
├── execution/                  # Shared utilities (76 scripts, 2+ project use)
├── directives/                 # Capability SOPs for projects
├── docs/                       # Reference documentation
│   ├── sops/                   # Individual SOP files (loaded on-demand)
│   └── archive/                # Old/superseded docs
├── projects/
│   ├── marceau-solutions/      # Our company (owner)
│   │   ├── website/            # marceausolutions.com (static HTML)
│   │   ├── pt-business/        # PT coaching business hub
│   │   ├── fitness-influencer/ # AI content platform (product code)
│   │   ├── website-builder/    # AI website generation service
│   │   ├── portfolio/          # Demo showcases for clients
│   │   └── ...
│   ├── swflorida-hvac/         # Client: SW Florida Comfort HVAC
│   │   ├── website/            # Client website (static HTML)
│   │   └── ...
│   ├── boabfit/                # Client: BoabFit (shower spray)
│   │   ├── website/            # Client website
│   │   └── research/           # Market analysis
│   ├── flames-of-passion/      # Client: Flames of Passion (candles)
│   │   └── website/            # Client website
│   ├── square-foot-shipping/   # Client: Square Foot Shipping
│   │   └── lead-gen/           # Lead generation
│   ├── shared/                 # Multi-tenant tools (2+ companies)
│   │   ├── lead-scraper/       # Lead scraping + SMS campaigns
│   │   ├── personal-assistant/ # Morning digest, calendar, routines
│   │   ├── social-media-automation/
│   │   ├── md-to-pdf/          # Markdown → PDF (MCP published)
│   │   └── ...
│   └── product-ideas/          # Exploration/research projects
└── .claude/
    ├── commands/               # Slash commands (/deploy, /test, etc.)
    ├── hooks/                  # PreToolUse hooks (tool reuse checker)
    └── settings.local.json     # Permissions + hooks config
```

## Deployment Targets

| What | Deploy To | SOP |
|------|-----------|-----|
| Skills (dev-sandbox Claude) | `~/production/[name]-prod/` | `docs/sops/sop-03-deployment.md` |
| AI Assistants (standalone) | `~/ai-assistants/[name]/` | `docs/sops/sop-31-ai-assistant.md` |
| MCP Packages | PyPI + MCP Registry | `docs/sops/sop-11-mcp-structure.md` through `sop-14` |
| Client Websites | GitHub Pages (auto via Actions) | `.github/workflows/deploy-websites.yml` |

## Three-Agent Model

| Agent | Where | Best For |
|-------|-------|----------|
| **Claude Code** | Mac terminal | Interactive work, publishing, debugging |
| **Clawdbot** | EC2 24/7 (Telegram) | Quick tasks, research, complexity 0-6 |
| **Ralph** | EC2 (PRD-driven) | Complex builds, complexity 7-10 |

See `docs/SOP-29-THREE-AGENT-COLLABORATION.md` for routing logic.

## Session Start Checklist

1. This file loads automatically (always in context)
2. Check which project we're working on — read its `CLAUDE.md` if it has one
3. Check `docs/session-history.md` if continuing previous work
4. Check `[project]/workflows/` for existing procedures

## Autonomous Agent Triggers

Launch agents WITHOUT explicit user request when:
- **New product idea mentioned** → SOP 17 (4 market viability agents)
- **Multiple implementation approaches** → SOP 9 (architecture exploration)
- **Complex feature done + manual test passed** → SOP 2 (multi-agent testing)
- **4+ independent components** → SOP 10 (parallel development)

## Principle

Be pragmatic. Be reliable. Self-anneal. Use Opus 4.6 for all work.
