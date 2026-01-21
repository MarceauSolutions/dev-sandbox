# Multi-Company Folder Structure Migration - Summary

**Ralph Execution:** Multi-Company Folder Structure Optimization PRD
**Status:** CHECKPOINT at Story 003 - Awaiting Approval
**Date:** 2026-01-20

---

## QUICK SUMMARY

Ralph has completed Stories 001-002 (design and categorization). Story 003 will create migration scripts but **WILL NOT EXECUTE** until you approve.

### What's Been Done ✅
1. **Migration plan created** - Complete reorganization plan with DOE preservation
2. **27 projects categorized** - Sorted into 6 categories by company ownership
3. **Documentation mapped** - 15 Marceau docs, 1 HVAC doc, rest global

### What's Next (Story 003) 🔶
1. Create migration script with `--dry-run` mode
2. Create rollback script
3. Show you the dry-run output
4. **WAIT FOR APPROVAL** before executing

---

## PROPOSED ORGANIZATION (6 Categories)

### 1. Shared Multi-Tenant (4 projects)
Used by ALL 3 companies with business_id separation.
```
projects/shared/
├── lead-scraper/              (all 3 companies)
├── social-media-automation/   (all 3 companies)
├── ai-customer-service/       (voice AI for all 3)
└── personal-assistant/        (William's personal)
```

### 2. Marceau Solutions (8 projects)
AI automation business - content creation, websites, lead gen.
```
projects/marceau-solutions/
├── fitness-influencer/
├── website-builder/
├── instagram-creator/
├── tiktok-creator/
├── youtube-creator/
├── interview-prep/
├── amazon-seller/
└── automated-social-media-campaign/  (archive?)
```

### 3. SW Florida HVAC (1 project)
HVAC business tools.
```
projects/swflorida-hvac/
└── hvac-distributors/
```

### 4. Shipping Logistics (0 projects)
Placeholder for future shipping projects.
```
projects/shipping-logistics/
└── README.md  (placeholder)
```

### 5. Global Utility (9 projects)
MCPs, frameworks, personal tools - no business affiliation.
```
projects/global-utility/
├── md-to-pdf/
├── twilio-mcp/
├── claude-framework/
├── registry/
├── mcp-aggregator/
├── naples-weather/
├── time-blocks/
├── resume/
└── shared/
```

### 6. Product Ideas (5 projects)
Future Marceau products (not yet developed).
```
projects/product-ideas/
├── crave-smart/
├── decide-for-her/
├── elder-tech-concierge/
├── amazon-buyer/
└── uber-lyft-comparison/
```

---

## WHAT STAYS UNCHANGED ✅

### DOE Architecture (PRESERVED)
```
execution/    ← Layer 3 - Shared utilities (UNCHANGED)
directives/   ← Layer 1 - Directives (UNCHANGED)
methods/      ← Internal frameworks (UNCHANGED)
```

### Deployment Model (PRESERVED)
```
dev-sandbox → deploy_to_skills.py → ~/[project]-prod/
(paths updated internally, but same behavior)
```

### Git Repository (PRESERVED)
```
Single .git repo at root
No nested repos
File history preserved via git mv
```

---

## QUESTIONS FOR YOU

### Question 1: Product Ideas
Currently placed in `projects/product-ideas/` (separate from Marceau).

**Options:**
- **A:** Keep as `product-ideas/` (separate until developed) ⭐ Recommended
- **B:** Move to `marceau-solutions/`
- **C:** Create `marceau-solutions/products/` subfolder

### Question 2: Automated_SocialMedia_Campaign
Appears superseded by `social-media-automation`.

**Options:**
- **A:** Archive to `projects/archived/` ⭐ Recommended
- **B:** Merge into `social-media-automation`
- **C:** Keep in `marceau-solutions/`

### Question 3: Shipping Logistics
No projects exist yet.

**Options:**
- **A:** Create README placeholder only ⭐ Recommended
- **B:** Skip until first project
- **C:** Create full structure now

---

## SAFETY GUARANTEES

### Git Safety ✅
- All moves use `git mv` (preserves file history)
- Single atomic commit (easy to revert)
- Rollback script available
- No nested .git repos

### Testing Before Commit ✅
- Import checker verifies all imports resolve
- Deployment test (`deploy_to_skills.py --list`)
- Manual verification of key projects

### Architecture Preserved ✅
- DOE unchanged (execution/, directives/, methods/)
- Deployment unchanged (deploy_to_skills.py → ~/[project]-prod/)
- Single repo (no git structure changes)

---

## DETAILED REVIEW FILES

| File | Purpose |
|------|---------|
| **ralph/MIGRATION_PLAN.md** | Complete before/after structure, all mappings |
| **ralph/PROJECT_CATEGORIZATION.md** | All 27 projects categorized with rationale |
| **ralph/CHECKPOINT_STORY_003.md** | Detailed checkpoint explanation, approval checklist |
| **ralph/EXECUTION_STATUS.md** | Story-by-story progress tracker |

---

## APPROVAL PROCESS

### Step 1: Review (NOW)
Review the 4 files above and answer the 3 questions.

### Step 2: Approve Story 003
Ralph creates migration scripts (does NOT execute).

### Step 3: Review Dry-Run
Ralph shows you what `--dry-run` would do.

### Step 4: Approve Execution
Ralph executes migration (Stories 004-005).

### Step 5: Verify
All projects tested, imports work, deploy works.

---

## HOW TO RESPOND

**Approve with recommendations:**
```
Approved - proceed with Story 003
- Question 1: Option A (keep product-ideas separate)
- Question 2: Option A (archive automated-social-media-campaign)
- Question 3: Option A (placeholder only)
```

**Request changes:**
```
Changes needed:
- [Specific feedback on categorization]
- [Concerns about DOE/deployment]
```

**Ask questions:**
```
Questions:
- [Specific clarifications needed]
```

---

**Files Created by Ralph:**
- ✅ `ralph/MIGRATION_PLAN.md`
- ✅ `ralph/PROJECT_CATEGORIZATION.md`
- ✅ `ralph/CHECKPOINT_STORY_003.md`
- ✅ `ralph/EXECUTION_STATUS.md`
- ✅ `ralph/MIGRATION_SUMMARY.md` (this file)

**Next Step:** Your approval to proceed with Story 003 (script creation)
