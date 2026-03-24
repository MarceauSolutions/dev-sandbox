# {{PROJECT_NAME}} — AgentOS Configuration

> {{PROJECT_DESCRIPTION}}

---

## Setup Detection

If the file `.agent-os-configured` does not exist in this directory, run the onboarding flow before doing anything else. See `docs/setup-guide.md`.

---

## Architecture

**Two-tier system:**
- **Shared utilities** (`execution/`): Used by 2+ projects. Reusable logic lives here.
- **Project code** (`projects/[name]/src/`): Single-project logic. Flexible structure.

**Where to put code:** If it serves 2+ projects, put it in `execution/`. If it's project-specific, put it in `projects/[name]/src/`.

## Interface-First Rules (Non-Negotiable)

> Every tool must be usable by {{USER_NAME}} WITHOUT opening VS Code. If it isn't, it isn't finished.

- **Automations** → {{AUTOMATION_PLATFORM}} by default. No CLI-only automation scripts.
- **Dashboards / interactive tools** → standalone web app at a fixed localhost URL with a launch script in `scripts/`.
- **Reports / guides** → PDF, auto-opened. Never a raw markdown file.
- **Alerts** → {{ALERT_CHANNEL}} (SMS, email, Slack, etc.). Never "run this command to check."
- **Before writing code**, confirm: *"How will {{USER_NAME}} access this without me?"*
- **Direct launch scripts** required for every web app: `scripts/[name].sh` — one command, browser opens.
- **Nothing deleted without explicit approval.** Move assets, never delete them.
- **Every generated file documented** in that project's CLAUDE.md the moment it's created.

## Execution Discipline Rules

> Each rule has an origin story. These exist because they were violated repeatedly.

- **E1 Just do it** — Never ask "want me to?" for obvious next steps. DO IT.
- **E2 Stay on track** — Never pursue a direction {{USER_NAME}} said no to.
- **E3 Failures compound** — Incomplete deliverables, skipped steps = zero tolerance.
- **E4 Verify before spending** — Check existing capabilities before paid services.
- **E5 Use APIs, never delegate** — Check `.env`, `execution/`, MCP tools BEFORE telling {{USER_NAME}} to do anything manually.
- **E6 Build foundations** — "Will this need redoing later?" If yes, do it right now.
- **E7 Complete the loop** — Send SMS/email → ALWAYS verify delivery after.
- **E8 Stay in the stack** — No unapproved services. Use the stack defined during setup.
- **E9 Pre-flight mandatory** — Search inventory, check service status before every task.
- **E10 Best-path evaluation (MANDATORY)** — Never default to the easiest implementation. Before building ANYTHING, answer these 5 questions:
  1. **Who is the end user and how will they interact?** — The answer determines the interface.
  2. **What existing infrastructure is the natural fit?** — Build ON existing systems, not beside them.
  3. **How does this need to scale?** — Choose architecture that fits the 6-month version, not just today.
  4. **What are the real constraints?** — Every design decision must account for worst-case usability.
  5. **Is there a consolidation opportunity?** — Adding a feature to an existing tool > building a new one.
  > **Origin**: AI repeatedly chose the fastest-to-code path over the right-for-user path. The fastest path to build is rarely the best path to use.
- **E11 Spec written ≠ deployed (MANDATORY)** — A specification is NOT a deliverable. Pipeline: Research → Design → Build → **Deploy → Test → Verify user can interact** → THEN mark complete.
  > **Origin**: An entire system was "built" as markdown files but never deployed. The user expected it to work — it didn't.
- **E12 Code to production pipeline (MANDATORY)** — A working local script is NOT a shipped product. **CLI is NEVER the final interface for user-facing tools.** Full pipeline:
  1. Interface decision FIRST — "How will {{USER_NAME}} use this?"
  2. Build core logic
  3. Wire to chosen interface
  4. Deploy to production
  5. Verify access — "Can {{USER_NAME}} use this right now, without me?" If no, keep building.
  6. Launch script in `scripts/`
  7. Documentation updated
  > **Origin**: Tools kept getting built as CLI scripts and declared "done."

## Critical Rules (Always Enforced)

1. **Check existing tools BEFORE creating new ones** — `python scripts/inventory.py search <keyword>`
2. **Never nest git repos** — Only one `.git` directory should exist at the project root.
3. **Test before committing** — New code must pass syntax check before commit.
4. **Document efforts >30 min** — See `docs/sops/sop-25-documentation.md`.
5. **Rule of Three** — Same approach fails 3x? STOP. Research root cause.
6. **Push after commit** — Every `git commit` should be followed by `git push` in the same session (if remote sync is enabled).
7. **Verify sync on session start** — Run `git log --oneline origin/main..HEAD`. If unpushed commits exist, push before doing anything else.

## Communication Patterns

| User Says | Agent Does |
|-----------|-----------|
| "Deploy" / "Ship it" | Follow `docs/sops/sop-03-deployment.md` |
| "New project" | Follow `docs/sops/sop-00-kickoff.md` then `sop-01-init.md` |
| "Continue from last session" | Check `docs/session-history.md` |
| "Roll back" | Follow `docs/sops/sop-07-rollback.md` |
| "What tools do we have?" | `python scripts/inventory.py list` |
| "Search for X" | `python scripts/inventory.py search X` |
| "Health check" | `python scripts/health_check.py` |

## Where Things Live

| What | Location |
|------|----------|
| SOPs | `docs/sops/INDEX.md` |
| Session history | `docs/session-history.md` |
| System state | `docs/system-state.md` |
| Architecture decisions | `docs/architecture-decisions.md` |
| API keys & secrets | `.env` (root) |
| Shared utilities | `execution/` |
| Project code | `projects/[name]/src/` |
| Launch scripts | `scripts/` |
| Agent memory | `memory/MEMORY.md` |
| Hooks | `.claude/hooks/` |
| Slash commands | `.claude/commands/` |

## Project Layout

```
project-root/
├── CLAUDE.md                  # This file (always in context)
├── .env                       # API keys and secrets
├── .agent-os-configured       # Onboarding complete marker
├── .agent-os-version          # AgentOS version
├── scripts/                   # Launch scripts, utilities
├── execution/                 # Shared utilities (2+ project use)
├── docs/                      # Reference documentation
│   ├── sops/                  # Standard operating procedures
│   ├── session-history.md     # Cross-session continuity
│   ├── system-state.md        # What's built, broken, in progress
│   └── architecture-decisions.md
├── projects/                  # Project-specific code
│   └── [name]/
│       └── src/
├── memory/                    # Agent memory files
│   ├── MEMORY.md              # Primary memory
│   └── templates/             # Memory file templates
└── .claude/
    ├── commands/              # Slash commands
    ├── hooks/                 # Pre/post tool-use hooks
    └── settings.local.json    # Permissions & hook config
```

## Session Start Checklist

1. This file loads automatically (always in context)
2. Read `docs/architecture-decisions.md` for cross-session conventions
3. Check `docs/system-state.md` for current state
4. Check which project we're working on — read its CLAUDE.md if it has one
5. Check `docs/session-history.md` if continuing previous work

## Principle

Be pragmatic. Be reliable. Self-anneal.
