# End-to-End Outreach Workflow

Complete guide to using the Apollo MCP's automated outreach pipeline.

## Overview

The `run_full_outreach_pipeline` tool automates the entire lead generation workflow from a single natural language prompt.

**Before (manual process):**
1. Search Apollo in web UI
2. Export to CSV
3. Import to lead scraper
4. Score leads manually
5. Select top leads
6. Enrich via API
7. Export to SMS tool

**After (automated):**
1. Say: "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
2. Done.

## Quick Start Examples

### Example 1: Southwest Florida Comfort (HVAC)

```
Prompt: "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"

What happens:
✓ Detects company: Southwest Florida Comfort
✓ Uses template: HVAC businesses in Naples, FL, 1-50 employees
✓ Searches for: Owner, CEO, President, Founder, General Manager
✓ Excludes: sales, coordinator, assistant
✓ Finds ~50-100 results
✓ Filters out sales reps (30-40% reduction)
✓ Scores remaining leads
✓ Selects top 20 leads
✓ Enriches (costs 20 credits)
✓ Returns enriched leads with emails/phones

Next step: Export to SMS campaign tool with template "swfl_comfort_hvac_intro"
```

### Example 2: Marceau Solutions (AI Automation)

```
Prompt: "Find gyms in Miami for Marceau Solutions"

What happens:
✓ Detects company: Marceau Solutions
✓ Overrides location: Miami (not default Southwest Florida)
✓ Overrides industry: Fitness (from "gyms")
✓ Searches for: Owner, CEO, Founder, Manager
✓ Excludes: sales, marketing coordinator, assistant, intern
✓ Scores and selects top 20
✓ Enriches leads

Next step: Use SMS template "marceau_no_website_intro"
```

### Example 3: Footer Shipping (E-commerce)

```
Prompt: "Get e-commerce leads for Footer Shipping"

What happens:
✓ Detects company: Footer Shipping
✓ No location filter (nationwide)
✓ Industry: E-commerce, Online Retail
✓ Searches for: Owner, Founder, CEO, Operations Manager
✓ Excludes: sales, warehouse, driver, picker
✓ Selects top leads
✓ Enriches

Next step: Use SMS template "footer_shipping_intro"
```

## Advanced Usage

### Skip Enrichment to Save Credits

```
Prompt: "Find Naples restaurants for Marceau Solutions"
Parameters:
  - skip_enrichment: true

Result:
- Returns scored, filtered leads WITHOUT enrichment
- Costs 0 credits
- Use for initial research/validation
```

### Control Enrichment Count

```
Prompt: "Get HVAC leads in Fort Myers for Southwest Florida Comfort"
Parameters:
  - enrich_top_n: 50

Result:
- Enriches top 50 leads instead of default 20
- Costs 50 credits
```

### Custom Max Results

```
Prompt: "Find all gyms in Naples for Marceau Solutions"
Parameters:
  - max_results: 200

Result:
- Searches up to 200 results before filtering
- More comprehensive but slower
```

## Understanding the Pipeline Log

The tool returns a detailed `pipeline_log` showing each step:

```json
{
  "pipeline_log": [
    "✓ Detected company: Southwest Florida Comfort",
    "✓ Using location: Naples, FL",
    "✓ Excluding titles: sales, outside sales, representative...",

    "--- Search Iteration 1 ---",
    "✓ Found 87 results",
    "✓ After filtering: 52 leads",
    "✓ High quality: 31 leads",
    "  Exclusion rate: 40%",
    "  Quality rate: 60%",
    "✓ Results look good",

    "--- Lead Selection ---",
    "✓ Selected top 20 leads for enrichment",

    "--- Enrichment (costs 20 credits) ---",
    "  1/20: John Smith - john@hvaccompany.com",
    "  2/20: Jane Doe - jane@coolairfl.com",
    "  ...",
    "✓ Enriched 18 leads",

    "--- Pipeline Complete ---",
    "✓ Total leads ready: 18"
  ]
}
```

## Iterative Search Refinement

The pipeline automatically refines searches if quality is poor:

### Iteration 1: Initial Search
```
Search params:
- Titles: Owner, CEO, President, Founder, General Manager
- Location: Naples, FL
- Employee range: 1-50

Results:
- Found: 100 leads
- After filtering: 45 leads (55% excluded)
- Quality rate: 40%

Decision: Quality too low, refine
```

### Iteration 2: Refined Search
```
Search params:
- Titles: Owner, CEO, Founder, President (removed General Manager)

Results:
- Found: 60 leads
- After filtering: 42 leads (30% excluded)
- Quality rate: 70%

Decision: Quality good, proceed
```

### When Refinement Stops
- Quality rate ≥ 30%
- Exclusion rate < 50%
- Max 3 iterations reached

## Quality Scoring System

Leads are scored 0.0 - 1.0 based on:

### Title Score (40 points)
- Owner/CEO/Founder/President: 0.4
- Director/VP/Vice President/Manager: 0.3
- Head of/Chief: 0.35
- Other: 0.1

### Contact Info (30 points)
- Email + Phone: 0.3
- Email OR Phone: 0.15
- Neither: 0.0

### Company Info (20 points)
- Website: 0.1
- Industry: 0.1

### LinkedIn (10 points)
- LinkedIn URL: 0.1

**Example Scores:**
- Owner with email + phone + LinkedIn + website: 1.0 (perfect)
- Manager with email only: 0.55 (medium)
- Employee with no contact info: 0.1 (low)

## Company Templates Reference

