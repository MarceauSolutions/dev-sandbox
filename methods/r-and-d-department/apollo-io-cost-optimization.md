# Apollo.io Cost Optimization & Best Practices
**Purpose:** Document cost-effective Apollo.io usage strategies
**Source:** Team session + industry best practices
**Last Updated:** January 21, 2026

---

## Apollo.io Credit System Overview

### What Costs Credits:

| Action | Credits | Our Strategy |
|--------|---------|--------------|
| **Email generation** | 1-5 credits | ❌ DON'T USE - Write our own templates |
| **Phone number reveal** | 1 credit | ✅ USE - Can't get these elsewhere |
| **Email reveal** | 1 credit | ✅ USE - For missing emails only |
| **Bulk enrichment** | 1 credit/record | ✅ USE - Only for qualified leads |
| **Search queries** | FREE | ✅ USE EXTENSIVELY |
| **Saved searches** | FREE | ✅ USE - Set up alerts |
| **Export to CSV** | FREE (limited) | ✅ USE - Then enrich selectively |

### Credit Conservation Strategy:

**❌ AVOID (Waste Credits):**
- AI-generated email templates (we write better ones anyway)
- Bulk "reveal all" on unqualified leads
- Enriching leads before basic qualification
- Exporting full contact info for entire search results

**✅ DO (Save Credits):**
- Use search filters to pre-qualify BEFORE revealing contacts
- Write our own SMS/email templates (better + free)
- Reveal phone/email only for leads that meet criteria
- Use saved searches with alerts (free monitoring)
- Export company data first (free), enrich individuals later

---

## Search Query Best Practices

### Priority 1: Geographic + Industry Filters (Most Important)

These narrow results to high-intent prospects:

```
Location:
- City: Naples, FL
- City: Fort Myers, FL
- City: Cape Coral, FL
- Radius: 25 miles

Industry:
- Fitness & Recreation (for gyms)
- Restaurants (for HVAC)
- Health, Wellness & Fitness
- Food & Beverages
```

**Why priority 1:**
- Eliminates 90% of irrelevant leads
- Local businesses more likely to convert
- Industry-specific pain points

### Priority 2: Company Size (High Value)

Filter by employee count to match our ICP:

```
Employees:
- 1-10 (small businesses, decision-maker accessible)
- 11-50 (growing, have budget)
- Avoid 500+ (too enterprise, slow sales cycle)
```

**Why priority 2:**
- Small businesses = faster decisions
- 1-50 employees = owner/manager accessible
- Budget sweet spot ($1K-$10K/month services)

### Priority 3: Technologies Used (Intent Signal)

Shows they're tech-forward:

```
Technologies:
- Google Analytics (they care about data)
- WordPress (have website, may need maintenance)
- Shopify (e-commerce, need automation)
- Square (payment processing, could use CRM)
```

**Why priority 3:**
- Tech stack = intent to invest in tools
- Existing tools = easier to sell integrations
- Shows sophistication level

### Priority 4: Recent Activity (Timing)

Catch them at the right moment:

```
Signals:
- Recently hired (growing = need automation)
- New funding (have budget)
- Posted job listings (expansion mode)
- Website updated recently (active business)
```

**Why priority 4:**
- Growth moments = open to solutions
- Recent activity = engaged business
- Timing increases conversion 2-3x

### Priority 5: Contact Level (Decision Maker)

Target the right person:

```
Job Titles:
- Owner
- Founder
- CEO
- General Manager
- Operations Manager

Avoid:
- Assistant
- Intern
- Junior
- Coordinator (unless small company)
```

**Why priority 5:**
- Decision-makers close faster
- No gatekeepers
- Direct ROI conversation

---

## Sample Search Queries (Cost-Effective)

### Query 1: Naples Gyms (HVAC Services)

