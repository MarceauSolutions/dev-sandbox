# Apollo.io MCP Server

mcp-name: io.github.wmarceau/apollo

MCP (Model Context Protocol) server that provides Apollo.io lead enrichment, prospecting, and company search capabilities through Claude and other AI assistants.

## Features

- **Full Outreach Pipeline** - End-to-end automation from natural language prompt to enriched leads
- **Company Context Detection** - Auto-detect which company (Southwest Florida Comfort, Marceau Solutions, Footer Shipping)
- **Iterative Search Refinement** - Automatically filters out sales reps and low-quality leads
- **Lead Quality Scoring** - Ranks leads by title, contact info, and company data
- **People Search** - Find contacts by title, location, company, and more (with excluded_titles support)
- **Company Search** - Search for businesses by location, industry, size
- **Lead Enrichment** - Reveal email addresses and phone numbers (costs credits)
- **Decision Maker Finder** - Find owners, CEOs, and managers at companies
- **Local Business Search** - Quick search for local businesses by location and industry

## Installation

### Via pip (when published to PyPI)

```bash
pip install apollo-mcp
```

### From source

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
pip install -e .
```

## Configuration

You need an Apollo.io API key to use this MCP server.

1. Sign up at [Apollo.io](https://www.apollo.io/)
2. Get your API key from [Settings > Integrations](https://app.apollo.io/settings/integrations)
3. Set the environment variable:

```bash
export APOLLO_API_KEY="your-api-key-here"
```

Or add to your `.env` file:

```
APOLLO_API_KEY=your-api-key-here
```

## Usage with Claude Desktop

Add this to your Claude Desktop configuration:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

## Available Tools

### End-to-End Pipeline

#### `run_full_outreach_pipeline`
**NEW**: Execute the complete lead generation workflow with a single natural language prompt.

**What it does:**
1. Detects company context (Southwest Florida Comfort, Marceau Solutions, Footer Shipping)
2. Loads company-specific search template
3. Executes search with automatic title exclusions
4. Validates results and refines search (up to 3 iterations)
5. Scores leads by quality
6. Selects top 20% for enrichment
7. Enriches leads (reveals emails/phones - costs credits)
8. Returns enriched leads ready for SMS campaigns

**Example prompts:**
- "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
- "Find gyms in Miami for Marceau Solutions"
- "Get e-commerce leads for Footer Shipping"

**Parameters:**
- `prompt` - Natural language description (required)
- `max_results` - Maximum initial search results (default: 100)
- `enrich_top_n` - Number of top leads to enrich (default: 20)
- `skip_enrichment` - Skip enrichment to save credits (default: false)

**Benefits:**
- Eliminates manual CSV export/import steps
- Automatic filtering of sales reps and assistants
- Quality scoring ensures you enrich the best leads
- Company-specific templates ensure consistent targeting

### Search Tools

#### `search_people`
Search Apollo's database for people matching criteria.

**Example prompts:**
- "Search Apollo for gym owners in Naples, FL"
- "Find CEOs at companies with 10-50 employees in Florida"
- "Search for marketing managers in Miami"

**Parameters:**
- `person_titles` - Job titles (e.g., ['owner', 'ceo', 'manager'])
- `person_locations` - Person locations (e.g., ['Naples, FL'])
- `organization_locations` - Company locations
- `organization_num_employees_ranges` - Company size (e.g., ['1,10', '11,50'])
- `q_keywords` - Keyword search
- `excluded_titles` - **NEW**: Exclude people with these title keywords (e.g., ['sales', 'assistant'])
- `page` - Page number (default: 1)
- `per_page` - Results per page, max 100 (default: 25)

#### `search_companies`
Search for companies by location, industry, and size.

**Example prompts:**
- "Search Apollo for gyms in Naples with 1-50 employees"
- "Find restaurants in Miami, FL"

**Parameters:**
- `organization_locations` - Locations
- `organization_num_employees_ranges` - Size ranges
- `q_keywords` - Keyword search
- `page`, `per_page` - Pagination

#### `search_local_businesses`
Convenience method for local business search.

**Example prompts:**
- "Search Apollo for gyms in Naples, FL with 1-50 employees"
- "Find local restaurants in Miami"

**Parameters:**
- `location` - Location string (required)
- `industry_keywords` - Industry/keyword
- `employee_range` - Size range (default: "1,50")
- `max_results` - Max results (default: 100)

### Enrichment Tools

#### `enrich_person`
Reveal full contact details for a person. **COSTS APOLLO CREDITS**.

**Example prompts:**
- "Enrich the contact info for john.doe@example.com"
- "Get contact details for John Smith at Example Corp"

**Parameters:**
- `email` - Email address
- `first_name`, `last_name`, `domain` - Name and company
- `linkedin_url` - LinkedIn profile

#### `enrich_company`
Get detailed company information.

**Example prompts:**
- "Enrich company data for example.com"
- "Get details about Acme Corporation"

**Parameters:**
- `domain` - Company domain
- `name` - Company name

### Decision Maker Tools

#### `find_decision_makers`
Find owners, CEOs, and managers at a company.

**Example prompts:**
- "Find decision makers at example.com"
- "Who are the owners and managers at Acme Corp?"

**Parameters:**
- `company_domain` - Company domain (required)
- `titles` - Custom titles (default: owner, ceo, president, founder, manager, director)

#### `find_email`
Find email address for a person. **COSTS APOLLO CREDITS**.

**Example prompts:**
- "Find email for John Smith at example.com"

**Parameters:**
- `first_name`, `last_name`, `domain` - All required

### Account Management

#### `get_credit_balance`
Note: Apollo API doesn't provide a direct credit balance endpoint. Check your balance at https://app.apollo.io/settings/credits

## Company Templates

The MCP includes pre-configured search templates for three companies:

### Southwest Florida Comfort (HVAC)
- **Target:** HVAC businesses in Southwest Florida
- **Titles:** Owner, CEO, President, Founder, General Manager
- **Location:** Naples, FL (customizable)
- **Employee range:** 1-50
- **Exclusions:** Sales reps, coordinators, assistants
- **SMS template:** `swfl_comfort_hvac_intro`

### Marceau Solutions (AI Automation)
- **Target:** Small businesses needing automation
- **Industries:** Restaurants, Fitness, Medical, Professional Services
- **Titles:** Owner, CEO, Founder, Manager
- **Location:** Southwest Florida (customizable)
- **Employee range:** 1-50
- **Exclusions:** Sales, marketing coordinators, assistants, interns
- **SMS template:** `marceau_no_website_intro`

### Footer Shipping (E-commerce)
- **Target:** E-commerce businesses
- **Industries:** E-commerce, Online Retail, Consumer Goods
- **Titles:** Owner, Founder, CEO, Operations Manager
- **Location:** None (nationwide)
- **Employee range:** 1-30
- **Exclusions:** Sales, warehouse, drivers, pickers
- **SMS template:** `footer_shipping_intro`

Templates are located in `/templates/` and can be customized for additional companies.

## Natural Language Examples

```
User: "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
→ Uses run_full_outreach_pipeline
→ Detects company: Southwest Florida Comfort
→ Searches HVAC businesses in Naples
→ Filters out sales reps
→ Enriches top 20 leads
→ Returns leads ready for SMS

User: "Search Apollo for gyms in Naples with 1-50 employees"
→ Uses search_local_businesses

User: "Enrich the top 5 leads from last search"
→ Uses enrich_person on each lead

User: "Find decision makers at ABC Company"
→ Uses find_decision_makers with company_domain

User: "How many Apollo credits do I have left?"
→ Returns instructions to check web dashboard
```

## API Rate Limits

Apollo.io has a rate limit of **50 requests per minute** by default. The client includes automatic rate limiting.

## Credit Usage

These operations consume Apollo credits:
- `enrich_person` - Reveals email and phone numbers
- `enrich_company` - Detailed company enrichment
- `find_email` - Email finder

Search operations (`search_people`, `search_companies`) do NOT cost credits.

## Development

### Testing the server locally

```bash
# Install in development mode
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
pip install -e .

# Test the server
python -m apollo_mcp.server
```

### Running from source

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
python src/apollo_mcp/server.py
```

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Apollo.io API Documentation: https://apolloio.github.io/apollo-api-docs/
- Apollo.io Support: https://help.apollo.io/

## Author

William Marceau Jr. - [Marceau Solutions](https://marceausolutions.com)
