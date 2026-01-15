# Unified Architecture Solution

**Date**: 2026-01-12
**Purpose**: Resolve ALL architectural conflicts with chosen best solutions
**Status**: ✅ READY FOR IMPLEMENTATION

---

## Executive Summary

After comprehensive audit of all SOPs, pipelines, and development strategies, **5 major conflicts** were identified and evaluated. This document presents the **chosen solutions** and **implementation plan**.

### Conflicts Identified & Resolved

| # | Conflict | Chosen Solution | Impact |
|---|----------|----------------|---------|
| 1 | Code Location (execution/ vs projects/src/) | **Hybrid Architecture** | HIGH |
| 2 | DOE Architecture Application | **Two-Tier System** | MEDIUM |
| 3 | Skills Deployment Location | **-prod Repos** | MEDIUM |
| 4 | Version Management | **Comprehensive (3-way)** | LOW |
| 5 | Testing Artifacts Location | **Separate by Purpose** | LOW |

---

## SOLUTION #1: Hybrid Code Architecture

### The Decision

**Chosen**: Option C - Hybrid Architecture

**`execution/` = Shared Utilities (DOE Layer 3)**
- Multi-project reusable code
- Examples: `gmail_monitor.py`, `twilio_sms.py`, `grok_image_gen.py`
- Deployed as shared dependencies

**`projects/[name]/src/` = Project Implementation**
- Project-specific code
- Examples: `md_to_pdf.py`, `pptx_generator.py`, `email_analyzer.py`
- Deployed with specific project

### Directory Structure

```
dev-sandbox/
├── execution/                    ← SHARED UTILITIES ONLY
│   ├── gmail_monitor.py          ← Used by: fitness, email-analyzer
│   ├── twilio_sms.py             ← Used by: fitness, amazon-seller
│   ├── grok_image_gen.py         ← Used by: interview-prep, fitness
│   └── [~15-20 shared utilities]
│
└── projects/
    ├── md-to-pdf/
    │   ├── src/
    │   │   ├── md_to_pdf.py      ← PROJECT-SPECIFIC
    │   │   └── convert.sh        ← PROJECT-SPECIFIC
    │   ├── workflows/
    │   ├── testing/
    │   └── demos/
    │
    ├── interview-prep/
    │   ├── src/
    │   │   ├── pptx_generator.py ← PROJECT-SPECIFIC
    │   │   ├── interview_research.py
    │   │   └── session_manager.py
    │   └── [...]
    │
    └── email-analyzer/
        ├── src/
        │   └── email_analyzer.py ← PROJECT-SPECIFIC
        └── [...]
```

### Decision Rules

**Put code in `execution/` when**:
- ✅ Used by 2+ projects
- ✅ General utility (not project-specific logic)
- ✅ Stable API (not frequently changing)
- ✅ Examples: API clients, notification systems, data processors

**Put code in `projects/[name]/src/` when**:
- ✅ Used by only ONE project
- ✅ Project-specific business logic
- ✅ Frequently changing/experimental
- ✅ Examples: Project main scripts, workflows, converters

**Migration pattern**:
1. Start in `projects/[name]/src/`
2. If another project needs it → Extract to `execution/`
3. Update both projects to use shared version

### Implementation Tasks

- [ ] Audit `execution/` folder (identify shared vs project-specific)
- [ ] Move project-specific scripts to `projects/[name]/src/`
- [ ] Update `execution/README.md` with guidelines
- [ ] Update deploy_to_skills.py to deploy from both locations

---

## SOLUTION #2: Two-Tier DOE Architecture

### The Decision

**Chosen**: Option C - Two-Tier Architecture

### Tier 1: Shared Utilities (Strict DOE)

```
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py)
```

**Applies to**: Shared utilities in `execution/`

**Rules**:
- Must have directive documenting purpose
- Called by Claude orchestration
- Deterministic, reusable

---

### Tier 2: Projects (Flexible Architecture)

```
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude or standalone)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py)
```

**Applies to**: Project-specific code

**Rules**:
- May or may not use strict DOE
- Can be standalone scripts
- Can have their own architecture

---

### Updated DOE Definition

**DOE Architecture** = Pattern for shared, reusable utilities

**Not a requirement** for all code, but a **recommended pattern** for:
- Multi-project utilities
- Complex orchestration workflows
- Shared execution scripts

---

## SOLUTION #3: Production Repo Deployment

### The Decision

**Chosen**: Option B - All Skills as -prod Repos

### Deployment Structure

```
Development:
/Users/williammarceaujr./dev-sandbox/
└── projects/[name]/

Production:
/Users/williammarceaujr./
├── dev-sandbox/              ← Development
├── [project-name]-prod/      ← Production deployments
│   ├── .git/                 ← Separate git repo
│   ├── README.md
│   ├── execution/            ← Copied from dev-sandbox
│   ├── VERSION
│   └── CHANGELOG.md
└── [project2-name]-prod/
```

### MCP Skills Integration

**Option A**: Create symlinks
```bash
ln -s /Users/williammarceaujr./[name]-prod/ \
      /Users/williammarceaujr./dev-sandbox/.claude/skills/[name]
```

