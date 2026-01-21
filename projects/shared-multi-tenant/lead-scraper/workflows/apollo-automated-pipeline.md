# Workflow: Apollo MCP → SMS Automated Pipeline

## Overview

Fully automated end-to-end workflow that connects Apollo MCP lead discovery to the multi-touch SMS outreach system. Implements the **80-90% credit savings strategy** by scoring leads before enrichment.

## Pipeline Flow

```
Apollo MCP Search → Export CSV (FREE)
    ↓
Import & Auto-Score (FREE)
    ↓
Filter Top 20% (scores 8-10) (FREE)
    ↓
Enrich via Apollo MCP (PAID - 2 credits per lead)
    ↓
SMS Campaign (Twilio cost)
    ↓
Multi-Touch Follow-up Sequence (3 touches over 7 days)
    ↓
Track Responses & Conversions
```

## Use Cases

- **New Market Entry**: Search for businesses in a new geographic area or industry
- **Targeted Campaigns**: Find businesses with specific pain points (no website, few reviews, etc.)
- **Scaling Outreach**: Process 100+ leads efficiently with automated scoring and filtering
- **Credit Efficiency**: Only spend Apollo credits on the highest-quality leads (top 20%)

## Prerequisites

| Requirement | Check | Expected |
|-------------|-------|----------|
| Apollo MCP Server | `mcp list \| grep apollo` | `io.github.wmarceau/apollo` |
| Twilio Account | Check `.env` has `TWILIO_*` vars | Account SID, Auth Token, Phone |
| Apollo Credits | Login to Apollo.io | >100 credits available |
| SMS Templates | `python -m src.scraper sms-templates` | Templates loaded |

## Full Automated Workflow

### Step 1: Execute Search (via MCP)

```bash
# Run Apollo search via MCP (natural language)
python -m src.apollo_pipeline run \
    --search "gyms in Naples FL, 1-50 employees, founded after 2015" \
    --campaign "Naples Gyms Voice AI Jan 2026" \
    --template no_website_intro \
    --dry-run
```

**What happens:**
- Apollo MCP executes the search
- Results exported to `output/apollo_search_TIMESTAMP.csv` (FREE)
- Auto-scoring applied based on pain points
- Summary displayed

**Cost:** $0 (Apollo search exports are unlimited)

---

### Step 2: Import & Score (Automatic)

If MCP integration isn't ready, manual fallback:

```bash
# Export from Apollo.io manually
# Then import the CSV
python -m src.apollo_pipeline import \
    output/apollo_search_20260121.csv \
    --campaign "Naples Gyms Voice AI"
```

**Auto-Scoring Criteria:**

| Score | Pain Point | Description |
|-------|-----------|-------------|
| **10** | `no_website` | No website found (critical need) |
| **9** | `poor_reviews` | Reviews mentioning poor service/calls |
| **8** | `no_online_booking` | No online transactions/booking |
| **7** | `few_reviews` | <10 reviews (needs review help) |
| **6** | `outdated_website` | Old website (detected by tech stack) |
| **1-5** | - | Lower priority |

**Output:** `output/apollo_leads_TIMESTAMP.json` with scores

**Cost:** $0

---

### Step 3: Filter Top 20% (Automatic)

```bash
# Filter for high-scoring leads only
python -m src.apollo_pipeline filter \
    output/apollo_leads_20260121_143522.json \
    --min-score 8
```

**What happens:**
- Filters leads with score ≥ 8
- Creates `output/apollo_leads_TIMESTAMP_top.json`
- Displays credit cost estimate

**Example Output:**
```
✅ Filtered to 23 leads (score >= 8)
   Original: 120 leads
   Saved to: output/apollo_leads_20260121_143522_top.json

💰 Credit cost estimate:
   23 leads × 2 credits = 46 credits
   (vs 240 credits if you enriched all leads = 80% savings!)
```

**Cost:** $0

---

### Step 4: Enrich Contacts (via Apollo MCP)

```bash
# Enrich only the top 20% of leads
python -m src.apollo_pipeline enrich \
    output/apollo_leads_20260121_143522_top.json \
    --limit 50
```

**What happens:**
- Apollo MCP reveals contact info for top leads
- Spends 2 credits per lead (phone + email)
- Creates `output/apollo_enriched_TIMESTAMP.csv`

**Cost:** 2 Apollo credits per lead (ONLY for top 20%)

**Credit Comparison:**
- **Without filtering:** 120 leads × 2 = 240 credits
- **With filtering:** 23 leads × 2 = 46 credits
- **Savings:** 194 credits (80.8%)

---

### Step 5: Merge & Prepare for SMS

```bash
# Merge enriched contacts with scored data
python -m src.apollo_pipeline merge \
    output/apollo_enriched_20260121.csv \
    output/apollo_leads_20260121_143522_top.json
```

