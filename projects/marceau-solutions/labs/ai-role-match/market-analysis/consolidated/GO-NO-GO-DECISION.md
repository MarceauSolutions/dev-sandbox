# Go/No-Go Decision: AI Role-Match Hiring System

## Overall Score: 3.05/5

## Decision: CONDITIONAL GO — PIVOT TO SERVICE MODEL

---

## Rationale

The AI Role-Match Hiring System scores 3.05/5, which falls in the "Conditional Go" range (3.0-3.9). The market is real ($750M SAM, 7% CAGR), the pain is genuine (7/10, $4,700/hire, 18+ hours screening), and the "job-to-job matching" concept is intellectually compelling. On paper, the unit economics work.

However, three factors prevent a clean GO for a SaaS product:

**1. No technical moat.** The core innovation — projecting candidates and jobs into the same vector space — is published academic research (ConFit v2, ACL 2025). Every well-funded competitor (Eightfold, HireVue, SeekOut) already uses vector embeddings for matching. The proposed approach is a UX/marketing differentiator, not a defensible technical advantage.

**2. Overwhelming competitive firepower.** $2.3B was invested in HR recruitment AI in 2025 alone. Competitors have 50-200+ person engineering teams and dedicated enterprise sales organizations. A bootstrapped solopreneur cannot win an arms race against these players on the SaaS battlefield.

**3. Execution constraints.** William starts a full-time job (7am-3pm) on April 6, 2026. HR SaaS requires enterprise sales motions — demos, POCs, security reviews, compliance documentation. This is fundamentally incompatible with building evenings and weekends without a co-founder or sales hire.

The idea is not bad — it's the wrong vehicle for the current situation. The underlying insight (AI-powered candidate matching using modern embedding techniques) has value, but it should be deployed differently.

---

## Recommended Pivot: AI Hiring Optimization as a Service

Instead of building a SaaS product, pivot to offering AI-powered candidate screening as a **consulting service** through Marceau Solutions' Digital Tower. This aligns with existing infrastructure and constraints.

### How It Works
1. **Client brings a job opening + stack of resumes/applications**
2. **William (or automated pipeline) runs the AI matching analysis** using the same technical approach — generate ideal JDs, compare via cosine similarity, rank candidates
3. **Deliver a branded PDF report** with ranked candidates, match scores, and insights (using existing `branded_pdf_engine.py`)
4. **Charge per-engagement**: $500-$1,500 per hiring round analysis
5. **No SaaS infrastructure needed** — Python scripts, LLM API calls, branded output

### Why This Works Better
- **No product to maintain** — it's a service, not a codebase
- **No enterprise sales cycle** — sell to the AI services clients William is already targeting in the sprint
- **Higher margin** — $500-$1,500 per engagement vs. $299/month subscription
- **Proof of concept** — validates the technical approach before investing in a product
- **Fits the schedule** — can run analyses on weekends; doesn't require daily customer support
- **Builds case studies** — successful service engagements become SaaS product testimonials if you ever build the product later

### Pricing
| Service | Price | Deliverable |
|---------|-------|------------|
| **Single Role Analysis** | $500 | AI match report for 1 open position (up to 50 candidates) |
| **Hiring Sprint** | $1,500 | Analysis for 3-5 open positions, priority ranking, hiring insights |
| **Retainer** | $2,000/mo | Ongoing AI screening for all open roles (up to 10/month) |

---

## If Building the SaaS Later (After Validation)

If the service model proves demand (5+ paying clients, repeat purchases), then consider:

### Recommended MVP Scope
- **Integration-first**: Build as a Greenhouse/Lever plugin, NOT a standalone ATS
- **Core feature only**: Upload candidates + job description, get ranked matches with scores
- **Compliance-first**: Bias audit built in, full explainability, FCRA-compliant disclosures
- **Simple pricing**: $499/month flat for up to 100 screenings

### Target Customer Segment
- Mid-market companies (100-500 employees) hiring 20-100 people/year
- Secondary: recruiting agencies (faster sales cycle, less compliance overhead)

