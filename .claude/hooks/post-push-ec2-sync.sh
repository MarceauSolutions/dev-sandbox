#!/bin/bash
###############################################################################
# post-push-ec2-sync.sh — Claude Code PostToolUse hook
#
# Fires after any Bash tool call containing "git push".
# Syncs EC2, verifies the pull succeeded, and alerts on failure.
#
# Input: JSON on stdin with tool_input.command
# Output: JSON with status (always proceed — sync is non-blocking)
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
LOG="$HOME/dev-sandbox/logs/ec2-sync.log"
REPO_ROOT="$HOME/dev-sandbox"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG")"

# Sync EC2 in background so we don't block Claude Code
(
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] PostToolUse: git push detected, syncing EC2..." >> "$LOG"

    # Get local HEAD before sync
    LOCAL_HEAD=$(cd "$REPO_ROOT" && git rev-parse --short HEAD 2>/dev/null)

    # Pull on EC2
    RESULT=$(ssh -i "$EC2_KEY" -o ConnectTimeout=8 -o StrictHostKeyChecking=no \
        "$EC2_USER@$EC2_HOST" \
        "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git fetch origin main && git pull origin main --rebase 2>&1'" \
        2>&1)
    PULL_EXIT=$?

    # Verify: compare commits
    EC2_HEAD=$(ssh -i "$EC2_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$EC2_USER@$EC2_HOST" \
        "sudo -u clawdbot bash -c 'cd /home/clawdbot/dev-sandbox && git rev-parse --short HEAD'" \
        2>/dev/null)

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if [ $PULL_EXIT -eq 0 ] && [ "$LOCAL_HEAD" = "$EC2_HEAD" ]; then
        echo "[$TIMESTAMP] VERIFIED: EC2 synced to $EC2_HEAD (matches local $LOCAL_HEAD)" >> "$LOG"
    elif [ $PULL_EXIT -eq 0 ]; then
        echo "[$TIMESTAMP] WARNING: Pull succeeded but commits differ — Local=$LOCAL_HEAD EC2=$EC2_HEAD" >> "$LOG"
        # Send Telegram alert for drift
        TG_TOKEN=$(cd "$REPO_ROOT" && python3 -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; print(os.getenv('TELEGRAM_BOT_TOKEN',''))" 2>/dev/null)
        TG_CHAT=$(cd "$REPO_ROOT" && python3 -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; print(os.getenv('TELEGRAM_CHAT_ID','5692454753'))" 2>/dev/null)
        if [ -n "$TG_TOKEN" ]; then
            curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
                -H "Content-Type: application/json" \
                -d "{\"chat_id\": \"${TG_CHAT}\", \"text\": \"⚠️ EC2 Sync Drift\\nLocal: ${LOCAL_HEAD}\\nEC2: ${EC2_HEAD}\\nPull output: ${RESULT:0:200}\"}" \
                > /dev/null 2>&1
        fi
    else
        echo "[$TIMESTAMP] FAILED: EC2 sync failed (exit $PULL_EXIT) — $RESULT" >> "$LOG"
        # Send Telegram alert for failure
        TG_TOKEN=$(cd "$REPO_ROOT" && python3 -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; print(os.getenv('TELEGRAM_BOT_TOKEN',''))" 2>/dev/null)
        TG_CHAT=$(cd "$REPO_ROOT" && python3 -c "from dotenv import load_dotenv; load_dotenv('.env'); import os; print(os.getenv('TELEGRAM_CHAT_ID','5692454753'))" 2>/dev/null)
        if [ -n "$TG_TOKEN" ]; then
            curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
                -H "Content-Type: application/json" \
                -d "{\"chat_id\": \"${TG_CHAT}\", \"text\": \"🔴 EC2 Sync FAILED\\nLocal: ${LOCAL_HEAD}\\nError: ${RESULT:0:200}\"}" \
                > /dev/null 2>&1
        fi
    fi

    # Keep log file from growing forever (last 500 lines)
    if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 500 ]; then
        tail -300 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
    fi
) &

# Always proceed — sync is non-blocking
echo '{"decision": "proceed"}'
exit 0
