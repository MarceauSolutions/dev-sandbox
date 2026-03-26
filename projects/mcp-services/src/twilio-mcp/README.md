# Twilio MCP

mcp-name: io.github.wmarceau/twilio-mcp

An MCP (Model Context Protocol) server that gives Claude access to your Twilio SMS inbox and messaging.

## Features

- **check_sms_inbox** - Check for incoming SMS replies from cold outreach
- **send_sms** - Send SMS messages to leads
- **get_sms_reply_summary** - Get summary of all replies (hot leads, opt-outs, etc.)
- **get_hot_leads** - Get list of interested leads requiring follow-up
- **get_campaign_stats** - View outreach campaign statistics
- **forward_message_to_phone** - Forward important messages to your personal phone

## Installation

```bash
pip install twilio-mcp
```

## Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "twilio": {
      "command": "python",
      "args": ["-m", "twilio_mcp.server"],
      "env": {
        "TWILIO_ACCOUNT_SID": "your_account_sid",
        "TWILIO_AUTH_TOKEN": "your_auth_token",
        "TWILIO_PHONE_NUMBER": "+1855XXXXXXX"
      }
    }
  }
}
```

## Usage

Once configured, ask Claude:

- "Check my Twilio inbox for new messages"
- "Show me any hot leads from SMS"
- "Send an SMS to +12395551234 saying..."
- "What are my campaign statistics?"
- "Forward that message to my phone at +12395551234"

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number (E.164 format) |

## Requirements

- Python 3.10+
- Twilio account with SMS-enabled phone number
- MCP package

## License

MIT
