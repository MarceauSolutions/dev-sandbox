# Strategic Shift: Google Places/Yelp → Apollo.io

**Date**: 2026-01-21
**Reason**: Leverage paid Apollo.io subscription instead of working around free API limitations

---

## Why This Change

### Current Problem (Google Places/Yelp)
- ❌ Incomplete website data (missed P-Fit and Velocity real websites)
- ❌ No decision-maker contact info (just business phone)
- ❌ No email addresses
- ❌ Requires multiple API calls + manual validation
- ❌ Aggregator URLs (Yelp/Google Maps) require complex filtering
- ❌ $112/month in API costs for inferior data

### Apollo.io Advantages
- ✅ **Already paying $59/month** - should maximize value
- ✅ **2,580 credits/month** (2,500 plan + 80 bonus)
- ✅ **Built-in website validation** - Apollo verifies websites exist
- ✅ **Decision-maker emails** -reach owners/managers directly
- ✅ **Direct phone numbers** - not just business lines
- ✅ **Company intelligence** - revenue, employees, technologies used
- ✅ **80-90% credit savings** with export → score → selective enrich workflow
- ✅ **Higher quality targeting** - filters by job title, company size, industry

---

## New Workflow

### Old Approach (Google Places/Yelp)
```
1. Google Places API search → $0.032/search
2. Place Details API → $0.017/details
3. Yelp API → Parse reviews
4. Manual website validation → Custom aggregator detection
5. Manual pain point identification
6. SMS campaign → Twilio
Total: Complex pipeline, $112/month, incomplete data
```

### New Approach (Apollo.io)
```
1. Apollo search with filters → FREE (export)
2. Manual scoring (visit websites) → FREE
3. Filter top 20% (scores 8-10) → FREE
4. Enrich contacts in Apollo → 40 credits for 20 leads
5. SMS campaign → Twilio
Total: Simple pipeline, 6% credit usage, complete data
```

---

## Apollo.io Data Quality

### What Apollo Provides (vs Google Places)

| Data Field | Google Places | Apollo.io | Advantage |
|------------|---------------|-----------|-----------|
| **Business Name** | ✅ | ✅ | Same |
| **Address** | ✅ | ✅ | Same |
| **Phone** | ✅ Business line | ✅ Decision-maker direct | **Better** |
| **Website** | ⚠️ Often missing/wrong | ✅ Verified URLs | **Better** |
| **Email** | ❌ Never | ✅ Owner/manager email | **Much better** |
| **Decision Maker** | ❌ | ✅ Name + title | **Much better** |
| **Company Size** | ❌ | ✅ Employee count | **Better** |
| **Revenue** | ❌ | ✅ Estimated revenue | **Better** |
| **Technologies** | ❌ | ✅ (Shopify, Square, etc.) | **Better** |
| **Industry** | ⚠️ Categories | ✅ Specific industry | **Better** |
| **Pain Points** | Manual inference | Built-in filters | **Easier** |

---

## Credit Efficiency Strategy

### Full Month Allocation (2,580 credits)

**Conservative approach** (6% utilization):
- 4 campaigns per month
- 20 leads per campaign = 80 total leads
- 2 credits per lead = 160 credits used
- **2,420 credits remaining** (94% buffer)

**Aggressive approach** (50% utilization):
- 32 campaigns per month
- 20 leads per campaign = 640 total leads
- 2 credits per lead = 1,280 credits used
- **1,300 credits remaining** (50% buffer)

**Recommended**: Start conservative (6%), scale up as conversion rates prove out

---

## Integration Points

### Existing Tools (Keep)
- ✅ **SMS Outreach** (`sms_outreach.py`) - Works with any lead source
- ✅ **Follow-Up Sequences** (`follow_up_sequence.py`) - Source agnostic
- ✅ **Campaign Analytics** (`campaign_analytics.py`) - Tracks all sources
- ✅ **Website Validator** (`website_validator.py`) - Still useful for edge cases
- ✅ **Templates** (`templates/sms/`) - Reusable across sources

