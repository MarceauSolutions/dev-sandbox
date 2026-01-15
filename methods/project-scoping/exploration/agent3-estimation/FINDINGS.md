# Agent 3 Findings: Project Estimation and Contract Structures

## Executive Summary

This research covers estimation frameworks and contract structures optimized for solopreneurs serving local small businesses (gyms, fitness studios, local services). The key finding is that **hybrid approaches outperform pure fixed-price or T&M models** for the Naples SMB market, and that **estimation accuracy improves dramatically with structured techniques** even for unknown features.

**Key Recommendations:**
1. Use Fixed Price for standard deliverables (websites, basic automations) with well-defined scope
2. Use Time & Materials (capped) for AI/automation projects with discovery phases
3. Apply 20-40% contingency buffers based on project complexity
4. Structure payments as 50% upfront / 25% milestone / 25% completion for most projects
5. Use three-point estimation (PERT) for unknown features

---

## 1. Fixed Price vs Time & Materials: Decision Framework

### Comparison Table

| Factor | Fixed Price | Time & Materials | Hybrid (Recommended) |
|--------|-------------|------------------|---------------------|
| **Client Budget Certainty** | High - client knows exact cost | Low - final cost unknown | Medium - cap provides ceiling |
| **Scope Clarity Required** | Very High | Low | Medium |
| **Your Risk** | High (eat overruns) | Low (bill all hours) | Medium (capped exposure) |
| **Client Risk** | Low | High (cost overruns) | Medium |
| **Profit Potential** | High (if efficient) | Moderate (hourly rate) | High (efficiency + flexibility) |
| **Suitable Project Types** | Template sites, known features | R&D, complex AI, ongoing work | Custom sites, AI automations |
| **Client Trust Required** | Low | High | Medium |
| **Administrative Burden** | Low (milestone billing) | High (time tracking) | Medium |

### Decision Framework for Marceau Solutions

```
START: New Project Inquiry
    |
    v
Q1: Is the scope 100% defined with zero ambiguity?
    |
    YES --> Q2: Have you built this exact thing 2+ times before?
    |           |
    |           YES --> FIXED PRICE (low risk, high margin)
    |           |
    |           NO --> FIXED PRICE + 25% CONTINGENCY
    |
    NO --> Q3: Is there a discovery/research component?
            |
            YES --> T&M with CAP (bill hours up to ceiling)
            |       OR
            |       PHASED: T&M Discovery + Fixed Price Build
            |
            NO --> Q4: Can scope be defined with 1-2 scoping sessions?
                    |
                    YES --> Paid Discovery ($500-1000) then Fixed Price
                    |
                    NO --> T&M with Weekly Cap + Monthly Review
```

### When to Use Each Model (Marceau Solutions Context)

**Use FIXED PRICE for:**
- WordPress/Squarespace template websites ($1,500-5,000)
- Standard contact forms, booking integrations
- Basic SEO setup packages
- Social media profile setup
- Email template design
- Repeat builds for similar businesses (e.g., 5th gym website)

**Use T&M (Capped) for:**
- Custom AI chatbots with unknown conversation flows
- API integrations with unfamiliar third-party systems
- Data migration from unknown legacy systems
- Ongoing maintenance/support retainers
- Complex automation workflows (Zapier/Make with 10+ steps)

**Use HYBRID (Phased) for:**
- Custom web applications
- AI automation projects with discovery needs
- Projects where client "doesn't know what they want"
- Anything involving machine learning training

### Hybrid Model Structures

**Option A: Paid Discovery + Fixed Build**
```
Phase 1: Discovery (T&M, capped at $500-1,000)
- Requirements gathering
- Technical feasibility
- Detailed scope document
- Fixed price quote for Phase 2

Phase 2: Build (Fixed Price based on discovery)
- Clear deliverables from Phase 1
- Change orders for anything outside scope
```

