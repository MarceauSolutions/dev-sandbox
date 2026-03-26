# Lead Scraper Skill

## Identity

**Name**: Lead Scraper
**Purpose**: Find local business leads for cold email outreach and automation consulting
**Version**: 1.0.0-dev

## Capabilities

### 1. Scrape Business Leads

Find local businesses using Google Places and Yelp APIs.

**Trigger phrases**:
- "Find leads in [location]"
- "Scrape [category] businesses"
- "Get local business contacts"
- "Find gyms/real estate/etc in Naples"

**Actions**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper
python -m src.scraper scrape --category "[category]" --area "[location]"
```

### 2. Filter and Export Leads

Query and export leads based on criteria.

**Trigger phrases**:
- "Show me leads without websites"
- "Find businesses with low ratings"
- "Export Naples gym leads"
- "How many leads do we have?"

**Actions**:
```bash
# View stats
python -m src.scraper stats

# Filter by pain point
python -m src.scraper filter --pain-point no_website

# Export filtered
python -m src.scraper filter --category gym --city Naples --export gym_leads
```

### 3. Enrich Leads with Email

Find email addresses from business websites.

**Trigger phrases**:
- "Find emails for these leads"
- "Enrich leads with contact info"
- "Get email addresses"

**Actions**:
```python
from src.scraper import LeadScraperCLI
from src.enrichment import LeadEnricher

scraper = LeadScraperCLI()
enricher = LeadEnricher()

leads = [l for l in scraper.leads.leads.values() if not l.email and l.website]
for lead in leads[:50]:
    enricher.enrich_lead(lead)
scraper.leads.save_csv("enriched.csv")
```

## Configuration

### Required Environment Variables

```bash
export GOOGLE_PLACES_API_KEY="your_google_key"
export YELP_API_KEY="your_yelp_key"  # Optional
```

### Target Areas (SW Florida)

- Naples, FL
- Fort Myers, FL
- Bonita Springs, FL
- Marco Island, FL
- Estero, FL
- Cape Coral, FL

### Target Categories

- Gym / Fitness Center / Personal Trainer
- Real Estate Agency
- Moving Company
- HVAC / Plumber / Electrician
- Salon / Medical Spa
- Restaurant / Retail

## Pain Points to Target

| Pain Point | Opportunity |
|------------|-------------|
| `no_website` | Web design + automation |
| `outdated_website` | Website redesign |
| `no_online_booking` | Booking system |
| `few_reviews` | Review automation |
| `low_rating` | Reputation management |

## Output

**Location**: `projects/lead-scraper/output/`

**Files**:
- `leads.csv` - All leads in spreadsheet format
- `leads.json` - All leads in JSON format
- `optout_list.json` - Businesses to exclude

## Integration

This skill can be invoked from the Personal Assistant when William asks for:
- Local business prospecting
- Lead generation for cold outreach
- Finding automation consulting prospects

## Ethical Guidelines

- Only collects publicly available information
- Respects robots.txt
- Rate-limits requests
- Maintains opt-out list
- Does not bypass authentication