```
Location: Naples, FL (25 mile radius)
Industry: Fitness & Recreation
Employees: 1-50
Job Title: Owner, Manager, Founder
Keywords: gym, fitness center, crossfit, yoga studio
Exclude: Planet Fitness, LA Fitness (chains)

Result: ~50-100 prospects
Credits used: 0 (search is free)
Next step: Export list, manually qualify, reveal contacts for top 20
```

### Query 2: Fort Myers Restaurants (AI Automation)

```
Location: Fort Myers, FL (20 mile radius)
Industry: Restaurants
Employees: 5-50
Technologies: Square, Toast POS
Job Title: Owner, General Manager
Revenue: $500K-$5M

Result: ~30-80 prospects
Credits used: 0 (search is free)
Next step: Check reviews for "slow service" complaints, reveal contacts for qualified
```

### Query 3: Cape Coral E-commerce (Lead Gen)

```
Location: Cape Coral, FL (25 mile radius)
Industry: Retail, E-commerce
Technologies: Shopify, WooCommerce
Employees: 1-20
Signals: Recently hired, new funding

Result: ~20-40 prospects
Credits used: 0 (search is free)
Next step: Visit websites, qualify by online presence quality
```

---

## Credit-Saving Workflow

### Phase 1: Broad Search (FREE)
```
1. Build search query with filters above
2. Export company list (no contact reveal)
3. Get: Company name, website, industry, size
4. Credits used: 0
```

### Phase 2: Manual Qualification (FREE)
```
1. Visit websites from export
2. Check for pain points:
   - No online booking? (HVAC opportunity)
   - Poor reviews mentioning calls? (Voice AI opportunity)
   - No social media? (Content automation)
3. Score leads 1-10
4. Credits used: 0
```

### Phase 3: Selective Enrichment (PAID)
```
1. Top 20% of scored leads only
2. Reveal phone number (1 credit)
3. Reveal email if needed (1 credit)
4. Total credits: 20-40 for highly qualified leads
```

### Phase 4: Custom Outreach (FREE)
```
1. Use OUR templates (not Apollo's AI)
2. Personalize with website research
3. Send via Twilio SMS (our system)
4. Credits used: 0
```

**Total credits per campaign:** 20-40 (vs 100-200 if revealing all)
**Savings:** 60-80% credit reduction

---

## Apollo.io Search Query Template

Copy-paste template for consistent searches:

```markdown
## Search: [Business Type] in [Location]

**Location:**
- City:
- Radius:
- State: FL

**Industry:**
- Primary:
- Secondary:

**Company Size:**
- Employees: 1-50
- Revenue: $500K-$5M (if applicable)

**Job Titles:**
- Owner
- Founder
- CEO
- General Manager

**Technologies:** (if applicable)
-
-

**Keywords:** (include)
-

**Exclude Keywords:**
- franchise
- chain
- corporate

**Signals:** (if applicable)
- Recently hired
- New funding
- Job postings

**Expected Results:** [number] prospects
**Qualification Criteria:**
1.
2.
3.

**Next Steps:**
1. Export list (free)
2. Visit top 50 websites
3. Score 1-10
4. Reveal contacts for 8-10 scores only
```

---

## Integration with Our System

### Workflow: Apollo → Our Lead Scraper

```python
# 1. Run Apollo search (free)
# 2. Export to CSV (free)
# 3. Import to our system
import csv
from src.models import Lead
from src.apollo import ApolloClient

apollo = ApolloClient()

# Load exported CSV from Apollo
with open('apollo_export.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Basic info from free export
        lead = Lead(
            business_name=row['Company'],
            website=row['Website'],
            industry=row['Industry'],
            city=row['City']
        )

        # ONLY reveal contact if lead scores high
        if qualifies_for_outreach(lead):  # Custom function
            # Spend 1-2 credits here
            enriched = apollo.enrich_person(
                company=lead.business_name,
                title='Owner'
            )
            lead.phone = enriched.get('phone')
            lead.email = enriched.get('email')

            # Now enroll in sequence
            enroll_in_followup(lead)
```

**Credits saved:** 80% (only enrich qualified leads)

