# Apollo MCP — Hub

**Version**: 1.1.1 | **Status**: Active | **Type**: MCP Server (PyPI published)
**Package**: `io.github.wmarceau/apollo`

## What It Does
MCP server providing Apollo.io lead enrichment, prospecting, and company search via Claude. 80% credit savings vs direct API. 60-90 sec per 100 leads.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Workflows | `workflows/` |
| Templates | `templates/` |
| Registry | `server.json`, `glama.json` |

## Key Commands
```bash
# Run locally
python -m src.server

# Test
python test_installation.py
python test_enhancements.py

# Verify version
python verify_v1.1.0.py
```

## Stack
- Apollo.io API
- MCP protocol
- Used by: lead-scraper project, Claude Desktop

## Related
- Lead scraper hub: `projects/shared/lead-scraper/CLAUDE.md`
- n8n workflow: Hot-Lead-to-ClickUp (active, uses ClickUp — flag for stack review)