**Option B: Fixed Price with T&M Change Orders**
```
Base Project: Fixed Price for defined scope
Change Orders: T&M at $X/hour for additions
- Requires clear scope document
- Change order process defined upfront
```

**Option C: T&M with Cap (Not-to-Exceed)**
```
Billing: Hourly rate ($75-150/hour typical)
Cap: Maximum budget ceiling
Review: Weekly progress reports
- Client gets T&M flexibility
- You're protected if efficient
- Client protected by cap
```

---

## 2. Scope Creep Management

### Contractual Strategies

**Essential Contract Clauses:**

1. **Detailed Scope Section**
```
SCOPE OF WORK

Included:
- 5-page WordPress website (Home, About, Services, Contact, Blog)
- Contact form with email notification
- Mobile responsive design
- Basic SEO (meta tags, sitemap)
- 1 round of revisions per page

NOT Included (Change Order Required):
- Additional pages beyond 5
- E-commerce functionality
- Custom plugins or development
- Content writing (client provides copy)
- Photography (client provides images)
- Ongoing maintenance
- Additional revision rounds beyond 1
```

2. **Change Order Clause**
```
CHANGES TO SCOPE

Any work requested beyond the defined Scope of Work requires
a written Change Order signed by both parties BEFORE work begins.

Change Orders will be quoted at:
- Simple additions: $X flat fee
- Complex additions: $Y per hour (estimated hours provided)
- Rush additions (< 48 hours): +50% premium

No additional work will be performed without signed Change Order.
Client acknowledges that "small changes" may require significant
technical work and will be quoted accordingly.
```

3. **Revision Limits Clause**
```
REVISIONS

This project includes [X] rounds of revisions per deliverable.

A "round" is defined as:
- Consolidated feedback provided within 5 business days
- Changes that don't alter fundamental scope/direction
- Client must designate single point of contact for feedback

Additional revision rounds: $X per round
"Revision creep" (continuous small changes without formal round):
Will be consolidated and billed as a new round after 3 incidents.
```

4. **Assumptions Clause**
```
ASSUMPTIONS

This quote assumes:
- Client provides all content within 7 days of kickoff
- Client responds to questions within 2 business days
- Existing systems are documented and accessible
- No legacy data cleanup required
- Third-party APIs function as documented

If assumptions prove incorrect, scope will be re-evaluated
via Change Order process.
```

### Practical Strategies (Day-to-Day Management)

**Prevention Techniques:**

1. **The Parking Lot**
   - Keep a running document of "great ideas for Phase 2"
   - When client suggests additions: "Love it! Adding to the Phase 2 parking lot"
   - Review parking lot at project end for upsell opportunities

2. **The Scope Check**
   - Before starting any task, ask: "Is this in the original scope?"
   - If unclear, check scope document
   - If not listed, it's a change order

3. **Weekly Scope Review**
   - End of each week: compare planned vs actual work
   - Flag any scope expansion immediately
   - Don't let "small things" accumulate

4. **Client Education Upfront**
   - In kickoff meeting: explain change order process clearly
   - Frame it positively: "This protects both of us"
   - Give examples of what IS and ISN'T included

**Response Scripts for Scope Creep:**

*When client asks for "quick addition":*
> "I'd love to add that feature! Let me put together a quick quote - it looks like about [X hours / $Y]. I'll send over a change order for your signature and can knock it out [timeframe]. Does that work?"

*When client claims it was "always part of the project":*
> "Let me pull up the scope document we signed... [reference specific section]. I don't see that included here. No worries though - I can add it! Here's what it would take..."

*When client says "it's just a small change":*
> "I totally get it - seems small from the outside! The tricky part is [technical explanation]. For a proper implementation, we're looking at about [X hours]. Want me to quote it out?"

**The Scope Creep Escalation Ladder:**

