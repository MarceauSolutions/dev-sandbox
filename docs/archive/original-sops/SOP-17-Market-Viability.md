<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 17: Market Viability Analysis (Multi-Agent)

**When**: BEFORE investing significant development time in a new product/project idea

**Purpose**: Quickly assess market viability using parallel research agents to determine if an idea is worth pursuing, saving weeks of wasted development time on unviable products.

**Agent**: Claude Code (orchestrate 4 agents). Clawdbot (research agents). Ralph (4-agent execution via PRD).

**Key Principle**: Fail fast, fail cheap. Better to spend 2 hours researching than 2 weeks building something nobody wants.

**Prerequisites**:
- Product/service idea defined (can be vague)
- Target customer hypothesis (who would use this?)

**Directory Structure**:
```
projects/[project-name]/
├── market-analysis/
│   ├── ANALYSIS-PLAN.md           # Research questions for each agent
│   ├── AGENT-PROMPTS.txt          # Copy-paste prompts for 4 agents
│   ├── agent1-market-size/
│   │   └── FINDINGS.md
│   ├── agent2-competition/
│   │   └── FINDINGS.md
│   ├── agent3-customer-research/
│   │   └── FINDINGS.md
│   ├── agent4-monetization/
│   │   └── FINDINGS.md
│   └── consolidated/
│       ├── VIABILITY-SCORECARD.md
│       └── GO-NO-GO-DECISION.md
```

**The 4 Research Agents**:

| Agent | Focus | Key Questions |
|-------|-------|---------------|
| **Agent 1: Market Size** | TAM/SAM/SOM | How big is the market? Growing or shrinking? |
| **Agent 2: Competition** | Competitive landscape | Who else solves this? How do they monetize? |
| **Agent 3: Customer** | Buyer persona & pain | Would they pay? How much? Where do they hang out? |
| **Agent 4: Monetization** | Revenue model | B2B vs B2C? Subscription? One-time? Unit economics? |

**Steps**:

**Phase 1: Define the Research Questions**

Create `market-analysis/ANALYSIS-PLAN.md`:

```markdown
# Market Viability Analysis: [Product Name]

## Product Hypothesis
**What it is**: [1-2 sentence description]
**Who it's for**: [Target customer]
**Problem it solves**: [Pain point]
**How we'd make money**: [Initial monetization idea]

## Agent 1: Market Size Questions
1. What is the TAM (Total Addressable Market)?
2. What is the SAM (Serviceable Addressable Market)?
3. What is the realistic SOM (Serviceable Obtainable Market)?
4. Is the market growing, stable, or shrinking?
5. What are the key market trends?

## Agent 2: Competition Questions
1. Who are the direct competitors (same solution)?
2. Who are indirect competitors (different solution, same problem)?
3. What do competitors charge? What's their revenue model?
4. What's their market share / funding / size?
5. What's their main weakness we could exploit?
6. Is there a gap in the market?

## Agent 3: Customer Research Questions
1. Who exactly is the target customer (be specific)?
2. How painful is this problem (1-10)?
3. How do they currently solve it (workarounds)?
4. How much do they currently pay for alternatives?
5. Where do they congregate online (forums, social)?
6. What triggers them to search for a solution?

## Agent 4: Monetization Questions
1. What pricing model makes sense (subscription, usage, one-time)?
2. What price point would the market bear?
3. What are realistic customer acquisition costs?
4. What's the expected LTV (lifetime value)?
5. What's the break-even timeline?
6. Are there adjacent revenue opportunities (upsells)?
```

**Phase 2: Create Agent Prompts**

Create `market-analysis/AGENT-PROMPTS.txt`:

```
==================================================
AGENT 1: MARKET SIZE RESEARCH
==================================================

I'm Agent 1 in a MARKET VIABILITY analysis for [Product Name].

MY WORKSPACE: /absolute/path/to/market-analysis/agent1-market-size/
MY OUTPUT: Create FINDINGS.md

PRODUCT HYPOTHESIS:
[Paste product description here]

MY MISSION: Determine market size (TAM/SAM/SOM) and trends

RESEARCH QUESTIONS:
1. What is the TAM (Total Addressable Market)?
2. What is the SAM (Serviceable Addressable Market)?
3. What is the realistic SOM (Serviceable Obtainable Market)?
4. Is the market growing, stable, or shrinking? What's the CAGR?
5. What are key market trends affecting this space?

DELIVERABLE FORMAT (FINDINGS.md):
- **TAM**: $X billion [source]
- **SAM**: $X million [source]
- **SOM**: $X million (realistic year 1-3) [methodology]
- **Growth Rate**: X% CAGR [source]
- **Key Trends**: Bullet list with sources
- **Market Viability Score**: 1-5 stars with rationale

Use web search extensively. Cite all sources. Be skeptical of inflated market claims.
```

(Create similar prompts for Agents 2, 3, 4 with their specific questions)

**Phase 3: Launch Agents in Parallel**

1. Open 4 separate Claude instances
2. Copy-paste each agent's prompt
3. Let agents research independently (30-60 minutes each)
4. Agents should use web search, industry reports, competitor analysis

**Phase 4: Consolidate into Viability Scorecard**

After all agents complete, create `consolidated/VIABILITY-SCORECARD.md`:

