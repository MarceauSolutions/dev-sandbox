# Recommended Approach: Phased Deployment (n8n Webhook First → Web App Scale)

**Date**: 2026-02-17
**Decision**: Multi-phase strategy, NOT a single approach

---

## Decision

Use a **3-phase deployment strategy** that starts with the fastest path to revenue and graduates to the highest-ceiling platform:

| Phase | Approach | Timeline | Revenue Target | Go/No-Go |
|-------|----------|----------|---------------|-----------|
| **Phase 0** | n8n Webhook + Landing Page | Days 1-5 | First 10 paying customers | Ship it |
| **Phase 1** | AI Assistant on Gumroad | Days 6-10 | $250/mo secondary income | Ship alongside Phase 0 |
| **Phase 2** | Web App (Next.js + FastAPI) | Days 11-25 | $1K MRR in 60 days | Only if Phase 0 gets 100+ sales/month |
| **Phase 3** | Free MCP Server | Day 26+ | Lead magnet (0 revenue) | Only after Web App is live |

---

## Why This Order

### Phase 0: n8n Webhook (Weighted Score: 90/115 — HIGHEST)

**Start here because:**
- **$0 incremental cost** — EC2, n8n, Stripe, Google Drive, Claude API all running
- **3-5 days to live product** — fastest of any approach
- **Real revenue from day 1** — $9.99/generation, 93% margin, break-even on sale #1
- **Validates the core question** — will people pay for AI-tailored resumes?
- **Every line of code reuses** in Phase 2 (same Python engine, different frontend)

**The decision gate:** If Phase 0 generates >100 sales in 60 days → green-light Phase 2. If <20 sales → the market signal is weak, don't invest 2+ weeks in a web app.

### Phase 1: AI Assistant (Weighted Score: 80/115)

**Ship alongside Phase 0 because:**
- Only 1-2 extra days (generalize profile.json, write CLAUDE.md)
- Different market segment (developers with Claude Code)
- Additional $250-750/mo revenue stream
- Portfolio piece for William's brand

### Phase 2: Web App (Weighted Score: 88/115 — HIGHEST CEILING)

**Build only after validation because:**
- 10-14 days of development time (significant investment)
- Requires ongoing maintenance, support, and marketing
- $2.5B TAM with 95% margins — this is the real business
- SEO takes 3-6 months to compound — start content early
- **All Phase 0 Python code becomes the FastAPI backend**

### Phase 3: MCP Server (Weighted Score: 73/115 — LOWEST)

**Free lead magnet, not a product:**
- 5 competing MCP resume tools already exist, all free
- No monetization path within MCP protocol
- But: drives developers to the web app (conversion funnel)
- Builds William's MCP/developer brand

---

## Revenue Projections (Combined Strategy)

| Month | Phase 0 (n8n) | Phase 1 (AI Asst) | Phase 2 (Web App) | Total MRR |
|-------|:---:|:---:|:---:|:---:|
| 1 | $200 | $100 | — | $300 |
| 2 | $400 | $200 | — | $600 |
| 3 | $500 | $250 | $350 (launch) | $1,100 |
| 6 | $500 | $300 | $1,750 | $2,550 |
| 12 | $500 (plateau) | $400 | $5,000 | $5,900 |

**Year 1 projection: ~$30,000-40,000** (conservative)
**Year 2 projection: ~$60,000-100,000** (if web app gains SEO traction)

---

## Cost Analysis

### Phase 0 Investment
- **Development time**: 3-5 days (22-33 hours)
- **New infrastructure cost**: $0 (everything already running)
- **Ongoing cost**: ~$0.68 per generation (Claude API + Stripe fees)

### Phase 1 Investment (incremental)
- **Development time**: 1-2 additional days
- **Gumroad listing**: $0 (Gumroad takes 10% on sales)
- **Ongoing cost**: $0 (users run locally)

### Phase 2 Investment (if validated)
- **Development time**: 10-14 days
- **Monthly infra**: $24/mo at 100 users → $359/mo at 1,000 users
- **Ongoing cost**: $0.04-0.08 per generation + hosting

