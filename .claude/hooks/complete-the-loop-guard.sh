#!/bin/bash
# Claude Code PreToolUse Hook: Complete The Loop Guard
#
# HARD RULE #7: Complete the loop — sending without monitoring is half a job.
#
# After any Twilio SMS send or email send command, this hook checks if the
# PREVIOUS commands in the session included a send. If so, it warns that
# a monitor/check should follow.
#
# This runs on Bash commands. If we detect a twilio_sms.py send that ISN'T
# followed by a twilio_inbox_monitor.py check, it warns.

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Track state: if we're SENDING, remind about monitoring
SEND_MARKER="/tmp/.claude-last-send"

# If this command is a SEND action
if echo "$COMMAND_LOWER" | grep -qE "(twilio_sms\.py|send_onboarding_email\.py)" 2>/dev/null; then
    if echo "$COMMAND_LOWER" | grep -qE "(--template|--message|--to)" 2>/dev/null; then
        # Mark that we sent something
        echo "$(date +%s):$COMMAND" > "$SEND_MARKER"
        echo "" >&2
        echo "--- Complete The Loop: SMS/Email sent ---" >&2
        echo "REMINDER: Follow up with inbox monitor to check for replies." >&2
        echo "  python execution/twilio_inbox_monitor.py check --hours 4" >&2
        echo "" >&2
        exit 0
    fi
fi

# If this command is a MONITOR action, clear the marker
if echo "$COMMAND_LOWER" | grep -qE "(twilio_inbox_monitor|gmail_monitor|inbox)" 2>/dev/null; then
    rm -f "$SEND_MARKER" 2>/dev/null
    exit 0
fi

# If marker exists and is recent (within 10 min) and we're doing something else
if [[ -f "$SEND_MARKER" ]]; then
    SEND_TIME=$(cut -d: -f1 "$SEND_MARKER" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$(( NOW - SEND_TIME ))

    # If send was within last 600 seconds (10 min) and we haven't monitored yet
    if [[ $AGE -lt 600 ]]; then
        echo "" >&2
        echo "--- Complete The Loop: REMINDER ---" >&2
        echo "You sent an SMS/email recently but haven't checked for replies." >&2
        echo "Run: python execution/twilio_inbox_monitor.py check --hours 4" >&2
        echo "" >&2
        # Don't block — just remind
    fi
fi

exit 0
