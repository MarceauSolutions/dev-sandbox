# Apollo.io Search Filters - Complete Reference

**Last Updated**: 2026-01-21

This document describes all available search filters for the Apollo.io API, as implemented in `src/apollo.py`.

---

## Quick Start

```python
from src.apollo import (
    ApolloClient,
    PeopleSearchFilters,
    OrganizationSearchFilters,
    SearchProfiles,
    Seniority,
    EmailStatus,
    EmployeeRange,
    Department,
    RevenueRange
)

# Initialize client
client = ApolloClient()

# Option 1: Use a preset profile (easiest)
filters = SearchProfiles.naples_gyms()
results = client.search_people_advanced(filters)

# Option 2: Build custom filters
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER],
    person_locations=["Naples, FL"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
    contact_email_status=[EmailStatus.VERIFIED],
    q_keywords="gym fitness",
    per_page=100
)
results = client.search_people_advanced(filters)

# Option 3: Use profile name string
results = client.search_with_profile("small_business_owners", location="Naples, FL", industry_keyword="gym")
```

---

## People Search Filters

### Person Filters

| Filter | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `person_titles` | `List[str]` | Job titles to include | `["owner", "ceo", "founder"]` |
| `person_not_titles` | `List[str]` | Job titles to exclude | `["intern", "assistant"]` |
| `person_seniorities` | `List[Seniority]` | Seniority levels | `[Seniority.OWNER, Seniority.C_SUITE]` |
| `person_locations` | `List[str]` | Person's location | `["Naples, FL", "Florida"]` |
| `person_departments` | `List[Department]` | Department filter | `[Department.SALES, Department.EXECUTIVE]` |

### Seniority Values

```python
from src.apollo import Seniority

Seniority.OWNER      # "owner"
Seniority.FOUNDER    # "founder"
Seniority.C_SUITE    # "c_suite" (CEO, CFO, CTO, etc.)
Seniority.PARTNER    # "partner"
Seniority.VP         # "vp"
Seniority.HEAD       # "head"
Seniority.DIRECTOR   # "director"
Seniority.MANAGER    # "manager"
Seniority.SENIOR     # "senior"
Seniority.ENTRY      # "entry"
Seniority.INTERN     # "intern"
```

### Contact Quality Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `contact_email_status` | `List[EmailStatus]` | Email verification status | `[EmailStatus.VERIFIED]` |
| `has_email` | `bool` | Only contacts with email | `True` |
| `has_phone` | `bool` | Only contacts with phone | `True` |

### Email Status Values

```python
from src.apollo import EmailStatus

EmailStatus.VERIFIED     # Verified email (highest quality)
EmailStatus.GUESSED      # Guessed/pattern-based email
EmailStatus.UNAVAILABLE  # Email not available
EmailStatus.BOUNCED      # Email bounced
EmailStatus.PENDING      # Verification pending
```

### Organization Filters (for People Search)

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `organization_locations` | `List[str]` | Company HQ location | `["Naples, FL"]` |
| `organization_domains` | `List[str]` | Company domains | `["example.com"]` |
| `organization_ids` | `List[str]` | Apollo organization IDs | `["abc123"]` |
| `organization_num_employees_ranges` | `List[EmployeeRange]` | Employee count | `[EmployeeRange.SMALL]` |
| `organization_not_locations` | `List[str]` | Exclude locations | `["New York, NY"]` |

### Employee Range Values

```python
from src.apollo import EmployeeRange

EmployeeRange.SOLO       # "1,1"       (1 employee)
EmployeeRange.MICRO      # "1,10"      (1-10 employees)
EmployeeRange.SMALL      # "11,50"     (11-50 employees)
EmployeeRange.MEDIUM     # "51,200"    (51-200 employees)
EmployeeRange.LARGE      # "201,500"   (201-500 employees)
EmployeeRange.ENTERPRISE # "501,1000"  (501-1000 employees)
EmployeeRange.MEGA       # "1001,5000" (1001-5000 employees)
EmployeeRange.MASSIVE    # "5001,10000"
EmployeeRange.HUGE       # "10001,"    (10001+ employees)
```