```
Level 1: Small Request (< 30 min work)
- Decision: Include if goodwill value > time cost
- Track it: Note in project log
- Limit: 2-3 freebies per project max

Level 2: Medium Request (30 min - 2 hours)
- Decision: Always quote as change order
- Response: Send CO within 24 hours
- Don't start until signed

Level 3: Large Request (> 2 hours)
- Decision: Formal scope expansion
- May require project timeline adjustment
- Update contract/SOW if significant

Level 4: Project-Altering Request
- Decision: Pause project, renegotiate
- May need new contract entirely
- Example: "Actually, let's add e-commerce"
```

---

## 3. Contingency Buffer Recommendations

### Buffer Percentages by Project Type

| Project Category | Base Buffer | Risk Factors | Adjusted Buffer |
|-----------------|-------------|--------------|-----------------|
| **Template Website** (WordPress, Squarespace using themes) | 10% | - | 10-15% |
| **Custom Website** (custom design, basic functionality) | 20% | New design style: +5%, New platform: +10% | 20-35% |
| **Basic Automation** (Zapier/Make, < 5 steps) | 15% | New integration: +10% | 15-25% |
| **Complex Automation** (5+ steps, conditional logic) | 25% | AI component: +15%, Multiple APIs: +10% | 25-50% |
| **AI Chatbot** (basic Q&A, predefined flows) | 30% | Custom training: +20%, Integrations: +15% | 30-65% |
| **Custom AI/ML** (training, novel application) | 40-50% | Always treat as R&D | 50-100% |
| **Data Migration** (from unknown legacy system) | 35% | Poor documentation: +25% | 35-60% |
| **Third-Party Integration** (unfamiliar API) | 25% | No sandbox: +15%, Poor docs: +20% | 25-60% |

### Risk Multipliers (Cumulative)

| Risk Factor | Multiplier | Notes |
|-------------|------------|-------|
| First time building this type | +15-25% | Learning curve |
| Client is unclear on requirements | +20% | Discovery overhead |
| Multiple stakeholders/decision makers | +15% | Communication overhead |
| Tight deadline | +25% | No buffer for issues |
| Dependency on client-provided content | +10% | Delays waiting |
| Unknown third-party system | +20% | Discovery/debugging |
| Legacy system involved | +25% | Documentation rarely accurate |
| Client has no technical contact | +10% | You become IT support |

### Contingency Calculation Formula

```
Final Estimate = Base Estimate x (1 + Base Buffer) x Risk Multipliers

Example: Custom website for gym with unclear requirements
- Base estimate: 40 hours
- Base buffer: 20% (custom website)
- Risk: Unclear requirements (+20%)
- Risk: Multiple stakeholders (+15%)

Final = 40 x 1.20 x 1.20 x 1.15 = 66.24 hours

Price at $100/hour = $6,624
(vs naive $4,000 without buffers)
```

### Buffer Allocation Strategy

**How to use the buffer:**

1. **Don't Quote the Buffer Separately**
   - Wrong: "The project is $4,000 + $1,000 contingency"
   - Right: "The project is $5,000" (buffer baked in)
   - Why: Clients will try to negotiate away visible contingency

2. **Track Buffer Usage Internally**
   - Log actual hours against base estimate
   - Review after project: Did buffer get used?
   - Adjust future estimates based on patterns

3. **Buffer as Profit Margin**
   - If project runs smooth, buffer becomes profit
   - This rewards your growing expertise
   - Over time, efficiency + buffer = healthy margins

4. **When to Reveal Buffer Exists**
   - Only if major scope change requires re-estimation
   - "This is beyond what I'd planned for, even with contingency"
   - Never say "I have 20% buffer left"

---

## 4. Payment Structure Comparison

### Common Structures

