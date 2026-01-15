# Comprehensive SOP & Pipeline Conflict Audit

**Date**: 2026-01-12
**Purpose**: Identify ALL conflicts across SOPs, pipelines, and development strategies
**Status**: 🔴 IN PROGRESS

---

## Audit Scope

### Documents Audited
1. ✅ CLAUDE.md - Core operating instructions
2. ✅ docs/testing-strategy.md - Testing pipeline
3. ✅ docs/development-to-deployment.md - Complete development flow
4. ✅ docs/deployment.md - Deployment specifics
5. ✅ docs/repository-management.md - Repository rules
6. ✅ docs/versioned-deployment.md - Version control
7. ✅ docs/ARCHITECTURE-CONFLICT-RESOLUTION.md - execution/ vs projects/src/
8. ✅ deploy_to_skills.py - Actual deployment implementation

### Conflicts to Evaluate
- [x] Testing: When/where/how
- [x] Deployment: What gets deployed from where
- [ ] Code Location: execution/ vs projects/src/
- [ ] DOE Architecture: How it applies to projects
- [ ] Versioning: Dev vs prod version management
- [ ] Repository: What gets committed where
- [ ] Skills: .claude/skills vs -prod repos

---

## CONFLICT #1: Code Location (execution/ vs projects/src/)

### Current State: CONFLICTING

**CLAUDE.md says**:
```
Layer 3: EXECUTION (execution/*.py) → Deterministic scripts
```

**Actual practice**:
```
projects/[name]/src/*.py  ← Development happens here
execution/*.py            ← Some scripts here, some not
```

**deploy_to_skills.py expects**:
- Scripts listed in configuration
- Copies from `execution/` to skills

### Three Solution Options

#### Option A: Pure DOE (All code in execution/)

**How it works**:
- Develop ALL scripts directly in `execution/`
- Remove `projects/[name]/src/` entirely
- Projects only contain workflows, testing, demos

**Structure**:
```
dev-sandbox/
├── execution/
│   ├── md_to_pdf.py              ← Develop here
│   ├── pptx_generator.py         ← Develop here
│   ├── email_analyzer.py         ← Develop here
│   └── [100+ scripts...]
└── projects/
    └── md-to-pdf/
        ├── workflows/            ← Documentation only
        ├── testing/              ← Tests
        └── demos/                ← Client outputs
```

**Pros**:
- ✅ Aligns perfectly with DOE architecture
- ✅ Single source of truth for all code
- ✅ No sync needed between folders
- ✅ deploy_to_skills.py works without changes

**Cons**:
- ❌ `execution/` becomes massive (100+ files)
- ❌ No project organization (hard to find files)
- ❌ Shared vs project-specific code mixed together
- ❌ Can't tell what belongs to what project
- ❌ Violates separation of concerns

**Effort**: Low (just move files)
**Maintainability**: Low (scales poorly)

---

#### Option B: Pure Projects (All code in projects/src/)

**How it works**:
- Develop ALL scripts in `projects/[name]/src/`
- `execution/` deprecated (or only config files)
- Update deploy_to_skills.py to deploy from `src/`

**Structure**:
```
dev-sandbox/
├── execution/                    ← Deprecated or configs only
└── projects/
    ├── md-to-pdf/
    │   └── src/
    │       └── md_to_pdf.py      ← Source of truth
    ├── interview-prep/
    │   └── src/
    │       ├── pptx_generator.py ← Source of truth
    │       └── interview_research.py
    └── email-analyzer/
        └── src/
            └── email_analyzer.py ← Source of truth
```

**Pros**:
- ✅ Clear project ownership
- ✅ Easy to find code (organized by project)
- ✅ Scales well (each project self-contained)
- ✅ Matches current practice
- ✅ Better separation of concerns

**Cons**:
- ❌ Breaks DOE architecture conceptually
- ❌ No place for truly shared utilities
- ❌ Requires updating deploy_to_skills.py
- ❌ Need to update all documentation
- ❌ What about multi-project utilities?

