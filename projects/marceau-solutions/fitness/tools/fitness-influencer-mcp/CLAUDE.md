# Fitness Influencer MCP — Hub

**Version**: 1.3.0 | **Status**: Active | **Type**: MCP Server (PyPI published)
**Package**: `io.github.wmarceau/fitness-influencer`

## What It Does
AI-powered automation suite for fitness content creators. Automates video editing, graphics creation, email management, SMS communication, and revenue analytics.

## Key Locations
| What | Where |
|------|-------|
| MCP server | `mcp-server/` |
| Source | `src/` |
| Workflows | `workflows/` |
| Docs | `docs/` |
| Deploy | `railway.toml`, `Procfile` |
| Registry | `server.json`, `registry/` |

## Entry Points
- **MCP server**: `mcp-server/server.py`
- **Skills**: `SKILL.md`
- **Deploy**: Railway (`railway.toml`) or EC2

## Key Commands
```bash
# Run locally
python -m src.main

# Deploy to Railway
railway up

# Test MCP
python -m pytest testing/
```

## Related
- Live demo: `https://fitai.marceausolutions.com`
- EC2 service: `fitai.service` (port 8001)
- Parent hub: `projects/marceau-solutions/fitness-influencer/CLAUDE.md`
