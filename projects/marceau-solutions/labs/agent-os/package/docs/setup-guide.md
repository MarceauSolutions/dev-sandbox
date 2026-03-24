# AgentOS Setup Guide

> This guide is for the AI agent, not the human user. When `.agent-os-configured` does not exist, walk through these phases conversationally.

---

## Detection

At the start of every conversation, check:
```
if .agent-os-configured does NOT exist:
    → Run this onboarding flow
    → Do NOT proceed with any other task until setup is complete
```

---

## Phase 1 — Identity

Ask the user these questions (conversationally, not as a survey):

1. **What's your name?** → Stored as `{{USER_NAME}}`
2. **What's your business or project called?** → Stored as `{{PROJECT_NAME}}`
3. **Give me a one-line description.** → Stored as `{{PROJECT_DESCRIPTION}}`
4. **What's your role?** (solo dev, agency owner, founder, student, freelancer, etc.) → Stored as `{{USER_ROLE}}`
5. **What's your primary tech stack?** (Python, Node, Go, etc.) → Stored as `{{TECH_STACK}}`
6. **How experienced are you with AI coding tools?** (beginner, intermediate, power user) → Stored as `{{EXPERIENCE_LEVEL}}`

---

## Phase 2 — Infrastructure

1. **Do you have a VPS or server?** (y/n)
   - If yes: SSH connection details → `{{SERVER_HOST}}`, `{{SERVER_USER}}`
   - Enables: multi-agent architecture, remote deployment, 24/7 services
   - If no: local-only mode, single-agent

2. **Do you use an automation platform?** (n8n, Make, Zapier, none)
   → Stored as `{{AUTOMATION_PLATFORM}}`
   - If none: recommend n8n (self-hosted, free) or skip automation features

3. **Communication/alert channels?** (check all that apply)
   - SMS via Twilio → needs `TWILIO_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE` in `.env`
   - Email via SMTP → needs `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` in `.env`
   - Slack → needs `SLACK_WEBHOOK_URL` in `.env`
   - Telegram → needs `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in `.env`
   - Discord → needs `DISCORD_WEBHOOK_URL` in `.env`
   - None → alerts go to terminal output only
   → Primary channel stored as `{{ALERT_CHANNEL}}`

4. **Where do you deploy?** (check all that apply)
   - GitHub Pages
   - Vercel
   - Netlify
   - AWS (EC2, Lambda, etc.)
   - Railway
   - Fly.io
   - Self-hosted VPS
   - Other: ___
   → Stored as `{{DEPLOY_TARGETS}}`

5. **Do you have a domain name?** → `{{DOMAIN}}`

---

## Phase 3 — Preferences

1. **Communication style**: Do you prefer terse, direct responses or detailed explanations?
   → Stored as `{{COMM_STYLE}}` (terse | detailed | balanced)

2. **What should I NEVER do without asking you first?**
   Examples: delete files, push to main, spend money on APIs, deploy to production
   → Stored as `{{NEVER_WITHOUT_ASKING}}`

3. **Blocked services/tools** — anything you explicitly do NOT want used?
   → Stored as `{{BLOCKED_TOOLS}}` — added to `.claude/hooks/stack-guard.sh`

4. **Approved stack** — services you trust and prefer?
   → Stored as `{{APPROVED_STACK}}`

5. **Output preferences**:
   - PDF style preference (minimal, branded, detailed)
   - Default file format for reports
   → Stored as `{{OUTPUT_PREFS}}`

---

## Phase 4 — Write Configuration

Execute these steps automatically:

### 4.1 Fill CLAUDE.md placeholders
Replace all `{{PLACEHOLDER}}` values in `CLAUDE.md` with collected answers.

### 4.2 Create personalized memory
Write `memory/MEMORY.md` with:
- User profile section (name, role, stack, preferences)
- Infrastructure section (server, automation, deploy targets)
- Hard rules section (populated from CLAUDE.md execution discipline)
- Empty sections for: session notes, project context, key references

### 4.3 Configure hooks
- Update `stack-guard.sh` with blocked/approved tools
- Update `api-cost-guard.sh` if paid API providers are listed
- Ensure all hooks use correct paths

### 4.4 Create .env template
If `.env` doesn't exist, create a template with commented-out entries for configured services:
```
# AgentOS Environment Variables
# Fill in the values for your configured services

# {{AUTOMATION_PLATFORM}} (if applicable)
# AUTOMATION_API_KEY=

# Alert channels
# TWILIO_SID=
# TWILIO_AUTH_TOKEN=
# SMTP_HOST=
# etc.
```

### 4.5 Create marker file
Write `.agent-os-configured`:
```
configured_at: {{TIMESTAMP}}
configured_by: AgentOS v1.0.0
user: {{USER_NAME}}
project: {{PROJECT_NAME}}
```

### 4.6 Run first health check
```bash
python scripts/health_check.py
```

### 4.7 Welcome message
Print:
```
AgentOS is configured. Here's what I can do now:

- Search your codebase: /inventory
- Start a new project: /new-project
- Deploy code: /deploy
- Run tests: /test
- Health check: /health-check

Your configuration is saved. I'll remember your preferences across sessions.
Start by telling me what you're working on.
```
