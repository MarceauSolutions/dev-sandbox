# CHECKPOINT: Story 003 - Migration Script Ready

**Status:** AWAITING APPROVAL
**Date:** 2026-01-20
**Autonomous Agent:** Ralph

---

## SUMMARY

Stories 001 and 002 are complete:
- **Story 001:** Migration plan designed → `ralph/MIGRATION_PLAN.md`
- **Story 002:** All 27 projects categorized → `ralph/PROJECT_CATEGORIZATION.md`

**Story 003** will create the migration script and new folder structure, but **WILL NOT EXECUTE** the migration until approval.

---

## WHAT WILL BE CREATED (Story 003)

### New Folder Structure
```
projects/
├── shared/        # NEW
├── marceau-solutions/          # NEW
├── swflorida-hvac/             # NEW
├── shipping-logistics/         # NEW
├── global-utility/             # NEW
└── product-ideas/              # NEW

docs/companies/                 # NEW
├── marceau-solutions/
├── swflorida-hvac/
└── shipping-logistics/

output/companies/               # NEW
templates/companies/            # NEW
```

### Migration Scripts
1. **migrate_to_company_structure.py**
   - `--dry-run` mode (shows what would happen)
   - `--execute` mode (actually moves files)
   - Uses `git mv` to preserve history
   - Updates imports automatically

2. **rollback_migration.py**
   - Reverses the migration if needed
   - Restores original structure

### README Files
- `projects/shared/README.md`
- `projects/marceau-solutions/README.md`
- `projects/swflorida-hvac/README.md`
- `projects/shipping-logistics/README.md`
- `projects/global-utility/README.md`
- `projects/product-ideas/README.md`
- `docs/companies/marceau-solutions/README.md`
- `docs/companies/swflorida-hvac/README.md`
- `docs/companies/shipping-logistics/README.md`

---

## PROPOSED PROJECT MOVES

### Shared Multi-Tenant (4 projects → used by ALL 3 companies)
```
projects/lead-scraper/              → projects/shared/lead-scraper/
projects/social-media-automation/   → projects/shared/social-media-automation/
projects/ai-customer-service/       → projects/shared/ai-customer-service/
projects/personal-assistant/        → projects/shared/personal-assistant/
```

### Marceau Solutions (8 projects → AI automation business)
```
projects/fitness-influencer/        → projects/marceau-solutions/fitness-influencer/
projects/website-builder/           → projects/marceau-solutions/website-builder/
projects/instagram-creator/         → projects/marceau-solutions/instagram-creator/
projects/tiktok-creator/            → projects/marceau-solutions/tiktok-creator/
projects/youtube-creator/           → projects/marceau-solutions/youtube-creator/
projects/Automated_SocialMedia_Campaign/ → projects/marceau-solutions/automated-social-media-campaign/
projects/interview-prep/            → projects/marceau-solutions/interview-prep/
projects/amazon-seller/             → projects/marceau-solutions/amazon-seller/
```

### SW Florida HVAC (1 project)
```
projects/hvac-distributors/         → projects/swflorida-hvac/hvac-distributors/
```

### Global Utility (9 projects → framework, MCPs, personal tools)
```
projects/md-to-pdf/                 → projects/global-utility/md-to-pdf/
projects/twilio-mcp/                → projects/global-utility/twilio-mcp/
projects/claude-framework/          → projects/global-utility/claude-framework/
projects/registry/                  → projects/global-utility/registry/
projects/mcp-aggregator/            → projects/global-utility/mcp-aggregator/
projects/naples-weather/            → projects/global-utility/naples-weather/
projects/time-blocks/               → projects/global-utility/time-blocks/
projects/resume/                    → projects/global-utility/resume/
projects/shared/                    → projects/global-utility/shared/
```

### Product Ideas (5 projects → future Marceau products)
```
projects/crave-smart/               → projects/product-ideas/crave-smart/
projects/decide-for-her/            → projects/product-ideas/decide-for-her/
projects/elder-tech-concierge/      → projects/product-ideas/elder-tech-concierge/
projects/amazon-buyer/              → projects/product-ideas/amazon-buyer/
projects/uber-lyft-comparison/      → projects/product-ideas/uber-lyft-comparison/
```

---

## DOCUMENTATION MOVES (Marceau-specific)

