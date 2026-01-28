# Apollo MCP - Claude Desktop Configuration

## Installation

Once Apollo MCP is published to the MCP Registry, add it to your Claude Desktop configuration.

## Configuration File Location

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## Configuration Snippet

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apollo": {
      "command": "apollo-mcp",
      "env": {
        "APOLLO_API_KEY": "88ptiN7zpJrVc1hNP6rjVw"
      }
    }
  }
}
```

**Important:** If you already have other MCPs configured, add the `"apollo"` block inside the existing `"mcpServers"` object. Don't replace the entire config.

### Example with Multiple MCPs

```json
{
  "mcpServers": {
    "some-other-mcp": {
      "command": "some-other-mcp"
    },
    "apollo": {
      "command": "apollo-mcp",
      "env": {
        "APOLLO_API_KEY": "88ptiN7zpJrVc1hNP6rjVw"
      }
    }
  }
}
```

## Restart Claude Desktop

After editing the config:
1. Quit Claude Desktop completely (Cmd+Q)
2. Reopen Claude Desktop
3. Check bottom left for Apollo MCP in the MCP list

## Verification

Test with these prompts in Claude Desktop:

### Basic Search
```
Search Apollo for gyms in Naples FL with 1-50 employees
```

Expected: List of gym businesses with names, locations, contact info

### Local Business Search
```
Find restaurants in Fort Myers FL
```

Expected: List of restaurant businesses

### Advanced Search (Company Template Detection)
```
Search for HVAC companies in Naples for Southwest Florida Comfort
```

Expected: Apollo MCP detects "Southwest Florida Comfort" company context and applies appropriate filters

## Troubleshooting

### Apollo MCP Not Listed
- Verify config syntax is valid JSON (no trailing commas)
- Restart Claude Desktop again
- Check Terminal/Console for error messages

### Authentication Errors
- Verify APOLLO_API_KEY is correct
- Get API key from: https://app.apollo.io/settings/integrations

### No Results Returned
- Check Apollo.io account has available credits
- Verify search query is specific enough (location + industry)
- Try broader search terms

## Test Workflow

Once working, try the full outreach pipeline:

```
Run cold outreach for Naples gyms for Marceau Solutions
```

This will:
1. Search Apollo for gyms in Naples
2. Filter to owner/decision maker titles
3. Score leads based on company data
4. Enrich top 20% with phone/email
5. Return leads ready for SMS campaign

**Note:** This costs credits (2 per enrichment). Test with small batches first.
