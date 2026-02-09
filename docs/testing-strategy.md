# Testing Strategy: When and How to Test Projects

**Purpose**: Define comprehensive testing strategy across the development-to-deployment pipeline

**Last Updated**: 2026-02-08

**Three-Agent Integration**: Testing scenarios map to the three-agent framework (SOP-29):

| Scenario | Primary Agent | Notes |
|----------|---------------|-------|
| Scenario 1 (Manual) | Claude Code / Clawdbot | Interactive = Claude Code; Simple scripts = Clawdbot |
| Scenario 2 (Multi-Agent) | Ralph + Claude Code | Ralph generates tests; Claude Code orchestrates |
| Scenario 3 (Pre-Deploy) | Claude Code | Requires interactive verification |
| Scenario 4 (Post-Deploy) | Claude Code | Requires Mac for PyPI/MCP verification |

---

## Testing Philosophy

**Core Principle**: Test EARLY and OFTEN in dev-sandbox. Deploy ONLY when stable.

**Complete Pipeline** (Deployment happens at Step 5):
```
Step 1: DEVELOP in dev-sandbox
   ↓
Step 2: Manual Testing (Scenario 1) - ALWAYS REQUIRED - in dev-sandbox
   ↓
Step 3: Multi-Agent Testing (Scenario 2) - OPTIONAL - in dev-sandbox
   ↓
Step 4: Pre-Deployment Verification (Scenario 3) - ALWAYS REQUIRED - in dev-sandbox
   ↓
Step 5: DEPLOY to skills ← First time deployment happens
   ↓
Step 6: Post-Deployment Verification (Scenario 4) - ALWAYS REQUIRED - in -prod repo
```

**CRITICAL TIMING**:
- **NEVER** deploy to skills during Steps 1-4 (development and testing)
- **ALWAYS** complete ALL testing in dev-sandbox BEFORE deploying
- **ONLY** deploy after Pre-Deployment Verification (Scenario 3) passes

**Location Rules**:
- Steps 1-4: Work in `/Users/williammarceaujr./dev-sandbox/projects/[name]/`
- Step 5: Deploy creates `/Users/williammarceaujr./[name]-prod/` (separate repo)
- Step 6: Verify in `/Users/williammarceaujr./[name]-prod/`

**Example Timeline for MD-to-PDF Project**:
```
Monday: Development in dev-sandbox/projects/md-to-pdf/src/
Tuesday: Manual testing (Scenario 1) - test.md → test.pdf
Wednesday: Multi-agent testing setup (Scenario 2) - 4 agents test edge cases
Thursday: Consolidate findings, fix critical issues
Friday: Pre-deployment verification (Scenario 3) - final-test.md → final-test.pdf
Friday EOD: DEPLOY to skills → Creates md-to-pdf-prod/  ← First deployment
Saturday: Post-deployment verification (Scenario 4) - test in production repo
```

**Common Mistake**: Deploying on Tuesday (before testing complete) ❌
**Correct Timing**: Deploying on Friday (after all testing) ✅

---

## Testing Scenarios & When to Use Each

### Scenario 1: Basic Manual Testing (ALWAYS REQUIRED)

**When**: Immediately after implementing core functionality

**Where**: `dev-sandbox/projects/[project]/`

**Purpose**: Verify basic functionality works (happy path)

**Process**:
1. Implement core feature in `src/`
2. Test manually with simple examples
3. Fix any immediate issues
4. Document in workflow if it works

**Example**:
```bash
# After creating md_to_pdf.py
cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf
python src/md_to_pdf.py test.md test.pdf
open test.pdf  # Verify it works
```

**Prerequisites**: None (this IS the first test)

**Success Criteria**:
- ✅ Script runs without crashing
- ✅ Output is generated
- ✅ Output is correct for simple cases
- ✅ Environment dependencies work

**Status Before Next Step**: Core implementation verified, ready for edge case testing

---

### Scenario 2: Multi-Agent Edge Case Testing (OPTIONAL, for complex projects)

**When**: After basic functionality is verified AND you need comprehensive edge case coverage

**Where**: `dev-sandbox/projects/[project]/testing/`

**Purpose**: Find edge cases, boundary conditions, and integration issues

**CRITICAL PREREQUISITES** (verify ALL before proceeding):
1. ✅ **Scenario 1 complete** - Basic manual testing passed
2. ✅ **Core implementation stable** - No crashes on happy path
3. ✅ **Environment working** - All dependencies resolved (libraries, paths, etc.)
4. ✅ **At least 1-2 workflows documented** - Basic usage is understood
5. ✅ **Basic functionality verified** - Tool works for intended purpose

