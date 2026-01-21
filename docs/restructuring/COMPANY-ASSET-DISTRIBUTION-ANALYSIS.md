# Company Asset Distribution Analysis

**Date**: 2026-01-21
**Purpose**: Determine if current folder structure already groups company assets appropriately, or if company-centric restructure is needed

---

## Executive Summary

**Current Status**: ❌ **Company assets are SCATTERED across multiple locations**

**Recommendation**: ⚠️ **CONDITIONAL** - Restructure would improve organization, but carries risk to automation tools

**Key Finding**: To access all work for a single company, you currently need to visit 2-4 different folders. This does NOT meet the goal of "I shouldn't have to go to multiple folders to get information for [company]."

---

## Current Company Asset Distribution

### 1. Marceau Solutions

**Assets Split Across 3 Locations**:

| Asset Type | Location | Status |
|------------|----------|--------|
| Main projects (9) | `dev-sandbox/projects/marceau-solutions/` | ✅ Grouped |
| Website | `websites/marceausolutions.com/` | ❌ Separate |
| Fitness backend | `active-projects/fitness-influencer-backend/` | ❌ Separate |
| Fitness frontend | `active-projects/fitness-influencer-frontend/` | ❌ Separate |

**Impact**: To see all Marceau Solutions work, you must visit **3 folders** (`projects/marceau-solutions/`, `websites/marceausolutions.com/`, `active-projects/fitness-influencer-*`)

**Assets in `projects/marceau-solutions/`**:
- amazon-seller
- fitness-influencer (MCP/main project)
- instagram-creator
- interview-prep (symlink)
- marceausolutions.com (folder - seems like a duplicate?)
- tiktok-creator
- website-builder
- youtube-creator

---

### 2. SW Florida Comfort HVAC

**Assets Split Across 2 Locations**:

| Asset Type | Location | Status |
|------------|----------|--------|
| Project (hvac-distributors) | `dev-sandbox/projects/swflorida-hvac/` | ✅ Grouped |
| Website | `websites/swflorida-comfort-hvac/` | ❌ Separate |

**Impact**: To see all SW Florida HVAC work, you must visit **2 folders** (`projects/swflorida-hvac/`, `websites/swflorida-comfort-hvac/`)

---

### 3. SquareFoot Shipping

**Assets Split Across 3 Locations**:

| Asset Type | Location | Status |
|------------|----------|--------|
| Project (mostly empty) | `dev-sandbox/projects/square-foot-shipping/` | ⚠️ Empty placeholder |
| Website | `websites/squarefoot-shipping-website/` | ❌ Separate |
| Lead gen project | `active-projects/square-foot-shipping/` | ❌ Separate |

**Impact**: To see all SquareFoot Shipping work, you must visit **3 folders** (`projects/square-foot-shipping/`, `websites/squarefoot-shipping-website/`, `active-projects/square-foot-shipping/`)

---

### 4. Shared Multi-Tenant Tools (All Companies)

**Location**: `dev-sandbox/projects/shared-multi-tenant/`

**Tools**:
- lead-scraper (critical automation tool - Apollo CSV import, SMS outreach)
- ai-customer-service (Voice AI for calls)
- social-media-automation (X posting, content generation)
- personal-assistant (morning digest, routine scheduler)

**Status**: ✅ Already grouped appropriately (shared across all companies)

---

## Problem Assessment

### Does Current Structure Meet User Goal?

**User Goal (from latest request)**: "I shouldn't have to go to multiple folders to get information for Southwest Florida comfort or any of the other companies were working with"

**Answer**: ❌ **NO** - Current structure does NOT meet this goal.

**Evidence**:
- SW Florida HVAC: 2 folders to visit (projects/ + websites/)
- SquareFoot Shipping: 3 folders to visit (projects/ + websites/ + active-projects/)
- Marceau Solutions: 3 folders to visit (projects/ + websites/ + active-projects/)

### Why Isn't It Grouped?

