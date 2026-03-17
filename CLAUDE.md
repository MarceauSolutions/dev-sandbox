# Agent Instructions

> This entire file fits in context. Detailed SOPs are in `docs/sops/`. Project-specific guidance is in each project's `CLAUDE.md`.

## Architecture

**Two-tier DOE system:**
- **Shared utilities** (`execution/*.py`): Used by 2+ projects. Strict Directive → Orchestration → Execution.
- **Project code** (`projects/[name]/src/`): Single-project logic. Flexible architecture.

**Where to put code:** `execution/` if shared (2+ projects), `projects/[name]/src/` if project-specific.

## Interface-First Rules (Non-Negotiable)

> Every tool must be usable by William WITHOUT opening VS Code. If it isn't, it isn't finished.

- **Automations → n8n** by default. No new CLI-only automation scripts. William already knows n8n.
- **Dashboards/content tools → standalone web app** at a fixed localhost URL with a direct launch script in `scripts/`
- **Reports/guides → branded PDF**, auto-opened. Never a markdown file.
- **Alerts → SMS or email** via Twilio/SMTP. Never "run this command to check".
- **Before writing code**, confirm: *"How will William access this without me?"*
- **Direct launch scripts** required for every web app: `scripts/[name].sh` — one command, browser opens.
- **Nothing deleted without explicit approval.** Move assets, never delete them.
- **Every generated file documented** in that project's CLAUDE.md the moment it's created.

## Critical Rules (Always Enforced)

1. **Check existing tools BEFORE creating new ones** — `python scripts/inventory.py search <keyword>`. Hook: `check-existing-tools.sh`
2. **Never nest git repos** — `find . -name ".git" \( -type d -o -type f \)` should only show `./.git`
3. **Test before committing** — New `.py` files must pass syntax check. Pre-commit hook enforces.
4. **DOE discipline** — Directive must exist before deploying. Never deploy untested code.
5. **Never contradict user statements** about prior work. Trust and proceed. (SOP 26)
6. **Document efforts >30 min** — `docs/sops/sop-25-documentation-decision-framework.md`
7. **Rule of Three** — Same approach fails 3x? STOP. Research root cause.
8. **Push after commit** — Every `git commit` MUST be followed by `git push origin main` in the same session. The PostToolUse hook auto-syncs EC2 after push. Unpushed commits = Clawdbot blind spot.
9. **Verify sync on session start** — Run `git log --oneline origin/main..HEAD` at start of any session. If >0 unpushed commits exist, push before doing anything else.

## Execution Discipline (Hook-Enforced Where Possible)

> These exist because they were violated repeatedly. Hooks BLOCK where they can. The rest is self-discipline.

- **E1 Just do it** — Never ask "want me to?" for obvious next steps. DO IT.
- **E2 Stay on track** — Never pursue a direction William said no to.
- **E3 Failures compound** — Incomplete deliverables, skipped steps = zero tolerance.
- **E4 Verify before spending** — Check existing capabilities before paid services. Hook: `api-cost-guard.sh`
- **E5 Use APIs, never delegate** — Check `.env`, `execution/`, MCP tools BEFORE telling William to do anything manually.
- **E6 Build foundations** — "Will this need redoing later?" If yes, do it right now.
- **E7 Complete the loop** — Send SMS/email → ALWAYS run inbox monitor after. Hook: `complete-the-loop-guard.sh`
- **E8 Stay in the stack** — No ngrok, Netlify, FormSubmit, random services. Hook: `stack-guard.sh` (BLOCKING)
- **E9 Pre-flight mandatory** — SOP 33 before every task. Search inventory, check service status, verify standards.
- **E11 Spec written ≠ deployed (MANDATORY)** — A specification document is NOT a deliverable. Writing a spec, generating a PDF, or creating a JSON template means NOTHING until the system is running on its target platform and verified with an end-to-end test. The pipeline is: Research → Design → Build → **Deploy → Test on target → Verify user can interact** → THEN mark complete. Never tell William something "is set up" when it's only been spec'd. This rule exists because the entire accountability system was "built" as markdown files but never deployed to EC2 or n8n — William woke up expecting it to work and it didn't.
- **E10 Best-path evaluation (MANDATORY)** — Never default to the easiest implementation. Before building ANYTHING, answer these 5 questions and document the reasoning:
  1. **Who is the end user and how will they interact with this?** (William on mobile? A client? An automation?) — The answer determines the interface. CLI is almost never the right answer for William.
  2. **What existing infrastructure is the natural fit?** (Clawdbot/Telegram for conversational, n8n for automation, FitAI for fitness features, branded PDF for documents, SMS for alerts) — Build ON existing systems, not beside them.
  3. **How does this need to scale?** (1 user → 10 → 100? One-time → daily → real-time?) — A Google Sheet works for 1 user tracking 1 thing. It breaks at 10 metrics updated daily. Choose the architecture that fits the 6-month version, not just today.
  4. **What are the real constraints?** (Energy levels, dystonia, treatment days, Naples FL location, zero clients currently) — Every design decision must account for worst-case-day usability.
  5. **Is there a consolidation opportunity?** (Can this be a new capability in an existing tool rather than a new tool?) — Adding a feature to Clawdbot > building a new bot. Adding a template to branded_pdf_engine > building a new PDF generator. Extending FitAI > building a separate fitness app.
  > **Origin**: This rule exists because Claude repeatedly chose the fastest-to-code path (terminal scripts, markdown files, manual spreadsheets) over the right-for-William path (Telegram bots, automated SMS, web dashboards). The fastest path to build is rarely the best path to use. Evaluate first, build second.

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
| **LaunchPad dashboard** | `./scripts/launchpad.sh [product]` |
| **Daily standup** | `./scripts/daily_standup.sh` |
| **System health** | `python scripts/health_check.py` |
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
| "Run morning digest" | `python -m projects.shared.personal-assistant.src.morning_digest --preview` |
| "Check leads" | `python -m projects.shared.lead-scraper.src.campaign_analytics report` |
| "Continue from last session" | Check `docs/session-history.md` |
| "Roll back" | `docs/sops/sop-07-rollback.md` |
| "Publish to registry" | `/publish-mcp` |
| "Run SMS campaign" | `docs/sops/sop-18-sms-campaign.md` |
| "Download photos" / "Export photos" | `/photos` interactive flow |
| "What tool for X?" / "Should we use Y?" | Tool Selection Framework in `docs/service-standards.md` |
| "New web dev client" | `projects/marceau-solutions/digital/tools/web-dev/workflows/client-onboarding.md` |
| "Deploy {client} website" | `./scripts/deploy_website.sh {client}` |
| "PT client needs a website" | POST to `/webhook/cross-referral` (cross-business handoff) |

