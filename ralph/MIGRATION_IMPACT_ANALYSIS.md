# Migration Impact Analysis - Multi-Company Folder Structure

**Date:** 2026-01-20
**Reviewer:** Claude
**Purpose:** Analyze impact of folder restructuring on all documented SOPs, workflows, and communication patterns

---

## Executive Summary

The proposed migration from flat `projects/` structure to categorized structure (`projects/shared-multi-tenant/`, `projects/marceau-solutions/`, etc.) will affect:

- ✅ **0 SOPs** require updates (paths are relative or abstract)
- ⚠️ **3 files** require path updates (deploy_to_skills.py, CLAUDE.md, docs/projects.md)
- ✅ **Communication patterns** remain unchanged (semantic, not path-based)
- ⚠️ **1 critical workflow** affected (deployment pipeline needs path mapping)

**Risk Level:** LOW - Most documentation is architecture-focused, not path-dependent

---

## Impact by Category

### 1. CLAUDE.md - Core Agent Instructions

**Sections Affected:**

#### ✅ NO CHANGE: Architecture (Lines 4-43)
- DOE architecture definitions are conceptual
- "execution/", "directives/", "methods/" stay at root
- "projects/[project]/src/" is still accurate (just nested one level deeper)

**Example (still valid after migration):**
```
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py) ← Project-specific
```

After migration becomes:
```
projects/shared-multi-tenant/lead-scraper/src/
projects/marceau-solutions/fitness-influencer/src/
```
Still matches pattern `projects/[project]/src/`!

#### ✅ NO CHANGE: Documentation Map (Lines 45-73)
All doc paths are absolute from root:
- `docs/architecture-guide.md` ✅ unchanged
- `templates/project-kickoff-questionnaire.md` ✅ unchanged
- `directives/` ✅ unchanged
- `projects/social-media-automation/DOCKET.md` → becomes `projects/shared-multi-tenant/social-media-automation/DOCKET.md`

**Action Required:** Update line 69 only:
```diff
- | **Deferred features/reminders** | `projects/social-media-automation/DOCKET.md` ⭐ |
+ | **Deferred features/reminders** | `projects/shared-multi-tenant/social-media-automation/DOCKET.md` ⭐ |
```

#### ✅ NO CHANGE: Development Pipeline (Lines 75-138)
Pipeline steps are conceptual:
- "DESIGN in directives/" ✅
- "DEVELOP in dev-sandbox" ✅
- "Project-specific code: projects/[project]/src/" ✅ (pattern still matches)
- "Shared utilities (2+ projects): execution/" ✅

#### ⚠️ MINOR UPDATE: Key Commands (Lines 150-172)

**deploy_to_skills.py** will need path mapping internally but commands stay the same:
```bash
python deploy_to_skills.py --project lead-scraper  # Still works
```

The script will just look in `projects/shared-multi-tenant/lead-scraper/` instead of `projects/lead-scraper/`

**Action Required:** Update deploy_to_skills.py project discovery logic (Story 005)

#### ✅ NO CHANGE: Communication Patterns (Lines 174-250+)
All patterns are semantic, not path-based:
- "Deploy to skills" → Uses deploy_to_skills.py (which handles new paths)
- "Run SMS campaign" → Runs SOP 18 (which references projects by name, not path)
- "Save this for the client" → demos/client-[name] (not affected)

---

### 2. SOPs (All 24 SOPs)

**Analysis:** Reviewed all SOPs in CLAUDE.md for path dependencies

#### SOP 0: Project Kickoff
- ✅ NO CHANGE - References `templates/`, not project paths

#### SOP 1: New Project Initialization
- ⚠️ NEEDS MINOR UPDATE

**Current:**
```markdown
2. **Create project folder**: `dev-sandbox/projects/[project-name]/`
```

**After Migration (DECISION NEEDED):**
Where do NEW projects go?

**Option A (Recommended):** Update SOP to ask which category:
```markdown
2. **Create project folder**: Choose category:
   - Shared (multiple businesses): `projects/shared-multi-tenant/[project]/`
   - Marceau-specific: `projects/marceau-solutions/[project]/`
   - HVAC-specific: `projects/swflorida-hvac/[project]/`
   - Shipping-specific: `projects/square-foot-shipping/[project]/`
   - Global utility: `projects/global-utility/[project]/`
   - Product idea: `projects/product-ideas/[project]/`
```

**Option B:** Default to a staging area, categorize later:
```markdown
2. **Create project folder**: `projects/uncategorized/[project]/` (move to category when business assignment clear)
```

