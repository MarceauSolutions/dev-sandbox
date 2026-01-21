# Apollo.io Credit-Efficient Lead Workflow

**Purpose**: Maximize Apollo.io value while minimizing credit usage (2,500 credits/month + 80 bonus)
**Strategy**: Export → Qualify → Enrich selectively (saves 80-90% credits)
**Integration**: Apollo search → Manual qualification → Selective enrichment → SMS campaign

---

## Overview

**Current Plan**: $59/month = 2,500 credits/month + 80 bonus = **2,580 total credits**

**Credit Costs**:
- Phone number reveal: **1 credit**
- Email reveal: **1 credit**
- Typical lead: **2 credits** (phone + email)
- Search & export: **FREE**

**Goal**: Get 100+ qualified leads per month while staying under credit limit

---

## Workflow Steps

### Phase 1: Free Search (0 Credits)

1. **Log into Apollo.io**: https://app.apollo.io

2. **Create targeted search** using priority filters:
   - **Location**: Naples, FL (25 mile radius)
   - **Industry**: Fitness & Recreation (or target industry)
   - **Employees**: 1-50
   - **Job Titles**: Owner, Founder, CEO, Manager
   - **Keywords**: gym, fitness center, crossfit (or target keywords)

3. **Expected results**: 50-100 companies

4. **Export to CSV** (FREE):
   - Click "Export" button
   - Select "Export list (free)" option
   - Download CSV with: Company name, website, industry, size, city

**Credits used**: 0 ✅

---

### Phase 2: Manual Qualification (0 Credits)

5. **Import CSV to lead scraper**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
   python -m src.apollo_import --file apollo_export.csv --output leads_to_score.json
   ```

6. **Visit top 50 websites** and score each lead 1-10:
   - **Pain point check**:
     - No website? (10 points - high priority)
     - No online booking? (8 points)
     - Poor Google reviews mentioning calls? (9 points - Voice AI opportunity)
     - No social media? (7 points - content automation)
     - Has website but outdated? (6 points)

   - **Budget indicators**:
     - Uses Square/Toast POS? (+2 points - has budget)
     - Multiple locations? (+2 points - can scale)
     - 10+ employees? (+1 point - bigger budget)

   - **Accessibility**:
     - Phone number visible on website? (+1 point - owner accessible)
     - Contact form only? (-1 point - harder to reach)

7. **Save scores** to spreadsheet or JSON:
   ```json
   {
     "business_name": "Naples CrossFit",
     "website": "naplescrossfit.com",
     "score": 9,
     "pain_points": ["no_website", "poor_reviews_calls"],
     "notes": "30 reviews, 10% mention missed calls, has Square POS"
   }
   ```

**Credits used**: 0 ✅

---

### Phase 3: Selective Enrichment (20-40 Credits)

8. **Filter for top 20%** (scores 8-10 only):
   ```bash
   python -m src.apollo_import --filter-scores 8-10 --output top_leads.json
   ```

9. **Enrich top leads in Apollo.io** (ONLY the qualified ones):
   - Go back to Apollo search
   - Manually select top 20 companies (8-10 scores)
   - Click "Reveal" for each contact
   - Cost: 20 leads × 2 credits = **40 credits**

10. **Export enriched leads** with phone/email:
   ```bash
   python -m src.apollo_import --enriched apollo_enriched.csv --output ready_for_outreach.json
   ```

**Credits used**: 40 (for 20 high-quality leads) ✅

---

### Phase 4: Custom Outreach (0 Credits)

11. **Use YOUR templates** (not Apollo's AI):
   - Templates already created in `templates/sms/intro/`
   - Free + better personalization

12. **Send via Twilio SMS**:
   ```bash
   python -m src.scraper sms \
     --for-real \
     --limit 20 \
     --template no_website_intro \
     --source apollo
   ```

13. **Enroll in follow-up sequence** (SOP 19):
   ```bash
   python -m src.follow_up_sequence create \
     --name "Apollo Naples Gyms" \
     --pain-point no_website \
     --source apollo
   ```

**Credits used**: 0 (using Twilio, not Apollo sending) ✅

---

## Cost Breakdown Example

### BAD Approach (Credit Wasteful):
```
1. Search for 500 gyms nationwide
2. Click "reveal all contacts" = 500 × 2 = 1,000 credits
3. Export full list
4. Send generic outreach to all 500

Total credits: 1,000
Conversion rate: 1-2% = 5-10 customers
Cost per customer: 100-200 credits
```

### GOOD Approach (Credit Efficient):
```
1. Targeted search: Naples gyms, 1-50 employees = 50 results
2. Export company data (FREE)
3. Visit websites, score 1-10
4. Reveal top 20 contacts (scores 8-10) = 20 × 2 = 40 credits
5. Personalized outreach

Total credits: 40
Conversion rate: 10-15% = 2-3 customers
Cost per customer: 13-20 credits
```

**Savings**: 96% fewer credits, similar customer count, 5x better conversion

---

## Monthly Credit Budget

**Total monthly credits**: 2,580 (2,500 plan + 80 bonus)

**Recommended allocation**:
| Campaign | Leads | Credits | % of Budget |
|----------|-------|---------|-------------|
| Naples Gyms (HVAC/Voice AI) | 20 | 40 | 1.5% |
| Fort Myers Restaurants | 20 | 40 | 1.5% |
| Cape Coral E-commerce | 20 | 40 | 1.5% |
| Naples Medical Practices | 20 | 40 | 1.5% |
| **Monthly Total** | **80 leads** | **160 credits** | **6%** |

**Buffer remaining**: 2,420 credits (94%) for:
- Additional campaigns
- Re-enrichment if contact info changes
- Testing new segments
- Emergency lead generation

**Max potential**: At 40 credits per 20-lead campaign, you could run **64 campaigns per month** (1,280 leads)

---

## Integration with Existing System

### Update `src/apollo_import.py` (new script):

```python
"""
Import and process Apollo.io exports with credit-efficient workflow.
"""