**Root Cause**: Assets were created at different times in different locations:
1. **Projects**: Created in `dev-sandbox/projects/[company]/`
2. **Websites**: Created in `~/websites/[company-website]/`
3. **Active development**: Created in `~/active-projects/[project]/`

**No consolidation step happened**, so they remain scattered.

---

## Restructure Impact Analysis

### Option 1: Company-Centric Restructure (PROPOSED in RESTRUCTURE-PROPOSAL-WITH-SAFEGUARDS.md)

**What It Does**:
- Groups ALL company assets into single folder per company
- Example: `dev-sandbox/projects/swflorida-hvac/` would contain:
  - hvac-distributors/ (project)
  - website/ (moved from ~/websites/)

**Benefits**:
- ✅ Single folder per company (meets user goal)
- ✅ Easy to showcase all work for client
- ✅ Eliminates duplicates (e.g., square-foot-shipping folder consolidation)
- ✅ Clear organization (company → assets)

**Risks**:
- ⚠️ **Path changes for automation tools** (lead-scraper, SMS outreach, campaign analytics)
  - Current: `projects/shared-multi-tenant/lead-scraper/`
  - After: `projects/shared/lead-scraper/`
  - **Impact**: All commands need path update
  - **Mitigation**: Test suite (`verify-automation-tools.sh`) verifies before/after

- ⚠️ **Import path changes** in Python code
  - Some scripts may have hardcoded paths
  - **Mitigation**: Comprehensive testing before deployment

- ⚠️ **Time investment**: 2-4 hours for full migration + testing

**Automation Tool Impact**: MEDIUM RISK (path changes only, functionality unchanged)

---

### Option 2: Minimal Move (Keep As Is, Fix Duplicates Only)

**What It Does**:
- Keep current structure
- Only fix obvious duplicates (e.g., square-foot-shipping consolidation)
- Leave websites in `~/websites/`
- Leave active-projects in `~/active-projects/`

**Benefits**:
- ✅ Zero risk to automation tools (no path changes)
- ✅ Minimal time investment (< 1 hour)
- ✅ No testing required

**Drawbacks**:
- ❌ Does NOT meet user goal (still need multiple folders per company)
- ❌ No client showcase improvement
- ❌ Scattered assets remain scattered

---

### Option 3: Hybrid Approach (Symlinks)

**What It Does**:
- Create symlinks in company folders pointing to assets in other locations
- Example: `dev-sandbox/projects/swflorida-hvac/website/` → symlink to `~/websites/swflorida-comfort-hvac/`

