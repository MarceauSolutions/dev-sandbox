# Optimization Threshold Policy

**Created**: 2026-01-14
**Purpose**: Prevent wasted effort on marginal improvements. Establish clear thresholds for when optimization is worth pursuing.

---

## The 10x Rule

**Only optimize if the change:**
1. Reduces cost by at least 10x, OR
2. Increases output value by at least 10x

If a proposed optimization doesn't meet this threshold, **skip it** and move on to higher-impact work.

---

## Why This Matters

### The Diminishing Returns Problem

```
Effort vs. Improvement Curve:

Improvement
    │
100%├────────────●──────────────────  (First 80% of value)
    │           /
 80%├──────────/
    │         /
 60%├────────/
    │       /
 40%├──────/
    │     /
 20%├────/
    │   /
  0%├──/────────────────────────────
    0%  20%  40%  60%  80%  100%
                Effort →
```

**Reality**:
- First 20% of effort → 80% of the value
- Next 80% of effort → 20% of the value
- That last 5% improvement? Could take 50% more effort.

### Time is the Constraint

Your time has a fixed supply. Every hour spent on 0.5% optimization is an hour NOT spent on:
- Building new revenue streams
- Fixing actual bugs
- Shipping features customers want
- Learning high-value skills

---

## Decision Framework

### Before Optimizing, Ask:

| Question | If NO → Skip | If YES → Continue |
|----------|--------------|-------------------|
| Will this save 10x cost? | Skip | Evaluate further |
| Will this increase value 10x? | Skip | Evaluate further |
| Is this blocking revenue? | Skip | Prioritize |
| Are users complaining? | Skip | Address |
| Is this a security issue? | Skip | Fix immediately |

### Quick Gut Check

```
"If I spend [X hours] on this optimization, will the result be
worth 10x more than spending those same hours on [alternative]?"
```

If the answer isn't a clear YES → skip the optimization.

---

## Examples

### SKIP These Optimizations

| Scenario | Improvement | Time Cost | Verdict |
|----------|-------------|-----------|---------|
| Refactoring working code for "cleanliness" | 0% functional | 4 hours | **SKIP** |
| Reducing API response from 200ms to 180ms | 10% faster | 8 hours | **SKIP** |
| Adding type hints to legacy code | 0.5% fewer bugs | 6 hours | **SKIP** |
| Switching from JSON to msgpack | 5% faster | 12 hours | **SKIP** |
| Optimizing rarely-used report | 2x faster | 10 hours | **SKIP** |

### PURSUE These Optimizations

| Scenario | Improvement | Time Cost | Verdict |
|----------|-------------|-----------|---------|
| Caching API calls (100 calls → 1) | 100x fewer calls | 2 hours | **DO IT** |
| Batch processing (1 request/item → 1 request/100 items) | 100x fewer requests | 4 hours | **DO IT** |
| Switching from polling to webhooks | 1000x fewer checks | 6 hours | **DO IT** |
| Adding Apollo.io (manual research → automated) | 50x faster enrichment | 3 hours | **DO IT** |
| Cloud functions (always-on → pay-per-use) | 10-100x cost reduction | 8 hours | **DO IT** |

---

## Application to Current Projects

### Lead Scraper Optimization Decisions

| Proposed Change | Impact | Verdict |
|-----------------|--------|---------|
| Add Apollo.io integration | 50x faster than manual LinkedIn research | ✅ **DONE** |
| Add cloud function deployment | 10x cost reduction when idle | ✅ **WORTH DOING** |
| Optimize scraping algorithm for 5% more leads | 1.05x improvement | ❌ **SKIP** |
| Add Hunter.io email verification | 10x better deliverability | ✅ **WORTH DOING** |
| Refactor to async for 20% speed boost | 1.2x improvement | ❌ **SKIP** |

### Architecture Optimization Decisions

| Proposed Change | Impact | Verdict |
|-----------------|--------|---------|
| Add Modal cloud function support | New revenue channel (10x+) | ✅ **WORTH DOING** |
| Refactor deploy_to_skills.py structure | 0% functional change | ❌ **SKIP** |
| Add Slack observability | Saves 10x debugging time | ✅ **WORTH DOING** |
| Migrate from Railway to K8s | 2x infrastructure complexity for 10% savings | ❌ **SKIP** |

---

## When to Break This Rule

### Exceptions (Optimize Even If <10x)

1. **Security vulnerabilities** - Fix immediately regardless of impact
2. **Data integrity issues** - Even 0.1% data loss is unacceptable
3. **User-reported pain points** - If users complain, it matters
4. **Blocking dependencies** - If it blocks other 10x improvements
5. **Regulatory/legal requirements** - Compliance isn't optional

### The "Itch" Test

Sometimes you just feel like something needs to be cleaner/better. Before scratching that itch:

1. Write down the specific improvement
2. Estimate time to implement
3. Estimate measurable impact
4. If impact < 10x and time > 1 hour → **add to backlog, don't do now**

---

## Backlog for <10x Optimizations

If something doesn't meet the 10x threshold but still seems valuable, add it here. Review quarterly.

| Item | Est. Impact | Est. Time | Added | Status |
|------|-------------|-----------|-------|--------|
| *Example: Add type hints to lead-scraper* | 1.5x fewer bugs | 4 hours | 2026-01-14 | Backlog |
| | | | | |

**Review schedule**: End of each quarter, batch small optimizations if time permits.

---

## Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION DECISION                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Does this change provide 10x improvement?                 │
│                                                             │
│        YES                              NO                  │
│         │                                │                  │
│         ▼                                ▼                  │
│   ┌─────────┐                     ┌─────────────┐          │
│   │  DO IT  │                     │  Is it a    │          │
│   └─────────┘                     │  security/  │          │
│                                   │  compliance │          │
│                                   │  issue?     │          │
│                                   └──────┬──────┘          │
│                                          │                  │
│                                   YES    │    NO            │
│                                    │     │     │            │
│                                    ▼     │     ▼            │
│                              ┌────────┐  │  ┌──────┐       │
│                              │ FIX IT │  │  │ SKIP │       │
│                              └────────┘  │  └──────┘       │
│                                          │                  │
└─────────────────────────────────────────────────────────────┘
```

**Default action**: Ship, move on, build new things.

---

*"Perfect is the enemy of good. Good enough ships, perfect doesn't."*