**Option B**: Update .claude/mcp_config.json to reference -prod folders

**Recommended**: Option B (cleaner, no symlink management)

### Implementation Tasks

- [ ] Verify all deployments create -prod repos (not in .claude/skills)
- [ ] Document MCP configuration for -prod folders
- [ ] Update deploy_to_skills.py to handle MCP config (if needed)

---

## SOLUTION #4: Comprehensive Version Management

### The Decision

**Chosen**: Option C - VERSION + CHANGELOG + Git Tags

### Three-Way Versioning

1. **VERSION file**:
   ```
   Development: 1.2.0-dev
   Pre-deploy:  1.2.0
   Post-deploy: 1.3.0-dev
   ```

2. **CHANGELOG.md**:
   ```markdown
   ## [1.2.0] - 2026-01-12

   ### Added
   - New feature X

   ### Fixed
   - Bug Y
   ```

3. **Git tag**:
   ```bash
   git tag -a v1.2.0 -m "Release 1.2.0"
   ```

### Synchronization Process

**Before deployment**:
```bash
# 1. Update VERSION
echo "1.2.0" > VERSION

# 2. Update CHANGELOG
# Add entry for 1.2.0 with date

# 3. Commit
git add VERSION CHANGELOG.md
git commit -m "chore: Prepare v1.2.0 release"

# 4. Deploy (creates tag automatically)
python deploy_to_skills.py --project [name] --version 1.2.0
```

**After deployment**:
```bash
# 5. Bump to next dev version
echo "1.3.0-dev" > VERSION
git add VERSION
git commit -m "chore: Bump to v1.3.0-dev"
```

### Implementation Tasks

- [ ] Verify deploy_to_skills.py creates git tags
- [ ] Add VERSION file check to pre-deployment checklist
- [ ] Document version bumping process in SOP 3

---

## SOLUTION #5: Testing Artifacts Organization

### The Decision

**Chosen**: Option B - Separate by Purpose

### Directory Structure

```
projects/[name]/
├── .tmp/                     ← Temporary test files (NOT committed)
│   ├── test-output.pdf
│   └── debug-*.log
│
├── testing/                  ← Multi-agent testing ONLY
│   ├── TEST-PLAN.md
│   ├── AGENT-PROMPTS.txt
│   ├── agent1/
│   │   └── FINDINGS.md
│   └── consolidated-results/
│
├── demos/                    ← Client demonstrations
│   └── client-[name]/
│       └── YYYY-MM-DD/
│           └── output.pdf
│
└── samples/                  ← Reference examples for docs
    └── example-*.pdf
```

### Usage Guidelines

**`.tmp/`**:
- Temporary test outputs
- Debug files
- Can be deleted anytime
- NOT committed to git

**`testing/`**:
- Multi-agent testing infrastructure
- Agent findings
- Test plans
- IS committed to git

**`demos/`**:
- Client demonstrations
- Date-stamped sessions
- Preserved for reference
- OPTIONAL git commit (if not sensitive)

**`samples/`**:
- Reference examples
- Documentation screenshots
- Edge case examples
- IS committed to git

### Implementation Tasks

- [ ] Update .gitignore to exclude `.tmp/`
- [ ] Document in testing-strategy.md
- [ ] Add to SOP 8 (Demo Management)

---

