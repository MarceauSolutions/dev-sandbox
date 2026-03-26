# Agent 3: Legal & Customer Research Findings

## Ticket Aggregator MCP - Market Viability Analysis

**Research Date**: 2026-02-07
**Agent Focus**: Legal Compliance, ToS Analysis, Customer Segments, Risk Assessment

---

## Summary: Is This Legally Viable?

**CONDITIONAL YES** - with significant constraints

The Ticket Aggregator MCP concept is legally viable **ONLY** through specific pathways:

1. **Official API Partner Programs** - Legal, but requires business relationships
2. **Affiliate/Discovery APIs** - Legal, limited to search/display (no purchasing)
3. **Licensed Broker Integration** - Legal, requires state licenses in some jurisdictions

**NOT viable through**:
- Web scraping of ticketing platforms (ToS violations + CFAA risk after hiQ settlement)
- Automated purchasing without authorization (BOTS Act violation)
- Circumventing security measures (federal crime under BOTS Act)

---

## 1. BOTS Act Analysis

### What the BOTS Act Prohibits

The [Better Online Ticket Sales (BOTS) Act of 2016](https://www.congress.gov/bill/114th-congress/senate-bill/3183) makes it **illegal** to:

| Prohibited Action | Description |
|-------------------|-------------|
| **Circumvent security measures** | Bypass CAPTCHA, rate limits, or access controls on ticket seller websites |
| **Exceed ticket limits** | Use technology to purchase more tickets than posted limits allow |
| **Use fake identities** | Create multiple accounts with false information to evade limits |
| **Sell circumvented tickets** | Resell tickets obtained through the above violations |

### What's NOT Prohibited

- Manual ticket purchasing within posted limits
- Using official APIs with authorization
- Legitimate ticket resale (subject to state laws)
- Price comparison/aggregation of public listing data
- Affiliate linking to ticket sellers

### Penalties

| Penalty Type | Amount | Source |
|--------------|--------|--------|
| Base fine per violation | $16,000 | [FTC Enforcement](https://www.ftc.gov/business-guidance/blog/2025/04/bots-act-compliance-time-refresher) |
| Just In Time Tickets settlement | $11.2M | [DOJ 2021](https://www.justice.gov/archives/opa/pr/justice-department-and-ftc-announce-first-enforcement-actions-violations-better-online-ticket) |
| Concert Specials settlement | $16M | [DOJ 2021](https://www.justice.gov/archives/opa/pr/justice-department-and-ftc-announce-first-enforcement-actions-violations-better-online-ticket) |
| Cartisim Corp settlement | $4.4M | [DOJ 2021](https://www.justice.gov/archives/opa/pr/justice-department-and-ftc-announce-first-enforcement-actions-violations-better-online-ticket) |

### Enforcement History

- **2016**: BOTS Act enacted
- **2021**: [First-ever FTC enforcement actions](https://www.ftc.gov/news-events/news/press-releases/2021/01/ftc-brings-first-ever-cases-under-bots-act) - 3 brokers fined $31M+ total
- **2022-2024**: [Minimal enforcement](https://www.nysenate.gov/newsroom/in-the-news/2024/james-skoufis/high-prices-ravenous-bots-ticket-scalping-thrives-despite) despite ongoing bot activity
- **2025**: [Executive Order calls for stronger FTC enforcement](https://www.wiley.law/alert-Executive-Order-on-Ticket-Resale-Market-Calls-for-Greater-FTC-Enforcement)
- **2026**: [FTC sues Ticketmaster/Live Nation](https://www.ticketnews.com/2026/01/ticketmaster-asks-court-to-dismiss-ftc-lawsuit-arguing-bots-act-doesnt-apply-to-it/) - case pending

**Key Insight**: Enforcement has been rare but when it happens, penalties are severe. The 2025 Executive Order signals increased enforcement ahead.

---

## 2. Terms of Service Analysis

### Platform ToS Comparison

| Platform | Bot Prohibition | Scraping Prohibition | API Access | Affiliate Program |
|----------|-----------------|---------------------|------------|-------------------|
| **Ticketmaster** | Yes - explicit | Yes - explicit | Partner API only (closed) | Yes via Impact |
| **StubHub** | Yes - explicit | Yes - explicit | Limited/closed | Yes |
| **SeatGeek** | Yes - explicit | Yes - explicit | Discovery API (read-only) | Yes |
| **Vivid Seats** | Presumed Yes | Presumed Yes | Seller API available | Yes via Impact |
| **AXS** | Yes - explicit | Yes - explicit | Partner only | Limited |

### Ticketmaster ToS Key Provisions

From [Ticketmaster Terms of Use](https://legal.ticketmaster.com/terms-of-use/):

> - Prohibits use of "ticket bot technology to search for, reserve, or purchase tickets"
> - Prohibits "automated ticket purchasing software"
> - Prohibits "circumventing security measures"
> - Prohibits "computer programs, bots, robots, spiders, or other automated devices to retrieve, index, data mine"

### SeatGeek ToS Key Provisions

From [SeatGeek API Terms](https://seatgeek.com/api-terms):

> - "You cannot display ticket listings on behalf of other ticket sellers"
> - "You cannot sell, rent, redistribute, transfer, or sublicense the API"
> - Prohibits "automated ticket purchasing software on the SeatGeek online marketplace"
> - Prohibits "circumventing any security measure, access control system"

### StubHub ToS Key Provisions

From [StubHub Community Terms](https://stubhub.community/t5/Welcome-to-the-StubHub-Community/STUBHUB-BEYOND-TERMS-amp-CONDITIONS/td-p/82873):

> - "Use of automated devices or programs to redeem Benefits is prohibited"
> - "Access via a bot script or other brute force attack" results in IP ban

### Legal Ways to Automate Within ToS

| Approach | Platform Support | Capability |
|----------|-----------------|------------|
| Discovery API | Ticketmaster, SeatGeek | Search events, get metadata, link to purchase |
| Affiliate API | All major platforms | Get event data, earn commission on referrals |
| Partner API | Ticketmaster (closed) | Full transactional capability for approved partners |
| Seller API | Vivid Seats, some others | List/manage inventory for brokers |

---

## 3. Legal Pathways Analysis

### Ranked from Most to Least Legal

#### Tier 1: Fully Legal (Green Light)

| Pathway | Description | Pros | Cons |
|---------|-------------|------|------|
| **Affiliate/Discovery API Integration** | Use official read-only APIs to search/display events, earn commission | Fully compliant, established programs | No purchasing capability |
| **Official API Partnership** | Apply for Ticketmaster Partner API or similar | Full transactional access | Very difficult to get approved, requires existing relationship |
| **Licensed Broker Platform** | Build tool for licensed ticket brokers to manage inventory | Clear legal framework | Limited to broker operations, not consumer purchasing |

#### Tier 2: Conditionally Legal (Yellow Light)

| Pathway | Description | Pros | Cons |
|---------|-------------|------|------|
| **Price Comparison (No Scraping)** | Aggregate data from official APIs/feeds only | Legal if using authorized data | Limited data availability |
| **Enterprise Perks Integration** | Partner with platforms like [TicketsatWork](https://www.ticketsatwork.com/rewards/who-we-are) or [Abenity](https://abenity.com/) | B2B model with existing legal framework | Requires partnership negotiation |
| **Concierge Service Layer** | Human-assisted ticket purchasing with AI coordination | Humans do actual purchasing | Doesn't scale, high labor cost |

#### Tier 3: High Risk (Red Light)

| Pathway | Description | Legal Risk | Consequence |
|---------|-------------|------------|-------------|
| **Web Scraping** | Scrape ticket data from platforms | ToS violation, potential CFAA after hiQ settlement | IP bans, lawsuits, injunctions |
| **Automated Purchasing** | Bot-driven ticket buying | BOTS Act violation | Federal penalties, $16K+ per violation |
| **Security Circumvention** | Bypass CAPTCHA, rate limits | BOTS Act + potential CFAA | Federal prosecution, millions in fines |

### How Legitimate Aggregators Operate

Based on [Google's ticket aggregator model](https://www.vice.com/en/article/should-competitors-fear-googles-entry-into-concert-ticket-aggregation/):

1. **Official Partnerships**: Google partnered directly with Ticketmaster, Ticketfly, and AXS
2. **Metadata Only**: Display event info, dates, venues - link to purchase
3. **No Direct Transactions**: Users leave aggregator to buy tickets
4. **Affiliate Revenue**: Earn commission on referred purchases

---

## 4. Web Scraping Legal Analysis

### hiQ Labs v. LinkedIn Precedent

The [hiQ v. LinkedIn case](https://en.wikipedia.org/wiki/HiQ_Labs_v._LinkedIn) initially suggested public data scraping was legal. However:

- **2022 Settlement**: hiQ paid [$500,000 judgment](https://natlawreview.com/article/hiq-and-linkedin-reach-proposed-settlement-landmark-scraping-case), found liable for trespass and misappropriation
- **Post-Settlement Reality**: The "scraping is legal" narrative is now much weaker

### Current CFAA Interpretation (2024-2026)

From recent [legal analysis](https://www.scraperapi.com/web-scraping/is-web-scraping-legal/):

| Factor | Increases Legal Risk | Decreases Legal Risk |
|--------|---------------------|---------------------|
| Data Type | Login-required data | Publicly accessible data |
| Access Method | Bypassing security | Using public endpoints |
| After Notice | Continuing after C&D | Stopping after C&D |
| Impact | Server overload | Minimal requests |

### Ticketmaster Specific Litigation

From [Ticketmaster v. Prestige Entertainment](https://www.proskauer.com/blog/ticketmaster-reaches-settlement-with-ticket-broker-over-unauthorized-use-of-automated-bots):

- Ticketmaster can state CFAA claims if it sends C&D + blocks IPs
- [Ticketmaster actively blocks broker IPs](https://www.ticketnews.com/2011/07/ticketmaster-admits-blocking-ips-of-brokers-others/)
- Settlement required broker to stop all automated activity

**Conclusion**: Web scraping ticketing platforms carries significant legal risk, especially after receiving any notice of unauthorized access.

---

## 5. Customer Research

### Potential Customer Segments

#### Segment A: AI/Agent Developers (Primary Target)

| Characteristic | Detail |
|----------------|--------|
| **Who** | Developers building AI agents/assistants |
| **Pain Level** | 7/10 - Currently no programmatic ticket access for agents |
| **Current Solution** | N/A - manually direct users to websites |
| **Willingness to Pay** | $50-200/month for API access |
| **Market Size** | Growing rapidly with AI agent adoption |

From [Edgar Dunn research](https://www.edgardunn.com/articles/how-ai-agents-will-make-ticket-buying-smarter-and-faster):
> "Agentic commerce, powered by AI agents, is expected to bring profound changes to event ticketing, with AI agents automating queueing for ticket release, price comparison and purchasing."

#### Segment B: Enterprise Concierge/Perks Platforms

| Characteristic | Detail |
|----------------|--------|
| **Who** | Companies like [TicketsatWork](https://www.ticketsatwork.com/), [Abenity](https://abenity.com/), [Great Work Perks](https://www.greatworkperks.com/) |
| **Pain Level** | 5/10 - Already have partnerships but want better automation |
| **Current Solution** | Direct integrations with ticketing platforms |
| **Willingness to Pay** | $500-5000/month enterprise contracts |
| **Market Size** | 40,000+ corporate clients (TicketsatWork alone) |

From [TicketOS](https://ticketos.com/):
> "Consolidates ticketing from sources like Ticketmaster, Tickets.com (MLB), SeatGeek, and AXS into a single, user-friendly platform"

#### Segment C: Licensed Ticket Brokers

| Characteristic | Detail |
|----------------|--------|
| **Who** | Professional ticket resellers with state licenses |
| **Pain Level** | 8/10 - Manual processes, fragmented tools |
| **Current Solution** | Individual platform seller portals |
| **Willingness to Pay** | $200-1000/month for unified management |
| **Market Size** | ~2,500 licensed brokers (NY alone requires license) |

From [NY DOS](https://dos.ny.gov/ticket-reseller):
> "$25,000 bond required for ticket reseller license"

#### Segment D: Event Discovery Platforms

| Characteristic | Detail |
|----------------|--------|
| **Who** | Apps/websites that recommend events to users |
| **Pain Level** | 3/10 - Discovery APIs already exist |
| **Current Solution** | SeatGeek API, Ticketmaster Discovery API |
| **Willingness to Pay** | Commission-based (5-10% of referral value) |
| **Market Size** | Large but well-served |

### Customer Verdict

**Best Opportunity**: Enterprise Concierge platforms (Segment B)
- Existing legal frameworks
- High contract values
- Clear business model

**Future Opportunity**: AI Agent Developers (Segment A)
- Market not yet mature
- Regulatory uncertainty
- Could be massive once AI agents become mainstream

---

## 6. Risk Matrix

### Legal Risks

| Approach | BOTS Act Risk | CFAA Risk | ToS Risk | Overall |
|----------|---------------|-----------|----------|---------|
| Official API Partnership | None | None | None | **LOW** |
| Affiliate/Discovery API | None | None | None | **LOW** |
| Web Scraping (public) | Low-Medium | Medium-High | **HIGH** | **HIGH** |
| Automated Purchasing | **CRITICAL** | High | **HIGH** | **CRITICAL** |
| Security Circumvention | **CRITICAL** | **CRITICAL** | **CRITICAL** | **CRITICAL** |

### Reputational Risks

| Factor | Risk Level | Mitigation |
|--------|------------|------------|
| Association with scalping | High | Clear positioning as tool for authorized users only |
| Platform ban/blocking | High | Partner relationships, compliance focus |
| Legal action publicity | Medium | Compliance-first architecture |
| Consumer perception | Medium | Transparency about data sources |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| IP blocking by platforms | Very High | Service outage | Use official APIs only |
| API access revocation | Medium | Loss of data source | Multiple partnerships |
| ToS changes | Medium | Feature restrictions | Flexible architecture |
| Regulatory changes | Medium | Business model pivot | Compliance monitoring |

---

## 7. State Licensing Requirements

For any approach involving ticket brokerage:

| State | License Required | Bond | Notes |
|-------|------------------|------|-------|
| **New York** | Yes | $25,000 | [Required for businesses, individuals, and websites](https://dos.ny.gov/get-ticket-reseller-license) |
| **New Jersey** | Yes | $10,000 | Must have in-state office |
| **Massachusetts** | Yes | Varies | [Criminal background check required](https://www.mass.gov/ticket-resellers) |
| **Connecticut** | Yes | Varies | [State registration required](https://cga.ct.gov/PS97/rpt/olr/htm/97-R-0501.htm) |
| **Most other states** | No | N/A | Generally legal without license |

---

## 8. Recommendations

### Viable Business Models

1. **Affiliate Aggregator** (Lowest Risk)
   - Aggregate event data from official Discovery APIs
   - Monetize via affiliate commissions (5-10% per referral)
   - No direct purchasing capability
   - Legal and scalable

2. **Enterprise Perks API** (Medium Risk)
   - Partner with existing perks platforms (TicketOS, TicketsatWork)
   - Provide AI/automation layer on top of their authorized access
   - B2B model with clear legal relationships
   - Requires partnership development

3. **Licensed Broker Tools** (Medium Risk)
   - Build inventory management for licensed brokers
   - Use Vivid Seats Seller API and similar
   - Limited to resale market, not primary tickets
   - Requires broker relationship development

### Non-Viable Approaches (Avoid)

- **Direct Automated Purchasing**: Violates BOTS Act
- **Web Scraping**: High legal risk post-hiQ settlement
- **Security Circumvention**: Federal crime
- **Unauthorized API Access**: ToS violation + CFAA risk

---

## Legal Viability Score

### Score: 2.5 out of 5 Stars

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Core Use Case Legality | 2/5 | 35% | 0.70 |
| Available Legal Pathways | 3/5 | 25% | 0.75 |
| Enforcement Risk | 2/5 | 20% | 0.40 |
| Customer Segment Viability | 3/5 | 20% | 0.60 |
| **TOTAL** | | 100% | **2.45/5** |

### Rationale

**The core value proposition - AI agents programmatically purchasing tickets - is NOT legally viable** without official partnerships that are difficult to obtain. However:

- **Read-only aggregation** via Discovery/Affiliate APIs is fully legal
- **Enterprise B2B** approaches with existing perks platforms are viable
- **Broker tools** using authorized seller APIs are viable

The legal landscape is hostile to automated purchasing. The BOTS Act specifically targets this use case, platforms actively combat it, and enforcement is increasing. A ticket aggregator MCP would need to pivot from "purchase tickets" to "discover and refer tickets" to operate legally.

---

## Sources

### Primary Legal Sources
- [BOTS Act Text - Congress.gov](https://www.congress.gov/bill/114th-congress/senate-bill/3183)
- [FTC BOTS Act Enforcement Blog](https://www.ftc.gov/business-guidance/blog/2025/04/bots-act-compliance-time-refresher)
- [DOJ First BOTS Act Enforcement](https://www.justice.gov/archives/opa/pr/justice-department-and-ftc-announce-first-enforcement-actions-violations-better-online-ticket)
- [hiQ v. LinkedIn Settlement](https://natlawreview.com/article/hiq-and-linkedin-reach-proposed-settlement-landmark-scraping-case)

### Platform Terms & APIs
- [Ticketmaster Terms of Use](https://legal.ticketmaster.com/terms-of-use/)
- [Ticketmaster Developer Portal](https://developer.ticketmaster.com/)
- [SeatGeek API Terms](https://seatgeek.com/api-terms)
- [Vivid Seats Affiliate Program](https://www.vividseats.com/affiliates)

### Market Research
- [AI Agents Transform Event Ticketing - Edgar Dunn](https://www.edgardunn.com/articles/how-ai-agents-will-make-ticket-buying-smarter-and-faster)
- [TicketsatWork Corporate Benefits](https://www.ticketsatwork.com/rewards/who-we-are)
- [TicketOS Enterprise Platform](https://ticketos.com/)

### State Licensing
- [NY Ticket Reseller License](https://dos.ny.gov/get-ticket-reseller-license)
- [MA Ticket Resellers](https://www.mass.gov/ticket-resellers)
- [State Ticket Resale Laws](https://ticketflipping.com/resources/ticket-resale-laws-by-us-state/)

### Recent Litigation
- [FTC Sues Ticketmaster/Live Nation](https://www.ticketnews.com/2026/01/ticketmaster-asks-court-to-dismiss-ftc-lawsuit-arguing-bots-act-doesnt-apply-to-it/)
- [Ticketmaster v. Prestige Settlement](https://www.proskauer.com/blog/ticketmaster-reaches-settlement-with-ticket-broker-over-unauthorized-use-of-automated-bots)
