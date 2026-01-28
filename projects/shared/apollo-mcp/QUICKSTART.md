# Apollo MCP - Quick Start Guide

Get up and running with Apollo MCP in 5 minutes.

## 🚀 New in v1.1.0: Full Outreach Pipeline

Run complete lead generation with a single prompt - no CSV exports!

**Try:** "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"

**Result:** Automatically searches, filters, scores, and enriches top 20 leads ready for SMS.

## Prerequisites

- Python 3.8+
- Apollo.io account with API key
- Claude Desktop (for AI integration)

## Step 1: Install (30 seconds)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
pip install -e .
```

## Step 2: Configure API Key (30 seconds)

Get your API key from https://app.apollo.io/settings/integrations

```bash
export APOLLO_API_KEY="your-api-key-here"
```

## Step 3: Test Installation (30 seconds)

```bash
python test_installation.py
```

You should see:
```
✓ Successfully imported apollo_mcp v1.0.0
✓ Apollo API key configured
✓ Apollo client initialized successfully
✓ MCP server imports successful
```

## Step 4: Add to Claude Desktop (2 minutes)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apollo": {
      "command": "python",
      "args": ["-m", "apollo_mcp.server"],
      "env": {
        "APOLLO_API_KEY": "your-api-key-here",
        "PYTHONPATH": "/Users/williammarceaujr./dev-sandbox/projects/apollo-mcp/src"
      }
    }
  }
}
```

## Step 5: Restart Claude Desktop

Quit and relaunch Claude Desktop completely.

## Step 6: Try It Out!

In Claude Desktop, try these prompts:

### NEW: Full Pipeline (v1.1.0)
```
"Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
"Find gyms in Miami for Marceau Solutions"
"Get e-commerce leads for Footer Shipping"
```

### Individual Tools
```
"Search Apollo for gyms in Naples, FL"
"Find decision makers at example.com"
"Search for restaurant owners in Miami with 1-50 employees"
```

## What You Can Do

### Free Operations (No Credits)

- **Search people** by title, location, company
- **Search companies** by location, industry, size
- **Find decision makers** at any company
- **Local business search** by location and industry

### Paid Operations (Costs Apollo Credits)

- **Enrich person** - Reveal email and phone numbers
- **Find email** - Discover email for a person
- **Enrich company** - Get detailed company information

## Example Workflows

### Find Local Leads

```
You: "Search Apollo for gyms in Naples, FL with 1-50 employees"
Claude: [Returns 25 gyms with name, domain, employee count]

You: "Find decision makers at the top 3"
Claude: [Returns owners/CEOs with titles and LinkedIn]

You: "Enrich contact info for the first one"
Claude: [Reveals email and phone - costs 1 credit]
```

### Competitive Research

```
You: "Search for fitness centers in Miami with 10-100 employees"
Claude: [Returns matching companies]

You: "For each, tell me their industry and estimated revenue"
Claude: [Uses enrich_company to get details]
```

## Troubleshooting

**Module not found?**
```bash
pip install -e .
```

**API errors?**
```bash
# Check API key
echo $APOLLO_API_KEY

# Verify at Apollo dashboard
open https://app.apollo.io/settings/integrations
```

**Claude Desktop not showing tools?**
1. Check JSON syntax in config file
2. Verify paths are correct
3. Completely quit and restart Claude Desktop

## Next Steps

- Read **README.md** for full documentation
- See **TESTING.md** for testing procedures
- Check **workflows/usage-examples.md** for advanced patterns
- Review **SETUP.md** for deployment instructions

## Get Help

- Apollo API Docs: https://apolloio.github.io/apollo-api-docs/
- MCP Protocol: https://modelcontextprotocol.io/
- Issues: Contact William Marceau Jr.

---

**That's it!** You're now ready to use Apollo.io for lead generation through Claude.