```markdown
# Market Viability Scorecard: [Product Name]

## Summary Scores

| Factor | Score (1-5) | Weight | Weighted |
|--------|-------------|--------|----------|
| **Market Size** | ⭐⭐⭐⭐ | 25% | 1.0 |
| **Competition** | ⭐⭐⭐ | 25% | 0.75 |
| **Customer Pain** | ⭐⭐⭐⭐⭐ | 30% | 1.5 |
| **Monetization** | ⭐⭐⭐ | 20% | 0.6 |
| **TOTAL** | | 100% | **3.85/5** |

## Scoring Guide
- ⭐⭐⭐⭐⭐ (5): Exceptional - strong signal to proceed
- ⭐⭐⭐⭐ (4): Good - worth pursuing
- ⭐⭐⭐ (3): Acceptable - proceed with caution
- ⭐⭐ (2): Weak - significant concerns
- ⭐ (1): Poor - likely not viable

## Key Findings

### Market Size (Agent 1)
- TAM: $X
- SAM: $X
- SOM: $X (year 1-3 realistic)
- Growth: X% CAGR
- **Verdict**: [Summary]

### Competition (Agent 2)
- Direct competitors: [List]
- Indirect competitors: [List]
- Market gap: [Opportunity]
- **Verdict**: [Summary]

### Customer Pain (Agent 3)
- Target persona: [Description]
- Pain level: X/10
- Current solutions: [How they solve it now]
- Willingness to pay: [Evidence]
- **Verdict**: [Summary]

### Monetization (Agent 4)
- Recommended model: [Subscription/Usage/etc]
- Price point: $X
- CAC estimate: $X
- LTV estimate: $X
- Break-even: X months
- **Verdict**: [Summary]

## Red Flags
- [List any serious concerns discovered]

## Opportunities
- [List any positive surprises or blue ocean opportunities]
```

**Phase 5: Make Go/No-Go Decision**

Create `consolidated/GO-NO-GO-DECISION.md`:

```markdown
# Go/No-Go Decision: [Product Name]

## Overall Score: X.XX/5

## Decision: [GO / NO-GO / PIVOT]

## Rationale
[2-3 paragraphs explaining the decision]

## If GO:
- Recommended MVP scope: [What to build first]
- Target customer segment: [Who to focus on]
- Pricing strategy: [How to price]
- Go-to-market: [Where to find customers]

## If NO-GO:
- Primary dealbreaker: [What killed it]
- Could this pivot work?: [Alternative ideas]

## If PIVOT:
- Original idea: [What we started with]
- Pivoted idea: [What might work instead]
- Why pivot is more viable: [Rationale]

## Next Steps
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]
```

**Scoring Thresholds**:

| Score | Decision | Action |
|-------|----------|--------|
| **4.0-5.0** | GO | Proceed to SOP 0 (Project Kickoff) |
| **3.0-3.9** | CONDITIONAL GO | Address red flags first, then proceed |
| **2.0-2.9** | PIVOT | Research alternative approaches |
| **1.0-1.9** | NO-GO | Archive idea, move on |

**Time Investment**:
- Phase 1-2: 30 minutes (setup)
- Phase 3: 1-2 hours (parallel agent research)
- Phase 4-5: 30 minutes (consolidation)
- **Total: 2-3 hours** vs weeks of building the wrong thing

**When to Use vs Skip**:

✅ **Use SOP 17 when**:
- New product idea with uncertain market
- Entering unfamiliar market segment
- Significant development investment required (>1 week)
- B2C product (harder to validate than B2B)
- No existing customers or waitlist

❌ **Skip SOP 17 when**:
- Building for yourself (dog-fooding)
- Existing customers already requesting it
- Simple feature addition to existing product
- Internal tool (no revenue model needed)
- Quick experiment (<2 days to build)

**Integration with Development Pipeline**:

```
-1. MARKET ANALYSIS (SOP 17) - BEFORE committing to build
    └── 4-agent parallel research
    └── Viability scorecard
    └── Go/No-Go decision
    └── If NO-GO: Stop here, save weeks of work

0. KICKOFF (SOP 0) - Only if SOP 17 = GO
   └── Complete questionnaire
   └── App type decision

1. DESIGN → 2. DEVELOP → 3. TEST → 4. DEPLOY
```

**Example: Fitness Influencer AI Viability**

```
Agent 1 (Market Size):
- TAM: $21.4B creator economy
- SAM: $2.1B fitness influencer tools
- SOM: $50-100K (year 1 realistic for solopreneur)
- Growth: 15% CAGR
- Score: ⭐⭐⭐⭐ (4/5)

Agent 2 (Competition):
- Direct: Later, Buffer (social scheduling)
- Indirect: Canva, CapCut (manual tools)
- Gap: All-in-one for fitness niche
- Score: ⭐⭐⭐ (3/5) - crowded but fragmented

Agent 3 (Customer):
- Persona: 10K-100K follower fitness creators
- Pain: 8/10 (time-consuming editing)
- Current: Piecing together 5+ tools
- WTP: $20-50/month
- Score: ⭐⭐⭐⭐⭐ (5/5) - strong pain

Agent 4 (Monetization):
- Model: Freemium + Pro subscription
- Price: $29/month Pro tier
- CAC: $10-30 (content marketing)
- LTV: $200+ (6+ month retention)
- Score: ⭐⭐⭐⭐ (4/5)

TOTAL: 4.0/5 = GO
```

**References**:
- SOP 0: Project Kickoff (runs after GO decision)
- SOP 9: Architecture Exploration (technical approach)
- `docs/cost-benefit-templates.md` (financial projections)

