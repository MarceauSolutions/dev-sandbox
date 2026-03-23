# Claude Code ↔ Clawdbot Communication Bridge

## Quick Reference

**EC2 IP**: `34.193.98.97` (or check `curl -s ifconfig.me` on EC2)

### Send Message to Clawdbot (appears in Telegram)

```bash
# From Mac terminal
curl -X POST http://YOUR_EC2_IP:5010/agents/message/send \
  -H "Content-Type: application/json" \
  -d '{"from_agent": "claude-code", "to_agent": "clawdbot", "message": "Hey, I finished the task. Ready for review."}'
```

### Update Your Status (Clawdbot can see what you're working on)

```bash
curl -X POST http://YOUR_EC2_IP:5010/agents/state/update \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "claude-code", "state": {"working_on": "YouTube video script", "status": "active", "progress": "75%"}}'
```

### Check if Clawdbot Sent You a Message

```bash
curl -X POST http://YOUR_EC2_IP:5010/agents/message/receive \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "claude-code"}'
```

### See Clawdbot's Current State

```bash
curl -X POST http://YOUR_EC2_IP:5010/agents/state/get \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "clawdbot"}'
```

### Trigger Git Sync on EC2

```bash
curl -X POST http://YOUR_EC2_IP:5010/git/pull \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/clawdbot/dev-sandbox"}'
```

---

## Shell Aliases (Add to ~/.zshrc)

```bash
# EC2 Agent Bridge
export EC2_IP="YOUR_EC2_IP"

# Send message to Clawdbot
clawdbot-msg() {
  curl -s -X POST http://$EC2_IP:5010/agents/message/send \
    -H "Content-Type: application/json" \
    -d "{\"from_agent\": \"claude-code\", \"to_agent\": \"clawdbot\", \"message\": \"$1\"}" | jq .
}

# Update my status
clawdbot-status() {
  curl -s -X POST http://$EC2_IP:5010/agents/state/update \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\": \"claude-code\", \"state\": {\"working_on\": \"$1\", \"status\": \"active\"}}" | jq .
}

# Check for messages
clawdbot-inbox() {
  curl -s -X POST http://$EC2_IP:5010/agents/message/receive \
    -H "Content-Type: application/json" \
    -d '{"agent_id": "claude-code"}' | jq .
}

# Sync git on EC2
clawdbot-sync() {
  curl -s -X POST http://$EC2_IP:5010/git/pull \
    -H "Content-Type: application/json" \
    -d '{"path": "/home/clawdbot/dev-sandbox"}' | jq .
}

# Check EC2 bridge health
clawdbot-health() {
  curl -s http://$EC2_IP:5010/health | jq '{status, uptime_seconds, version}'
}
```

---

## Integration with Claude Code

### At Session Start (Claude Code should do this automatically)

```python
# Check for messages from Clawdbot
import subprocess
result = subprocess.run(['curl', '-s', '-X', 'POST', 
    f'http://{EC2_IP}:5010/agents/message/receive',
    '-H', 'Content-Type: application/json',
    '-d', '{"agent_id": "claude-code"}'], capture_output=True)
# Process any pending messages

# Update status
subprocess.run(['curl', '-s', '-X', 'POST',
    f'http://{EC2_IP}:5010/agents/state/update',
    '-H', 'Content-Type: application/json',
    '-d', '{"agent_id": "claude-code", "state": {"status": "active", "session_start": "now"}}'])
```

### After Completing Major Tasks

```python
# Notify Clawdbot (and William via Telegram)
subprocess.run(['curl', '-s', '-X', 'POST',
    f'http://{EC2_IP}:5010/agents/message/send',
    '-H', 'Content-Type: application/json',
    '-d', '{"from_agent": "claude-code", "to_agent": "clawdbot", "message": "Completed: YouTube video script. Pushed to GitHub."}'])
```

---

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Claude Code   │◄───────►│  Agent Bridge   │◄───────►│    Clawdbot     │
│   (Mac/VS Code) │  HTTP   │   (EC2:5010)    │  Python │  (EC2/Telegram) │
└─────────────────┘         └─────────────────┘         └─────────────────┘
         │                          │                           │
         │                          │                           │
         ▼                          ▼                           ▼
    git push ──────────────► GitHub ◄────────────────── git pull
                                │
                                ▼
                    PostToolUse hook triggers
                    EC2 auto-sync (when working)
```

## When To Use What

| Scenario | Method |
|----------|--------|
| Quick message to William | `clawdbot-msg "message"` |
| Handoff task to Clawdbot | Update HANDOFF.md + push + `clawdbot-msg` |
| Need Clawdbot to do something | `clawdbot-msg "Please do X"` |
| Finished major task | `clawdbot-msg "Done: X"` + git push |
| Want Clawdbot to pull latest | `clawdbot-sync` |
| Check if Clawdbot pinged you | `clawdbot-inbox` |
