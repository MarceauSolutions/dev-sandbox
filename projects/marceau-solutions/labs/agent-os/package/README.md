# AgentOS — The Operating System for Claude Code

> Drop in. Open VS Code. Your AI configures itself in 5 minutes.

## Quick Start

1. **Copy** this entire directory into your project root
2. **Open** VS Code with the Claude Code extension
3. **Start a conversation** — AgentOS detects the fresh install and walks you through setup
4. **Done.** Your AI agent now has persistent memory, execution discipline, and guard rails.

## What's Inside

```
├── CLAUDE.md                  # Agent configuration (the brain)
├── .claude/
│   ├── commands/              # Slash commands (/deploy, /test, etc.)
│   ├── hooks/                 # Guard hooks (cost, stack, destructive, etc.)
│   └── settings.local.json    # Permissions & hook wiring
├── memory/
│   ├── MEMORY.md              # Persistent memory index
│   └── templates/             # Memory file templates
├── docs/
│   ├── sops/                  # Standard Operating Procedures
│   ├── setup-guide.md         # AI onboarding instructions
│   ├── session-history.md     # Cross-session continuity
│   ├── system-state.md        # What's built/broken tracker
│   └── architecture-decisions.md
├── scripts/
│   ├── health_check.py        # System health monitor
│   └── inventory.py           # Tool search & discovery
├── execution/                 # Shared utilities (2+ project use)
└── projects/                  # Your project code
```

## Key Features

- **Self-Configuring**: 5-minute onboarding — the AI interviews you and fills in everything
- **Persistent Memory**: Your AI remembers preferences, feedback, and context across sessions
- **Execution Discipline**: 12 battle-tested rules that prevent common AI mistakes
- **Guard Hooks**: Automatic protection against cost blowouts, stack drift, and destructive commands
- **Session Continuity**: Pick up exactly where you left off, every time
- **Slash Commands**: /deploy, /test, /inventory, /new-project, /health-check

## Requirements

- [Claude Code](https://claude.ai/claude-code) (VS Code extension)
- Python 3.8+
- Git

## Documentation

- [Setup Guide](docs/setup-guide.md) — How onboarding works
- [Settings Guide](.claude/settings-guide.md) — Permissions & hooks explained
- [SOP Index](docs/sops/INDEX.md) — Standard operating procedures
- [Architecture Decisions](docs/architecture-decisions.md) — Cross-session conventions

## Version

See `.agent-os-version` for current version.

---

**AgentOS** by [Marceau Solutions](https://marceausolutions.com) — Embrace the Pain & Defy the Odds
