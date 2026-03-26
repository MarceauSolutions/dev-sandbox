# Ticket Discovery MCP

mcp-name: io.github.wmarceau/ticket-discovery

An MCP server that helps AI agents discover, search, and compare concert and event ticket prices across multiple platforms.

## Features

- **Multi-Platform Search**: Query Ticketmaster and SeatGeek simultaneously
- **Price Comparison**: Compare prices across platforms for the same event
- **Smart Filtering**: Filter by artist, city, state, date range, and max price
- **Affiliate Ready**: Built-in support for affiliate link tracking
- **100% Legal**: Uses only official public APIs - no scraping or automation

## Tools Available

| Tool | Description |
|------|-------------|
| `search_events` | Search for events across all platforms |
| `compare_prices` | Compare ticket prices for a specific event |
| `get_event_details` | Get detailed info about a specific event |
| `get_upcoming_events` | Find upcoming events for an artist |
| `find_cheap_tickets` | Find tickets under a specific price |
| `check_api_status` | Verify which APIs are configured |

## Installation

```bash
pip install ticket-discovery-mcp
```

Or install from source:

```bash
git clone https://github.com/wmarceau/ticket-discovery-mcp
cd ticket-discovery-mcp
pip install -e .
```

## Configuration

### Get API Keys (Free)

1. **Ticketmaster**: Get a free API key at [developer.ticketmaster.com](https://developer.ticketmaster.com/)
2. **SeatGeek**: Get a free client ID at [seatgeek.com/account/develop](https://seatgeek.com/account/develop)

### Set Environment Variables

```bash
export TICKETMASTER_API_KEY="your-ticketmaster-key"
export SEATGEEK_CLIENT_ID="your-seatgeek-client-id"
export SEATGEEK_CLIENT_SECRET="your-seatgeek-secret"  # Optional

# For affiliate commissions (optional)
export SEATGEEK_AFFILIATE_ID="your-affiliate-id"
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ticket-discovery": {
      "command": "ticket-discovery-mcp",
      "env": {
        "TICKETMASTER_API_KEY": "your-key",
        "SEATGEEK_CLIENT_ID": "your-client-id"
      }
    }
  }
}
```

## Usage Examples

### Search for Events

```
User: Find Kendrick Lamar concerts in Florida

AI uses: search_events(query="Kendrick Lamar", state="FL")
```

### Compare Prices

```
User: Compare ticket prices for Taylor Swift in Miami on March 15

AI uses: compare_prices(
    event_name="Taylor Swift",
    date="2026-03-15",
    city="Miami",
    state="FL"
)
```

### Find Cheap Tickets

```
User: Find concert tickets under $100 in New York this month

AI uses: find_cheap_tickets(
    event_name="concert",
    max_price=100,
    state="NY",
    start_date="2026-02-01",
    end_date="2026-02-28"
)
```

## API Rate Limits

| Platform | Free Tier Limit |
|----------|-----------------|
| Ticketmaster | 5,000 calls/day |
| SeatGeek | 1,000 calls/hour |

## Legal Notice

This MCP uses only official, public APIs provided by ticket platforms. It does NOT:
- Automate ticket purchasing (prohibited by BOTS Act)
- Scrape ticket websites (ToS violation)
- Bypass security measures (illegal)

Users complete purchases on the official platform websites.

## Monetization

This MCP supports affiliate links. When users click through to purchase, you can earn:
- **SeatGeek**: ~$11 average per sale
- **StubHub**: 9% commission (via Partnerize)
- **Vivid Seats**: 4-6% commission

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.
