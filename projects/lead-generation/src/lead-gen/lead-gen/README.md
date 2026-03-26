# Square Foot Shipping - Lead Generation

**E-commerce lead scraper focused on finding businesses with shipping volume of 100-1000 packages/month.**

This directory contains scripts that leverage the existing `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper` infrastructure to find and qualify e-commerce sellers who need shipping services.

---

## Scripts Overview

### 1. `scrape_ecommerce_leads.py`
**Purpose**: Scrape and identify e-commerce businesses with shipping needs

**Target Profile**:
- E-commerce stores (Shopify, WooCommerce, Amazon FBA sellers)
- Physical goods (not digital products)
- Estimated shipping volume: 100-1000 packages/month
- Located in SW Florida (expanding nationwide)

**How It Works**:
- Uses Google Places API and Yelp API to find businesses
- Filters for e-commerce categories (online stores, retail with websites, etc.)
- Estimates shipping volume based on review count and website indicators
- Outputs qualified leads to `scraped-leads/scraped-leads.json`

---

### 2. `qualify_leads.py`
**Purpose**: Score and categorize scraped leads (HOT/WARM/COLD)

**Scoring Criteria** (0-10 scale):
| Factor | Weight | Scoring |
|--------|--------|---------|
| **Shipping Volume** | 30% | 100-1000/mo = 10pts, 50-100 = 7pts, 10-50 = 5pts |
| **Business Type** | 30% | E-commerce/Physical goods = 10pts, Retail = 8pts |
| **Contact Quality** | 20% | Email+Phone+Name = 10pts, Email+Phone = 9pts |
| **Location** | 20% | US-based = 10pts, Canada/Mexico = 7pts |

**Lead Categories**:
- **HOT** (8-10): High-volume e-commerce, complete contact info, US-based
- **WARM** (5-7): Medium-volume, some contact info missing
- **COLD** (1-4): Low-volume or poor data quality

---

## Usage

### Step 1: Scrape E-commerce Leads

**Dry Run** (test without making API calls):
```bash
python scrape_ecommerce_leads.py --dry-run --limit 10
```

**Scrape Naples area**:
```bash
python scrape_ecommerce_leads.py --area "Naples, FL" --limit 50
```

**Scrape all SW Florida areas**:
```bash
python scrape_ecommerce_leads.py --all-areas --limit 100
```

**Scrape specific areas**:
```bash
python scrape_ecommerce_leads.py --area "Fort Myers, FL" --area "Cape Coral, FL" --limit 75
```

**Output**: `scraped-leads/scraped-leads.json`

---

### Step 2: Qualify and Score Leads

**Score all leads and save**:
```bash
python qualify_leads.py --input scraped-leads/scraped-leads.json --output qualified-leads.json
```

**Show only HOT leads** (score 8-10):
```bash
python qualify_leads.py --input scraped-leads/scraped-leads.json --show-hot
```

**Show WARM leads**:
```bash
python qualify_leads.py --input scraped-leads/scraped-leads.json --show-warm
```

**Show leads with minimum score**:
```bash
python qualify_leads.py --input scraped-leads/scraped-leads.json --min-score 7
```

**Output**: `qualified-leads.json`

---

## Output Format

### `scraped-leads.json` Structure
```json
{
  "scrape_date": "2026-01-19T17:00:00",
  "total_scraped": 145,
  "qualified_count": 67,
  "leads": [
    {
      "business_name": "Naples Fitness Apparel",
      "contact_name": "John Smith",
      "phone": "+1-239-555-0100",
      "email": "john@naplesfit.com",
      "website": "https://naplesfit.com",
      "address": "123 Main St",
      "city": "Naples",
      "state": "FL",
      "category": "online store",
      "rating": 4.5,
      "review_count": 87,
      "volume_tier": "medium",
      "estimated_packages_min": 100,
      "estimated_packages_max": 500,
      "confidence": 0.7,
      "has_website": true,
      "social_media": {
        "facebook": "https://facebook.com/naplesfit",
        "instagram": "@naplesfit"
      },
      "scraped_at": "2026-01-19T17:00:00"
    }
  ]
}
```

### `qualified-leads.json` Structure
```json
{
  "qualified_leads": [
    {
      "business_name": "Naples Fitness Apparel",
      "email": "john@naplesfit.com",
      "phone": "+1-239-555-0100",
      "score": 8.5,
      "category": "HOT",
      "score_breakdown": {
        "volume": 10.0,
        "business_type": 10.0,
        "contact_quality": 9.0,
        "location": 10.0
      }
    }
  ],
  "total_count": 67,
  "hot_count": 12,
  "warm_count": 38,
  "cold_count": 17
}
```

