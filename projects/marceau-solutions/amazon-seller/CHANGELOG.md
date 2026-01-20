# Changelog

All notable changes to the Amazon Seller Operations project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-13

### Added
- MCP server wrapper (`mcp-server/amazon_seller_mcp.py`)
- Eight MCP tools:
  - `get_inventory_summary` - FBA inventory levels
  - `get_orders` - Recent order retrieval
  - `get_order_items` - Order line items
  - `get_product_details` - Product info and dimensions
  - `calculate_fba_fees` - Comprehensive fee breakdown
  - `estimate_profit_margin` - Profit analysis
  - `suggest_restock_quantities` - Reorder recommendations
  - `analyze_sell_through_rate` - Sales velocity analysis
- Registry manifest for MCP Registry submission
- SKILL.md documentation

### Features (from initial development)
- Amazon SP-API integration with OAuth authentication
- FBA fee calculator with 2026 fee structure
- Inventory optimizer with cost-benefit analysis
- Multi-marketplace support
- Caching layer to minimize API calls (cost optimization)
- Rate limiting aware of 2026 GET call fees

---

[Unreleased]: https://github.com/williammarceaujr/amazon-seller/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/williammarceaujr/amazon-seller/releases/tag/v1.0.0
