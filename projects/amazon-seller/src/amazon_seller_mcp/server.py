#!/usr/bin/env python3
"""
Amazon Seller Operations MCP Server

MCP (Model Context Protocol) server that provides Amazon seller tools
including inventory management, fee calculation, and optimization recommendations.

Registry: io.github.williammarceaujr/amazon-seller
"""

import asyncio
import json
import sys

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from .amazon_sp_api import AmazonSPAPI
    from .amazon_fee_calculator import FBAFeeCalculator
    from .amazon_inventory_optimizer import InventoryOptimizer
except ImportError as e:
    print(f"Error importing amazon modules: {e}", file=sys.stderr)
    sys.exit(1)


# Server instance
server = Server("amazon-seller")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        # Inventory Tools
        Tool(
            name="get_inventory_summary",
            description="""Get FBA inventory summary for your Amazon products.

Returns current inventory levels, inbound shipments, and product status.
Supports caching to minimize API calls (important for 2026 fee structure).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "asins": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ASINs to query. Leave empty for all inventory."
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Use cached data to save API calls (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_orders",
            description="""Get recent orders from your Amazon seller account.

Returns order information for sales analysis and velocity calculations.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Use cached data (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_order_items",
            description="""Get line items for a specific order.

Returns detailed item information including ASIN, quantity, and pricing.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Amazon Order ID (e.g., 111-1234567-1234567)"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="get_product_details",
            description="""Get product details including dimensions and competitive pricing.

Returns product information useful for fee calculations.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "asin": {
                        "type": "string",
                        "description": "Product ASIN"
                    }
                },
                "required": ["asin"]
            }
        ),

        # Fee Calculator Tools
        Tool(
            name="calculate_fba_fees",
            description="""Calculate comprehensive FBA fees for a product.

Includes 2026 fee structure:
- FBA fulfillment fees (size-tier based)
- Monthly storage fees (seasonal rates)
- Referral fees (category-based)
- Aged inventory surcharges
- Low inventory level fees""",
            inputSchema={
                "type": "object",
                "properties": {
                    "asin": {
                        "type": "string",
                        "description": "Product ASIN"
                    },
                    "price": {
                        "type": "number",
                        "description": "Selling price in USD"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category (affects referral fee). Options: default, electronics, furniture, home, toys, clothing, jewelry",
                        "default": "default"
                    },
                    "month": {
                        "type": "integer",
                        "description": "Month (1-12) for storage fee calculation. Affects peak season rates."
                    },
                    "units": {
                        "type": "integer",
                        "description": "Number of units (default: 1)",
                        "default": 1
                    },
                    "age_days": {
                        "type": "integer",
                        "description": "Age of inventory in days (affects aged inventory surcharge)",
                        "default": 0
                    },
                    "cost_per_unit": {
                        "type": "number",
                        "description": "Your cost per unit (for profit calculation)"
                    }
                },
                "required": ["asin", "price"]
            }
        ),
        Tool(
            name="estimate_profit_margin",
            description="""Estimate profit margin for a product after all Amazon fees.

Quick calculation of expected profit based on price and estimated fees.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "price": {
                        "type": "number",
                        "description": "Selling price in USD"
                    },
                    "cost": {
                        "type": "number",
                        "description": "Your cost per unit"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category",
                        "default": "default"
                    },
                    "weight_lbs": {
                        "type": "number",
                        "description": "Product weight in pounds",
                        "default": 1.0
                    }
                },
                "required": ["price", "cost"]
            }
        ),

        # Inventory Optimizer Tools
        Tool(
            name="suggest_restock_quantities",
            description="""Get intelligent reorder recommendations with cost-benefit analysis.

Analyzes:
- Current inventory levels
- Sales velocity
- Storage fee projections
- Stockout risk assessment
- Optimal reorder quantities""",
            inputSchema={
                "type": "object",
                "properties": {
                    "asin": {
                        "type": "string",
                        "description": "Product ASIN to analyze"
                    },
                    "lead_time_days": {
                        "type": "integer",
                        "description": "Days until new inventory arrives (default: 30)",
                        "default": 30
                    },
                    "target_days_supply": {
                        "type": "integer",
                        "description": "Target days of inventory to maintain (default: 60)",
                        "default": 60
                    }
                },
                "required": ["asin"]
            }
        ),
        Tool(
            name="analyze_sell_through_rate",
            description="""Analyze sales velocity and sell-through rate for a product.

Returns daily sales rate based on historical order data.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "asin": {
                        "type": "string",
                        "description": "Product ASIN"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to analyze (default: 30)",
                        "default": 30
                    }
                },
                "required": ["asin"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    try:
        if name == "get_inventory_summary":
            return await handle_inventory_summary(arguments)

        elif name == "get_orders":
            return await handle_get_orders(arguments)

        elif name == "get_order_items":
            return await handle_get_order_items(arguments)

        elif name == "get_product_details":
            return await handle_get_product_details(arguments)

        elif name == "calculate_fba_fees":
            return await handle_calculate_fees(arguments)

        elif name == "estimate_profit_margin":
            return await handle_estimate_profit(arguments)

        elif name == "suggest_restock_quantities":
            return await handle_restock_suggestion(arguments)

        elif name == "analyze_sell_through_rate":
            return await handle_sell_through_rate(arguments)

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "hint": "Check that your Amazon SP-API credentials are configured in .env"
            }, indent=2)
        )]


