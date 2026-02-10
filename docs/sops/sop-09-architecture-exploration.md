# SOP 9: Multi-Agent Architecture Exploration

**When**: Before starting implementation of a new project with multiple possible approaches

**Purpose**: Research and evaluate 3-4 different implementation strategies in parallel to choose the optimal approach BEFORE writing code

**Agent**: Claude Code (orchestrate, interactive). Clawdbot (research agents). Ralph (complex 4-agent analysis).

**Key Distinction**:
- **SOP 9 (Exploration)**: BEFORE implementation - "Which approach should we use?"
- **SOP 2 (Testing)**: AFTER implementation - "Does our implementation handle edge cases?"

**Directory Structure**:
```
projects/[project-name]/
├── exploration/                    # PRE-implementation research
│   ├── EXPLORATION-PLAN.md         # Research questions for each agent
│   ├── AGENT-PROMPTS.txt           # Copy-paste prompts for 4 agents
│   ├── agent1-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent2-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent3-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent4-[approach-name]/
│   │   └── FINDINGS.md
│   └── consolidated-results/
│       ├── COMPARISON-MATRIX.md    # Side-by-side comparison
│       └── RECOMMENDATION.md        # Chosen approach + rationale
│
├── directives/                     # Created AFTER choosing approach
└── src/                            # Implementation starts AFTER exploration
```

**Steps**:

**1. Identify Multiple Approaches**

Define 3-4 possible ways to build the project:

Example (Uber/Lyft Price Comparison):
- Approach 1: Official APIs
- Approach 2: Web Scraping
- Approach 3: Third-Party Aggregator APIs
- Approach 4: Mobile App Integration

**2. Define Evaluation Criteria** (`exploration/EXPLORATION-PLAN.md`):

```markdown
## Evaluation Criteria
- **Feasibility**: Can this actually be built?
- **Legal**: Does this violate Terms of Service or laws?
- **Cost**: What are the ongoing API/service costs?
- **Reliability**: How often will this break?
- **Maintenance**: How much ongoing work is required?
- **User Experience**: How fast/accurate are the results?
- **Scalability**: Can this handle growth?

## Scoring System
- 5 stars: Excellent
- 4 stars: Good
- 3 stars: Acceptable
- 2 stars: Poor
- 1 star: Unusable
```

**3. Create Agent Prompts** (`exploration/AGENT-PROMPTS.txt`):

```
==================================================
AGENT 1: [APPROACH NAME] RESEARCH
==================================================

I'm Agent 1 in a multi-agent EXPLORATION effort for [Project Name].

MY WORKSPACE: /Users/williammarceaujr./dev-sandbox/projects/[project]/exploration/agent1-[approach]/

MY MISSION: Research [Approach 1 Name]

RESEARCH QUESTIONS:
1. [Specific question about feasibility]
2. [Specific question about cost]
3. [Specific question about legal compliance]
4. [Specific question about reliability]
5. [Specific question about maintenance]

DELIVERABLE: Create FINDINGS.md with:
- **Summary** (feasible? yes/no)
- **Technical Details** (how it works)
- **Costs** (setup, ongoing, per-use)
- **Pros** (3-5 advantages)
- **Cons** (3-5 disadvantages)
- **Risks** (legal, technical, business)
- **Code Example** (if feasible - proof of concept)
- **RECOMMENDATION** (1-5 stars with rationale)

Use web search, documentation review, technical analysis, and proof-of-concept code.

DO NOT implement the full solution - only research and create small proof-of-concept if helpful.
```

Create similar prompts for Agents 2, 3, 4 (different approaches).

**4. Launch 4 Agents in Parallel**:
- Open 4 separate Claude instances (browser tabs or windows)
- Copy-paste each agent prompt into a separate instance
- Let agents research independently (1-2 hours each)
- Agents should use web search, read documentation, write proof-of-concept code

**5. Consolidate Findings** (`exploration/consolidated-results/COMPARISON-MATRIX.md`):

```markdown
# Approach Comparison Matrix

| Criterion | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|-----------|------------|------------|------------|------------|
| **Feasibility** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Legal** | ✅ Allowed | ❌ Violation | ✅ Allowed | ⚠️ Gray area |
| **Cost** | $0.10/call | Free | $50/mo | Free |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Maintenance** | ⭐⭐⭐⭐⭐ Low | ⭐⭐ High | ⭐⭐⭐⭐ Low | ⭐⭐⭐ Med |
| **Speed** | <1s | 3-5s | <2s | 2-3s |
| **UX** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **TOTAL SCORE** | 23/25 | 9/25 | 20/25 | 15/25 |

## Key Findings

**Approach 1** (Highest Score):
- Pros: [List from agent findings]
- Cons: [List from agent findings]
- Risk: [Main risk identified]

**Approach 2** (Lowest Score):
- Fatal Flaw: [Why this won't work]

[etc...]
```

