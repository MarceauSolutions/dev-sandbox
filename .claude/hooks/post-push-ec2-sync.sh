#!/bin/bash
###############################################################################
# post-push-ec2-sync.sh — Claude Code PostToolUse hook
#
# Fires after any Bash tool call containing "git push".
# Automatically pulls latest to EC2 so Clawdbot stays in sync.
#
# Input: JSON on stdin with tool_input.command
# Output: JSON with status (proceed if push detected and sync succeeds)
###############################################################################

INPUT=$(cat)

# Only trigger on git push commands
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

if ! echo "$COMMAND" | grep -q "git push"; then
    echo '{"decision": "proceed"}'
    exit 0
fi

EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"
EC2_HOST="34.193.98.97"
EC2_USER="ec2-user"
LOG="/tmp/post-push-ec2-sync.log"

# Sync EC2 in background so we don't block Claude Code
(
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PostToolUse: git push detected, syncing EC2..." >> "$LOG"

    RESULT=$(ssh -i "$EC2_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$EC2_USER@$EC2_HOST" \
        "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git fetch origin main && git pull origin main --rebase 2>&1'" \
        2>&1)

    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] EC2 synced ✓ — $RESULT" >> "$LOG"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] EC2 sync FAILED — $RESULT" >> "$LOG"
    fi
) &

# Always proceed — sync is best-effort and non-blocking
echo '{"decision": "proceed"}'
exit 0
