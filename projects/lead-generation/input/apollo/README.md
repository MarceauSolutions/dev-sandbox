# Apollo.io CSV Import Directory

**Purpose**: This is where you place exported CSV files from Apollo.io for lead import and enrichment.

## How to Use

### Step 1: Export from Apollo.io
1. Log into https://app.apollo.io
2. Create search (e.g., "Gyms in Naples FL, 1-50 employees, Owner/Manager titles")
3. Click **Export** → **Download CSV** (FREE - no credits used)
4. Save as `apollo_export_YYYY-MM-DD.csv`

### Step 2: Place CSV Here
Drop your exported CSV file into this directory:
```
input/apollo/apollo_export_2026-01-21.csv
```

### Step 3: Manual Scoring (Optional)
If using credit-efficient workflow:
1. Open CSV in Excel/Numbers
2. Visit top 50 websites
3. Score each 1-10 using `APOLLO-SCORING-GUIDE.md`
4. Save as `apollo_scored_YYYY-MM-DD.csv`

### Step 4: Import to Lead Database
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper

# Import all leads (no filtering)
python -m src.apollo_import import --input input/apollo/apollo_export_2026-01-21.csv

# OR import only top 20% (scores 8-10) for credit efficiency
python -m src.apollo_import import --input input/apollo/apollo_scored_2026-01-21.csv --min-score 8
```

## File Naming Convention
- `apollo_export_YYYY-MM-DD.csv` - Raw Apollo export
- `apollo_scored_YYYY-MM-DD.csv` - Manually scored export
- `apollo_enriched_YYYY-MM-DD.csv` - After contact enrichment in Apollo

## What Gets Imported
- Business name
- Phone number (if available)
- Website URL
- Email address (if enriched)
- Decision maker name/title (if enriched)
- Industry/category tags
- Employee count
- Location

## Next Steps After Import
1. Run website validator: `python -m src.revalidate_leads_v2`
2. Assign to A/B test variant (if running tests)
3. Enroll in 7-touch sequence
4. Send first outreach batch

## Credit Management
- **Search**: FREE (unlimited)
- **Export**: FREE (unlimited)
- **Contact Enrichment**: PAID (~2-4 credits per contact)
- **Strategy**: Score → Enrich top 20% only → Save 80% of credits

See `APOLLO-MIGRATION-PLAN.md` for full workflow details.
