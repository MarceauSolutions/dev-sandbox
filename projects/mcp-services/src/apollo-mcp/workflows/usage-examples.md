# Apollo MCP Usage Examples

## Overview

This document provides real-world examples of using the Apollo MCP server through natural language with Claude.

## Search Operations (No Credits Required)

### Example 1: Local Business Search

**User**: "Search Apollo for gyms in Naples, FL with 1-50 employees"

**Claude uses**: `search_local_businesses`
```json
{
  "location": "Naples, FL",
  "industry_keywords": "gym fitness",
  "employee_range": "1,50",
  "max_results": 25
}
```

**Result**: List of gyms with business name, domain, employee count, industry

---

### Example 2: Find Decision Makers

**User**: "Find decision makers at example.com"

**Claude uses**: `find_decision_makers`
```json
{
  "company_domain": "example.com"
}
```

**Result**: List of owners, CEOs, presidents, founders, managers with titles and LinkedIn

---

### Example 3: People Search by Title

**User**: "Search Apollo for marketing managers in Miami"

**Claude uses**: `search_people`
```json
{
  "person_titles": ["marketing manager", "head of marketing"],
  "person_locations": ["Miami, FL"],
  "per_page": 25
}
```

**Result**: List of marketing managers with company info

---

### Example 4: Company Search

**User**: "Find restaurants in Naples with 10-100 employees"

**Claude uses**: `search_companies`
```json
{
  "organization_locations": ["Naples, FL"],
  "organization_num_employees_ranges": ["10,100"],
  "q_keywords": "restaurant"
}
```

**Result**: List of restaurants matching criteria

## Enrichment Operations (Costs Credits)

### Example 5: Enrich Person

**User**: "Get full contact details for john.smith@example.com"

**Claude uses**: `enrich_person`
```json
{
  "email": "john.smith@example.com"
}
```

**Result**: Full contact card with email, phone, title, company, social links

**Credit Cost**: 1 credit per enrichment

---

### Example 6: Find Email

**User**: "Find the email address for John Smith at Acme Corp"

**Claude uses**: `find_email`
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "domain": "acme.com"
}
```

**Result**: Email address if found

**Credit Cost**: 1 credit per lookup

---

### Example 7: Enrich Company

**User**: "Get detailed information about acme.com"

**Claude uses**: `enrich_company`
```json
{
  "domain": "acme.com"
}
```

**Result**: Company details including industry, size, revenue, technologies

**Credit Cost**: May cost credits depending on Apollo plan

## Multi-Step Workflows

### Workflow 1: Find and Enrich Local Leads

**User**: "Find gyms in Naples without websites, then get owner contact info for the first 3"

**Step 1**: Search for gyms
```
Claude uses: search_local_businesses
Location: Naples, FL
Industry: gym
```

**Step 2**: Filter results without websites
```
Claude filters where website_url is empty
```

**Step 3**: Find decision makers for each
```
Claude uses: find_decision_makers (for each company)
```

**Step 4**: Enrich top 3 contacts
```
Claude uses: enrich_person (costs 3 credits)
```

**Result**: 3 enriched contacts with email/phone for gym owners

---

### Workflow 2: Competitive Analysis

**User**: "Find all fitness centers in Naples with 1-20 employees and identify their decision makers"

**Step 1**: Search companies
```
search_local_businesses
Location: Naples, FL
Industry: fitness
Employee range: 1,20
```

**Step 2**: For each company, find decision makers
```
find_decision_makers (no credits)
```

**Result**: Comprehensive list of fitness centers with owner/manager info

---

### Workflow 3: Targeted Prospecting

**User**: "Find restaurant owners in Miami who don't have LinkedIn profiles"

**Step 1**: Search people
```
search_people
Titles: ["owner", "founder"]
Locations: ["Miami, FL"]
Keywords: "restaurant"
```

**Step 2**: Filter results
```
Claude filters where linkedin_url is null/empty
```

**Result**: Restaurant owners without LinkedIn (potential outreach targets)

## Best Practices

### Minimize Credit Usage

1. **Search first, enrich later**: Use search to find leads, then only enrich the most promising
2. **Batch operations**: Collect all leads, then enrich in batch
3. **Use free data**: Search results include basic info (name, title, company) without credits

### Effective Searching

1. **Be specific with locations**: "Naples, FL" better than "Florida"
2. **Use multiple titles**: `["owner", "ceo", "founder"]` casts wider net
3. **Combine filters**: Location + industry + size for targeted results
4. **Paginate wisely**: Start with per_page=25, increase if needed

### Credit Management

1. **Check balance regularly**: `get_credit_balance` (returns web link)
2. **Test with free searches**: Validate search criteria before enriching
3. **Enrich selectively**: Only enrich qualified leads
4. **Track usage**: Monitor how many enrichments you perform

## Common Use Cases

### Lead Generation for Sales

```
1. Search local businesses in target market
2. Filter by employee count (SMB sweet spot: 10-50)
3. Find decision makers at each company
4. Enrich top 20 prospects with full contact info
5. Export to CRM
```

### Competitive Intelligence

```
1. Search companies in competitor's market
2. Identify key players by employee count and revenue
3. Find their leadership team
4. Analyze company technologies and funding
```

### Recruitment

```
1. Search for people with specific job titles
2. Filter by location and company size
3. Find candidates at competitor companies
4. Enrich contact info for outreach
```

### Partnership Development

```
1. Search companies in complementary industries
2. Find decision makers (BD, partnerships, CEO)
3. Enrich contact info for warm outreach
4. Track company info for pitch customization
```

## Error Handling

### No Results Found

**User**: "Search Apollo for ice cream shops in Antarctica"

**Result**:
```json
{
  "success": true,
  "count": 0,
  "companies": []
}
```

**Claude response**: "No ice cream shops found in Antarctica. Try a different location or industry."

---

### Missing Required Fields

**User**: "Find email for John Smith"

**Result**: Error - missing domain

**Claude response**: "I need the company domain to find an email. What company does John Smith work for?"

---

### API Key Issues

**Result**:
```json
{
  "error": "Apollo API error",
  "hint": "Check that your APOLLO_API_KEY is configured"
}
```

**Claude response**: "Apollo API key is not configured or invalid. Please set APOLLO_API_KEY environment variable."

## Integration with Other MCPs

### Apollo + ClickUp

```
1. Search Apollo for leads
2. Find decision makers
3. Enrich top prospects
4. Create ClickUp tasks for each lead
5. Add contact info to ClickUp custom fields
```

### Apollo + Email Analyzer

```
1. Search Apollo for prospects
2. Enrich contact info
3. Use Email Analyzer to draft personalized outreach
4. Send via SMTP
```

### Apollo + Lead Scraper

```
1. Scrape Google/Yelp for businesses
2. Extract domains
3. Use Apollo to find decision makers
4. Enrich contact details
5. Add to SMS campaign
```

## Natural Language Patterns

Claude understands these patterns:

- "Search Apollo for [business type] in [location]"
- "Find [job title] at [company]"
- "Get contact info for [name] at [company]"
- "Enrich the top [N] results"
- "Find decision makers at [domain]"
- "Search for [title] in [location] with [criteria]"

## Rate Limits

Apollo API: **50 requests per minute**

The client automatically rate limits. For large batches:

```python
# Searching 500 companies = 10 minutes minimum
# Enriching 500 contacts = 10 minutes minimum
```

Plan accordingly for batch operations.
