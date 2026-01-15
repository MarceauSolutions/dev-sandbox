# Uber/Lyft Price Comparison App

**Status**: Architecture Exploration (SOP 9)
**Created**: 2026-01-12
**Owner**: William Marceau Jr.

---

## Project Goal

Build an app that automatically compares Uber and Lyft prices in real-time, allowing users to choose the cheaper option without manually checking both apps.

---

## Current Phase: Architecture Exploration (SOP 9)

**What We're Doing**: Researching 4 different approaches in parallel to determine the best way to build this app BEFORE writing any code.

**Why**: Avoid spending 1-2 weeks implementing the wrong approach (e.g., web scraping that violates ToS, expensive APIs, unreliable third-party services).

**How**: 4 agents researching in parallel:
1. Official Uber/Lyft APIs
2. Web Scraping
3. Third-Party Aggregators
4. Mobile App/Deep Linking

**Timeline**:
- Day 1-2: Research (agents working in parallel)
- Day 3: Consolidate findings and make recommendation
- Day 4+: Begin implementation with chosen approach

---

## Quick Start

**To launch the exploration**:
```bash
cd exploration/
open START-HERE.md
open AGENT-PROMPTS.txt
```

Then follow instructions in START-HERE.md to launch 4 agents.

---

## Project Structure

```
uber-lyft-comparison/
├── README.md                       # This file
├── exploration/                    # Architecture research (SOP 9)
│   ├── START-HERE.md               # How to launch agents
│   ├── QUICK-LAUNCH.txt            # Quick reference card
│   ├── EXPLORATION-PLAN.md         # Research plan and criteria
│   ├── AGENT-PROMPTS.txt           # Copy-paste prompts for agents
│   ├── agent1-official-apis/       # Research workspace
│   ├── agent2-web-scraping/        # Research workspace
│   ├── agent3-third-party/         # Research workspace
│   ├── agent4-mobile-approach/     # Research workspace
│   └── consolidated-results/       # Final recommendation
│       ├── COMPARISON-MATRIX.md    # (will be created)
│       └── RECOMMENDATION.md        # (will be created)
│
├── directives/                     # (will be created after exploration)
│   └── uber_lyft_comparison.md
│
└── src/                            # (will be created after exploration)
    └── (implementation files)
```

---

## User Requirements

**Core Functionality**:
- Input: Pickup location, Dropoff location
- Output: Uber price, Lyft price, recommendation (cheaper option)
- Performance: < 5 seconds response time
- Accuracy: Real-time or near-real-time pricing

**Nice-to-Have**:
- Multiple service levels (UberX, Lyft, UberXL, Lyft XL)
- Price history tracking
- Surge pricing alerts
- Favorite routes

---

## Evaluation Criteria

We'll choose the approach that scores highest on:

1. **Feasibility** (25%): Can we actually build this?
2. **Legal** (25%): Does it comply with Uber/Lyft Terms of Service?
3. **Cost** (20%): What are the ongoing expenses? Is it sustainable?
4. **Reliability** (15%): How often will it break?
5. **User Experience** (15%): How fast and accurate?

**Scoring**: 1-5 stars per criterion, weighted total out of 25 points

**Decision**:
- 20-25 points: Strong candidate → Implement
- 15-19 points: Viable with caveats
- 10-14 points: Risky
- < 10 points: Rule out

---

## Approaches Being Explored

### Approach 1: Official Uber/Lyft APIs
**Hypothesis**: Use official developer APIs

**Pros**: Legal, reliable, well-documented
**Cons**: Potential costs, rate limits
**Research Focus**: API availability, pricing, authentication

---

### Approach 2: Web Scraping
**Hypothesis**: Scrape Uber.com and Lyft.com

**Pros**: Free, no API limits
**Cons**: Legal risks (ToS), maintenance burden, anti-scraping measures
**Research Focus**: Legal compliance, technical feasibility

---

### Approach 3: Third-Party Aggregators
**Hypothesis**: Use existing aggregator services (RideGuru, Rome2rio, etc.)

**Pros**: Pre-built solution, potentially legal
**Cons**: Lock-in risk, costs, data freshness
**Research Focus**: Service availability, pricing, reliability

---

### Approach 4: Mobile App / Deep Linking
**Hypothesis**: Build mobile app using Uber/Lyft SDKs

**Pros**: Native integration, good UX
**Cons**: Mobile-only, platform limitations
**Research Focus**: SDK capabilities, authentication, UX

---

## Next Steps

**Current**: Waiting for 4 agents to complete research

**After Research**:
1. Review all FINDINGS.md files
2. Create comparison matrix
3. Make recommendation
4. Create directive
5. Begin implementation (SOP 1)

---

## References

- **SOP 9**: `CLAUDE.md` - Multi-Agent Architecture Exploration
- **Architecture Guide**: `docs/architecture-guide.md`
- **Testing Strategy**: `docs/testing-strategy.md` (will use after implementation)

---

## Development Philosophy

**Why we're doing this exploration first**:

❌ **Without exploration**:
- Day 1: Pick approach (guess)
- Day 2-7: Implement wrong approach
- Day 8: Discover it violates ToS / too expensive / doesn't work
- Day 9: Start over
- Total wasted: 1-2 weeks

✅ **With exploration**:
- Day 1-2: Research 4 approaches in parallel
- Day 3: Choose best one with evidence
- Day 4+: Implement with confidence
- Time saved: 1-2 weeks

**Result**: Build the right thing the first time.

---

**Status**: Ready to launch agents → Open `exploration/START-HERE.md`
