# Amazon Seller Operations MCP

Comprehensive Amazon seller tools for inventory management, fee calculation, and optimization.

## Registry Information

- **Namespace**: `io.github.williammarceaujr/amazon-seller`
- **Category**: E-commerce
- **Connectivity**: HTTP (requires Amazon SP-API credentials)
- **Authentication**: OAuth 2.0 (Amazon Login with Amazon)

## Tools

### Inventory Management

#### `get_inventory_summary`
Get FBA inventory levels for your products.

**Input**:
- `asins` (array, optional): List of ASINs to query
- `use_cache` (boolean, default: true): Use cached data

**Output**: Inventory data with available and inbound quantities

#### `get_orders`
Get recent orders from your seller account.

**Input**:
- `days_back` (integer, default: 7): Days to look back
- `use_cache` (boolean, default: true): Use cached data

**Output**: Order list with status and amounts

#### `get_order_items`
Get line items for a specific order.

**Input**:
- `order_id` (string, required): Amazon Order ID

**Output**: Order items with ASINs, quantities, pricing

#### `get_product_details`
Get product information including dimensions.

**Input**:
- `asin` (string, required): Product ASIN

**Output**: Product details for fee calculations

### Fee Calculation

#### `calculate_fba_fees`
Calculate comprehensive FBA fees with 2026 fee structure.

**Input**:
- `asin` (string, required): Product ASIN
- `price` (number, required): Selling price in USD
- `category` (string, optional): Product category
- `month` (integer, optional): Month for seasonal storage rates
- `units` (integer, default: 1): Number of units
- `age_days` (integer, default: 0): Inventory age
- `cost_per_unit` (number, optional): Your cost for profit calc

**Output**:
```json
{
  "fees": {
    "fulfillment": 4.66,
    "storage": 0.43,
    "referral": 4.50,
    "aged_inventory": 0.00,
    "low_inventory": 0.00,
    "total_per_unit": 9.59
  },
  "profit": {
    "revenue_per_unit": 20.41,
    "profit_per_unit": 10.41,
    "margin_percent": 34.7
  }
}
```

#### `estimate_profit_margin`
Quick profit estimation without API calls.

**Input**:
- `price` (number, required): Selling price
- `cost` (number, required): Your cost per unit
- `category` (string, optional): Product category
- `weight_lbs` (number, default: 1.0): Product weight

**Output**: Estimated fees, profit, and ROI

### Inventory Optimization

#### `suggest_restock_quantities`
Intelligent reorder recommendations with cost-benefit analysis.

**Input**:
- `asin` (string, required): Product ASIN
- `lead_time_days` (integer, default: 30): Shipping lead time
- `target_days_supply` (integer, default: 60): Target inventory days

**Output**:
```json
{
  "recommended_quantity": 150,
  "current_inventory": 45,
  "days_until_stockout": 15.2,
  "urgency": "HIGH",
  "estimated_storage_cost": 12.50
}
```

#### `analyze_sell_through_rate`
Calculate sales velocity for demand planning.

**Input**:
- `asin` (string, required): Product ASIN
- `days` (integer, default: 30): Analysis period

**Output**: Daily/weekly/monthly sales rates and days of supply

## Features

### 2026 Fee Structure Support
- FBA fulfillment fees (size-tier based)
- Monthly storage fees (Jan-Sep vs Oct-Dec peak)
- Aged inventory surcharges (12-15mo, 15+mo)
- Low inventory level fees
- GET call fee awareness (post April 2026)

### Caching Layer
Aggressive caching to minimize API calls (cost optimization):
- Inventory: 30 min cache
- Orders: 15 min cache
- Product details: 24 hour cache
- Fee data: 24 hour cache

### Multi-Marketplace Support
- US (ATVPDKIKX0DER) - default
- Canada, Mexico, Brazil
- UK, Germany, France, Italy, Spain, Netherlands
- Japan, Singapore, Australia

## Dependencies

- Python 3.8+
- `python-amazon-sp-api`: SP-API library
- `python-dotenv`: Environment management
- `mcp`: MCP SDK

## Installation

```bash
pip install python-amazon-sp-api python-dotenv mcp
```

## Configuration

Create `.env` file with Amazon SP-API credentials:

```env
AMAZON_REFRESH_TOKEN=your_refresh_token
AMAZON_LWA_APP_ID=your_client_id
AMAZON_LWA_CLIENT_SECRET=your_client_secret
AMAZON_AWS_ACCESS_KEY=your_aws_access_key
AMAZON_AWS_SECRET_KEY=your_aws_secret_key
AMAZON_ROLE_ARN=arn:aws:iam::123456789:role/your-role
AMAZON_MARKETPLACE_ID=ATVPDKIKX0DER
```

### Getting SP-API Credentials

1. Register as Amazon developer: https://developer.amazonservices.com/
2. Create SP-API application in Seller Central
3. Set up IAM role and policies in AWS
4. Run OAuth flow to get refresh token

## Running the Server

```bash
python mcp-server/amazon_seller_mcp.py
```

## Example Usage

```python
# Via MCP client
result = await client.call_tool("calculate_fba_fees", {
    "asin": "B08XYZ123",
    "price": 29.99,
    "cost_per_unit": 10.00,
    "category": "home"
})

# Get restock recommendation
restock = await client.call_tool("suggest_restock_quantities", {
    "asin": "B08XYZ123",
    "lead_time_days": 21,
    "target_days_supply": 45
})
```

## Integration

This MCP integrates with the MCP Aggregator platform:

```python
# Via MCP Aggregator
await aggregator.route({
    "category": "E_COMMERCE",
    "tool": "calculate_fba_fees",
    "params": {...}
})
```

## Revenue Model

- **Market**: Amazon seller tools (massive market)
- **Moat**: SP-API complexity, 2026 fee structure expertise
- **Value**: Cost savings through fee optimization