**DO NOT use multi-agent testing if**:
- Implementation is incomplete
- Basic manual tests haven't passed
- Environment has unresolved issues (library paths, missing dependencies)
- You haven't tested it manually yourself first

**Process**:
1. **Reference working example**: Check `email-analyzer/testing/` as template
2. **Create test infrastructure**:
   ```
   projects/[project]/testing/
   ├── TEST-PLAN.md           # Test scenarios for each agent
   ├── AGENT-PROMPTS.txt      # Copy-paste prompts (ABSOLUTE PATHS!)
   ├── START-HERE.md          # Quick launch guide
   ├── agent1/                # Isolated workspace
   ├── agent2/
   ├── agent3/
   ├── agent4/
   └── consolidated-results/
   ```
3. **Launch agents in parallel**: 4 separate Claude instances
4. **Consolidate findings**: Create `CONSOLIDATED-FINDINGS.md`
5. **Fix critical issues**: Address issues in dev-sandbox
6. **Re-test manually**: Verify fixes work

**Example Projects**:
- ✅ **Email Analyzer**: Multi-agent testing found 12 issues before v1.1.0 deployment
- ❌ **MD-to-PDF (first attempt)**: Jumped to multi-agent testing too early, agents crashed on environment issues

**Success Criteria**:
- ✅ All 4 agents complete testing
- ✅ FINDINGS.md documents created
- ✅ Critical issues identified and fixed
- ✅ Manual re-testing confirms fixes work

**Status Before Next Step**: Edge cases tested, critical issues resolved, ready for deployment

**Reference**: CLAUDE.md SOP 2

---

### Scenario 3: Pre-Deployment Verification (ALWAYS REQUIRED)

**When**: Immediately before running `deploy_to_skills.py`

**Where**: `dev-sandbox/projects/[project]/`

**Purpose**: Final confirmation that everything works before deployment

**Prerequisites**:
- ✅ Basic manual testing complete (Scenario 1)
- ✅ Multi-agent testing complete (if applicable, Scenario 2)
- ✅ All known issues fixed
- ✅ Documentation updated

**Process**:
```bash
# From dev-sandbox root
cd /Users/williammarceaujr./dev-sandbox

# Test core functionality
python projects/[project]/src/[script].py [test-input] [test-output]

# Verify output quality
open [test-output]  # Visual inspection

# Test edge cases manually (based on multi-agent findings)
python projects/[project]/src/[script].py [edge-case-input] [output]

# Verify workflows are accurate
# Follow your own workflow docs to ensure they're correct
```

**Checklist**:
- [ ] Core functionality works (happy path)
- [ ] Known edge cases handled
- [ ] No crashes or errors
- [ ] Output quality is production-ready
- [ ] Environment dependencies documented in troubleshooting
- [ ] All workflows tested and accurate

**Success Criteria**:
- ✅ Everything in checklist complete
- ✅ Confident deploying to end users

**Status After**: Ready for deployment

---

### Scenario 4: Post-Deployment Verification (ALWAYS REQUIRED)

**When**: Immediately after `deploy_to_skills.py` completes

**Where**: `/Users/williammarceaujr./[project]-prod/`

**Purpose**: Verify deployment structure AND functionality in production environment

**Why This Matters**: The deployed skills structure is different from dev-sandbox:
- Different directory structure (`execution/` vs `projects/[name]/src/`)
- Different import paths (if applicable)
- Standalone package (no dev-sandbox context)
- This is what Claude skills actually runs

**CRITICAL**: Testing in dev-sandbox tests the code, but post-deployment testing verifies the **deployment process** and **production structure**.

**Process**:
```bash
# 1. Navigate to production repo
cd /Users/williammarceaujr./[project]-prod

# 2. Verify structure
ls -la  # Check files present
cat README.md  # Verify documentation accurate
cat SKILL.md  # Verify skill definition correct

# 3. TEST FUNCTIONALITY in production structure
# This tests the DEPLOYED version, not the dev version
python execution/[script].py [test-input] [test-output]

# 4. Verify output identical to dev-sandbox testing
diff [test-output] /Users/williammarceaujr./dev-sandbox/projects/[project]/.tmp/[test-output]
# Should be identical

# 5. Test any dependencies or imports
# If script imports from execution/, verify those work in prod structure
python -c "from execution.[script] import main; print('Import successful')"

# 6. Check git status
git log  # Verify commit and tag
git tag  # Verify version tag
git status  # Should be clean

# 7. Test skill integration (if MCP skill)
# Verify SKILL.md has correct paths and commands
```