### Go-to-Market
- G2/Capterra listing for organic discovery
- LinkedIn content marketing (thought leadership on "job-to-job matching")
- Integration marketplace listings (Greenhouse, Lever, Ashby app stores)
- HR podcast guest appearances

---

## Next Steps

1. **Build the technical prototype** (2-3 days): Python script that takes a JD + batch of resumes, generates ideal JDs for each candidate, computes cosine similarity, outputs ranked report. Use existing `branded_pdf_engine.py` for output.

2. **Package as a Marceau Solutions service** (1 day): Add to Digital Tower service offerings, create a one-pager/leave-behind for the AI client sprint.

3. **Test with 1-2 free pilot clients** (1-2 weeks): Offer free AI hiring analysis to companies William knows or encounters in the AI sprint. Validate the output quality and client reaction.

4. **If pilots succeed**: Price it, add to the AI services lineup, build case studies.

5. **If 5+ paying clients**: Then — and only then — evaluate building it as a SaaS product.

---

## Sources

### Market Size
- [Future Market Insights - Talent Acquisition Market](https://www.futuremarketinsights.com/reports/talent-acquisition-and-staffing-technology-market)
- [Fortune Business Insights - Online Recruitment Market](https://www.fortunebusinessinsights.com/online-recruitment-market-103730)
- [SkyQuest - AI Recruitment Market](https://www.skyquestt.com/report/ai-recruitment-market)
- [Mordor Intelligence - AI Recruitment Market](https://www.mordorintelligence.com/industry-reports/ai-recruitment-market)
- [DemandSage - AI Recruitment Statistics 2026](https://www.demandsage.com/ai-recruitment-statistics/)

### Competition
- [Peoplebox - 20 Best AI Recruiting Software 2026](https://www.peoplebox.ai/blog/best-ai-recruiting-software-2025/)
- [MokaHR - Best AI Resume Ranking Engine 2026](https://www.mokahr.io/articles/en/the-best-AI-resume-ranking-engine)
- [ConFit v2 (ACL 2025) - Hypothetical Resume Embedding](https://arxiv.org/abs/2502.12361)
- [CareerBERT - Shared Embedding Space Matching](https://arxiv.org/html/2503.02056v1)
- [National Law Review - Eightfold AI Lawsuit](https://natlawreview.com/article/ai-hiring-under-fire-what-eightfold-lawsuit-means-every-employer-using-algorithmic)

### Customer Research
- [Unbench - Hiring Pain Points 2025](https://www.unbench.us/blog/hiring-paint-points)
- [HiBob - 2025 Recruiting Challenges](https://www.hibob.com/blog/hiring-challenges/)
- [SHRM - Future of Talent Acquisition 2025](https://www.hr.com/en/resources/free_research_white_papers/hrcoms-future-of-talent-acquisition-2025_m9cg27v4.html)
- [Scion Staffing - Skills-Based Hiring 2026](https://scionstaffing.com/skills-based-hiring-trends-2026/)
- [HR Defense Blog - AI Hiring Legal Developments 2026](https://www.hrdefenseblog.com/2025/11/ai-in-hiring-emerging-legal-developments-and-compliance-guidance-for-2026/)

### Monetization
- [Select Software Reviews - ATS Pricing Guide 2026](https://www.selectsoftwarereviews.com/blog/ats-pricing-short-guide)
- [Toggl - ATS Pricing Guide](https://toggl.com/blog/applicant-tracking-system-pricing-guide)
- [SaaS Hero - B2B SaaS CAC Benchmarks 2026](https://www.saashero.net/strategy/b2b-saas-cac-benchmarks-2026/)
- [First Page Sage - B2B SaaS CAC Report](https://firstpagesage.com/reports/b2b-saas-customer-acquisition-cost-2024-report/)
- [SHRM - 2025 Recruiting Benchmarking Report](https://www.shrm.org/content/dam/en/shrm/research/2025-recruiting-benchmarking-report.pdf)
