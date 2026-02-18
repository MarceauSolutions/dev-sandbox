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

### Task: Sign Up for Brave Search API
- **From**: clawdbot → claude code (completed security fixes)
- **Priority**: medium
- **Created**: 2026-02-18 17:10 UTC
- **Context**: Brave Search API gives Clawdbot web search. Requires signup with credit card for identity verification.
- **Action**: Go to https://brave.com/search/api/ → sign up → get API key → SSH to EC2 and run `clawdbot configure --section web`
- **Cost**: Free tier = $5/mo credits (~1,000 queries). Requires attribution.

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

### ✅ Clawdbot Security Fixes + Full Capability Upgrade
- **Completed**: 2026-02-18 17:16 UTC
- **By**: Claude Code (Mac)
- **What was done**:
  - Fixed config file permissions (`chmod 600 clawdbot.json`)
  - Fixed credentials dir permissions (`chmod 700 credentials/`)
  - Secured all .env, backup configs, API key files
  - Added gateway auth token
  - Fixed .env parse errors (unquoted values with spaces)
  - Installed Python 3.11 packages: n8n-mcp-server, mcp-telegram, google-api-python-client, tweepy
  - Configured 3 MCP servers: n8n (localhost:5678), Context7, Telegram
  - Deployed 33 API keys to both .clawdbot/.env and dev-sandbox/.env
  - Copied Google OAuth tokens (calendar, gmail, sheets, marceausolutions)
  - Updated SOUL.md v1.0 → v2.0 with full capability docs
  - Updated systemd service PATH + dual .env sourcing
  - Telegram DM isolation: NOT supported by clawdbot config schema (skipped)

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