### Total Upfront Investment: 5-7 days for Phases 0+1

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Nobody pays $9.99 for AI resume | Phase 0 validates in 3-5 days for $0 cost. Fail fast. |
| EC2 single point of failure | Monitor with CloudWatch + Telegram alerts. Upgrade to t3.large if scaling. |
| Web app takes too long | Use Streamlit as Phase 2a fast-track (2-3 day MVP) before full Next.js build |
| Claude API costs spike | Use Haiku for parsing/ATS scoring, Sonnet only for writing. $0.037 optimized flow. |
| Competitors copy the approach | 89+ battle-tested output examples give quality edge. Speed to market matters. |
| High churn on web app subscriptions | Offer annual plans ($99/yr). Credit packs for occasional users. |

---

## Alternatives Considered

### Web App First (Agent 3's recommendation)
- **Why not chosen as Phase 0**: 10-14 days to MVP, $50-100/mo hosting before revenue. Higher risk for first product launch.
- **When we'd reconsider**: If William has high confidence in demand (e.g., waitlist of 100+ emails)

### MCP Server as primary product (Agent 2's research)
- **Why not chosen**: Zero revenue potential. All 5 competitors are free. No payment infrastructure in MCP.
- **When we'd reconsider**: If MCP adds a marketplace/payment layer (unlikely near-term)

### AI Assistant as primary product (Agent 1's research)
- **Why not chosen as sole approach**: $9K/year ceiling, market too small (5K-15K prospects)
- **When we'd reconsider**: If Claude Code user base grows 10x

---

## Next Steps

### Week 1: Phase 0 (n8n Webhook MVP)

| Day | Deliverable |
|-----|------------|
| Day 1 | Python scripts: `job_parser.py`, `resume_generator.py`, `cover_letter_gen.py`, `pdf_builder.py` |
| Day 2 | n8n workflow: 8-node webhook-to-email pipeline + Stripe checkout integration |
| Day 3 | Landing page: `index.html` (sales), `upload.html` (input form), `status.html` (confirmation) |
| Day 4 | End-to-end testing: 5 real test generations, error handling, monitoring |
| Day 5 | Soft launch: live on marceausolutions.com/resume-builder or subdomain |

### Week 2: Phase 1 (AI Assistant) + Marketing

| Day | Deliverable |
|-----|------------|
| Day 6 | Generalize `profile.json` template from resume_data.json |
| Day 7 | Write standalone CLAUDE.md + README.md for AI assistant repo |
| Day 8 | Test with fresh Claude Code instance, list on Gumroad |
| Day 9-10 | Launch marketing: Reddit (r/resumes, r/jobs), Product Hunt listing prep |

### Decision Gate (Day 60)

| Metric | Green Light Phase 2 | Yellow (Iterate) | Red (Pivot) |
|--------|---------------------|-------------------|-------------|
| Phase 0 sales | >100 total | 20-100 total | <20 total |
| Phase 1 sales | >10 total | 1-10 total | 0 |
| Customer feedback | Positive, repeat buyers | Mixed | Negative |
| Refund rate | <5% | 5-15% | >15% |

---

## Architecture Decision

### Shared Core Engine (used by ALL phases)

**Location**: `projects/shared/resume/src/` (project-specific, not execution/)

```
projects/shared/resume/src/
├── resume_data.json          # Schema template (existing)
├── engine/
│   ├── job_parser.py         # Extract requirements from job posting
│   ├── resume_generator.py   # Tailor resume from profile + job match
│   ├── cover_letter_gen.py   # Generate cover letter
│   ├── ats_optimizer.py      # ATS keyword scoring
│   └── pdf_builder.py        # Markdown → PDF (pandoc wrapper)
├── templates/
│   ├── profile_template.json # Buyer-friendly profile schema
│   ├── resume_modern.md      # Resume markdown template
│   └── cover_letter.md       # Cover letter template
└── output/                   # (existing 89+ examples, gitignored for buyers)
```

### Phase 0 Additions (n8n webhook)
- 1 n8n workflow on EC2
- 3 HTML pages for landing site

### Phase 1 Additions (AI assistant)
- `~/ai-assistants/resume-builder/` (SOP 31 structure)
- CLAUDE.md + README.md

### Phase 2 Additions (web app)
- `projects/shared/resume/webapp/` (Next.js frontend)
- FastAPI wrapper around engine/ scripts
- PostgreSQL for user accounts

---

## Success Criteria

- [ ] Phase 0 live within 5 days
- [ ] Phase 1 on Gumroad within 10 days
- [ ] 10 paying customers within 30 days
- [ ] 100 paying customers within 60 days (Phase 2 go/no-go)
- [ ] $1K MRR within 90 days
- [ ] Comparison matrix and recommendation documented (this file)
