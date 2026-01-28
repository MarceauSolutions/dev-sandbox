#!/usr/bin/env python3
"""
Test script to verify Apollo MCP installation and basic functionality.
"""

import sys
import os

# Add src to path for development testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from apollo_mcp import __version__
    from apollo_mcp.apollo import ApolloClient, ApolloConfig
    print(f"✓ Successfully imported apollo_mcp v{__version__}")
except ImportError as e:
    print(f"✗ Failed to import apollo_mcp: {e}")
    sys.exit(1)

# Test Apollo client initialization
try:
    config = ApolloConfig.from_env()
    client = ApolloClient(config)

    if config.api_key:
        print(f"✓ Apollo API key configured (first 10 chars: {config.api_key[:10]}...)")
    else:
        print("⚠ Apollo API key not found in environment")
        print("  Set APOLLO_API_KEY environment variable to test API calls")

    print(f"✓ Apollo client initialized successfully")
    print(f"  Base URL: {config.base_url}")
    print(f"  Rate limit: {config.requests_per_minute} requests/minute")

except Exception as e:
    print(f"✗ Failed to initialize Apollo client: {e}")
    sys.exit(1)

# Test MCP server imports
try:
    from apollo_mcp.server import server, list_tools, call_tool
    print("✓ MCP server imports successful")
except ImportError as e:
    print(f"✗ Failed to import MCP server: {e}")
    print("  Install MCP SDK with: pip install mcp")
    sys.exit(1)

print("\n" + "="*60)
print("All imports successful! Apollo MCP is ready to use.")
print("="*60)
print("\nNext steps:")
print("1. Set APOLLO_API_KEY environment variable")
print("2. Test with: python -m apollo_mcp.server")
print("3. Add to Claude Desktop config (see README.md)")
