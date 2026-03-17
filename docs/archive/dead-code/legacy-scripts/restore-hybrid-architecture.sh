#!/bin/bash

# Restore Hybrid Architecture: Company-Centric + Website Submodules
# Combines the benefits of both approaches

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Hybrid Architecture Restoration                               ║"
echo "║  Company-Centric Folders + Website Submodules                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Check we're in dev-sandbox
if [ ! -f "CLAUDE.md" ]; then
    echo "❌ Error: Must run from dev-sandbox root"
    exit 1
fi

echo "Step 1: Clone production website repos (outside dev-sandbox)"
echo "============================================================"
cd ~

if [ ! -d "marceausolutions.com" ]; then
    echo "Cloning marceausolutions.com..."
    gh repo clone MarceauSolutions/marceausolutions.com
else
    echo "✓ marceausolutions.com already exists"
fi

if [ ! -d "swflorida-comfort-hvac" ]; then
    echo "Cloning swflorida-comfort-hvac..."
    gh repo clone MarceauSolutions/swflorida-comfort-hvac
else
    echo "✓ swflorida-comfort-hvac already exists"
fi

# Check if square-foot-shipping website repo exists
echo
echo "Checking for square-foot-shipping website repo..."
if gh repo view MarceauSolutions/squarefoot-shipping-website &>/dev/null; then
    SQUAREFOOT_REPO="MarceauSolutions/squarefoot-shipping-website"
    echo "✓ Found: $SQUAREFOOT_REPO"
    if [ ! -d "squarefoot-shipping-website" ]; then
        gh repo clone $SQUAREFOOT_REPO
    fi
elif gh repo view SquareFootShipping/squarefoot-shipping-website &>/dev/null; then
    SQUAREFOOT_REPO="SquareFootShipping/squarefoot-shipping-website"
    echo "✓ Found: $SQUAREFOOT_REPO"
    if [ ! -d "squarefoot-shipping-website" ]; then
        gh repo clone $SQUAREFOOT_REPO
    fi
else
    echo "⚠ Square Foot Shipping website repo not found on GitHub"
    echo "  Will skip this website"
    SQUAREFOOT_REPO=""
fi

echo
echo "Step 2: Backup current website state from dev-sandbox"
echo "====================================================="
cd /Users/williammarceaujr./dev-sandbox

mkdir -p /tmp/website-backup
echo "Backing up websites to /tmp/website-backup..."
cp -r projects/marceau-solutions/website /tmp/website-backup/marceausolutions 2>/dev/null || echo "  (Marceau website already removed)"
cp -r projects/swflorida-hvac/website /tmp/website-backup/swflorida-hvac 2>/dev/null || echo "  (HVAC website already removed)"
cp -r projects/square-foot-shipping/website /tmp/website-backup/squarefoot-shipping 2>/dev/null || echo "  (Shipping website already removed)"
echo "✓ Backup complete"

echo
echo "Step 3: Sync latest changes to production repos"
echo "============================================="

# Marceau Solutions
echo "Syncing marceausolutions.com..."
cd ~/marceausolutions.com
if [ -d "/tmp/website-backup/marceausolutions" ]; then
    rsync -av --delete /tmp/website-backup/marceausolutions/ ./
    if [ -n "$(git status --porcelain)" ]; then
        git add .
        git commit -m "sync: Update from dev-sandbox before submodule conversion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        git push origin main
        echo "✓ Synced and pushed"
    else
        echo "✓ No changes to sync"
    fi
else
    echo "  (No backup found - website may already be synced)"
fi

# SW Florida HVAC
echo
echo "Syncing swflorida-comfort-hvac..."
cd ~/swflorida-comfort-hvac
if [ -d "/tmp/website-backup/swflorida-hvac" ]; then
    rsync -av --delete /tmp/website-backup/swflorida-hvac/ ./
    if [ -n "$(git status --porcelain)" ]; then
        git add .
        git commit -m "sync: Update from dev-sandbox before submodule conversion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        git push origin main
        echo "✓ Synced and pushed"
    else
        echo "✓ No changes to sync"
    fi
else
    echo "  (No backup found - website may already be synced)"
fi

