# Apollo MCP Setup & Deployment Guide

## Project Created: 2026-01-21

This Apollo.io MCP server provides lead enrichment and prospecting capabilities through Claude Desktop and other MCP-compatible AI assistants.

## Current Status

✅ **Package Structure Created** (SOP 11 Complete)
- Full MCP server implementation
- Apollo API client integration
- 8 MCP tools defined
- Package structure ready for deployment

📋 **Next Steps**: Install, Test, Deploy

## Quick Setup (Development)

### 1. Install Dependencies

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp

# Install in development mode
pip install -e .
```

This installs:
- `mcp` - MCP SDK
- `requests` - HTTP client for Apollo API
- `python-dotenv` - Environment variable management

### 2. Configure API Key

Get your Apollo API key from https://app.apollo.io/settings/integrations

**Option A**: Environment variable
```bash
export APOLLO_API_KEY="your-api-key-here"
```

**Option B**: `.env` file (recommended)
Create `/Users/williammarceaujr./dev-sandbox/.env` and add:
```
APOLLO_API_KEY=your-api-key-here
```

### 3. Test Installation

```bash
python test_installation.py
```

Expected output:
```
✓ Successfully imported apollo_mcp v1.0.0
✓ Apollo API key configured
✓ Apollo client initialized successfully
✓ MCP server imports successful
```

### 4. Test MCP Server

```bash
python -m apollo_mcp.server
```

The server will start and wait for MCP protocol messages. Press Ctrl+C to exit.

## Integration with Claude Desktop

### MacOS Configuration

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Development Mode** (use local source):
```json
{
  "mcpServers": {
    "apollo": {
      "command": "python",
      "args": [
        "-m",
        "apollo_mcp.server"
      ],
      "env": {
        "APOLLO_API_KEY": "your-api-key-here",
        "PYTHONPATH": "/Users/williammarceaujr./dev-sandbox/projects/apollo-mcp/src"
      }
    }
  }
}
```

**Production Mode** (after pip install):
```json
{
  "mcpServers": {
    "apollo": {
      "command": "apollo-mcp",
      "env": {
        "APOLLO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Restart Claude Desktop

After editing config:
1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. Check that Apollo MCP tools are available

## Testing with Claude

Try these prompts:

```
"Search Apollo for gyms in Naples, FL"
"Find decision makers at example.com"
"Search for restaurant owners in Miami with 1-50 employees"
```

## Available Tools

1. **search_people** - Find contacts by title, location, company
2. **search_companies** - Search businesses by location, industry, size
3. **search_local_businesses** - Convenience method for local search
4. **enrich_person** - Reveal contact details (costs credits)
5. **enrich_company** - Get detailed company info
6. **find_decision_makers** - Find owners/CEOs at companies
7. **find_email** - Find email for person (costs credits)
8. **get_credit_balance** - Instructions for checking credits

## Deployment Pipeline

Following the dev-sandbox SOPs:

### Manual Testing (Scenario 1)

✅ Package structure created
⏳ Install and test locally
⏳ Verify all tools work
⏳ Test with real Apollo API calls

### Pre-Deployment (Scenario 3)

After manual testing passes:

```bash
cd /Users/williammarceaujr./dev-sandbox

# Deploy to production (-prod directory)
python deploy_to_skills.py --project apollo-mcp --version 1.0.0
```

### PyPI Publishing (SOP 12)

After deployment:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN
```

### MCP Registry Publishing (SOP 13)

After PyPI:

```bash
# Authenticate with GitHub
/path/to/mcp-publisher login github

# Publish to MCP Registry
/path/to/mcp-publisher publish --server server.json
```

## Troubleshooting

### Module Not Found

If `ModuleNotFoundError: No module named 'apollo_mcp'`:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
pip install -e .
```

### MCP SDK Not Installed

```bash
pip install mcp
```

### Apollo API Errors

1. Verify API key: `echo $APOLLO_API_KEY`
2. Check key is valid at https://app.apollo.io/settings/integrations
3. Ensure account has credits remaining
4. Test with free search operations first

### Claude Desktop Not Showing Tools

1. Check config file syntax (valid JSON)
2. Verify path to server.py is correct
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

## Project Structure

```
apollo-mcp/
├── src/
│   └── apollo_mcp/
│       ├── __init__.py          # Package version
│       ├── apollo.py            # Apollo API client
│       └── server.py            # MCP server
├── workflows/
│   └── usage-examples.md        # Usage patterns
├── pyproject.toml               # Package config
├── server.json                  # MCP registry manifest
├── README.md                    # User documentation
├── TESTING.md                   # Testing guide
├── SETUP.md                     # This file
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT License
├── VERSION                      # 1.0.0
└── test_installation.py         # Installation test
```

## Development Workflow

1. **Make changes** to `src/apollo_mcp/*.py`
2. **Test locally**: `python test_installation.py`
3. **Test with Claude**: Add to Claude Desktop config
4. **Update version**: Bump in VERSION, pyproject.toml, server.json, __init__.py
5. **Update CHANGELOG.md**: Document changes
6. **Deploy**: `python deploy_to_skills.py --project apollo-mcp --version X.Y.Z`
7. **Publish**: PyPI → MCP Registry

## Credits and Rate Limits

### Apollo API Limits

- **Rate limit**: 50 requests per minute
- **Search operations**: Free (no credits)
- **Enrichment operations**: Cost credits
  - `enrich_person` - 1 credit
  - `find_email` - 1 credit
  - `enrich_company` - Varies by plan

### Check Credit Balance

https://app.apollo.io/settings/credits

### Best Practices

1. Search first to qualify leads
2. Only enrich high-quality prospects
3. Batch enrichment operations
4. Monitor credit usage regularly

## Support

- **Apollo API Docs**: https://apolloio.github.io/apollo-api-docs/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Project Issues**: Contact William Marceau Jr.

## References

- SOP 11: MCP Package Structure
- SOP 12: PyPI Publishing
- SOP 13: MCP Registry Publishing
- `docs/testing-strategy.md`: Complete testing pipeline
