# Amazon Seller Operations

AI-powered Amazon Seller Central tools for inventory management, fee calculation, and optimization via SP-API.

mcp-name: io.github.wmarceau/amazon-seller

## Features

| Feature | Script | Description |
|---------|--------|-------------|
| SP-API Integration | `amazon_sp_api.py` | Core API with caching |
| FBA Fee Calculator | `amazon_fee_calculator.py` | 2026 fee structure |
| Inventory Optimizer | `amazon_inventory_optimizer.py` | Restock recommendations |
| OAuth Authentication | `amazon_oauth_server.py` | OAuth flow handling |
| MCP Server | `amazon_seller_mcp.py` | MCP protocol wrapper |

## Directory Structure

```
amazon-seller/
├── src/
│   ├── amazon_sp_api.py              # Core SP-API client
│   ├── amazon_fee_calculator.py      # FBA fee calculations
│   ├── amazon_inventory_optimizer.py # Restock recommendations
│   ├── amazon_oauth_server.py        # OAuth server
│   └── ...
├── mcp-server/
│   └── amazon_seller_mcp.py          # MCP server wrapper
├── registry/
│   └── manifest.json                 # MCP Registry manifest
├── VERSION                           # Current version
├── CHANGELOG.md                      # Version history
├── SKILL.md                          # MCP tool documentation
└── README.md                         # This file
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_inventory_summary` | Get FBA inventory levels |
| `get_orders` | Get recent orders |
| `get_order_items` | Get order line items |
| `get_product_details` | Get product info |
| `calculate_fba_fees` | Calculate comprehensive fees |
| `estimate_profit_margin` | Quick profit estimation |
| `suggest_restock_quantities` | Reorder recommendations |
| `analyze_sell_through_rate` | Sales velocity analysis |

See [SKILL.md](SKILL.md) for detailed tool documentation.

## Quick Start

### 1. Install Dependencies
```bash
pip install python-amazon-sp-api python-dotenv mcp
```

### 2. Configure Credentials
Create `.env` file:
```env
AMAZON_REFRESH_TOKEN=your_refresh_token
AMAZON_LWA_APP_ID=your_client_id
AMAZON_LWA_CLIENT_SECRET=your_client_secret
AMAZON_AWS_ACCESS_KEY=your_aws_access_key
AMAZON_AWS_SECRET_KEY=your_aws_secret_key
AMAZON_ROLE_ARN=arn:aws:iam::123456789:role/your-role
AMAZON_MARKETPLACE_ID=ATVPDKIKX0DER
```

### 3. Test Connection
```bash
python src/test_amazon_connection.py
```

### 4. Run MCP Server
```bash
python mcp-server/amazon_seller_mcp.py
```

## CLI Usage

### Calculate Fees
```bash
python src/amazon_fee_calculator.py --asin B08XYZ123 --price 29.99 --cost 10.00
```

### Get Inventory Recommendations
```bash
python src/amazon_inventory_optimizer.py --asin B08XYZ123 --days 30
```

## Key Features

### 2026 Fee Structure
- FBA fulfillment fees (size-tier based)
- Monthly storage fees (seasonal rates)
- Aged inventory surcharges (12-15mo, 15+mo)
- Low inventory level fees
- GET call fee awareness (post April 2026)

### Caching Layer
Aggressive caching to minimize API costs:
- Inventory: 30 min
- Orders: 15 min
- Products: 24 hours
- Fees: 24 hours

### Multi-Marketplace
Supports US, CA, MX, BR, UK, DE, FR, IT, ES, NL, JP, SG, AU

## Version

Current version: 1.0.0

## License

MIT License
