"""
amazon-seller-mcp: Amazon seller tools via MCP.

Tools:
- get_inventory_summary: FBA inventory levels
- get_orders: Recent order history
- calculate_fba_fees: Comprehensive fee calculation (2026 structure)
- estimate_profit_margin: Quick profit estimation
- suggest_restock_quantities: Intelligent reorder recommendations
- analyze_sell_through_rate: Sales velocity analysis
"""

__version__ = "1.0.0"

from .server import main

__all__ = [
    "main",
    "__version__",
]
