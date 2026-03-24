#!/usr/bin/env bash
# AgentOS Hook: Complete The Loop Guard
# After sending an SMS/email, reminds to check for replies.
# Informational — warns but does not block.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')
SEND_MARKER="/tmp/.agent-os-last-send"

# If this command sends a message (SMS, email, etc.)
if echo "$COMMAND_LOWER" | grep -qE "(twilio|sendgrid|smtp|send.*email|send.*sms|send.*message)" 2>/dev/null; then
    echo "$(date +%s):$COMMAND" > "$SEND_MARKER"
    echo "" >&2
    echo "--- Complete The Loop: Message sent ---" >&2
    echo "REMINDER: Check for replies/delivery confirmation after." >&2
    echo "" >&2
    exit 0
fi

# If marker exists and is recent (within 10 min)
if [[ -f "$SEND_MARKER" ]]; then
    SEND_TIME=$(cut -d: -f1 "$SEND_MARKER" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    AGE=$(( NOW - SEND_TIME ))
    if [[ $AGE -lt 600 ]]; then
        # Check if this command is a monitoring/check action
        if echo "$COMMAND_LOWER" | grep -qE "(monitor|inbox|check.*reply|check.*message)" 2>/dev/null; then
            rm -f "$SEND_MARKER" 2>/dev/null
        else
            echo "" >&2
            echo "--- Complete The Loop: REMINDER ---" >&2
            echo "You sent a message recently but haven't checked for replies." >&2
            echo "" >&2
        fi
    fi
fi

exit 0