---

## Filtering Criteria

### E-commerce Categories Targeted
- Online stores
- E-commerce
- Retail stores with websites
- Gift shops
- Boutiques
- Sporting goods
- Home goods
- Apparel stores
- Electronics stores
- Jewelry stores
- Toy stores
- Bookstores
- Pet stores
- Health food stores
- Vitamin stores

### Volume Estimation Logic

**HIGH** (500-1000 packages/month):
- Review count ≥ 100
- Keywords: "nationwide shipping", "ships worldwide", "free shipping"

**MEDIUM** (100-500 packages/month):
- Review count ≥ 30
- Keywords: "online orders", "delivery available", "shop online"

**LOW** (10-100 packages/month):
- Review count ≥ 10
- Keywords: "shipping", "mail order"

---

## Dependencies

### Required Environment Variables
Set in `/Users/williammarceaujr./dev-sandbox/.env`:

```bash
GOOGLE_PLACES_API_KEY=your_key_here
YELP_API_KEY=your_key_here
```

### Python Dependencies
All dependencies come from the dev-sandbox lead-scraper project:
- `google-places` (Google Places API client)
- `yelp-fusion` (Yelp API client)
- `python-dotenv` (Environment variable management)

**No additional installation required** - scripts use the existing dev-sandbox infrastructure.

---

## Workflow Example

```bash
# 1. Test setup (dry run)
python scrape_ecommerce_leads.py --dry-run --limit 10

# 2. Scrape e-commerce leads (Naples area)
python scrape_ecommerce_leads.py --area "Naples, FL" --limit 50

# 3. Qualify and score leads
python qualify_leads.py --input scraped-leads/scraped-leads.json --output qualified-leads.json

# 4. Review HOT leads
python qualify_leads.py --input scraped-leads/scraped-leads.json --show-hot

# 5. Export for outreach (HOT leads only)
# Use qualified-leads.json, filter by category == "HOT"
```

---

## Notes

### Volume Estimation Accuracy
The shipping volume estimates are **heuristic-based** and should be validated during outreach:
- Review count is a rough proxy for business volume
- Website keyword analysis improves confidence
- Always confirm actual volume during discovery calls

### Contact Information
- Not all leads will have email addresses
- Phone numbers are typically from Google/Yelp business listings
- Use `qualify_leads.py` to prioritize leads with complete contact info

### Lead Nurturing
Once qualified:
1. **HOT leads** → Immediate outreach (personal email/call)
2. **WARM leads** → Follow-up sequence (3-5 touches)
3. **COLD leads** → Archive for future campaigns

---

## Troubleshooting

### Error: "No module named 'src.scraper'"
**Solution**: The script can't find the dev-sandbox lead-scraper. Verify path:
```bash
ls /Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/scraper.py
```

### Error: "API key not found"
**Solution**: Check that environment variables are set in `/Users/williammarceaujr./dev-sandbox/.env`:
```bash
grep GOOGLE_PLACES_API_KEY /Users/williammarceaujr./dev-sandbox/.env
grep YELP_API_KEY /Users/williammarceaujr./dev-sandbox/.env
```

### No leads found
**Possible causes**:
- Area name doesn't match Google/Yelp format
- E-commerce categories not present in that area
- API rate limits hit (check logs)

**Solution**: Try different areas or increase limit

---

## Integration with dev-sandbox

This project **reuses** the existing lead-scraper infrastructure:

| Component | Location |
|-----------|----------|
| **Lead scraper engine** | `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/scraper.py` |
| **Data models** | `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/models.py` |
| **API configs** | `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/config.py` |
| **Google Places** | `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/google_places.py` |
| **Yelp scraper** | `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/yelp.py` |
| **Environment vars** | `/Users/williammarceaujr./dev-sandbox/.env` |

**No duplication** - wrapper scripts configure the existing engine for e-commerce focus.

---

## Future Enhancements

- [ ] Add Shopify store detection (check if website uses Shopify)
- [ ] Integrate Amazon Seller API to find FBA sellers
- [ ] Add website scraping for shipping volume clues (product count, inventory size)
- [ ] Connect to Apollo.io for enrichment (owner email, LinkedIn)
- [ ] Automated follow-up sequences (email + SMS campaigns)

---

**Questions?** Review the dev-sandbox lead-scraper documentation:
- `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/README.md`
- `/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/workflows/`
