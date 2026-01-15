# Project Viability Assessment

**Created**: 2026-01-14
**Purpose**: Quick assessment of all dev-sandbox projects for MCP commercialization potential

---

## Assessment Criteria

Using our documented framework from `docs/app-type-decision-guide.md`:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **MCP Fit** | 25% | Is value in data/computation (not UI)? Transaction-based revenue? |
| **Market Pain** | 25% | Is the pain real, quantified, and worth paying to solve? |
| **Competition** | 20% | Is there a gap we can fill? |
| **Unit Economics** | 20% | Can we make money at scale? |
| **Build Effort** | 10% | How much work to productize? |

---

## Project Assessments

### 1. Fitness Influencer AI

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 2/5 | Value is in UX/workflow, not raw data |
| Market Pain | 5/5 | 73% burnout, 3-4 hrs/video, $40-77/mo spend |
| Competition | 4/5 | No direct competitor, but Canva/CapCut threat |
| Unit Economics | 4/5 | 5.8x LTV/CAC achievable at $49/mo |
| Build Effort | 3/5 | Core built, needs polish |

**Overall: 3.6/5** | **Verdict: CONDITIONAL GO (Web App, not MCP)**

**Already Analyzed**: See `projects/fitness-influencer/market-analysis/consolidated/GO-NO-GO-DECISION.md`

**Recommendation**: Continue as subscription web app, NOT MCP. Value is in the integrated experience.

---

### 2. Lead Scraper

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 5/5 | Pure data service, perfect for per-lead pricing |
| Market Pain | 4/5 | Manual prospecting takes 10+ hrs/week |
| Competition | 3/5 | Apollo, Hunter, ZoomInfo exist but expensive |
| Unit Economics | 4/5 | $0.25-0.50/lead viable, API costs ~$0.05/lead |
| Build Effort | 4/5 | Core built, needs Apollo/LinkedIn integration |

**Overall: 4.0/5** | **Verdict: GO for MCP**

**MCP Revenue Model**:
- Per-lead pricing: $0.25 (basic) to $0.50 (enriched)
- Target: Small businesses priced out of Apollo ($99/mo+)
- Niche: Local service businesses (gyms, contractors, salons)

**Channels**: PyPI + MCP Registry + Cloud Function

---

### 3. Interview Prep

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 2/5 | Value is in interactive experience, not data |
| Market Pain | 4/5 | Interview anxiety is real, prep is time-consuming |
| Competition | 3/5 | Many tools exist (Pramp, interviewing.io) |
| Unit Economics | 3/5 | One-time use limits LTV |
| Build Effort | 4/5 | Core built, working well |

**Overall: 3.2/5** | **Verdict: KEEP AS PERSONAL TOOL**

**Recommendation**: Great personal productivity tool, poor MCP candidate. Interview prep is interactive, not transactional.

---

### 4. Amazon Seller Operations

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 5/5 | Pure data (inventory, fees, analytics) |
| Market Pain | 4/5 | Seller Central is painful, manual work |
| Competition | 4/5 | No MCP-native competitor |
| Unit Economics | 4/5 | Per-query pricing viable |
| Build Effort | 3/5 | SP-API integration complex |

**Overall: 4.0/5** | **Verdict: GO for MCP**

**MCP Revenue Model**:
- Per-query: $0.01-0.05 for inventory/fee lookups
- Target: Amazon sellers who want AI-assisted operations
- Niche: Small sellers (1-100 SKUs) who can't afford enterprise tools

**Channels**: PyPI + MCP Registry

---

### 5. MCP Aggregator (Platform)

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 5/5 | IS the MCP platform itself |
| Market Pain | 5/5 | AI agents need standardized service access |
| Competition | 4/5 | First-mover in aggregation space |
| Unit Economics | 5/5 | Per-transaction fees at scale |
| Build Effort | 2/5 | Complex platform, lots of work |

**Overall: 4.2/5** | **Verdict: LONG-TERM PRIORITY**

**Revenue Model**: Transaction fees (5-10%) on all routed queries

**Note**: This is the platform that hosts other MCPs. Higher priority than individual MCPs.

---