### Industry/Keyword Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `q_keywords` | `str` | Keyword search | `"gym fitness health"` |
| `q_organization_keyword_tags` | `List[str]` | Industry tags | `["fitness", "gym"]` |

### Technology Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `currently_using_any_of_technology_uids` | `List[str]` | Using these techs | `["wordpress"]` |
| `not_using_any_of_technology_uids` | `List[str]` | NOT using these | `["shopify", "wix"]` |

### Revenue Filter

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `revenue_range` | `RevenueRange` | Company revenue | `RevenueRange.R_1M_10M` |

### Revenue Range Values

```python
from src.apollo import RevenueRange

RevenueRange.UNDER_1M     # $0 - $1M
RevenueRange.R_1M_10M     # $1M - $10M
RevenueRange.R_10M_50M    # $10M - $50M
RevenueRange.R_50M_100M   # $50M - $100M
RevenueRange.R_100M_500M  # $100M - $500M
RevenueRange.R_500M_1B    # $500M - $1B
RevenueRange.OVER_1B      # $1B+
```

### Prospecting Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `prospected_by_current_team` | `bool` | Already contacted by team | `False` |
| `revealed_for_current_team` | `bool` | Already revealed (credited) | `False` |

---

## Organization Search Filters

Use `OrganizationSearchFilters` for company-level searches:

```python
from src.apollo import OrganizationSearchFilters, EmployeeRange

filters = OrganizationSearchFilters(
    organization_locations=["Naples, FL"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
    q_organization_keyword_tags=["gym", "fitness"],
    organization_not_technologies=["shopify"],  # Not using Shopify
    organization_founded_year_min=2015
)
results = client.search_organizations_advanced(filters)
```

### Additional Organization Filters

| Filter | Type | Description |
|--------|------|-------------|
| `organization_technologies` | `List[str]` | Using these technologies |
| `organization_not_technologies` | `List[str]` | NOT using these technologies |
| `organization_latest_funding_stage_cd` | `List[str]` | Funding stage (seed, series_a, etc.) |
| `organization_founded_year_min` | `int` | Founded after this year |
| `organization_founded_year_max` | `int` | Founded before this year |

---

## Search Profiles (Pre-built Templates)

Use `SearchProfiles` for common search patterns:

### Available Profiles

| Profile | Description | Parameters |
|---------|-------------|------------|
| `small_business_owners` | Owners/founders at 1-50 employee companies | `location`, `industry_keyword` |
| `verified_contacts_only` | Only verified emails | `location`, `industry_keyword` |
| `decision_makers_all_sizes` | Decision-makers at any company size | `location`, `titles` |
| `local_service_businesses` | Local service companies | `location`, `industry_tags` |
| `no_tech_stack` | Businesses NOT using certain tech | `location`, `exclude_technologies` |
| `naples_gyms` | Pre-configured Naples FL gyms | None |
| `naples_hvac` | Pre-configured Naples FL HVAC | None |
| `naples_restaurants` | Pre-configured Naples FL restaurants | None |

### Using Profiles

```python
from src.apollo import ApolloClient, SearchProfiles, EmailStatus

client = ApolloClient()

# Use preset Naples profile
filters = SearchProfiles.naples_gyms()
results = client.search_people_advanced(filters)

# Use generic profile with customization
filters = SearchProfiles.small_business_owners("Fort Myers, FL", "restaurant")
filters.contact_email_status = [EmailStatus.VERIFIED]  # Add filter
results = client.search_people_advanced(filters)

# Use profile by name
results = client.search_with_profile(
    "small_business_owners",
    location="Naples, FL",
    industry_keyword="gym"
)
```

---

## Pagination

### Single Page

```python
filters = PeopleSearchFilters(
    person_locations=["Naples, FL"],
    page=1,
    per_page=100  # Max 100
)
results = client.search_people_advanced(filters)
```

### All Pages

```python
# Automatically handles pagination
filters = SearchProfiles.naples_gyms()
all_leads = client.search_all_pages(filters, max_results=500)
```

---

## Best Practices

### 1. Use Verified Email Filter for Outreach

```python
# For cold email campaigns - only verified emails
filters = PeopleSearchFilters(
    person_locations=["Naples, FL"],
    contact_email_status=[EmailStatus.VERIFIED],
    ...
)
```

### 2. Combine Multiple Filters for Quality