| Structure | Cash Flow | Your Risk | Client Risk | Best For |
|-----------|-----------|-----------|-------------|----------|
| **100% Upfront** | Excellent | None | High | < $500 projects, retainers |
| **50/50** (start/end) | Good | Medium | Medium | Standard small projects |
| **50/25/25** (start/mid/end) | Good | Low | Low | $2,000-10,000 projects |
| **25/25/25/25** (4 milestones) | Fair | Very Low | Very Low | Large/long projects |
| **Net 30** (100% on completion) | Poor | Very High | None | Avoid for solopreneurs |
| **Monthly Retainer** | Excellent | Low | Medium | Ongoing relationships |

### Recommended Structure for Marceau Solutions

**Default Structure: 50/25/25**

```
Payment 1: 50% - Due before work begins
- Covers your opportunity cost
- Demonstrates client commitment
- Funds initial materials/tools

Payment 2: 25% - Due at midpoint milestone
- Usually: design approval or MVP demo
- Client must approve to trigger payment
- Creates natural check-in point

Payment 3: 25% - Due on delivery/launch
- Final payment before handoff
- "Go live" happens after payment clears
- Training/documentation included
```

**Structure by Project Size:**

| Project Value | Structure | Milestones |
|--------------|-----------|------------|
| Under $500 | 100% upfront | Single deliverable |
| $500-2,000 | 50/50 | Start / Completion |
| $2,000-5,000 | 50/25/25 | Start / Design Approval / Launch |
| $5,000-10,000 | 40/30/30 | Start / Design / Development Complete / Launch |
| $10,000+ | 30/25/25/20 | Start / Design / Dev / UAT / Launch |

### Payment Terms Best Practices

**Non-Negotiables:**
- Payment due dates are NET 0 (due on invoice)
- Work pauses if payment is > 7 days late
- Final deliverables not released until final payment
- No source files without final payment

**Late Payment Clause:**
```
PAYMENT TERMS

Invoices are due upon receipt.

Payments not received within 7 days of due date:
- Will incur 1.5% monthly interest (18% APR)
- Project work will be paused
- Project timeline will be adjusted accordingly

Final deliverables (source files, access credentials, launch)
will only be provided upon receipt of final payment.
```

**Payment Method Preferences:**
1. Credit card (immediate, automatic) - Offer 2-3% discount
2. ACH/bank transfer (1-3 days)
3. Check (avoid - slow, can bounce)
4. PayPal/Venmo (acceptable for < $1,000)

---

## 5. Estimating Unknown Features

### The Three-Point Estimation Method (PERT)

**Formula:**
```
Expected Time = (Optimistic + 4 × Most Likely + Pessimistic) / 6

Standard Deviation = (Pessimistic - Optimistic) / 6

Use Expected Time + (1 to 2 × SD) for quote
```

**Example: AI Chatbot Integration (Never Built Before)**

```
Optimistic (O): Everything works perfectly
- API docs are accurate
- No edge cases
- Client requirements clear
= 15 hours

Most Likely (M): Normal challenges
- Some API quirks
- Moderate debugging
- 1-2 requirement clarifications
= 25 hours

Pessimistic (P): Multiple issues
- API differs from docs
- Complex edge cases
- Client changes mind mid-build
= 50 hours

Expected = (15 + 4×25 + 50) / 6 = 27.5 hours
SD = (50 - 15) / 6 = 5.8 hours

Conservative quote: 27.5 + (2 × 5.8) = 39 hours
At $100/hour = $3,900
```

### Research-Based Estimation for Unknown Features

**Step 1: Decompose the Unknown**
Break the unknown feature into smaller known components:

```
Unknown: "AI-powered appointment scheduler"

Decomposed:
- Calendar UI (known - 4 hours)
- Database for appointments (known - 3 hours)
- API connection to client's system (unknown - ???)
- AI component for suggestions (unknown - ???)
- Notification system (known - 2 hours)

Known total: 9 hours
Unknown items: 2 features to research
```

**Step 2: Find Comparable Projects**
- Search GitHub for similar implementations
- Check forum discussions (Reddit, Stack Overflow)
- Look at SaaS products that solve this - how long did they take?
- Ask AI assistants for complexity assessment

