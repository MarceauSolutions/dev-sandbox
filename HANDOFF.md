# HANDOFF.md — Agent Task Queue

**Purpose**: Single source of truth for work handoffs between EC2 (Clawdbot/Ralph) and MacBook (Claude Code).

**Last Updated**: 2026-02-09

---

## 📥 Pending for Mac (Claude Code)

_Tasks that need Mac-specific tools or interactive work_

<!-- When adding tasks, use this format:
### Task: [Short Title]
- **From**: clawdbot | ralph
- **Priority**: high | medium | low
- **Created**: YYYY-MM-DD HH:MM UTC
- **Context**: Brief description
- **Files**: List of relevant files
- **Action**: What Claude Code should do
-->

_No pending tasks_

---

## 📤 Pending for EC2 (Clawdbot/Ralph)

_Tasks to be picked up when Mac work is done_

_No pending tasks_

---

## 🔄 In Progress

_Currently being worked on_

_None_

---

## ✅ Recently Completed

_Last 10 completed handoffs (auto-archived)_

_None yet_

---

## Quick Commands

**On Mac (Claude Code)**:
```bash
# Pull latest and check for work
cd ~/dev-sandbox && git pull && cat HANDOFF.md

# After completing Mac work, commit and push
git add . && git commit -m "feat: [description]" && git push
```

**On EC2 (Clawdbot)**:
```bash
# Check for Mac-completed work
cd /home/clawdbot/dev-sandbox && git pull

# Add task for Mac
# (Clawdbot edits HANDOFF.md, commits, pushes)
```

---

## Handoff Protocol

### EC2 → Mac
1. Clawdbot/Ralph completes work up to Mac-specific step
2. Updates `HANDOFF.md` with task details
3. Commits and pushes to GitHub
4. Sends Telegram notification to William

### Mac → EC2
1. Claude Code pulls latest, reads `HANDOFF.md`
2. Completes Mac-specific work
3. Moves task to "Completed" section
4. Commits and pushes
5. (Optional) Adds follow-up task for EC2

### Sync Trigger
- **Heartbeat**: Clawdbot checks `git pull` periodically
- **Manual**: William says "sync" or "check handoffs"
- **Webhook**: (Future) n8n workflow triggers on push