**Benefits**:
- ✅ Single folder navigation (user can stay in one place)
- ✅ Zero automation tool impact (files don't move)
- ✅ Quick to implement (< 30 minutes)

**Drawbacks**:
- ⚠️ Symlinks can be confusing
- ⚠️ Git doesn't follow symlinks well (showcase repos would break)
- ❌ Doesn't actually consolidate (files still scattered)

---

## Cost-Benefit Analysis

| Option | Time | Risk | Benefit | Meets User Goal? |
|--------|------|------|---------|------------------|
| **Company-Centric Restructure** | 2-4 hours | MEDIUM | HIGH | ✅ YES |
| **Minimal Move** | < 1 hour | ZERO | LOW | ❌ NO |
| **Hybrid (Symlinks)** | < 30 min | LOW | MEDIUM | ⚠️ PARTIAL |

---

## Recommendation

### Recommended Approach: **Company-Centric Restructure with Safeguards**

**Rationale**:
1. Current structure does NOT meet user goal ("shouldn't have to go to multiple folders")
2. Safeguards are already in place (test suite, backup plan, rollback)
3. Benefits outweigh risks (showcase capability, clear organization)
4. Automation tool impact is PATH ONLY (not functional)

### Prerequisites Before Proceeding:

1. ✅ **Run automation verification BEFORE restructure**:
   ```bash
   bash verify-automation-tools.sh
   ```
   Must pass 100% before proceeding.

2. ✅ **Create full backup**:
   ```bash
   cp -r ~/dev-sandbox ~/dev-sandbox-backup-$(date +%Y%m%d)
   ```

3. ✅ **Commit all current work**:
   ```bash
   cd ~/dev-sandbox
   git add .
   git commit -m "chore: Pre-restructure checkpoint"
   git push
   ```

4. ✅ **Get William's approval** on the approach

### If User Prefers Lower Risk: **Minimal Move**

If the time/risk trade-off isn't worth it right now:
1. Keep current structure (dev-sandbox/projects/, websites/, active-projects/)
2. Only fix square-foot-shipping duplicate (consolidate 3 locations → 1)
3. Document where each company's assets live (create COMPANY-ASSET-MAP.md)
4. Accept that showcasing work requires pointing to multiple repos
5. Revisit company-centric restructure later (when automation is more stable)

---

## Questions for William

1. **Priority**: Is single-folder-per-company navigation a HIGH priority right now, or can it wait?

2. **Showcase Need**: Do you need to showcase company work to clients soon? (If yes → restructure helps)

3. **Risk Tolerance**: Are you comfortable with 2-4 hours of testing to verify automation tools still work after restructure?

4. **Timing**: Would you prefer to:
   - **Restructure now** (while we have momentum and safeguards in place)
   - **Minimal fix** (just consolidate square-foot-shipping, wait on rest)
   - **Wait entirely** (keep as is, revisit in 1-2 months)

---

## Next Steps (Based on Decision)

### If GO on Restructure:
1. Run `bash verify-automation-tools.sh` (verify BEFORE)
2. Create backup (`cp -r ~/dev-sandbox ~/dev-sandbox-backup-$(date +%Y%m%d)`)
3. Execute company-centric restructure (detailed plan in RESTRUCTURE-PROPOSAL-WITH-SAFEGUARDS.md)
4. Run `bash verify-automation-tools.sh` (verify AFTER)
5. If tests fail → rollback from backup
6. If tests pass → commit and update docs

### If NO-GO on Restructure:
1. Fix square-foot-shipping duplicate only (consolidate 3 folders → 1)
2. Create COMPANY-ASSET-MAP.md documenting where each company's assets live
3. Update CLAUDE.md with current structure as permanent
4. Close restructure proposal (archive for future consideration)

---

## Appendix: Detailed Asset Inventory

### Marceau Solutions (9 projects)
- **Location 1** (`dev-sandbox/projects/marceau-solutions/`):
  - amazon-seller/
  - fitness-influencer/ (MCP)
  - instagram-creator/
  - interview-prep@ (symlink)
  - marceausolutions.com/ (duplicate?)
  - tiktok-creator/
  - website-builder/
  - youtube-creator/

- **Location 2** (`websites/marceausolutions.com/`):
  - Full website deployment

- **Location 3** (`active-projects/`):
  - fitness-influencer-backend/
  - fitness-influencer-frontend/

### SW Florida Comfort HVAC (1 project + website)
- **Location 1** (`dev-sandbox/projects/swflorida-hvac/`):
  - hvac-distributors/

- **Location 2** (`websites/swflorida-comfort-hvac/`):
  - Full website deployment

### SquareFoot Shipping (1 project + website)
- **Location 1** (`dev-sandbox/projects/square-foot-shipping/`):
  - README.md (mostly empty)

- **Location 2** (`websites/squarefoot-shipping-website/`):
  - Full website deployment

- **Location 3** (`active-projects/square-foot-shipping/`):
  - Lead gen project

### Shared Multi-Tenant (4 tools)
- **Location** (`dev-sandbox/projects/shared-multi-tenant/`):
  - lead-scraper/ (Apollo CSV, SMS outreach, campaign analytics)
  - ai-customer-service/ (Voice AI)
  - social-media-automation/ (X posting)
  - personal-assistant/ (morning digest)

---

**End of Analysis**
