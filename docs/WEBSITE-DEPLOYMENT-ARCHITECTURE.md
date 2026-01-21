# Website Deployment Architecture

**Problem**: How do we organize websites in dev-sandbox while maintaining separate GitHub repos for hosting?

**Created**: 2026-01-21

---

## The Correct Architecture

### Development (dev-sandbox repo)
```
dev-sandbox/ (ONE git repo: MarceauSolutions/dev-sandbox)
├── projects/
│   ├── marceau-solutions/
│   │   └── website/           ← Development copy (tracked in dev-sandbox)
│   ├── swflorida-hvac/
│   │   └── website/           ← Development copy (tracked in dev-sandbox)
│   └── square-foot-shipping/
│       └── website/           ← Development copy (tracked in dev-sandbox)
```

### Production (separate repos for hosting)
```
~/marceausolutions.com/ (SEPARATE repo: MarceauSolutions/marceausolutions.com)
└── [website files for GitHub Pages hosting]

~/swflorida-comfort-hvac/ (SEPARATE repo: SWFloridaComfortHVAC/swflorida-comfort-hvac.com)
└── [website files for hosting]

~/squarefoot-shipping-website/ (SEPARATE repo: SquareFootShipping/squarefoot-shipping.com)
└── [website files for hosting]
```

---

## Why Both Are Needed

### dev-sandbox/projects/[company]/website/
**Purpose**: Development workspace
**Git Repo**: dev-sandbox (parent)
**Location**: Inside dev-sandbox
**Benefits**:
- All company assets in one place for development
- Easy to work on website alongside automation
- Full git history in development context

### ~/[company-website]/ (separate location)
**Purpose**: Production hosting
**Git Repo**: Separate repo (e.g., marceausolutions.com)
**Location**: OUTSIDE dev-sandbox (sibling directory)
**Benefits**:
- Clean repo for GitHub Pages hosting
- No automation code cluttering website repo
- Separate deploy history
- Separate collaborators/permissions

---

## Deployment Workflow

### Step 1: Develop in dev-sandbox
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website
# Edit index.html, contact.html, etc.
git add .
git commit -m "feat: Update homepage hero section"
git push origin main  # Pushes to dev-sandbox repo
```

### Step 2: Deploy to Production
```bash
# Copy changes to production website repo
rsync -av --delete \
  /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website/ \
  /Users/williammarceaujr./marceausolutions.com/

# Commit and push to production
cd /Users/williammarceaujr./marceausolutions.com
git add .
git commit -m "feat: Update homepage hero section"
git push origin main  # Triggers GitHub Pages deployment
```

---

## Current State (After Today's Migration)

### ❌ PROBLEM: Website repos no longer exist

When I converted submodules to regular directories, I removed the .git folders from:
- `projects/marceau-solutions/website/.git` ← Was pointing to marceausolutions.com repo
- `projects/swflorida-hvac/website/.git` ← Was pointing to swflorida-comfort-hvac repo
- `projects/square-foot-shipping/website/.git` ← Was pointing to squarefoot-shipping repo

### ✅ SOLUTION: Restore the dual-repo architecture

Option A: **Keep submodules** (RECOMMENDED)
- Restore website folders as git submodules
- Development copy stays in dev-sandbox
- Production copy has separate repo
- Best of both worlds

Option B: **Manual sync script**
- Keep websites as regular folders in dev-sandbox
- Create deploy script to sync to production repos
- More manual, but simpler

---

## RECOMMENDED: Option A (Restore Submodules)

### Why Submodules Are Actually Good Here

Git submodules get a bad reputation, but for this use case they're perfect:

**Benefits**:
1. Work on website in dev-sandbox context (alongside automation)
2. Website changes committed to BOTH repos (dev-sandbox + production)
3. Production repo stays clean (no automation clutter)
4. Automatic sync between development and production

**How it works**:
```
dev-sandbox/projects/marceau-solutions/website/
└── .git (points to ~/marceausolutions.com repo)
    └── All website files tracked in production repo
    └── Submodule reference tracked in dev-sandbox repo
