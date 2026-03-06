# Optimized Handoff Workflow

**Version**: 1.0.0
**Created**: 2026-02-09

---

## Overview

This document describes the optimized handoff process between:
- **Clawdbot** (EC2, 24/7, Telegram/WhatsApp)
- **Ralph** (EC2, autonomous PRD execution)
- **Claude Code** (MacBook, interactive development)

**Key Files**:
- `HANDOFF.md` — Human-readable task queue (git-tracked)
- `ralph/handoffs.json` — Machine-readable state (git-tracked)
- `scripts/sync-handoffs.sh` — EC2 sync script
- `scripts/mac-sync.sh` — Mac sync script (copy to ~/dev-sandbox)

---

## Quick Reference

### From Telegram (William → Clawdbot)
```
"Build X" → Clawdbot handles or creates PRD for Ralph
"Sync" → Clawdbot pulls latest and reports pending tasks
"Push to Mac" → Clawdbot adds task to HANDOFF.md for Claude Code
"Check handoffs" → Shows pending work in both directions
```

### From Mac (Claude Code)
```bash
# Start of session
cd ~/dev-sandbox && git pull && cat HANDOFF.md

# After work
git add . && git commit -m "feat: description" && git push

# Notify EC2 (optional)
# Add task to "Pending for EC2" section if follow-up needed
```

---

## Workflow Patterns

### Pattern A: Simple EC2 → Mac → Done

```
┌─────────────────────────────────────────────────────────────┐
│  1. William (Telegram): "Build X and deploy to PyPI"        │
│                          ↓                                  │
│  2. Clawdbot: Builds X, commits                            │
│                          ↓                                  │
│  3. Clawdbot: Adds "Deploy to PyPI" task to HANDOFF.md     │
│               Commits & pushes                              │
│               Notifies William: "Ready for Mac"             │
│                          ↓                                  │
│  4. William (Mac): Opens Claude Code                        │
│               `git pull && cat HANDOFF.md`                  │
│                          ↓                                  │
│  5. Claude Code: Deploys to PyPI                           │
│               Moves task to "Completed"                     │
│               Commits & pushes                              │
│                          ↓                                  │
│  6. Done!                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Pattern B: Mac → EC2 → Mac (Round-trip)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Claude Code: Designs API, needs bulk implementation    │
│               Adds task to "Pending for EC2"               │
│               Commits & pushes                              │
│                          ↓                                  │
│  2. Clawdbot (heartbeat or manual): `git pull`              │
│               Sees pending task                             │
│               Notifies William: "New task from Mac"         │
│                          ↓                                  │
│  3. Clawdbot/Ralph: Implements bulk work                   │
│               Adds "Review & polish" to "Pending for Mac"   │
│               Commits & pushes                              │
│                          ↓                                  │
│  4. Claude Code: Pulls, reviews, finalizes                 │
│               Deploys if needed                             │
│                          ↓                                  │
│  5. Done!                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Pattern C: Parallel Work with Merge

```
┌─────────────────────────────────────────────────────────────┐
│  1. William: "Build dashboard with analytics pipeline"      │
│                          ↓                                  │
│  2. Clawdbot: Creates branches                             │
│     - clawdbot/dashboard (UI work)                         │
│     - ralph/pipeline (backend, triggers Ralph)             │
│                          ↓                                  │
│  3. Both work in parallel                                   │
│     Clawdbot: Dashboard UI                                  │
│     Ralph: Analytics pipeline                               │
│                          ↓                                  │
│  4. Clawdbot: Merges both branches                         │
│               Adds "Deploy + verify" to HANDOFF.md          │
│               Notifies William                              │
│                          ↓                                  │
│  5. Claude Code: Final verification, deploy                │
└─────────────────────────────────────────────────────────────┘
```

---

## Task Format

### In HANDOFF.md

```markdown
### Task: Deploy Trainerize MCP to PyPI
- **From**: clawdbot
- **Priority**: high
- **Created**: 2026-02-09 03:30 UTC
- **Context**: MCP built with 27 tools, tested, ready for publishing
- **Files**: projects/marceau-solutions/trainerize-mcp/
- **Action**: Run `python -m build` and `twine upload dist/*`
```

### In handoffs.json

```json
{
  "pending_for_mac": [
    {
      "id": "handoff-001",
      "title": "Deploy Trainerize MCP to PyPI",
      "from": "clawdbot",
      "priority": "high",
      "created": "2026-02-09T03:30:00Z",
      "context": "MCP built with 27 tools, tested, ready for publishing",
      "files": ["projects/marceau-solutions/trainerize-mcp/"],
      "action": "Run python -m build and twine upload dist/*"
    }
  ]
}
```

---

## Clawdbot Commands

### Handoff Management

| Command | Action |
|---------|--------|
| `sync` | Pull latest, show pending tasks |
| `check handoffs` | Same as sync |
| `push to mac: [task]` | Add task for Claude Code |
| `handoff status` | Show all active handoffs |

### Examples

```
"Push to mac: Deploy calculator to PyPI"
→ Clawdbot adds task to HANDOFF.md, commits, pushes, notifies

