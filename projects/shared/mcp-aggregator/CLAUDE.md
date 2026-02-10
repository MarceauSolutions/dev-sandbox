# Universal MCP Aggregation Platform

## What This Does
Marketplace platform ("Amazon for AI Agent Services") that sits between AI agents (Claude, ChatGPT) and service providers. Provides intelligent routing, MCP discovery, billing/transaction tracking, and quality control. Routes requests to the best available MCP based on capability, health, latency, and cost. Revenue model: 10-20% transaction fees + $99/month developer listing fees.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/mcp-aggregator

# Run local API server
python src/api/server.py

# Test routing
curl -X POST http://localhost:8000/v1/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare Uber and Lyft from Union Square SF to SFO"}'

# Database setup (requires PostgreSQL)
createdb mcp_aggregator_dev
python src/cli/setup_db.py
```

## Architecture
- **`src/core/router.py`** - Intelligent routing engine with multi-factor scoring, circuit breaker, auto-fallback
- **`src/core/registry.py`** - MCP discovery and registration, health checks, SLA monitoring
- **`src/core/billing.py`** - Transaction tracking, fee calculations, developer payouts
- **`src/core/database.py`** - Database abstraction layer
- **`src/core/schema.sql`** - PostgreSQL schema for MCPs, transactions, SLAs
- **`src/api/`** - REST API server (FastAPI)
- **`src/mcps/rideshare/`** - Flagship rideshare comparison MCP (Uber/Lyft pricing, deep links, surge prediction)
- **`rideshare-mcp/`** - Standalone rideshare MCP package
- **`hvac-mcp/`** - HVAC service comparison MCP
- **`mcp-server/`** - MCP protocol server
- **`agent1-rest-api/`** through **`agent3-platform-core/`** - Multi-agent parallel dev outputs (SOP 10)

## Project-Specific Rules
- Requires PostgreSQL 14+ for production (SQLite for dev)
- Core platform is category-agnostic -- no rideshare-specific assumptions in `src/core/`
- Routing algorithm uses multi-factor scoring: capability match, health, latency, cost, user preferences
- Circuit breaker pattern prevents cascade failures to unhealthy MCPs
- Platform earns revenue on every routed request (transaction fees)
- Agent workspace directories (`agent1-*`, `agent2-*`, `agent3-*`) are SOP 10 parallel dev artifacts
- Version: 1.0.0-dev (active development)

## Relevant SOPs
- SOP 10: Multi-Agent Parallel Development (how agent dirs were created)
- SOP 9: Multi-Agent Architecture Exploration (approach selection)
- SOP 17: Market Viability Analysis (market validation)
- SOPs 11-14: MCP Publishing (for rideshare-mcp and hvac-mcp)
