# Apollo MCP Phase 2 Preparation

**Status:** Ready to Execute
**Prerequisites:** Phase 1 complete (Apollo MCP published)
**Estimated Time:** 6-8 hours

---

## Overview

Phase 2 integrates Apollo MCP with lead-scraper and validates the apollo_pipeline.py automation.

**Goals:**
1. Test apollo_pipeline.py (existing automation)
2. Integrate apollo_mcp_bridge.py (NEW - unified API)
3. Export and review 984 saved leads
4. Create 5 saved searches for common campaigns

---

## Task 2.1: Test apollo_pipeline.py (2 hrs)

### Objective
Validate the existing Apollo automation pipeline.

### Test Sequence

#### Test 1: Dry Run (0 credits) - 30 min

**Command:**
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "TEST Naples Gyms Dry Run" \
    --dry-run \
    --limit 10
```

**Expected Output:**
- Search returns ~10 results
- Auto-scoring works (website data → pain points)
- Top 20% identified
- NO enrichment performed (dry run)
- Output: JSON file with scored leads

**Success Criteria:**
- ✅ No errors during execution
- ✅ Leads have valid scores (1-10)
- ✅ Pain points identified correctly
- ✅ Output file created in `output/`

---

#### Test 2: Small Enrichment (10 credits) - 30 min

**Command:**
```bash
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "TEST Naples Gyms Small Batch" \
    --for-real \
    --limit 5
```

**Expected Output:**
- Search: 5 results
- Auto-scored
- Top 1-2 leads selected (min score 8)
- Enriched via Apollo API (2-4 credits)
- Output: JSON with phone/email

**Success Criteria:**
- ✅ Enrichment returns phone numbers
- ✅ Enrichment returns email addresses
- ✅ Credits tracked correctly
- ✅ Output format compatible with SMS system

**Verify Output:**
```bash
cat output/apollo_ready_for_outreach.json | jq '.'
```

---

#### Test 3: Full Workflow (40 credits) - 1 hr

**Command:**
```bash
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees" \
    --campaign "Naples Gyms Test Campaign" \
    --for-real \
    --limit 20 \
    --template no_website_intro
```

**Expected Output:**
- Search: 20 results
- Auto-score all
- Select top 20% (4 leads) for enrichment
- Enrich 4 leads (8 credits)
- Export to lead-scraper format
- Ready for SMS campaign

**Run SMS Campaign:**
```bash
python -m src.scraper sms \
    --source apollo \
    --for-real \
    --limit 4 \
    --template no_website_intro
```

**Expected:**
- 4 SMS sent to gym owners
- Twilio logs show delivery
- No errors

**Success Criteria:**
- ✅ End-to-end pipeline works
- ✅ SMS sent successfully
- ✅ Webhook receives replies (if any)
- ✅ Leads enrolled in follow-up sequence

---

### If apollo_pipeline.py Works

**Document:**
1. Create `workflows/apollo-pipeline-test-results.md`
2. Record test outcomes, errors, fixes
3. Update `workflows/apollo-automated-pipeline.md` with learnings

**Use Cases:**
- Batch processing (>50 leads)
- Scheduled campaigns (cron jobs)
- Python-native automation (no MCP required)

---

### If apollo_pipeline.py Fails

**Debug Steps:**
1. Check import errors (missing modules?)
2. Verify Apollo API auth (APOLLO_API_KEY valid?)
3. Test individual functions (search, score, enrich)
4. Check output format compatibility

**If Unfixable:**
- Archive apollo_pipeline.py
- Focus on Apollo MCP only (primary workflow)
- Document known issues in DOCKET.md

---

## Task 2.2: Integrate apollo_mcp_bridge.py (3 hrs)

### Status: ✅ Bridge Created

**File:** `/Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/src/apollo_mcp_bridge.py`

**What it does:**
- Calls Apollo MCP server
- Detects company templates
- Scores and filters leads
- Enriches top 20%
- Returns Lead objects compatible with SMS workflows

---

### Integration Steps

#### Step 1: Update scraper.py (30 min)

**Add import:**
```python
from .apollo_mcp_bridge import ApolloMCPBridge
```

**In LeadScraper.__init__:**
```python
self.apollo_mcp_bridge = ApolloMCPBridge(api_key=os.getenv("APOLLO_API_KEY"))
```

**In search_businesses method, add elif block:**
```python
elif api == "apollo_mcp":
    logger.info(f"Using Apollo MCP for {area_name}...")
    try:
        leads = self.apollo_mcp_bridge.search(
            query=query,
            location=area_name,
            campaign_name=campaign_name or f"{query}_{area_name}",
            company_context="marceau-solutions",
            max_results=limit or 100,
            enrich_top_n=20
        )
        all_leads.extend(leads)
    except Exception as e:
        logger.error(f"Apollo MCP error for {area_name}: {e}")
