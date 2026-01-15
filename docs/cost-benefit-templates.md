# Cost-Benefit Analysis Templates

Templates for evaluating development costs, operational expenses, and revenue potential before starting a new project.

## When to Use

Complete a cost-benefit analysis:
- BEFORE starting any project expected to take >8 hours
- When choosing between app types (MCP vs Web App vs Desktop)
- When presenting project proposals to stakeholders
- Before committing to hosting/infrastructure costs

---

## Development Cost Matrix

### By App Type

| App Type | Hours (Min-Max) | Complexity | Skills Required |
|----------|-----------------|------------|-----------------|
| CLI Tool | 8-24 | Low | Python basics |
| Python Skill (Claude) | 16-40 | Low-Medium | Python + Claude patterns |
| MCP Server (HTTP) | 24-60 | Medium | MCP protocol + Python + API design |
| MCP Server (EMAIL) | 40-80 | Medium | MCP + SMTP/IMAP + async workflows |
| MCP Server (OAUTH) | 60-100 | Medium-High | MCP + OAuth flows + token management |
| Web API (Backend Only) | 40-80 | Medium | FastAPI/Flask + deployment |
| Full-Stack Web App | 120-240 | High | Frontend + backend + DevOps + security |
| Desktop App | 160-320 | High | GUI framework + packaging + installers |
| Hybrid (MCP + Web) | 80-160 | Medium-High | MCP + Web + integration patterns |

### Complexity Factors

Add 20-50% to base hours for each:

| Factor | Impact | Example |
|--------|--------|---------|
| External API Integration | +20-30% | Calling Uber/Lyft/weather APIs |
| Authentication System | +30-40% | User accounts, OAuth, session management |
| Payment Processing | +40-50% | Stripe/PayPal integration |
| Real-time Features | +30-40% | WebSockets, live updates |
| Offline Capability | +40-50% | Local storage, sync logic |
| Multi-tenant | +50%+ | Per-organization data isolation |

### Development Cost Formula

```
Total Dev Cost = Base Hours × Hourly Rate × Complexity Multiplier

Example:
- MCP Server (HTTP): 40 hours base
- With external API: 40 × 1.25 = 50 hours
- Hourly rate: $50
- Total: 50 × $50 = $2,500 development cost
```

---

## Operational Cost Matrix

### Monthly Hosting Costs

| App Type | Hosting Range | Typical Setup |
|----------|---------------|---------------|
| CLI Tool | $0 | Local execution |
| Python Skill | $0 | Runs in Claude environment |
| MCP Server | $0-20 | Railway Starter / Heroku Free |
| Web API | $5-50 | Railway Pro / Heroku Basic |
| Full-Stack Web | $20-200 | Railway + Database + CDN |
| Desktop App | $0 | Local execution |
| Hybrid | $10-100 | MCP hosting + Web hosting |

### Common Service Costs

| Service | Free Tier | Paid Tier | Notes |
|---------|-----------|-----------|-------|
| Railway | 500 hrs/mo | $5-20/mo | Good for small projects |
| Heroku | Limited | $7-25/mo | Established, reliable |
| Vercel | Generous | $20/mo | Best for frontend |
| Supabase | 500MB | $25/mo | Postgres + Auth |
| MongoDB Atlas | 512MB | $9/mo | Document storage |
| SendGrid | 100/day | $15/mo | Email sending |
| Twilio | Trial credits | Pay-per-use | SMS/Voice |

### External API Costs

| API Type | Typical Cost | Volume Consideration |
|----------|--------------|---------------------|
| Weather APIs | $0-50/mo | Free tiers often sufficient |
| Maps/Geocoding | $0-200/mo | Per-request pricing |
| AI/ML APIs | $10-500/mo | Token-based pricing |
| Payment APIs | 2.9% + $0.30 | Per-transaction |
| Email APIs | $0-100/mo | Volume-based |
| SMS APIs | $0.01-0.05/msg | Per-message |

### Monthly Cost Formula

```
Monthly Operational Cost = Hosting + APIs + Services + Buffer

Example MCP Server:
- Hosting: $10/mo (Railway)
- External APIs: $20/mo (weather, geocoding)
- Services: $0 (no email/SMS)
- Buffer (10%): $3
- Total: $33/month
```

---

## Revenue Model Alignment

### MCP Aggregator Compatible

| Revenue Model | Per-Request | MCP Compatible | Best For |
|---------------|-------------|----------------|----------|
| Per-transaction | $0.01-0.50 | ✅ YES | Data lookups, comparisons |
| Usage-based tiers | Varies | ✅ YES | High-volume services |
| Freemium + Premium | Free + paid | ⚠️ Partial | Feature gating |

### Non-MCP Revenue Models

| Revenue Model | MCP Compatible | Best For |
|---------------|----------------|----------|
| Monthly subscription | ❌ NO | SaaS products |
| One-time purchase | ❌ NO | Desktop apps |
| Ad-supported | ❌ NO | Consumer web apps |
| Enterprise licensing | ❌ NO | B2B software |

### Revenue Projection Template

```markdown
## Revenue Projection: [Project Name]

### Assumptions
- Average requests per user per month: [X]
- Expected users (Month 1): [Y]
- User growth rate: [Z]% monthly
- Price per request: $[P]
- Platform fee (MCP Aggregator): 15%

### Projections

| Month | Users | Requests | Gross Revenue | Net (after 15%) |
|-------|-------|----------|---------------|-----------------|
| 1 | 100 | 500 | $50 | $42.50 |
| 3 | 150 | 750 | $75 | $63.75 |
| 6 | 250 | 1,250 | $125 | $106.25 |
| 12 | 500 | 2,500 | $250 | $212.50 |

### Break-Even Analysis
- Development cost: $[X]
- Monthly operational: $[Y]
- Monthly net revenue: $[Z]
- Break-even month: [Calculate]
```