**Step 3: Time-Box Research**
```
Research Protocol:
1. Spend 1-2 hours researching before estimating
2. Find 2-3 tutorials/examples
3. Attempt simplest version (spike)
4. If spike takes > 2 hours, double your estimate

Charge for research time (include in quote or discovery phase)
```

**Step 4: Analogous Estimation**
```
Unknown Feature: Real-time sync between systems

Find Analogy: Previously built API integration
- That integration took: 8 hours
- New feature is: ~2x more complex (real-time adds difficulty)
- Estimate: 16 hours + 25% uncertainty buffer = 20 hours
```

### The "Unknown Unknown" Protocol

For features where you truly have no reference point:

1. **Mandatory Discovery Phase**
   - Quote 4-8 hours of paid discovery
   - Deliver: Feasibility assessment, architecture plan, refined estimate
   - Client pays for discovery regardless of build decision

2. **T&M with Weekly Cap**
   - Propose Time & Materials billing
   - Weekly cap of [X hours/$Y]
   - Weekly progress report with burn rate
   - Client can stop at any week

3. **Prototype Pricing**
   - Quote a prototype/MVP version
   - Reduced scope, proof of concept
   - Full feature quote after prototype complete

**Red Flags: When to Increase Unknown Buffer**

| Red Flag | Buffer Increase | Action |
|----------|----------------|--------|
| No documentation for third-party system | +50% | Ask client for contacts at provider |
| Client says "it should be easy" | +30% | Probe deeply, educate on complexity |
| "We'll figure it out as we go" | +40% | Insist on discovery phase |
| Timeline is "ASAP" | +50% | Add rush premium separately |
| Client comparing to consumer products | +30% | "Instagram took 100 engineers" |
| Decision by committee | +25% | Identify single point of contact |

---

## 6. Practical Toolset for Marceau Solutions

### Estimation Checklist

Before quoting any project:

```markdown
## Project Estimation Checklist

### Scope Clarity
- [ ] Written scope document exists
- [ ] Client approved scope in writing
- [ ] "Not included" section defined
- [ ] Success criteria defined
- [ ] Revision limits specified

### Complexity Assessment
- [ ] All features classified as Known/Unknown
- [ ] Unknown features researched (1-2 hours)
- [ ] Third-party dependencies identified
- [ ] Client-provided content identified
- [ ] Legacy systems assessed

### Buffer Calculation
- [ ] Base buffer applied (10-50% by type)
- [ ] Risk multipliers applied
- [ ] Three-point estimation for unknowns
- [ ] Timeline buffer added (not just hours)

### Pricing Verification
- [ ] Hourly rate meets minimum ($100/hour target)
- [ ] Project minimum met ($1,500 for websites)
- [ ] Payment structure defined
- [ ] Late payment terms included
```

### Quick Reference Card

```
ESTIMATION QUICK REFERENCE

Standard Buffers:
- Template site: 10-15%
- Custom site: 20-35%
- Basic automation: 15-25%
- Complex automation: 25-50%
- AI features: 40-100%

Payment Structure:
- < $500: 100% upfront
- $500-2K: 50/50
- $2K-10K: 50/25/25
- > $10K: 4 milestones

Scope Creep Response:
1. "Let me quote that for you"
2. Send change order in writing
3. Don't start until signed

Unknown Feature Protocol:
1. Decompose into known parts
2. Research 1-2 hours
3. Use PERT: (O + 4M + P) / 6
4. Add 1-2 standard deviations
5. Or: Paid discovery phase
```

---

## 7. Scoring and Assessment

### Applicability to Marceau Solutions

