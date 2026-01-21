# URGENT: Fix Website Architecture

**Problem**: I incorrectly removed website submodules and merged them into dev-sandbox
**Impact**: Production website repos on GitHub are now out of sync
**Status**: ⚠️ NEEDS IMMEDIATE FIX

---

## What Went Wrong

1. Websites WERE correctly set up as git submodules pointing to separate repos:
   - `projects/marceau-solutions/website` → `MarceauSolutions/marceausolutions.com`
   - `projects/swflorida-hvac/website` → `MarceauSolutions/swflorida-comfort-hvac`
   - `projects/square-foot-shipping/website` → (separate repo)

2. I incorrectly thought this was a "nested repo problem" and removed the submodules

3. I merged all website files into the dev-sandbox repo (commit ccf718b)

4. Now the production repos on GitHub are outdated and disconnected

---

## The Correct Architecture (Which We HAD)

```
dev-sandbox/ (MarceauSolutions/dev-sandbox repo)
├── projects/
│   ├── marceau-solutions/
│   │   └── website/  ← git submodule → MarceauSolutions/marceausolutions.com
│   ├── swflorida-hvac/
│   │   └── website/  ← git submodule → MarceauSolutions/swflorida-comfort-hvac
│   └── square-foot-shipping/
│       └── website/  ← git submodule → (production repo)
```

**This was CORRECT!** Submodules are the right solution here because:
- Websites need separate repos for GitHub Pages hosting
- But we want to work on them in dev-sandbox context (alongside automation)
- Submodules solve exactly this problem

---

## How to Fix It

### Option 1: Revert and Restore Submodules (RECOMMENDED)

```bash
cd /Users/williammarceaujr./dev-sandbox

# Revert the bad commit
git revert ccf718b --no-commit

# This will restore the submodule setup but we need to reinitialize them

# Clone production repos locally (outside dev-sandbox)
cd ~
gh repo clone MarceauSolutions/marceausolutions.com
gh repo clone MarceauSolutions/swflorida-comfort-hvac
# (clone square-foot-shipping if it exists)

# Back to dev-sandbox and initialize submodules
cd dev-sandbox
git submodule init
git submodule update

# Commit the revert
git commit -m "Revert 'fix: Convert website submodules to regular directories'

This reverts commit ccf718b.

Websites SHOULD be submodules because they need separate GitHub repos
for hosting while being developed in dev-sandbox context.

Restoring correct architecture."

# Push to dev-sandbox
git push origin main
```

### Option 2: Manual Reconstruction

If revert doesn't work cleanly:

```bash
# 1. Remove website folders from dev-sandbox tracking
git rm -r projects/marceau-solutions/website
git rm -r projects/swflorida-hvac/website
git rm -r projects/square-foot-shipping/website

# 2. Clone production repos outside dev-sandbox
cd ~
gh repo clone MarceauSolutions/marceausolutions.com
gh repo clone MarceauSolutions/swflorida-comfort-hvac

# 3. Add them back as submodules
cd ~/dev-sandbox
git submodule add https://github.com/MarceauSolutions/marceausolutions.com projects/marceau-solutions/website
git submodule add https://github.com/MarceauSolutions/swflorida-comfort-hvac projects/swflorida-hvac/website

# 4. Commit
git commit -m "fix: Restore websites as git submodules for proper deployment"
git push origin main
```

---

## Current Risk Assessment

### HIGH RISK: Production websites may be outdated

**Check immediately**:
```bash
# What's the last commit on production repos?
gh api repos/MarceauSolutions/marceausolutions.com/commits/main --jq '.[0] | {date:.commit.author.date, message:.commit.message}'

gh api repos/MarceauSolutions/swflorida-comfort-hvac/commits/main --jq '.[0] | {date:.commit.author.date, message:.commit.message}'
```

**If they're outdated** (older than today's changes):
- Latest changes are ONLY in dev-sandbox
- Need to sync them to production repos ASAP
- Live websites might be showing old content

---

## Immediate Actions Required

1. ✅ **Document the problem** (this file)
2. ⚠️ **Check production repo status** (are they outdated?)
3. ⚠️ **Decide: Revert or Manual?** (Option 1 vs 2)
4. ⚠️ **Execute the fix**
5. ⚠️ **Sync any missing changes to production**
6. ✅ **Verify websites are live and current**

---

## William's Decision Needed

**Question 1**: Do you want me to revert the submodule removal (Option 1)?
- This restores the previous submodule setup
- Websites will again be in separate repos
- Development happens in dev-sandbox, deployment to production repos

**Question 2**: OR should we use manual sync (Option 2)?
- Keep websites in dev-sandbox as regular folders
- Create deployment script to sync to production repos
- More manual but simpler

**Recommendation**: **Option 1** (restore submodules) because that's how it was working before and it's the correct architecture for this use case.

---

## What NOT to Do

❌ **Don't push dev-sandbox to production website repos** - They should stay separate
❌ **Don't delete production repos** - They're hosting the live sites
❌ **Don't ignore this** - Live websites might be outdated

---

## Timeline

- **2026-01-21 14:39**: Completed company-centric migration (websites were submodules - CORRECT)
- **2026-01-21 14:48**: INCORRECTLY removed submodules (commit ccf718b) - WRONG
- **2026-01-21 14:53**: Pushed to dev-sandbox (now production is disconnected)
- **2026-01-21 NOW**: Need to fix immediately

**Time to fix**: ~5-10 minutes
**Risk if not fixed**: Production websites outdated, no way to deploy updates

---

## After Fix: Correct Workflow

Once submodules are restored:

### Making website changes:
```bash
# Work in dev-sandbox context
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website

# Edit files
vim index.html

# Commit to PRODUCTION repo (because website is a submodule)
git add .
git commit -m "feat: Update homepage"
git push origin main  # Pushes to marceausolutions.com repo → triggers GitHub Pages deploy

# Update dev-sandbox to reference new commit
cd /Users/williammarceaujr./dev-sandbox
git add projects/marceau-solutions/website  # Updates submodule reference
git commit -m "chore: Update website submodule"
git push origin main  # Updates dev-sandbox
```

**This is the correct workflow** - changes go to both repos appropriately.
