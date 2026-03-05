#!/bin/bash
# Claude Code PreToolUse Hook: No Delegation Guard
#
# HARD RULE #5: Use APIs, never delegate to user.
#
# When Claude outputs text that tells the user to do something manually
# that could be done programmatically, this hook catches common patterns
# and blocks them.
#
# Applies to: text output (SendMessage tool) — not tool calls.
# This hook runs on the SendMessage matcher.

INPUT=$(cat)

# Extract the message content
MESSAGE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('tool_input', {}).get('content', '')
print(msg.lower())
" 2>/dev/null)

if [[ -z "$MESSAGE" ]]; then
    exit 0
fi

# Patterns that indicate delegation of programmable work
VIOLATIONS=()

# "Go to [URL] and..." — telling user to visit a dashboard we have API access to
if echo "$MESSAGE" | grep -qE '(go to|visit|navigate to|open|log into)\s+(stripe|n8n|google sheets|twilio|github)' 2>/dev/null; then
    VIOLATIONS+=("Telling user to visit a service we have API/MCP access to")
fi

# "You'll need to..." / "You should..." for technical tasks
if echo "$MESSAGE" | grep -qE "(you('ll| will) need to|you should|you can then)\s+(add|set|configure|update|change|create|delete|enable|disable)" 2>/dev/null; then
    VIOLATIONS+=("Delegating a technical task to the user")
fi

# "Manually" anything
if echo "$MESSAGE" | grep -qE "manual(ly)?\s+(add|set|configure|update|change|create|run|execute)" 2>/dev/null; then
    VIOLATIONS+=("Suggesting manual action for automatable task")
fi

if [[ ${#VIOLATIONS[@]} -gt 0 ]]; then
    echo "" >&2
    echo "=== NO DELEGATION GUARD ===" >&2
    echo "HARD RULE #5: Use APIs, never delegate to user." >&2
    echo "" >&2
    for v in "${VIOLATIONS[@]}"; do
        echo "  VIOLATION: $v" >&2
    done
    echo "" >&2
    echo "Before telling William to do something:" >&2
    echo "  1. Check .env for API keys" >&2
    echo "  2. Check execution/ for existing scripts" >&2
    echo "  3. Check available MCP tools" >&2
    echo "  4. If programmatic access exists, USE IT." >&2
    echo "" >&2
    # Block the output — force Claude to rethink
    exit 1
fi

exit 0
