# SOP Audit Improvement Plan

**Audit Date**: 2026-02-08
**Audit Method**: 4 parallel agents (SOPs 0-10, SOPs 11-20, SOPs 21-30, Cross-references)
**Overall Health**: 3.9/5 - Functional but needs standardization

---

## Executive Summary

| Category | Score | Critical Issues |
|----------|-------|-----------------|
| SOPs 0-10 | 3.8/5 | SOP 7 needs overhaul, missing three-agent routing |
| SOPs 11-20 | 3.7/5 | Broken references, SOPs 15-16 incomplete |
| SOPs 21-30 | 4.3/5 | SOPs 27-29 exemplary, others need three-agent routing |
| Cross-references | 3.5/5 | 81 orphaned docs, naming inconsistencies |

---

## Priority 1: Critical Fixes (This Session)

### 1.1 Add Three-Agent Routing to All SOPs
**Impact**: High (unified agent selection)
**Effort**: Medium

SOPs missing explicit agent routing:
- SOPs 0-10 (all)
- SOPs 11-20 (all)
- SOPs 21, 22, 23, 24, 30

**Action**: Add `**Agent**:` line after Purpose or Prerequisites.

### 1.2 Add Missing SOPs to Quick Reference Table
**Impact**: High (discoverability)
**Effort**: Low

Missing from table:
- SOP 25: Documentation Decision Framework
- SOP 29: Three-Agent Collaboration

### 1.3 Fix Broken References
**Impact**: High (broken links confuse users)
**Effort**: Low

| SOP | Broken Reference | Fix |
|-----|-----------------|-----|
| 11 | `projects/md-to-pdf/` | Update to existing project |
| 11 | `projects/amazon-seller/` | Update to existing project |
| 15 | `docs/deployment-channels-guide.md` | Remove or create file |

### 1.4 Add Success Criteria to SOPs Missing Them
**Impact**: Medium (completion verification)
**Effort**: Medium

SOPs missing explicit Success Criteria:
- SOP 0, 1, 3, 4, 5, 6, 7, 8, 9
- SOP 15, 16, 19, 20
- SOP 21, 30

---

## Priority 2: Medium Fixes (Next Session)

### 2.1 Add Prerequisites to SOPs
SOPs missing Prerequisites:
- SOP 4, 5, 6, 7, 8
- SOP 19, 20
- SOP 21, 22, 23, 30

### 2.2 Overhaul SOP 7 (DOE Rollback)
**Score**: 2.5/5 (lowest in audit)
- Missing Purpose, Prerequisites, Success Criteria
- Weak example reference
- May be outdated for internal tools

### 2.3 Flesh Out SOP 16 (OpenRouter Registration)
**Score**: 2/5
- Currently just URLs with no guidance
- Missing actual registration walkthroughs
- Missing approval timelines

### 2.4 Add Troubleshooting Sections
SOPs that would benefit:
- SOP 22 (Campaign Analytics)
- SOP 30 (n8n Workflow Management)

---

## Priority 3: Cleanup (Ongoing)

### 3.1 Documentation Organization
- 81 orphaned docs in `docs/`
- Create `docs/archive/` for session files
- Create `docs/INTEGRATIONS-INDEX.md` for 40+ tool guides

### 3.2 Naming Standardization
Files using underscores (should be hyphens):
- DEPLOYMENT_GUIDE.md → DEPLOYMENT-GUIDE.md
- TESTING_GUIDE.md → TESTING-GUIDE.md
- SETUP_GUIDE.md → SETUP-GUIDE.md

### 3.3 Add Missing Docs to Documentation Map
Referenced but not in map:
- AGENT-ORCHESTRATOR-GUIDE.md
- FOLDER-STRUCTURE-GUIDE.md
- HYBRID-ARCHITECTURE-QUICK-REF.md
- EC2-N8N-SETUP.md
- MCP-CONVERSION-PLAN.md

---

## Standard SOP Template (Based on Audit)

Best practices from SOP 17 (Market Viability) and SOPs 27-29 (Three-Agent):

```markdown
### SOP N: [Name]

**When**: [Trigger condition]

**Purpose**: [What this SOP accomplishes]

**Prerequisites**:
- ✅ [Requirement 1]
- ✅ [Requirement 2]

**Agent**:
| Agent | Usage | Example |
|-------|-------|---------|
| Claude Code | [When] | [Example] |
| Clawdbot | [When] | [Example] |
| Ralph | [When or N/A] | [Example] |

**Steps**:
1. [Step 1]
2. [Step 2]
...

**Success Criteria**:
- [ ] [Verification 1]
- [ ] [Verification 2]

**Troubleshooting**:
| Issue | Cause | Solution |
|-------|-------|----------|

**References**: [Links to related docs]

---
```

---

## Exemplary SOPs (Models for Others)

| SOP | Score | Why It's Good |
|-----|-------|---------------|
| 17 | 5/5 | Complete agent prompts, real examples, scoring guide |
| 27 | 5/5 | Comprehensive Clawdbot usage, clear decision tree |
| 28 | 5/5 | Detailed PRD guidance, execution flow |
| 29 | 5/5 | Master routing document, 5 collaboration patterns |
| 14 | 5/5 | Quick update workflow, version mismatch detection |

---

## Implementation Order

### Session 1 (Now):
1. ✅ Add three-agent routing to all SOPs
2. ✅ Add SOP 25, 29 to Quick Reference table
3. ✅ Fix broken references in SOPs 11, 15

### Session 2:
4. ✅ Add Success Criteria to 15+ SOPs
5. ✅ Add Prerequisites to 10+ SOPs
6. ✅ Overhaul SOP 7

### Session 3:
7. ✅ Flesh out SOP 16
8. ✅ Add Troubleshooting to SOPs 22, 30
9. ✅ Create docs/archive/ structure

### Ongoing:
10. ✅ Move orphaned session files to archive (19 files total)
11. ✅ Standardize file naming (6 MD files renamed)
12. ✅ Update Documentation Map (6 entries added)

---

## Verification Checklist

After implementing Priority 1:
- [x] All SOPs have Agent line (25 SOPs updated)
- [x] Quick Reference table includes SOP 25 and 29
- [x] No broken project references in SOPs (SOP 11 + SOP 15 fixed)
- [x] Test: Can user easily determine which agent handles any SOP?

**Session 1 Complete**: 2026-02-08

After implementing Priority 2 (Session 2):
- [x] Success Criteria added to SOPs 0, 1, 3, 4, 5, 6, 7, 8, 9, 19, 20, 21, 30
- [x] Prerequisites added to SOPs 1, 19, 20, 22, 30
- [x] SOP 7 overhauled (2.5/5 → 4.5/5 estimated)

**Session 2 Complete**: 2026-02-08

After implementing Priority 3 (Session 3):
- [x] SOP 16 enhanced with timelines, troubleshooting, maintenance section
- [x] Troubleshooting tables added to SOPs 22 and 30
- [x] docs/archive/ structure created with README
- [x] 11 files archived (10 analysis, 1 deprecated)

**Session 3 Complete**: 2026-02-08

---

*Plan created from 4-agent parallel audit on 2026-02-08*
