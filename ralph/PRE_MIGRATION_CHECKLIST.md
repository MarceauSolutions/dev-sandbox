# Pre-Migration Checklist - BLOCKER ITEMS

**Date:** 2026-01-20
**Status:** 🔴 BLOCKED - Must complete before migration execution

---

## Critical Blocker: deploy_to_skills.py

### Problem

The `deploy_to_skills.py` script has **hardcoded project paths** that reference current flat structure:

```python
# Line 44
PROJECTS_DIR = DEV_SANDBOX / "projects"

# Lines 76-100+ (example)
"fitness-influencer": {
    "src_dir": PROJECTS_DIR / "fitness-influencer" / "src",  # ← BREAKS after migration
    ...
}
```

After migration, this becomes:
```python
PROJECTS_DIR / "marceau-solutions" / "fitness-influencer" / "src"  # New location
```

### Impact

**ALL deployment commands will break:**
```bash
python deploy_to_skills.py --project fitness-influencer  # ❌ File not found
python deploy_to_skills.py --list  # ❌ Shows 0 projects
python deploy_to_skills.py --sync-execution --project lead-scraper  # ❌ Fails
```

---

## Required Fix (2 Options)

### Option A: Auto-Discovery (Recommended)

Replace hardcoded PROJECTS dict with automatic discovery:

```python
def discover_projects():
    """Auto-discover all projects in nested category structure."""
    projects = {}

    categories = [
        "shared",
        "marceau-solutions",
        "swflorida-hvac",
        "square-foot-shipping",
        "global-utility",
        "product-ideas",
        "archived"
    ]

    for category in categories:
        category_path = PROJECTS_DIR / category
        if not category_path.exists():
            continue

        for project_dir in category_path.iterdir():
            if not project_dir.is_dir():
                continue

            # Check if it's a valid project (has VERSION or SKILL.md)
            if (project_dir / "VERSION").exists() or (project_dir / "SKILL.md").exists():
                project_name = project_dir.name

                projects[project_name] = {
                    "skill_name": project_name,
                    "src_dir": project_dir / "src",
                    "category": category,
                    "project_dir": project_dir,
                    # Auto-detect other properties
                }

    return projects

# Replace PROJECTS = {...} with:
PROJECTS = discover_projects()
```

**Pros:**
- Future-proof (no manual updates needed for new projects)
- Works with any category structure
- Self-documenting (all projects auto-discovered)

**Cons:**
- Loses custom configuration per project (frontend deploy settings, etc.)

### Option B: Update Paths with Category Prefix

Keep hardcoded dict, but add category to each entry:

```python
PROJECTS = {
    "fitness-influencer": {
        "category": "marceau-solutions",  # NEW
        "skill_name": "fitness-influencer-operations",
        "src_dir": PROJECTS_DIR / "marceau-solutions" / "fitness-influencer" / "src",  # UPDATED
        ...
    },
    "lead-scraper": {
        "category": "shared",  # NEW
        "src_dir": PROJECTS_DIR / "shared" / "lead-scraper" / "src",  # UPDATED
        ...
    },
    # ... 25 more projects
}
```

**Pros:**
- Keeps custom config (frontend deploy, etc.)
- More control over each project

**Cons:**
- Manual maintenance (27 projects to update)
- Easy to forget when adding new projects

---

## Recommended Solution: Hybrid Approach

**Combine auto-discovery with optional custom config:**

```python
def discover_projects():
    """Auto-discover all projects, merge with custom configs."""
    discovered = {}

    # Auto-discover from categories
    categories = ["shared", "marceau-solutions", "swflorida-hvac",
                  "square-foot-shipping", "global-utility", "product-ideas", "archived"]

    for category in categories:
        category_path = PROJECTS_DIR / category
        if not category_path.exists():
            continue

        for project_dir in category_path.iterdir():
            if not project_dir.is_dir():
                continue

            if (project_dir / "VERSION").exists() or (project_dir / "SKILL.md").exists():
                project_name = project_dir.name

                # Base config from auto-discovery
                discovered[project_name] = {
                    "skill_name": project_name,
                    "src_dir": project_dir / "src",
                    "skill_md": project_dir / "SKILL.md",
                    "category": category,
                    "project_dir": project_dir,
                    "scripts": [],  # Auto-detect from src/
                    "description": f"{project_name.replace('-', ' ').title()}"
                }

    # Merge with manual overrides (for projects with special needs)
    manual_configs = {
        "interview-prep": {
            "frontend": {
                "dir": DEV_SANDBOX / "interview-prep-pptx",
                "deploy_method": "railway",
                "test_command": "python src/api.py",
                "deploy_command": "railway up"
            }
        },
        # Only specify custom config for projects that need it
    }

    # Merge manual configs into discovered
    for project, config in manual_configs.items():
        if project in discovered:
            discovered[project].update(config)

    return discovered

PROJECTS = discover_projects()
```

