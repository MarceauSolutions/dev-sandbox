# Autonomous Migration - Ready to Execute

**Created**: 2026-01-21
**Status**: Ready for execution
**Type**: Single-session autonomous migration with rollback

---

## What You Asked For

> "I don't want it to take four days for the same reason that we performed the earlier restructuring efforts all at once due to the fact that if I continue to work as we're doing the restructuring, it could create further complications... let's use Ralph to perform the whole restructuring effort autonomously ensuring to place necessary safeguards so that we can do the rollback if anything breaks or a test long way"

**Delivered**: Complete autonomous migration script that executes everything in ONE SESSION (4-8 hours) with automatic rollback.

---

## The Script: `migrate_company_centric_autonomous.py`

### Two Commands Only

```bash
# 1. Preview (ALWAYS start here)
python migrate_company_centric_autonomous.py --dry-run

# 2. Execute (all or nothing)
python migrate_company_centric_autonomous.py --execute
```

### What It Does Automatically

**Phase 1: Pre-Flight** (15 minutes)
- Creates timestamped backup
- Exports current state (git status, crontab, launchd)
- Stops all automation
- Runs 38 pre-migration tests (MUST PASS)
- Commits current state

**Phase 2: Folder Migrations** (1-2 hours)
- Renames `shared-multi-tenant/` → `shared/`
- Moves 3 websites into company folders
- Consolidates fitness-influencer (backend + frontend + mcp)
- Consolidates square-foot-shipping
- Uses `git mv` to preserve history

**Phase 3: Import Updates** (30 minutes)
- Updates 73+ Python files
- Changes all `projects.shared_multi_tenant` → `projects.shared`
- Fully automated search/replace

**Phase 4: Config Updates** (30 minutes)
- Updates deploy_to_skills.py (category detection)
- Updates launchd plist files (paths)
- Updates 8 cron scripts (working directories)
- Updates 4 VSCode workspaces
- Updates verify-automation-tools.sh

**Phase 5: Documentation Updates** (30 minutes)
- Updates CLAUDE.md (SOPs 18, 19, 22, 24)
- Updates 66+ workflow documents
- All command examples updated

**Phase 6: Post-Migration Verification** (30 minutes)
- Runs 38 post-migration tests (MUST PASS or rollback)
- Tests business_id separation (3 businesses)
- Verifies historical data intact
- Tests Python imports

**Phase 7: Restart Automation** (15 minutes)
- Reloads launchd jobs with new paths
- Restores cron jobs
- Tests each automation manually

**Phase 8: Commit Migration** (10 minutes)
- Commits all changes with detailed message
- Creates migration report

**Total Time**: 4-8 hours (single session)

---

## Safety Guarantees

### Zero-Tolerance Failure Policy

**If ANY of these fail → Automatic rollback**:
- Pre-migration tests (38 tests)
- Post-migration tests (38 tests)
- Business_id separation tests
- Data preservation checks
- Python import tests

### Rollback Process

Automatic rollback:
1. Stops all automation
2. Deletes current dev-sandbox
3. Restores from timestamped backup
4. Reloads old automation (launchd + cron)
5. Creates failure report

**Result**: System restored to exact pre-migration state

---

## What Gets Changed

### 8 Major Folder Moves

1. `projects/shared-multi-tenant/` → `projects/shared/`
2. `~/websites/marceausolutions.com/` → `projects/marceau-solutions/website/`
3. `~/websites/swflorida-comfort-hvac/` → `projects/swflorida-hvac/website/`
4. `~/websites/squarefoot-shipping-website/` → `projects/square-foot-shipping/website/`
5. `~/active-projects/fitness-influencer-backend/` → `projects/marceau-solutions/fitness-influencer/backend/`
6. `~/active-projects/fitness-influencer-frontend/` → `projects/marceau-solutions/fitness-influencer/frontend/`
7. Current `fitness-influencer/` → `projects/marceau-solutions/fitness-influencer/mcp/`
8. `~/active-projects/square-foot-shipping/` → `projects/square-foot-shipping/lead-gen/`