import csv
import json
from typing import List, Dict
from pathlib import Path

def import_apollo_export(
    csv_file: str,
    output_file: str,
    min_score: int = 0,
    max_score: int = 10
) -> List[Dict]:
    """
    Import Apollo CSV export and convert to our Lead format.

    Args:
        csv_file: Path to Apollo CSV export
        output_file: Where to save processed leads
        min_score: Minimum score to include (for filtering)
        max_score: Maximum score to include

    Returns:
        List of lead dicts
    """
    leads = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                "business_name": row.get("Company", ""),
                "website": row.get("Website", ""),
                "city": row.get("City", ""),
                "state": row.get("State", ""),
                "industry": row.get("Industry", ""),
                "employees": row.get("# Employees", ""),
                "phone": row.get("Phone", ""),  # Empty until enriched
                "email": row.get("Email", ""),  # Empty until enriched
                "source": "apollo",
                "score": 0,  # To be filled manually
                "pain_points": [],
                "notes": ""
            }
            leads.append(lead)

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(leads, f, indent=2)

    print(f"✅ Imported {len(leads)} leads from Apollo")
    print(f"   Saved to: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Visit each website and score 1-10")
    print(f"2. Add scores to JSON file")
    print(f"3. Filter for top 20% (scores 8-10)")
    print(f"4. Reveal contacts in Apollo for top leads only")

    return leads


def filter_by_score(
    input_file: str,
    output_file: str,
    min_score: int = 8
) -> List[Dict]:
    """
    Filter leads by score threshold.

    Args:
        input_file: JSON file with scored leads
        output_file: Where to save filtered leads
        min_score: Minimum score to include

    Returns:
        Filtered list of high-scoring leads
    """
    with open(input_file, 'r') as f:
        all_leads = json.load(f)

    top_leads = [
        lead for lead in all_leads
        if lead.get("score", 0) >= min_score
    ]

    with open(output_file, 'w') as f:
        json.dump(top_leads, f, indent=2)

    print(f"✅ Filtered to {len(top_leads)} leads (score >= {min_score})")
    print(f"   Saved to: {output_file}")
    print(f"\nNext step:")
    print(f"Go to Apollo.io and reveal contacts for these {len(top_leads)} businesses")
    print(f"Estimated cost: {len(top_leads) * 2} credits")

    return top_leads


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "import":
            import_apollo_export(
                csv_file=sys.argv[2],
                output_file="output/apollo_leads_to_score.json"
            )
        elif sys.argv[1] == "filter":
            filter_by_score(
                input_file="output/apollo_leads_scored.json",
                output_file="output/apollo_top_leads.json",
                min_score=8
            )
    else:
        print("Usage:")
        print("  python -m src.apollo_import import apollo_export.csv")
        print("  python -m src.apollo_import filter")
```

---

## Saved Searches to Create in Apollo

### Search 1: Naples Gyms
```
Location: Naples, FL (25 mile radius)
Industry: Fitness & Recreation
Employees: 1-50
Job Title: Owner, Manager, Founder
Keywords: gym, fitness center, crossfit, yoga studio
Exclude: Planet Fitness, LA Fitness
```

### Search 2: Fort Myers Restaurants
```
Location: Fort Myers, FL (20 mile radius)
Industry: Restaurants
Employees: 5-50
Technologies: Square, Toast POS
Job Title: Owner, General Manager
Revenue: $500K-$5M
```

### Search 3: Cape Coral E-commerce
```
Location: Cape Coral, FL (25 mile radius)
Industry: Retail, E-commerce
Technologies: Shopify, WooCommerce
Employees: 1-20
Signals: Recently hired, new funding
```

### Search 4: Naples Medical Practices
```
Location: Naples, FL (25 mile radius)
Industry: Medical Practice
Employees: 1-30
Job Title: Practice Manager, Owner
Keywords: dental, chiropractic, dermatology
```

### Search 5: SWFL Home Services
```
Location: Naples, Fort Myers, Cape Coral (30 mile radius)
Industry: Professional Services
Keywords: HVAC, plumbing, electrical, landscaping
Employees: 1-50
Job Title: Owner, Manager
```

---

## Success Metrics

**Track these monthly**:
- Credits used vs budget (goal: <10% utilization)
- Leads enriched per campaign (goal: 20 per campaign)
- Conversion rate (goal: 10-15%)
- Cost per customer (goal: <20 credits)
- Credits per closed deal (goal: <40 credits)

**Dashboard** (`output/apollo_metrics.json`):
```json
{
  "month": "2026-01",
  "credits_budget": 2580,
  "credits_used": 160,
  "utilization": "6.2%",
  "campaigns": 4,
  "leads_enriched": 80,
  "responses": 12,
  "response_rate": "15%",
  "customers": 3,
  "cost_per_customer": 53
}
```

---

## Next Steps

1. ✅ Create `src/apollo_import.py` script
2. ⏳ Run first search in Apollo.io (Naples Gyms)
3. ⏳ Export CSV (free)
4. ⏳ Score leads manually
5. ⏳ Reveal top 20 contacts (40 credits)
6. ⏳ Run SMS campaign
7. ⏳ Track conversion rate

**Status**: Ready to implement - awaiting user to run first Apollo search