### Southwest Florida Comfort
```json
{
  "target": "HVAC businesses in Southwest Florida",
  "location": "Naples, FL",
  "employee_range": "1-50",
  "titles": ["Owner", "CEO", "President", "Founder", "General Manager"],
  "excluded_titles": ["sales", "coordinator", "assistant"],
  "sms_template": "swfl_comfort_hvac_intro"
}
```

### Marceau Solutions
```json
{
  "target": "Small businesses needing automation",
  "industries": ["Restaurants", "Fitness", "Medical", "Professional Services"],
  "location": "Southwest Florida",
  "employee_range": "1-50",
  "titles": ["Owner", "CEO", "Founder", "Manager"],
  "excluded_titles": ["sales", "marketing coordinator", "assistant", "intern"],
  "sms_template": "marceau_no_website_intro"
}
```

### Footer Shipping
```json
{
  "target": "E-commerce businesses",
  "industries": ["E-commerce", "Online Retail", "Consumer Goods"],
  "location": null,
  "employee_range": "1-30",
  "titles": ["Owner", "Founder", "CEO", "Operations Manager"],
  "excluded_titles": ["sales", "warehouse", "driver", "picker"],
  "sms_template": "footer_shipping_intro"
}
```

## Customizing Templates

To add a new company template:

1. Create `/templates/new_company.json`:
```json
{
  "company_name": "New Company",
  "company_key": "new_company",
  "description": "Target market description",
  "search_template": {
    "industry": ["Industry1", "Industry2"],
    "location": "City, State",
    "employee_range": "1,50",
    "titles": ["Owner", "CEO"],
    "excluded_titles": ["sales", "assistant"],
    "keywords": "industry keywords"
  },
  "sms_templates": {
    "intro": "new_company_intro"
  }
}
```

2. Update `src/apollo_mcp/company_templates.py`:
```python
COMPANY_TEMPLATES["new_company"] = {
    "name": "New Company",
    # ... template data
}
```

3. Update detection logic in `detect_company_from_prompt()`.

## Troubleshooting

### "Could not detect company context"
**Problem:** Prompt doesn't mention company name or recognizable keywords

**Solution:**
- Include company name explicitly: "for Southwest Florida Comfort"
- OR use industry keywords: "HVAC" → Southwest Florida Comfort, "gym" → Marceau Solutions, "e-commerce" → Footer Shipping

### "No leads found after search refinement"
**Problem:** Search criteria too narrow or location has no matching businesses

**Solution:**
- Broaden location (e.g., "Southwest Florida" instead of "Naples")
- Use broader industry keywords
- Check if industry exists in that location

### High exclusion rate (>70%)
**Problem:** Too many sales reps/assistants in results

**Solution:**
- This is normal - the pipeline automatically refines
- After 3 iterations, it uses the best results available
- Consider adding more excluded titles to template

### Low quality rate (<30%)
**Problem:** Results don't have good contact information or decision-maker titles

**Solution:**
- Try different location (some areas have better data)
- Use more specific titles in template
- Consider enriching more leads (increase `enrich_top_n`)

## Integration with SMS Campaigns

After the pipeline completes:

1. **Export leads** from pipeline output:
```python
enriched_leads = pipeline_result["leads"]
```

2. **Format for SMS tool**:
```python
for lead in enriched_leads:
    sms_data = {
        "phone": lead["phone_numbers"][0]["raw_number"],
        "business_name": lead["organization"]["name"],
        "contact_name": f"{lead['first_name']} {lead['last_name']}",
        "email": lead["email"]
    }
```

3. **Use company-specific SMS template**:
- Southwest Florida Comfort: `swfl_comfort_hvac_intro`
- Marceau Solutions: `marceau_no_website_intro`
- Footer Shipping: `footer_shipping_intro`

4. **Run SMS campaign** (per SOP 18):
```bash
python -m src.scraper sms --for-real --template swfl_comfort_hvac_intro
```

## Credit Usage Tracking

The pipeline returns:
```json
{
  "credits_used": 20,
  "leads_enriched": 18,
  "leads_selected": 20
}
```

**Cost breakdown:**
- Search operations: FREE
- Each enrichment: 1 credit
- `enrich_top_n: 20` with 90% success rate = ~18 credits

**Optimization tips:**
- Use `skip_enrichment: true` for initial research (0 credits)
- Enrich only top leads (default 20 is optimal)
- Higher quality searches = higher enrichment success rate = fewer wasted credits

## Best Practices

1. **Start with skip_enrichment**
   - Run pipeline without enrichment first
   - Review quality scores
   - Then run again with enrichment if quality is good

2. **Use location overrides**
   - Default templates have standard locations
   - Override in prompt: "Find gyms in Tampa for Marceau Solutions"

3. **Monitor exclusion rates**
   - 30-50% exclusion is normal and healthy
   - >70% may indicate poor search criteria
   - <20% may mean not filtering enough

4. **Quality over quantity**
   - Default 20 enrichments is optimal
   - Better to enrich 20 high-quality leads than 100 low-quality

5. **Check pipeline_log**
   - Review iteration history
   - Understand why refinements happened
   - Learn what search criteria work best

## Performance Benchmarks

Typical pipeline execution:
- **Search iteration 1:** 2-3 seconds
- **Search iteration 2 (if needed):** 2-3 seconds
- **Lead scoring:** <1 second
- **Enrichment (20 leads):** 40-60 seconds (rate limited)
- **Total:** ~60-90 seconds for full pipeline

## See Also

- SOP 18: SMS Campaign Execution
- SOP 19: Multi-Touch Follow-Up Sequence
- `/templates/` - Company template JSON files
- `test_enhancements.py` - Test suite demonstrating features