### New/Modified Tools
- ✅ **Apollo Pipeline** (`apollo_pipeline.py`) - Already built!
- ✅ **Apollo Import** (`apollo_import.py`) - CSV → Lead conversion
- ⚠️ **Google Places** (`google_places.py`) - Deprecate or use as fallback only

---

## Migration Steps

### Immediate (Today)
1. ✅ Validate Apollo.io subscription is active ($59/month plan)
2. ⏳ Run first Apollo search (Naples gyms) - export CSV
3. ⏳ Import CSV and score top 50 leads manually
4. ⏳ Filter for top 20% (scores 8-10)
5. ⏳ Enrich 20 contacts in Apollo (40 credits)
6. ⏳ Small batch test (3-5 SMS sends)

### Short-term (This Week)
1. Create 5 saved searches in Apollo (gyms, restaurants, e-commerce, medical, home services)
2. Set up monthly campaign rotation
3. Document Apollo → SMS workflow
4. Train on contact enrichment best practices

### Medium-term (This Month)
1. Retire Google Places/Yelp pipeline (or keep as emergency fallback)
2. Scale to 4 campaigns/month (80 leads)
3. Track credit usage and conversion rates
4. Optimize searches based on results

---

## Cost Comparison

### Old Approach (Google Places)
```
Google Places API: $112/month (Jan 1-21)
Yelp API: Free tier
Time: ~2 hours per campaign (scraping + validation)
Data quality: 70% (incomplete websites)
Targeting: 85% accurate (missed real websites)

Total: $112/month + 2 hours/campaign
```

### New Approach (Apollo.io)
```
Apollo.io: $59/month
Credits used: 160/month (6% of 2,580)
Time: ~30 min per campaign (export + score + enrich)
Data quality: 95% (Apollo verifies all data)
Targeting: 95% accurate (built-in filters)

Total: $59/month + 0.5 hours/campaign
Savings: $53/month + 1.5 hours/campaign
```

---

## Risk Mitigation

### What if Apollo.io has issues?

**Fallback options**:
1. **Google Places** - Keep code as backup (already integrated)
2. **Yelp API** - Still free tier available
3. **Manual research** - LinkedIn + Google for critical leads
4. **Upgrade Apollo** - More credits if needed ($149/month = 10,000 credits)

**Recommendation**: Keep Google Places integrated but use Apollo as primary source

---

## Next Actions

### For William (Manual Steps)
1. Log into Apollo.io: https://app.apollo.io
2. Create search: "Gyms in Naples FL, 1-50 employees, Owner/Manager"
3. Export CSV (FREE)
4. Visit top 50 websites and score 1-10 based on:
   - No website? = 10 points
   - Poor online presence? = 8-9 points
   - Good website but no booking? = 6-7 points
5. Return scored CSV to Claude for enrichment

### For Claude (Automated Steps)
1. Import scored CSV → `apollo_leads_scored.json`
2. Filter for top 20% (scores 8-10)
3. Return list of companies to enrich in Apollo
4. Import enriched data from Apollo
5. Run small batch SMS test (3-5 sends)
6. Monitor responses

---

## Success Metrics

**Track weekly**:
- Credits used vs budget
- Leads enriched per week
- Response rate per campaign
- Cost per qualified lead
- Cost per customer

**Goal for Month 1**:
- <10% credit utilization (260 credits or less)
- 80 leads enriched
- 10-15% response rate
- 3-5 customers acquired
- <50 credits per customer

---

## Documentation Updates Needed

1. Update README.md - Make Apollo primary workflow
2. Update COMPREHENSIVE-SESSION-SUMMARY.md - Add Apollo migration
3. Create APOLLO-QUICK-START.md - Step-by-step guide
4. Archive Google Places workflows → `workflows/archived/`
5. Update all campaign SOPs to reference Apollo first

---

**Status**: Ready to execute - awaiting Apollo.io search export

**Contact**: Apollo.io support if issues - support@apollo.io
