# MCP Services Tower Directive

## Domain
Model Context Protocol server development, MCP aggregation platform, and AI agent tooling interfaces.

## Core Capabilities
- **MCP Aggregator** (`mcp-aggregator/`): "Amazon for AI Agent Services" — marketplace platform for discovering and routing MCP tools
- **Apollo MCP** (`apollo-mcp/`): Lead enrichment via Apollo API as MCP tools
- **Canva MCP** (`canva-mcp/`): Design creation via Canva API as MCP tools
- **Twilio MCP** (`twilio-mcp/`): SMS/voice via Twilio as MCP tools
- **Ticket Aggregator MCP** (`ticket-aggregator-mcp/`): Ticket discovery across platforms
- **MCP Security** (`mcp_security.py`): Shared sanitization, validation, rate limiting

## Entry Point
- No unified Flask app yet (each MCP server runs independently)
- Individual servers: `python -m src.[mcp-name].src.[server-module]`

## Integration Points
- **lead-generation**: Apollo MCP provides lead enrichment
- **fitness-influencer**: Canva MCP provides design generation
- **personal-assistant**: Twilio MCP provides SMS capabilities
- **All towers**: MCP aggregator could serve as universal tool routing layer

## Current Status
1.0.0-dev — 5 MCP server sub-projects exist with code. MCP aggregator (21,856 lines) is the largest component. No unified entry point.

## Current Version
1.0.0-dev