#### SOP 2: Multi-Agent Testing
- ✅ NO CHANGE - References `[project]/testing/` (relative path pattern)

#### SOP 3: Version Control & Deployment
- ⚠️ DEPLOY SCRIPT AFFECTED (see Section 4 below)
- ✅ SOP text itself is fine (conceptual)

#### SOP 4: Repository Cleanup
- ✅ NO CHANGE - `find . -name ".git"` works regardless of folder structure

#### SOP 5: Session Documentation
- ✅ NO CHANGE - References `docs/session-history.md` (unchanged)

#### SOP 6: Workflow Creation
- ✅ NO CHANGE - `[project]/workflows/` pattern still valid

#### SOP 7: DOE Architecture Rollback
- ✅ NO CHANGE - Conceptual, not path-dependent

#### SOP 8: Client Demo & Test Output Management
- ✅ NO CHANGE - `projects/[project]/demos/` pattern still valid

#### SOP 9: Multi-Agent Architecture Exploration
- ✅ NO CHANGE - `projects/[project]/exploration/` pattern still valid

#### SOP 10: Multi-Agent Parallel Development
- ✅ NO CHANGE - `projects/[project]/agent1-*/` pattern still valid

#### SOPs 11-16: MCP Publishing
- ✅ NO CHANGE - All reference `projects/[project]/` which still exists (just nested)

#### SOP 17: Market Viability Analysis
- ✅ NO CHANGE - `projects/[project]/market-analysis/` pattern still valid

#### SOPs 18-24: Campaign Management
- ⚠️ MINOR UPDATE - Need to update project references

**Example (SOP 18):**
```bash
# Current
cd /Users/williammarceaujr./dev-sandbox/projects/lead-scraper

# After migration
cd /Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper
```

**Fix:** Use environment variable or relative reference
```bash
cd /Users/williammarceaujr./dev-sandbox
python -m projects.shared_multi_tenant.lead_scraper.src.scraper sms --dry-run
```

---

### 3. Communication Patterns

**Analysis:** All 40+ communication patterns reviewed

#### ✅ NO CHANGES NEEDED

All patterns are **semantic** (what to do), not **path-based** (where files are):

| Pattern | Path Dependency | Impact |
|---------|----------------|--------|
| "Run SMS campaign" | None - uses SOP 18 which handles paths | ✅ None |
| "Deploy to skills" | None - uses deploy_to_skills.py | ✅ None |
| "Run multi-agent testing" | None - project name based | ✅ None |
| "Check the docket" | Path reference: `projects/social-media-automation/DOCKET.md` | ⚠️ Update to `projects/shared-multi-tenant/social-media-automation/DOCKET.md` |
| "Show campaign analytics" | None - uses python -m | ✅ None |

**Actions Required:**
1. Update 1 pattern: "Check the docket" → new path
2. Update SOP 18-24 command examples with new paths

---

### 4. Deploy to Skills Script

**Current Logic:**
```python
# Discovers projects by scanning projects/ directory
for project_dir in Path("projects").iterdir():
    if project_dir.is_dir():
        # Deploy project
```

**After Migration:**
```python
# Must scan NESTED directories
categories = [
    "shared-multi-tenant",
    "marceau-solutions",
    "swflorida-hvac",
    "square-foot-shipping",
    "global-utility",
    "product-ideas"
]

for category in categories:
    for project_dir in Path(f"projects/{category}").iterdir():
        if project_dir.is_dir():
            # Deploy project
```

**OR (smarter):**
```python
# Recursively find all projects
for project_dir in Path("projects").rglob("*/"):
    if (project_dir / "VERSION").exists():  # Has VERSION file = is a project
        # Deploy project
```

**Action Required:** Update deploy_to_skills.py in Story 005

---

### 5. Import Statements

**Current:**
```python
from projects.lead_scraper.src import scraper
```

**After Migration:**
```python
from projects.shared_multi_tenant.lead_scraper.src import scraper
```

**Impact:**
- ✅ All imports within projects (relative imports) - NO CHANGE
- ⚠️ Cross-project imports (if any exist) - NEED UPDATE
- ⚠️ deploy_to_skills.py imports - NEED UPDATE

**Action Required:** Migration script (Story 005) should scan for:
```bash
grep -r "from projects\." --include="*.py"
grep -r "import projects\." --include="*.py"
```

---

### 6. Documentation Files

