# Amazon Seller Tower Directive

## Domain
Amazon marketplace operations: SP-API integration, inventory management, fee calculation, and seller operations.

## Core Capabilities
- **SP-API Integration**: Amazon Selling Partner API wrapper
- **Fee Calculator**: FBA/FBM fee estimation and comparison
- **Inventory Optimizer**: Stock level recommendations
- **OAuth Server**: Amazon API authentication flow
- **MCP Server**: Amazon seller operations as MCP tools

## Entry Point
- No Flask app yet (skeleton tower)
- CLI: `python -m projects.amazon_seller.src.[script]`

## Integration Points
- **Standalone**: No dependencies on other towers
- **Future**: Could feed inventory data to lead-generation for product-market research

## Current Status
1.0.0-dev — SP-API wrappers and fee calculator exist. No active Amazon business. Tower is dormant until an Amazon SKU is activated.

## Current Version
1.0.0-dev
