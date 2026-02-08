# Rideshare Comparison MCP

mcp-name: io.github.wmarceau/rideshare-comparison

Compare Uber and Lyft prices for any route using Claude Desktop.

## Installation

```bash
pip install rideshare-comparison-mcp
```

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rideshare-comparison": {
      "command": "python",
      "args": ["-m", "rideshare_comparison_mcp"],
      "env": {
        "RIDESHARE_API_URL": "http://your-api-url",
        "RIDESHARE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### compare_rideshare_prices
Compare Uber and Lyft prices for a specific route.

**Example prompt:** "Compare Uber and Lyft prices from SFO airport to downtown San Francisco"

### get_supported_cities
Get a list of cities with rideshare pricing data.

**Example prompt:** "Which cities are supported for rideshare comparison?"

### get_booking_link
Get a deep link to book a ride directly in the Uber or Lyft app.

**Example prompt:** "Get me a booking link for Uber from my location to the airport"

## Features

- Real-time price comparison between Uber and Lyft
- Surge pricing detection
- Deep links for instant booking
- Support for major US cities
- Distance and duration estimates

## License

MIT
