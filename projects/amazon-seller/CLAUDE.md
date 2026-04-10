# Amazon Seller Operations

## What This Does
AI-powered Amazon Seller Central tools for inventory management, FBA fee calculation (2026 fee structure), and restock optimization via SP-API. Published as an MCP server (`io.github.wmarceau/amazon-seller`) for Claude Desktop integration.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/amazon-seller

# Test SP-API connection
python src/test_amazon_connection.py

# Calculate FBA fees
python src/amazon_fee_calculator.py --asin B08XYZ123 --price 29.99 --cost 10.00

# Get inventory/restock recommendations
python src/amazon_inventory_optimizer.py --asin B08XYZ123 --days 30

# Run MCP server
python mcp-server/amazon_seller_mcp.py

# OAuth token refresh
python src/refresh_amazon_token.py
```

## Architecture
- **`src/amazon_sp_api.py`** - Core SP-API client with response caching
- **`src/amazon_fee_calculator.py`** - 2026 FBA fee structure (size-tier based fulfillment, storage, aged inventory surcharges, low inventory fees)
- **`src/amazon_inventory_optimizer.py`** - Restock quantity recommendations based on sell-through rate
- **`src/amazon_oauth_server.py`** - OAuth flow handling for SP-API authentication
- **`src/refresh_amazon_token.py`** - Token refresh utility
- **`src/test_amazon_connection.py`** + **`src/test_sp_api_simple.py`** - Connection verification
- **`src/amazon_seller_mcp/`** - MCP package directory (for PyPI publishing)
- **`mcp-server/amazon_seller_mcp.py`** - MCP server wrapper exposing 8 tools
- **`pyproject.toml`** + **`server.json`** - MCP Registry publishing config

## MCP Tools Available
| Tool | Description |
|------|-------------|
| `get_inventory_summary` | FBA inventory levels |
| `get_orders` | Recent orders |
| `get_order_items` | Order line items |
| `get_product_details` | Product info by ASIN |
| `calculate_fba_fees` | Comprehensive fee breakdown |
| `estimate_profit_margin` | Quick profit estimation |
| `suggest_restock_quantities` | Reorder recommendations |
| `analyze_sell_through_rate` | Sales velocity analysis |

## Project-Specific Rules
- SP-API credentials stored in root `.env` (`AMAZON_REFRESH_TOKEN`, `AMAZON_LWA_APP_ID`, etc.)
- GET call fee awareness post-April 2026 -- minimize unnecessary API calls
- Fee calculator uses 2026 rate cards (seasonal storage rates, aged inventory surcharges at 12-15mo and 15+mo)
- MCP name: `io.github.wmarceau/amazon-seller` (registered on PyPI and MCP Registry)
- Legal documents in `LegalAgreement/` and `BJKPaperTrail/`

## Relevant SOPs
- SOP 14: MCP Update & Version Bump (for publishing updates)
- SOPs 11-13: MCP Package Structure, PyPI, Registry (initial publish)
- SOP 3: Version Control & Deployment
- Testing: `docs/testing-strategy.md`