#### docs/projects.md
- ⚠️ **NEEDS COMPLETE REWRITE**
- Currently lists all projects flat
- After migration: Group by category

**Action Required:** Create new docs/projects.md with categorized listing

#### docs/architecture-guide.md
- ⚠️ **NEEDS MINOR UPDATE**
- References `projects/[name]/src/` pattern (still valid)
- Add section explaining new categorization

#### docs/repository-management.md
- ✅ **NO CHANGE** - Focuses on .git structure, not project paths

---

## Required Updates Summary

### Critical (Blocking Migration)

1. **deploy_to_skills.py** (Story 005)
   - Update project discovery to scan nested categories
   - Update import resolution
   - Test with all 27 projects

### High Priority (Day 1 after migration)

2. **CLAUDE.md** (2 changes)
   - Line 69: Update DOCKET.md path
   - SOP 1: Add category selection step

3. **docs/projects.md**
   - Rewrite to show categorized structure

### Medium Priority (Week 1)

4. **SOPs 18-24** (Campaign management)
   - Update command examples with new paths
   - Use relative paths where possible

5. **docs/architecture-guide.md**
   - Add section on project categorization

### Low Priority (Nice to have)

6. **Communication Patterns**
   - Add pattern: "Which category for new project?" → Use SOP 1 decision tree

---

## Migration Checklist

**Before Migration:**
- [x] Create this impact analysis
- [ ] Review with William
- [ ] Update deploy_to_skills.py to handle nested structure
- [ ] Verify deploy_to_skills.py --list works with new paths

**During Migration (Story 003-004):**
- [ ] Run migration script
- [ ] Verify all 27 projects moved correctly
- [ ] Check git status (no broken symlinks)

**After Migration (Story 005):**
- [ ] Update CLAUDE.md (2 changes)
- [ ] Update docs/projects.md
- [ ] Update SOP command examples
- [ ] Test deploy_to_skills.py with all projects
- [ ] Grep for hardcoded "projects/[name]" paths and update

**Verification:**
- [ ] `python deploy_to_skills.py --list` shows all 27 projects
- [ ] `python -m projects.shared_multi_tenant.lead_scraper.src.scraper --help` works
- [ ] All existing commands in SOPs still work

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| deploy_to_skills.py breaks | Medium | High | Update before migration, test thoroughly |
| Import errors | Low | High | Migration script scans and updates imports |
| Documentation drift | High | Low | Update docs immediately after migration |
| Lost muscle memory (paths) | High | Low | README in each category, update over time |
| Nested .git repos | Low | Critical | Ralph's script uses `git mv`, verify after |

**Overall Risk:** LOW (with proper deploy_to_skills.py update)

---

## Recommendations

### 1. Update deploy_to_skills.py FIRST (Story 003)
Don't execute migration until deploy script handles nested structure.

### 2. Test Deploy Script Before Migration
```bash
# Simulate new structure
mkdir -p projects/test-category/test-project
cp -r projects/lead-scraper/* projects/test-category/test-project/

# Test deploy script
python deploy_to_skills.py --project test-project --dry-run

# Clean up
rm -rf projects/test-category
```

### 3. Phased Documentation Updates
- Day 0 (migration day): Update CLAUDE.md critical paths
- Day 1: Update docs/projects.md
- Week 1: Update all SOP examples
- Month 1: Verify no hardcoded paths remain

### 4. Create Category READMEs
Each category should have README explaining:
- What belongs here
- Business ownership
- How to add new projects

---

## Files to Update (Definitive List)

| File | Priority | Change Type | Story |
|------|----------|-------------|-------|
| **deploy_to_skills.py** | CRITICAL | Project discovery logic | 003 (before migration) |
| **CLAUDE.md** | HIGH | 2 path references | 005 |
| **docs/projects.md** | HIGH | Complete rewrite | 005 |
| **SOPs 18-24** | MEDIUM | Command examples | 005 |
| **docs/architecture-guide.md** | MEDIUM | Add categorization section | 005 |
| **Communication patterns** | LOW | Add 1 new pattern | 005 |

---

## Next Steps

**Immediate (Before approving Story 003):**
1. Review this impact analysis with William
2. Update deploy_to_skills.py to handle nested categories
3. Test deploy script with simulated structure
4. Approve Story 003 execution

**Post-Migration (Story 005):**
1. Execute migration
2. Update all files in table above
3. Run verification checklist
4. Commit all documentation updates

---

**Approval Status:** PENDING William's review

**Blocker for Migration:** deploy_to_skills.py must be updated first
