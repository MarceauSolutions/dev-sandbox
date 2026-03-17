#!/bin/bash
# sync-handoffs.sh — Pull latest from GitHub and check for pending work

set -e

REPO_DIR="/home/clawdbot/dev-sandbox"
HANDOFF_FILE="$REPO_DIR/HANDOFF.md"
HANDOFF_JSON="$REPO_DIR/ralph/handoffs.json"

cd "$REPO_DIR"

echo "=== Syncing Handoffs ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Pull latest
echo ""
echo "Pulling from GitHub..."
git pull origin main

# Check HANDOFF.md for pending EC2 tasks
echo ""
echo "=== Pending for EC2 ==="
if grep -q "^### Task:" "$HANDOFF_FILE" 2>/dev/null; then
    # Extract tasks from "Pending for EC2" section
    sed -n '/## 📤 Pending for EC2/,/## 🔄 In Progress/p' "$HANDOFF_FILE" | grep -A10 "^### Task:" || echo "No pending EC2 tasks"
else
    echo "No pending tasks found"
fi

# Check handoffs.json
echo ""
echo "=== Active Handoffs (JSON) ==="
if [ -f "$HANDOFF_JSON" ]; then
    python3 -c "
import json
with open('$HANDOFF_JSON') as f:
    data = json.load(f)
    pending = data.get('pending_for_ec2', [])
    if pending:
        for task in pending:
            print(f\"- {task.get('title', 'Untitled')}: {task.get('status', 'unknown')}\")
    else:
        print('No pending JSON tasks')
"
else
    echo "handoffs.json not found"
fi

echo ""
echo "=== Sync Complete ==="