**Effort**: Medium (update deployment + docs)
**Maintainability**: High (clear organization)

---

#### Option C: Hybrid (Shared in execution/, Projects in src/)

**How it works**:
- **Shared utilities** (multi-project): `execution/`
- **Project-specific code**: `projects/[name]/src/`
- deploy_to_skills.py handles both

**Structure**:
```
dev-sandbox/
├── execution/                    ← SHARED utilities only
│   ├── gmail_monitor.py          ← Used by multiple projects
│   ├── twilio_sms.py             ← Used by multiple projects
│   ├── grok_image_gen.py         ← Used by multiple projects
│   └── [~20 shared utilities]
└── projects/
    ├── md-to-pdf/
    │   └── src/
    │       └── md_to_pdf.py      ← Project-specific
    ├── interview-prep/
    │   └── src/
    │       ├── pptx_generator.py ← Project-specific
    │       └── interview_research.py
    └── shared-lib/               ← OR: Shared as a "project"
        └── src/
            ├── gmail_monitor.py
            └── twilio_sms.py
```

**Pros**:
- ✅ Clear separation: shared vs project-specific
- ✅ DOE applies to shared utilities
- ✅ Projects self-contained
- ✅ Scales well
- ✅ Can extract shared code when pattern emerges
- ✅ Best of both worlds

**Cons**:
- ❌ More complex mental model (two patterns)
- ❌ Need clear guidelines on what goes where
- ❌ Requires updating deploy_to_skills.py
- ❌ Need to audit/reorganize existing code

**Effort**: High (audit + reorganize + update deployment)
**Maintainability**: High (clear rules once established)

---

### Recommended: Option C (Hybrid)

**Rationale**:
- Maintains DOE philosophy for truly shared code
- Allows projects to be self-contained
- Scales better than Option A
- More organized than Option B alone
- Reflects real-world usage patterns

**Decision Matrix**:
| Criteria | Option A | Option B | Option C |
|----------|----------|----------|----------|
| Aligns with DOE | ✅ Perfect | ❌ No | ⚠️ Partial |
| Project organization | ❌ Poor | ✅ Excellent | ✅ Excellent |
| Shared code handling | ❌ Mixed | ❌ Unclear | ✅ Clear |
| Scalability | ❌ Poor | ✅ Good | ✅ Excellent |
| Maintainability | ❌ Poor | ✅ Good | ✅ Excellent |
| Implementation effort | ✅ Low | ⚠️ Medium | ❌ High |

**Winner**: Option C (best long-term despite higher upfront cost)

---

## CONFLICT #2: DOE Architecture Application

### Current State: UNCLEAR

**Question**: Does DOE architecture apply to ALL code or just shared utilities?

### Three Solution Options

#### Option A: DOE for Everything

**Application**: All projects must follow strict DOE

**Structure**:
```
For EVERY project:
Layer 1: directives/[project].md
Layer 2: Claude orchestration
Layer 3: execution/[project]_*.py
```

**Pros**:
- ✅ Consistent architecture everywhere
- ✅ Clear mental model

**Cons**:
- ❌ Forces all code into execution/
- ❌ Doesn't work well for standalone projects
- ❌ Too rigid

---

#### Option B: DOE Optional

**Application**: DOE is a pattern, not a requirement

**Guidelines**:
- Use DOE when: Building shared utilities, complex orchestration
- Don't use DOE when: Simple projects, self-contained tools

**Pros**:
- ✅ Flexible
- ✅ Choose best pattern for each project

**Cons**:
- ❌ Inconsistent
- ❌ Confusing when to use which

---

#### Option C: Two-Tier Architecture

**Application**:
- **Tier 1 (Shared/Platform)**: Strict DOE
- **Tier 2 (Projects)**: Flexible, project-specific patterns

**Structure**:
```
Tier 1 (DOE - Shared Utilities):
directives/shared_utilities.md
execution/*.py  ← Shared code

Tier 2 (Project-Specific):
directives/[project].md
projects/[project]/src/*.py  ← Project code
```