**What happens:**
- Combines enriched phone/email with scores and pain points
- Creates `output/apollo_ready_for_outreach.json`
- Ready for SMS campaign

**Output:** Leads with:
- ✅ Phone numbers
- ✅ Email addresses
- ✅ Pain point scores
- ✅ Business context

**Cost:** $0

---

### Step 6: SMS Campaign (Dry Run First!)

```bash
# Preview SMS campaign (no sending)
python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --template no_website_intro \
    --dry-run \
    --limit 100

# Then send for real
python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --template no_website_intro \
    --for-real \
    --limit 100
```

**What happens:**
- Sends personalized SMS via Twilio
- Auto-selects template based on pain points
- Automatically enrolls in follow-up sequence
- Tracks delivery status

**Template Auto-Selection:**
- `no_website` pain point → `no_website_intro` template
- `few_reviews` pain point → `few_reviews` template
- `no_online_booking` → `no_online_transactions` template

**Cost:** ~$0.0075 per SMS (Twilio)

---

### Step 7: Multi-Touch Follow-Up (Automatic)

After SMS sends, leads are **automatically enrolled** in the 3-touch follow-up sequence:

| Touch | Day | Template | Strategy |
|-------|-----|----------|----------|
| Touch 1 | Day 0 | (Initial SMS) | Direct value offer |
| Touch 2 | Day 3 | `{pain_point}_followup_question` | Question hook |
| Touch 3 | Day 7 | `{pain_point}_followup_breakup` | Scarcity/breakup |

**Automatic Processing (Daily Cron):**

```bash
# Check what's due today
python -m src.follow_up_sequence queue --days 7

# Process due follow-ups (dry run)
python -m src.follow_up_sequence process --dry-run

# Process for real
python -m src.follow_up_sequence process --for-real
```

**Exit Conditions (Auto-Stop):**
- Lead replies (any message)
- Lead opts out (STOP)
- Delivery fails 2x
- Day 7 completed

**Cost:** ~$0.0075 per follow-up SMS × 2 touches = ~$0.015 per lead

---

## One-Command Full Pipeline (Future)

When Apollo MCP integration is complete:

```bash
# Single command for entire workflow
python -m src.apollo_pipeline run \
    --search "restaurants in Fort Myers FL, no website" \
    --campaign "Fort Myers Restaurants Website" \
    --template no_website_intro \
    --for-real \
    --limit 100
```

**This will:**
1. Search Apollo via MCP ✅
2. Auto-score leads ✅
3. Filter top 20% ✅
4. Enrich via Apollo MCP ✅
5. Send SMS campaign ✅
6. Enroll in follow-up sequence ✅
7. Track responses ✅

**Total time:** ~30 minutes for 100 leads
**Manual time saved:** ~4 hours

---

## Cost Analysis

### Example: 100 Leads Campaign

| Step | Cost | Notes |
|------|------|-------|
| Apollo Search | $0 | Unlimited free exports |
| Auto-Scoring | $0 | Automated |
| Filter Top 20% | $0 | 20 leads selected |
| Enrich 20 Leads | 40 credits | 20 × 2 credits |
| SMS Campaign (20 leads) | $0.15 | 20 × $0.0075 |
| Follow-up (2 touches × 20) | $0.30 | 40 × $0.0075 |
| **TOTAL** | **40 credits + $0.45** | vs 200 credits if no filtering |

**Savings:** 160 Apollo credits (80% reduction)

---

## Manual Fallback Steps

If Apollo MCP isn't available, use manual workflow:

### 1. Search in Apollo.io
- Go to https://app.apollo.io
- Run search: "gyms in Naples FL, 1-50 employees"
- Export to CSV (FREE)

### 2. Import CSV
```bash
python -m src.apollo_pipeline import apollo_export.csv --campaign "Naples Gyms"
```

### 3. Manually Review Websites (Optional)
- Open `output/apollo_leads_TIMESTAMP.json`
- Visit each website
- Adjust scores (1-10) based on observations
- Save file

### 4. Filter Top Leads
```bash
python -m src.apollo_pipeline filter output/apollo_leads_TIMESTAMP.json
```

### 5. Enrich in Apollo.io
- Go back to Apollo.io
- Find the 20 top-scoring businesses
- Click "Reveal" for each (spends 2 credits)
- Export enriched CSV

### 6. Merge & Send
```bash
python -m src.apollo_pipeline merge \
    apollo_enriched.csv \
    output/apollo_leads_TIMESTAMP_top.json

python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --for-real
```

---

## Response Handling

### When Lead Replies

```bash
# Mark lead as responded (auto-stops follow-up sequence)
python -m src.follow_up_sequence response "+12399999999" \
    --type responded \
    --notes "Interested in website quote"
```

