# Hybrid Architecture Solution

**Goal**: Combine company-centric folder structure WITH proper website deployment architecture

**Created**: 2026-01-21

---

## The Best of Both Worlds

### What We Want to Keep (Company-Centric Structure)
✅ All company assets in ONE folder
✅ Easy navigation: "Here's ALL your work"
✅ Projects grouped by company, not by type
✅ Shared multi-tenant tools in `projects/shared/`

### What We Need to Add Back (Website Submodules)
✅ Websites have separate GitHub repos (for hosting)
✅ Work on websites in dev-sandbox context
✅ Deploy to production repos automatically
✅ Clean separation: development vs production

---

## The Hybrid Architecture

```
dev-sandbox/ (MarceauSolutions/dev-sandbox - main development repo)
├── projects/
│   ├── marceau-solutions/              ← Company folder (✅ KEEP)
│   │   ├── README.md
│   │   ├── website/                    ← Git submodule → marceausolutions.com repo
│   │   ├── amazon-seller/
│   │   ├── fitness-influencer/
│   │   │   ├── backend/
│   │   │   ├── frontend/
│   │   │   └── mcp/
│   │   └── [8 other projects]
│   │
│   ├── swflorida-hvac/                 ← Company folder (✅ KEEP)
│   │   ├── README.md
│   │   ├── website/                    ← Git submodule → swflorida-comfort-hvac repo
│   │   └── hvac-distributors/
│   │
│   ├── square-foot-shipping/           ← Company folder (✅ KEEP)
│   │   ├── README.md
│   │   ├── website/                    ← Git submodule → squarefoot-shipping repo
│   │   └── lead-gen/
│   │
│   └── shared/                         ← Shared tools (✅ KEEP)
│       ├── lead-scraper/
│       ├── ai-customer-service/
│       ├── social-media-automation/
│       └── personal-assistant/

Outside dev-sandbox (production website repos):
~/marceausolutions.com/                 ← Separate repo for GitHub Pages
~/swflorida-comfort-hvac/               ← Separate repo for hosting
~/squarefoot-shipping-website/          ← Separate repo for hosting
```

---

## How This Works

### For Non-Website Projects (No Change)
Projects like `amazon-seller`, `fitness-influencer`, `hvac-distributors`, etc.:
- ✅ Regular folders in dev-sandbox
- ✅ Tracked in dev-sandbox repo
- ✅ No submodules needed

### For Websites (Submodules)
Websites like `website/` folders:
- ✅ Git submodules pointing to production repos
- ✅ Located in company folders (company-centric structure)
- ✅ Production repos exist outside dev-sandbox
- ✅ Changes sync to both repos

---

## Implementation Steps

### Step 1: Clone Production Repos (Outside dev-sandbox)

```bash
cd ~
gh repo clone MarceauSolutions/marceausolutions.com
gh repo clone MarceauSolutions/swflorida-comfort-hvac

# Check if square-foot-shipping website repo exists
gh repo view MarceauSolutions/squarefoot-shipping-website 2>/dev/null || \
gh repo view SquareFootShipping/squarefoot-shipping-website
```

### Step 2: Save Current Website Changes

Before removing website folders from dev-sandbox, save the latest changes:

```bash
cd /Users/williammarceaujr./dev-sandbox

# Copy current website state to temp location
mkdir -p /tmp/website-backup
cp -r projects/marceau-solutions/website /tmp/website-backup/marceausolutions
cp -r projects/swflorida-hvac/website /tmp/website-backup/swflorida-hvac
cp -r projects/square-foot-shipping/website /tmp/website-backup/squarefoot-shipping
```

### Step 3: Remove Websites from dev-sandbox Tracking

```bash
cd /Users/williammarceaujr./dev-sandbox

# Remove website folders from git (but keep files locally for now)
git rm -r --cached projects/marceau-solutions/website
git rm -r --cached projects/swflorida-hvac/website
git rm -r --cached projects/square-foot-shipping/website

# Don't delete the actual folders yet - we'll replace them with submodules
```

### Step 4: Update Production Repos with Latest Changes

```bash
# Marceau Solutions
cd ~/marceausolutions.com
rsync -av --delete /tmp/website-backup/marceausolutions/ ./
git add .
git commit -m "sync: Update from dev-sandbox with latest changes

Syncing latest website updates from dev-sandbox before
converting to submodule architecture.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push origin main

# SW Florida HVAC
cd ~/swflorida-comfort-hvac
rsync -av --delete /tmp/website-backup/swflorida-hvac/ ./
git add .
git commit -m "sync: Update from dev-sandbox with latest changes"
git push origin main

# Square Foot Shipping (if repo exists)
# cd ~/squarefoot-shipping-website
# rsync -av --delete /tmp/website-backup/squarefoot-shipping/ ./
# git add .
# git commit -m "sync: Update from dev-sandbox with latest changes"
# git push origin main
```

### Step 5: Remove Local Website Folders in dev-sandbox

```bash
cd /Users/williammarceaujr./dev-sandbox

# Now safe to delete since we've synced to production
rm -rf projects/marceau-solutions/website
rm -rf projects/swflorida-hvac/website
rm -rf projects/square-foot-shipping/website
```

### Step 6: Add Websites Back as Submodules