## Updated Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ DEVELOPMENT (dev-sandbox - Single Git Repo)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tier 1: SHARED UTILITIES (DOE Architecture)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Layer 1: directives/shared_utilities.md                    │ │
│  │ Layer 2: Claude Orchestration                              │ │
│  │ Layer 3: execution/*.py (shared across projects)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Tier 2: PROJECTS (Flexible Architecture)                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ directives/[project].md                                    │ │
│  │ projects/[project]/                                        │ │
│  │   ├── src/*.py         (project implementation)           │ │
│  │   ├── workflows/       (documentation)                    │ │
│  │   ├── testing/         (multi-agent tests)                │ │
│  │   ├── demos/           (client outputs)                   │ │
│  │   └── .tmp/            (temporary, not committed)         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                         TESTING
              (Manual → Multi-Agent → Pre-Deploy)
              See: docs/testing-strategy.md
                              ↓
                    deploy_to_skills.py
           (Copies from execution/ + projects/src/)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCTION (-prod repos - Separate Git Repos)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /Users/williammarceaujr./[project]-prod/                       │
│  ├── .git/              (separate repo)                         │
│  ├── README.md          (end-user documentation)                │
│  ├── execution/         (copied shared utilities)               │
│  ├── src/               (copied project code)                   │
│  ├── VERSION            (e.g., "1.2.0")                         │
│  └── CHANGELOG.md       (release notes)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Documentation (Week 1)

**Priority**: HIGH - Prevents future confusion

1. **Update CLAUDE.md**:
   - [ ] Add Two-Tier Architecture section
   - [ ] Clarify execution/ vs projects/src/ usage
   - [ ] Update Development Pipeline diagram
   - [ ] Add decision rules

2. **Create docs/architecture-guide.md**:
   - [ ] Comprehensive architecture explanation
   - [ ] Decision trees for code location
   - [ ] Migration patterns
   - [ ] Best practices

3. **Update testing-strategy.md**:
   - [ ] Confirm testing in projects/src/
   - [ ] Document .tmp/ vs testing/ vs demos/
   - [ ] Update examples

4. **Update SOP 3 (Deployment)**:
   - [ ] Add version management checklist
   - [ ] Document deploy from projects/src/
   - [ ] Update deployment flow diagram

**Estimated Time**: 4-6 hours
**Dependencies**: None
**Output**: All documentation consistent

---

### Phase 2: Code Audit & Reorganization (Week 2)

**Priority**: MEDIUM - Improves organization

5. **Audit execution/ folder**:
   - [ ] List all scripts
   - [ ] Identify shared vs project-specific
   - [ ] Create migration plan
   - [ ] Document findings

6. **Reorganize execution/**:
   - [ ] Move project-specific scripts to projects/
   - [ ] Keep only shared utilities
   - [ ] Update imports in projects
   - [ ] Test all affected projects

7. **Create execution/README.md**:
   - [ ] Document what belongs here
   - [ ] List all shared utilities
   - [ ] Usage examples
   - [ ] Contribution guidelines

**Estimated Time**: 8-12 hours
**Dependencies**: Phase 1 complete
**Output**: Clean code organization

---

### Phase 3: Deployment Updates (Week 3)

**Priority**: MEDIUM - Enables new workflow

8. **Update deploy_to_skills.py**:
   - [ ] Support deploying from projects/[name]/src/
   - [ ] Support deploying from execution/
   - [ ] Handle both patterns automatically
   - [ ] Update project configurations

9. **Test deployment workflow**:
   - [ ] Deploy md-to-pdf from projects/src/
   - [ ] Deploy interview-prep with shared utilities
   - [ ] Verify all files copied correctly
   - [ ] Test deployed skills work

10. **Update deployment documentation**:
    - [ ] Document new deployment paths
    - [ ] Update examples
    - [ ] Add troubleshooting

**Estimated Time**: 6-8 hours
**Dependencies**: Phase 2 complete
**Output**: Deployment supports new architecture

---

### Phase 4: Verification & Cleanup (Week 4)

**Priority**: LOW - Polish and verify

11. **Verify all SOPs consistent**:
    - [ ] Check all cross-references
    - [ ] Verify no contradictions
    - [ ] Update SOP-VERIFICATION.md

12. **Update project READMEs**:
    - [ ] Document new structure
    - [ ] Add migration guides if needed
    - [ ] Update examples

13. **Clean up deprecated patterns**:
    - [ ] Remove old documentation
    - [ ] Archive outdated guides
    - [ ] Update session-history.md

**Estimated Time**: 4-6 hours
**Dependencies**: Phases 1-3 complete
**Output**: Fully consistent, documented architecture

---

## Success Criteria

### Phase 1 (Documentation)
- ✅ All SOPs reference unified architecture
- ✅ No conflicting statements in documentation
- ✅ Clear guidelines for code location

### Phase 2 (Code Organization)
- ✅ execution/ contains only shared utilities
- ✅ All project-specific code in projects/[name]/src/
- ✅ No broken imports

### Phase 3 (Deployment)
- ✅ deploy_to_skills.py works with new structure
- ✅ Can deploy from both execution/ and projects/src/
- ✅ All test deployments successful

### Phase 4 (Verification)
- ✅ SOP-VERIFICATION.md shows all green
- ✅ No TODO items remaining
- ✅ Team can follow architecture without confusion

---

## Risk Mitigation

### Risk 1: Breaking Existing Projects

**Mitigation**:
- Test deployment before reorganizing
- Create migration scripts
- Keep old structure until verified working

### Risk 2: Confusion During Transition

**Mitigation**:
- Update docs FIRST (Phase 1)
- Clear communication in session-history.md
- Document "old vs new" patterns

### Risk 3: deploy_to_skills.py Changes Break Things

**Mitigation**:
- Backup current version
- Test with one project first
- Gradual rollout

---

## Decision Log

| Decision | Date | Rationale |
|----------|------|-----------|
| Hybrid architecture (execution/ + projects/src/) | 2026-01-12 | Best balance of DOE philosophy and project organization |
| Two-tier DOE application | 2026-01-12 | Strict for shared, flexible for projects |
| -prod repos for deployment | 2026-01-12 | Clean git workflow, GitHub-ready |
| Comprehensive versioning (3-way) | 2026-01-12 | Redundancy ensures consistency |
| Separate testing artifacts by purpose | 2026-01-12 | Clear organization, prevents confusion |

---

## Next Steps

1. **Review & Approve**: Get confirmation on all solutions
2. **Begin Phase 1**: Update documentation (4-6 hours)
3. **Schedule Phase 2**: Plan code reorganization
4. **Track Progress**: Update COMPREHENSIVE-CONFLICT-AUDIT.md

---

**Status**: ✅ APPROVED - READY FOR IMPLEMENTATION
**Last Updated**: 2026-01-12
**Next Review**: After Phase 4 completion
