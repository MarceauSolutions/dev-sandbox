# Apollo MCP Testing Guide

## Prerequisites

1. **Apollo API Key**: Get from https://app.apollo.io/settings/integrations
2. **MCP SDK**: `pip install mcp`
3. **Dependencies**: `pip install -e .`

## Quick Start Testing

### 1. Install in Development Mode

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
pip install -e .
```

### 2. Set API Key

```bash
export APOLLO_API_KEY="your-api-key-here"
```

Or create `.env` file:
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

Run the server directly:

```bash
python -m apollo_mcp.server
```

The server will start and wait for MCP protocol messages via stdin/stdout.

## Testing with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "apollo": {
      "command": "python",
      "args": ["-m", "apollo_mcp.server"],
      "env": {
        "APOLLO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or if installed via pip:

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

Then restart Claude Desktop and try:

- "Search Apollo for gyms in Naples, FL"
- "Find decision makers at example.com"
- "Search for local restaurants in Miami with 1-50 employees"

## Manual API Testing

Test the Apollo client directly:

```python
from apollo_mcp.apollo import ApolloClient

client = ApolloClient()

# Search for companies
companies = client.search_local_businesses(
    location="Naples, FL",
    industry_keywords="gym",
    employee_range="1,50",
    max_results=10
)
print(f"Found {len(companies)} gyms in Naples")

# Search for people
result = client.search_people(
    person_titles=["owner", "ceo"],
    person_locations=["Naples, FL"],
    per_page=5
)
print(f"Found {len(result.get('people', []))} decision makers")

# Find decision makers (requires domain)
decision_makers = client.find_decision_makers(
    company_domain="example.com"
)
print(f"Found {len(decision_makers)} decision makers at example.com")
```

## Testing Credit-Based Operations

**WARNING**: These operations consume Apollo credits!

```python
from apollo_mcp.apollo import ApolloClient

client = ApolloClient()

# Enrich person (costs credits)
person = client.enrich_person(
    first_name="John",
    last_name="Smith",
    domain="example.com"
)
print(f"Email: {person.get('email')}")

# Find email (costs credits)
email = client.find_email(
    first_name="John",
    last_name="Smith",
    domain="example.com"
)
print(f"Found email: {email}")
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'apollo_mcp'`:

```bash
# Make sure you're in the project directory
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp

# Install in development mode
pip install -e .
```

### MCP SDK Not Found

If you see `Error: MCP SDK not installed`:

```bash
pip install mcp
```

### API Key Issues

If API calls fail:

1. Verify key is set: `echo $APOLLO_API_KEY`
2. Check key is valid at https://app.apollo.io/settings/integrations
3. Try a simple search first (doesn't cost credits)

### Rate Limiting

Apollo.io limits to 50 requests/minute. The client includes automatic rate limiting, but if you see 429 errors:

1. Reduce request frequency
2. Add delays between batches
3. Check Apollo dashboard for current usage

## Example Test Scenarios

### Scenario 1: Local Business Search

```python
client = ApolloClient()

# Search for gyms in Naples
companies = client.search_local_businesses(
    location="Naples, FL",
    industry_keywords="fitness gym",
    employee_range="1,50",
    max_results=25
)

for company in companies[:5]:
    print(f"Company: {company.get('name')}")
    print(f"  Domain: {company.get('website_url')}")
    print(f"  Employees: {company.get('estimated_num_employees')}")
    print()
```

### Scenario 2: Find Decision Makers

```python
client = ApolloClient()

# Find owners/CEOs at a company
decision_makers = client.find_decision_makers(
    company_domain="example.com",
    titles=["owner", "ceo", "president"]
)

for person in decision_makers:
    print(f"Name: {person.get('first_name')} {person.get('last_name')}")
    print(f"  Title: {person.get('title')}")
    print(f"  LinkedIn: {person.get('linkedin_url')}")
    print()
```

### Scenario 3: Search People by Title

```python
client = ApolloClient()

# Search for gym owners in Florida
result = client.search_people(
    person_titles=["owner", "founder"],
    person_locations=["Florida"],
    q_keywords="fitness gym",
    per_page=10
)

people = result.get("people", [])
print(f"Found {len(people)} gym owners in Florida")

for person in people[:5]:
    org = person.get("organization", {})
    print(f"Name: {person.get('first_name')} {person.get('last_name')}")
    print(f"  Title: {person.get('title')}")
    print(f"  Company: {org.get('name')}")
    print(f"  Location: {person.get('city')}, {person.get('state')}")
    print()
```

## Success Criteria

- ✅ `test_installation.py` runs without errors
- ✅ MCP server starts: `python -m apollo_mcp.server`
- ✅ Apollo client can search companies (no API key needed for testing)
- ✅ All imports work from package
- ✅ Package installable via `pip install -e .`

## Next Steps After Testing

1. **Manual Testing Complete** → See `docs/testing-strategy.md` Scenario 1
2. **Deploy to Production** → Use `deploy_to_skills.py` (SOP 3)
3. **Publish to PyPI** → Follow SOP 12
4. **Publish to MCP Registry** → Follow SOP 13