### 273+ Files Updated

- 73+ Python files (imports)
- 1 deploy script (category detection)
- 2 launchd plists (paths)
- 8 cron scripts (working directories)
- 4 VSCode workspaces (folder paths)
- 1 verification script (path detection)
- 1 CLAUDE.md (4 SOPs)
- 66+ workflow docs (commands)

---

## What Stays the Same

### No Changes To

✓ `.env` file location (stays at root)
✓ API credentials (all unchanged)
✓ Business_id separation logic (preserved)
✓ Data separation (companies/ structure)
✓ Webhook URLs (unchanged)
✓ DOE architecture (intact)
✓ Testing strategy (unchanged)
✓ Git history (preserved with git mv)
✓ Automation functionality (only paths change)

---

## How to Execute

### Step 1: Dry Run (5-10 minutes)

```bash
cd ~/dev-sandbox
python migrate_company_centric_autonomous.py --dry-run
```

**Review output**: Shows all folder moves, file updates, config changes

**Look for**:
- Any missing files or directories
- Any unexpected changes
- Confirmation all 8 migrations will happen

### Step 2: Execute Migration (4-8 hours)

**Prerequisites**:
- ✅ Dry run reviewed and looks good
- ✅ You have 4-8 hours uninterrupted time
- ✅ No urgent work needed during migration
- ✅ You're ready to commit to the restructure

**Execute**:
```bash
python migrate_company_centric_autonomous.py --execute
```

**What you'll see**:
- Real-time progress in terminal
- Each phase logged with ✓ checkmarks
- Test results (38 tests before, 38 tests after)
- Success message or automatic rollback

**Monitoring**:
- Watch terminal output (real-time)
- Or check `migration.log` in another terminal: `tail -f migration.log`

---

## Expected Output

### Successful Migration

```
============================================================
PHASE 1: PRE-FLIGHT VALIDATION
============================================================
[2026-01-21 10:00:00] [INFO] Creating full backup...
[2026-01-21 10:05:00] [INFO] ✓ Backup created: /Users/williammarceaujr./dev-sandbox-backup-20260121_100000
[2026-01-21 10:05:30] [INFO] ✓ Current state exported
[2026-01-21 10:06:00] [INFO] ✓ Cron jobs disabled
[2026-01-21 10:06:30] [INFO] Running pre-migration tests (38 tests)...
[2026-01-21 10:10:00] [INFO] ✓ All 38 pre-migration tests PASSED
[2026-01-21 10:10:30] [INFO] ✓ Current state committed

============================================================
PHASE 2: FOLDER MIGRATIONS
============================================================
[2026-01-21 10:11:00] [INFO] ✓ git mv: projects/shared-multi-tenant → projects/shared
[2026-01-21 10:15:00] [INFO] ✓ moved: ~/websites/marceausolutions.com → projects/marceau-solutions/website
... (6 more migrations)

============================================================
PHASE 3: IMPORT PATH UPDATES
============================================================
[2026-01-21 11:30:00] [INFO] ✓ Updated imports in 73 Python files

============================================================
PHASE 4: CONFIGURATION UPDATES
============================================================
[2026-01-21 12:00:00] [INFO] ✓ Updated deploy_to_skills.py
[2026-01-21 12:01:00] [INFO] ✓ Updated: com.marceausolutions.campaign-launcher.plist
... (more config updates)

============================================================
PHASE 5: DOCUMENTATION UPDATES
============================================================
[2026-01-21 12:30:00] [INFO] ✓ Updated CLAUDE.md
[2026-01-21 12:35:00] [INFO] ✓ Updated 66 workflow documents

============================================================
PHASE 6: POST-MIGRATION VERIFICATION
============================================================
[2026-01-21 13:00:00] [INFO] Running post-migration tests (38 tests)...
[2026-01-21 13:05:00] [INFO] ✓ All 38 post-migration tests PASSED
[2026-01-21 13:06:00] [INFO] ✓ Business ID separation verified
[2026-01-21 13:07:00] [INFO] ✓ All historical data preserved

============================================================
PHASE 7: RESTART AUTOMATION
============================================================
[2026-01-21 13:10:00] [INFO] ✓ Loaded: com.marceausolutions.campaign-launcher.plist
[2026-01-21 13:11:00] [INFO] ✓ Cron jobs restored

============================================================
PHASE 8: COMMIT MIGRATION
============================================================
[2026-01-21 13:15:00] [INFO] ✓ Migration committed

============================================================
✓ MIGRATION COMPLETE
============================================================
[2026-01-21 13:20:00] [INFO] Total time: 3:20:00
[2026-01-21 13:20:00] [INFO] Backup preserved at: /Users/williammarceaujr./dev-sandbox-backup-20260121_100000
```