```python
# High-quality lead filter
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
    person_locations=["Naples, FL"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
    contact_email_status=[EmailStatus.VERIFIED],
    q_keywords="gym",
    prospected_by_current_team=False,  # New leads only
    per_page=100
)
```

### 3. Exclude Bad Fit Leads

```python
filters = PeopleSearchFilters(
    person_titles=["owner", "ceo"],
    person_not_titles=["intern", "assistant", "coordinator"],  # Exclude
    organization_not_locations=["New York, NY"],  # Exclude NYC
    not_using_any_of_technology_uids=["enterprise-software"],  # Not enterprise
    ...
)
```

### 4. Technology-Based Targeting

```python
# Find businesses without a website builder (opportunity!)
filters = PeopleSearchFilters(
    person_locations=["Naples, FL"],
    not_using_any_of_technology_uids=["wordpress", "wix", "squarespace", "shopify"],
    ...
)
```

---

## API Response Format

### People Search Response

```python
{
    "people": [
        {
            "id": "abc123",
            "first_name": "John",
            "last_name": "Smith",
            "title": "Owner",
            "email": "john@example.com",
            "email_status": "verified",
            "phone_numbers": [{"raw_number": "+1234567890"}],
            "linkedin_url": "https://linkedin.com/in/johnsmith",
            "organization": {
                "name": "Acme Gym",
                "website_url": "https://acmegym.com",
                "estimated_num_employees": 15,
                "industry": "Health & Fitness"
            }
        },
        ...
    ],
    "pagination": {
        "page": 1,
        "per_page": 100,
        "total_entries": 250,
        "total_pages": 3
    }
}
```

---

## Integration with Pipeline

The enhanced filters work with the existing pipeline:

```bash
# Use advanced filters in pipeline
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, verified email, 1-50 employees" \
    --campaign "Naples Gyms Q1" \
    --dry-run
```

Or programmatically:

```python
from src.apollo import ApolloClient, SearchProfiles
from src.apollo_pipeline import ApolloPipeline

# Search with filters
client = ApolloClient()
filters = SearchProfiles.naples_gyms()
results = client.search_all_pages(filters, max_results=100)

# Feed into pipeline
pipeline = ApolloPipeline()
# ... continue with SMS campaign
```

---

## Common Filter Combinations

### Local Small Business Outreach

```python
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER],
    person_locations=["Naples, FL"],
    organization_num_employees_ranges=[EmployeeRange.SOLO, EmployeeRange.MICRO, EmployeeRange.SMALL],
    contact_email_status=[EmailStatus.VERIFIED],
    per_page=100
)
```

### Service Business (HVAC, Plumbing, etc.)

```python
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
    person_locations=["Naples, FL", "Fort Myers, FL"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL, EmployeeRange.MEDIUM],
    q_organization_keyword_tags=["hvac", "plumbing", "electrical", "contractor"],
    per_page=100
)
```

### Restaurants & Hospitality

```python
filters = PeopleSearchFilters(
    person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.MANAGER],
    person_locations=["Naples, FL"],
    q_organization_keyword_tags=["restaurant", "hospitality", "food service"],
    organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
    per_page=100
)
```

---

## Troubleshooting

### No Results

1. Check location spelling: `"Naples, FL"` not `"naples fl"`
2. Broaden employee range: Include more `EmployeeRange` values
3. Remove restrictive filters one at a time
4. Try without `contact_email_status` (may limit results)

### Too Many Results

1. Add `contact_email_status=[EmailStatus.VERIFIED]`
2. Narrow `person_seniorities`
3. Add `organization_num_employees_ranges`
4. Add industry-specific `q_organization_keyword_tags`

### API Errors

```python
# Check API key
import os
print(os.getenv("APOLLO_API_KEY"))  # Should not be None

# Test connection
client = ApolloClient()
results = client.search_people(person_locations=["Naples, FL"], per_page=5)
print(results)
```

---

## Related Files

- `src/apollo.py` - Main Apollo client with filters
- `src/apollo_mcp_bridge.py` - MCP bridge integration
- `src/apollo_pipeline.py` - Full pipeline automation
- `ZAPIER_APOLLO_CLICKUP.md` - Zapier integration guide
