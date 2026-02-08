#!/usr/bin/env python3
"""
MCP Aggregator Server

This MCP server provides a unified gateway to all MCPs registered in the platform.
It uses the platform core (router, registry, billing) to:
- Discover available MCPs and capabilities
- Intelligently route requests to the best MCP
- Log transactions for billing

Required Flow:
    Claude Desktop -> aggregator_mcp.py -> router.py -> selects MCP -> calls endpoint
                                        -> registry.py -> discovers MCPs
                                        -> billing.py -> logs transactions

Usage:
    python aggregator_mcp.py

For Claude Desktop, add to claude_desktop_config.json:
{
    "mcpServers": {
        "mcp-aggregator": {
            "command": "python",
            "args": ["/Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/mcp-server/aggregator_mcp.py"],
            "env": {
                "DATABASE_URL": "sqlite:///path/to/aggregator.db",
                "AI_PLATFORM_ID": "your_platform_id",
                "AI_PLATFORM_KEY": "your_api_key"
            }
        }
    }
}
"""

import os
import sys
import json
import asyncio
import uuid
import time
import logging
from typing import Any, Dict, Optional, List
from decimal import Decimal
from datetime import datetime
import httpx

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import platform core modules from src.core
from src.core.database import Database, DatabaseConfig, create_test_database
from src.core.registry import Registry as MCPRegistry, MCPCategory, MCPStatus, MCP, ConnectivityType
from src.core.router import Router as MCPRouter, RoutingRequest, RoutingStrategy, get_scoring_profile
from src.core.billing import BillingSystem, PricingModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Protocol constants
JSONRPC_VERSION = "2.0"

# Configuration
AI_PLATFORM_ID = os.environ.get("AI_PLATFORM_ID", "default_platform")
AI_PLATFORM_KEY = os.environ.get("AI_PLATFORM_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")


