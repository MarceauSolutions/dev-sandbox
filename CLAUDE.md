# Agent Instructions

> Rules live in `rules/`. SOPs in `docs/sops/`. Project context in each project's `CLAUDE.md`.

## SESSION START — 6 Steps (no exceptions)

1. Read `docs/SYSTEM-STATE.md` — live infra state, DO NOT REDO list
2. Read `docs/ARCHITECTURE-DECISIONS.md` — cross-agent conventions
3. Check `HANDOFF.md` — pending tasks between agents
4. Check which project — read its `CLAUDE.md` if it has one
5. Check `docs/session-history.md` if continuing previous work
6. Run `git log --oneline origin/main..HEAD` — push any unpushed commits before starting

## STOP — Read Before Acting

| Situation | Command — no exceptions |
|-----------|------------------------|
| Need a PDF | `python execution/branded_pdf_engine.py --list-templates` then `--template generic_document` with key `content_markdown` |
| Need to send email | Use `execution/send_onboarding_email.py` SMTP pattern — credentials in `.env` |
| Need to send SMS | Use `execution/twilio_sms.py` — Twilio +1 (855) 239-9364 |
| Need API credit info | `./scripts/api-key-manager.sh` → http://127.0.0.1:8793 |
| About to write a .py file | `python scripts/inventory.py search <keyword>` first |
| About to call a paid API | Check `.env` for key + check api-key-manager for balance |
| Any routing / interface / agent / output decision | Load `rules/routing/ROUTING.md` |

## RULES SYSTEM

All rules live in `rules/`. Load on demand — don't pre-load everything.

| Need | Load |
|------|------|
| Any routing, interface, agent, or output decision | `rules/routing/ROUTING.md` |
| Registry of all rules + hooks | `rules/INDEX.md` |
| E-rule reasoning (E01–E12) | `rules/behavioral/E[N]-[name].md` |
| Exact tool commands | `rules/tools/[tool-name].md` |
| Interface selection detail | `rules/routing/interface-selection.md` |
| PDF template selection | `rules/routing/pdf-template-selection.md` |
| Agent routing detail | `rules/routing/agent-routing.md` |
| Code placement detail | `rules/routing/code-placement.md` |

## SLASH COMMANDS

| Command | What It Does |
|---------|-------------|
| `/deploy` | Load deployment SOP |
| `/new-project` | Project kickoff + init SOPs |
| `/publish-mcp` | MCP packaging + publishing SOPs |
| `/test` | Testing strategy |
| `/market-check` | Market viability (4 agents) |
| `/inventory` | Search existing tools |
| `/photos` | Interactive photo export from Photos.app |
| `/session-summary` | Capture session work to session-history.md |
| `/context` | Pre-load relevant files for a project |
| `/memory-check` | Audit and consolidate memory files |

## QUICK COMMANDS

| Command | Run |
|---------|-----|
| Marceau Hub | http://127.0.0.1:8760 (auto-starts on login) |
| LaunchPad | `./scripts/launchpad.sh [product]` |
| Daily standup | `./scripts/daily_standup.sh` |
| System health | `python scripts/health_check.py` |
| Search tools | `python scripts/inventory.py search <keyword>` |
| Dystonia digest | `./scripts/dystonia-digest.sh` → http://127.0.0.1:8792 |
| Deploy | `python deploy_to_skills.py --project <name> --version X.Y.Z` |

## WHERE THINGS LIVE

| What | Location |
|------|----------|
| **Live system state** | `docs/SYSTEM-STATE.md` |
| **Architecture decisions** | `docs/ARCHITECTURE-DECISIONS.md` |
| **Agent handoffs** | `HANDOFF.md` |
| **Session history** | `docs/session-history.md` |
| **All SOPs (33)** | `docs/sops/INDEX.md` |
| **API keys** | `.env` (root) |
| **Shared scripts** | `execution/` (106 scripts) |
| **Tower index** | `projects/marceau-solutions/CLAUDE.md` |
| **PT coaching hub** | `projects/marceau-solutions/fitness/clients/pt-business/CLAUDE.md` |
| **Web dev hub** | `projects/marceau-solutions/digital/tools/web-dev/CLAUDE.md` |
| **n8n workflows** | `projects/shared/n8n-workflows/backups/` |
| **Service standards** | `docs/service-standards.md` |

## PROJECT LAYOUT

```
dev-sandbox/                    # ONE git repo
├── CLAUDE.md                   # This file
├── rules/                      # All rules (behavioral/, routing/, tools/)
├── .env                        # All API keys and secrets
├── scripts/                    # Inventory, maintenance scripts
├── execution/                  # Shared utilities (106 scripts, 2+ project use)
├── directives/                 # Capability SOPs
├── docs/                       # Reference docs, SOPs, session history
├── projects/
│   ├── marceau-solutions/      # Company — organized by tower
│   │   ├── fitness/            # Fitness & Coaching (FitAI, PT clients)
│   │   ├── digital/            # Digital Services (web clients, website)
│   │   ├── media/              # Content & Media (IG, YouTube, TikTok)
│   │   └── labs/               # R&D & New Ventures
│   ├── shared/                 # Multi-tenant tools
│   └── product-ideas/          # Exploration
└── .claude/
    ├── commands/               # Slash commands
    ├── hooks/                  # PreToolUse hooks
    └── settings.local.json
```

## PRINCIPLE

Be pragmatic. Be reliable. Self-anneal. Use Opus 4.6 for all work. Every tool must be usable by William without opening VS Code — if it isn't, it isn't finished.