```bash
cd /Users/williammarceaujr./dev-sandbox

# Add as submodules pointing to production repos
git submodule add https://github.com/MarceauSolutions/marceausolutions.com projects/marceau-solutions/website
git submodule add https://github.com/MarceauSolutions/swflorida-comfort-hvac projects/swflorida-hvac/website

# If square-foot-shipping repo exists:
# git submodule add https://github.com/[org]/squarefoot-shipping-website projects/square-foot-shipping/website
```

### Step 7: Initialize and Update Submodules

```bash
git submodule init
git submodule update
```

### Step 8: Commit the Submodule Setup

```bash
git add .gitmodules projects/marceau-solutions/website projects/swflorida-hvac/website
git commit -m "fix: Restore websites as submodules (hybrid architecture)

Combines company-centric folder structure with proper website deployment:

Company-centric structure (KEPT):
- All company assets in single folder
- projects/marceau-solutions/ contains ALL Marceau assets
- projects/swflorida-hvac/ contains ALL HVAC assets
- projects/square-foot-shipping/ contains ALL shipping assets

Website deployment (RESTORED):
- Websites are git submodules pointing to production repos
- Production repos host on GitHub Pages
- Work on websites in dev-sandbox, deploy to production automatically

Best of both worlds: organized development + proper deployment.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

---

## How to Work with This Architecture

### Working on a Website

```bash
# Navigate to website in company folder
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/website

# Make changes
vim index.html

# Commit to PRODUCTION repo (because it's a submodule)
git add .
git commit -m "feat: Update homepage hero section"
git push origin main  # Pushes to marceausolutions.com → deploys via GitHub Pages

# Go back to dev-sandbox root and update submodule reference
cd /Users/williammarceaujr./dev-sandbox
git add projects/marceau-solutions/website
git commit -m "chore: Update website submodule to latest"
git push origin main
```

### Working on Other Projects (Non-websites)

```bash
# Navigate to project
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/amazon-seller

# Make changes
vim src/inventory.py

# Commit to dev-sandbox (regular git workflow)
git add .
git commit -m "feat: Add inventory optimizer"

# Push to dev-sandbox
cd /Users/williammarceaujr./dev-sandbox
git push origin main
```

### Cloning dev-sandbox Fresh

When cloning dev-sandbox on a new machine:

```bash
# Clone dev-sandbox
git clone https://github.com/MarceauSolutions/dev-sandbox.git
cd dev-sandbox

# Initialize submodules (pulls website repos)
git submodule init
git submodule update --remote

# Now all websites are present and linked to production repos
```

---

## Benefits of Hybrid Approach

### ✅ Company-Centric Organization
- All Marceau Solutions assets: `projects/marceau-solutions/`
- All HVAC assets: `projects/swflorida-hvac/`
- All Shipping assets: `projects/square-foot-shipping/`
- Easy to showcase: "Here's ALL your work in one folder"

### ✅ Proper Website Deployment
- Websites have separate GitHub repos for hosting
- GitHub Pages deploys from `marceausolutions.com` repo (not dev-sandbox)
- Clean deployment history (only website commits)
- Can have different collaborators on website vs dev-sandbox

### ✅ Development Convenience
- Work on everything in dev-sandbox context
- Website alongside automation projects
- Changes to website automatically sync to production
- No manual deployment scripts needed

### ✅ No Nested Repo Problems
- Submodules are Git's official solution for this
- dev-sandbox tracks submodule references (not full content)
- Each website repo is independent

---

## Verification After Setup

```bash
# Check submodule status
git submodule status

# Should show:
# <commit-hash> projects/marceau-solutions/website (heads/main)
# <commit-hash> projects/swflorida-hvac/website (heads/main)

# Verify no nested .git folders (besides submodules)
find . -name '.git' -type d
# Should show:
# ./.git (main repo)
# ./projects/marceau-solutions/website/.git (submodule - OK)
# ./projects/swflorida-hvac/website/.git (submodule - OK)

# Check folder structure still company-centric
ls projects/marceau-solutions/
# Should show: website/ (submodule), amazon-seller/, fitness-influencer/, etc.

ls projects/swflorida-hvac/
# Should show: website/ (submodule), hvac-distributors/
```

---

## Common Operations

### Update Website and Deploy
```bash
cd projects/marceau-solutions/website
git pull origin main  # Get latest from production
# Make changes
git add . && git commit -m "Update" && git push origin main  # Deploy
cd ../.. && git add projects/marceau-solutions/website && git commit -m "Update website submodule"
```

### Update All Submodules
```bash
git submodule update --remote --merge
```

### Add New Company with Website
```bash
# Create company folder
mkdir -p projects/new-company

# If they have a website hosted separately:
git submodule add https://github.com/[org]/new-company-website projects/new-company/website

# If no separate website repo needed:
# Just create regular website/ folder (no submodule)
```

---

## Migration Script

I'll create `scripts/restore-hybrid-architecture.sh` to automate all these steps.

---

## Questions Before Executing

1. **Do all 3 website repos exist on GitHub?**
   - ✅ MarceauSolutions/marceausolutions.com
   - ✅ MarceauSolutions/swflorida-comfort-hvac
   - ❓ Square-foot-shipping website repo?

2. **Are there any website changes in dev-sandbox that aren't in production repos?**
   - Need to sync before converting to submodules

3. **Ready to execute the migration?**
   - This will take ~10-15 minutes
   - Websites will be briefly unavailable during sync

**Let me know and I'll execute the hybrid architecture setup!**