class MCPExecutor:
    """
    Executes requests against registered MCPs.

    This bridges the gap between the router's abstract MCP selection
    and actual HTTP calls to MCP endpoints.
    """

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Initialize HTTP client"""
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def stop(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()

    def execute_sync(self, mcp: MCP, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous MCP execution (called by router's thread pool).

        Args:
            mcp: MCP to call
            payload: Request payload with 'capability' and 'arguments'

        Returns:
            Response from MCP
        """
        import requests

        capability = payload.get('capability', '')
        arguments = payload.get('arguments', {})

        # Use MCP's configured timeout (or default)
        timeout_seconds = mcp.timeout_ms / 1000.0

        # Build request to MCP endpoint
        try:
            response = requests.post(
                mcp.endpoint_url,
                json={
                    'capability': capability,
                    'arguments': arguments
                },
                timeout=timeout_seconds,
                headers={
                    'Content-Type': 'application/json',
                    'X-Request-ID': str(uuid.uuid4())
                }
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise Exception(f"MCP {mcp.name} timed out after {timeout_seconds}s")
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP {mcp.name} request failed: {str(e)}")


class AggregatorMCPServer:
    """
    MCP Server that aggregates all registered MCPs through the platform core.

    This is the main entry point that Claude Desktop connects to.
    It provides:
    - route_request: Generic tool to call any registered MCP capability
    - list_capabilities: Discover all available capabilities
    - list_mcps: Discover all registered MCPs
    - get_mcp_health: Check health of a specific MCP
    """

    def __init__(self, db: Database):
        self.db = db
        self.registry = MCPRegistry(db)
        self.billing = BillingSystem(db)
        self.executor = MCPExecutor()

        # Create router with custom executor
        self.router = MCPRouter(
            db=db,
            executor=self.executor.execute_sync
        )

        # Platform identity (for billing)
        self.ai_platform_id = AI_PLATFORM_ID

    async def start(self):
        """Start the server"""
        await self.executor.start()
        logger.info("Aggregator MCP Server started")
        logger.info(f"Platform Core loaded from: {PROJECT_ROOT}/src/core")

    async def stop(self):
        """Stop the server"""
        await self.executor.stop()
        logger.info("Aggregator MCP Server stopped")

    def get_server_info(self) -> dict:
        """Return server capabilities"""
        return {
            "name": "mcp-aggregator",
            "version": "1.0.0",
            "description": "Unified gateway to all MCPs in the aggregator platform"
        }

    def get_tools(self) -> list:
        """Return available tools"""
        return [
            {
                "name": "route_request",
                "description": "Route a request to the best available MCP for a capability. Uses intelligent routing based on health, performance, cost, and rating.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "capability": {
                            "type": "string",
                            "description": "The capability name to invoke (e.g., 'compare_prices', 'get_weather')"
                        },
                        "payload": {
                            "type": "object",
                            "description": "The request payload to send to the MCP",
                            "additionalProperties": True
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by MCP category (rideshare, flights, hotels, etc.)",
                            "enum": [cat.value for cat in MCPCategory]
                        },
                        "preferred_mcp_id": {
                            "type": "string",
                            "description": "Optional: Prefer a specific MCP by ID"
                        },
                        "max_latency_ms": {
                            "type": "integer",
                            "description": "Optional: Maximum acceptable latency in milliseconds"
                        },
                        "max_cost": {
                            "type": "number",
                            "description": "Optional: Maximum cost per request in USD"
                        },
                        "strategy": {
                            "type": "string",
                            "description": "Optional: Routing strategy",
                            "enum": ["best_score", "lowest_cost", "fastest", "round_robin", "random"],
                            "default": "best_score"
                        },
                        "timeout_ms": {
                            "type": "integer",
                            "description": "Optional: Request timeout in milliseconds (overrides MCP default)",
                            "default": 30000
                        }
                    },
                    "required": ["capability", "payload"]
                }
            },
            {
                "name": "list_capabilities",
                "description": "List all available capabilities across registered MCPs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by category",
                            "enum": [cat.value for cat in MCPCategory]
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "list_mcps",
                "description": "List all registered MCPs with their status and capabilities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by category",
                            "enum": [cat.value for cat in MCPCategory]
                        },
                        "status": {
                            "type": "string",
                            "description": "Optional: Filter by status",
                            "enum": ["active", "inactive", "suspended", "pending_review"],
                            "default": "active"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_mcp_health",
                "description": "Get health status and metrics for a specific MCP",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mcp_id": {
                            "type": "string",
                            "description": "The MCP ID to check"
                        }
                    },
                    "required": ["mcp_id"]
                }
            },
            {
                "name": "get_routing_scores",
                "description": "Get scoring breakdown for MCPs that can handle a capability (debugging/transparency)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "capability": {
                            "type": "string",
                            "description": "The capability name"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by category",
                            "enum": [cat.value for cat in MCPCategory]
                        }
                    },
                    "required": ["capability"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool and return results"""

        if name == "route_request":
            return await self._route_request(arguments)
        elif name == "list_capabilities":
            return self._list_capabilities(arguments)
        elif name == "list_mcps":
            return self._list_mcps(arguments)
        elif name == "get_mcp_health":
            return self._get_mcp_health(arguments)
        elif name == "get_routing_scores":
            return self._get_routing_scores(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _route_request(self, args: dict) -> dict:
        """
        Route a request through the platform core.

        This is the main entry point that:
        1. Logs the transaction (billing)
        2. Routes to best MCP (router)
        3. Executes the request
        4. Completes/fails the transaction
        """
        capability = args.get('capability')
        payload = args.get('payload', {})

        # Parse optional filters
        category = None
        if args.get('category'):
            category = MCPCategory(args['category'])

        strategy = RoutingStrategy.BEST_SCORE
        if args.get('strategy'):
            strategy = RoutingStrategy(args['strategy'])

        # Build routing request
        routing_request = RoutingRequest(
            capability=capability,
            payload={
                'capability': capability,
                'arguments': payload
            },
            category=category,
            preferred_mcp_id=args.get('preferred_mcp_id'),
            max_latency_ms=args.get('max_latency_ms'),
            max_cost=args.get('max_cost'),
            strategy=strategy,
            timeout_ms=args.get('timeout_ms', 30000)
        )

        # Generate request ID for idempotency
        request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Find the MCP that will handle this (for billing)
        candidates = self.registry.find_by_capability(capability)
        if not candidates:
            return {
                'success': False,
                'error': f"No MCPs found for capability '{capability}'",
                'available_capabilities': self._get_all_capability_names()
            }

        # Get the likely MCP (first candidate for billing purposes)
        selected_mcp = candidates[0]

        # Log transaction BEFORE execution
        try:
            transaction_id = self.billing.log_transaction(
                ai_platform_id=self.ai_platform_id,
                mcp_id=selected_mcp.id,
                developer_id=selected_mcp.developer_id,
                request_id=request_id,
                capability_name=capability,
                request_payload=payload,
                gross_amount=Decimal(str(selected_mcp.fee_per_request)),
                developer_share=Decimal(str(selected_mcp.developer_share))
            )
        except ValueError as e:
            # Duplicate request ID
            return {
                'success': False,
                'error': f"Duplicate request: {str(e)}"
            }

        # Execute through router
        start_time = time.time()
        result = self.router.route_request(routing_request)
        response_time_ms = int((time.time() - start_time) * 1000)

        # Update transaction based on result
        if result.success:
            self.billing.complete_transaction(
                transaction_id=transaction_id,
                response=result.response or {},
                response_time_ms=response_time_ms
            )

            return {
                'success': True,
                'mcp_id': result.mcp_id,
                'mcp_name': result.mcp_name,
                'response': result.response,
                'metadata': {
                    'response_time_ms': result.response_time_ms,
                    'cost': f"${result.cost:.4f}",
                    'attempts': result.attempts,
                    'fallback_used': result.fallback_used,
                    'transaction_id': transaction_id
                }
            }
        else:
            self.billing.fail_transaction(
                transaction_id=transaction_id,
                error_message=result.error or "Unknown error"
            )

            return {
                'success': False,
                'error': result.error,
                'metadata': {
                    'response_time_ms': result.response_time_ms,
                    'attempts': result.attempts,
                    'fallback_used': result.fallback_used,
                    'transaction_id': transaction_id
                }
            }

    def _list_capabilities(self, args: dict) -> dict:
        """List all available capabilities"""
        category = None
        if args.get('category'):
            category = MCPCategory(args['category'])

        # Get all active MCPs
        mcps = self.registry.find_mcps(category=category, status=MCPStatus.ACTIVE)

        capabilities = {}
        for mcp in mcps:
            # Load capabilities for each MCP
            mcp_with_caps = self.registry.get_mcp(mcp.id)
            if mcp_with_caps:
                for cap in mcp_with_caps.capabilities:
                    if cap.name not in capabilities:
                        capabilities[cap.name] = {
                            'description': cap.description,
                            'mcps': [],
                            'input_schema': cap.input_schema
                        }
                    capabilities[cap.name]['mcps'].append({
                        'id': mcp.id,
                        'name': mcp.name,
                        'category': mcp.category.value,
                        'fee': f"${mcp.fee_per_request:.4f}",
                        'rating': mcp.avg_rating
                    })

        return {
            'total_capabilities': len(capabilities),
            'capabilities': capabilities
        }

    def _list_mcps(self, args: dict) -> dict:
        """List all registered MCPs"""
        category = None
        if args.get('category'):
            category = MCPCategory(args['category'])

        status = MCPStatus.ACTIVE
        if args.get('status'):
            status = MCPStatus(args['status'])

        mcps = self.registry.find_mcps(category=category, status=status)

        result = []
        for mcp in mcps:
            mcp_full = self.registry.get_mcp(mcp.id)
            result.append({
                'id': mcp.id,
                'name': mcp.name,
                'slug': mcp.slug,
                'description': mcp.description,
                'category': mcp.category.value,
                'status': mcp.status.value,
                'endpoint_url': mcp.endpoint_url,
                'fee_per_request': f"${mcp.fee_per_request:.4f}",
                'avg_rating': mcp.avg_rating,
                'avg_response_time_ms': mcp.avg_response_time_ms,
                'uptime_percent': mcp.uptime_percent,
                'timeout_ms': mcp.timeout_ms,
                'capabilities': [
                    {'name': cap.name, 'description': cap.description}
                    for cap in (mcp_full.capabilities if mcp_full else [])
                ]
            })

        return {
            'total_mcps': len(result),
            'mcps': result
        }

    def _get_mcp_health(self, args: dict) -> dict:
        """Get health status for an MCP"""
        mcp_id = args.get('mcp_id')

        health = self.registry.get_health_status(mcp_id)
        if not health:
            return {
                'success': False,
                'error': f"MCP not found: {mcp_id}"
            }

        return {
            'success': True,
            'health': health
        }

    def _get_routing_scores(self, args: dict) -> dict:
        """Get scoring breakdown for transparency"""
        capability = args.get('capability')
        category = None
        if args.get('category'):
            category = MCPCategory(args['category'])

        scores = self.router.get_routing_scores(capability, category)

        return {
            'capability': capability,
            'total_candidates': len(scores),
            'scores': scores
        }

    def _get_all_capability_names(self) -> List[str]:
        """Get list of all capability names"""
        mcps = self.registry.find_mcps(status=MCPStatus.ACTIVE)
        capabilities = set()
        for mcp in mcps:
            mcp_full = self.registry.get_mcp(mcp.id)
            if mcp_full:
                for cap in mcp_full.capabilities:
                    capabilities.add(cap.name)
        return sorted(list(capabilities))


async def handle_message(server: AggregatorMCPServer, message: dict) -> dict:
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
                        "text": json.dumps(tool_result, indent=2, default=str)
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
        logger.exception(f"Error handling message: {e}")
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }


def setup_database() -> Database:
    """
    Set up database connection.

    Uses DATABASE_URL env var if set, otherwise creates in-memory test DB.
    """
    db_url = os.environ.get('DATABASE_URL', '')

    if db_url:
        # Use configured database
        config = DatabaseConfig.from_env()
        db = Database(config)
        db.connect()
        logger.info(f"Connected to database: {config.db_type.value}")
    else:
        # Create test database for development
        logger.info("No DATABASE_URL set, using in-memory test database")
        db = create_test_database()

        # Seed with test data for development
        _seed_test_data(db)

    return db


def _seed_test_data(db: Database):
    """Seed test database with sample MCPs for development"""
    import uuid as uuid_mod

    # Create test developer
    dev_id = str(uuid_mod.uuid4())
    db.execute(
        "INSERT INTO developers (id, email, display_name, api_key_hash) VALUES (?, ?, ?, ?)",
        (dev_id, 'test@example.com', 'Test Developer', 'hash123')
    )

    # Create test AI platform
    platform_id = str(uuid_mod.uuid4())
    db.execute(
        "INSERT INTO ai_platforms (id, name, api_key_hash) VALUES (?, ?, ?)",
        (platform_id, 'Test Platform', 'hash456')
    )

    # Update the global platform ID
    global AI_PLATFORM_ID
    AI_PLATFORM_ID = platform_id

    # Create test rideshare MCP
    from registry import MCPRegistry, MCPCapability, MCPCategory
    registry = MCPRegistry(db)

    mcp_id = registry.register_mcp(
        developer_id=dev_id,
        name="Rideshare Compare",
        slug="rideshare-compare",
        category=MCPCategory.RIDESHARE,
        endpoint_url="http://localhost:8000/v1/compare",
        description="Compare Uber and Lyft prices for any route",
        fee_per_request=0.02,
        timeout_ms=30000,
        capabilities=[
            MCPCapability(
                name='compare_prices',
                description='Compare rideshare prices for a route',
                input_schema={
                    'type': 'object',
                    'properties': {
                        'pickup_lat': {'type': 'number'},
                        'pickup_lng': {'type': 'number'},
                        'dropoff_lat': {'type': 'number'},
                        'dropoff_lng': {'type': 'number'}
                    },
                    'required': ['pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng']
                }
            ),
            MCPCapability(
                name='get_supported_cities',
                description='Get list of supported cities'
            )
        ]
    )
    registry.activate_mcp(mcp_id)
    registry.update_rating(mcp_id, 4.5)

    logger.info(f"Seeded test database with MCP: {mcp_id}")


async def main():
    """Main entry point - runs MCP server over stdio"""
    # Set up database
    db = setup_database()

    # Create server
    server = AggregatorMCPServer(db)
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

        logger.info("Aggregator MCP Server ready, listening on stdio")

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

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                continue

    finally:
        await server.stop()
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
