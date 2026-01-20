# Workflow: Scrape Local Business Leads

## Overview

This workflow guides you through using the Lead Scraper to find local businesses for cold outreach. It covers setup, running scrapes, filtering results, and exporting data for email campaigns.

## Prerequisites

- Python 3.10+
- Google Places API key (primary source)
- Yelp API key (optional, secondary source)
- `requests` and `beautifulsoup4` packages

## Setup

### 1. Install Dependencies

```bash
pip install requests beautifulsoup4
```

### 2. Get API Keys

**Google Places API (Required)**:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable "Places API" and "Places API (New)"
4. Go to "APIs & Services" > "Credentials"
5. Create API Key
6. (Recommended) Restrict key to Places API only

**Yelp Fusion API (Optional)**:
1. Go to [Yelp Fusion](https://www.yelp.com/developers/v3/manage_app)
2. Create a new app
3. Copy your API Key

### 3. Set Environment Variables

```bash
# Add to ~/.zshrc or ~/.bash_profile
export GOOGLE_PLACES_API_KEY="your_google_key_here"
export YELP_API_KEY="your_yelp_key_here"  # Optional
```

## Usage

### Basic Commands

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Scrape single category in Naples
python -m src.scraper scrape --category "gym" --area "Naples, FL"

# Scrape all categories in Naples
python -m src.scraper scrape --all-categories --area "Naples, FL"

# Scrape all categories in all configured areas (SW Florida)
python -m src.scraper scrape --all-categories --all-areas

# Scrape only using Google (faster, uses fewer API calls)
python -m src.scraper scrape --source google --all-categories --area "Naples, FL"

# Faster scrape without fetching details (less data but cheaper)
python -m src.scraper scrape --no-details --all-categories --area "Naples, FL"
```

### View Statistics

```bash
python -m src.scraper stats
```

Output:
```
=== Lead Statistics ===
Total leads: 1234
With email: 156
With phone: 1102
With website: 987

By Category:
  gym: 234
  real estate agency: 189
  ...

By City:
  Naples: 456
  Fort Myers: 312
  ...
```

### Filter Leads

```bash
# Find gyms without websites (great opportunity!)
python -m src.scraper filter --category gym --pain-point no_website

# Find all businesses in Naples with phone numbers
python -m src.scraper filter --city Naples --has-phone

# Find businesses with low ratings (need help!)
python -m src.scraper filter --pain-point low_rating

# Export filtered results
python -m src.scraper filter --category gym --city Naples --export naples_gyms
```

### Export Data

```bash
# Export all leads to CSV and JSON
python -m src.scraper export --format both

# Export just CSV with custom filename
python -m src.scraper export --format csv --filename naples_leads_2026-01

# Export to JSON only
python -m src.scraper export --format json
```

## Targeting High-Value Leads

### Pain Point Filters

Leads with these pain points are excellent prospects for automation consulting:

| Pain Point | Meaning | Opportunity |
|------------|---------|-------------|
| `no_website` | No website found | Web design + automation |
| `outdated_website` | Website looks old | Website redesign |
| `no_online_booking` | Can't book online | Booking system |
| `few_reviews` | Less than 10 reviews | Review automation |
| `low_rating` | Below 3.5 stars | Reputation management |
| `no_reviews` | Zero reviews | Review solicitation |

### Best Categories for Automation

1. **Fitness/Gyms** - Member management, booking, billing
2. **Personal Trainers** - Scheduling, client tracking
3. **Real Estate** - Lead follow-up, listing management
4. **Moving Companies** - Quote automation, scheduling
5. **HVAC/Plumbers** - Dispatch, invoicing, scheduling
6. **Salons/Spas** - Booking, inventory, client reminders

### Sample Scraping Strategy

```bash
# Day 1: Naples gyms and fitness
python -m src.scraper scrape -c "gym" -a "Naples, FL"
python -m src.scraper scrape -c "personal trainer" -a "Naples, FL"
python -m src.scraper scrape -c "fitness center" -a "Naples, FL"

# Day 2: Real estate and moving
python -m src.scraper scrape -c "real estate agency" -a "Naples, FL"
python -m src.scraper scrape -c "moving company" -a "Naples, FL"

# Day 3: Service businesses
python -m src.scraper scrape -c "hvac contractor" -a "Naples, FL"
python -m src.scraper scrape -c "plumber" -a "Naples, FL"
python -m src.scraper scrape -c "electrician" -a "Naples, FL"

# Export prioritized leads
python -m src.scraper filter --pain-point no_website --export high_priority
python -m src.scraper filter --pain-point no_online_booking --export booking_opportunity
```

## Enriching Leads with Email

The scraper can analyze business websites to find email addresses:

```python
# In Python
from src.scraper import LeadScraperCLI
from src.enrichment import LeadEnricher

scraper = LeadScraperCLI()
enricher = LeadEnricher()

# Get leads without emails
leads_no_email = [l for l in scraper.leads.leads.values() if not l.email and l.website]

# Enrich them (rate-limited, be patient)
for lead in leads_no_email[:50]:  # Do 50 at a time
    enricher.enrich_lead(lead)

# Save enriched data
scraper.leads.save_csv("leads_enriched.csv")
```

## Opt-Out Management

Respect businesses that don't want to be contacted:

```bash
# Add to opt-out list
python -m src.scraper optout --add "business@example.com"
python -m src.scraper optout --add "Acme Gym"
python -m src.scraper optout --add "239-555-1234"

# View opt-out list
python -m src.scraper optout --list
```

## API Cost Estimation

### Google Places API
- **Nearby Search**: $32 per 1,000 requests
- **Place Details**: $17-$30 per 1,000 requests
- **Free tier**: $200/month (~6,000 basic searches)

### Yelp API
- **Free tier**: 500 calls/day (no cost)

### Cost Example

Scraping all categories in Naples (~17 categories):
- Nearby searches: ~17 requests
- Detail fetches: ~500 requests (assuming 30 results/category)
- **Estimated cost**: ~$15-20 (under free tier)

Full SW Florida scan (6 areas, 17 categories):
- Nearby searches: ~102 requests
- Detail fetches: ~3,000 requests
- **Estimated cost**: ~$100-150

## Output Files

All output goes to `projects/lead-scraper/output/`:

| File | Description |
|------|-------------|
| `leads.csv` | All leads in CSV format |
| `leads.json` | All leads in JSON format |
| `optout_list.json` | Opted-out identifiers |
| `scrape_progress.json` | Resume data (if interrupted) |

### CSV Columns

```
id, source, business_name, owner_name, email, phone, website,
facebook, instagram, linkedin, twitter, address, city, state,
zip_code, latitude, longitude, category, subcategories, rating,
review_count, price_level, pain_points, notes, scraped_at, last_updated
```

## Troubleshooting

### "No API key configured"

Set environment variables:
```bash
export GOOGLE_PLACES_API_KEY="your_key"
source ~/.zshrc  # or ~/.bash_profile
```

### "REQUEST_DENIED" from Google

1. Check API is enabled in Cloud Console
2. Check API key restrictions
3. Ensure billing is set up

### "Rate limit hit"

The scraper automatically backs off. For faster scrapes:
```bash
# Use --no-details to reduce API calls
python -m src.scraper scrape --no-details --all-categories
```

### Duplicate leads

Deduplication is automatic based on business name + address + phone. Duplicates from different sources are merged.

## Best Practices

1. **Start small**: Test with one category in one area first
2. **Use --no-details**: For initial scans, skip details to save API costs
3. **Filter then enrich**: Only enrich high-priority leads
4. **Respect opt-outs**: Add businesses that ask to be removed
5. **Rate limit**: Don't hammer APIs; the scraper handles this automatically
6. **Save progress**: The scraper auto-saves periodically

## Next Steps After Scraping

1. **Filter high-priority leads**: Focus on `no_website` and `no_online_booking`
2. **Enrich with emails**: Run enrichment on top prospects
3. **Import to email tool**: Use CSV export for Mailshake, Lemlist, etc.
4. **Personalize outreach**: Use pain points to customize messages
5. **Track responses**: Add responders to opt-out if they decline