## Where Things Live

| What | Location |
|------|----------|
| **SOPs (all 33)** | `docs/sops/INDEX.md` — loaded on-demand |
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
| **Unified business ops** | `docs/UNIFIED-BUSINESS-OPS.md` |
| **System state (live)** | `docs/SYSTEM-STATE.md` |
| **PT coaching hub** | `projects/marceau-solutions/fitness/clients/pt-business/CLAUDE.md` |
| **Web dev hub** | `projects/marceau-solutions/digital/tools/web-dev/CLAUDE.md` |
| **Tower index** | `projects/marceau-solutions/CLAUDE.md` |
| **Tower structure** | `projects/marceau-solutions/{fitness,digital,media,labs}/` |

## Project Layout

```
dev-sandbox/                    # ONE git repo (parent tracks everything)
├── CLAUDE.md                   # This file (always in context)
├── .env                        # All API keys and secrets
├── scripts/                    # Inventory, company setup, maintenance
├── execution/                  # Shared utilities (106 scripts, 2+ project use)
├── directives/                 # Capability SOPs for projects
├── docs/                       # Reference documentation
│   ├── sops/                   # Individual SOP files (loaded on-demand)
│   └── archive/                # Old/superseded docs
├── projects/
│   ├── marceau-solutions/      # Our company — organized by tower
│   │   ├── CLAUDE.md           #   Tower index + placement rules
│   │   ├── fitness/            # TOWER: Fitness & Coaching
│   │   │   ├── clients/
│   │   │   │   ├── boabfit/    #     Julia's fitness influencer brand
│   │   │   │   └── pt-business/ #    William's 1:1 coaching ($197/mo)
│   │   │   └── tools/
│   │   │       ├── fitness-influencer/ # FitAI platform
│   │   │       ├── fitness-influencer-mcp/
│   │   │       └── trainerize-mcp/
│   │   ├── digital/            # TOWER: Digital Services
│   │   │   ├── clients/
│   │   │   │   ├── swflorida-hvac/
│   │   │   │   ├── flames-of-passion/
│   │   │   │   └── square-foot-shipping/
│   │   │   ├── tools/
│   │   │   │   ├── website-builder/ # AI website generator
│   │   │   │   └── web-dev/        # Web dev workflows/ops
│   │   │   └── website/        #   marceausolutions.com
│   │   ├── media/              # TOWER: Content & Media
│   │   │   └── tools/
│   │   │       ├── instagram-creator/
│   │   │       ├── youtube-creator/
│   │   │       └── tiktok-creator/
│   │   └── labs/               # TOWER: R&D & New Ventures
│   │       ├── dumbphone-lock/ #   iOS focus app
│   │       ├── vuori-lead-magnet/
│   │       ├── amazon-seller/
│   │       ├── mikos-lab/
│   │       └── legal-case-manager/
│   ├── shared/                 # Multi-tenant tools (2+ companies)
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
| Client Websites | GitHub Pages | `./scripts/deploy_website.sh <client>` |

## Three-Agent Model

| Agent | Where | Best For |
|-------|-------|----------|
| **Claude Code** | Mac terminal | Interactive work, publishing, debugging |
| **Clawdbot** | EC2 24/7 (Telegram) | Quick tasks, research, complexity 0-6 |
| **Ralph** | EC2 (PRD-driven) | Complex builds, complexity 7-10 |

See `docs/sops/sop-29-three-agent-collaboration.md` for routing logic.

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
