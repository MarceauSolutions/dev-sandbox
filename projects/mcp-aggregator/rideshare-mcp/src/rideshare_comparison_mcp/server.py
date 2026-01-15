#!/usr/bin/env python3
"""
Rideshare Comparison MCP Server

Compare Uber and Lyft prices for any route. Returns estimated fares,
which service is cheaper, and deep links to book.

Usage:
    python -m rideshare_comparison_mcp

For Claude Desktop, add to claude_desktop_config.json:
{
    "mcpServers": {
        "rideshare-comparison": {
            "command": "python",
            "args": ["-m", "rideshare_comparison_mcp"],
            "env": {
                "RIDESHARE_API_URL": "http://localhost:8000",
                "RIDESHARE_API_KEY": "your_api_key"
            }
        }
    }
}
"""

import os
import sys
import json
import asyncio
import httpx
from typing import Any

# MCP Protocol constants
JSONRPC_VERSION = "2.0"

# Configuration
API_URL = os.environ.get("RIDESHARE_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("RIDESHARE_API_KEY", "test_free_key_12345")


class RideshareMCPServer:
    """MCP Server for rideshare price comparison"""

    def __init__(self):
        self.http_client = None

    async def start(self):
        """Start the HTTP client"""
        self.http_client = httpx.AsyncClient(
            base_url=API_URL,
            headers={"X-API-Key": API_KEY},
            timeout=30.0
        )

    async def stop(self):
        """Close the HTTP client"""
        if self.http_client:
            await self.http_client.aclose()

    def get_server_info(self) -> dict:
        """Return server capabilities"""
        return {
            "name": "rideshare-comparison",
            "version": "1.0.0",
            "description": "Compare Uber and Lyft prices for any route"
        }

    def get_tools(self) -> list:
        """Return available tools"""
        return [
            {
                "name": "compare_rideshare_prices",
                "description": "Compare Uber and Lyft prices for a route. Returns estimated fares, which service is cheaper, and deep links to book.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pickup_lat": {
                            "type": "number",
                            "description": "Pickup latitude (e.g., 37.7879 for San Francisco)"
                        },
                        "pickup_lng": {
                            "type": "number",
                            "description": "Pickup longitude (e.g., -122.4074 for San Francisco)"
                        },
                        "dropoff_lat": {
                            "type": "number",
                            "description": "Dropoff latitude"
                        },
                        "dropoff_lng": {
                            "type": "number",
                            "description": "Dropoff longitude"
                        },
                        "pickup_address": {
                            "type": "string",
                            "description": "Optional: Human-readable pickup address for context"
                        },
                        "dropoff_address": {
                            "type": "string",
                            "description": "Optional: Human-readable dropoff address for context"
                        }
                    },
                    "required": ["pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng"]
                }
            },
            {
                "name": "get_supported_cities",
                "description": "Get list of cities with rideshare pricing data",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_booking_link",
                "description": "Get a deep link to book a ride with Uber or Lyft",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "enum": ["uber", "lyft"],
                            "description": "Which service to get booking link for"
                        },
                        "pickup_lat": {
                            "type": "number",
                            "description": "Pickup latitude"
                        },
                        "pickup_lng": {
                            "type": "number",
                            "description": "Pickup longitude"
                        },
                        "dropoff_lat": {
                            "type": "number",
                            "description": "Dropoff latitude"
                        },
                        "dropoff_lng": {
                            "type": "number",
                            "description": "Dropoff longitude"
                        }
                    },
                    "required": ["service", "pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool and return results"""

        if name == "compare_rideshare_prices":
            return await self._compare_prices(arguments)
        elif name == "get_supported_cities":
            return await self._get_cities()
        elif name == "get_booking_link":
            return await self._get_booking_link(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _compare_prices(self, args: dict) -> dict:
        """Call the compare endpoint"""
        response = await self.http_client.post(
            "/v1/compare",
            json={
                "pickup": {
                    "latitude": args["pickup_lat"],
                    "longitude": args["pickup_lng"],
                    "address": args.get("pickup_address")
                },
                "dropoff": {
                    "latitude": args["dropoff_lat"],
                    "longitude": args["dropoff_lng"],
                    "address": args.get("dropoff_address")
                }
            }
        )
        response.raise_for_status()
        data = response.json()

        # Format for human-readable output
        return {
            "summary": f"{'Lyft' if data['recommendation'] == 'lyft' else 'Uber'} is cheaper by ${data['savings']:.2f} ({data['savings_percent']}%)",
            "uber": {
                "price": f"${data['uber']['estimate']:.2f}",
                "range": f"${data['uber']['low_estimate']:.2f} - ${data['uber']['high_estimate']:.2f}",
                "surge": f"{data['uber']['surge_multiplier']}x" if data['uber']['surge_multiplier'] > 1 else "No surge",
                "book_link": data['uber']['deep_link']
            },
            "lyft": {
                "price": f"${data['lyft']['estimate']:.2f}",
                "range": f"${data['lyft']['low_estimate']:.2f} - ${data['lyft']['high_estimate']:.2f}",
                "surge": f"{data['lyft']['surge_multiplier']}x" if data['lyft']['surge_multiplier'] > 1 else "No surge",
                "book_link": data['lyft']['deep_link']
            },
            "recommendation": data['recommendation'],
            "route_info": {
                "distance": f"{data['distance_miles']:.1f} miles",
                "duration": f"{data['duration_minutes']:.0f} minutes",
                "city": data['city']
            },
            "confidence": f"{data['confidence'] * 100:.0f}%",
            "disclaimer": data['disclaimer']
        }

    async def _get_cities(self) -> dict:
        """Get supported cities"""
        response = await self.http_client.get("/v1/cities")
        response.raise_for_status()
        data = response.json()
        return {
            "supported_cities": data['cities'],
            "count": data['count'],
            "note": "Price estimates are most accurate for these cities"
        }

    async def _get_booking_link(self, args: dict) -> dict:
        """Get booking deep link"""
        service = args["service"]
        response = await self.http_client.get(
            f"/v1/deeplink/{service}",
            params={
                "pickup_lat": args["pickup_lat"],
                "pickup_lng": args["pickup_lng"],
                "dropoff_lat": args["dropoff_lat"],
                "dropoff_lng": args["dropoff_lng"]
            }
        )
        response.raise_for_status()
        data = response.json()
        return {
            "service": service.capitalize(),
            "app_link": data['app_link'],
            "web_link": data['web_link'],
            "instruction": f"Click the link to open {service.capitalize()} and book your ride"
        }


async def handle_message(server: RideshareMCPServer, message: dict) -> dict:
    """Handle incoming JSON-RPC message"""
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params", {})

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": server.get_server_info(),
                "capabilities": {
                    "tools": {}
                }
            }
        elif method == "tools/list":
            result = {"tools": server.get_tools()}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            tool_result = await server.call_tool(tool_name, arguments)
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(tool_result, indent=2)
                    }
                ]
            }
        elif method == "notifications/initialized":
            # Notification, no response needed
            return None
        else:
            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "result": result
        }

    except Exception as e:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }


async def run_server():
    """Main entry point - runs MCP server over stdio"""
    server = RideshareMCPServer()
    await server.start()

    try:
        # Read from stdin, write to stdout (MCP stdio transport)
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            # Read line (JSON-RPC message)
            line = await reader.readline()
            if not line:
                break

            try:
                message = json.loads(line.decode())
                response = await handle_message(server, message)

                if response:  # Some messages (notifications) don't need responses
                    writer.write((json.dumps(response) + "\n").encode())
                    await writer.drain()

            except json.JSONDecodeError:
                continue

    finally:
        await server.stop()


def main():
    """Entry point for console script"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
