# Clawdbot AI Assistant - Capabilities & Integration Guide

*Last Updated: 2026-01-28*

## Overview

Clawdbot is William's personal AI assistant running on a dedicated EC2 instance, accessible via multiple messaging channels (Telegram, WhatsApp, iMessage). It uses Claude Max subscription (OAuth) for unlimited conversations without API credit costs.

## Official Documentation

**Always consult documentation before troubleshooting:**

| Resource | URL | Purpose |
|----------|-----|---------|
| **Clawdbot CLI Docs** | https://docs.molt.bot/cli | CLI commands and usage |
| **OAuth Concepts** | https://docs.molt.bot/concepts/oauth | Token setup and refresh |
| **Plugins Guide** | https://docs.molt.bot/cli/plugins | Plugin management |

## Infrastructure

Clawdbot runs on the **same EC2 instance** as web services, as a systemd service.

| Property | Value |
|----------|-------|
| **EC2 Instance** | `i-01752306f94897d7d` (marceau-production) |
| **SSH Host** | `ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97` |
| **Clawdbot User** | `clawdbot` (switch with `sudo -u clawdbot bash`) |
| **App Directory** | `/home/clawdbot/app/` |
| **Config Directory** | `/home/clawdbot/.clawdbot/` |
| **Auth Method** | Claude Max OAuth (`sk-ant-oat01-...` access token) |
| **Token Refresh** | Automatic via refresh token (`sk-ant-ort01-...`) |
| **Service** | systemd `clawdbot.service` (auto-starts on reboot) |

### EC2 Services

| Service | IP | Port | Purpose |
|---------|-------|------|---------|
| **Web Services** | 34.193.98.97 | 80/443 | SW Florida Comfort website |
| **Voice AI API** | 34.193.98.97 | 8000 | Twilio webhooks |
| **Clawdbot Gateway** | 34.193.98.97 | internal | AI assistant (Telegram, WhatsApp) |

## Channels

| Channel | Status | Configuration | Access |
|---------|--------|---------------|--------|
| **Telegram** | ✅ Active | @W_marceaubot | DM policy: "open", Memory: disabled |
| **WhatsApp** | ✅ Active | Personal number linked | Direct messages |
| **iMessage** | ⚠️ Configured | Status unknown | May need verification |
| **Twilio SMS** | ⏳ Pending | Integration planned | Via WhatsApp Business API |

## Skills (Estimated 54+)

Based on the Clawdbot framework, expected skill categories include:

### Productivity & Scheduling
- Calendar management
- Task/todo management
- Reminders and notifications
- Note-taking

### Communication
- Email drafting/sending
- Message composition
- Contact management

### Research & Information
- Web search
- Document analysis
- Data lookups

### Development & Code
- Code generation
- Code review
- Git operations
- File management

### Business Operations
- CRM integration (ClickUp)
- Lead management
- Analytics reporting

### Personal
- Weather updates
- News summaries
- Custom routines

**Note:** Full skill inventory requires SSH access to EC2 to list `/home/clawdbot/.clawdbot/skills/`

## Plugins (8 Active)

| Plugin | Status | Notes |
|--------|--------|-------|
| **memory-core** | ✅ Active | Built-in memory, uses Ollama embeddings |
| **memory-lancedb** | Disabled | Not needed - memory-core handles this |
| **telegram** | ✅ Active | Primary channel |
| **whatsapp** | ✅ Active | Personal number |
| **imessage** | ⚠️ Unknown | May need verification |
| Others | Unknown | Requires EC2 access to inventory |

## Known Issues & Backlog

| Issue | Priority | Status |
|-------|----------|--------|
| ~~OpenAI embedding quota exceeded~~ | ~~High~~ | ✅ RESOLVED - Using Ollama |
| ~~Ollama is installed but not connected~~ | ~~High~~ | ✅ RESOLVED - Connected via memorySearch config |
| Twilio integration not set up | Medium | Would enable SMS/call auto-response |

## Memory Configuration (Ollama)

Memory is now powered by **Ollama** running locally on EC2 with the `nomic-embed-text` embedding model.

**Configuration in `clawdbot.json`:**
```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "provider": "openai",
        "model": "nomic-embed-text",
        "remote": {
          "baseUrl": "http://localhost:11434/v1/"
        }
      }
    }
  }
}
```

