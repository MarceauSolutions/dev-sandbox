# Project Scoping Method - Final Recommendation

*Date: 2026-01-15*
*Source: 4-Agent Multi-Agent Exploration (SOP 9)*
*Target: Marceau Solutions (Naples, FL - Solopreneur Web/AI Agency)*

---

## Executive Recommendation

**Implement a Hybrid Value-Based Scoping Framework** combining:
1. **3-Tier Fixed Pricing** for standard web projects
2. **T&M with Cap** for AI/automation projects with discovery needs
3. **BANT+ Qualification** to filter leads before proposal
4. **ClickUp + HoneyBook** as the tooling backbone

**Expected Outcomes**:
- 80% reduction in bad-fit client engagements
- 20% improvement in estimation accuracy
- 2-3 hours saved per proposal
- Consistent pricing that builds market positioning

---

## The Complete Framework

### Phase 1: Lead Qualification (Before Any Proposal)

#### Step 1.1: Pre-Call Intake Form

Capture via HoneyBook or ClickUp Form:

| Question | Purpose | Auto-Disqualify If |
|----------|---------|-------------------|
| What's your business name and website URL? | Research prep | - |
| What problem are you hoping to solve? | Qualify need | "Just want it to look better" |
| What's your budget range? | Budget fit | Under $1,500 |
| When do you need this completed? | Timeline reality | "ASAP" with no reason |
| Who makes the final decision? | Authority check | - |

#### Step 1.2: BANT+ Scoring (During Discovery Call)

Score each dimension 1-5:

| Dimension | 1 (Disqualify) | 3 (Caution) | 5 (Ideal) |
|-----------|----------------|-------------|-----------|
| **Budget** | Won't discuss, price shopper | Has range but below yours | Clear budget matching your rates |
| **Authority** | Not decision-maker | Needs to consult partner | Sole decision-maker |
| **Need** | Vanity/"just because" | Vague business goal | Clear problem + success metrics |
| **Timeline** | "ASAP" or no deadline | Reasonable but tight | Realistic with buffer |
| **Fit** | Red flags in past contractors | Some concerns | Values expertise, clear communicator |

**Minimum Score to Proceed**: 15/25

---

### Phase 2: Project Classification

#### Step 2.1: Tier Classification

| Tier | Type | Indicators | Price Range |
|------|------|------------|-------------|
| **Starter** | Landing/Micro | 1-3 pages, template, no CMS | $1,500-2,500 |
| **Standard** | Small Business | 4-7 pages, simple CMS, forms | $3,500-5,500 |
| **Professional** | Full Website | 8-15 pages, full CMS, integrations | $6,000-10,000 |
| **Enterprise** | Custom Platform | 15+ pages, custom features, API | $10,000+ |

#### Step 2.2: Complexity Multipliers

Apply if present:

| Factor | Multiplier | Examples |
|--------|------------|----------|
| E-commerce | 1.5-2x | Shopping cart, payments |
| Membership/Login | 1.3x | User accounts, gated content |
| Third-party API | 1.2x per API | CRM, booking, payments |
| Custom animations | 1.2x | Complex motion design |
| Rush (<2 weeks) | 1.5x | Expedited delivery |
| Content creation | 1.2-1.5x | Copywriting, photography |
| AI/Automation | 1.5-2x | Chatbots, workflows |

#### Step 2.3: Pricing Model Selection

```
Is scope 100% defined?
├── YES → Have you built this 2+ times?
│         ├── YES → FIXED PRICE
│         └── NO  → FIXED PRICE + 25% buffer
└── NO  → Is there discovery/research needed?
          ├── YES → T&M with CAP or Phased (T&M Discovery → Fixed Build)
          └── NO  → Paid Discovery ($500-1,000) then Fixed Price
```

---

### Phase 3: Estimation

#### Step 3.1: Base Estimate + Contingency

| Project Type | Base Buffer | Risk Multipliers |
|--------------|-------------|------------------|
| Template website | 10-15% | - |
| Custom website | 20-25% | New design +5%, new platform +10% |
| Basic automation | 15-20% | New integration +10% |
| Complex automation | 25-35% | AI +15%, multiple APIs +10% |
| AI/ML features | 40-50% | Custom training +20%, unknowns +25% |

**Formula**: `Final Hours = Base Estimate × (1 + Buffer) × Risk Multipliers`

#### Step 3.2: Unknown Feature Estimation (PERT)

For features never built before:

```
Expected Time = (Optimistic + 4 × Most Likely + Pessimistic) / 6
Quote = Expected Time + (2 × Standard Deviation)
```

**Example**: AI Chatbot (unknown)
- Optimistic: 15 hrs, Most Likely: 25 hrs, Pessimistic: 50 hrs
- Expected: 27.5 hrs, SD: 5.8 hrs
- Quote: 39 hrs @ $100/hr = $3,900

---

### Phase 4: Proposal & Contract

#### Step 4.1: 3-Tier Proposal Structure

Always present three options:

| Option | Content | Pricing Strategy |
|--------|---------|------------------|
| **Essential** | Must-haves only | Base price |
| **Recommended** | Essential + value features | Base + 40% |
| **Premium** | Everything + advanced | Base + 100% |

#### Step 4.2: Required Contract Clauses

1. **Detailed Scope Section**
   - Explicit "Included" list
   - Explicit "Not Included" list (content, photography, SEO, etc.)

