# HVAC Distributor RFQ System

Submit RFQs (Request for Quote) to HVAC equipment distributors and compare quotes to find the best deals.

## Quick Start

```bash
# Run demo to see full workflow
python src/hvac_cli.py demo

# Submit an RFQ
python src/hvac_cli.py submit --type ac_unit --address "Naples, FL" --tonnage 3 --seer 16

# Check status
python src/hvac_cli.py status <RFQ_ID>

# Simulate a quote (for testing)
python src/hvac_cli.py simulate <RFQ_ID> --price 2500

# Get quotes
python src/hvac_cli.py quotes <RFQ_ID>

# Compare quotes
python src/hvac_cli.py compare <RFQ_ID1> <RFQ_ID2> <RFQ_ID3>
```

## Features

- **Submit RFQs** to multiple distributors at once
- **Track status** of pending RFQs
- **Compare quotes** by price, delivery time, and total value
- **Mock email mode** for testing without SMTP

## Equipment Types

| Type | CLI Value | Description |
|------|-----------|-------------|
| Air Conditioner | `ac_unit` | Central AC units |
| Furnace | `furnace` | Gas/electric furnaces |
| Heat Pump | `heat_pump` | Heat pump systems |
| Rooftop Unit | `rooftop_unit` | Commercial units |
| Mini-Split | `mini_split` | Ductless systems |
| Boiler | `boiler` | Hot water boilers |
| Chiller | `chiller` | Commercial chillers |
| Air Handler | `air_handler` | Air handling units |

## Specifications

When submitting an RFQ, you can include:

| Option | Type | Example |
|--------|------|---------|
| `--tonnage` | float | 3, 4, 5 |
| `--seer` | int | 14, 16, 18, 20 |
| `--btu` | int | 80000 |
| `--voltage` | string | "208-230V" |
| `--brand` | string | "Carrier", "Trane" |
| `--quantity` | int | 2 |
| `--needed-by` | date | "2026-01-25" |

## Project Structure

```
hvac-distributors/
├── SKILL.md           # Skill definition
├── README.md          # This file
├── VERSION            # Version number
├── CHANGELOG.md       # Version history
├── workflows/         # Task procedures
└── src/
    ├── hvac_cli.py        # CLI interface
    ├── hvac_mcp.py        # MCP server for Claude Desktop
    ├── rfq_manager.py     # Core business logic
    ├── models.py          # Data models
    ├── distributor_db.py  # Distributor database
    ├── quote_tracker.py   # RFQ/quote tracking
    ├── email_sender.py    # SMTP email sending
    └── email_receiver.py  # IMAP quote polling
```

## Claude Desktop Integration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "hvac-distributors": {
      "command": "python",
      "args": ["/path/to/hvac-distributors/src/hvac_mcp.py"],
      "env": {
        "HVAC_MOCK_EMAIL": "true"
      }
    }
  }
}
```

## Current Mode

Running in **mock email mode** - RFQs are logged but not actually sent via SMTP. Use `simulate` command to test the quote comparison workflow.

## Response Times

| Scenario | Expected Time |
|----------|---------------|
| In-stock items | 4-8 hours |
| Standard requests | 24-48 hours |
| Special orders | 3-5 business days |

---

**Version**: 1.0.0-dev
