# HVAC Quotes MCP

> HVAC equipment RFQ management for contractors via Claude Desktop

**Package:** `hvac-quotes-mcp`
**Version:** 1.0.0
**Registry:** `io.github.wmarceau/hvac-quotes`

## What does this MCP do?

The HVAC Quotes MCP helps HVAC contractors manage Request for Quotes (RFQs) through Claude. Submit quotes to multiple distributors, track responses, and compare pricing - all through natural language.

## Installation

```bash
pip install hvac-quotes-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

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
Submit an RFQ to HVAC equipment distributors.

**Parameters:**
- `equipment_type`: Type of equipment (ac_unit, furnace, heat_pump, etc.)
- `delivery_address`: Full delivery address including state
- `specifications`: Equipment specs (tonnage, SEER, BTU, voltage)
- `brand_preference` (optional): Preferred brand
- `quantity` (optional): Number of units needed

### check_rfq_status
Check the status of a submitted RFQ.

### get_quotes
Retrieve all quotes received for an RFQ.

### compare_quotes
Compare quotes from multiple distributors to find the best deal.

### simulate_quote
(Testing) Simulate a distributor quote response.

## Example Prompts

Ask Claude:

> "I need quotes for a 3-ton Carrier AC unit delivered to Naples, FL"

> "Check the status of my RFQ abc12345"

> "Compare all the quotes I've received and show me the best deal"

> "Submit an RFQ for a 16 SEER heat pump with R-410A refrigerant"

## Supported Equipment Types

| Type | Description |
|------|-------------|
| ac_unit | Central air conditioning units |
| furnace | Gas or electric furnaces |
| heat_pump | Heat pump systems |
| air_handler | Air handlers |
| condenser | Condenser units |
| evaporator_coil | Evaporator coils |
| mini_split | Ductless mini-split systems |
| thermostat | Smart and standard thermostats |
| ductwork | Duct materials and accessories |

## How It Works

1. **Submit RFQ:** You provide equipment requirements
2. **Distributor Matching:** System finds distributors in your region
3. **Email Sent:** RFQ sent via email (mocked by default for testing)
4. **Wait for Response:** Real distributors respond in 24-48 hours
5. **Compare Quotes:** Review and compare received quotes

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HVAC_MOCK_EMAIL` | Use mock mode for testing | `true` |
| `SMTP_HOST` | SMTP server for real emails | - |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASS` | SMTP password | - |

## FAQ

### Is this connected to real distributors?
By default, it runs in mock mode for testing. Set `HVAC_MOCK_EMAIL=false` and configure SMTP for real distributor emails.

### How long do quotes take?
Real distributor responses typically take 24-48 hours. Use `simulate_quote` for immediate testing.

### What regions are supported?
Major US states, primarily Southeast (FL, GA, AL, SC, NC, TN). Distributor coverage varies by region.

### Can I specify exact equipment models?
Yes, use the `specifications` parameter to include model preferences and exact requirements.

### Is there a cost per quote?
The MCP itself is free. Actual equipment purchases are between you and the distributors.

## Links

- **PyPI:** [pypi.org/project/hvac-quotes-mcp](https://pypi.org/project/hvac-quotes-mcp/)
- **Claude Registry:** `io.github.wmarceau/hvac-quotes`
- **Source:** [github.com/wmarceau/hvac-quotes-mcp](https://github.com/wmarceau/hvac-quotes-mcp)

## License

MIT License - Free for personal and commercial use.
