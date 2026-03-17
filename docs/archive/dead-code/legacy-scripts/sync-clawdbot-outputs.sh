#!/bin/bash
# Sync Clawdbot outputs from VPS to local dev-sandbox
# Usage: ./sync-clawdbot-outputs.sh [--force]
#
# This script pulls new outputs from Clawdbot VPS and places them
# in the local inbox for processing/routing to projects.

set -e

CLAWDBOT_HOST="clawdbot@44.193.244.59"
DEV_SANDBOX="/Users/williammarceaujr./dev-sandbox"
LOCAL_INBOX="$DEV_SANDBOX/.tmp/clawdbot-inbox"
PROCESSED_LOG="$LOCAL_INBOX/.processed"
NOTIFICATIONS_LOG="$LOCAL_INBOX/notifications.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$LOCAL_INBOX"
touch "$PROCESSED_LOG"
touch "$NOTIFICATIONS_LOG"

echo -e "${GREEN}Clawdbot Output Sync${NC}"
echo "========================"
echo "VPS: $CLAWDBOT_HOST"
echo "Inbox: $LOCAL_INBOX"
echo ""

# Check SSH connectivity
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $CLAWDBOT_HOST "echo ok" &>/dev/null; then
    echo -e "${RED}Error: Cannot connect to Clawdbot VPS${NC}"
    echo "Check: SSH keys, VPS status, network"
    exit 1
fi

echo -e "${GREEN}Connected to VPS${NC}"

# Check if output directory exists on VPS
if ! ssh $CLAWDBOT_HOST "test -d ~/output" 2>/dev/null; then
    echo -e "${YELLOW}No output directory on VPS (~/output/)${NC}"
    echo "Creating it..."
    ssh $CLAWDBOT_HOST "mkdir -p ~/output"
fi

# Get list of outputs from Clawdbot
OUTPUTS=$(ssh $CLAWDBOT_HOST "ls ~/output/ 2>/dev/null" || echo "")

if [ -z "$OUTPUTS" ]; then
    echo "No outputs to sync"
    exit 0
fi

NEW_COUNT=0
SKIP_COUNT=0

# Process each output
while IFS= read -r request_id; do
    if [ -z "$request_id" ]; then
        continue
    fi

    if grep -q "^$request_id$" "$PROCESSED_LOG" && [ "$1" != "--force" ]; then
        ((SKIP_COUNT++))
        continue
    fi

    echo -e "${GREEN}Syncing:${NC} $request_id"

    # Create local directory
    mkdir -p "$LOCAL_INBOX/$request_id"

    # Sync files
    if scp -r "$CLAWDBOT_HOST:~/output/$request_id/*" "$LOCAL_INBOX/$request_id/" 2>/dev/null; then
        # Mark as processed
        echo "$request_id" >> "$PROCESSED_LOG"

        # Log notification
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$TIMESTAMP] New Clawdbot output: $request_id" >> "$NOTIFICATIONS_LOG"

        ((NEW_COUNT++))
    else
        echo -e "${RED}Failed to sync:${NC} $request_id"
    fi
done <<< "$OUTPUTS"

echo ""
echo "========================"
echo -e "${GREEN}Sync Complete${NC}"
echo "New outputs: $NEW_COUNT"
echo "Skipped (already synced): $SKIP_COUNT"

if [ $NEW_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}New outputs ready for review:${NC}"
    ls -la "$LOCAL_INBOX" | grep -E "^d" | grep -v "^\." | tail -$NEW_COUNT
    echo ""
    echo "To route to a project:"
    echo "  python scripts/route-clawdbot-contribution.py <request-id> <project-path>"
fi
