# Execution Folder: Shared Utilities Only

**Purpose**: This folder contains **shared utility scripts** used by **2 or more projects**. Project-specific code belongs in `projects/[name]/src/`.

**Last Updated**: 2026-01-12

---

## What Belongs in execution/

### ✅ Shared Utilities (2+ Projects)

Scripts that are used by **multiple projects** and provide **reusable functionality**:

- API clients used by multiple projects (e.g., `gmail_monitor.py`, `twilio_sms.py`)
- Common utilities used across projects (e.g., `grok_image_gen.py`, `markdown_to_pdf.py`)
- Cross-project analytics (e.g., `revenue_analytics.py`)
- Shared PDF generation (e.g., `pdf_outputs.py`)

**Current Shared Utilities** (as of 2026-01-12):

| Script | Used By Projects | Purpose |
|--------|-----------------|---------|
| `gmail_monitor.py` | fitness-influencer, amazon-seller, personal-assistant | Gmail monitoring and alerts |
| `grok_image_gen.py` | interview-prep, fitness-influencer, personal-assistant | AI image generation via Grok |
| `twilio_sms.py` | fitness-influencer, amazon-seller, personal-assistant | SMS notifications via Twilio |
| `revenue_analytics.py` | fitness-influencer, amazon-seller | Revenue tracking and analytics |
| `markdown_to_pdf.py` | naples-weather, md-to-pdf | Markdown to PDF conversion |
| `pdf_outputs.py` | interview-prep, (other projects) | PDF generation utilities |

---

## What Does NOT Belong in execution/

### ❌ Project-Specific Scripts (1 Project Only)

If a script is used by **only one project**, it belongs in that project's `src/` folder:

**Examples of scripts that should NOT be here**:
- `interview_research.py` → Move to `projects/interview-prep/src/`
- `amazon_sp_api.py` → Move to `projects/amazon-seller/src/`
- `video_jumpcut.py` → Move to `projects/fitness-influencer/src/`
- `fetch_naples_weather.py` → Move to `projects/naples-weather/src/`

**Rule**: If removing the script would only affect **one project**, it doesn't belong in `execution/`.

---

## Decision Tree: Where to Put Code

```
START: I just wrote a new script
│
├─ Is this used by 2+ projects?
│  │
│  ├─ YES → Put in execution/
│  │        ✅ Example: gmail_monitor.py (used by fitness, amazon, personal-assistant)
│  │
│  └─ NO → Is this used by 1 project only?
│           │
│           ├─ YES → Put in projects/[name]/src/
│           │        ✅ Example: interview_research.py (only interview-prep)
│           │
│           └─ UNSURE → Put in projects/[name]/src/ first
│                       You can always promote to execution/ later if other projects use it
```

**Principle**: When in doubt, start in `projects/[name]/src/`. Promote to `execution/` when a **second project** needs it.

---

## How to Promote a Script to Shared Utility

**Scenario**: You wrote a script in `projects/project-a/src/utils.py` and now `project-b` needs it too.

**Steps**:

1. **Move to execution/**:
   ```bash
   mv projects/project-a/src/utils.py execution/utils.py
   ```

2. **Update import paths in both projects**:
   ```python
   # Before (in project-a)
   from src.utils import helper_function

   # After (in both project-a and project-b)
   import sys
   from pathlib import Path
   sys.path.append(str(Path(__file__).parent.parent.parent / "execution"))
   from utils import helper_function
   ```

3. **Update deployment configs** in `deploy_to_skills.py`:
   ```python
   "project-a": {
       "shared_utils": ["utils.py"],  # NEW: Declare shared dependency
       "scripts": [...]
   }
   ```

4. **Document in this README**:
   - Add to "Current Shared Utilities" table
   - Update "Used By Projects" column

5. **Test both projects** to ensure imports work

---

## How to Demote a Script to Project-Specific

**Scenario**: A script in `execution/` is only used by one project now.

**Steps**:

1. **Verify usage**: Check all projects in `deploy_to_skills.py`
   ```bash
   grep -r "import script_name" projects/*/src/
   # Should only show ONE project
   ```

2. **Move to project folder**:
   ```bash
   mv execution/script_name.py projects/[project]/src/
   ```

3. **Update import paths in project**:
   ```python
   # Before
   from execution.script_name import function

   # After
   from src.script_name import function
   ```

4. **Update deployment config** in `deploy_to_skills.py`:
   ```python
   "project-name": {
       "scripts": ["script_name.py", ...],  # Add to project scripts
       "shared_utils": [...],  # Remove from shared_utils if present
   }
   ```

5. **Remove from this README**:
   - Delete from "Current Shared Utilities" table

6. **Test project** to ensure imports work

---

## Architecture Context

This folder is part of the **Two-Tier Architecture** system:

### Tier 1: Shared Utilities (Strict DOE)

```
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py) ← This folder
```

**Purpose**: Reusable, stable utilities shared across multiple projects

**Rules**:
- Must be used by 2+ projects
- Should have stable, well-defined APIs
- Changes affect multiple projects (test all dependents!)

### Tier 2: Projects (Flexible Architecture)

```
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py)
```

**Purpose**: Project-specific logic and workflows

**See**: [docs/architecture-guide.md](../docs/architecture-guide.md) for complete architecture documentation

---

## Common Mistakes

### Mistake 1: Putting Project Code in execution/

**Symptom**: `execution/` has 60+ scripts, most used by single projects

**Problem**: Violates separation of concerns, makes it hard to find shared utilities

**Fix**: Move project-specific scripts to `projects/[name]/src/`

**Reference**: See [EXECUTION-FOLDER-AUDIT.md](../docs/EXECUTION-FOLDER-AUDIT.md) for migration plan

---

### Mistake 2: Creating Shared Utility Too Early

**Symptom**: Script in `execution/` is only used by one project

**Problem**: Premature abstraction, harder to iterate

**Fix**: Start in `projects/[name]/src/`, promote when **second project** needs it

**Principle**: **YAGNI** (You Aren't Gonna Need It) - Don't make it shared until you actually need it shared

---

### Mistake 3: Not Testing All Dependents After Changes

**Symptom**: Change a shared utility, breaks multiple projects

**Problem**: Shared utilities have multiple consumers

**Fix**: Before deploying changes to shared utility, test **all projects** that use it:

```bash
# Example: Testing changes to gmail_monitor.py
cd projects/fitness-influencer && python src/test.py  # Test project 1
cd projects/amazon-seller && python src/test.py      # Test project 2
cd projects/personal-assistant && python src/test.py # Test project 3

