# Deployment Model Decision Tree
**Quick Guide: Which Deployment Model for Which Scenario?**

---

## Start Here

```
Is this a NEW customer or EXISTING product evolution?
│
├─ NEW CUSTOMER
│  │
│  └─ What's their technical sophistication?
│     │
│     ├─ LOW (small business, no IT team)
│     │  │
│     │  └─ How much customization do they need?
│     │     │
│     │     ├─ MINIMAL (standard templates work)
│     │     │  → Use: MULTI-TENANT
│     │     │     Price: $99/mo
│     │     │     Example: Email automation, basic social media
│     │     │
│     │     └─ MODERATE to HIGH (custom workflows/branding)
│     │        → Use: HYBRID (SaaS + configs)
│     │           Price: $299-999/mo
│     │           Example: Voice AI, lead generation with custom targeting
│     │
│     └─ HIGH (enterprise, IT team, budget >$2K/mo)
│        │
│        └─ Do they need data sovereignty or compliance?
│           │
│           ├─ YES (HIPAA, finance, government)
│           │  → Use: HYBRID + CUSTOMER-HOSTED AGENTS
│           │     OR: PER-CUSTOMER INSTANCE (if extreme isolation needed)
│           │     Price: $999-2,499/mo
│           │
│           └─ NO (just want premium/white-label)
│              → Use: HYBRID + WHITE-LABEL
│                 Price: $999/mo or agency tier $297-497/mo
│
└─ EXISTING PRODUCT EVOLUTION
   │
   └─ How many customers currently?
      │
      ├─ 1-10 customers
      │  → Start with: HYBRID (easiest to evolve)
      │     Migrate path: Multi-tenant core → add configs as needed
      │
      ├─ 10-50 customers
      │  → Evaluate current pain:
      │     - Too expensive? → Consolidate to HYBRID or MULTI-TENANT
      │     - Too rigid? → Add HYBRID config layer
      │     - Support nightmare? → Move away from SELF-HOSTED
      │
      └─ 50+ customers
         → Optimize for:
            - Cost efficiency → MULTI-TENANT (if low variance)
            - Flexibility → HYBRID (if high variance)
            - Never: PER-CUSTOMER (doesn't scale past 100)
```

---

## Quick Scenario Checklist

**Choose MULTI-TENANT if:**
- [ ] Product has <20% feature variance between customers
- [ ] Customers are okay with standardized experience
- [ ] Low budget ($99-299/mo target price)
- [ ] Volume play (want 1,000+ customers)
- [ ] Simple product (email, social media scheduling)

**Choose HYBRID if:**
- [ ] Product needs per-customer customization (50-80% variance)
- [ ] Want tiered pricing ($99 basic → $999 enterprise)
- [ ] Mix of simple + complex customers
- [ ] Voice AI, workflow automation, or lead generation
- [ ] Want to offer both SaaS ease + enterprise depth

**Choose PER-CUSTOMER INSTANCE if:**
- [ ] Customer requires dedicated infrastructure (compliance)
- [ ] Budget is $2,500+/mo per customer
- [ ] Only have 1-20 customers (not scaling to hundreds)
- [ ] Extreme customization (forked codebase per customer)
- [ ] SLA requires isolated failure domains