2. **Change Order Clause**
   ```
   Any work beyond defined scope requires written Change Order
   BEFORE work begins. Changes billed at $100/hour.
   ```

3. **Revision Limits**
   ```
   Includes [X] rounds of revisions. Additional rounds: $X each.
   ```

4. **Assumptions Clause**
   ```
   Quote assumes: client provides content in 7 days,
   responds within 2 business days, third-party APIs work as documented.
   ```

#### Step 4.3: Payment Structure

| Project Value | Structure | Milestones |
|---------------|-----------|------------|
| Under $500 | 100% upfront | - |
| $500-2,000 | 50/50 | Start / Complete |
| **$2,000-10,000** | **50/25/25** (Default) | Start / Design / Launch |
| $10,000+ | 30/25/25/20 | Start / Design / Dev / Launch |

**Non-Negotiables**:
- 50% due before work starts
- Final deliverables after final payment
- Work pauses if payment >7 days late

---

### Phase 5: Tooling Setup

#### Recommended Stack: $19/month

| Tool | Function | Cost |
|------|----------|------|
| **ClickUp** (existing) | Project management, CRM pipeline | $0 |
| **HoneyBook Starter** | Proposals, contracts, invoicing, scheduling | $19/mo |
| **Zapier Free** | Integration | $0 |

#### Integration Flow

```
1. Lead fills HoneyBook inquiry form
2. Zapier creates ClickUp task in "Sales Pipeline"
3. Discovery call scheduled via HoneyBook
4. Proposal sent via HoneyBook (with e-sign)
5. On signature: Zapier creates ClickUp project
6. HoneyBook auto-sends 50% invoice
```

#### ClickUp Sales Pipeline Statuses

`Lead → Qualified → Proposal Sent → Negotiation → Won → Lost`

---

## Implementation Checklist

### Week 1: Foundation

- [ ] Create 3-tier pricing packages (use pricing table above)
- [ ] Set up HoneyBook account ($19/mo)
- [ ] Create proposal template in HoneyBook
- [ ] Create contract template with required clauses
- [ ] Set up ClickUp Sales Pipeline space

### Week 2: Integration

- [ ] Create HoneyBook intake form with qualification questions
- [ ] Set up Zapier: HoneyBook → ClickUp task
- [ ] Set up Zapier: Proposal signed → ClickUp project
- [ ] Create discovery call script (from Agent 2)
- [ ] Create estimation checklist

### Week 3: Validation

- [ ] Apply framework to 3 past projects (retrospective)
- [ ] Apply to 2 hypothetical inquiries
- [ ] Adjust pricing/buffers based on validation
- [ ] Document in VALIDATION-LOG.md

### Ongoing

- [ ] Track actual vs estimated hours (every project)
- [ ] Review qualification → outcome correlation
- [ ] Adjust buffers based on data (quarterly)

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Qualification accuracy | 80% of qualified leads close | Won/Qualified ratio |
| Estimation accuracy | Within 20% of actual hours | Estimated vs actual tracking |
| Scope creep incidents | <20% of projects | Change orders as % of projects |
| Proposal-to-close rate | 40%+ | Proposals sent vs won |
| Time saved per proposal | 2+ hours | Before/after comparison |

---

## Pricing Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                 MARCEAU SOLUTIONS PRICING                   │
├─────────────────────────────────────────────────────────────┤
│ STARTER        │ $1,500-2,500  │ 1-3 pages, template       │
│ STANDARD       │ $3,500-5,500  │ 4-7 pages, CMS            │
│ PROFESSIONAL   │ $6,000-10,000 │ 8-15 pages, integrations  │
│ ENTERPRISE     │ $10,000+      │ 15+ pages, custom         │
├─────────────────────────────────────────────────────────────┤
│ MULTIPLIERS: E-commerce 1.5-2x │ AI 1.5-2x │ Rush 1.5x     │
├─────────────────────────────────────────────────────────────┤
│ HOURLY: $100/hr dev │ $125/hr consulting │ $75/hr maint   │
├─────────────────────────────────────────────────────────────┤
│ MAINTENANCE: $175/month default (hosting + 1-2 hrs)        │
├─────────────────────────────────────────────────────────────┤
│ PAYMENTS: 50% upfront │ 25% at design │ 25% at launch     │
├─────────────────────────────────────────────────────────────┤
│ BUFFERS: Template 15% │ Custom 25% │ AI 50%               │
└─────────────────────────────────────────────────────────────┘
```

---

## When to Use This Method

**Use for**:
- Any new web design/development project inquiry
- AI/automation project scoping
- Consulting engagement pricing

**Modify for**:
- Existing client add-on work (skip qualification)
- Rush projects (add 1.5x multiplier)
- Retainer clients (monthly rate negotiation)

**Skip for**:
- Existing maintenance clients (use hourly)
- Small tasks under $500 (quick quote)

---

## References

- Agent 1 Findings: `agent1-pricing/FINDINGS.md`
- Agent 2 Findings: `agent2-intake/FINDINGS.md`
- Agent 3 Findings: `agent3-estimation/FINDINGS.md`
- Agent 4 Findings: `agent4-tooling/FINDINGS.md`
- Comparison Matrix: `consolidated/COMPARISON-MATRIX.md`

---

*Recommendation Complete - Ready for Implementation*
*Next: Create CLASSIFICATION-MATRIX.md and INTAKE-QUESTIONNAIRE.md*