### 6. Time Blocks

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 2/5 | Personal productivity, not data service |
| Market Pain | 2/5 | Calendars exist, pain is mild |
| Competition | 1/5 | Google Calendar, Calendly, etc. |
| Unit Economics | 1/5 | No clear revenue model |
| Build Effort | 5/5 | Already built |

**Overall: 2.2/5** | **Verdict: PERSONAL TOOL ONLY**

**Recommendation**: Keep for personal use. No commercial potential.

---

### 7. Naples Weather

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 3/5 | Data service, but very niche |
| Market Pain | 2/5 | Weather apps exist everywhere |
| Competition | 1/5 | Weather.com, Dark Sky, etc. |
| Unit Economics | 1/5 | No differentiation to charge for |
| Build Effort | 5/5 | Already built |

**Overall: 2.4/5** | **Verdict: PERSONAL TOOL ONLY**

---

### 8. Email Analyzer

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 4/5 | Analysis service, good for AI agents |
| Market Pain | 3/5 | Email overload is real |
| Competition | 3/5 | Superhuman, SaneBox exist |
| Unit Economics | 3/5 | Per-email pricing could work |
| Build Effort | 3/5 | Needs more development |

**Overall: 3.2/5** | **Verdict: MAYBE - Needs more analysis**

---

### 9. Resume Generator

| Criterion | Score | Notes |
|-----------|-------|-------|
| MCP Fit | 3/5 | Could be document generation service |
| Market Pain | 3/5 | Resume writing is tedious |
| Competition | 2/5 | Many resume builders exist |
| Unit Economics | 2/5 | One-time use, low LTV |
| Build Effort | 4/5 | Mostly built |

**Overall: 2.8/5** | **Verdict: PERSONAL TOOL ONLY**

---

## Summary: MCP Commercialization Priorities

### Tier 1: Build and Launch MCPs

| Project | Score | Action | Revenue Model |
|---------|-------|--------|---------------|
| **Lead Scraper** | 4.0 | Convert to MCP + Cloud Function | $0.25-0.50/lead |
| **Amazon Seller** | 4.0 | Publish to MCP Registry | $0.01-0.05/query |

### Tier 2: Platform Investment

| Project | Score | Action | Revenue Model |
|---------|-------|--------|---------------|
| **MCP Aggregator** | 4.2 | Continue platform development | 5-10% transaction fee |

### Tier 3: Subscription Products (Not MCP)

| Project | Score | Action | Revenue Model |
|---------|-------|--------|---------------|
| **Fitness Influencer** | 3.6 | Launch as web app | $19-49/mo subscription |

### Tier 4: Personal Tools (No Commercialization)

| Project | Score | Action |
|---------|-------|--------|
| Interview Prep | 3.2 | Keep as skill |
| Email Analyzer | 3.2 | Maybe revisit later |
| Resume Generator | 2.8 | Keep as skill |
| Naples Weather | 2.4 | Keep as skill |
| Time Blocks | 2.2 | Keep as skill |

---

## Immediate Action Items

1. **Lead Scraper** → You need to get API keys:
   - Google Places: https://console.cloud.google.com/apis/credentials
   - Yelp Fusion: https://www.yelp.com/developers/v3/manage_app
   - Apollo.io: https://app.apollo.io/#/settings/integrations/api (free tier: 50 credits/mo)

2. **Fitness Influencer** → Continue development toward subscription launch

3. **Amazon Seller** → Already has API keys, can publish to MCP Registry

---

## 10x Rule Application

Per `docs/optimization-threshold-policy.md`, only pursue if 10x improvement:

| Project | Current State | With MCP | 10x? |
|---------|---------------|----------|------|
| Lead Scraper | Manual prospecting | Automated at $0.25/lead | ✅ YES |
| Amazon Seller | Manual Seller Central | AI-assisted queries | ✅ YES |
| Fitness Influencer | Using 4-6 apps | One integrated platform | ✅ YES |
| Interview Prep | Works fine as skill | MCP wouldn't add value | ❌ NO |
| Time Blocks | Works fine as skill | No commercial need | ❌ NO |

---

*Assessment complete. Focus on Lead Scraper MCP and Fitness Influencer subscription.*
