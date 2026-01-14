# Amazon Buyer MCP - Consolidated Research Findings

**Research Date**: 2026-01-14
**Status**: Architecture Exploration Complete (SOP 9)

---

## Executive Summary

Research from two parallel agents indicates that building an Amazon Buyer MCP is **FEASIBLE** but with significant constraints. The key insight is that **no single API solves all problems** - a successful solution requires combining multiple specialized APIs.

**Overall Feasibility**: ⭐⭐⭐⭐ (4/5) - Possible with constraints

---

## Agent 1: API Feasibility Research

### API Options Analyzed

| API | Status | Cost | Use Case |
|-----|--------|------|----------|
| **Keepa** | ✅ Recommended | €29-99/mo | Price history, trends, stock tracking |
| **PA-API v5** (Amazon) | ⚠️ Requires approval | Variable | Current pricing, product data |
| **CamelCamelCamel** | ❌ No API | N/A | Deprecated |
| **ReviewMeta** | ❌ No API | N/A | Not available |
| **Fakespot** | ❌ No API | N/A | Not available |

### Recommended Architecture

**Tier 1: Core Data (Keepa)**
- Product information
- Price history and trends
- Stock/availability tracking
- Rating history

**Tier 2: Enhanced Data (PA-API)**
- Current pricing from multiple sellers
- Additional product metadata
- Basic review metadata

**Tier 3: Analysis (Optional)**
- Sentiment analysis via NLP service
- Price trend analysis
- Deal detection algorithms

### Legal/Compliance Status

| Approach | Status |
|----------|--------|
| Keepa API | ✅ SAFE - Explicitly allowed |
| PA-API v5 | ✅ SAFE - Official Amazon API |
| Web scraping Amazon.com | ❌ AVOID - Violates ToS |
| Cart/checkout automation | ❌ AVOID - Violates ToS |
| ReviewMeta/Fakespot scraping | ❌ AVOID - No API, ToS violation |

### Cost Projections

**Small-scale (100 DAU)**
- Keepa: $30/month
- PA-API: $10-20/month
- NLP (optional): $5-10/month
- **Total: $45-60/month**

**Medium-scale (1000 DAU)**
- Keepa: $99/month (premium)
- PA-API: $50-100/month
- NLP: $30-50/month
- **Total: $179-249/month**

---

## Agent 2: Competitive Landscape Analysis

### Competitor Matrix

| Feature | Honey | Keepa | Fakespot | CamelCamelCamel |
|---------|-------|-------|----------|-----------------|
| Price Tracking | Limited | ✓✓ Advanced | ✗ | ✓✓ Advanced |
| Price History | ✗ | ✓✓ Detailed | ✗ | ✓✓ Very Detailed |
| Coupon Finder | ✓✓ Strong | ✗ | ✗ | ✗ |
| Review Analysis | ✗ | ✗ | ✓✓ Advanced | ✗ |
| Fake Review Detection | ✗ | ✗ | ✓✓ ML-based | ✗ |
| API/Integration | ✗ | ✓✓ Robust | ✗ | ✓ Basic |

### Market Gaps Identified

**What existing tools DON'T do:**

1. **AI-Powered Summarization** - No tool summarizes 1000+ reviews intelligently
2. **Context-Aware Recommendations** - Tools don't know user budget/needs
3. **Fragmented Experience** - Users toggle between 4+ tools
4. **Smart Comparison** - No intelligent cross-product comparison
5. **Purchase Timing Guidance** - No AI advice on when to buy
6. **Return Risk Assessment** - No tool evaluates return rates
7. **Seller Reliability** - Consumer tools hide seller history

### Unique Value Proposition

**"Your Personal Amazon Shopping AI"**

What an AI assistant can do that these tools can't:

1. **Intelligent Review Summarization**
   - Filter fake reviews
   - Extract common complaints/praises
   - Surface real user quotes

2. **Contextual Deal Intelligence**
   - Compare to historical prices
   - Predict upcoming sales
   - Stock level awareness

3. **Multi-Product Comparison with Reasoning**
   - Ranked recommendations
   - Trade-off explanations
   - User profile matching

4. **Fraud & Quality Risk Assessment**
   - Review authenticity
   - Seller reliability
   - Price anomaly detection

---

## Decision: PROCEED

### Recommended Approach

**Phase 1: MVP (Keepa Only)**
- Product lookup
- Price history
- Trend analysis
- Price alerts

**Cost**: $30/month
**Timeline**: 2-3 weeks

**Phase 2: Enhanced (Keepa + PA-API)**
- Multi-seller pricing
- Inventory tracking
- Current availability

**Cost**: $40-50/month
**Timeline**: +1 week

**Phase 3: AI Layer**
- NLP review analysis
- Comparison intelligence
- Purchase recommendations

**Cost**: +$10-20/month
**Timeline**: +1 week

### Tools to Implement

| Tool | Description | Priority |
|------|-------------|----------|
| `lookup_product` | Get product details + price history | P0 |
| `track_price` | Set price alerts | P0 |
| `compare_products` | Side-by-side comparison | P1 |
| `analyze_reviews` | NLP-based review summary | P1 |
| `find_deals` | Best deals in category | P2 |
| `check_seller` | Seller reliability info | P2 |

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| PA-API approval denial | Use Keepa as primary, make PA-API optional |
| Keepa pricing increase | Monitor, research alternatives |
| Rate limit exhaustion | Smart caching, user quotas |
| Data staleness | Cache with TTL, refresh on demand |

---

## Next Steps

1. **Validate Keepa API** - Test with real ASINs
2. **Apply for PA-API** - Create affiliate account
3. **Create directive** - `directives/amazon-buyer.md`
4. **Prototype MCP** - Basic 2-3 tools
5. **Test with Claude Desktop** - Verify integration

---

## Files to Create

```
projects/amazon-buyer/
├── exploration/                    # ✅ Created
│   └── CONSOLIDATED-FINDINGS.md    # ✅ This file
├── directives/
│   └── amazon-buyer.md             # TODO
├── src/
│   └── amazon_buyer_mcp/
│       ├── __init__.py
│       ├── server.py
│       └── keepa_client.py
├── pyproject.toml
├── server.json
└── README.md
```

---

## Sources

- Agent 1: API Feasibility Research (aa428e6)
- Agent 2: Competitive Landscape Analysis (ade1394)
- Keepa API Documentation (knowledge cutoff)
- Amazon PA-API v5 Documentation (knowledge cutoff)
