# Next Steps: Restore Hybrid Architecture

**Status**: Ready to execute
**Time Required**: ~10-15 minutes
**Risk**: Low (all changes backed up, can be reverted)

---

## What We're About to Do

**Restore the BEST of both approaches**:

1. ✅ **KEEP**: Company-centric folder structure
   - All Marceau assets in `projects/marceau-solutions/`
   - All HVAC assets in `projects/swflorida-hvac/`
   - All Shipping assets in `projects/square-foot-shipping/`

2. ✅ **RESTORE**: Websites as git submodules
   - Each website has its own GitHub repo (for hosting)
   - Websites referenced as submodules in dev-sandbox
   - Work in dev-sandbox, deploy to production automatically

---

## Before Executing: Pre-Flight Checks

### 1. Check Production Repos Exist on GitHub

```bash
gh repo view MarceauSolutions/marceausolutions.com
gh repo view MarceauSolutions/swflorida-comfort-hvac

# Check for square-foot-shipping (might be under different org)
gh repo view MarceauSolutions/squarefoot-shipping-website || \
gh repo view SquareFootShipping/squarefoot-shipping-website
```

**Expected**: All repos exist and are accessible

### 2. Check if Websites are Currently Live

Visit these URLs to confirm they're working:
- https://marceausolutions.com
- https://swflorida-comfort-hvac.com (or whatever the domain is)
- Square Foot Shipping website URL

**Expected**: All websites load correctly

### 3. Check for Uncommitted Changes

```bash
cd /Users/williammarceaujr./dev-sandbox
git status

# Should show:
# - URGENT-FIX-NEEDED.md (untracked)
# - docs/HYBRID-ARCHITECTURE-SOLUTION.md (untracked)
# - scripts/restore-hybrid-architecture.sh (untracked)
```

**Action**: Commit these docs before proceeding

---

## Execution Steps

### Step 1: Commit Documentation

```bash
cd /Users/williammarceaujr./dev-sandbox

git add URGENT-FIX-NEEDED.md \
        NEXT-STEPS-HYBRID-ARCHITECTURE.md \
        docs/WEBSITE-DEPLOYMENT-ARCHITECTURE.md \
        docs/HYBRID-ARCHITECTURE-SOLUTION.md \
        scripts/restore-hybrid-architecture.sh

git commit -m "docs: Add hybrid architecture solution and migration script

Identified issue: Incorrectly removed website submodules
Solution: Restore submodules while keeping company-centric structure
Benefit: Best of both worlds (organized + proper deployment)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

### Step 2: Execute the Migration Script

```bash
cd /Users/williammarceaujr./dev-sandbox
./scripts/restore-hybrid-architecture.sh
```

**What it does**:
1. Clones production repos to `~/marceausolutions.com`, `~/swflorida-comfort-hvac`, etc.
2. Syncs latest changes from dev-sandbox to production repos
3. Removes website folders from dev-sandbox tracking
4. Deletes local website folders
5. Adds websites back as git submodules
6. Initializes and updates submodules
7. Commits and pushes to dev-sandbox

**Time**: ~10-15 minutes

### Step 3: Verify the Setup

```bash
# Check submodule status
git submodule status

# Should show 3 submodules (or 2 if square-foot doesn't exist)

# Check folder structure
ls -la projects/marceau-solutions/
# Should show: website/ (with -> pointing to submodule)

# Verify no nested repos (except submodules which are OK)
find . -name '.git' -type d
# Should show:
# ./.git (main repo)
# ./projects/marceau-solutions/website/.git (submodule - OK)
# ./projects/swflorida-hvac/website/.git (submodule - OK)
```

### Step 4: Test Website Editing Workflow

```bash
# Go to website
cd projects/marceau-solutions/website

# Make a test change
echo "<!-- Test -->" >> index.html

# Commit to production repo
git add index.html
git commit -m "test: Verify submodule workflow"
git push origin main

# This pushes to marceausolutions.com repo → triggers GitHub Pages deploy

# Update dev-sandbox to reference new commit
cd /Users/williammarceaujr./dev-sandbox
git add projects/marceau-solutions/website
git commit -m "chore: Update website submodule"
git push origin main
```

### Step 5: Verify Website Deployed

Wait 1-2 minutes, then visit:
- https://marceausolutions.com

Check if "<!-- Test -->" appears in page source

---

## What Changes

### Before (Current - WRONG)
```
dev-sandbox repo tracks ALL website files directly
├── projects/marceau-solutions/website/
│   └── index.html (tracked in dev-sandbox)
```
**Problem**: No separate repo for hosting, can't use GitHub Pages properly

### After (Hybrid - CORRECT)
```
dev-sandbox repo tracks submodule REFERENCE
├── projects/marceau-solutions/website/ (submodule)
    └── Points to ~/marceausolutions.com repo

~/marceausolutions.com repo (outside dev-sandbox)
└── index.html (tracked in production repo)
```
**Benefit**: Proper hosting + company-centric organization

---

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# Revert the submodule restoration
cd /Users/williammarceaujr./dev-sandbox
git revert HEAD

# This puts websites back as regular folders
# Production repos still exist with latest changes (safe)
```

---

## After Migration: New Workflow

### Editing a Website

```bash
# Navigate in company context
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website

# Make changes
vim index.html

# Commit to PRODUCTION repo (it's a submodule)
git add .
git commit -m "feat: Update homepage"
git push origin main
# ↑ Pushes to marceausolutions.com → GitHub Pages deploys

# Update dev-sandbox submodule reference
cd /Users/williammarceaujr./dev-sandbox
git add projects/marceau-solutions/website
git commit -m "chore: Update website submodule"
git push origin main
```

### Editing Other Projects (Non-websites)

```bash
# Business as usual
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/amazon-seller
vim src/inventory.py
git add . && git commit -m "feat: Add optimizer"
cd ../.. && git push origin main
```

---

## Expected Results

### ✅ Company-Centric Structure (Maintained)
- All Marceau assets: `projects/marceau-solutions/`
- All HVAC assets: `projects/swflorida-hvac/`
- All Shipping assets: `projects/square-foot-shipping/`

### ✅ Proper Website Deployment (Restored)
- Websites have separate GitHub repos
- GitHub Pages hosts from production repos
- Clean separation: development vs production

### ✅ Convenient Development (Maintained)
- Work on websites in dev-sandbox context
- Alongside automation and other projects
- Company folder contains EVERYTHING for that company

### ✅ No Git Issues (Fixed)
- No nested repos (submodules are Git's official solution)
- Production and development properly separated
- Clear deployment history

---

## Questions Before Proceeding

1. ✅ Do all production website repos exist on GitHub?
2. ✅ Are websites currently live and accessible?
3. ✅ Ready to spend 10-15 minutes on migration?
4. ✅ Have uncommitted work saved?

**If all YES, proceed with Step 1!**

---

## Success Criteria

After migration is complete:

- [ ] `git submodule status` shows all 3 websites
- [ ] `ls projects/marceau-solutions/` shows `website/` folder
- [ ] `ls projects/marceau-solutions/website/` shows website files
- [ ] `cd projects/marceau-solutions/website && git remote -v` shows marceausolutions.com repo
- [ ] Test website edit pushes to production repo
- [ ] GitHub Pages deploys the change
- [ ] Company-centric structure intact (all assets in company folders)

---

## Ready to Execute?

Run:
```bash
cd /Users/williammarceaujr./dev-sandbox
./scripts/restore-hybrid-architecture.sh
```

**This is the correct architecture!**
