# Lead Scraper

A local business lead generation tool for cold email outreach and automation consulting. Built to find small businesses in Southwest Florida (Naples, Fort Myers, and surrounding areas) that could benefit from automation services.

## Features

- **Multi-Source Scraping**: Google Places API (primary) + Yelp Fusion API (secondary)
- **Pain Point Detection**: Automatically identifies businesses without websites, online booking, or with low ratings
- **Lead Enrichment**: Extracts email addresses and social media from business websites
- **Deduplication**: Merges duplicate leads from multiple sources
- **Rate Limiting**: Respects API limits and avoids bans
- **Progress Saving**: Resume interrupted scrapes
- **Opt-Out Management**: Track businesses that don't want to be contacted
- **Export Formats**: CSV (for email tools) and JSON (for programmatic access)

## Quick Start

### 1. Install Dependencies

```bash
pip install requests beautifulsoup4
```

### 2. Set Up API Keys

```bash
# Required: Google Places API
export GOOGLE_PLACES_API_KEY="your_key_here"

# Optional: Yelp Fusion API
export YELP_API_KEY="your_key_here"
```

### 3. Run Your First Scrape

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# Scrape gyms in Naples
python -m src.scraper scrape --category "gym" --area "Naples, FL"

# View results
python -m src.scraper stats

# Export to CSV
python -m src.scraper export --format csv
```

## Usage

### Scraping Leads

```bash
# Single category, single area
python -m src.scraper scrape --category "gym" --area "Naples, FL"

# All configured categories in one area
python -m src.scraper scrape --all-categories --area "Naples, FL"

# All categories in all SW Florida areas
python -m src.scraper scrape --all-categories --all-areas

# Using only Google (skip Yelp)
python -m src.scraper scrape --source google --all-categories --area "Naples, FL"

# Fast mode (skip details, fewer API calls)
python -m src.scraper scrape --no-details --all-categories --area "Naples, FL"
```

### Filtering Leads

```bash
# Find businesses without websites (great prospects!)
python -m src.scraper filter --pain-point no_website

# Find gyms in Naples with phone numbers
python -m src.scraper filter --category gym --city Naples --has-phone

# Export filtered results
python -m src.scraper filter --pain-point no_online_booking --export booking_prospects
```

### Exporting

```bash
# Export all to CSV and JSON
python -m src.scraper export --format both

# Custom filename
python -m src.scraper export --format csv --filename naples_leads_jan2026
```

### Statistics

```bash
python -m src.scraper stats
```

## Target Categories

The scraper is pre-configured to find:

| Category | Automation Opportunity |
|----------|----------------------|
| Gym / Fitness Center | Member management, billing, booking |
| Personal Trainer | Client scheduling, progress tracking |
| Real Estate Agency | Lead follow-up, listing management |
| Moving Company | Quote automation, scheduling |
| HVAC / Plumber / Electrician | Dispatch, invoicing |
| Salon / Medical Spa | Appointment booking, reminders |
| Restaurant / Cafe | Reservations, online ordering |
| Dental Office | Appointment scheduling |
| Auto Repair | Service scheduling, invoicing |
| Cleaning Service | Booking, customer management |

## Target Areas

Pre-configured for Southwest Florida:

- Naples, FL
- Fort Myers, FL
- Bonita Springs, FL
- Marco Island, FL
- Estero, FL
- Cape Coral, FL

## Pain Points Detected

The scraper identifies leads with these issues:

| Pain Point | Description | Opportunity |
|------------|-------------|-------------|
| `no_website` | No website found | Web design + automation |
| `outdated_website` | Old design indicators | Website modernization |
| `no_online_booking` | Can't book online | Booking system setup |
| `few_reviews` | Under 10 reviews | Review automation |
| `no_reviews` | Zero reviews | Review solicitation |
| `low_rating` | Below 3.5 stars | Reputation management |

## Output Files

All output is saved to `output/`:

| File | Description |
|------|-------------|
| `leads.csv` | Spreadsheet format for email tools |
| `leads.json` | JSON format for programmatic access |
| `optout_list.json` | Businesses to exclude from outreach |

### CSV Columns

```
id, source, business_name, owner_name, email, phone, website,
facebook, instagram, linkedin, twitter, address, city, state,
zip_code, latitude, longitude, category, subcategories, rating,
review_count, price_level, pain_points, notes, scraped_at, last_updated
```

## API Setup

### Google Places API (Required)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable "Places API"
4. Create an API key under Credentials
5. Set `GOOGLE_PLACES_API_KEY` environment variable

**Pricing**: ~$32 per 1,000 searches. Free tier: $200/month credit.

### Yelp Fusion API (Optional)

1. Go to [Yelp Developers](https://www.yelp.com/developers/v3/manage_app)
2. Create a new app
3. Copy your API key
4. Set `YELP_API_KEY` environment variable

**Pricing**: Free (500 calls/day)

## Ethical Guidelines

This tool is designed for ethical lead generation:

- **Public Data Only**: Only collects publicly available business information
- **Robots.txt**: Respects website crawling rules
- **Rate Limiting**: Built-in delays to avoid overloading servers
- **Opt-Out**: Maintains list of businesses that don't want contact
- **No Authentication Bypass**: Never attempts to access restricted content

## Project Structure

```
lead-scraper/
├── src/
│   ├── __init__.py
│   ├── config.py         # Configuration and constants
│   ├── models.py         # Lead data model
│   ├── scraper.py        # Main CLI and orchestrator
│   ├── google_places.py  # Google Places API integration
│   ├── yelp.py           # Yelp Fusion API integration
│   └── enrichment.py     # Email discovery and enrichment
├── output/               # Scraped data output
├── workflows/
│   └── scrape-leads.md   # Usage workflow guide
├── VERSION
├── CHANGELOG.md
├── SKILL.md
└── README.md
```

## License

For personal use in automation consulting business.
