# Canva MCP

**Version**: See `VERSION` | **Status**: Published (PyPI) | **Type**: MCP Package
**MCP name**: `io.github.wmarceau/canva-mcp`

## What It Does
MCP server wrapping the Canva Connect API. Create designs, manage brand assets, auto-fill brand templates, and export graphics — all from Claude.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |

## Key Commands
```bash
# Install
pip install canva-mcp

# Publish update
/publish-mcp
```

## Prerequisites
- Canva Connect API access (requires Canva for Teams or Partner account)
- `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET` in `.env`

## Use Cases
- Generate client website graphics
- Auto-fill brand templates with client data
- Create fitness content visuals
- Export designs for social media

## Related
- Image router: `execution/multi_provider_image_router.py`
- Educational graphics: `execution/educational_graphics.py`
- Social automation: `projects/shared/social-media-automation/`
