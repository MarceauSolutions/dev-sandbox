# Rideshare Comparison MCP

> Compare Uber and Lyft prices for any route via Claude Desktop

**Package:** `rideshare-comparison-mcp`
**Version:** 1.0.0
**Registry:** `io.github.wmarceau/rideshare-comparison`

## What does this MCP do?

The Rideshare Comparison MCP lets you compare Uber and Lyft prices for any route directly through Claude. Get price estimates, detect surge pricing, and get deep links to book your ride.

## Installation

```bash
pip install rideshare-comparison-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rideshare-comparison": {
      "command": "rideshare-comparison-mcp",
      "env": {
        "RIDESHARE_API_URL": "http://localhost:8000",
        "RIDESHARE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### compare_rideshare_prices
Compare Uber and Lyft prices for a specific route.

**Parameters:**
- `pickup_lat`, `pickup_lng`: Pickup location coordinates
- `dropoff_lat`, `dropoff_lng`: Dropoff location coordinates
- `pickup_address` (optional): Human-readable pickup address
- `dropoff_address` (optional): Human-readable dropoff address

### get_supported_cities
List cities with pricing data available.

### get_booking_link
Get a deep link to book a ride with Uber or Lyft.

## Example Prompts

Ask Claude:

> "Compare Uber and Lyft prices from SFO airport to downtown San Francisco"

> "Which is cheaper right now, Uber or Lyft, from Times Square to JFK?"

> "Get me a booking link for the cheaper option from my location to the airport"

> "Is there surge pricing on Uber right now in San Francisco?"

## Response Format

The comparison returns:
- **Summary:** Which service is cheaper and by how much
- **Uber estimate:** Price range, surge multiplier, booking link
- **Lyft estimate:** Price range, surge multiplier, booking link
- **Route info:** Distance, duration, city
- **Confidence score:** How accurate the estimate is

## Supported Cities

Major US metropolitan areas including:
- San Francisco Bay Area
- New York City
- Los Angeles
- Chicago
- Miami
- And many more

## FAQ

### How accurate are the price estimates?
Estimates are typically within 10-15% of actual prices. Surge pricing can cause larger variations.

### Does this book rides automatically?
No, it provides deep links. You complete the booking in the Uber or Lyft app.

### Can I use this for international cities?
Currently focused on US cities. International support planned.

### How often are prices updated?
Prices are fetched in real-time when you make a comparison request.

### Is surge pricing detected?
Yes, the comparison shows surge multipliers for both services.

## Links

- **PyPI:** [pypi.org/project/rideshare-comparison-mcp](https://pypi.org/project/rideshare-comparison-mcp/)
- **Claude Registry:** `io.github.wmarceau/rideshare-comparison`
- **Source:** [github.com/wmarceau/rideshare-comparison-mcp](https://github.com/wmarceau/rideshare-comparison-mcp)

## License

MIT License - Free for personal and commercial use.
