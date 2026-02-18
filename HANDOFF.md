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

### Task: Clawdbot Security Fixes + Brave API Setup
- **From**: clawdbot
- **Priority**: high
- **Created**: 2026-02-18 17:10 UTC
- **Context**: Security audit found issues; also need Brave Search API for web search capability

#### 🚨 Security Fixes (Run on EC2 via SSH)

```bash
# SSH to EC2
ssh clawdbot@34.193.98.97

# Fix 1: Config file permissions (CRITICAL)
chmod 600 /home/clawdbot/.clawdbot/clawdbot.json

# Fix 2: Credentials directory permissions (WARN)
chmod 700 /home/clawdbot/.clawdbot/credentials

# Verify fixes
ls -la /home/clawdbot/.clawdbot/clawdbot.json
ls -la /home/clawdbot/.clawdbot/credentials
```

#### 🔍 Add Brave Search API

1. Get free API key: https://brave.com/search/api/
2. Configure Clawdbot:
```bash
ssh clawdbot@34.193.98.97
clawdbot configure --section web
# Paste the Brave API key when prompted
```

#### 🔐 Optional: Gateway Auth (Extra Security)

If you want to secure the gateway:
```bash
# Generate a random token
openssl rand -hex 32

# Edit config
nano /home/clawdbot/.clawdbot/clawdbot.json
# Add under "gateway": { "auth": { "token": "YOUR_TOKEN_HERE" } }

# Restart gateway
clawdbot gateway restart
```

#### 📱 Optional: Isolate Telegram DM Sessions

To prevent context leaking between different Telegram users:
```bash
# Edit config and add under "channels.telegram":
# "session": { "dmScope": "per-channel-peer" }
```

#### ✅ After Completing
- Move this task to "Completed" section
- Commit and push: `git add HANDOFF.md && git commit -m "fix: security hardening complete" && git push`

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