"Sync"
→ Clawdbot: "Pulled latest. 1 task pending for EC2: 'Add tests for API'"

"Check handoffs"
→ Clawdbot: "Active: 0 | For Mac: 1 | For EC2: 0 | Completed today: 2"
```

---

## Claude Code Quick Start

Add this to your Mac workflow:

```bash
# ~/.bashrc or ~/.zshrc
alias devsync='cd ~/dev-sandbox && git pull && cat HANDOFF.md'
alias devpush='cd ~/dev-sandbox && git add . && git commit -m'

# Usage
devsync                    # Start of session
devpush "feat: deployed X" # After work
git push                   # Send to GitHub
```

---

## Sync Triggers

### Automatic (EC2)
- **Heartbeat**: Every 30 min during active hours
- **On notification**: When Telegram message received
- **On Ralph complete**: After PRD execution

### Manual
- `sync` command via Telegram
- `./scripts/sync-handoffs.sh` on EC2
- `git pull` on Mac

### Future (Planned)
- n8n webhook on GitHub push → notifies relevant agent
- Slack/Discord integration for team handoffs

---

## Best Practices

### DO
- ✅ Always `git pull` before starting work
- ✅ Write clear task descriptions with file paths
- ✅ Move completed tasks to "Completed" section
- ✅ Commit after every logical unit of work
- ✅ Notify when handing off (Telegram or commit message)

### DON'T
- ❌ Work on same files simultaneously (use branches)
- ❌ Leave tasks in "In Progress" for >24 hours
- ❌ Push without pulling first (causes conflicts)
- ❌ Forget to move completed tasks (clutters queue)

---

## Troubleshooting

### Merge Conflict
```bash
git stash
git pull
git stash pop
# Resolve conflicts manually
git add . && git commit -m "fix: resolve merge conflict"
```

### Task Stuck in Queue
1. Check if blocking dependency exists
2. If Mac-specific: Move to "Pending for Mac"
3. If EC2-specific: Move to "Pending for EC2"
4. Update status in handoffs.json

### Agent Didn't See Task
1. Verify commit was pushed: `git log origin/main --oneline -5`
2. Verify pull happened: Check agent logs or ask to sync
3. Check HANDOFF.md format (must match expected structure)

---

## Related Docs

- [SOP-29-THREE-AGENT-COLLABORATION.md](SOP-29-THREE-AGENT-COLLABORATION.md)
- [AGENT-ORCHESTRATOR-GUIDE.md](AGENT-ORCHESTRATOR-GUIDE.md)
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md)
- [SOP-28-RALPH-USAGE.md](SOP-28-RALPH-USAGE.md)
