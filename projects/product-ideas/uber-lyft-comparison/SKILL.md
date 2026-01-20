# Uber/Lyft Price Comparison MCP

Compare rideshare prices between Uber and Lyft using proprietary rate card algorithm.

## Overview

This MCP server provides real-time price comparison between Uber and Lyft services using locally-stored rate card data. Unlike scraping or unofficial API access, this approach uses publicly available rate information to estimate prices accurately.

## Tools

### compare_prices
Get price estimates for both Uber and Lyft services.

**Parameters:**
- `origin` (string): Pickup location (address or place name)
- `destination` (string): Drop-off location (address or place name)
- `service_type` (optional): Filter by service type (e.g., "UberX", "Lyft", "UberXL")

**Returns:**
- Price estimates for available services
- Estimated travel time and distance
- Deep links to book directly in each app

### get_deep_link
Generate booking links for Uber or Lyft apps.

**Parameters:**
- `provider` (string): "uber" or "lyft"
- `origin` (string): Pickup location
- `destination` (string): Drop-off location

**Returns:**
- Universal deep link that opens the correct app
- Web fallback URL if app not installed

## Integration

This service connects to the MCP Aggregator platform:
- **Category**: TRANSPORTATION
- **Connectivity**: HTTP (real-time)
- **Latency**: <500ms typical
- **Revenue Model**: Affiliate commission per booking

## Data Sources

Rate card data stored in `data/` directory:
- `uber-rates-naples.csv` - Uber rate cards for Naples, FL
- `lyft-rates-naples.csv` - Lyft rate cards for Naples, FL
- `test-routes.csv` - Validation routes for accuracy testing

## Architecture

```
uber-lyft-comparison/
├── src/
│   ├── comparison.py    # RideshareComparison class
│   ├── rate_cards.py    # Rate card database
│   ├── deep_links.py    # Deep linking utilities
│   └── __init__.py
├── mcp-server/
│   └── rideshare_mcp.py # MCP server implementation
├── data/                # Rate card CSVs
├── testing/
│   └── accuracy/        # Accuracy validation tests
└── workflows/           # Task procedures
```

## Usage Example

```python
from src.comparison import RideshareComparison

comparison = RideshareComparison()
result = comparison.compare(
    origin="Naples Airport",
    destination="Downtown Naples"
)

print(f"Uber: ${result.uber.price:.2f}")
print(f"Lyft: ${result.lyft.price:.2f}")
print(f"Savings: ${abs(result.uber.price - result.lyft.price):.2f}")
```

## Registration

This MCP server is registered on the official MCP Registry:
- **Namespace**: `io.github.williammarceaujr/rideshare-comparison`
- **Registry**: https://registry.modelcontextprotocol.io/