# Square Foot Shipping (if exists)
if [ -n "$SQUAREFOOT_REPO" ]; then
    echo
    echo "Syncing squarefoot-shipping-website..."
    cd ~/squarefoot-shipping-website
    if [ -d "/tmp/website-backup/squarefoot-shipping" ]; then
        rsync -av --delete /tmp/website-backup/squarefoot-shipping/ ./
        if [ -n "$(git status --porcelain)" ]; then
            git add .
            git commit -m "sync: Update from dev-sandbox before submodule conversion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
            git push origin main
            echo "✓ Synced and pushed"
        else
            echo "✓ No changes to sync"
        fi
    else
        echo "  (No backup found - website may already be synced)"
    fi
fi

echo
echo "Step 4: Remove websites from dev-sandbox tracking"
echo "==============================================="
cd /Users/williammarceaujr./dev-sandbox

# Remove from git tracking (but keep files for now)
git rm -r --cached projects/marceau-solutions/website 2>/dev/null || echo "  Marceau website already removed from tracking"
git rm -r --cached projects/swflorida-hvac/website 2>/dev/null || echo "  HVAC website already removed from tracking"
git rm -r --cached projects/square-foot-shipping/website 2>/dev/null || echo "  Shipping website already removed from tracking"

echo
echo "Step 5: Delete local website folders in dev-sandbox"
echo "================================================"
rm -rf projects/marceau-solutions/website 2>/dev/null && echo "✓ Removed Marceau website folder" || echo "  (already removed)"
rm -rf projects/swflorida-hvac/website 2>/dev/null && echo "✓ Removed HVAC website folder" || echo "  (already removed)"
rm -rf projects/square-foot-shipping/website 2>/dev/null && echo "✓ Removed Shipping website folder" || echo "  (already removed)"

echo
echo "Step 6: Add websites back as submodules"
echo "======================================"

# Marceau Solutions
if [ ! -d "projects/marceau-solutions/website" ]; then
    echo "Adding marceausolutions.com as submodule..."
    git submodule add https://github.com/MarceauSolutions/marceausolutions.com projects/marceau-solutions/website
    echo "✓ Added"
else
    echo "✓ Marceau website submodule already exists"
fi

# SW Florida HVAC
if [ ! -d "projects/swflorida-hvac/website" ]; then
    echo "Adding swflorida-comfort-hvac as submodule..."
    git submodule add https://github.com/MarceauSolutions/swflorida-comfort-hvac projects/swflorida-hvac/website
    echo "✓ Added"
else
    echo "✓ HVAC website submodule already exists"
fi

# Square Foot Shipping (if repo exists)
if [ -n "$SQUAREFOOT_REPO" ]; then
    if [ ! -d "projects/square-foot-shipping/website" ]; then
        echo "Adding squarefoot-shipping-website as submodule..."
        git submodule add https://github.com/$SQUAREFOOT_REPO projects/square-foot-shipping/website
        echo "✓ Added"
    else
        echo "✓ Shipping website submodule already exists"
    fi
fi

echo
echo "Step 7: Initialize and update submodules"
echo "======================================"
git submodule init
git submodule update
echo "✓ Submodules initialized"

echo
echo "Step 8: Commit the hybrid architecture"
echo "===================================="
git add .gitmodules projects/
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

echo
echo "Step 9: Push to remote"
echo "===================="
git push origin main
echo "✓ Pushed to dev-sandbox"

echo
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Hybrid Architecture Restored Successfully!                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo
echo "Verification:"
echo "-------------"
git submodule status
echo
echo "Folder structure:"
echo "-----------------"
ls -la projects/marceau-solutions/ | grep website
ls -la projects/swflorida-hvac/ | grep website
if [ -n "$SQUAREFOOT_REPO" ]; then
    ls -la projects/square-foot-shipping/ | grep website
fi
echo
echo "Next steps:"
echo "-----------"
echo "1. Test website editing:"
echo "   cd projects/marceau-solutions/website"
echo "   # Make changes, commit, push"
echo
echo "2. Changes push to production repo (marceausolutions.com)"
echo "3. GitHub Pages auto-deploys"
echo "4. Update dev-sandbox submodule reference:"
echo "   cd /Users/williammarceaujr./dev-sandbox"
echo "   git add projects/marceau-solutions/website"
echo "   git commit -m 'Update website submodule'"
echo
echo "✅ Done!"