### To `docs/companies/marceau-solutions/`
- `AI-VOICE-SERVICE-ECONOMICS.md`
- `MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md`
- `COLD-OUTREACH-STRATEGY-JAN-19-2026.md`
- `CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md`
- `BUSINESS-MODEL-OPTIONS-ANALYSIS.md`
- `MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md`
- `EXECUTION-PLAN-WEEK-JAN-19-2026.md`
- `API-USAGE-COST-CHECKER.md`
- `APOLLO-IO-MAXIMIZATION-PLAN.md`
- `COST-BUDGET-TRACKING-JAN-19-2026.md`
- `LEAD-TRACKING-FOLLOWUP-SYSTEM.md`
- `ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md`
- `ACTION-ITEMS-JAN-20-2026.md`
- `EXECUTION-SUMMARY-JAN-19-2026.md`
- `GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md`

### To `docs/companies/swflorida-hvac/`
- `3-PHASE-HVAC-PLAN-JAN-19-2026.md`

### Global Docs (STAY AT ROOT)
- All architecture guides
- All SOPs
- All testing/deployment guides

---

## WHAT WILL NOT CHANGE

### DOE Architecture (PRESERVED)
- `execution/` - Execution layer (Layer 3) - **UNCHANGED**
- `directives/` - Directive layer (Layer 1) - **UNCHANGED**
- `methods/` - Internal frameworks - **UNCHANGED**

### Deployment Model (PRESERVED)
- `deploy_to_skills.py` - **UPDATED** with new paths (but same functionality)
- Deployment destinations - `~/[project]-prod/` - **UNCHANGED**

### Git Repository (PRESERVED)
- Single `.git` repo at root - **UNCHANGED**
- No nested repos
- File history preserved via `git mv`

---

## DRY-RUN WORKFLOW

### Step 1: Create Script (Story 003)
```bash
python migrate_to_company_structure.py --dry-run
```
**Output:**
- Shows all proposed file moves
- Shows import updates
- Shows no actual changes made

### Step 2: Review Output
- Verify all moves make sense
- Check for unexpected moves
- Confirm no files will be lost

### Step 3: Get Approval
**CHECKPOINT: William reviews and approves**

### Step 4: Execute (Story 004)
```bash
python migrate_to_company_structure.py --execute
```
**Result:**
- Files moved with `git mv`
- Imports updated
- Single atomic commit

---

## QUESTIONS FOR APPROVAL

### 1. Product Ideas → Marceau Solutions?
All 5 product ideas (crave-smart, decide-for-her, elder-tech-concierge, amazon-buyer, uber-lyft-comparison) are currently categorized under `product-ideas/`.

**Option A:** Keep as `projects/product-ideas/` (separate from Marceau)
**Option B:** Move to `projects/marceau-solutions/` (all are Marceau products)
**Option C:** Create `projects/marceau-solutions/products/` subfolder

**Recommendation:** Option A - Keep separate until developed, then move to Marceau

### 2. Automated_SocialMedia_Campaign
This project appears to be superseded by `social-media-automation`.

**Option A:** Archive (move to `projects/archived/`)
**Option B:** Merge into `social-media-automation`
**Option C:** Keep as-is in Marceau Solutions

**Recommendation:** Option A - Archive (but keep in git history)

### 3. Shipping Logistics Placeholder
Currently no shipping projects exist.

**Option A:** Create empty `projects/shipping-logistics/README.md` placeholder
**Option B:** Skip until first shipping project created
**Option C:** Create full structure now (projects/, docs/, templates/, output/)

**Recommendation:** Option A - Just README placeholder

---

## SAFETY MECHANISMS

### Git Safety
1. **All moves use `git mv`** - Preserves file history
2. **Single atomic commit** - Easy to revert if needed
3. **No nested repos** - Maintains single .git

### Testing Before Commit
1. Import checker - Verifies all imports resolve
2. Deployment test - `deploy_to_skills.py --list` works
3. Manual verification - Key projects still work

### Rollback Available
```bash
python rollback_migration.py
```
Restores original structure in case of issues

---

## APPROVAL NEEDED

**Ralph will proceed with Story 003 (creating scripts) but will NOT execute the migration until William approves.**

### Review Checklist
- [ ] Project categorization correct? (27 projects → 6 categories)
- [ ] Documentation moves make sense?
- [ ] DOE architecture preserved?
- [ ] Deployment model unchanged?
- [ ] Product ideas → Keep separate or move to Marceau?
- [ ] Automated_SocialMedia_Campaign → Archive?
- [ ] Shipping logistics → Placeholder only?

**Once approved, Ralph will:**
1. Create migration scripts
2. Create folder structure
3. Run dry-run
4. Show output for final approval
5. Execute migration (after approval)

---

**Status:** CHECKPOINT REACHED - Awaiting approval to proceed
**Next:** Story 003 - Create migration scripts and structure (but don't execute)