**6. Make Recommendation** (`exploration/consolidated-results/RECOMMENDATION.md`):

```markdown
# Recommended Approach: [Chosen Approach]

## Decision
Use **[Approach Name]** for the following reasons:

**Pros**:
- ✅ [Key advantage 1]
- ✅ [Key advantage 2]
- ✅ [Key advantage 3]

**Cons**:
- ❌ [Known limitation 1]
- ❌ [Known limitation 2]

**Cost Analysis**:
- [Detailed cost breakdown]
- [ROI or sustainability plan]

**Risk Mitigation**:
- [How we'll handle main risk 1]
- [How we'll handle main risk 2]

**Alternative Considered**: [Second best approach]
- Why not chosen: [Specific reason]
- When we'd reconsider: [Conditions that would change decision]

## Next Steps
1. [First implementation task]
2. [Second implementation task]
3. Create directive: `directives/[project].md`
4. Implement using SOP 1

## Architecture Decision
**Tier 2 (Project-Specific)**:
- `projects/[name]/src/[main-script].py`
- `projects/[name]/src/[helper].py`

**Shared Utilities** (if needed):
- `execution/[utility].py` (if other projects use it)
```

**7. Proceed to Implementation** (SOP 1):
- Now implement the CHOSEN approach
- Create directive based on recommendation
- Build with confidence (research already done)
- Skip approaches that were ruled out

**When to Use**:

✅ **Use SOP 9 when**:
- Multiple valid approaches exist (3+ ways to solve it)
- Significant cost, legal, or technical unknowns
- High stakes (don't want to rebuild from scratch)
- New technology domain (unfamiliar territory)
- Examples: API vs Scraping vs Third-party, SQL vs NoSQL, Cloud provider selection

❌ **Skip SOP 9 when**:
- Obvious approach (only one way to do it)
- Low stakes (quick experiment, easy to pivot)
- Familiar domain (you know the best approach already)
- Simple project with clear requirements

**Benefits**:

1. **Avoid Costly Mistakes**: Don't spend 2 weeks implementing wrong approach
2. **Evidence-Based Decisions**: Compare approaches with data, not guessing
3. **Uncover Hidden Issues Early**: Discover ToS violations, API limits, costs BEFORE coding
4. **Parallel Research = Faster**: 4 agents in parallel (1-2 hours) vs sequential (4-8 hours)
5. **Documentation for Future**: Explains WHY you chose this approach for future reference

**Integration with Development Pipeline**:

```
0. KICKOFF (SOP 0) - ALWAYS FIRST
   └── Complete questionnaire (19 questions)
   └── App type decision, cost-benefit analysis
   └── Template vs clean slate decision

0.5 EXPLORE (SOP 9) - IF multiple approaches possible
   └── Multi-agent architecture exploration
   └── Choose best approach

1. DESIGN (Directive)
   └── Based on chosen approach

2. DEVELOP (SOP 1)
   └── Implement chosen approach

3. TEST (SOP 2)
   └── Test implementation for edge cases

4. DEPLOY (SOP 3)

5. VERIFY (Scenario 4)
```

**Example Timeline**:
```
Day 1-2: Architecture Exploration (SOP 9) - 4 agents research in parallel
Day 3: Consolidate findings, choose approach
Day 4: Create directive based on chosen approach
Day 5-9: Implement (SOP 1)
Day 10-12: Multi-Agent Testing (SOP 2) - Test implementation
Day 13-14: Deploy (SOP 3)
```

**Compared to Without SOP 9**:
```
Day 1: Pick approach (guess)
Day 2-7: Implement wrong approach
Day 8: Discover it violates ToS / too expensive / doesn't work
Day 9: Start over with different approach
Day 10-15: Implement correct approach
Day 16-18: Testing
Day 19-20: Deploy

Net savings with SOP 9: 5-7 days
```

**Success Criteria**:
- [ ] 3-4 approaches researched by parallel agents
- [ ] `exploration/COMPARISON-MATRIX.md` created with scores
- [ ] `exploration/RECOMMENDATION.md` documents chosen approach with rationale
- [ ] Chosen approach has clear implementation path
- [ ] Alternatives documented for future reference

**References**:
- See `docs/testing-strategy.md` for distinction between exploration (SOP 9) and testing (SOP 2)
- See `email-analyzer/testing/` as template for multi-agent setup (similar structure)
