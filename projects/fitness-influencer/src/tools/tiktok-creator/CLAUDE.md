# TikTok Creator MCP

**Version**: See `VERSION` | **Status**: Published (PyPI) | **Type**: MCP Package
**MCP name**: `io.github.wmarceau/tiktok-creator`

## What It Does
MCP server giving Claude access to TikTok's Content Publishing API. Post videos, set privacy, track analytics, read and reply to comments.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |
| OAuth helper | `get_credentials.py` |

## Key Commands
```bash
# Get TikTok OAuth credentials
python get_credentials.py

# Install
pip install tiktok-creator-mcp

# Publish update
/publish-mcp
```

## Prerequisites
- TikTok Developer account with Content Publishing API access
- `TIKTOK_ACCESS_TOKEN` and `TIKTOK_CLIENT_KEY` in `.env`

## Related
- Instagram MCP: `projects/marceau-solutions/instagram-creator/`
- YouTube MCP: `projects/marceau-solutions/youtube-creator/`
- Social automation: `projects/shared/social-media-automation/`
