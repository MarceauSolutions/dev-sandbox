# Architecture Conflict Resolution: execution/ vs projects/src/

**Date**: 2026-01-12
**Status**: 🔴 CONFLICT IDENTIFIED - NEEDS RESOLUTION

---

## The Conflict

### Conflicting Mental Models

**Model A: DOE Architecture (from CLAUDE.md)**
```
Layer 1: DIRECTIVE (directives/*.md)     → What to do
Layer 2: ORCHESTRATION (Claude)           → Decision making
Layer 3: EXECUTION (execution/*.py)       → Deterministic scripts
```

**Model B: Project Development (actual practice)**
```
directives/[project].md           → What to do
projects/[project]/src/*.py        → Implementation
Claude                             → Orchestration
```

**THE PROBLEM**: These models are inconsistent!

---

## Current Reality

### What Actually Exists

1. **`/Users/williammarceaujr./dev-sandbox/execution/`**
   - Contains: 69 Python scripts
   - Examples: `amazon_sp_api.py`, `email_analyzer.py`, `add_lead.py`
   - Used by: Shared across multiple projects
   - Purpose: **Shared utility scripts**

2. **`/Users/williammarceaujr./dev-sandbox/projects/[name]/src/`**
   - Contains: Project-specific implementation
   - Examples: `md_to_pdf.py`, `generate_pptx.py`
   - Used by: Single project only
   - Purpose: **Project-specific logic**

3. **What deploy_to_skills.py does**:
   ```python
   # From deploy_to_skills.py
   "scripts": [
       "interview_research.py",
       "pptx_generator.py",
       # ... listed scripts
   ]
   ```
   - **Copies scripts FROM `execution/` TO skills deployment**
   - Does NOT deploy from `projects/[name]/src/` directly

---

## The Contradictions

### Contradiction #1: Where to Write Code

**CLAUDE.md says**: "Implement Execution (Layer 3)" in `execution/`

**Actual practice**: Write in `projects/[name]/src/`, then maybe sync to `execution/`

**Problem**: Which is the source of truth?

---

### Contradiction #2: What Gets Deployed

**DOE Architecture implies**: Deploy `execution/` scripts to skills

**Deploy script actually does**:
1. Looks for scripts in `execution/` folder
2. Copies them to skills deployment
3. BUT projects develop in `projects/[name]/src/`

**Problem**: Extra step needed: sync from `src/` to `execution/`

---

### Contradiction #3: Shared vs. Project-Specific

**`execution/` folder**: Contains both shared utilities AND project-specific scripts mixed together

Examples:
- `amazon_sp_api.py` - Shared (used by amazon-seller project)
- `email_analyzer.py` - Project-specific (email-analyzer only)
- `pptx_generator.py` - Project-specific (interview-prep only)

**Problem**: No clear separation of concerns

---

### Contradiction #4: Testing References

**testing-strategy.md says**: Test scripts in `projects/[name]/src/`

**DOE architecture implies**: Test scripts in `execution/`

**Example from testing-strategy.md**:
```bash
python projects/md-to-pdf/src/md_to_pdf.py README.md test.pdf
```

**Problem**: Where is the script actually located during development?

---

## Real-World Examples

### Example 1: MD-to-PDF

**Current structure**:
```
projects/md-to-pdf/
├── src/
│   ├── md_to_pdf.py       ← Developed here
│   └── convert.sh          ← Testing uses this
└── testing/
    └── agent1/             ← Tests run against src/
```

**Deployment**:
- Script stays in `projects/md-to-pdf/src/`
- NOT copied to `execution/`
- NOT deployed to skills (yet)

**Question**: Should it be copied to `execution/` before deployment?

---

### Example 2: Interview Prep

**deploy_to_skills.py configuration**:
```python
"interview-prep": {
    "src_dir": DEV_SANDBOX / "interview-prep-pptx" / "src",
    "scripts": [
        "pptx_generator.py",
        "interview_research.py",
        # ... more scripts
    ]
}
```

**Deployment flow**:
1. Develop in `interview-prep-pptx/src/`
2. ??? (sync to `execution/` somehow?)
3. Deploy copies from `execution/` to skills

**Problem**: Step 2 is unclear and manual

---

### Example 3: Email Analyzer

**File exists**: `/Users/williammarceaujr./dev-sandbox/execution/email_analyzer.py`

**Questions**:
- Was it developed in `projects/email-analyzer/src/` first?
- When was it copied to `execution/`?
- Is `execution/email_analyzer.py` the source of truth?

**Problem**: Unclear workflow

---

## Proposed Solutions

### Option A: Pure DOE Architecture (execution/ is source)

**All development** happens in `execution/`
- Remove `projects/[name]/src/` entirely
- `projects/[name]/` only contains:
  - `workflows/` - Documentation
  - `testing/` - Multi-agent testing
  - `demos/` - Client demos
- Scripts live in `execution/` from day one

**Pros**:
- Aligns with DOE architecture
- Single source of truth
- No sync needed

**Cons**:
- `execution/` becomes cluttered with 100+ scripts
- Hard to distinguish shared vs. project-specific
- Loses project organization

---

### Option B: Projects-First Architecture (src/ is source)

**All development** happens in `projects/[name]/src/`
- Scripts stay in project folders
- `execution/` is deprecated OR only for truly shared utilities
- Deployment copies FROM `projects/[name]/src/` TO skills

**Pros**:
- Better project organization
- Clear ownership of code
- Matches current practice