**Deployment Structure Verification Checklist**:
- [ ] Production repo exists at `/Users/williammarceaujr./[project]-prod/`
- [ ] All required files copied correctly
- [ ] `execution/[script].py` runs successfully (same output as dev-sandbox)
- [ ] Import paths work in production structure
- [ ] Dependencies available (no missing imports)
- [ ] Git repository initialized
- [ ] Version tag created (e.g., `v1.0.0`)
- [ ] README.md accurate for end users
- [ ] SKILL.md has correct commands and paths
- [ ] CHANGELOG.md documents this version

**Functional Testing Checklist** (run same tests as Scenario 3):
- [ ] Core functionality works (happy path)
- [ ] Known edge cases handled
- [ ] No crashes or errors
- [ ] Output quality matches dev-sandbox testing
- [ ] All workflows documented in README work

**Success Criteria**:
- ✅ Production repo is self-contained and functional
- ✅ Scripts run identically to dev-sandbox testing
- ✅ No import errors or missing dependencies
- ✅ Documentation accurate
- ✅ Ready to share with end users or push to GitHub

**If Issues Found**:
1. **Import errors**: Update `deploy_to_skills.py` to copy missing dependencies
2. **Path issues**: Update script to handle production structure
3. **Missing files**: Update deployment configuration
4. **Functionality different**: Investigate deployment process (files may have been modified during copy)

**Status After**: Production deployment verified, ready for distribution

---

## Complete Testing Pipeline

### For Simple Projects (no edge cases needed)

```
1. Implement feature in dev-sandbox
2. Manual testing (Scenario 1) ✅
3. Fix any issues
4. Pre-deployment verification (Scenario 3) ✅
5. Deploy: python deploy_to_skills.py --project [name] --version X.Y.Z
6. Post-deployment verification (Scenario 4) ✅
```

**Example**: Simple utility scripts, straightforward converters

---

### For Complex Projects (comprehensive testing needed)

```
1. Implement feature in dev-sandbox
2. Manual testing (Scenario 1) ✅
3. Fix immediate issues
4. Multi-agent edge case testing (Scenario 2) ✅
   - Create testing/TEST-PLAN.md
   - Create testing/AGENT-PROMPTS.txt
   - Launch 4 agents
   - Consolidate findings
5. Fix critical and important issues
6. Manual re-testing of fixes
7. Pre-deployment verification (Scenario 3) ✅
8. Deploy: python deploy_to_skills.py --project [name] --version X.Y.Z
9. Post-deployment verification (Scenario 4) ✅
```

**Example**: Email analyzers, multi-step workflows, projects with many edge cases

---

## Decision Tree: Do I Need Multi-Agent Testing?

```
START: I just implemented a feature
│
├─ Is this a simple, straightforward tool?
│  └─ YES → Skip to Pre-Deployment Verification (Scenario 3)
│
└─ Is this complex with multiple edge cases?
   │
   ├─ Did I complete manual testing (Scenario 1)?
   │  ├─ NO → Do manual testing FIRST
   │  └─ YES → Continue
   │
   ├─ Did I resolve environment issues?
   │  ├─ NO → Fix environment FIRST
   │  └─ YES → Continue
   │
   ├─ Do I have 1-2 workflows documented?
   │  ├─ NO → Document basic workflows FIRST
   │  └─ YES → Continue
   │
   └─ ALL CLEAR → Proceed with Multi-Agent Testing (Scenario 2)
```

---

## Common Mistakes & How to Avoid

### Mistake 1: Jumping to Multi-Agent Testing Too Early

**Symptoms**:
- Agents crash immediately
- Basic functionality doesn't work
- Environment issues block testing

**Prevention**:
- ✅ Always do manual testing first (Scenario 1)
- ✅ Verify prerequisites before multi-agent testing
- ✅ Check `email-analyzer/testing/` as reference

**Fix**:
- Go back to manual testing
- Fix environment issues
- Verify basic functionality
- THEN try multi-agent testing

**Reference**: `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`

---

### Mistake 2: Deploying Before Testing

**Symptoms**:
- Production repo doesn't work
- End users report immediate issues
- Have to rollback deployment

**Prevention**:
- ✅ Follow testing pipeline completely
- ✅ Use pre-deployment verification checklist
- ✅ Never skip manual testing

**Fix**:
- Don't deploy yet
- Return to dev-sandbox
- Complete testing scenarios
- Then deploy

---

### Mistake 3: Testing in Production Instead of Dev-Sandbox

**Symptoms**:
- Making changes directly to `-prod` repo
- Losing development history
- Can't iterate quickly

**Prevention**:
- ✅ ALL testing happens in dev-sandbox
- ✅ Production is deployment target ONLY
- ✅ Never develop in production repo

**Fix**:
- Return to dev-sandbox
- Port changes back if needed
- Test in dev-sandbox
- Re-deploy when ready

---

## Testing Environment Setup

### Required for All Testing

**Location**: `/Users/williammarceaujr./dev-sandbox/projects/[project]/`

