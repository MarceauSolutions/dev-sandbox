# Instagram Creator MCP

**Version**: See `VERSION` | **Status**: Published (PyPI) | **Type**: MCP Package
**MCP name**: `io.github.wmarceau/instagram-creator`

## What It Does
MCP server giving Claude access to Instagram Graph API. Post images, carousels, Reels, Stories, read analytics, and manage comments — all from Claude.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |

## Key Commands
```bash
# Install
pip install instagram-creator-mcp

# Publish update
/publish-mcp
```

## Prerequisites
- Facebook Business Account + Instagram Professional Account
- Meta Developer App with Instagram Graph API access
- `INSTAGRAM_ACCESS_TOKEN` in `.env`

## Related
- TikTok MCP: `projects/marceau-solutions/tiktok-creator/`
- YouTube MCP: `projects/marceau-solutions/youtube-creator/`
- Social automation: `projects/shared/social-media-automation/`
- Publish SOP: `docs/sops/sop-11-mcp-structure.md`
