# Amazon Seller MCP

> Manage Amazon Seller Central operations via Claude Desktop

**Package:** `amazon-seller-mcp`
**Version:** 1.0.0
**Registry:** `io.github.wmarceau/amazon-seller`

## What does this MCP do?

The Amazon Seller MCP connects Claude Desktop to Amazon's Selling Partner API (SP-API), enabling you to manage your Amazon seller account through natural language conversations.

## Installation

```bash
pip install amazon-seller-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "amazon-seller": {
      "command": "amazon-seller-mcp",
      "env": {
        "AMAZON_REFRESH_TOKEN": "your-refresh-token",
        "AMAZON_LWA_APP_ID": "your-app-id",
        "AMAZON_LWA_CLIENT_SECRET": "your-client-secret",
        "AMAZON_MARKETPLACE_ID": "ATVPDKIKX0DER"
      }
    }
  }
}
```

## Available Tools

### get_inventory
Check inventory levels for your products.

### get_orders
Retrieve recent orders with filtering options.

### update_listing
Update product listings (price, quantity, description).

### get_sales_report
Generate sales analytics reports.

## Example Prompts

Ask Claude:

> "What's my current inventory level for ASIN B08XYZ123?"

> "Show me all orders from the last 7 days"

> "Update the price of my product to $24.99"

> "Generate a sales report for this month"

## Prerequisites

You need an Amazon Seller Central account with SP-API credentials:

1. Register as a developer in Seller Central
2. Create an SP-API application
3. Generate LWA credentials
4. Obtain a refresh token

See Amazon's [SP-API documentation](https://developer-docs.amazon.com/sp-api/) for setup instructions.

## Supported Marketplaces

| Marketplace | ID |
|-------------|-----|
| US | ATVPDKIKX0DER |
| Canada | A2EUQ1WTGCTBG2 |
| UK | A1F83G8C2ARO7P |
| Germany | A1PA6795UKMFR9 |

## FAQ

### Do I need an Amazon Professional Seller account?
Yes, SP-API access requires a Professional seller account.

### Is my data secure?
All API calls are made directly from your machine. Credentials never leave your environment.

### Can I manage multiple marketplaces?
Yes, configure different marketplace IDs for each region.

### What permissions are required?
The MCP requires read/write access to inventory, orders, and listings.

## Links

- **PyPI:** [pypi.org/project/amazon-seller-mcp](https://pypi.org/project/amazon-seller-mcp/)
- **Claude Registry:** `io.github.wmarceau/amazon-seller`
- **Source:** [github.com/wmarceau/amazon-seller-mcp](https://github.com/wmarceau/amazon-seller-mcp)

## License

MIT License - Free for personal and commercial use.