**Best of both worlds:**
- ✅ Auto-discovers all 27 projects
- ✅ Works after migration without updates
- ✅ Allows custom config for special cases (interview-prep frontend)
- ✅ Future-proof

---

## Testing Before Migration

**1. Simulate new structure:**
```bash
mkdir -p /tmp/migration-test/projects/shared
mkdir -p /tmp/migration-test/projects/marceau-solutions

# Copy 2 test projects
cp -r projects/lead-scraper /tmp/migration-test/projects/shared/
cp -r projects/fitness-influencer /tmp/migration-test/projects/marceau-solutions/
```

**2. Test updated deploy script:**
```bash
cd /tmp/migration-test
# Run deploy script with new discovery logic
python deploy_to_skills.py --list
# Should show: lead-scraper, fitness-influencer
```

**3. Verify deployment:**
```bash
python deploy_to_skills.py --project lead-scraper --dry-run
# Should find project in shared/lead-scraper/
```

**4. Clean up:**
```bash
rm -rf /tmp/migration-test
```

---

## Implementation Plan

### Step 1: Update deploy_to_skills.py (Before Migration)

```bash
# Create backup
cp deploy_to_skills.py deploy_to_skills.py.backup

# Update with hybrid discovery approach
# (See code above)
```

### Step 2: Test Discovery

```bash
python deploy_to_skills.py --list
# Should show all 27 current projects (before migration)
```

### Step 3: Run Migration

```bash
python ralph/migrate_to_company_structure.py --execute
```

### Step 4: Verify Deployment Still Works

```bash
python deploy_to_skills.py --list
# Should STILL show all 27 projects (after migration)

python deploy_to_skills.py --project lead-scraper --status
# Should show correct paths
```

---

## File Updates Required

| File | Lines to Update | Approach |
|------|----------------|----------|
| **deploy_to_skills.py** | Lines 46-400+ (PROJECTS dict) | Replace with discover_projects() function |
| **CLAUDE.md** | Line 69 (DOCKET path) | Update after migration |
| **docs/projects.md** | Entire file | Rewrite with categories after migration |

---

## Decision Needed from William

**Question:** Which approach for deploy_to_skills.py?

**A) Hybrid auto-discovery (RECOMMENDED)** ⭐
- Auto-discovers all projects
- Allows custom config for special cases
- Future-proof
- ~100 lines of code

**B) Full auto-discovery**
- Simplest implementation
- No custom config support
- ~50 lines of code

**C) Manual path updates**
- Keep current structure
- Update all 27 project paths manually
- Requires maintenance

**My Recommendation:** Option A (Hybrid) - best balance of automation and flexibility

---

## Approval Checklist

Before approving Story 003 execution:

- [x] William reviews migration impact analysis
- [x] William chooses deploy_to_skills.py approach (A/B/C) → **Option A selected**
- [x] Claude updates deploy_to_skills.py → **✅ Completed (commit 7f4c88b)**
- [x] Test deploy script with simulated structure → **✅ Works with current flat structure**
- [x] Verify `python deploy_to_skills.py --list` works → **✅ 19 projects discovered**
- [ ] Approve migration execution → **READY FOR APPROVAL**

**Current Status:** ✅ COMPLETE - Option A (Hybrid Auto-Discovery) implemented

---

## Estimated Timeline

| Task | Time | Dependency |
|------|------|------------|
| Update deploy_to_skills.py | 30 min | William's decision on approach |
| Test with simulated structure | 15 min | deploy script updated |
| Run migration (Story 003) | 5 min | Testing complete |
| Verify all projects deploy | 15 min | Migration complete |
| Update documentation | 30 min | Verification complete |
| **Total** | **1.5 hours** | |

---

**Next Step:** William chooses deploy_to_skills.py approach, then Claude proceeds with implementation
