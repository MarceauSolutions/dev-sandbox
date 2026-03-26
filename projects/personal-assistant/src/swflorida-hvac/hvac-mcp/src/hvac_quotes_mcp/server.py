#!/usr/bin/env python3
"""
HVAC Quotes MCP Server

MCP server for Claude Desktop integration.
Provides tools for contractors to manage HVAC equipment RFQs.

This MCP validates the platform's support for:
- EMAIL connectivity (not HTTP REST API)
- ASYNC scoring (24-48 hour response times)
- Per-RFQ billing

Tools:
- submit_rfq: Send RFQ to HVAC distributors
- check_rfq_status: Check status of submitted RFQ
- get_quotes: Get quotes received for an RFQ
- compare_quotes: Compare quotes from multiple distributors
- simulate_quote: (Testing) Simulate a quote response

Usage in Claude Desktop config:
{
    "mcpServers": {
        "hvac-quotes": {
            "command": "hvac-quotes-mcp",
            "env": {
                "HVAC_MOCK_EMAIL": "true"
            }
        }
    }
}
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional

from .rfq_manager import RFQManager, get_rfq_manager
from .models import EquipmentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# MCP Protocol constants
JSONRPC_VERSION = "2.0"


class HVACMCPServer:
    """
    MCP Server for HVAC Distributor services.

    Implements the Model Context Protocol for Claude Desktop integration.
    Uses stdio transport (read from stdin, write to stdout).

    Key difference from rideshare MCP:
    - No HTTP API calls - uses email for distributor communication
    - Async workflow - responses take hours, not milliseconds
    - Per-RFQ billing instead of per-request
    """

    def __init__(self):
        self.rfq_manager: Optional[RFQManager] = None
        self._initialized = False

    async def start(self):
        """Initialize the server"""
        self.rfq_manager = get_rfq_manager()
        self._initialized = True
        logger.info("HVAC MCP Server started")
        logger.info("Mock email mode: ON (set HVAC_MOCK_EMAIL=false for real SMTP)")

    async def stop(self):
        """Stop the server"""
        self._initialized = False
        logger.info("HVAC MCP Server stopped")

    def get_server_info(self) -> dict:
        """Return server capabilities"""
        return {
            "name": "hvac-quotes",
            "version": "1.0.0",
            "description": "HVAC equipment RFQ management - submit quotes to distributors and compare responses",
            "protocolVersion": "2024-11-05"
        }

    def get_tools(self) -> list:
        """Return available tools"""
        equipment_types = [e.value for e in EquipmentType]

        return [
            {
                "name": "submit_rfq",
                "description": (
                    "Submit a Request for Quote (RFQ) to HVAC equipment distributors. "
                    "RFQs are sent via email to distributors who match your region and equipment needs. "
                    "Expect responses within 24-48 hours. Returns RFQ IDs for tracking."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "equipment_type": {
                            "type": "string",
                            "enum": equipment_types,
                            "description": "Type of HVAC equipment needed"
                        },
                        "delivery_address": {
                            "type": "string",
                            "description": "Full delivery address including city and state"
                        },
                        "specifications": {
                            "type": "object",
                            "description": "Equipment specifications",
                            "properties": {
                                "tonnage": {
                                    "type": "number",
                                    "description": "AC/heat pump size in tons (e.g., 2, 3, 4, 5)"
                                },
                                "seer": {
                                    "type": "integer",
                                    "description": "SEER efficiency rating (e.g., 14, 16, 18, 20)"
                                },
                                "btu": {
                                    "type": "integer",
                                    "description": "Heating capacity in BTU"
                                },
                                "voltage": {
                                    "type": "string",
                                    "description": "Required voltage (e.g., '208-230V', '460V')"
                                },
                                "refrigerant": {
                                    "type": "string",
                                    "description": "Refrigerant type (e.g., 'R-410A', 'R-32')"
                                },
                                "additional_notes": {
                                    "type": "string",
                                    "description": "Any additional requirements or notes"
                                }
                            }
                        },
                        "brand_preference": {
                            "type": "string",
                            "description": "Preferred brand (e.g., 'Carrier', 'Trane', 'Lennox')"
                        },
                        "quantity": {
                            "type": "integer",
                            "default": 1,
                            "description": "Number of units needed"
                        },
                        "needed_by_date": {
                            "type": "string",
                            "format": "date",
                            "description": "When equipment is needed (YYYY-MM-DD)"
                        }
                    },
                    "required": ["equipment_type", "delivery_address"]
                }
            },
            {
                "name": "check_rfq_status",
                "description": (
                    "Check the status of a submitted RFQ. "
                    "Shows whether quotes have been received and RFQ expiration status."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rfq_id": {
                            "type": "string",
                            "description": "The RFQ ID returned from submit_rfq"
                        }
                    },
                    "required": ["rfq_id"]
                }
            },
            {
                "name": "get_quotes",
                "description": (
                    "Get all quotes received for an RFQ. "
                    "Returns pricing, availability, and lead time from distributors."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rfq_id": {
                            "type": "string",
                            "description": "The RFQ ID"
                        }
                    },
                    "required": ["rfq_id"]
                }
            },
            {
                "name": "compare_quotes",
                "description": (
                    "Compare quotes from multiple distributors. "
                    "Identifies best price, fastest delivery, and recommended option."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rfq_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of RFQ IDs to compare quotes from"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["price", "lead_time", "total_value"],
                            "default": "total_value",
                            "description": "How to rank quotes"
                        }
                    },
                    "required": ["rfq_ids"]
                }
            },
            {
                "name": "simulate_quote",
                "description": (
                    "TESTING ONLY: Simulate a quote response from a distributor. "
                    "Use this to test the quote comparison workflow without waiting for real email responses."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rfq_id": {
                            "type": "string",
                            "description": "The RFQ to simulate a response for"
                        },
                        "unit_price": {
                            "type": "number",
                            "description": "Simulated unit price"
                        },
                        "lead_time_days": {
                            "type": "integer",
                            "default": 5,
                            "description": "Simulated lead time in days"
                        },
                        "quantity_available": {
                            "type": "integer",
                            "default": 10,
                            "description": "Simulated quantity in stock"
                        }
                    },
                    "required": ["rfq_id", "unit_price"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        if not self._initialized:
            await self.start()

        try:
            if name == "submit_rfq":
                return await self._submit_rfq(arguments)
            elif name == "check_rfq_status":
                return await self._check_rfq_status(arguments)
            elif name == "get_quotes":
                return await self._get_quotes(arguments)
            elif name == "compare_quotes":
                return await self._compare_quotes(arguments)
            elif name == "simulate_quote":
                return await self._simulate_quote(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"error": str(e)}

    async def _submit_rfq(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Submit RFQ to distributors"""
        from datetime import date

        # Parse needed_by_date if provided
        needed_by = None
        if args.get('needed_by_date'):
            try:
                needed_by = date.fromisoformat(args['needed_by_date'])
            except ValueError:
                pass

        result = self.rfq_manager.submit_rfq(
            contractor_id=args.get('contractor_id', 'default-contractor'),
            equipment_type=args['equipment_type'],
            delivery_address=args['delivery_address'],
            specifications=args.get('specifications', {}),
            brand_preference=args.get('brand_preference'),
            needed_by_date=needed_by,
            quantity=args.get('quantity', 1),
            max_distributors=args.get('max_distributors', 3)
        )

        return result

    async def _check_rfq_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check RFQ status"""
        return self.rfq_manager.check_rfq_status(args['rfq_id'])

    async def _get_quotes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get quotes for RFQ"""
        return self.rfq_manager.get_quotes(args['rfq_id'])

    async def _compare_quotes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare quotes"""
        return self.rfq_manager.compare_quotes(
            rfq_ids=args['rfq_ids'],
            sort_by=args.get('sort_by', 'total_value')
        )

    async def _simulate_quote(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a quote response for testing"""
        return self.rfq_manager.simulate_quote_response(
            rfq_id=args['rfq_id'],
            unit_price=args['unit_price'],
            lead_time_days=args.get('lead_time_days', 5),
            quantity_available=args.get('quantity_available', 10),
            shipping_cost=args.get('shipping_cost', 150.0)
        )

    # ==========================================
    # MCP Protocol Handlers
    # ==========================================

    async def handle_request(self, request: dict) -> dict:
        """Handle incoming JSON-RPC request"""
        method = request.get("method", "")
        request_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = {"tools": self.get_tools()}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                tool_result = await self.call_tool(tool_name, arguments)
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tool_result, indent=2, default=str)
                        }
                    ]
                }
            elif method == "notifications/initialized":
                # Notification, no response needed
                return None
            else:
                return self._error_response(request_id, -32601, f"Method not found: {method}")

            return self._success_response(request_id, result)

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return self._error_response(request_id, -32603, str(e))

    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request"""
        await self.start()

        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.get_server_info(),
            "capabilities": {
                "tools": {}
            }
        }

    def _success_response(self, request_id: Any, result: Any) -> dict:
        """Build success response"""
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "result": result
        }

    def _error_response(self, request_id: Any, code: int, message: str) -> dict:
        """Build error response"""
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def run_server():
    """Main entry point - stdio transport"""
    server = HVACMCPServer()

    logger.info("HVAC MCP Server starting (stdio transport)")

    try:
        while True:
            # Read line from stdin
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = await server.handle_request(request)

                if response:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": JSONRPC_VERSION,
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await server.stop()


def main():
    """Entry point for console script"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
