# MCP Registry Materials

This folder contains materials for registering with the official MCP Registry.

## Registry Information

- **Registry URL**: https://registry.modelcontextprotocol.io/
- **GitHub**: https://github.com/modelcontextprotocol/registry
- **API Status**: Frozen at v0.1 (stable)

## Quick Registration Guide

```bash
# 1. Clone registry tools
git clone https://github.com/modelcontextprotocol/registry.git
cd registry

# 2. Build publisher
make publisher

# 3. Login with GitHub
./bin/mcp-publisher login --github

# 4. Publish servers
./bin/mcp-publisher publish io.github.williammarceaujr/rideshare-comparison
./bin/mcp-publisher publish io.github.williammarceaujr/hvac-quotes
./bin/mcp-publisher publish io.github.williammarceaujr/mcp-aggregator
```

## Our Namespaces

| Server | Namespace | Status |
|--------|-----------|--------|
| MCP Aggregator | `io.github.williammarceaujr/mcp-aggregator` | Pending |
| Rideshare Comparison | `io.github.williammarceaujr/rideshare-comparison` | Pending |
| HVAC Quotes | `io.github.williammarceaujr/hvac-quotes` | Pending |

## Files in This Directory

| File | Purpose |
|------|---------|
| `manifest.json` | Service manifest for registry |
| `README.md` | This file |

## Custom Domain (Future)

For a more professional namespace, register a custom domain:

1. Buy domain: `mcp-aggregator.com`
2. Add DNS TXT record: `_mcp-verify.mcp-aggregator.com` -> verification token
3. Publish under: `mcp-aggregator.com/aggregator`

## Auto-Notifications

Set up GitHub Watch for automatic updates:

1. Go to https://github.com/modelcontextprotocol/registry
2. Click **Watch** -> **Custom**
3. Select: Releases, Discussions, Security alerts
4. GitHub emails you automatically

## Also Monitor

- https://github.com/modelcontextprotocol/specification
- https://blog.modelcontextprotocol.io/ (RSS)
