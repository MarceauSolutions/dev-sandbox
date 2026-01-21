# Apollo Pipeline Quick Start Guide

## One-Command Full Workflow

```bash
# Dry run (preview only)
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "Naples Gyms Voice AI" \
    --template no_website_intro \
    --dry-run

# For real (sends SMS)
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "Naples Gyms Voice AI" \
    --template no_website_intro \
    --for-real
```

## Step-by-Step Manual Workflow

### 1. Import Apollo CSV
```bash
python -m src.apollo_pipeline import \
    output/apollo_export.csv \
    --campaign "Naples Gyms"
```

### 2. Filter Top 20%
```bash
python -m src.apollo_pipeline filter \
    output/apollo_leads_20260121_143522.json
```

### 3. Enrich Contacts
```bash
python -m src.apollo_pipeline enrich \
    output/apollo_leads_20260121_143522_top.json \
    --limit 50
```

### 4. Merge Enriched Data
```bash
python -m src.apollo_pipeline merge \
    output/apollo_enriched.csv \
    output/apollo_leads_20260121_143522_top.json
```

### 5. Send SMS Campaign
```bash
# Dry run first
python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --template no_website_intro \
    --dry-run

# Then for real
python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --template no_website_intro \
    --for-real
```

## Follow-Up Management

```bash
# Check what's scheduled
python -m src.follow_up_sequence queue --days 7

# Process due follow-ups
python -m src.follow_up_sequence process --for-real

# Mark response
python -m src.follow_up_sequence response "+12399999999" --type converted
```

## Campaign Analytics

```bash
# Overall performance
python -m src.campaign_analytics report

# Template comparison
python -m src.campaign_analytics templates

# Conversion funnel
python -m src.campaign_analytics funnel
```

## Key Features

- **80% Credit Savings**: Auto-scores leads before enrichment
- **Auto-Enrollment**: Leads automatically enter 3-touch sequence
- **Response Tracking**: Auto-stops sequence when lead replies
- **Template Auto-Selection**: Picks best template based on pain points

## See Full Documentation

[Apollo Automated Pipeline](apollo-automated-pipeline.md) - Complete workflow guide
