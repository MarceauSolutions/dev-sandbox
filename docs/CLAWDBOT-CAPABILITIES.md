# Clawdbot AI Assistant - Capabilities & Integration Guide

*Last Updated: 2026-01-27*

## Overview

Clawdbot is William's personal AI assistant running on a dedicated EC2 instance, accessible via multiple messaging channels (Telegram, WhatsApp, iMessage). It uses Claude Max subscription (OAuth) for unlimited conversations without API credit costs.

## Infrastructure

Clawdbot runs on a **dedicated VPS** separate from the web services EC2. This provides:
- Isolation from production web traffic
- Dedicated resources for AI processing
- Independent scaling and maintenance

| Property | Value |
|----------|-------|
| **EC2 Instance** | Dedicated VPS (separate from web services at 34.193.98.97) |
| **SSH Host** | `clawdbot@44.193.244.59` |
| **Auth Method** | Claude Max OAuth (`sk-ant-oat01-...` access token) |
| **Token Refresh** | Automatic via refresh token (`sk-ant-ort01-...`) |
| **Service** | systemd (auto-starts on reboot) |

### Two EC2 Architecture

| Server | IP | Purpose |
|--------|-------|---------|
| **Web Services EC2** | 34.193.98.97 | SW Florida Comfort website, Voice AI API |
| **Clawdbot VPS** | 44.193.244.59 | AI assistant (Telegram, WhatsApp, iMessage) |

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
| **memory-lancedb** | ⚠️ Limited | Hardcoded for OpenAI embeddings (quota exceeded) |
| **telegram** | ✅ Active | Primary channel |
| **whatsapp** | ✅ Active | Personal number |
| **imessage** | ⚠️ Unknown | May need verification |
| Others | Unknown | Requires EC2 access to inventory |

## Known Issues & Backlog

| Issue | Priority | Status |
|-------|----------|--------|
| OpenAI embedding quota exceeded | High | memory-lancedb plugin needs Ollama integration |
| Ollama is installed but not connected | High | Plugin code change needed |
| Twilio integration not set up | Medium | Would enable SMS/call auto-response |

## Configuration Files

| File | Purpose |
|------|---------|
| `/home/clawdbot/.clawdbot/clawdbot.json` | Main configuration |
| `/home/clawdbot/.clawdbot/agents/main/agent/auth-profiles.json` | OAuth credentials |
| `/home/clawdbot/.clawdbot/.env` | Environment variables |
| `/home/clawdbot/.clawdbot/skills/` | Skill definitions |
| `/home/clawdbot/.clawdbot/plugins/` | Plugin configurations |

## OAuth Configuration (Working)

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
      "anthropic:claude-cli": {
        "provider": "anthropic",
        "mode": "oauth"
      }
    },
    "order": {
      "anthropic": ["anthropic:claude-cli"]
    }
  }
}
```

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
- LanceDB (vector memory, limited by OpenAI quota)

### Planned Integrations
| Integration | Purpose | Status |
|-------------|---------|--------|
| Twilio SMS | Auto-respond to business SMS | Pending |
| Twilio Voice | Auto-respond to calls | Pending |
| WhatsApp Business | Scale messaging | Pending |
| Ollama Embeddings | Replace OpenAI for memory | Blocked (code change needed) |

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
ssh clawdbot@44.193.244.59 "systemctl status clawdbot"
```

### View Logs
```bash
ssh clawdbot@44.193.244.59 "journalctl -u clawdbot -f"
```

### Check OAuth Status
```bash
ssh clawdbot@44.193.244.59 "clawdbot models status"
```

Expected output: `anthropic:claude-cli=OAuth` with expiry time

### Restart Clawdbot
```bash
ssh clawdbot@44.193.244.59 "sudo systemctl restart clawdbot"
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "No API key found for provider anthropic" | Auth profile mismatch | Ensure clawdbot.json references the profile in auth-profiles.json |
| OAuth token expired | Normal expiration | Should auto-refresh; if not, re-run OAuth flow |
| Memory not working | OpenAI quota exceeded | Pending: Integrate Ollama embeddings |
| Channel not responding | Service down | Check systemd status, restart if needed |

## Related Documents

- [EC2-SERVER-INFO.md](EC2-SERVER-INFO.md) - Web services EC2 (different server)
- [RALPH-CAPABILITIES.md](RALPH-CAPABILITIES.md) - Ralph autonomous agent
- [SOP-27-CLAWDBOT-USAGE.md](SOP-27-CLAWDBOT-USAGE.md) - When/how to use Clawdbot