### If Rollback Happens

```
============================================================
PHASE 6: POST-MIGRATION VERIFICATION
============================================================
[2026-01-21 13:00:00] [INFO] Running post-migration tests (38 tests)...
[2026-01-21 13:05:00] [ERROR] ✗ POST-MIGRATION TESTS FAILED

[2026-01-21 13:05:01] [ERROR] ✗ MIGRATION FAILED: Post-migration tests failed. Initiating rollback.
[2026-01-21 13:05:02] [ERROR] ⚠ ROLLING BACK MIGRATION
[2026-01-21 13:10:00] [ERROR] ✓ Rollback complete - system restored

Migration failed. System restored to pre-migration state.
See migration.log for details.
```

---

## After Migration

### Verify Everything Works

```bash
# 1. Check structure
ls -la projects/marceau-solutions/
ls -la projects/swflorida-hvac/
ls -la projects/square-foot-shipping/
ls -la projects/shared/

# 2. Test automation manually
cd projects/shared/lead-scraper
python -m src.scraper --help

cd ../social-media-automation
python -m src.business_scheduler --help

cd ../personal-assistant
python -m src.morning_digest --preview

# 3. Check deployment
python deploy_to_skills.py --list

# 4. Verify no nested repos
find . -name ".git" -type d
# Should show only: ./.git
```

### Next Steps (Optional)

**Create GitHub Showcase Repos** (if desired):
```bash
mkdir -p ~/github-showcases/

# Marceau Solutions showcase
cp -r ~/dev-sandbox/projects/marceau-solutions/ ~/github-showcases/marceausolutions-complete/
cd ~/github-showcases/marceausolutions-complete/
git init
gh repo create MarceauSolutions/marceausolutions-complete --public
git add .
git commit -m "Initial commit: Complete Marceau Solutions portfolio"
git push -u origin main

# SW Florida HVAC showcase
# (repeat for other companies)
```

---

## Files Created

1. **migrate_company_centric_autonomous.py** - The migration script (725 lines)
2. **COMPREHENSIVE-RESTRUCTURE-PLAN.md** - Full 50+ page analysis
3. **COMPANY-ASSET-DISTRIBUTION-ANALYSIS.md** - Current state analysis
4. **MIGRATION-READY-TO-EXECUTE.txt** - Quick reference (on Desktop)
5. **This file** - Execution summary

---

## Questions?

**Before executing**:
- Review dry-run output carefully
- Check that all expected folders exist
- Ensure you have 4-8 hours available
- Verify backup directory will be created

**During execution**:
- Don't interrupt the process
- Don't work in dev-sandbox during migration
- Monitor terminal or migration.log for progress

**After completion**:
- Test all automation manually
- Monitor for 24 hours
- Keep backup for 7 days
- Create GitHub showcases when ready

---

## Ready to Execute?

**Command**:
```bash
cd ~/dev-sandbox
python migrate_company_centric_autonomous.py --execute
```

**Sit back and watch** - the script handles everything autonomously with full rollback protection.

---

**End of Summary**
