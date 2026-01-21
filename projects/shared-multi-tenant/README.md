# Shared Multi-Tenant Projects

**Used by ALL 3 companies:**
- Marceau Solutions
- SW Florida HVAC
- Square Foot Shipping

## Projects

### lead-scraper
Lead generation system with business_id separation.
Used by all 3 companies for local lead scraping.

### social-media-automation
Social media posting with business separation.
Schedules posts for all 3 companies.

### ai-customer-service
Voice AI phone ordering system.
Handles calls for all 3 businesses (restaurant ordering, HVAC quotes, shipping quotes).

### personal-assistant
William's personal digest and calendar system.
Global utility - no business affiliation.

## Business Separation

All shared projects use `business_id` separation in code/data:
- `business_id: "marceau-solutions"`
- `business_id: "swflorida-hvac"`
- `business_id: "square-foot-shipping"`

## Data Organization

Data is separated by business_id:
- Forms: `output/form_submissions/` with business_id in data
- SMS campaigns: `output/companies/{company}/campaigns/`
- Social posts: `output/companies/{company}/social/`