```

---

#### Step 2: Test Integration (1 hr)

**Test 1: Dry Run**
```bash
python -m src.scraper search \
    --query "gyms" \
    --location "Naples, FL" \
    --api apollo_mcp \
    --limit 20 \
    --dry-run
```

**Expected:**
- Apollo MCP bridge called
- Company template detected ("marceau-solutions")
- Leads returned with scores
- NO enrichment (dry run)

**Test 2: Small Enrichment (10 credits)**
```bash
python -m src.scraper search \
    --query "restaurants" \
    --location "Fort Myers, FL" \
    --api apollo_mcp \
    --limit 20 \
    --for-real
```

**Expected:**
- Search: 20 results
- Top 20% (4 leads) enriched
- Credits used: ~8
- Output: JSON with phone/email

---

#### Step 3: Compare to Google/Yelp (30 min)

**Run parallel searches:**
```bash
# Google Places
python -m src.scraper search --query "gyms" --location "Naples, FL" --api google --limit 10

# Yelp
python -m src.scraper search --query "gyms" --location "Naples, FL" --api yelp --limit 10

# Apollo MCP
python -m src.scraper search --query "gyms" --location "Naples, FL" --api apollo_mcp --limit 10
```

**Compare:**
- Data quality (Apollo has decision makers, not just business listings)
- Contact data (Apollo provides direct phone/email)
- Cost (Apollo: credits, Google/Yelp: free but less data)

---

### Success Criteria

- ✅ `--api apollo_mcp` option works
- ✅ Leads returned in correct format
- ✅ Compatible with existing SMS workflows
- ✅ No breaking changes to Google/Yelp
- ✅ Documentation updated

---

## Task 2.3: Export 984 Saved Leads (1 hr)

### Investigation Steps

1. **Log into Apollo.io**
   ```
   open https://app.apollo.io
   ```

2. **Navigate to "Saved" or "People" section**
   - Check date range (when were these saved?)
   - Check source (which searches created them?)
   - Check quality (decision makers or sales reps?)

3. **Review Sample**
   - Click into 10-20 random leads
   - Check titles (Owner, CEO, or Assistant, Sales Rep?)
   - Check if contacts already revealed
   - Assess overall quality

4. **Export Decision**

   **Scenario A: High Quality (80%+ decision makers)**
   - Export to CSV
   - Import to lead-scraper
   - Score top 100
   - Run campaigns

   **Scenario B: Mixed Quality (50-80% decision makers)**
   - Export subset (filter by title in Apollo)
   - Import filtered leads only
   - Manual review before campaign

   **Scenario C: Low Quality (<50% decision makers)**
   - Archive or delete
   - Document what NOT to save in future

---

### Export Workflow

**If exporting:**

```bash
# 1. Download CSV from Apollo
# Save to: input/apollo/saved_leads_20260121.csv

# 2. Import to lead-scraper
cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
python -m src.apollo_import import input/apollo/saved_leads_20260121.csv \
    --campaign "Apollo Saved Leads Review Jan 2026"

# 3. Score leads (manual - visit websites)
# Output: output/apollo_leads_scored.json

# 4. Filter top 20%
python -m src.apollo_import filter output/apollo_leads_scored.json --min-score 8

# 5. Check if already enriched
# If phone/email visible in CSV: skip enrichment (already paid for)
# If not: reveal in Apollo UI for top leads