**Pros**:
- ✅ Clear distinction
- ✅ DOE where it makes sense
- ✅ Flexibility for projects

**Cons**:
- ❌ Two patterns to remember

---

### Recommended: Option C (Two-Tier)

**Rationale**: DOE is perfect for shared utilities (Tier 1), but projects need flexibility (Tier 2)

---

## CONFLICT #3: Skills Deployment Location

### Current State: MULTIPLE PATTERNS

**Pattern A**: `.claude/skills/[name]/` (MCP skills)
**Pattern B**: `/Users/williammarceaujr./[name]-prod/` (Production repos)
**Pattern C**: Projects stay in dev-sandbox (not deployed)

### Three Solution Options

#### Option A: All Skills in .claude/skills/

**Structure**:
```
dev-sandbox/.claude/skills/
├── interview-prep/
├── email-analyzer/
└── md-to-pdf/
```

**Pros**:
- ✅ MCP integration ready
- ✅ All in one place

**Cons**:
- ❌ Inside dev-sandbox (nested)
- ❌ Not separate git repos
- ❌ Can't push to GitHub individually

---

#### Option B: All Skills as -prod Repos

**Structure**:
```
/Users/williammarceaujr./
├── dev-sandbox/
├── interview-prep-prod/
├── email-analyzer-prod/
└── md-to-pdf-prod/
```

**Pros**:
- ✅ Separate git repos
- ✅ Can push to GitHub
- ✅ Clear dev vs prod separation

**Cons**:
- ❌ Not in .claude/skills (manual MCP setup)
- ❌ More folders at user root

---

#### Option C: Hybrid Deployment

**Structure**:
```
MCP Skills (for Claude usage):
dev-sandbox/.claude/skills/[name]/  ← Symlink to -prod

Production Repos (for distribution):
/Users/williammarceaujr./[name]-prod/  ← Actual git repos

deploy_to_skills.py creates both
```

**Pros**:
- ✅ Best of both
- ✅ MCP integration + GitHub distribution
- ✅ Clean separation

**Cons**:
- ❌ Symlink management
- ❌ More complex deployment

---

### Recommended: Option B (-prod repos) + Document MCP setup

**Rationale**: Cleaner, standard git workflow. MCP can reference -prod folders.

---

## CONFLICT #4: Version Management

### Current State: INCONSISTENT

**Pattern A**: VERSION file with `-dev` suffix during development
**Pattern B**: Git tags for versions
**Pattern C**: CHANGELOG.md documents versions

### Three Solution Options

#### Option A: VERSION File Only

**Process**:
1. VERSION: `1.0.0-dev` (development)
2. Before deploy: Remove `-dev` → `1.0.0`
3. After deploy: Bump to `1.1.0-dev`
4. Git tags optional

---

#### Option B: Git Tags Only

**Process**:
1. No VERSION file
2. Use git tags: `v1.0.0`
3. Deployment creates tag
4. Query git for current version

---

#### Option C: Comprehensive Versioning

**Process**:
1. VERSION file: `1.0.0-dev`
2. CHANGELOG.md: Documents all changes
3. Git tag: `v1.0.0` on deployment
4. All three stay in sync

---

### Recommended: Option C (Comprehensive)

**Rationale**: Redundancy ensures consistency, CHANGELOG provides context

---

## CONFLICT #5: Testing Artifacts Location

### Current State: MULTIPLE LOCATIONS

**Pattern A**: `.tmp/` for temporary test outputs (not committed)
**Pattern B**: `projects/[name]/testing/` for multi-agent testing
**Pattern C**: `projects/[name]/demos/` for client outputs

### Three Solution Options

#### Option A: Everything in testing/

**Structure**:
```
projects/[name]/testing/
├── manual/          ← Manual test outputs
├── multi-agent/     ← Multi-agent tests
├── demos/           ← Client demos
└── .tmp/            ← Temporary (not committed)
```

