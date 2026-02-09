"""
Rideshare Comparison MCP - Compare Uber and Lyft prices

This MCP server provides tools for comparing rideshare prices
and generating booking deep links.
"""

__version__ = "1.0.0"

from .server import RideshareMCPServer, main

__all__ = ["RideshareMCPServer", "main", "__version__"]