# 6. Ready for SMS
python -m src.scraper sms --source apollo --template no_website_intro --for-real --limit 10
```

---

### Potential Value

**Best Case:**
- 984 leads × 10% qualified = ~100 high-quality leads
- Already enriched (contacts visible) = $0 credit cost
- 5-10 campaigns worth of leads
- Value: $500-$1,000 in potential business

**Worst Case:**
- Mostly low-quality (sales reps, assistants)
- Archive and move on
- Learning: document what NOT to save

---

## Task 2.4: Create 5 Saved Searches (30 min)

### Goal
Eliminate manual search configuration for top 5 campaigns.

**Time Savings:** 3-5 min per campaign

---

### Saved Searches to Create

#### 1. Naples Gyms (Marceau Solutions)

**Settings:**
- **Name:** "Naples Gyms - Marceau Solutions"
- **Location:** Naples, FL (25 mile radius)
- **Industry:** Fitness & Recreation
- **Employees:** 1-50
- **Job Title:** Owner, CEO, Founder, Manager
- **Keywords:** gym, fitness, crossfit, yoga
- **Exclude Companies:** Planet Fitness, LA Fitness, Anytime Fitness

---

#### 2. Fort Myers Restaurants (Voice AI)

**Settings:**
- **Name:** "Fort Myers Restaurants - Voice AI"
- **Location:** Fort Myers, FL (20 mile radius)
- **Industry:** Restaurants
- **Employees:** 5-50
- **Technologies:** Square, Toast POS (if available)
- **Job Title:** Owner, General Manager
- **Revenue:** $500K-$5M (if available)

---

#### 3. Naples HVAC (Southwest Florida Comfort)

**Settings:**
- **Name:** "Naples HVAC - SWFL Comfort"
- **Location:** Naples, FL (30 mile radius)
- **Industry:** HVAC
- **Employees:** 1-50
- **Job Title:** Owner, CEO, President, GM
- **Keywords:** HVAC, air conditioning, AC repair

---

#### 4. Cape Coral E-commerce (Footer Shipping)

**Settings:**
- **Name:** "Cape Coral E-commerce - Footer"
- **Location:** Cape Coral, FL (25 mile radius)
- **Industry:** E-commerce, Online Retail
- **Technologies:** Shopify, WooCommerce (if available)
- **Employees:** 1-20
- **Job Title:** Owner, Founder, Operations Manager

---

#### 5. Naples Medical (Booking AI)

**Settings:**
- **Name:** "Naples Medical - Booking AI"
- **Location:** Naples, FL (25 mile radius)
- **Industry:** Medical Practice
- **Employees:** 1-30
- **Job Title:** Practice Manager, Owner
- **Keywords:** dental, chiropractic, dermatology

---

### Workflow

1. **Log into Apollo.io**
2. **Go to Search**
3. **Configure filters** (see settings above)
4. **Click "Save Search"**
5. **Name it** (use naming convention above)
6. **Repeat for all 5 searches**

**Future Use:**
```
1. Open Apollo.io
2. Click "Saved Searches"
3. Select search
4. Click "Export" → CSV
5. Import to lead-scraper
6. Run campaign
```

**Time:** 60-90 seconds instead of 5-7 minutes

---

## Phase 2 Deliverables

By the end of Phase 2, we will have:

✅ **apollo_pipeline.py tested** - Alternative automation validated or archived
✅ **apollo_mcp_bridge.py integrated** - Unified search API for Google, Yelp, Apollo
✅ **984 saved leads reviewed** - Potential 100+ qualified leads identified
✅ **5 saved searches created** - 3-5 min savings per campaign
✅ **Workflows documented** - Future campaigns follow standardized process

---

## Success Metrics

### Time Savings
- Campaign setup: 15-20 min → 60-90 sec (10x improvement)
- Manual CSV exports: Eliminated
- Search configuration: 5 min → 1 min (saved searches)

### Credit Efficiency
- Before: Enrich all leads (100% cost)
- After: Enrich top 20% only (80% savings)

### Lead Quality
- Before: Mix of decision makers and sales reps
- After: Filtered to decision makers only (2-3x better conversion)

---

## Next: Phase 3

Once Phase 2 complete:
- Apollo metrics dashboard (track ROI)
- Zapier integration (auto-CRM updates)
- Advanced filter templates (technographic, funding, revenue)

**Estimated Start:** 2026-01-22 or 2026-01-23
