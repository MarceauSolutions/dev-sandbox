#!/bin/bash
# mac-sync-safe.sh — Safe sync for parallel Mac/EC2 workflow
# Handles conflicts gracefully, preserves code, discards output conflicts

set -e
cd ~/dev-sandbox

echo "=== Safe Mac Sync ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Abort any stuck merge
git merge --abort 2>/dev/null || true

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📦 Stashing local changes..."
    git stash push -m "auto-stash-$(date +%Y%m%d-%H%M%S)"
    STASHED=1
else
    STASHED=0
fi

# Remove untracked files that would conflict (output files only)
echo "🧹 Cleaning untracked output files..."
git clean -fd -- '**/output/' 2>/dev/null || true

# Pull latest
echo "⬇️  Pulling from GitHub..."
git pull origin main --no-edit || {
    echo "⚠️  Pull failed. Attempting auto-resolution..."
    # Accept theirs for any output/state files
    git checkout --theirs -- '**/output/' '**/output/**' '**/*_state.json' '**/*_cache.json' 2>/dev/null || true
    git add . 2>/dev/null || true
    git commit -m "auto: resolve sync conflicts (accept EC2 outputs)" 2>/dev/null || true
}

# Re-apply stashed changes if any
if [ "$STASHED" -eq 1 ]; then
    echo "📦 Re-applying your local changes..."
    git stash pop || {
        echo "⚠️  Couldn't auto-apply stash. Your changes are in 'git stash list'"
    }
fi

echo ""
echo "✅ Sync complete!"
echo ""
echo "Current branch: $(git branch --show-current)"
echo "Latest commit: $(git log -1 --oneline)"