# ALL must pass before deploying gmail_monitor.py changes
```

---

## Deployment Impact

### How Shared Utilities Are Deployed

**Deploy Script**: `deploy_to_skills.py`

**Process**:
1. Project deployment copies from `projects/[name]/src/`
2. Shared utilities copied from `execution/` based on `shared_utils` config
3. Both end up in `[project]-prod/execution/`

**Example**:
```python
# deploy_to_skills.py configuration
"interview-prep": {
    "src_dir": PROJECTS_DIR / "interview-prep" / "src",  # Project code
    "shared_utils": ["gmail_monitor.py", "grok_image_gen.py"],  # Shared deps
    "scripts": [
        "interview_research.py",  # From projects/interview-prep/src/
        "pptx_generator.py",
        # ...
    ]
}
```

**Result**:
```
interview-prep-prod/
├── execution/
│   ├── interview_research.py  ← From projects/interview-prep/src/
│   ├── pptx_generator.py      ← From projects/interview-prep/src/
│   ├── gmail_monitor.py       ← From execution/ (shared)
│   └── grok_image_gen.py      ← From execution/ (shared)
└── README.md
```

---

## Guidelines for New Scripts

### Before Creating a New Script

**Ask yourself**:

1. **Is this project-specific or shared?**
   - If unsure, start in `projects/[name]/src/`

2. **Does a similar utility already exist?**
   - Check `execution/` for existing shared utilities
   - Check other projects for similar functionality

3. **Will this be used by multiple projects?**
   - If NO → Create in `projects/[name]/src/`
   - If YES → Create in `execution/`
   - If MAYBE → Create in `projects/[name]/src/`, promote later if needed

### Script Naming Conventions

**Shared utilities should have generic names**:
- ✅ `gmail_monitor.py` (generic, reusable)
- ❌ `interview_gmail_checker.py` (project-specific name)

**Project-specific scripts can have specific names**:
- ✅ `interview_research.py` (in projects/interview-prep/src/)
- ✅ `amazon_inventory_optimizer.py` (in projects/amazon-seller/src/)

---

## Maintenance

### Weekly Audit

Run this check weekly to prevent clutter:

```bash
# Check how many scripts in execution/
cd /Users/williammarceaujr./dev-sandbox/execution
ls -1 *.py | wc -l
# Should be ~6 (shared utilities only)

# If count is > 10, audit for project-specific scripts
ls -1 *.py
# Review each script - is it used by 2+ projects?
```

### When Adding a New Project

1. Create `projects/[new-project]/src/`
2. Develop scripts there
3. Check if any existing `execution/` utilities can be reused
4. Only promote to `execution/` when **second project** needs it

---

## Related Documentation

- [Two-Tier Architecture Guide](../docs/architecture-guide.md) - Complete architecture overview
- [Execution Folder Audit](../docs/EXECUTION-FOLDER-AUDIT.md) - Current state and migration plan
- [Testing Strategy](../docs/testing-strategy.md) - How to test shared utilities
- [Development to Deployment](../docs/development-to-deployment.md) - Complete pipeline

---

## Current Status (2026-01-12)

**Before Migration**:
- 62 scripts in `execution/`
- Mix of shared utilities and project-specific code

**After Migration** (target):
- 6 shared utilities in `execution/`
- 50+ project-specific scripts moved to `projects/[name]/src/`

**Migration Status**: Phase 2 (Code Audit Complete) - Awaiting Phase 3 (Deployment Updates)

**See**: [EXECUTION-FOLDER-AUDIT.md](../docs/EXECUTION-FOLDER-AUDIT.md) for detailed migration plan

---

**Principle**: Shared utilities are powerful but come with responsibility. Only promote to `execution/` when truly needed by multiple projects. Start in `projects/[name]/src/` and promote when the **second project** needs it.
