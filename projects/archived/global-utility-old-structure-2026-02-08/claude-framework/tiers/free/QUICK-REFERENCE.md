# Claude Development Framework - Quick Reference Card

## Core Workflow

```
1. INIT    → Create project structure, CLAUDE.md
2. DEVELOP → Build with Claude, document as you go
3. TEST    → Verify it works
4. DEPLOY  → Version bump, changelog, release
5. REPEAT  → Iterate based on learnings
```

## Essential Commands

| Action | How |
|--------|-----|
| Start session | Claude reads CLAUDE.md automatically |
| Continue session | "Read session-history.md for context" |
| End session | Update session-history.md, commit |
| Deploy | Update VERSION, CHANGELOG, tag, push |

## Version Format

```
1.2.3-dev
│ │ │  └── Development suffix (remove for release)
│ │ └──── Patch: Bug fixes
│ └────── Minor: New features (backwards compatible)
└──────── Major: Breaking changes
```

## Project Structure

```
project/
├── CLAUDE.md         # Agent instructions (READ THIS)
├── src/              # Your code
├── workflows/        # Documented procedures
├── docs/
│   └── session-history.md  # Session continuity
├── VERSION           # Current version
└── CHANGELOG.md      # Version history
```

## Communication Patterns

| Say This | Claude Does |
|----------|-------------|
| "Follow the SOP" | Executes documented procedure |
| "Document this" | Creates workflow doc |
| "Deploy" | Runs SOP 3 |
| "Save progress" | Updates session history |
| "What's the status?" | Reports current state |

## SOPs at a Glance

| # | SOP | When |
|---|-----|------|
| 1 | Project Init | Starting new project |
| 3 | Deployment | Ready to release |
| 5 | Session Docs | End of session |

## Quick Session End

```bash
# 1. Document session
# Add entry to docs/session-history.md

# 2. Commit
git add .
git commit -m "docs: Session progress 2026-01-16"
```

## Quick Deploy

```bash
# 1. Set version
echo "1.0.0" > VERSION

# 2. Update CHANGELOG.md

# 3. Commit & tag
git add . && git commit -m "release: v1.0.0"
git tag -a v1.0.0 -m "Version 1.0.0"

# 4. Bump to dev
echo "1.1.0-dev" > VERSION
git add VERSION && git commit -m "chore: bump to dev"
```

---

**Free Tier** | Full system at marceausolutions.com/claude-framework