---

#### Option B: Separate by Purpose

**Structure**:
```
projects/[name]/
├── .tmp/            ← Temporary (not committed)
├── testing/         ← Multi-agent only
└── demos/           ← Client outputs only
```

---

#### Option C: Separate + Archive

**Structure**:
```
projects/[name]/
├── .tmp/                  ← Active temp files
├── testing/               ← Multi-agent tests
├── demos/client-[name]/   ← Client demos (dated)
└── archive/               ← Old test results
```

---

### Recommended: Option B (Separate by Purpose)

**Rationale**: Clear separation, .tmp/ stays clean, demos preserved

---

## Summary of Recommended Solutions

| Conflict | Winner | Rationale |
|----------|--------|-----------|
| **Code Location** | Option C: Hybrid | Shared in execution/, projects in src/ |
| **DOE Application** | Option C: Two-Tier | DOE for shared, flexible for projects |
| **Skills Deployment** | Option B: -prod repos | Clean git workflow |
| **Version Management** | Option C: Comprehensive | VERSION + CHANGELOG + Git tags |
| **Testing Artifacts** | Option B: Separate by Purpose | Clear organization |

---

## Implementation Plan

### Phase 1: Documentation Updates (Immediate)

1. **Update CLAUDE.md**:
   - Clarify: `execution/` = shared utilities
   - Clarify: `projects/[name]/src/` = project code
   - Update DOE architecture explanation

2. **Update testing-strategy.md**:
   - Confirm: Test in `projects/[name]/src/`
   - Note: Shared utilities are dependencies

3. **Create docs/architecture-guide.md**:
   - Define two-tier architecture
   - Guidelines for shared vs project-specific
   - Decision tree for where to put code

### Phase 2: Code Reorganization (Next)

4. **Audit execution/ folder**:
   - Identify truly shared scripts
   - Move project-specific scripts to projects/

5. **Update deploy_to_skills.py**:
   - Support deploying from `projects/[name]/src/`
   - Support deploying shared from `execution/`
   - Handle both patterns

### Phase 3: Verification (Final)

6. **Test deployment workflow**:
   - Deploy a project from `projects/[name]/src/`
   - Verify skills work correctly

7. **Update all project READMEs**:
   - Document new structure
   - Migration guide if needed

---

## Next Steps

1. **Get approval** on recommended solutions
2. **Implement Phase 1** (documentation updates)
3. **Begin Phase 2** (code reorganization)
4. **Verify** no remaining conflicts

---

**Status**: ✅ Phase 1, 2, 3 Complete - Implementation Ready
**Next**: Phase 4 (Optional - Gradual Code Migration)

**Implemented**:

**Phase 1 (Documentation)**:
- ✅ Created `docs/architecture-guide.md` - Comprehensive architecture reference
- ✅ Updated CLAUDE.md with Two-Tier Architecture
- ✅ Updated all cross-references in CLAUDE.md
- ✅ Added deployment timing and post-deployment testing guidance

**Phase 2 (Code Audit)**:
- ✅ Audited all 62 scripts in execution/ folder
- ✅ Created `docs/EXECUTION-FOLDER-AUDIT.md` - Categorization and migration plan
- ✅ Created `execution/README.md` - Guidelines for what belongs in execution/

**Phase 3 (Deployment Updates)**:
- ✅ Updated `deploy_to_skills.py` to support deploying from projects/src/
- ✅ Updated both deploy_to_local_workspace() and deploy_to_github()
- ✅ Added shared_utils support for explicit shared utility declaration
- ✅ Maintained full backward compatibility
- ✅ Tested with naples-weather project

**See**:
- [architecture-guide.md](architecture-guide.md) for complete architecture documentation
- [EXECUTION-FOLDER-AUDIT.md](EXECUTION-FOLDER-AUDIT.md) for code audit results
- [PHASE-2-3-COMPLETION.md](PHASE-2-3-COMPLETION.md) for detailed completion report