async def handle_inventory_summary(arguments: dict):
    """Get inventory summary."""
    api = AmazonSPAPI()
    asins = arguments.get("asins")
    use_cache = arguments.get("use_cache", True)

    inventory = api.get_inventory_summary(asins=asins, use_cache=use_cache)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "inventory": inventory,
            "api_calls_made": api.get_calls_count
        }, indent=2, default=str)
    )]


async def handle_get_orders(arguments: dict):
    """Get recent orders."""
    api = AmazonSPAPI()
    days_back = arguments.get("days_back", 7)
    use_cache = arguments.get("use_cache", True)

    orders = api.get_orders(days_back=days_back, use_cache=use_cache)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "order_count": len(orders) if orders else 0,
            "orders": orders,
            "api_calls_made": api.get_calls_count
        }, indent=2, default=str)
    )]


async def handle_get_order_items(arguments: dict):
    """Get order items."""
    api = AmazonSPAPI()
    order_id = arguments.get("order_id")

    if not order_id:
        return [TextContent(type="text", text="Error: order_id is required")]

    items = api.get_order_items(order_id, use_cache=True)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "order_id": order_id,
            "item_count": len(items) if items else 0,
            "items": items
        }, indent=2, default=str)
    )]


async def handle_get_product_details(arguments: dict):
    """Get product details."""
    api = AmazonSPAPI()
    asin = arguments.get("asin")

    if not asin:
        return [TextContent(type="text", text="Error: asin is required")]

    details = api.get_product_details(asin, use_cache=True)

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "asin": asin,
            "details": details
        }, indent=2, default=str)
    )]


async def handle_calculate_fees(arguments: dict):
    """Calculate comprehensive FBA fees."""
    asin = arguments.get("asin")
    price = arguments.get("price")

    if not asin or price is None:
        return [TextContent(type="text", text="Error: asin and price are required")]

    calculator = FBAFeeCalculator()

    result = calculator.calculate_comprehensive_fees(
        asin=asin,
        price=price,
        category=arguments.get("category", "default"),
        month=arguments.get("month"),
        units=arguments.get("units", 1),
        age_days=arguments.get("age_days", 0),
        cost_per_unit=arguments.get("cost_per_unit")
    )

    # Clean up for JSON serialization
    result_clean = {
        "asin": result["asin"],
        "price": result["price"],
        "size_tier": result["size_tier"],
        "fees": result["fees"],
        "profit": result["profit"],
        "api_calls_made": calculator.api.get_calls_count
    }

    return [TextContent(
        type="text",
        text=json.dumps(result_clean, indent=2, default=str)
    )]


