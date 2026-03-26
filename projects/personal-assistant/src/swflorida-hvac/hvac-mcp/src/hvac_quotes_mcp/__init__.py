"""
HVAC Quotes MCP - Claude Desktop integration for HVAC equipment RFQ management

Provides tools for HVAC contractors to:
- Submit RFQs to distributors
- Check RFQ status
- Get and compare quotes
- Simulate quotes for testing

Usage:
    pip install hvac-quotes-mcp

    # In Claude Desktop config
    {
        "mcpServers": {
            "hvac-quotes": {
                "command": "hvac-quotes-mcp"
            }
        }
    }
"""

__version__ = "1.0.0"

from .models import (
    RFQ,
    Quote,
    RFQStatus,
    RFQSpecifications,
    Distributor,
    QuoteComparison,
    EquipmentType
)
from .rfq_manager import RFQManager, get_rfq_manager
from .server import HVACMCPServer, main

__all__ = [
    # Models
    'RFQ',
    'Quote',
    'RFQStatus',
    'RFQSpecifications',
    'Distributor',
    'QuoteComparison',
    'EquipmentType',
    # Manager
    'RFQManager',
    'get_rfq_manager',
    # Server
    'HVACMCPServer',
    'main',
    # Version
    '__version__',
]
