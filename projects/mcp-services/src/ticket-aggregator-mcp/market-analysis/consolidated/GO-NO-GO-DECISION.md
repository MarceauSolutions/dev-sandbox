# Go/No-Go Decision: Ticket Aggregator MCP

**Analysis Date**: 2026-02-07
**Overall Score**: 3.09/5

---

## Decision: CONDITIONAL GO - PIVOT REQUIRED

The original vision of "AI agents programmatically purchasing tickets" is **NOT viable** due to legal constraints (BOTS Act). However, a **pivoted approach** is viable and worth pursuing.

---

## The Dealbreaker

The BOTS Act of 2016 makes it **illegal** to:
- Use automated tools to circumvent security measures on ticket sites
- Use technology to exceed posted ticket limits
- Use automated ticket purchasing software

**Enforcement is real**: $31M+ in fines against 3 brokers in 2021. A 2025 Executive Order signals increased enforcement ahead.

**Bottom line**: Building an MCP that automates ticket purchasing without official partnerships = federal law violation.

---

## Viable Pivot: "Ticket Discovery MCP"

Instead of **purchasing** tickets, build an MCP that helps AI agents **discover and refer** tickets.

### What This Looks Like

```
User: "Find me tickets to Kendrick Lamar in Miami under $200"

AI Agent → Ticket Discovery MCP
           ├── Search SeatGeek API (public)
           ├── Search Ticketmaster Discovery API (public)
           ├── Compare prices across platforms
           └── Return: "Found 4 options. Best price: $189 on SeatGeek"
                       [Affiliate link to SeatGeek]
```

### Why This Works

| Factor | Original Vision | Pivoted Vision |
|--------|-----------------|----------------|
| **Legality** | Illegal (BOTS Act) | Legal (using public APIs) |
| **API Access** | Requires partnerships | Public APIs available |
| **Monetization** | Transaction fees | Affiliate commissions (6-9%) |
| **Complexity** | High (payments, liability) | Low (just search + link) |
| **Time to Market** | 6-12 months | 2-4 weeks MVP |
| **Risk** | High (legal, platform) | Low |

---

## Recommended Path Forward

### Phase 1: Discovery MVP (Weeks 1-4)
**Build**: Search-only MCP using public APIs
- Ticketmaster Discovery API (free, 5000 calls/day)
- SeatGeek API (free, public)
- Eventbrite API (free)

**Features**:
- `search_events` - Find events by artist, venue, date, location
- `get_prices` - Compare prices across platforms
- `get_details` - Venue info, seating charts, event details

**Monetization**: None (validate demand first)

**Success Metric**: 100 developers install/try the MCP

### Phase 2: Affiliate Integration (Months 2-3)
**Add**: Affiliate links for commission
- StubHub Affiliate (9% commission)
- SeatGeek Partner Program (~$11/sale)
- Vivid Seats Affiliate (4-6%)

**Features**:
- `get_purchase_link` - Returns affiliate link to best price
- Track conversions

**Monetization**: 4-9% of referred purchases

**Success Metric**: First $1,000 in affiliate revenue

### Phase 3: Premium Features (Months 4-6)
**Add**: Subscription tier for power users
- Price alerts / drop notifications
- Historical price data
- Exclusive pre-sale access (via partnerships)

**Monetization**: $29-99/month subscriptions

**Success Metric**: 50 paying subscribers

### Phase 4: Partnership Pursuit (Month 6+)
**Pursue**: Official API partnerships
- Apply for Ticketmaster Partner API
- Negotiate TicketNetwork Mercury access
- Explore white-label deals with enterprise perks platforms

**This only makes sense AFTER proving demand in Phases 1-3**

---

## Alternative: B2B Pivot

If consumer/developer market is slow, pivot to B2B:

**Target Customers**:
- Enterprise perks platforms (TicketsatWork, Abenity)
- Travel agencies with ticket offerings
- Corporate concierge services
- Licensed ticket brokers (tools, not purchasing)

**Value Proposition**: Unified API layer for their existing authorized access

**Pricing**: $1,000-$5,000/month enterprise contracts

---

## Financial Projections (Pivoted Model)

### Year 1 (Discovery + Affiliate)
| Quarter | Developers | Affiliate Revenue | Total |
|---------|------------|-------------------|-------|
| Q1 | 50 | $500 | $1,500 |
| Q2 | 150 | $2,000 | $6,000 |
| Q3 | 300 | $5,000 | $15,000 |
| Q4 | 500 | $10,000 | $30,000 |
| **Year 1** | | | **$52,500** |

### Year 2 (Add Subscriptions)
| Revenue Stream | Projection |
|----------------|------------|
| Affiliate | $80,000 |
| Subscriptions (200 @ $29) | $70,000 |
| **Year 2 Total** | **$150,000** |

### Year 3 (Scale)
| Revenue Stream | Projection |
|----------------|------------|
| Affiliate | $200,000 |
| Subscriptions | $200,000 |
| Enterprise (3 contracts) | $100,000 |
| **Year 3 Total** | **$500,000** |

---

## What We're NOT Building

To be crystal clear, we will NOT:

1. **Automate ticket purchasing** - Illegal under BOTS Act
2. **Scrape ticket websites** - ToS violation, legal risk
3. **Bypass CAPTCHAs or security** - Federal crime
4. **Store payment information** - Unnecessary liability
5. **Complete transactions** - Users click affiliate links

---

## Next Steps

If proceeding:

1. **Week 1**: Set up project structure, apply for API keys
2. **Week 2**: Build core search functionality
3. **Week 3**: Create MCP server with tool definitions
4. **Week 4**: Test, document, publish to MCP registry

**Estimated MVP Cost**: $0 (API keys are free, can use existing infrastructure)
**Estimated Time**: 20-40 hours of development

---

## Decision Summary

| Original Concept | Verdict |
|------------------|---------|
| AI agents purchase tickets autonomously | **NO-GO** (illegal) |

| Pivoted Concept | Verdict |
|-----------------|---------|
| AI agents discover & compare tickets, link to purchase | **GO** |

---

## Rationale

The pivot is worth pursuing because:

1. **Legal**: Uses only public APIs within ToS
2. **Fast**: 2-4 week MVP vs 6-12 months
3. **Low Risk**: No payments, no liability, affiliate fallback
4. **First Mover**: No MCP competitors in ticket discovery
5. **Scalable**: Can add partnerships later if successful
6. **Validates Demand**: Proves market before heavy investment

The key insight from this analysis: **the AI agent future for ticketing will happen through official partnerships, not automation**. By building the discovery layer now, you position to be the preferred partner when platforms open up AI-native APIs.

---

## Final Recommendation

**PROCEED** with the pivoted "Ticket Discovery MCP" approach.

Build the MVP in 2-4 weeks, validate demand with developers, monetize via affiliates, then pursue official partnerships from a position of demonstrated traction.

**Do NOT** attempt automated purchasing - the legal risk far outweighs the potential reward.