async def handle_estimate_profit(arguments: dict):
    """Quick profit margin estimation."""
    price = arguments.get("price")
    cost = arguments.get("cost")

    if price is None or cost is None:
        return [TextContent(type="text", text="Error: price and cost are required")]

    category = arguments.get("category", "default")
    weight = arguments.get("weight_lbs", 1.0)

    # Quick fee estimation
    referral_rate = {
        "default": 0.15,
        "electronics": 0.08,
        "clothing": 0.17,
        "jewelry": 0.20
    }.get(category, 0.15)

    referral_fee = max(price * referral_rate, 0.30)

    # Estimate fulfillment fee based on weight
    if weight <= 1:
        fulfillment_fee = 4.07
    elif weight <= 2:
        fulfillment_fee = 4.66
    elif weight <= 3:
        fulfillment_fee = 5.83
    else:
        fulfillment_fee = 5.83 + ((weight - 3) * 0.16)

    # Storage estimate (monthly average)
    storage_fee = 0.50  # Rough estimate

    total_fees = referral_fee + fulfillment_fee + storage_fee
    profit = price - total_fees - cost
    margin = (profit / price) * 100 if price > 0 else 0
    roi = (profit / cost) * 100 if cost > 0 else 0

    return [TextContent(
        type="text",
        text=json.dumps({
            "price": price,
            "cost": cost,
            "estimated_fees": {
                "referral": round(referral_fee, 2),
                "fulfillment": round(fulfillment_fee, 2),
                "storage": round(storage_fee, 2),
                "total": round(total_fees, 2)
            },
            "profit_per_unit": round(profit, 2),
            "profit_margin_percent": round(margin, 1),
            "roi_percent": round(roi, 1),
            "note": "This is an estimate. Use calculate_fba_fees for precise calculation."
        }, indent=2)
    )]


async def handle_restock_suggestion(arguments: dict):
    """Get restock recommendations."""
    asin = arguments.get("asin")

    if not asin:
        return [TextContent(type="text", text="Error: asin is required")]

    optimizer = InventoryOptimizer()

    result = optimizer.recommend_reorder_quantity(
        asin=asin,
        lead_time_days=arguments.get("lead_time_days", 30),
        target_days_supply=arguments.get("target_days_supply", 60)
    )

    # Clean up for JSON serialization
    result_clean = {
        "asin": result["asin"],
        "recommended_quantity": result["recommended_quantity"],
        "current_inventory": result["current_inventory"],
        "days_until_stockout": round(result["days_until_stockout"], 1),
        "urgency": result["urgency"],
        "estimated_storage_cost": round(result["storage_cost"], 2),
        "api_calls_made": optimizer.api.get_calls_count
    }

    return [TextContent(
        type="text",
        text=json.dumps(result_clean, indent=2, default=str)
    )]


async def handle_sell_through_rate(arguments: dict):
    """Analyze sell-through rate."""
    asin = arguments.get("asin")

    if not asin:
        return [TextContent(type="text", text="Error: asin is required")]

    days = arguments.get("days", 30)

    optimizer = InventoryOptimizer()
    velocity = optimizer.calculate_sales_velocity(asin, days=days)

    # Get current inventory for context
    inventory = optimizer.get_current_inventory(asin)
    days_supply = inventory["available"] / velocity if velocity > 0 else 999

    return [TextContent(
        type="text",
        text=json.dumps({
            "asin": asin,
            "analysis_period_days": days,
            "daily_sales_rate": round(velocity, 2),
            "weekly_sales_rate": round(velocity * 7, 2),
            "monthly_sales_rate": round(velocity * 30, 2),
            "current_inventory": inventory["available"],
            "days_of_supply": round(days_supply, 1),
            "api_calls_made": optimizer.api.get_calls_count
        }, indent=2)
    )]


def main():
    """Run the MCP server."""
    asyncio.run(run_server())


async def run_server():
    """Async server runner."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    main()