**Choose SELF-HOSTED if:**
- [ ] Customer has strict data residency laws (can't leave their country)
- [ ] Air-gapped environment (no internet access)
- [ ] Customer wants perpetual license (not subscription)
- [ ] You're building open-source business (support/services revenue)
- [ ] Government/defense contract

**Choose WHITE-LABEL if:**
- [ ] Selling to agencies (they resell to end customers)
- [ ] Customer brand perception is critical
- [ ] Want reseller channel (agencies mark up and keep difference)
- [ ] Franchise model (same process, different brands)

---

## Product-Specific Quick Answers

### Voice AI Phone Systems
**Recommended:** HYBRID
**Why:** Every restaurant has different menu/script, but core Twilio/Vapi logic is shared. Some need customer-hosted for compliance.
**Tier Structure:**
- Basic ($299): Core voice AI, standard scripts
- Pro ($999): Custom voice flows, branded caller ID
- Enterprise ($2,499): Customer-hosted agent in their VPC

---

### Lead Generation Automation
**Recommended:** MULTI-TENANT (basic tier) or HYBRID (pro tier)
**Why:** Scraping logic is standardized, but targeting criteria varies per customer.
**Tier Structure:**
- Basic ($99): Standard scraping (Google Places, Yelp), pre-built filters
- Pro ($299): Custom scraping rules, advanced filtering, ClickUp integration

---

### Social Media Automation
**Recommended:** HYBRID
**Why:** Scheduling engine is shared, but brand voice/content rules are highly custom.
**Tier Structure:**
- Basic ($99): Template posts, basic scheduling
- Pro ($299): AI content generation, brand voice training, multi-account

---

### Email Automation
**Recommended:** MULTI-TENANT
**Why:** Templates + merge tags sufficient for 90% of customers.
**Tier Structure:**
- Basic ($29): Standard templates, basic segmentation
- Pro ($99): Custom templates, advanced automation, A/B testing

---

### Workflow Automation (n8n)
**Recommended:** HYBRID (hard isolation with Docker per customer)
**Why:** Every customer has unique integrations/workflows. Security requires isolation.
**Tier Structure:**
- Basic ($199): Shared n8n instance, pre-built workflows
- Pro ($499): Dedicated n8n Docker container, custom workflows
- Enterprise ($1,499): Customer-hosted n8n, unlimited executions

---

## Cost Calculator (at 100 customers)

| Model | Infrastructure | DevOps | Total/Mo | Per-Customer |
|-------|----------------|--------|----------|--------------|
| Multi-Tenant | $202 | $500 | $702 | $7.02 |
| White Label | $352 | $800 | $1,152 | $11.52 |
| **Hybrid** | $800 | $400 | **$1,200** | **$12.00** |
| Per-Customer | $3,323 | $1,000 | $4,323 | $43.23 |
| Self-Hosted (support) | $0 | $5,200 | $5,200 | $52.00 |

**Break-even points:**
- **Multi-Tenant wins** if: <10% of customers need customization
- **Hybrid wins** if: 30-70% need customization (William's products)
- **Per-Customer wins** if: <20 customers AND each pays >$2,500/mo
- **Self-Hosted wins** if: Never (unless forced by customer/regulation)

---

## Migration Paths

### From Per-Customer → Hybrid
**Why migrate:** Costs too high as you scale (10+ customers)

**Steps:**
1. Deploy hybrid core platform
2. Migrate customers one-by-one (keep old instance running)
3. Export configs from per-customer instances → import to hybrid config layer
4. Run in parallel for 1 month (verify parity)
5. Shut down old per-customer instances
6. **Savings:** 72% cost reduction at 100 customers

---

### From Multi-Tenant → Hybrid
**Why migrate:** Customers demanding more customization

**Steps:**
1. Add configuration layer (DynamoDB + Vault)
2. Refactor workflows to read from configs (not hardcoded)
3. Build customer self-service portal for config editing
4. Migrate power users to "Pro" tier (uses configs)
5. Keep basic tier on pure multi-tenant
6. **Cost increase:** 71% ($702 → $1,200), but can charge 3x more ($99 → $299)

---

### From Self-Hosted → Hybrid
**Why migrate:** Support burden too high, customers want managed service

**Steps:**
1. Deploy hybrid platform (SaaS core)
2. Offer migration incentive (3 months free)
3. Data migration scripts (export from customer on-prem → import to SaaS)
4. Optional: Keep customer-hosted agents for compliance customers
5. Sunset on-prem licenses (1-year transition period)
6. **Win:** Predictable recurring revenue, 80% reduction in support tickets

---

## Red Flags (Anti-Patterns)

### 🚩 DON'T use Multi-Tenant if:
- Customers have wildly different requirements (>50% feature variance)
- Compliance requires physical data isolation
- Customization is your main selling point

### 🚩 DON'T use Per-Customer if:
- You want to scale beyond 100 customers
- Budget <$2K/mo per customer
- Customers don't care about dedicated infrastructure

### 🚩 DON'T use Self-Hosted if:
- Your customers are small businesses without IT teams
- You want predictable recurring revenue
- Support bandwidth is limited

### 🚩 DON'T use Hybrid if:
- Product is super simple (email templates, basic scheduling)
- All customers have identical needs
- Budget for infrastructure is <$1K/mo

---

## Final Answer for William

**For your AI automation suite:**

| Product | Model | Monthly Price | Target Customers |
|---------|-------|--------------|------------------|
| Voice AI | Hybrid | $299-2,499 | All tiers |
| Lead Gen | Multi-Tenant (basic), Hybrid (pro) | $99-299 | SMBs |
| Social Media | Hybrid | $99-499 | All tiers |
| Email | Multi-Tenant | $29-99 | All tiers |
| Workflows | Hybrid | $199-1,499 | Power users |

**Platform Strategy:**
1. Build hybrid core (supports all products)
2. Multi-tenant is a feature flag (disable configs for "Basic" tier)
3. Per-customer instances only for Enterprise tier (>$2,499/mo)
4. Self-hosted never offered (too much support burden)

**Expected Year 1:**
- 100 customers (50% Basic, 30% Pro, 15% Enterprise, 5% Custom)
- $496K ARR at 94% gross margin
- $1,200/mo infrastructure cost (scales to $3K at 1,000 customers)

---

**See Full Analysis:** `/Users/williammarceaujr./dev-sandbox/docs/END-CUSTOMER-DEPLOYMENT-STRATEGY.md`

**Last Updated:** 2026-01-21
