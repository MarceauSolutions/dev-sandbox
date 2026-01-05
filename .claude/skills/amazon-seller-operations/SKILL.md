---
name: amazon-seller-operations
description: Provide natural language interface to Amazon Seller Central via SP-API for inventory management, cost optimization, review management, and seller operations.
allowed-tools: ["Bash(python:*)"]
---

# Amazon Seller Operations

## Overview

This skill was deployed from the DOE development environment.

**Source Directive:** `directives/amazon_seller_operations.md`

Provide natural language interface to Amazon Seller Central via SP-API for inventory management, cost optimization, review management, and seller operations.

## When to use

This skill is automatically triggered based on the description above. Claude will detect when your request matches this skill's capabilities.

## Execution Scripts

This skill uses the following execution scripts:

- `execution/amazon_sp_api.py` - Base SP-API wrapper with authentication
- `execution/amazon_inventory_optimizer.py` - Inventory reorder recommendations (COMPLETE ✓)
- `execution/amazon_fee_calculator.py` - FBA fee calculator with 2026 structure (COMPLETE ✓)
- `execution/amazon_get_refresh_token.py` - OAuth token management
- `execution/amazon_oauth_server.py` - OAuth authorization flow

**Status:**
- ✅ Inventory optimization - Fully implemented
- ✅ Fee calculator - Fully implemented (includes 2026 fee structure)
- ⏳ Review monitor - Planned
- ⏳ Listing manager - Planned


## Instructions

For detailed implementation instructions, refer to the source directive:

**Directive:** [amazon_seller_operations.md](../../directives/amazon_seller_operations.md)

The directive contains:
- Goal and purpose
- Input requirements
- Step-by-step process
- Output format
- Edge cases and error handling
- API considerations
- Best practices

## Usage

python execution scripts

## Deployment Information

- **Deployed:** 2026-01-05 10:48:36
- **Source:** DOE development environment
- **Status:** Production-ready

## Notes

This skill references the directive in `directives/` for complete documentation.
All execution logic is in deterministic Python scripts in `execution/`.

Intermediate files are stored in `.tmp/` and are not committed to version control.