---

## Questions from Apollo.io Team Session

### Q: Which filters matter most?
**A:** Location → Industry → Company Size (in that order)
- These 3 eliminate 90% of bad fits
- Everything else refines the remaining 10%

### Q: How to avoid wasting credits?
**A:** Export → Qualify → Enrich selectively
- Never "reveal all" contacts
- Use free data to pre-qualify
- Spend credits only on scored leads

### Q: Best practices for saved searches?
**A:** Set up 5-10 targeted searches with alerts
- One per city/industry combo
- Alert weekly for new matches
- Review alerts, qualify, then enrich

### Q: How to use technologies filter?
**A:** Look for intent signals
- Has tech = willing to adopt tools
- WordPress/Shopify = has website (need maintenance)
- CRM = understands automation value

### Q: Employee count sweet spot?
**A:** 1-50 for our services
- 1-10: Owner accessible, fast decisions
- 11-50: Have budget, growth mode
- 50+: Too slow, need enterprise sales

---

## Cost Comparison

### Bad Approach (Wastes Credits):
```
1. Run broad search (500 results)
2. Click "reveal all contacts" (500 × 2 = 1000 credits)
3. Export full list
4. Send generic outreach to all

Total credits: 1000
Conversion rate: 1-2% (5-10 customers)
Cost per customer: 100-200 credits
```

### Good Approach (Saves Credits):
```
1. Run targeted search (100 results)
2. Export company data only (0 credits)
3. Visit websites, score leads
4. Reveal top 20 contacts (20 × 2 = 40 credits)
5. Send personalized outreach

Total credits: 40
Conversion rate: 10-15% (2-3 customers)
Cost per customer: 13-20 credits
```

**Savings:** 90% fewer credits, 5x better conversion

---

## Apollo.io vs Our System - Division of Labor

| Task | Apollo.io | Our System | Why |
|------|-----------|------------|-----|
| **Search/Filter** | ✅ Use Apollo | - | Better database, filters |
| **Company Data** | ✅ Export free | - | Huge database |
| **Phone/Email Reveal** | ✅ Use (selectively) | - | Can't get elsewhere |
| **Email Templates** | ❌ Don't use | ✅ We write | Better + free |
| **SMS Templates** | ❌ Not available | ✅ We write | Apollo doesn't do SMS |
| **Sending Messages** | ❌ Don't use | ✅ Twilio | We control deliverability |
| **Follow-up Sequences** | ❌ Don't use | ✅ Our system | More flexible |
| **Lead Scoring** | ❌ Don't use | ✅ Our logic | Custom criteria |
| **CRM** | ❌ Don't use | ✅ ClickUp | Already integrated |

**Apollo's role:** Lead discovery + contact enrichment ONLY
**Our system:** Everything else (templates, sending, follow-up, CRM)

---

## Action Items

- [ ] Set up 5 saved searches in Apollo (Naples gyms, Fort Myers restaurants, etc.)
- [ ] Enable weekly alerts for new matches
- [ ] Create qualification scorecard (1-10 criteria)
- [ ] Build import script for Apollo CSV exports
- [ ] Test workflow: Export → Score → Enrich top 20% only
- [ ] Measure credit usage per month
- [ ] Document additional learnings from team session

---

## Additional Research Needed

**Questions for community/Reddit:**
1. What's the best way to track credit usage over time?
2. Are there undocumented filters that work well?
3. How do others handle bulk enrichment cost-effectively?
4. Best practices for B2B vs B2C searches?
5. Any tips for local service business searches?

**Where to research:**
- r/sales
- Apollo.io Facebook group
- GrowthHackers community
- Indie Hackers
- Sales-focused Slack/Discord communities

---

**Next Steps:**
1. Document any additional insights from your Apollo team session
2. Research community best practices (Reddit, Facebook groups)
3. Test the credit-saving workflow on 1 campaign
4. Measure conversion rate difference

**Status:** Draft - awaiting additional insights from team session