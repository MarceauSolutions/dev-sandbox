# Resume & Cover Letter Builder — Approach Comparison Matrix

**Date**: 2026-02-17
**Evaluators**: 4 parallel research agents (SOP 9)

---

## Raw Scores (1-5 Stars)

| Criterion | Weight | Approach 1: AI Assistant | Approach 2: MCP Server | Approach 3: Web App | Approach 4: n8n Webhook |
|-----------|--------|:---:|:---:|:---:|:---:|
| **Revenue Potential** | 5x | 2 | 1 | 5 | 3 |
| **Time to Market** | 4x | 5 | 5 | 3 | 5 |
| **Build Complexity** | 4x | 5 | 4 | 3 | 5 |
| **Target Market Size** | 3x | 1 | 2 | 5 | 3 |
| **Maintenance Burden** | 3x | 5 | 4 | 2 | 4 |
| **Scalability** | 2x | 1 | 2 | 5 | 2 |
| **Infrastructure Reuse** | 2x | 5 | 5 | 4 | 5 |
| **Simple Average** | | **3.4/5** | **2.9/5** | **3.9/5** | **3.9/5** |

---

## Weighted Scores (max 115 points)

| Criterion | Weight | AI Assistant | MCP Server | Web App | n8n Webhook |
|-----------|--------|:---:|:---:|:---:|:---:|
| Revenue Potential | 5x | 10 | 5 | **25** | 15 |
| Time to Market | 4x | **20** | **20** | 12 | **20** |
| Build Complexity | 4x | **20** | 16 | 12 | **20** |
| Target Market Size | 3x | 3 | 6 | **15** | 9 |
| Maintenance Burden | 3x | **15** | 12 | 6 | 12 |
| Scalability | 2x | 2 | 4 | **10** | 4 |
| Infrastructure Reuse | 2x | **10** | **10** | 8 | **10** |
| **WEIGHTED TOTAL** | | **80/115** | **73/115** | **88/115** | **90/115** |
| **WEIGHTED %** | | **69.6%** | **63.5%** | **76.5%** | **78.3%** |

---

## Head-to-Head Comparison

### Revenue & Business Model

| Metric | AI Assistant | MCP Server | Web App | n8n Webhook |
|--------|-------------|------------|---------|-------------|
| **Pricing** | $49 one-time | Free (no monetization) | $14.99/mo subscription | $9.99 per generation |
| **Revenue Model** | One-time sales | Lead magnet only | SaaS subscription | Per-use transactional |
| **Monthly Revenue (realistic)** | $245-735 | $0-200 | $350-35,000 | $100-5,000 |
| **Annual Revenue (ceiling)** | $9,000 | ~$2,400 | $420,000+ | $60,000 |
| **Gross Margin** | ~100% | N/A | 91-97% | 93% |
| **Break-even** | Day 1 (no costs) | N/A | Month 2-3 | Sale #1 |

### Technical Profile

| Metric | AI Assistant | MCP Server | Web App | n8n Webhook |
|--------|-------------|------------|---------|-------------|
| **New Code** | ~800 lines | ~600 lines | ~3,000+ lines | ~1,030 lines |
| **New Infrastructure** | None | None | Vercel + DB | None |
| **AI Cost/Generation** | $0 (user pays Claude) | $0 (local) | $0.04-0.08 | $0.085 |
| **Dependencies** | Python, pandoc | Python, pandoc, MCP SDK | Node.js, Python, PostgreSQL, Vercel | Existing EC2 stack |
| **Concurrent Users** | N/A (local) | N/A (local) | 500+ | 5-10 |
| **Max Monthly Volume** | N/A (local) | N/A (local) | 50,000+ | ~2,000 |

### Build Timeline

| Phase | AI Assistant | MCP Server | Web App | n8n Webhook |
|-------|-------------|------------|---------|-------------|
| **MVP** | 3-5 days | 4-5 days | 10-14 days | 3-5 days |
| **Production-ready** | 5-6 days | 7-10 days | 14-21 days | 5 days |
| **With monetization** | 5-6 days | 7-10 days (needs API backend) | 14-21 days | 5 days |

### Target Market

| Metric | AI Assistant | MCP Server | Web App | n8n Webhook |
|--------|-------------|------------|---------|-------------|
| **Who buys** | Developers with Claude Code | Nobody (free) | All job seekers | Quality-focused job seekers |
| **Market size** | 5K-15K | 25-900 paying users | Millions | Millions (but niche positioning) |
| **Requires tech skills** | Yes (CLI, git, JSON) | Yes (pip, MCP config) | No | No |
| **Distribution** | Gumroad | PyPI + MCP Registry | SEO, ads, Product Hunt | Landing page + ads |

---

## Key Findings from Each Agent

### Agent 1 (AI Assistant) — "Build it, but don't expect a business"
- Fastest and cheapest to build, highest infrastructure reuse
- Extremely narrow market (Claude Code users who are job-seeking)
- Best use: Phase 1 quick win, portfolio piece, code reuse for bigger product
- Fatal weakness: $9K/year ceiling, market too small

### Agent 2 (MCP Server) — "Great portfolio piece, terrible business"
- 5 competing MCP resume packages already exist, ALL free
- MCP protocol has zero payment infrastructure
- Monetization requires a hosted backend (doubles complexity)
- Best use: Free lead magnet driving users to paid web app

### Agent 3 (Web App) — "The real business, but takes the longest"
- $2.5B TAM, 10-12% CAGR, proven willingness to pay $15-30/mo
- 95% margins at scale, SEO as free acquisition channel
- Requires 10-14 days for MVP, ongoing maintenance and support
- Best use: The scalable, revenue-generating end state

### Agent 4 (n8n Webhook) — "Ship in 3 days, validate with real money"
- $0 incremental infrastructure cost (everything already running)
- 93% margin on $9.99/generation, break-even on first sale
- Hard ceiling at ~2,000 resumes/month, no self-service UX
- Best use: Lean validation — test demand before investing in SaaS

---

## Critical Insight: These Are NOT Mutually Exclusive

All 4 agents independently recommended a **phased approach**. The approaches build on each other:

```
Phase 0 (Days 1-5):    n8n Webhook MVP → validate demand with real $$$
Phase 1 (Days 6-10):   AI Assistant on Gumroad → secondary revenue stream
Phase 2 (Days 11-25):  Web App MVP → scalable SaaS platform
Phase 3 (ongoing):     MCP Server → free lead magnet → drives web app signups
```

Every line of Python code written for Phase 0 (n8n webhook) is reusable in Phase 2 (web app backend). The resume generation engine, cover letter logic, ATS scoring, and PDF pipeline are the same across all 4 approaches — only the delivery mechanism changes.
