# YouTube Creator MCP

**Version**: See `VERSION` | **Status**: Published (PyPI) | **Type**: MCP Package
**MCP name**: `io.github.wmarceau/youtube-creator`

## What It Does
MCP server giving Claude access to YouTube Data API v3. Upload videos and Shorts, schedule releases, track analytics, manage playlists, read and reply to comments.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |
| OAuth helper | `get_credentials.py` |
| OAuth client secret | `client_secret_*.json` (gitignored) |

## Key Commands
```bash
# Get YouTube OAuth credentials
python get_credentials.py

# Install
pip install youtube-creator-mcp

# Publish update
/publish-mcp
```

## Prerequisites
- Google Cloud project with YouTube Data API v3 enabled
- OAuth 2.0 credentials (client ID/secret)
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` in `.env`

## Related
- Instagram MCP: `projects/marceau-solutions/instagram-creator/`
- TikTok MCP: `projects/marceau-solutions/tiktok-creator/`
- Social automation: `projects/shared/social-media-automation/`
