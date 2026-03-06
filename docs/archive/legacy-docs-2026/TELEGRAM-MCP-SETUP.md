# Telegram MCP Setup Guide

**Purpose**: Add Telegram MCP server to Claude Code so you can send/read Telegram messages directly from the terminal — no context switching.

**Status**: Awaiting your Telegram API credentials (5 min setup)

---

## Step 1: Get Telegram API Credentials (2 min)

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API development tools"
4. Fill in:
   - **App title**: "Claude Code"
   - **Short name**: "claudecode"
   - **Platform**: Other
5. Copy your **api_id** (number) and **api_hash** (string)

---

## Step 2: Install Telegram MCP (1 min)

Run:
```bash
pip install mcp-telegram
```

Or if using the `sparfenyuk/mcp-telegram` package:
```bash
pip install mcp-server-telegram
```

---

## Step 3: Add to Claude Code Config (1 min)

Open `~/.claude.json` and add to the `mcpServers` section under your dev-sandbox project:

```json
"telegram": {
  "type": "stdio",
  "command": "/opt/anaconda3/bin/python",
  "args": ["-m", "mcp_telegram"],
  "env": {
    "TELEGRAM_API_ID": "<your_api_id>",
    "TELEGRAM_API_HASH": "<your_api_hash>",
    "TELEGRAM_BOT_TOKEN": "8596701493:AAHZm9agw78C2co6-z4cgWqhuC5YswQ6v0o"
  }
}
```

---

## Step 4: Restart Claude Code

The MCP server will be available after restarting. You'll be able to:

- **Read messages** from Clawdbot conversations
- **Send messages** to trigger Clawdbot tasks
- **Check handoff status** without switching apps

---

## What This Enables

| Use Case | Before | After |
|----------|--------|-------|
| Tell Clawdbot to start a task | Switch to Telegram app, type message | `/handoff to ec2: <task>` or send directly via MCP |
| Read Clawdbot's research results | Switch to Telegram, scroll up | Read directly in Claude Code context |
| Check if Clawdbot finished | Switch to Telegram | Query via MCP tool |
| Send handoff with code context | Copy/paste between apps | MCP sends directly with full context |

---

## Note on Bot Token vs API Credentials

- **Bot Token** (`8596701493:...`): Already have this. Used by Clawdbot to send/receive as a bot.
- **API ID + Hash**: Needed for the MCP to access Telegram's API as a client. Get from my.telegram.org.

Both are needed for the MCP to work fully. The bot token alone allows bot-level access (send messages, read bot conversations). The API credentials enable user-level access (read any chat, search messages).

---

## Quick Test After Setup

In Claude Code, try:
```
Send a test message to Clawdbot: "Hello from Claude Code via MCP"
```

If the MCP is working, you'll see the message arrive in your Telegram chat with Clawdbot.