**Response Types:**
- `responded` - General response
- `converted` - Booked call/meeting
- `opted_out` - Sent STOP

### When Lead Converts

```bash
# Mark as converted
python -m src.follow_up_sequence response "+12399999999" \
    --type converted \
    --notes "Scheduled discovery call for Jan 25"
```

---

## Campaign Analytics

### View Campaign Performance

```bash
# Overall stats
python -m src.campaign_analytics report

# Template performance
python -m src.campaign_analytics templates

# Conversion funnel
python -m src.campaign_analytics funnel
```

**Key Metrics:**
- Response rate (target: 5-10%)
- Conversion rate (target: 1-3%)
- Opt-out rate (target: <2%)
- Best-performing templates

---

## Troubleshooting

### Issue: Apollo MCP not found

**Solution:**
```bash
# Check MCP server status
mcp list | grep apollo

# Install Apollo MCP
pip install apollo-mcp

# Verify in Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

---

### Issue: No phone numbers after enrichment

**Solution:**
- Apollo doesn't always have phone numbers for all businesses
- Try enriching email first, then use other tools for phone lookup
- Or scrape Google Places for phone numbers:

```bash
python -m src.scraper scrape \
    --category gym \
    --area "Naples, FL" \
    --source google
```

---

### Issue: SMS delivery failing

**Solution:**
```bash
# Check Twilio balance
# Check phone number formatting (must be E.164: +1XXXXXXXXXX)

# Test with dry run first
python -m src.apollo_pipeline sms \
    output/apollo_ready_for_outreach.json \
    --dry-run
```

---

## Success Criteria

- ✅ 100+ leads searched via Apollo MCP
- ✅ Auto-scoring assigns scores (1-10)
- ✅ Top 20% filtered (scores 8-10)
- ✅ Enrichment spending <50 credits for 20 leads
- ✅ SMS delivery rate >95%
- ✅ Response rate >5%
- ✅ Follow-up sequence auto-running
- ✅ Responses tracked in CRM

---

## Integration with Other Systems

### ClickUp CRM

Hot leads auto-create ClickUp tasks:

```bash
python -m src.crm_sync sync \
    --source apollo_pipeline \
    --min-response-quality hot
```

### Google Sheets

Campaign results exported to Sheets:

```bash
python -m src.campaign_analytics export \
    --format sheets \
    --campaign "Naples Gyms Voice AI"
```

### Voice AI Follow-Up

For high-intent responses, trigger Voice AI call:

```bash
python -m src.voice_ai_tracker trigger \
    --phone "+12399999999" \
    --script "gym_demo"
```

---

## Best Practices

### 1. Always Dry Run First
- Never send SMS without previewing
- Check template personalization
- Verify phone number formatting

### 2. Start Small, Scale Up
- Test with 10-20 leads first
- Measure response rate
- Optimize templates
- Then scale to 100+

### 3. Monitor Apollo Credits
- Check balance before enrichment
- Filter aggressively (top 10-20%)
- Only enrich high-scoring leads

### 4. Track Everything
- Record responses immediately
- Update CRM when leads convert
- Analyze metrics weekly

### 5. Respect Opt-Outs
- STOP = immediate removal from all sequences
- Never re-engage opted-out leads
- Maintain clean opt-out list

---

## Related Workflows

- [Apollo Credit-Efficient Workflow](apollo-credit-efficient-workflow.md) - Manual Apollo workflow
- [SMS Campaign SOP](sms-campaign-sop.md) - SMS best practices
- [Multi-Touch Follow-Up SOP](multi-touch-followup-sop.md) - Follow-up sequence details
- [Cold Outreach Strategy SOP](cold-outreach-strategy-sop.md) - Messaging strategy

---

## Commands Quick Reference

```bash
# Full pipeline
python -m src.apollo_pipeline run --search "gyms in Naples FL" --campaign "Naples Gyms" --for-real

# Individual steps
python -m src.apollo_pipeline import <csv_file> --campaign "Name"
python -m src.apollo_pipeline filter <scored_json>
python -m src.apollo_pipeline enrich <top_json> --limit 50
python -m src.apollo_pipeline merge <enriched_csv> <scored_json>
python -m src.apollo_pipeline sms <ready_json> --for-real

# Follow-up management
python -m src.follow_up_sequence queue --days 7
python -m src.follow_up_sequence process --for-real
python -m src.follow_up_sequence response <phone> --type converted

# Analytics
python -m src.campaign_analytics report
python -m src.campaign_analytics templates
python -m src.campaign_analytics funnel
```

---

**Last Updated:** 2026-01-21
**Version:** 1.0.0
**Maintainer:** William Marceau
