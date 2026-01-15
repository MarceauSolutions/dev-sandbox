# MCP Conversion Assessment Framework

> **Purpose**: Lightweight framework for converting EXISTING projects to registry-ready MCPs. Not for new projects (use SOP 0 for those).

## When to Use This Framework

Use this instead of SOP 0 when:
- Project already exists with working code
- Core functionality is built and tested
- You're deciding "how fast can we convert?" not "should we build?"

## Conversion Assessment Checklist

### 1. Technical Readiness (Required)

| Criterion | Weight | Check |
|-----------|--------|-------|
| Has working Python code in `src/` | Required | [ ] |
| Code is functional (runs without errors) | Required | [ ] |
| No critical bugs or incomplete features | Required | [ ] |

**If any required item fails → Not ready for conversion**

### 2. MCP Suitability Score

| Factor | Points | Description |
|--------|--------|-------------|
| **Standalone execution** | +3 | Can run without web frontend or human orchestration |
| **Clear tool boundaries** | +2 | Functions map cleanly to MCP tools |
| **No/few API keys** | +2 | Minimal external dependencies |
| **Stateless operations** | +2 | Each request is independent |
| **Single-purpose** | +1 | Does one thing well |
| | |
| **Requires web frontend** | -3 | Needs UI for core functionality |
| **Workflow-based** | -3 | Requires Claude orchestration, not code |
| **Heavy orchestration** | -2 | Multi-step AI reasoning required |
| **Complex auth flow** | -1 | OAuth, token refresh, etc. |

**Score interpretation:**
- 8+ points: Excellent candidate
- 5-7 points: Good candidate (some work needed)
- 2-4 points: Moderate candidate (significant work)
- <2 points: Poor candidate (reconsider)

### 3. Effort Estimation Matrix

| Starting State | Has MCP Server | Effort |
|----------------|----------------|--------|
| Complete code, tested | No | 2-4 hours |
| Complete code, untested | No | 4-8 hours |
| Partial code (70%+) | No | 8-16 hours |
| Partial code (50-70%) | No | 16-24 hours |
| Minimal code (<50%) | No | 24+ hours |

**Add time for:**
- +2 hours if missing VERSION/CHANGELOG
- +4 hours if complex API integrations
- +4 hours if needs OAuth/token management
- +2 hours per external API that needs key management

### 4. Impact Assessment

| Factor | Impact Score |
|--------|--------------|
| **Unique capability** (no competitors in registry) | HIGH |
| **High demand** (common user need) | HIGH |
| **Complex orchestration** (hard to replicate) | HIGH |
| **Proven revenue model** | HIGH |
| | |
| **Many competitors** (crowded category) | LOW |
| **Niche use case** (narrow audience) | LOW |
| **Simple utility** (easy to replicate) | LOW |

---

## Applying the Framework

### Project: [Name]

**Technical Readiness:**
- [ ] Has working code
- [ ] Code runs without errors
- [ ] No critical bugs

**Suitability Score:** ___/10

**Effort Estimate:** ___ hours

**Impact:** HIGH / MEDIUM / LOW

**Priority:** ___ (1 = highest)

**Blockers:**
- [ ] Blocker 1
- [ ] Blocker 2

**Decision:** CONVERT / DEFER / SKIP

---

## Prioritization Formula

```
Priority Score = (Impact × 3) + (Suitability × 2) - (Effort Hours / 4)
```

Higher score = higher priority

**Example:**
- High Impact (3) × 3 = 9
- Suitability 8 × 2 = 16
- Effort 4 hours / 4 = 1
- **Score: 9 + 16 - 1 = 24** (high priority)

---

## Quick Decision Tree

```
Has working code in src/?
├── NO → Not ready for MCP conversion
│
└── YES → Can it run standalone (no web UI needed)?
    │
    ├── NO → Consider as Web App instead
    │
    └── YES → Does it require Claude orchestration?
        │
        ├── YES → Keep as Claude Skill, not MCP
        │
        └── NO → Calculate Priority Score
            │
            ├── Score > 20 → CONVERT NOW
            ├── Score 10-20 → CONVERT NEXT
            └── Score < 10 → DEFER
```

---

## Related Documentation

- [SOP 0: Project Kickoff](../CLAUDE.md#sop-0) - For NEW projects
- [App Type Decision Guide](app-type-decision-guide.md) - MCP vs standalone decisions
- [MCP Registry Guide](../projects/mcp-aggregator/registry/README.md) - How to register