**Memory Status:**
- Provider: `openai` (pointing to Ollama's OpenAI-compatible endpoint)
- Model: `nomic-embed-text` (768-dimensional embeddings)
- Storage: `~/.clawdbot/memory/main.sqlite`
- Embeddings: Local (no API costs)

**Troubleshooting Memory:**
```bash
# Check memory status
sudo -u clawdbot bash -c 'cd /home/clawdbot/app && export HOME=/home/clawdbot && ./node_modules/.bin/clawdbot memory status --deep'

# If Ollama reports insufficient memory, restart it
sudo systemctl restart ollama

# Verify Ollama is running
curl -s http://localhost:11434/api/tags
```

## Configuration Files

| File | Purpose |
|------|---------|
| `/home/clawdbot/.clawdbot/clawdbot.json` | Main configuration |
| `/home/clawdbot/.clawdbot/agents/main/agent/auth-profiles.json` | OAuth credentials |
| `/home/clawdbot/.clawdbot/.env` | Environment variables |
| `/home/clawdbot/.clawdbot/skills/` | Skill definitions |
| `/home/clawdbot/.clawdbot/plugins/` | Plugin configurations |

## OAuth Configuration (Working)

**Two auth profiles are configured:**
- `anthropic:manual` - Static token (primary, for headless server)
- `anthropic:claude-cli` - OAuth with refresh (backup, expires)

```json
// auth-profiles.json
{
  "version": 1,
  "profiles": {
    "anthropic:claude-cli": {
      "type": "oauth",
      "provider": "anthropic",
      "access": "sk-ant-oat01-...",
      "refresh": "sk-ant-ort01-...",
      "expires": 1769552372818
    },
    "anthropic:manual": {
      "type": "token",
      "provider": "anthropic",
      "token": "sk-ant-oat01-..."
    }
  },
  "lastGood": {
    "anthropic": "anthropic:claude-cli"
  }
}

// clawdbot.json (auth section)
{
  "auth": {
    "profiles": {
      "anthropic:manual": {
        "provider": "anthropic",
        "mode": "token"
      },
      "anthropic:claude-cli": {
        "provider": "anthropic",
        "mode": "oauth"
      }
    },
    "order": {
      "anthropic": ["anthropic:manual", "anthropic:claude-cli"]
    }
  }
}
```

**Note:** The `order` array determines which profile is tried first. `anthropic:manual` should be first for headless servers.

## How to Use Clawdbot

### Via Telegram
1. Open Telegram
2. Search for @W_marceaubot
3. Send a direct message
4. Clawdbot responds using Claude Max

### Via WhatsApp
1. Open WhatsApp
2. Message the linked personal number
3. Clawdbot responds (if logged in)

### Via iMessage (if configured)
1. Send iMessage to configured number
2. Response routed through Clawdbot

## Integration Points

### Current Integrations
- Telegram Bot API
- WhatsApp (personal link)
- Claude Max (OAuth)
- **Ollama Embeddings** (local vector memory via nomic-embed-text)

### Planned Integrations
| Integration | Purpose | Status |
|-------------|---------|--------|
| Twilio SMS | Auto-respond to business SMS | Pending |
| Twilio Voice | Auto-respond to calls | Pending |
| WhatsApp Business | Scale messaging | Pending |
| ~~Ollama Embeddings~~ | ~~Replace OpenAI for memory~~ | ✅ COMPLETED (2026-01-28) |

## Clawdbot vs Claude Code vs Ralph

| Tool | Best For | Access Method |
|------|----------|---------------|
| **Clawdbot** | Quick tasks, mobile access, personal assistant | Telegram/WhatsApp anywhere |
| **Claude Code** | Development, complex coding, file editing | Terminal on Mac |
| **Ralph** | Autonomous multi-story development loops | Claude Code invocation |

### When to Use Clawdbot
- ✅ Quick questions while away from computer
- ✅ Scheduling and reminders
- ✅ Simple lookups and research
- ✅ Message drafting on the go
- ❌ Complex multi-file development (use Claude Code)
- ❌ Autonomous development loops (use Ralph)

## Monitoring & Health Checks

### Check Clawdbot Status
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 "sudo systemctl status clawdbot"
```

### View Logs
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 "sudo journalctl -u clawdbot -f"
```

### Check OAuth Status
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 "sudo -u clawdbot bash -c 'cd /home/clawdbot/app && HOME=/home/clawdbot ./node_modules/.bin/clawdbot models status'"
```

Expected output: `anthropic:claude-cli=OAuth` with expiry time

### Restart Clawdbot
```bash
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 "sudo systemctl restart clawdbot"
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "No API key found for provider anthropic" | Auth profile mismatch | Ensure clawdbot.json references the profile in auth-profiles.json |
| OAuth token expired | Normal expiration | See "Re-authenticating OAuth" below |
| "No provider plugins found" | Anthropic plugin not installed | Run `./node_modules/.bin/clawdbot plugins install @clawdbot/anthropic` |
| Memory not working | OpenAI quota exceeded | Pending: Integrate Ollama embeddings |
| Channel not responding | Service down | Check systemd status, restart if needed |

### Re-authenticating OAuth (When Token Expires)

**Reference**: https://docs.molt.bot/concepts/oauth

**Why standard OAuth fails on EC2:** Headless servers can't complete browser-based OAuth redirects. The solution is to generate a token on your Mac and paste it on EC2.

#### Step 1: Generate Token on Mac

On your local Mac (with browser access):
```bash
claude setup-token
```
This opens a browser, you authenticate with Claude Max, and it gives you a token starting with `sk-ant-oat01-...`. Copy this token.

#### Step 2: Paste Token on EC2

```bash
# SSH into EC2
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97

# Switch to clawdbot user
sudo -u clawdbot bash
cd /home/clawdbot/app
export HOME=/home/clawdbot

# Paste the token
./node_modules/.bin/clawdbot models auth paste-token --provider anthropic
# When prompted, paste your sk-ant-oat01-... token
```

#### Step 3: Verify and Restart

```bash
# Check status (should show anthropic:manual as static)
./node_modules/.bin/clawdbot models status

# Exit to ec2-user and restart
exit
sudo systemctl restart clawdbot
```

#### Step 4: Test

Send a message to @W_marceaubot on Telegram to verify it's working.

**Important:** The pasted token is static (doesn't auto-refresh). When it expires, repeat this process.

## Related Documents

- [EC2-SERVER-INFO.md](EC2-SERVER-INFO.md) - Web services EC2 (different server)
- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md) - Ralph autonomous agent
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - When/how to use Clawdbot