| Framework Component | Applicability Score | Notes |
|--------------------|---------------------|-------|
| Fixed vs T&M Decision Framework | 5/5 | Directly applicable to all project types |
| Scope Creep Management | 5/5 | Critical for local SMB clients |
| Contingency Buffers | 5/5 | Essential for profitability |
| Payment Structures | 5/5 | Cash flow critical for solopreneur |
| Unknown Feature Estimation | 4/5 | Very useful for AI/automation work |

**Overall Applicability: 4.8/5**

### Actionability

| Recommendation | Implementation Effort | Impact |
|----------------|----------------------|--------|
| Create scope template | 2 hours | High - use on every project |
| Add change order clause | 30 min | High - immediate protection |
| Implement 50/25/25 payments | 0 hours | High - just enforce |
| Create estimation checklist | 1 hour | Medium - improves consistency |
| Practice scope creep scripts | Ongoing | High - skill development |

**Overall Actionability: 4.5/5** - Most recommendations can be implemented immediately

### Evidence Quality

| Topic | Evidence Base | Confidence |
|-------|--------------|------------|
| Fixed vs T&M comparison | Industry standard, extensive literature | High |
| Scope creep management | Widespread practitioner consensus | High |
| Contingency percentages | Varies by source, numbers are guidelines | Medium |
| Payment structures | Standard industry practice | High |
| PERT estimation | Proven methodology, NASA/engineering origin | High |

**Overall Evidence Quality: 4/5** - Strong foundations, some variability in specific numbers

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Client rejects 50% upfront | Medium | Medium | Offer credit card payment, explain policy |
| Underestimating unknown features | High | High | Always use PERT + buffer; discovery phases |
| Scope creep despite clauses | Medium | Medium | Enforce consistently, track freebies |
| Client disputes change orders | Low | Medium | Document everything in writing |
| Buffer erodes profit margin | Low | Low | Track actuals, adjust future estimates |

---

## 8. Sources and References

### Industry Standards Referenced

1. **Software Estimation: Demystifying the Black Art** - Steve McConnell
   - PERT methodology
   - Cone of Uncertainty concept
   - Buffer calculation approaches

2. **Agile Estimating and Planning** - Mike Cohn
   - Three-point estimation
   - Velocity-based estimation for known work

3. **Project Management Institute (PMI)** - PMBOK Guide
   - Industry-standard contingency guidelines
   - Risk management frameworks

4. **Freelancers Union Survey Data**
   - Payment structure best practices
   - Non-payment statistics and protections

5. **Stack Overflow Developer Survey**
   - Rate benchmarks
   - Project complexity assessments

### Practitioner Sources

- Brennan Dunn (Double Your Freelancing)
- Paul Jarvis (Company of One)
- Jonathan Stark (Hourly Billing Is Nuts)
- Freelance community discussions (Reddit r/freelance, Hacker News)

### Note on Specific Numbers

Contingency percentages and buffer recommendations are based on:
- Aggregated industry guidance
- Practitioner experience
- Risk assessment frameworks

Actual numbers should be calibrated based on Marceau Solutions' project history over time. Track actual vs estimated hours to refine these guidelines.

---

## 9. Summary Recommendations for Marceau Solutions

### Immediate Actions (This Week)

1. **Create contract template** with scope, change order, and payment clauses
2. **Set 50/25/25 as default payment structure**
3. **Implement "not included" section** in all scope documents
4. **Practice scope creep response scripts**

### Short-Term (This Month)

1. **Build estimation checklist** and use on next 3 projects
2. **Create quick reference card** for client calls
3. **Track actual vs estimated hours** for buffer calibration
4. **Define paid discovery offering** for complex projects

### Long-Term (Quarter)

1. **Review buffer accuracy** after 5-10 projects
2. **Adjust contingencies** based on actual data
3. **Build project type templates** with pre-calculated estimates
4. **Create client education materials** about process

---

*Agent 3 Research Complete*

*Workspace: /Users/williammarceaujr./dev-sandbox/methods/project-scoping/exploration/agent3-estimation/*
*Date: 2026-01-15*