**Cons**:
- Breaks DOE architecture conceptually
- `execution/` folder becomes confusing
- Need to update deploy_to_skills.py

---

### Option C: Hybrid Architecture (both serve different purposes)

**Clarify the distinction**:

**`execution/`** = Shared utility scripts used by MULTIPLE projects
- Examples: `gmail_monitor.py`, `twilio_sms.py`, `grok_image_gen.py`
- Deployed to skills as shared dependencies
- Versioned separately

**`projects/[name]/src/`** = Project-specific implementation
- Examples: `md_to_pdf.py`, `pptx_generator.py`
- Deployed to project-specific skills
- Versioned with project

**Deployment flow**:
1. Develop in `projects/[name]/src/`
2. Test in `projects/[name]/src/`
3. Deploy copies `src/` scripts to skills (NOT to `execution/`)
4. Shared utilities in `execution/` deploy separately

**Pros**:
- Clear separation of concerns
- Maintains DOE philosophy for shared code
- Projects can be self-contained

**Cons**:
- Need to refactor deploy_to_skills.py
- More complex deployment logic
- Two types of deployments

---

## Recommended Solution: Option C (Hybrid)

### Clarified Architecture

```
DOE Architecture (for shared utilities):
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py) ← SHARED utilities only

Project Architecture (for project-specific code):
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py) ← Project-specific
```

### Updated Definitions

**`execution/`** → Shared Utilities Layer
- **Purpose**: Reusable scripts used across multiple projects
- **Examples**: API clients, notification systems, data processors
- **Deployment**: Copy to skills as shared dependencies
- **Development**: Can be developed in `execution/` OR extracted from projects when shared

**`projects/[name]/src/`** → Project Implementation Layer
- **Purpose**: Project-specific logic and workflows
- **Examples**: `md_to_pdf.py`, project-specific APIs
- **Deployment**: Copy to project-specific skills
- **Development**: Always develop here first

### Migration Path

1. **Audit `execution/` folder**:
   - Identify truly shared scripts (keep in `execution/`)
   - Identify project-specific scripts (move to `projects/[name]/src/`)

2. **Update deploy_to_skills.py**:
   - Support deploying from `projects/[name]/src/` directly
   - Support deploying shared utilities from `execution/`

3. **Update CLAUDE.md**:
   - Clarify difference between `execution/` (shared) and `projects/[name]/src/` (project-specific)
   - Update DOE architecture explanation

4. **Update all SOPs**:
   - SOP 1: Develop in `projects/[name]/src/`
   - Testing: Test in `projects/[name]/src/`
   - Deployment: Deploy from `projects/[name]/src/`

---

## Impact on Existing SOPs

### SOP 1: New Project Initialization

**Before** (ambiguous):
```
3. Develop iteratively:
   - Write scripts in `src/`
   - Test using `execution/` shared scripts
```

**After** (clarified):
```
3. Develop iteratively:
   - Write project-specific scripts in `projects/[name]/src/`
   - Use shared utilities from `execution/` (if needed)
   - Test scripts in `projects/[name]/src/`
```

---

### SOP 2: Multi-Agent Testing

**Before** (references execution):
```
Test using `execution/` shared scripts
```

**After** (clarified):
```
Test scripts in `projects/[name]/src/`
May use shared utilities from `execution/` as dependencies
```

---

### Testing Strategy

**Before** (unclear):
```
python execution/[script].py [test-input] [test-output]
```

**After** (clarified):
```
# Test project-specific scripts
python projects/[name]/src/[script].py [test-input] [test-output]

# Shared utilities are tested separately in execution/
python execution/[shared-utility].py [test-input]
```

---

## Action Items

### Immediate (to resolve conflict):

1. **[ ] Create `docs/architecture-clarification.md`**
   - Define `execution/` as shared utilities only
   - Define `projects/[name]/src/` as project implementation
   - Provide migration guide

2. **[ ] Update CLAUDE.md**
   - Section: DOE Architecture
   - Add: "Projects develop in `projects/[name]/src/`, shared utilities in `execution/`"

3. **[ ] Update testing-strategy.md**
   - Clarify: Test in `projects/[name]/src/`
   - Note: Shared utilities from `execution/` are dependencies

4. **[ ] Update deploy_to_skills.py**
   - Support deploying from `projects/[name]/src/` directly
   - Don't require scripts to be in `execution/` first

### Long-term (cleanup):

5. **[ ] Audit execution/ folder**
   - Move project-specific scripts to their projects
   - Keep only truly shared utilities

6. **[ ] Create execution/README.md**
   - Document what belongs in `execution/`
   - Provide guidelines for shared vs. project-specific

---

## Summary

**Conflict**: Confusion between `execution/` (shared utilities) and `projects/[name]/src/` (project code)

**Resolution**: Hybrid architecture
- `execution/` = Shared utilities (DOE Layer 3)
- `projects/[name]/src/` = Project implementation (not DOE, different pattern)

**Next Steps**:
1. Update documentation to clarify distinction
2. Update deploy_to_skills.py to deploy from `src/`
3. Audit and reorganize `execution/` folder

---

**Status**: ✅ RESOLVED - Option C (Hybrid Architecture) Implemented

**Phase 1 Complete**:
- ✅ Created comprehensive architecture guide: [architecture-guide.md](architecture-guide.md)
- ✅ Updated CLAUDE.md with Two-Tier Architecture
- ✅ Updated all documentation cross-references

**Next**: Phase 2 (Code Audit & Reorganization) - see COMPREHENSIVE-CONFLICT-AUDIT.md
