#!/usr/bin/env python3
"""
MCP Services Tower - Flask API Server

Minimal entry point for tower independence.
Exposes health check and MCP server registry.

Port: 5015
"""

import os
import logging
from pathlib import Path
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_DIR = Path(__file__).parent


def create_app():
    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        servers = _discover_servers()
        return jsonify({
            "tower": "mcp-services",
            "status": "healthy",
            "version": "1.0.0-dev",
            "mcp_servers": servers,
            "capabilities": ["list_servers", "server_status"],
        })

    @app.route('/servers', methods=['GET'])
    def list_servers():
        """List all available MCP servers — callable via tower_protocol."""
        servers = _discover_servers()
        return jsonify({"success": True, "servers": servers, "count": len(servers)})

    return app


def _discover_servers() -> list:
    """Find all MCP server directories."""
    servers = []
    # Check direct sub-projects (apollo-mcp, canva-mcp, etc.)
    for d in MCP_DIR.parent.iterdir():
        if d.is_dir() and d.name.endswith("-mcp") and (d / "src").exists():
            servers.append(d.name)
    # Check mcp-aggregator sub-MCPs
    agg_dir = MCP_DIR.parent / "mcp-aggregator" / "src" / "mcps"
    if agg_dir.exists():
        for d in agg_dir.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                servers.append(f"aggregator/{d.name}")
    return sorted(servers)


if __name__ == '__main__':
    port = int(os.getenv('MCP_TOWER_PORT', 5015))
    logger.info(f"MCP Services Tower starting on port {port}")
    create_app().run(host='0.0.0.0', port=port, debug=False)
