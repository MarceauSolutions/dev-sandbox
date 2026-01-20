# Agent Instructions

> Read this file at the start of every session. It contains core operating methods.

## Project Overview

**Project Name**: [Your Project Name]
**Purpose**: [What this project does]
**Current Status**: [Development/Testing/Production]

## Architecture

### Directory Structure
```
[project]/
├── src/              # Source code
├── workflows/        # Documented procedures
├── VERSION           # Current version
├── CHANGELOG.md      # Version history
└── README.md         # Project documentation
```

### Key Files
| File | Purpose |
|------|---------|
| `src/main.py` | [Description] |
| `src/utils.py` | [Description] |

## Communication Patterns

| User Says | Claude Does |
|-----------|-------------|
| "Follow the SOP" | Read and execute documented procedure |
| "Document this" | Create workflow or update docs |
| "Deploy" | Run deployment procedure |
| "Save progress" | Update session history |

## Operating Principles

1. **Read before writing** - Always read existing code before modifying
2. **Check for existing tools** - Look in project before creating new
3. **Document as you work** - Create workflows while completing tasks
4. **Self-anneal** - When errors occur: fix → update tool → update docs

## Session Start Checklist

1. ✅ Read this file (automatic)
2. Check context - what are we working on?
3. Check `workflows/` for existing procedures
4. Ask clarifying questions if needed

## Where to Put Things

| What | Where |
|------|-------|
| Source code | `src/` |
| Task procedures | `workflows/` |
| Session notes | `docs/session-history.md` |
| Test files | `.tmp/` (not committed) |

---

**Principle:** Be pragmatic. Be reliable. Document as you go.