**Structure**:
```
projects/[project]/
├── src/                    # Project-specific scripts to test
├── workflows/              # How to use it
├── .tmp/                   # Temporary test outputs
└── testing/                # Multi-agent testing (if needed)
```

**Architecture Note**:
- Test **project-specific code** in `projects/[project]/src/`
- Test **shared utilities** separately in `execution/` (used as dependencies)
- See: [architecture-guide.md](architecture-guide.md) for code organization

**Environment**:
- All dependencies installed
- Library paths configured (use wrapper scripts if needed)
- Test data available
- Shared utilities from `execution/` accessible (import path configured)

---

### Optional: Multi-Agent Testing Setup

**Additional structure**:
```
projects/[project]/testing/
├── TEST-PLAN.md            # Scenarios for each agent
├── AGENT-PROMPTS.txt       # Copy-paste prompts
├── START-HERE.md           # Launch instructions
├── agent1/                 # Workspace (absolute path in prompts!)
├── agent2/
├── agent3/
├── agent4/
└── consolidated-results/   # Merged findings
    └── CONSOLIDATED-FINDINGS.md
```

**Critical**:
- Use **absolute paths** in AGENT-PROMPTS.txt
- Reference `email-analyzer/testing/` as template
- Include exact commands with full paths
- Create wrapper scripts for environment variables

---

## Testing Artifacts & Where They Live

| Artifact | Location | Committed To | When Created |
|----------|----------|--------------|--------------|
| Test scripts (manual) | `projects/[project]/.tmp/` | ❌ Not tracked | During Scenario 1 |
| Test outputs | `projects/[project]/.tmp/` | ❌ Not tracked | During testing |
| Test plan | `projects/[project]/testing/TEST-PLAN.md` | ✅ dev-sandbox | Before Scenario 2 |
| Agent prompts | `projects/[project]/testing/AGENT-PROMPTS.txt` | ✅ dev-sandbox | Before Scenario 2 |
| Agent findings | `projects/[project]/testing/agent[N]/FINDINGS.md` | ✅ dev-sandbox | During Scenario 2 |
| Consolidated findings | `projects/[project]/testing/consolidated-results/` | ✅ dev-sandbox | After Scenario 2 |
| Demo outputs (client) | `projects/[project]/demos/client-[name]/` | ⚠️ Optional | When needed |
| Issue resolution docs | `projects/[project]/testing/TESTING-ISSUES-RESOLVED.md` | ✅ dev-sandbox | If testing fails |

---

## Integration with Two-Tier Architecture

**Two-Tier System** (see [architecture-guide.md](architecture-guide.md)):

**Tier 1: Shared Utilities (Strict DOE)**:
```
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py) ← Shared across projects
```

**Tier 2: Projects (Flexible Architecture)**:
```
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py) ← Project-specific
```

**Testing fits in**:
```
1. Write Directive (Layer 1)
2. Implement Code (Layer 3: execution/ or projects/[name]/src/)
3. TEST in dev-sandbox ← You are here
   - Test project code in projects/[name]/src/
   - Shared utilities from execution/ are dependencies
4. Deploy when stable
```

**Architecture Rule**: Don't deploy without directive AND testing (applies to both tiers)

---

## Summary: Testing Decision Matrix

| Question | Answer | Action |
|----------|--------|--------|
| Just wrote new code? | - | Manual test it (Scenario 1) |
| Does it work for simple cases? | NO | Fix bugs, re-test |
| Does it work for simple cases? | YES | Document in workflow |
| Is this a complex project? | NO | Pre-deployment verification (Scenario 3) |
| Is this a complex project? | YES | Check prerequisites for Scenario 2 |
| Prerequisites met for multi-agent? | NO | Complete prerequisites first |
| Prerequisites met for multi-agent? | YES | Set up multi-agent testing (Scenario 2) |
| Multi-agent testing complete? | - | Fix issues, re-test manually |
| All issues resolved? | YES | Pre-deployment verification (Scenario 3) |
| Pre-deployment checks pass? | YES | Deploy to production |
| Deployed successfully? | - | Post-deployment verification (Scenario 4) |

---

## Related Documentation

- [CLAUDE.md SOP 1](../CLAUDE.md#sop-1-new-project-initialization) - Project setup
- [CLAUDE.md SOP 2](../CLAUDE.md#sop-2-multi-agent-testing) - Multi-agent testing
- [Development to Deployment](development-to-deployment.md) - Complete pipeline
- [Email Analyzer Testing](../email-analyzer/testing/TEST-PLAN.md) - Successful example
- [MD-to-PDF Testing Issues](../projects/md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md) - Lessons learned

---

**Principle**: Test in dev-sandbox. Deploy when stable. Never deploy untested code.