---

## Quick Analysis Templates

### Template 1: Simple Project (CLI/Skill)

```markdown
## Cost-Benefit: [Project Name]

**App Type**: CLI Tool / Python Skill
**Development Hours**: [8-40]
**Monthly Cost**: $0

### Value Proposition
- Time saved per use: [X] minutes
- Uses per month: [Y]
- Monthly time saved: [X × Y] minutes = [Z] hours

### ROI Calculation
- Dev hours: [A]
- Time saved per month: [B] hours
- Break-even: [A ÷ B] months

### Decision
✅ Build if break-even < 6 months
❌ Skip if break-even > 12 months
```

### Template 2: MCP Server

```markdown
## Cost-Benefit: [Project Name]

**App Type**: MCP Server ([connectivity type])
**Development Hours**: [24-100]
**Monthly Cost**: $[10-50]

### Revenue Model
- Price per request: $[0.01-0.50]
- Platform fee: 15%
- Net per request: $[calculate]

### Cost Analysis
| Item | Monthly Cost |
|------|-------------|
| Hosting | $[X] |
| External APIs | $[Y] |
| Services | $[Z] |
| **Total** | $[sum] |

### Revenue Projections
| Scenario | Monthly Requests | Gross | Net |
|----------|------------------|-------|-----|
| Conservative | [X] | $[Y] | $[Z] |
| Expected | [X] | $[Y] | $[Z] |
| Optimistic | [X] | $[Y] | $[Z] |

### Break-Even
- Development cost: $[X]
- Monthly net (expected): $[Y]
- Monthly operational: $[Z]
- Monthly profit: $[Y - Z]
- Break-even: [X ÷ (Y - Z)] months

### Decision
✅ Build if: Break-even < 12 months AND monthly profit > $50
⚠️ Reconsider if: Break-even 12-24 months
❌ Skip if: Break-even > 24 months OR monthly profit < $20
```

### Template 3: Full-Stack Web App

```markdown
## Cost-Benefit: [Project Name]

**App Type**: Full-Stack Web App
**Development Hours**: [120-240]
**Monthly Cost**: $[50-200]

### Revenue Model
- Subscription price: $[X]/month
- Expected conversion rate: [Y]%
- Churn rate: [Z]%

### Cost Analysis
| Item | Monthly Cost |
|------|-------------|
| Hosting (Railway) | $[X] |
| Database (Supabase) | $[Y] |
| CDN/Assets | $[Z] |
| External APIs | $[A] |
| Email service | $[B] |
| **Total** | $[sum] |

### User & Revenue Projections
| Month | Users | Paying | MRR | Costs | Profit |
|-------|-------|--------|-----|-------|--------|
| 1 | [X] | [Y] | $[Z] | $[A] | $[B] |
| 6 | [X] | [Y] | $[Z] | $[A] | $[B] |
| 12 | [X] | [Y] | $[Z] | $[A] | $[B] |

### Break-Even
- Development cost: $[X]
- Cumulative profit by month 12: $[Y]
- Break-even month: [calculate]

### Decision
✅ Build if: Break-even < 18 months AND MRR potential > $500
⚠️ MVP first if: Uncertain market demand
❌ Skip if: Break-even > 24 months OR high competition exists
```

---

## Comparison Worksheet

Use this to compare multiple approaches:

```markdown
## Project: [Name]
## Date: [YYYY-MM-DD]

### Options Compared

| Criteria | Option A: [Type] | Option B: [Type] | Option C: [Type] |
|----------|------------------|------------------|------------------|
| **Dev Hours** | | | |
| **Dev Cost** | | | |
| **Monthly Cost** | | | |
| **Revenue Model** | | | |
| **Monthly Revenue (Expected)** | | | |
| **Break-Even (Months)** | | | |
| **MCP Compatible** | | | |
| **Maintenance Effort** | | | |
| **Scalability** | | | |
| **Risk Level** | | | |

### Weighted Score (1-5 each)

| Factor | Weight | Option A | Option B | Option C |
|--------|--------|----------|----------|----------|
| Low dev cost | 20% | | | |
| Low operational cost | 15% | | | |
| Revenue potential | 25% | | | |
| MCP alignment | 20% | | | |
| Low maintenance | 10% | | | |
| Low risk | 10% | | | |
| **Weighted Total** | 100% | | | |

### Recommendation
[Choose option with highest weighted score, explain rationale]
```

---

## Decision Thresholds

### Go/No-Go Criteria

| Metric | Green (Go) | Yellow (Caution) | Red (No-Go) |
|--------|------------|------------------|-------------|
| Break-even | < 6 months | 6-12 months | > 12 months |
| Monthly profit | > $100 | $20-100 | < $20 |
| Dev hours | < 40 | 40-120 | > 120 |
| Monthly cost | < $50 | $50-150 | > $150 |
| Maintenance hrs/mo | < 4 | 4-10 | > 10 |

### Quick Decision Matrix

```
High Revenue + Low Cost = ✅ BUILD NOW
High Revenue + High Cost = ⚠️ MVP FIRST
Low Revenue + Low Cost = ⚠️ INTERNAL TOOL ONLY
Low Revenue + High Cost = ❌ DON'T BUILD
```

---

## Related Documentation

- [App Type Decision Guide](app-type-decision-guide.md)
- [Project Kickoff Questionnaire](../templates/project-kickoff-questionnaire.md)
- [Development to Deployment Pipeline](development-to-deployment.md)
