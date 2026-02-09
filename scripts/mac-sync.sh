#!/bin/bash
# mac-sync.sh — Copy this to ~/dev-sandbox/scripts/ on your Mac
# Syncs with GitHub and shows pending tasks for Claude Code

set -e

REPO_DIR="${HOME}/dev-sandbox"
HANDOFF_FILE="$REPO_DIR/HANDOFF.md"

cd "$REPO_DIR"

echo "=== Mac Dev Sync ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Pull latest
echo "Pulling from GitHub..."
git pull origin main
echo ""

# Show pending Mac tasks
echo "=== Pending for Mac (Claude Code) ==="
echo ""

# Extract the "Pending for Mac" section
if grep -q "## 📥 Pending for Mac" "$HANDOFF_FILE"; then
    sed -n '/## 📥 Pending for Mac/,/## 📤 Pending for EC2/p' "$HANDOFF_FILE" | head -n -1
else
    echo "No HANDOFF.md found or section missing"
fi

echo ""
echo "=== Quick Actions ==="
echo "  Edit tasks:  code HANDOFF.md"
echo "  After work:  git add . && git commit -m 'feat: description' && git push"
echo ""
