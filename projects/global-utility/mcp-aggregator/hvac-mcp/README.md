# HVAC Quotes MCP

mcp-name: io.github.wmarceau/hvac-quotes

HVAC equipment RFQ (Request for Quote) management via MCP for Claude Desktop.

## Features

- **Submit RFQs** to HVAC equipment distributors
- **Check RFQ status** and track responses
- **Get and compare quotes** from multiple distributors
- **Simulate quotes** for testing workflows

## Installation

```bash
pip install hvac-quotes-mcp
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hvac-quotes": {
      "command": "hvac-quotes-mcp",
      "env": {
        "HVAC_MOCK_EMAIL": "true"
      }
    }
  }
}
```

## Available Tools

### submit_rfq
Submit a Request for Quote to HVAC distributors.

```
Equipment types: ac_unit, furnace, heat_pump, air_handler, condenser,
                 evaporator_coil, mini_split, thermostat, ductwork, other
```

### check_rfq_status
Check the status of a submitted RFQ.

### get_quotes
Get all quotes received for an RFQ.

### compare_quotes
Compare quotes from multiple distributors - identifies best price, fastest delivery, and recommended option.

### simulate_quote
(Testing) Simulate a quote response from a distributor without waiting for real email responses.

## Example Usage

Ask Claude:

> "I need a 3-ton AC unit delivered to Naples, FL. Can you get me quotes from distributors?"

Claude will:
1. Submit RFQs to matching distributors in Florida
2. Return RFQ IDs for tracking
3. You can check status later or simulate quotes for testing

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HVAC_MOCK_EMAIL` | Use mock email mode for testing | `true` |
| `SMTP_HOST` | SMTP server hostname | - |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASS` | SMTP password | - |
| `SMTP_FROM` | From email address | - |
| `HVAC_DB_PATH` | SQLite database path | temp directory |

## How It Works

Unlike instant-response APIs, this MCP models real-world HVAC procurement:

1. **RFQ Submission**: Sends email requests to distributors (mocked by default)
2. **Async Response**: Distributors respond in 24-48 hours (simulate for testing)
3. **Quote Comparison**: Compare received quotes for best value

## License

MIT