```

When you:
- `cd projects/marceau-solutions/website && git commit` → Commits to marceausolutions.com repo
- `cd dev-sandbox && git commit` → Commits the submodule reference (which commit the website is at)

---

## Restoring the Correct Architecture

### Step 1: Undo the submodule removal

```bash
cd /Users/williammarceaujr./dev-sandbox

# Revert the commit that removed submodules
git revert ccf718b  # The commit that converted submodules to regular dirs

# This restores the submodule references
```

### Step 2: Verify production repos still exist

```bash
# Check if production website repos exist
ls -la ~/marceausolutions.com/.git
ls -la ~/swflorida-comfort-hvac/.git
ls -la ~/squarefoot-shipping-website/.git
```

If they DON'T exist, we need to:
1. Re-clone from GitHub (if they exist there)
2. OR re-initialize them (if they never existed separately)

### Step 3: Re-link submodules

```bash
# For each website, add as submodule pointing to production repo
git submodule add ~/marceausolutions.com projects/marceau-solutions/website
git submodule add ~/swflorida-comfort-hvac projects/swflorida-hvac/website
git submodule add ~/squarefoot-shipping-website projects/square-foot-shipping/website
```

---

## Alternative: Option B (Manual Sync Script)

If you prefer NOT to use submodules:

### Create deployment script

```bash
#!/bin/bash
# scripts/deploy-website.sh

WEBSITE=$1  # marceau-solutions, swflorida-hvac, square-foot-shipping

case $WEBSITE in
  marceau-solutions)
    SRC="projects/marceau-solutions/website/"
    DEST="~/marceausolutions.com/"
    ;;
  swflorida-hvac)
    SRC="projects/swflorida-hvac/website/"
    DEST="~/swflorida-comfort-hvac/"
    ;;
  square-foot-shipping)
    SRC="projects/square-foot-shipping/website/"
    DEST="~/squarefoot-shipping-website/"
    ;;
esac

# Sync files
rsync -av --delete "$SRC" "$DEST"

# Commit to production repo
cd "$DEST"
git add .
git commit -m "Deploy from dev-sandbox"
git push origin main

echo "✓ Deployed $WEBSITE to production"
```

**Usage**:
```bash
./scripts/deploy-website.sh marceau-solutions
```

**Pros**:
- No submodules (simpler mental model)
- Explicit deployment step

**Cons**:
- Manual sync required
- Can forget to deploy
- Two separate histories (dev-sandbox vs production)

---

## Recommendation

**USE SUBMODULES** (Option A) because:

1. **Websites ARE separate products** - They deserve their own repos
2. **GitHub Pages hosting requires separate repo** - marceausolutions.com repo hosts the site
3. **Submodules maintain both contexts** - Work in dev-sandbox, deploy to production automatically
4. **This is what submodules were designed for** - Exactly this use case

---

## Questions to Answer

1. **Do production website repos still exist?**
   - Check ~/marceausolutions.com/.git
   - Check GitHub: `gh repo view MarceauSolutions/marceausolutions.com`

2. **What is currently hosting marceausolutions.com?**
   - GitHub Pages from which repo?
   - Netlify/Vercel?

3. **Do you want submodules or manual sync?**
   - Submodules: Automatic, dual-context
   - Manual: Explicit, simpler

**Let me know and I'll set up the correct architecture.**

---

## Current Risk

⚠️ **WARNING**: If marceausolutions.com was being hosted from a separate GitHub repo, and that repo is now outdated (because I merged website into dev-sandbox), your live website might not have the latest changes!

**Check immediately**:
```bash
# See when production repo was last updated
cd ~/marceausolutions.com && git log -1

# See when dev-sandbox website was last updated
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website
ls -lt | head -5
```

If production is outdated, we need to deploy ASAP!
